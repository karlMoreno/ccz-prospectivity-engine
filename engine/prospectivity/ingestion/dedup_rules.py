"""Concrete dedup policy (Phase 1, E1.3; restructured C2 2026-07-30), implementing
normalization.yaml's `deduplication:` block (Contract 7) as composable
predicates over an Observation, per specification.py's frozen ABC.

`DuplicateResolutionPolicy` implements rules 1 and 2 together (DOMES
families dedupe by cruise+station/event+coords+date, NOT DOI; NOAA/PANGAEA
mirrors prefer the clearer record but retain both provenance links) — their
underlying mechanics are identical (same key match, same survivor rule), so
one class serves both named rules. Rules 4 and 5 (GRID never merged with an
observed station; COVER/COUNT never merged with MASS) are NOT separate
separate rules — they're expressed as `_comparable_evidence()`, a guard on
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
aggregated [05] row reaches this policy it's already one row per
event — there is nothing left for dedup to collapse.

    ┌────────────────────────────────────────────────────────────┐
    │             DuplicateResolutionPolicy(corpus)                  │
    │  resolve(candidate) -> Resolution:   # PURE: reads, never writes │
    │    existing = _find_duplicate(candidate)  # scans the live corpus │
    │    if existing is None:      return Admit(...)                    │
    │    if existing IS candidate: return AlreadyPresent(...)           │
    │    survivor = candidate if quality(candidate) > quality(existing) │
    │               else existing               # existing keeps ties   │
    │    merged = _build_merge(survivor, loser)  # D1 gap-fill + D4     │
    │             provenance + sticky qa_status, all computed, none     │
    │             applied                                               │
    │    return Replace(...) if candidate won else AbsorbInto(...)      │
    └────────────────────────────────────────────────────────────┘
              │
              ▼  IngestionPipeline._dedup APPLIES the decision
       corpus[index of existing] = resolution.merged

Survivor precedence (confirmed with the engineer of record, 2026-07-27):
highest `quality_grade` wins (A > B > C); ties (the common case today, since
E1.2's normalizers set one quality_grade default per evidence class,
independent of source) go to whichever row was accepted first.

Merge-on-dedup (D1) and symmetric provenance (D4) — confirmed with the
engineer of record, 2026-07-27 review, sharing one code path
(`_build_merge`, called from `resolve` regardless of which side wins) since both
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
from engine.prospectivity.ingestion.resolution import (
    AbsorbInto,
    Admit,
    AlreadyPresent,
    Replace,
    Resolution,
)

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


class DuplicateResolutionPolicy:
    """Decides what should happen to one candidate observation; changes
    nothing. `IngestionPipeline._dedup` applies the returned Resolution.

    Replaced `DuplicateStationSpecification` on 2026-07-30 (C2 refactor,
    docs/PATTERNS.md §3.0). The old class implemented a `Specification` ABC and
    exposed `is_satisfied_by(candidate) -> bool`, but was neither composable
    nor a predicate: it read the corpus and, on a match, rewrote a row in place
    and returned False to COMMIT that. Two calls to something named
    `is_satisfied_by` were assumed to be free, and that assumption produced a
    real bug (E1.5). `resolve()` is a pure function of (candidate, corpus): it
    is safe to call any number of times, and the mutation it implies is
    explicit in the value object it returns.

        resolve(candidate) -> Admit | AlreadyPresent | AbsorbInto | Replace

    The five effects that used to be hidden are now all named on the
    Resolution: which corpus row is affected (`existing`), what the slot must
    hold (`merged`), which fields were gap-filled (`donated_fields`), the
    provenance link (`note`), and the sticky QA verdict (`escalated_status`).

    Dedup rules 1 & 2 (DOMES families / NOAA-PANGAEA mirrors) are the domain
    rules this implements; rules 4 & 5 live in `_comparable_evidence`, and
    rule 3 is handled upstream by `NoduleAggregateAdapter`."""

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

    def _build_merge(
        self, survivor: Observation, dropped: Observation
    ) -> tuple[Observation, tuple[str, ...], str | None, QAStatus | None]:
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
        escalated_status: QAStatus | None = None
        if _qa_severity(dropped.qa_status) > _qa_severity(survivor.qa_status):
            escalated_status = QAStatus(dropped.qa_status)
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
        applied_note: str | None = None
        if not already_linked:
            applied_note = link_note
            updates["notes"] = f"{survivor.notes}; {link_note}" if survivor.notes else link_note
        return (
            survivor.model_copy(update=updates),
            tuple(sorted(donated_fields)),
            applied_note,
            escalated_status,
        )

    def resolve(self, candidate: Observation) -> Resolution:
        """PURE. Reads the corpus, decides, returns — never writes.

        Safe to call any number of times for the same candidate: the returned
        Resolution is a function of (candidate, current corpus contents), so
        repeated calls against an unchanged corpus produce equal decisions."""
        existing = self._find_duplicate(candidate)
        if existing is None:
            return Admit(candidate=candidate)

        # Same RECORD re-offered, not a duplicate PAIR. On a re-run of the
        # same adapter against an already-populated corpus, a candidate matches
        # the very row it produced last time. Merging that pair made the row
        # record itself as "duplicate of <its own source_record_id>" — corrupt
        # provenance, invisible to a length-only idempotency check (E1.5).
        # Now it is a NAMED OUTCOME rather than an early `return False`, so the
        # pipeline can distinguish "nothing to do" from "absorbed by another
        # source" — which is what the recorder needs to stop inferring.
        if (
            candidate.source_id == existing.source_id
            and candidate.source_record_id == existing.source_record_id
        ):
            return AlreadyPresent(candidate=candidate, existing=existing)

        candidate_wins = _quality_rank(candidate.quality_grade) > _quality_rank(
            existing.quality_grade
        )
        # Ties go to first-encountered, i.e. the row already in the corpus.
        survivor, dropped = (candidate, existing) if candidate_wins else (existing, candidate)
        merged, donated_fields, note, escalated_status = self._build_merge(survivor, dropped)

        outcome = Replace if candidate_wins else AbsorbInto
        return outcome(
            candidate=candidate,
            existing=existing,
            merged=merged,
            donated_fields=donated_fields,
            note=note,
            escalated_status=escalated_status,
        )
