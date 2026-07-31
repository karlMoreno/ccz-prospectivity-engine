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
    └───────────────────────────┘        │  on_resolved/on_rejected  │
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
from engine.prospectivity.ingestion.resolution import (
    AbsorbInto,
    Admit,
    AlreadyPresent,
    Replace,
    Resolution,
)
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

    def on_resolved(self, source_id: str, resolution: Resolution) -> None:
        """The dedup decision for one candidate (C2, 2026-07-30). Replaced
        `on_absorbed`, which announced only that SOMETHING was dropped and
        left the recorder to infer what it meant."""

    def on_admitted(self, source_id: str, observations: list[Observation]) -> None: ...


class NullObserver(PipelineObserver):
    """The default. Exists so the pipeline can always call an observer without
    a `if self._observer is not None` branch at every step — Null Object, the
    companion pattern that keeps Observer from leaking conditionals into the
    Template Method."""


@dataclass
class SourceRecord:
    """What the observer SAW happen to one source.

    Dispositions are now OBSERVED, not inferred (C2, 2026-07-30). Before this,
    the recorder only learned that something had been dropped, so the manifest
    had to recompute `admitted`/`absorbed` by counting the finished corpus and
    subtracting — and an earlier version of that inference, based on append
    order, was wrong: the dedup merge writes a winning row into the loser's
    slot without appending it, so attribution flipped when adapter order
    changed while the corpus stayed identical (found by the reversed-order
    manifest test, 2026-07-29).

    `Replace` is what made this hard, and it is now explicit: the candidate's
    source gains a row and the displaced row's source loses one. Booking both
    sides as they are decided makes these tallies match the finished corpus
    regardless of order, with no subtraction anywhere.
    """

    source_id: str
    fetched_rows: int = 0
    adapted_records: int = 0
    normalized_records: int = 0
    rejected_rows: int = 0
    adapted_by_evidence_class: dict[str, int] = field(default_factory=dict)

    # Dispositions, OBSERVED from the Resolution rather than inferred (C2).
    admitted_rows: int = 0
    absorbed_rows: int = 0
    already_present_rows: int = 0
    admitted_by_evidence_class: dict[str, int] = field(default_factory=dict)
    absorbed_by_evidence_class: dict[str, int] = field(default_factory=dict)


class ProvenanceRecorder(PipelineObserver):
    """Accumulates per-source counts across every pipeline run it observes.

    One recorder instance is shared across all of a build's adapters (the way
    the dedup policy is), so it sees the whole corpus assembly and can
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

    @staticmethod
    def _bump(counts: dict[str, int], evidence_class: str, delta: int) -> None:
        """Add `delta`, then DROP the key if it nets to zero.

        The prune is not cosmetic. A `Replace` decrements the displaced
        source's count, so a source that was admitted and then wholly
        displaced ends at zero — and `{"MASS": 0}` is a different dict from
        `{}` even though it is the same fact. Without this, the manifest's
        content_hash differed between a forward and a reversed build purely by
        dict shape, while every published number was identical. Caught by the
        order-invariance test, 2026-07-30."""
        if not delta:
            return
        total = counts.get(evidence_class, 0) + delta
        if total:
            counts[evidence_class] = total
        else:
            counts.pop(evidence_class, None)

    def _tally(self, source_id: str, evidence_class: str, *, admitted: int, absorbed: int) -> None:
        record = self._record(source_id)
        record.admitted_rows += admitted
        record.absorbed_rows += absorbed
        self._bump(record.admitted_by_evidence_class, evidence_class, admitted)
        self._bump(record.absorbed_by_evidence_class, evidence_class, absorbed)

    def on_resolved(self, source_id: str, resolution: Resolution) -> None:
        """Record the disposition the policy actually decided.

        The one subtlety is `Replace`: the candidate takes the slot, so its
        source gains an admitted row AND the displaced row's source loses one
        — it was admitted earlier in this same build and is no longer in the
        corpus. Booking both sides is what makes the tallies match the
        finished corpus regardless of adapter order, which is exactly what the
        manifest used to have to recompute (and got wrong once)."""
        evidence_class = resolution.candidate.evidence_class.value
        if isinstance(resolution, Admit):
            self._tally(source_id, evidence_class, admitted=1, absorbed=0)
        elif isinstance(resolution, AbsorbInto):
            self._tally(source_id, evidence_class, admitted=0, absorbed=1)
        elif isinstance(resolution, Replace):
            self._tally(source_id, evidence_class, admitted=1, absorbed=0)
            displaced = resolution.existing
            self._tally(displaced.source_id, displaced.evidence_class.value, admitted=-1, absorbed=1)
        elif isinstance(resolution, AlreadyPresent):
            self._record(source_id).already_present_rows += 1

    def on_admitted(self, source_id: str, observations: list[Observation]) -> None:
        """The append step. Dispositions are recorded in on_resolved; this
        exists so an observer can still see the batch boundary."""

    def sources(self) -> list[SourceRecord]:
        """Every source observed, INCLUDING ones whose rows were all absorbed
        and therefore carry no `source_id` in the corpus."""
        return list(self._sources.values())
