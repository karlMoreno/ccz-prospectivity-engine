"""PipelineObserver / ProvenanceRecorder — OBSERVER.

The problem: `data/corpus/master_observations.csv` cannot answer "which
sources does this corpus draw on?" The Phase-1 audit found `[05]`
(`src_so268_nodules`) contributes 36 events' worth of `mean_nodule_mass_g`
yet appears nowhere in the CSV as a `source_id`, because dedup absorbed every
one of its rows into `[01]`'s. A reader of the CSV sees one source; two
contributed. That fact took a dedicated investigation to surface, and it
should have been a field in a build record.

Why OBSERVER and not a reporting method on the pipeline: `IngestionPipeline`
is a Template Method whose whole value is that the sequence is fixed and
readable. Growing a reporting responsibility inside it would (a) mix two
concerns in one class and (b) make every test that runs a pipeline care about
recording. Instead the pipeline announces what happened to a collaborator it
knows nothing about beyond this interface, and the DEFAULT collaborator does
nothing at all.

    ┌───────────────────────────┐        ┌──────────────────────────┐
    │    IngestionPipeline        │───────►│   PipelineObserver (ABC)  │
    │  (Template Method; emits    │ notify │  on_fetched/on_adapted/   │
    │   events, never reads them) │        │  on_normalized/on_admitted│
    └───────────────────────────┘        │  on_absorbed/on_rejected  │
                                           └──────────────────────────┘
                                              ▲                  ▲
                                    ┌────────────────┐  ┌──────────────────┐
                                    │ NullObserver    │  │ ProvenanceRecorder│
                                    │ (DEFAULT: no-op)│  │ (accumulates)     │
                                    └────────────────┘  └──────────────────┘

THE INVARIANT: recording never changes a pipeline decision. `NullObserver` is
the default so an un-observed pipeline behaves exactly as it did before this
module existed, and `test_corpus_manifest.py`'s no-op test proves a recorded
build and an unrecorded build produce a byte-identical corpus. Observers must
therefore never mutate what they are handed.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.source_adapter import RawRecord


class PipelineObserver(ABC):
    """Pipeline lifecycle events. Concrete no-ops rather than abstract methods
    on purpose: an observer that only cares about one event shouldn't have to
    implement six empty overrides, and a new event added later must not break
    every existing observer."""

    def on_fetched(self, source_id: str, raw_rows: list[dict]) -> None: ...

    def on_adapted(self, source_id: str, records: list[RawRecord]) -> None: ...

    def on_normalized(self, source_id: str, records: list[RawRecord]) -> None: ...

    def on_rejected(self, source_id: str, record: RawRecord, error: Exception) -> None: ...

    def on_absorbed(self, source_id: str, observation: Observation) -> None: ...

    def on_admitted(self, source_id: str, observations: list[Observation]) -> None: ...


class NullObserver(PipelineObserver):
    """The default. Exists so the pipeline can always call an observer without
    a `if self._observer is not None` branch at every step — Null Object, the
    companion pattern that keeps Observer from leaking conditionals into the
    Template Method."""


@dataclass
class SourceRecord:
    """What the observer SAW happen to one source, as raw pipeline events.

    These are process counts, not outcome counts, and the difference matters.
    `appended_rows` counts rows this source's own `_append` step added to the
    corpus list — which is NOT the same as "rows in the finished corpus
    carrying this source_id", because the dedup merge can later overwrite a
    corpus slot IN PLACE with a higher-quality row from a different source
    (D1/D4: the winner is written into the loser's slot and never appended).

    So attribution flips with adapter order here while the finished corpus
    stays identical — found by the reversed-order manifest test, 2026-07-29.
    The manifest therefore derives `admitted`/`absorbed` from the FINAL CORPUS
    (see corpus_manifest.build_corpus_manifest) and uses these event counts
    only for the stages the corpus cannot show: fetched, adapted, normalized,
    rejected.
    """

    source_id: str
    fetched_rows: int = 0
    adapted_records: int = 0
    normalized_records: int = 0
    rejected_rows: int = 0
    # Order-dependent process bookkeeping — see the class docstring. Never
    # published as "admitted"; the manifest recomputes that from the corpus.
    appended_rows: int = 0
    adapted_by_evidence_class: dict[str, int] = field(default_factory=dict)
    dropped_by_dedup_rows: int = 0


class ProvenanceRecorder(PipelineObserver):
    """Accumulates per-source counts across every pipeline run it observes.

    One recorder instance is shared across all of a build's adapters (the way
    the dedup Specification is), so it sees the whole corpus assembly and can
    report sources whose rows were entirely absorbed — the `[05]` case this
    module exists for.
    """

    def __init__(self) -> None:
        # Insertion-ordered: sources appear in the manifest in the order they
        # actually ran, which is REAL_ADAPTER_BUILDERS order.
        self._sources: dict[str, SourceRecord] = {}

    def _record(self, source_id: str) -> SourceRecord:
        return self._sources.setdefault(source_id, SourceRecord(source_id=source_id))

    def on_fetched(self, source_id: str, raw_rows: list[dict]) -> None:
        self._record(source_id).fetched_rows += len(raw_rows)

    def on_adapted(self, source_id: str, records: list[RawRecord]) -> None:
        record = self._record(source_id)
        record.adapted_records += len(records)
        for raw_record in records:
            evidence_class = str(raw_record.get("evidence_class"))
            record.adapted_by_evidence_class[evidence_class] = (
                record.adapted_by_evidence_class.get(evidence_class, 0) + 1
            )

    def on_normalized(self, source_id: str, records: list[RawRecord]) -> None:
        self._record(source_id).normalized_records += len(records)

    def on_rejected(self, source_id: str, record: RawRecord, error: Exception) -> None:
        self._record(source_id).rejected_rows += 1

    def on_absorbed(self, source_id: str, observation: Observation) -> None:
        # Dedup declined to append this row (it merged into a corpus row
        # instead). Order-dependent by itself — the manifest cross-checks it
        # against the finished corpus rather than publishing it directly.
        self._record(source_id).dropped_by_dedup_rows += 1

    def on_admitted(self, source_id: str, observations: list[Observation]) -> None:
        self._record(source_id).appended_rows += len(observations)

    def sources(self) -> list[SourceRecord]:
        """Every source observed, INCLUDING ones whose rows were all absorbed
        and therefore carry no `source_id` in the corpus."""
        return list(self._sources.values())
