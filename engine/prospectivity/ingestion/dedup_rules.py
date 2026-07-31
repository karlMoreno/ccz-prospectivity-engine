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

from engine.prospectivity.domain.evidence import EvidenceClass, QAStatus, QualityGrade
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


def _qa_severity(status: QAStatus) -> int:
    """QA verdict severity, mirroring E1.2's screening precedence
    (normalizer_registry._SCREENING_MAY_OVERWRITE): "fail" is terminal and
    outranks "flagged"; pass/pending are the unadjudicated baseline. Used by
    _merge to keep a verdict from being erased by dedup."""
    return {QAStatus.FAIL: 2, QAStatus.FLAGGED: 1}.get(QAStatus(status), 0)


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
    """⚠ THIS CLASS MUTATES THE CORPUS. It is an admission POLICY, not a
    predicate — read this before calling `is_satisfied_by`.

    On a duplicate match, `is_satisfied_by(candidate)` may:

      - REPLACE the matched corpus row in place, when the candidate outranks it
        on `quality_grade` (the candidate's values become the survivor's);
      - MERGE fields from the loser into the survivor — gap-fill only, never
        overwriting a non-null survivor value (D1);
      - APPEND to the survivor's `notes` a provenance link naming the absorbed
        row, and its `duplicate_group_id`;
      - ESCALATE the survivor's `qa_status` to the more severe of the pair, so
        a `fail`/`flagged` verdict cannot be erased by dedup (2026-07-30).

    ...and then return **False**, which here means "the corpus slot already
    holds the final row — do not also append this candidate", NOT "this
    candidate is uninteresting". Returning False is how the merge is committed.

    `corpus` is a LIVE reference (the same list `IngestionPipeline` appends
    into), which is what makes the decision visible to every subsequent adapter
    run against the same corpus.

    THE IDEMPOTENCY GUARDS ARE LOAD-BEARING, NOT DEFENSIVE. Two of them exist,
    and removing either reintroduces a bug that shipped:

      1. `_merge` refuses to re-append a provenance link already present.
         Without it, every `build_corpus()` re-run grew each merged row's
         `notes` (1 link -> 3 after two runs), while the row COUNT stayed
         correct — so the length-only idempotency test passed throughout.
      2. `is_satisfied_by` short-circuits when the candidate IS the corpus row
         (same source_id + source_record_id). Without it, a re-run made a row
         record itself as "duplicate of <its own source_record_id>".

    Both are covered by tests that fail when the guard is removed
    (`test_dedup_rules.py`'s idempotency tests, `test_corpus_builder.py`'s
    strengthened `..._adds_nothing`). They make repeated evaluation SAFE; they
    do not make it FREE, and they do not make this class a predicate. See
    docs/PATTERNS.md §3.1 and specification.py's ABC docstring.

    Dedup rules 1 & 2 (DOMES families / NOAA-PANGAEA mirrors) are the domain
    rules this implements."""

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

        # QA VERDICTS ARE STICKY ACROSS A MERGE (2026-07-30).
        #
        # The bug this fixes: qa_status is never null, so the gap-fill above
        # could never carry it — and survivorship is decided by quality_grade,
        # which says nothing about QA. So a row adjudicated qa_status="fail"
        # that lost the slot to a higher-grade candidate had its verdict
        # ERASED: the survivor came out "pending" and TRAINING-ELIGIBLE, with
        # notes recording only "duplicate of ...", no trace of the failure.
        # Whether a fail survived was decided by an unrelated field.
        #
        # The rule: the merged row carries the MOST SEVERE status of the pair,
        # using E1.2's established precedence (fail > flagged > pass/pending —
        # the same ordering apply_screening's _SCREENING_MAY_OVERWRITE
        # encodes). A merge may replace a failed row's VALUES with a better
        # measurement's; it may not discard its VERDICT.
        #
        # WHY ESCALATE — stated honestly, because the obvious justification is
        # weaker than it looks (sharpened 2026-07-30):
        #
        # The motivating case is STATION-level failure: a failed box-core
        # recovery (D5.3, SO268/1_12-2) taints any record of that station, so
        # the verdict must propagate. But that case does NOT currently need
        # this rule — [01] and [05] each detect the "failed" header COMMENT
        # independently (D8-A), so both sides of the pair already carry
        # qa_status="flagged" and the escalation is a no-op there. Verified:
        # SO268/1_12-2 is the only flagged event, flagged on both sides.
        #
        # Meanwhile the only fail-GENERATOR that exists in code today is D6
        # (mass_normalizer.py: sampled_area_m2 <= 0), which is RECORD-level —
        # one source's corrupt transcription — and it does not fire on either
        # wired source (both use a static 0.25 m2), so no real corpus row is
        # "fail" at all right now. Record-level is exactly the case where
        # escalation is CONSERVATIVE rather than obviously correct: a good
        # measurement of the same station inherits a fail it did not earn.
        #
        # The rule is retained on the asymmetric-cost argument, not on the
        # station-level case: escalating wrongly loses one training row,
        # visibly and reversibly; not escalating trains the model on a bad
        # sample, silently. Given the corpus cannot tell the two apart, assume
        # the worse one.
        #
        # [GEOLOGY — ISAAC] A `qa_scope` field on the observation (record |
        # station) would let this rule read INTENT instead of assuming the
        # worst — escalate only station-scoped verdicts, leave record-scoped
        # ones with the record that earned them. That is a Contract 1 change
        # (schema version bump) and needs your call on whether the distinction
        # is reliably determinable at ingest. Until then the conservative
        # default stands.
        if _qa_severity(dropped.qa_status) > _qa_severity(survivor.qa_status):
            updates["qa_status"] = dropped.qa_status
            link_note += (
                f"; qa_status escalated {survivor.qa_status.value} -> "
                f"{dropped.qa_status.value} from {dropped.source_record_id}"
            )

        updates["duplicate_group_id"] = group_id
        # IDEMPOTENCY (2026-07-29, E1.5 follow-up): only append a provenance
        # link that isn't already recorded. The gap-fill above is naturally
        # idempotent (it only ever fills a None), but the notes append was not
        # — merging the same pair twice duplicated the link text. That was a
        # real defect, not a hypothetical: build_corpus() documents itself as
        # safe to re-run against the same corpus, and each re-run grew every
        # merged row's notes while the row COUNT stayed correct, so the
        # length-only idempotency test never saw it.
        already_linked = survivor.notes is not None and (
            f"duplicate of {dropped.source_record_id}" in survivor.notes
        )
        if not already_linked:
            updates["notes"] = f"{survivor.notes}; {link_note}" if survivor.notes else link_note
        return survivor.model_copy(update=updates)

    def is_satisfied_by(self, candidate: Observation) -> bool:
        existing = self._find_duplicate(candidate)
        if existing is None:
            return True
        # Same RECORD being re-offered, not a duplicate PAIR (2026-07-29, E1.5
        # follow-up). On a re-run of the same adapter against an
        # already-populated corpus, a candidate matches the very row it
        # produced last time. Merging that pair made the row record itself as
        # "duplicate of <its own source_record_id>" — corrupt provenance, and
        # invisible to a length-only idempotency check. Nothing to merge here:
        # the corpus already holds this record.
        if (
            candidate.source_id == existing.source_id
            and candidate.source_record_id == existing.source_record_id
        ):
            return False
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
