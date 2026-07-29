"""Concrete dedup Specifications — SPECIFICATION (Phase 1, E1.3), implementing
normalization.yaml's `deduplication:` block (Contract 7) as composable
predicates over an Observation, per specification.py's frozen ABC.

`DuplicateStationSpecification` implements rules 1 and 2 together (DOMES
families dedupe by cruise+station/event+coords+date, NOT DOI; NOAA/PANGAEA
mirrors prefer the clearer record but retain both provenance links) — their
underlying mechanics are identical (same key match, same survivor rule), so
one class serves both named rules. Rules 4 and 5 (GRID never merged with an
observed station; COVER/COUNT never merged with MASS) are NOT separate
Specifications — they're expressed as `_comparable_evidence()`, a guard on
what counts as a "match" at all, because a single box-core event fans out
into MASS+COUNT+COVER RawRecords that legitimately share the same
cruise/station/event/coords/date (E1.1's `_column_mapping.build_records`) —
without this guard, a box-core event's own COVER row would look like a
"duplicate" of its own MASS row. GRID additionally requires the SAME
source_id to match another GRID row (D3, 2026-07-27 review) — two different
compiled grids ([18] vs [19]) covering the same cell are two independent
model products, not two observations of one sample; see
`_comparable_evidence()` for the full reasoning.

Rule 3 (individual nodules [05] nested within box-core events [01]: the
event is the sample) is deliberately NOT implemented here at all — per the
engineer of record's decision (2026-07-27 E1.3 review), it's a many-to-one
aggregation (sum nodule masses per event, derive mean_nodule_mass_g), which
doesn't fit a per-observation boolean predicate. That lives in
`nodule_aggregate_adapter.py`, upstream of dedup, so by the time an
aggregated [05] row reaches this Specification it's already one row per
event — there is nothing left for dedup to collapse.

    ┌────────────────────────────────────────────────────────────┐
    │            DuplicateStationSpecification(corpus)               │
    │  is_satisfied_by(candidate):                                    │
    │    existing = _find_duplicate(candidate)  # scans the live corpus │
    │    if existing is None: return True          # not a duplicate    │
    │    survivor = candidate if quality(candidate) > quality(existing) │
    │               else existing               # existing keeps ties   │
    │    merged = _merge(survivor, loser)   # D1: gap-fill: donate every │
    │             non-null field the loser carries that survivor lacks; │
    │             D4: record loser's provenance regardless of direction │
    │    corpus[index of existing] = merged; return False               │
    │        # (False always: the corpus slot already holds the final   │
    │        # row, whichever one won -- the pipeline must not ALSO     │
    │        # append the raw candidate via its normal append step)     │
    └────────────────────────────────────────────────────────────┘

Survivor precedence (confirmed with the engineer of record, 2026-07-27):
highest `quality_grade` wins (A > B > C); ties (the common case today, since
E1.2's normalizers set one quality_grade default per evidence class,
independent of source) go to whichever row was accepted first.

Merge-on-dedup (D1) and symmetric provenance (D4) — confirmed with the
engineer of record, 2026-07-27 review, sharing one code path (`_merge`,
called from `is_satisfied_by` regardless of which side wins) since both
decisions apply at the exact moment a survivor is chosen: the survivor
absorbs any non-null field the dropped row carries that the survivor itself
lacks (gap-fill only — a non-null value already on the survivor is never
overwritten, so merge cannot arbitrate a disagreement, only fill an
absence), and the survivor's `notes` + `duplicate_group_id` record the
dropped row's `source_id`/`source_record_id` — regardless of whether the
survivor is the row already in the corpus or the newly-arriving candidate.
Before D1/D4, quality-tie-break-goes-to-first-encountered meant `[01]`'s
box-core MASS row (which never carries `mean_nodule_mass_g`) would silently
out-survive `[05]`'s aggregated nodule MASS row (which does) whenever both
described the same event — exactly the field `CountNormalizer`'s row-only
gate depends on. The dropped row itself still does not remain as a second
corpus row; only the merged copy of the survivor does.

Key matching (confirmed with the engineer of record, 2026-07-27): a
null-tolerant per-field match on normalization.yaml's `key:` list
(cruise/station_id/event_id/sample_datetime_utc) — a field only blocks a
match if BOTH sides have it and they disagree; a missing field on either
side never blocks a match on its own. Coordinates always use
`coordinate_tolerance_deg` (a radius, not exact equality) — read from
normalization.yaml, not duplicated here. Known limitation: two otherwise
unrelated rows with every key field null and coordinates within ~100m of
each other would be treated as duplicates; this is undocumented in the
contract and considered low-risk (real cruise samples almost always carry a
cruise/date; GRID cells matching other nearby GRID cells is arguably
correct, not a bug).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import EvidenceClass, QualityGrade
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._contract_paths import load_normalization_yaml
from engine.prospectivity.ingestion.specification import Specification

_KEY_FIELDS = ("cruise", "station_id", "event_id", "sample_datetime_utc")

_QUALITY_RANK = {QualityGrade.A: 3, QualityGrade.B: 2, QualityGrade.C: 1}

# D4: computed explicitly by _merge() itself (the new provenance link/notes
# text), never gap-filled verbatim from the dropped row's own values.
_PROVENANCE_FIELDS = {"duplicate_group_id", "notes"}


def default_coordinate_tolerance_deg() -> float:
    """normalization.yaml's `deduplication.coordinate_tolerance_deg` (~100m),
    loaded rather than duplicated as a Python literal."""
    return load_normalization_yaml()["deduplication"]["coordinate_tolerance_deg"]


def _quality_rank(grade: QualityGrade | None) -> int:
    return 0 if grade is None else _QUALITY_RANK[grade]


def _comparable_evidence(a: Observation, b: Observation) -> bool:
    """Rules 4 & 5: GRID is a prior/benchmark, never merged with an observed
    station; COVER/COUNT are never merged with MASS. Requiring the SAME
    evidence_class implements both as a single check — it blocks GRID from
    ever matching a MASS/COUNT/COVER/GRADE row (rule 4) and blocks
    COVER/COUNT from ever matching MASS (rule 5), while still allowing two
    MASS rows (or two COUNT rows, etc.) to match each other, which
    idempotency depends on for observed sources, and cross-source dedup
    (rule 1: DOMES families dedupe by key, not DOI) depends on generally.

    GRID is the one exception to "same evidence_class is enough" (D3,
    2026-07-27 review): two GRID rows must ALSO share source_id to be
    comparable. A compiled grid ([18] TS-6, [19] Washburn, ...) is a
    distinct MODEL PRODUCT, not a sample — two different grids covering the
    same cell are two independent estimates worth comparing (that's the
    whole point of a benchmark), not two observations of one physical
    sample that should be deduped down to one. Without this, [19]'s cells
    would dedupe against [18]'s nearby cells (both often have sparse
    cruise/station/event/date, so the null-tolerant key match matches on
    coordinates alone) and silently drop benchmark data instead of keeping
    it for TS6Reference/compare_to_ts6 to use. GRID-vs-GRID matching
    *within* the same source_id is unaffected — that's what makes
    re-ingesting a GRID source idempotent (see the module docstring)."""
    if a.evidence_class != b.evidence_class:
        return False
    if a.evidence_class == EvidenceClass.GRID:
        return a.source_id == b.source_id
    return True


def _within_coordinate_tolerance(a: Observation, b: Observation, tolerance_deg: float) -> bool:
    return (
        abs(a.latitude - b.latitude) <= tolerance_deg
        and abs(a.longitude - b.longitude) <= tolerance_deg
    )


def _same_station(a: Observation, b: Observation, tolerance_deg: float) -> bool:
    """normalization.yaml's dedup `key:` — null-tolerant per field, coordinates
    via tolerance radius (see module docstring for the confirmed semantics)."""
    for field in _KEY_FIELDS:
        value_a, value_b = getattr(a, field), getattr(b, field)
        if value_a is not None and value_b is not None and value_a != value_b:
            return False
    return _within_coordinate_tolerance(a, b, tolerance_deg)


class DuplicateStationSpecification(Specification):
    """DOMES-family / NOAA-PANGAEA-mirror dedup (rules 1 & 2): is `candidate`
    NOT a duplicate of a station already in `corpus`? `corpus` is a live
    reference (the same list `IngestionPipeline` appends into), so this
    Specification's decision — and, when a duplicate is found, its in-place
    replacement of the corpus slot with a merged survivor (D1/D4) — is
    visible to every subsequent adapter run against the same corpus, which is
    what makes re-running an adapter against an already-populated corpus
    idempotent."""

    def __init__(self, corpus: list[Observation], tolerance_deg: float | None = None) -> None:
        self._corpus = corpus
        self._tolerance_deg = (
            tolerance_deg if tolerance_deg is not None else default_coordinate_tolerance_deg()
        )

    def _find_duplicate(self, candidate: Observation) -> Observation | None:
        for existing in self._corpus:
            if _comparable_evidence(candidate, existing) and _same_station(
                candidate, existing, self._tolerance_deg
            ):
                return existing
        return None

    def _merge(self, survivor: Observation, dropped: Observation) -> Observation:
        """D1 (merge-on-dedup): survivor absorbs any non-null field `dropped`
        carries that survivor lacks — gap-fill only; a non-null value already
        on survivor is never overwritten, so this cannot arbitrate a
        disagreement, only fill an absence. D4 (symmetric provenance): notes
        + duplicate_group_id record dropped's source, plus which fields (if
        any) were donated, regardless of which row is `survivor`."""
        updates: dict[str, object] = {}
        donated_fields: list[str] = []
        for field_name in Observation.model_fields:
            if field_name in _PROVENANCE_FIELDS:
                continue  # notes/duplicate_group_id are computed below, not gap-filled verbatim
            if getattr(survivor, field_name) is not None:
                continue  # never overwrite a non-null survivor value
            dropped_value = getattr(dropped, field_name)
            if dropped_value is not None:
                updates[field_name] = dropped_value
                donated_fields.append(field_name)

        group_id = survivor.duplicate_group_id or f"dupgrp_{survivor.source_record_id}"
        link_note = f"duplicate of {dropped.source_record_id} ({dropped.source_id})"
        if donated_fields:
            link_note += f"; merged fields: {', '.join(sorted(donated_fields))}"
        updates["duplicate_group_id"] = group_id
        updates["notes"] = f"{survivor.notes}; {link_note}" if survivor.notes else link_note
        return survivor.model_copy(update=updates)

    def is_satisfied_by(self, candidate: Observation) -> bool:
        existing = self._find_duplicate(candidate)
        if existing is None:
            return True
        if _quality_rank(candidate.quality_grade) > _quality_rank(existing.quality_grade):
            survivor, dropped = candidate, existing
        else:
            # existing wins (higher or equal quality; ties go to first-encountered).
            survivor, dropped = existing, candidate
        index = self._corpus.index(existing)
        self._corpus[index] = self._merge(survivor, dropped)
        # Always False: the corpus slot above already holds the final
        # (possibly merged) survivor, whichever row won. The pipeline's own
        # append step must not ALSO add the raw candidate — that would
        # either duplicate it (existing won) or add an un-merged copy
        # alongside the merged one already in the corpus (candidate won).
        return False
