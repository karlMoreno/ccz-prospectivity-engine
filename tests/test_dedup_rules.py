"""Real dedup Specification (SPECIFICATION, E1.3) tests — one per
normalization.yaml dedup rule, run directly against hand-built Observations
(rule 3's test lives in test_nodule_aggregate_adapter.py; see dedup_rules.py's
module docstring for why it isn't a Specification here at all).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import QAStatus
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.dedup_rules import DuplicateStationSpecification

_SHARED = dict(
    cruise="SO268",
    station_id="ST042",
    event_id="EV042BC",
    latitude=11.842,
    longitude=-118.512,
    sample_datetime_utc="2019-04-12T00:00:00Z",
    observation_or_prediction="observed",
    is_open=True,
    qa_status="pending",
)


def _obs(**overrides: object) -> Observation:
    fields = dict(_SHARED)
    fields.update(overrides)
    return Observation(**fields)


# --- rule 1: DOMES families dedupe by key, not DOI -------------------------


def test_domes_family_duplicate_by_key_not_doi_is_rejected() -> None:
    """Two different sources (different source_id/'DOI'), same station key ->
    the second one is recognized as a duplicate, not admitted as a second
    station, even though nothing about their source_id/DOI matches."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_domes_fewkes1980_MASS_000001",
        source_id="src_domes_fewkes1980",
        evidence_class="MASS",
        abundance_kg_m2=9.2,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(first)
    corpus.append(first)

    second = _obs(
        source_record_id="src_domes_piper1979_MASS_000001",
        source_id="src_domes_piper1979",  # different source entirely
        evidence_class="MASS",
        abundance_kg_m2=9.0,
        quality_grade="A",
    )
    assert not spec.is_satisfied_by(second)  # tie on quality -> first-encountered wins
    assert len(corpus) == 1


# --- rule 2: NOAA/PANGAEA mirrors: prefer clearer record, retain both links -


def test_higher_quality_grade_survivor_replaces_lower_quality_existing() -> None:
    """Post-D1/D4: is_satisfied_by ALWAYS returns False on a duplicate match
    (merged or not) -- the Specification replaces the corpus slot itself, so
    the pipeline's normal append step must not also add the raw candidate."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    weaker = _obs(
        source_record_id="src_noaa_mirror_MASS_000001",
        source_id="src_noaa_mirror",
        evidence_class="MASS",
        abundance_kg_m2=9.0,
        quality_grade="B",
    )
    assert spec.is_satisfied_by(weaker)
    corpus.append(weaker)

    clearer = _obs(
        source_record_id="src_pangaea_mirror_MASS_000001",
        source_id="src_pangaea_mirror",
        evidence_class="MASS",
        abundance_kg_m2=9.1,
        quality_grade="A",
    )
    assert not spec.is_satisfied_by(clearer)  # higher quality -> wins, but corpus already updated
    assert len(corpus) == 1  # weaker row replaced in place, not kept alongside
    survivor = corpus[0]
    assert survivor.source_record_id == "src_pangaea_mirror_MASS_000001"
    assert survivor.abundance_kg_m2 == 9.1
    assert survivor.quality_grade == "A"


def test_survivor_retains_provenance_link_to_the_dropped_duplicate() -> None:
    """Rule 2's "retain both provenance links": the surviving row records the
    dropped row's source, rather than keeping a second corpus row."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_noaa_mirror_MASS_000001",
        source_id="src_noaa_mirror",
        evidence_class="MASS",
        abundance_kg_m2=9.0,
        quality_grade="A",
    )
    corpus.append(first)

    duplicate = _obs(
        source_record_id="src_pangaea_mirror_MASS_000001",
        source_id="src_pangaea_mirror",
        evidence_class="MASS",
        abundance_kg_m2=9.05,
        quality_grade="A",  # tie -> existing (first) wins
    )
    assert not spec.is_satisfied_by(duplicate)
    survivor = corpus[0]
    assert survivor.duplicate_group_id is not None
    assert "src_pangaea_mirror_MASS_000001" in survivor.notes
    assert "src_pangaea_mirror" in survivor.notes


# --- rule 4: regional grids never merged with observed stations ------------


def test_grid_row_never_merged_with_an_observed_station() -> None:
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    mass_row = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(mass_row)
    corpus.append(mass_row)

    grid_row = _obs(
        source_record_id="src_ts6_grid_GRID_000001",
        source_id="src_ts6_grid",
        evidence_class="GRID",
        abundance_kg_m2=5.5,
        observation_or_prediction="compiled",
        quality_grade="C",
    )
    assert spec.is_satisfied_by(grid_row)  # not treated as a duplicate of the MASS row
    corpus.append(grid_row)
    assert len(corpus) == 2


def test_two_grid_rows_at_the_same_cell_still_dedupe_against_each_other() -> None:
    """Rule 4 says GRID is never merged with an OBSERVED station -- it does
    not exempt GRID from dedup entirely. Re-ingesting the same grid cell
    twice must still be recognized as a duplicate (this is what idempotency
    depends on for GRID sources)."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_ts6_grid_GRID_000001",
        source_id="src_ts6_grid",
        evidence_class="GRID",
        abundance_kg_m2=5.5,
        observation_or_prediction="compiled",
        quality_grade="C",
    )
    assert spec.is_satisfied_by(first)
    corpus.append(first)

    reingested = _obs(
        source_record_id="src_ts6_grid_GRID_000001_rerun",
        source_id="src_ts6_grid",
        evidence_class="GRID",
        abundance_kg_m2=5.5,
        observation_or_prediction="compiled",
        quality_grade="C",
    )
    assert not spec.is_satisfied_by(reingested)  # recognized as the same cell, not a 2nd row
    assert len(corpus) == 1


def test_grid_rows_from_different_sources_never_dedupe_even_at_the_same_cell() -> None:
    """D3 (2026-07-27 review): [18] TS-6 and [19] Washburn are independent
    compiled model products. Two grids covering the same cell are two
    independent estimates worth comparing, not two observations of one
    sample -- deduping them would silently delete benchmark data."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    ts6_cell = _obs(
        source_record_id="src_ts6_grid_GRID_000001",
        source_id="src_ts6_grid",
        evidence_class="GRID",
        abundance_kg_m2=5.5,
        observation_or_prediction="compiled",
        quality_grade="C",
    )
    assert spec.is_satisfied_by(ts6_cell)
    corpus.append(ts6_cell)

    washburn_cell = _obs(
        source_record_id="src_washburn2021_grid_GRID_000001",
        source_id="src_washburn2021_grid",
        evidence_class="GRID",
        abundance_kg_m2=5.7,  # a different estimate for the same cell
        observation_or_prediction="interpolated",
        quality_grade="C",
    )
    assert spec.is_satisfied_by(washburn_cell)  # a different model product, not a duplicate
    corpus.append(washburn_cell)
    assert len(corpus) == 2  # neither dropped


# --- rule 5: image cover/count != recovered mass ----------------------------


def test_cover_row_never_merged_with_a_mass_row_from_the_same_event() -> None:
    """A single box-core event's own MASS and COVER RawRecords legitimately
    share cruise+station+event+coords+date (E1.1's fan-out) -- they must NOT
    be treated as duplicates of each other."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    mass_row = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(mass_row)
    corpus.append(mass_row)

    cover_row = _obs(
        source_record_id="src_so268_boxcore_COVER_000001",
        source_id="src_so268_boxcore",
        evidence_class="COVER",
        visible_cover_percent=35.0,
        quality_grade="B",
    )
    assert spec.is_satisfied_by(cover_row)  # not a duplicate of the MASS row
    corpus.append(cover_row)
    assert len(corpus) == 2


# --- null-tolerant key matching (confirmed 2026-07-27) ----------------------


def test_null_tolerant_key_match_still_catches_a_duplicate_with_a_blank_event_id() -> None:
    """A source that only reports station_id (event_id blank) must still be
    recognized as a duplicate of a source that reports both, provided nothing
    they BOTH report disagrees."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    with_event_id = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    corpus.append(with_event_id)

    blank_event_id = _obs(
        source_record_id="src_domes_fewkes1980_MASS_000001",
        source_id="src_domes_fewkes1980",
        evidence_class="MASS",
        event_id=None,  # this source never reported an event_id
        abundance_kg_m2=14.5,
        quality_grade="A",
    )
    assert not spec.is_satisfied_by(blank_event_id)  # still recognized as a duplicate


def test_disagreeing_non_null_field_blocks_the_match() -> None:
    """If both sides DO report a field and it disagrees, that's not a
    null-tolerant pass -- it's a real disagreement, and the rows are distinct
    stations."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    corpus.append(first)

    different_event = _obs(
        source_record_id="src_so268_boxcore_MASS_000002",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        event_id="EV999OTHER",  # explicitly disagrees with EV042BC
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(different_event)  # a distinct station, not a duplicate


# --- D1: merge-on-dedup (confirmed 2026-07-27) ------------------------------


def test_merge_fills_the_survivors_missing_mean_nodule_mass_g_forward_order() -> None:
    """The real-shape bug this decision fixes: [01]'s box-core MASS row never
    carries mean_nodule_mass_g; [05]'s aggregated nodule MASS row does.
    Whichever order they arrive in, the surviving row must end up with it --
    exactly the field CountNormalizer's row-only gate depends on."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    boxcore_shaped = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        nodule_mass_kg=3.65,
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(boxcore_shaped)
    corpus.append(boxcore_shaped)

    nodules_shaped = _obs(
        source_record_id="src_so268_nodules_MASS_000001",
        source_id="src_so268_nodules",
        evidence_class="MASS",
        nodule_mass_kg=3.65,
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        mean_nodule_mass_g=45.2,
        quality_grade="A",  # tie -> first-encountered (boxcore_shaped) wins
    )
    assert not spec.is_satisfied_by(nodules_shaped)

    assert len(corpus) == 1
    survivor = corpus[0]
    assert survivor.mean_nodule_mass_g == 45.2  # gap-filled from the dropped row


def test_merge_fills_the_survivors_missing_mean_nodule_mass_g_reversed_order() -> None:
    """Same scenario, insertion order reversed -- completeness must not
    depend on which row arrived first."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    nodules_shaped = _obs(
        source_record_id="src_so268_nodules_MASS_000001",
        source_id="src_so268_nodules",
        evidence_class="MASS",
        nodule_mass_kg=3.65,
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        mean_nodule_mass_g=45.2,
        quality_grade="A",
    )
    assert spec.is_satisfied_by(nodules_shaped)
    corpus.append(nodules_shaped)

    boxcore_shaped = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        nodule_mass_kg=3.65,
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        quality_grade="A",  # tie -> first-encountered (nodules_shaped) wins
    )
    assert not spec.is_satisfied_by(boxcore_shaped)

    assert len(corpus) == 1
    survivor = corpus[0]
    assert survivor.mean_nodule_mass_g == 45.2  # still present, regardless of arrival order


def test_merge_never_overwrites_a_non_null_survivor_value() -> None:
    """Merge fills gaps; it does not arbitrate disagreements. A field
    already non-null on the survivor keeps its own value even when the
    dropped row disagrees -- no silent value substitution."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_so268_boxcore_MASS_000001",
        source_id="src_so268_boxcore",
        evidence_class="MASS",
        nodule_mass_kg=3.65,
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    corpus.append(first)

    duplicate_with_different_value = _obs(
        source_record_id="src_so268_nodules_MASS_000001",
        source_id="src_so268_nodules",
        evidence_class="MASS",
        nodule_mass_kg=99.0,  # disagrees with the survivor's 3.65
        sampled_area_m2=0.25,
        abundance_kg_m2=14.6,
        quality_grade="A",  # tie -> first (existing) wins
    )
    assert not spec.is_satisfied_by(duplicate_with_different_value)

    survivor = corpus[0]
    assert survivor.nodule_mass_kg == 3.65  # survivor's own value kept, not overwritten


# --- D4: symmetric provenance (confirmed 2026-07-27) ------------------------


def test_provenance_recorded_when_existing_row_wins() -> None:
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_a_MASS_000001",
        source_id="src_a",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
    )
    corpus.append(first)

    duplicate = _obs(
        source_record_id="src_b_MASS_000001",
        source_id="src_b",
        evidence_class="MASS",
        abundance_kg_m2=14.5,
        quality_grade="B",  # lower -> existing wins
    )
    assert not spec.is_satisfied_by(duplicate)

    survivor = corpus[0]
    assert survivor.source_record_id == "src_a_MASS_000001"  # existing keeps its identity
    assert "src_b_MASS_000001" in survivor.notes
    assert "src_b" in survivor.notes


def test_provenance_recorded_when_candidate_wins() -> None:
    """D4's fix: before this decision, this direction recorded NOTHING --
    the existing row was simply removed with no link to it at all."""
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    first = _obs(
        source_record_id="src_a_MASS_000001",
        source_id="src_a",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="B",
    )
    corpus.append(first)

    duplicate = _obs(
        source_record_id="src_b_MASS_000001",
        source_id="src_b",
        evidence_class="MASS",
        abundance_kg_m2=14.5,
        quality_grade="A",  # higher -> candidate wins
    )
    assert not spec.is_satisfied_by(duplicate)

    assert len(corpus) == 1
    survivor = corpus[0]
    assert survivor.source_record_id == "src_b_MASS_000001"  # candidate is now the survivor
    assert "src_a_MASS_000001" in survivor.notes
    assert "src_a" in survivor.notes


# --- E1.5 follow-up: the stateful Specification must be idempotent ----------


def test_calling_is_satisfied_by_twice_on_the_same_duplicate_is_idempotent() -> None:
    """`is_satisfied_by` is NOT a pure predicate — on a match it merges the
    candidate into the corpus row in place (D1/D4). That is exactly the
    fragility that got the AND/OR/NOT combinators deleted (see
    specification.py): under composition, evaluation order would decide how
    many times a merge ran, invisibly.

    So the state transition must be a fixed point. A second identical call
    must change NOTHING: not the corpus length, not any survivor field, and
    critically not `notes` — the merge APPENDS its provenance link, so a
    double-merge would silently duplicate that text (and re-donate fields)
    while every count-based assertion still passed.
    """
    corpus: list[Observation] = []
    spec = DuplicateStationSpecification(corpus)

    existing = _obs(
        source_record_id="src_a_MASS_000001",
        source_id="src_a",
        evidence_class="MASS",
        abundance_kg_m2=14.6,
        quality_grade="A",
        # deliberately absent, so the merge has a real field to donate:
        mean_nodule_mass_g=None,
    )
    corpus.append(existing)

    duplicate = _obs(
        source_record_id="src_b_MASS_000001",
        source_id="src_b",
        evidence_class="MASS",
        abundance_kg_m2=14.5,
        quality_grade="B",  # lower -> existing wins, duplicate is absorbed
        mean_nodule_mass_g=41.3,
    )

    assert not spec.is_satisfied_by(duplicate)
    after_first = corpus[0].model_dump()
    assert len(corpus) == 1
    # The merge did happen: the donated field and the provenance link landed.
    assert after_first["mean_nodule_mass_g"] == 41.3
    assert after_first["notes"].count("src_b_MASS_000001") == 1
    assert after_first["notes"].count("merged fields") == 1

    # Second identical call — the fixed-point assertion.
    assert not spec.is_satisfied_by(duplicate)
    after_second = corpus[0].model_dump()

    assert len(corpus) == 1
    assert after_second == after_first  # every field, not just the counts
    assert after_second["notes"].count("src_b_MASS_000001") == 1  # not 2
    assert after_second["notes"].count("merged fields") == 1


# --- fail-is-terminal UNDER DEDUP (2026-07-30) -----------------------------
#
# The gap: qa_status is never null, so _merge's gap-fill could never carry it,
# and survivorship is decided by quality_grade — a field that says nothing
# about QA. A row adjudicated "fail" that lost the slot to a higher-grade
# candidate therefore had its verdict ERASED and became training-eligible.
# Decision: a merge may replace a failed row's VALUES, never its VERDICT.


def _pair(existing_qa: str, existing_grade: str, candidate_qa: str, candidate_grade: str):
    existing = _obs(
        source_record_id="src_a_MASS_000001",
        source_id="src_a",
        evidence_class="MASS",
        abundance_kg_m2=12.0,
        qa_status=existing_qa,
        quality_grade=existing_grade,
    )
    candidate = _obs(
        source_record_id="src_b_MASS_000001",
        source_id="src_b",
        evidence_class="MASS",
        abundance_kg_m2=14.0,
        qa_status=candidate_qa,
        quality_grade=candidate_grade,
    )
    corpus: list[Observation] = [existing]
    spec = DuplicateStationSpecification(corpus)
    assert not spec.is_satisfied_by(candidate)
    return corpus[0]


def test_fail_verdict_survives_being_outranked_by_a_higher_grade_candidate() -> None:
    """THE case the old end-to-end test could not reach (its fail row sat at
    coordinates no adapter covers, so no merge ever fired). A clean grade-A
    candidate wins the slot on quality_grade; it must NOT win away the fail."""
    survivor = _pair("fail", "B", "pending", "A")

    assert survivor.source_record_id == "src_b_MASS_000001"  # candidate won the slot
    assert survivor.abundance_kg_m2 == 14.0  # ... and its better measurement
    assert survivor.qa_status == QAStatus.FAIL  # but NOT the verdict
    assert not survivor.is_training_eligible()
    # An auditor must be able to see WHY a grade-A row is failed.
    assert "escalated pending -> fail" in survivor.notes
    assert "src_a_MASS_000001" in survivor.notes


def test_fail_verdict_survives_when_the_failed_row_wins_the_slot() -> None:
    survivor = _pair("fail", "A", "pending", "A")  # tie -> existing wins
    assert survivor.source_record_id == "src_a_MASS_000001"
    assert survivor.qa_status == QAStatus.FAIL
    assert not survivor.is_training_eligible()
    # No escalation happened, so no escalation note is written.
    assert "escalated" not in (survivor.notes or "")
    assert "duplicate of src_b_MASS_000001" in survivor.notes


def test_a_failed_candidate_escalates_a_clean_existing_row() -> None:
    """Symmetric: the verdict is sticky in both directions, so which row
    happens to arrive first cannot decide whether a failure is recorded."""
    survivor = _pair("pending", "A", "fail", "B")
    assert survivor.source_record_id == "src_a_MASS_000001"  # existing won the slot
    assert survivor.qa_status == QAStatus.FAIL
    assert not survivor.is_training_eligible()
    assert "escalated pending -> fail" in survivor.notes


def test_flagged_verdict_is_sticky_the_same_way() -> None:
    survivor = _pair("flagged", "B", "pending", "A")
    assert survivor.qa_status == QAStatus.FLAGGED
    assert not survivor.is_training_eligible()
    assert "escalated pending -> flagged" in survivor.notes


def test_fail_outranks_flagged_when_both_sides_are_adjudicated() -> None:
    """E1.2's precedence (fail is terminal, stronger than flagged) holds
    through a merge too — a merge must not launder a fail into a flagged."""
    survivor = _pair("flagged", "A", "fail", "B")
    assert survivor.qa_status == QAStatus.FAIL
    assert "escalated flagged -> fail" in survivor.notes


def test_escalation_is_idempotent_across_repeated_merges() -> None:
    existing = _obs(
        source_record_id="src_a_MASS_000001", source_id="src_a", evidence_class="MASS",
        abundance_kg_m2=12.0, qa_status="fail", quality_grade="B",
    )
    candidate = _obs(
        source_record_id="src_b_MASS_000001", source_id="src_b", evidence_class="MASS",
        abundance_kg_m2=14.0, qa_status="pending", quality_grade="A",
    )
    corpus: list[Observation] = [existing]
    spec = DuplicateStationSpecification(corpus)

    spec.is_satisfied_by(candidate)
    after_first = corpus[0].model_dump()
    spec.is_satisfied_by(candidate)

    assert corpus[0].model_dump() == after_first
    assert corpus[0].notes.count("escalated") == 1
