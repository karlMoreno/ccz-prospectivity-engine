"""IngestionPipeline — TEMPLATE METHOD.

`run()` is the one fixed, honest sequence every source goes through:

    fetch -> adapt -> normalize -> validate -> dedup -> append

(The alpha proposal states this shorthand as "fetch→adapt→normalize→dedup→
validate→append." This implementation validates *before* deduping: the dedup
policy (dedup_rules.py) matches on typed fields — parsed coordinates, parsed
datetimes — so it needs Observation objects, not raw strings. Both orderings run entirely before `append`, so the corpus
guarantee is identical; flagged here because the contracts are frozen and any
reading of their order deserves to be explicit, not silent.)

This is Template Method by composition rather than subclassing: the sequence
itself never changes, but each step delegates to an injected Strategy
(SourceAdapter, a NormalizerRegistry of AbundanceNormalizer per evidence
class, an optional DuplicateResolutionPolicy) so a new source or a new dedup
rule is a new object passed to the constructor, never a new subclass of the
pipeline.

    ┌─────────────────────────────────────────────────────────┐
    │                  IngestionPipeline.run()                   │
    │                                                             │
    │  fetch ──► adapt ──► normalize ──► validate ──► dedup ──►  │
    │   │          │           │             │           │   append
    │   ▼          ▼           ▼             ▼           ▼      │
    │ adapter   adapter   normalizers    Observation   policy    │
    │ .fetch()  .adapt()  .normalize()   (**record)   .resolve()  │
    │                                                  + APPLY    │
    │                     (NormalizerRegistry;                    │
    │                      REGISTRY, ingestion/normalizer_registry.py) │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.normalizer_registry import NormalizerRegistry
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter
from engine.prospectivity.ingestion.dedup_rules import DuplicateResolutionPolicy
from engine.prospectivity.ingestion.resolution import AbsorbInto, Admit, Replace
from engine.prospectivity.provenance.recorder import NullObserver, PipelineObserver


class IngestionPipeline:
    """Runs one SourceAdapter through fetch/adapt/normalize/validate/dedup/append.

    `dedup_policy` (C2, 2026-07-30) DECIDES; this pipeline APPLIES. It
    replaced a `Specification` whose `is_satisfied_by` both decided and
    mutated — see `_dedup` and docs/PATTERNS.md §3.0.

    `observer` (OBSERVER; provenance/recorder.py) is how the pipeline reports
    what happened without owning a reporting responsibility. It defaults to
    NullObserver (Null Object), so an un-observed pipeline behaves exactly as
    it did before observers existed and no test is forced to assert on them.
    The pipeline never READS an observer's state and never branches on it —
    recording cannot change a decision here.
    """

    def __init__(
        self,
        adapter: SourceAdapter,
        normalizers: NormalizerRegistry,
        corpus: list[Observation],
        dedup_policy: DuplicateResolutionPolicy | None = None,
        observer: PipelineObserver | None = None,
    ) -> None:
        self._adapter = adapter
        self._normalizers = normalizers
        self._corpus = corpus
        self._policy = dedup_policy
        self._observer = observer or NullObserver()

    def run(self) -> list[Observation]:
        raw_records = self._fetch()
        adapted_records = self._adapt(raw_records)
        normalized_records = self._normalize(adapted_records)
        observations = self._validate(normalized_records)
        deduped = self._dedup(observations)
        self._append(deduped)
        return deduped

    def _fetch(self) -> list[dict]:
        raw_records = self._adapter.fetch()
        self._observer.on_fetched(self._adapter.source_id, raw_records)
        return raw_records

    def _adapt(self, raw_records: list[dict]) -> list[RawRecord]:
        adapted = self._adapter.adapt(raw_records)
        self._observer.on_adapted(self._adapter.source_id, adapted)
        return adapted

    def _normalize(self, records: list[RawRecord]) -> list[RawRecord]:
        normalized = [self._normalizers.normalize(record) for record in records]
        self._observer.on_normalized(self._adapter.source_id, normalized)
        return normalized

    def _validate(self, records: list[RawRecord]) -> list[Observation]:
        return [Observation(**record) for record in records]

    def _dedup(self, observations: list[Observation]) -> list[Observation]:
        """DECIDE, then APPLY — the two used to be one call (C2, 2026-07-30).

        `policy.resolve()` is pure, so calling it is free; every corpus write
        happens here, in this one method. Resolutions are computed and applied
        one candidate at a time, in list order, because a decision depends on
        what earlier candidates in the same batch already put in the corpus.

        WHERE IDEMPOTENCY LIVES NOW. Re-running an adapter against an
        already-populated corpus still re-offers rows, so the property still
        has to hold — it moved, it did not disappear. It is now STRUCTURAL
        rather than a pair of defensive patches:

          * "this exact record is already here" is the `AlreadyPresent`
            variant, and the guard is simply that this method has no branch
            writing anything for it. Previously an early `return False` that
            read like "not a duplicate".
          * "don't record the same provenance link twice" is folded into the
            pure merge computation, so `merged` is already correct when it
            arrives here; applying the same Resolution twice writes the same
            row. Previously an `if not already_linked` guard around a mutation.

        Both are covered by tests that fail when either is removed (see
        `test_dedup_rules.py` and `test_corpus_builder.py`'s idempotency
        tests)."""
        if self._policy is None:
            return observations
        kept: list[Observation] = []
        for observation in observations:
            resolution = self._policy.resolve(observation)
            if isinstance(resolution, Admit):
                kept.append(observation)
            elif isinstance(resolution, (AbsorbInto, Replace)):
                self._corpus[self._corpus.index(resolution.existing)] = resolution.merged
            # AlreadyPresent: deliberately nothing — see the docstring above.
            self._observer.on_resolved(self._adapter.source_id, resolution)
        return kept

    def _append(self, observations: list[Observation]) -> None:
        self._corpus.extend(observations)
        self._observer.on_admitted(self._adapter.source_id, observations)
