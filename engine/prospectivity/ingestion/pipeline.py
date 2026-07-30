"""IngestionPipeline — TEMPLATE METHOD.

`run()` is the one fixed, honest sequence every source goes through:

    fetch -> adapt -> normalize -> validate -> dedup -> append

(The alpha proposal states this shorthand as "fetch→adapt→normalize→dedup→
validate→append." This implementation validates *before* deduping: the
Specification-based dedup rules (specification.py) match on typed fields —
parsed coordinates, parsed datetimes — so they need Observation objects, not
raw strings. Both orderings run entirely before `append`, so the corpus
guarantee is identical; flagged here because the contracts are frozen and any
reading of their order deserves to be explicit, not silent.)

This is Template Method by composition rather than subclassing: the sequence
itself never changes, but each step delegates to an injected Strategy
(SourceAdapter, a NormalizerRegistry of AbundanceNormalizer per evidence
class, an optional dedup Specification) so a new source or a new dedup rule
is a new object passed to the constructor, never a new subclass of the
pipeline.

    ┌─────────────────────────────────────────────────────────┐
    │                  IngestionPipeline.run()                   │
    │                                                             │
    │  fetch ──► adapt ──► normalize ──► validate ──► dedup ──►  │
    │   │          │           │             │           │   append
    │   ▼          ▼           ▼             ▼           ▼      │
    │ adapter   adapter   normalizers    Observation   dedup_    │
    │ .fetch()  .adapt()  .normalize()   (**record)     spec     │
    │                     (NormalizerRegistry;                    │
    │                      REGISTRY, ingestion/normalizer_registry.py) │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.normalizer_registry import NormalizerRegistry
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter
from engine.prospectivity.ingestion.specification import Specification
from engine.prospectivity.provenance.recorder import NullObserver, PipelineObserver


class IngestionPipeline:
    """Runs one SourceAdapter through fetch/adapt/normalize/validate/dedup/append.

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
        dedup_specification: Specification | None = None,
        observer: PipelineObserver | None = None,
    ) -> None:
        self._adapter = adapter
        self._normalizers = normalizers
        self._corpus = corpus
        self._dedup_specification = dedup_specification
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
        if self._dedup_specification is None:
            return observations
        # One is_satisfied_by call per observation, in list order — unchanged
        # from the comprehension this replaces. That matters: the dedup
        # Specification MUTATES the corpus as it goes (merging losers into
        # survivors), so both the number and the order of calls are part of
        # the behavior, not an implementation detail.
        kept: list[Observation] = []
        for observation in observations:
            if self._dedup_specification.is_satisfied_by(observation):
                kept.append(observation)
            else:
                self._observer.on_absorbed(self._adapter.source_id, observation)
        return kept

    def _append(self, observations: list[Observation]) -> None:
        self._corpus.extend(observations)
        self._observer.on_admitted(self._adapter.source_id, observations)
