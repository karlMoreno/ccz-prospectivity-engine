"""SampleSource.get_training_samples() enforces the MASS-only training rule
(AR-P02, CLAUDE.md "Train on MASS only") regardless of the concrete strategy.
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.domain.observation import Observation
from tests.fixtures.sample_source import FixtureSampleSource


def test_get_training_samples_returns_mass_only(synthetic_corpus: list[Observation]) -> None:
    sample_source = FixtureSampleSource(synthetic_corpus)
    training_samples = sample_source.get_training_samples()

    assert training_samples
    assert all(obs.evidence_class == EvidenceClass.MASS for obs in training_samples)
    assert all(obs.abundance_kg_m2 is not None for obs in training_samples)
    assert all(obs.is_open for obs in training_samples)


def test_get_training_samples_excludes_cover_count_and_grid(
    synthetic_corpus: list[Observation],
) -> None:
    sample_source = FixtureSampleSource(synthetic_corpus)
    training_ids = {obs.source_record_id for obs in sample_source.get_training_samples()}
    non_mass_ids = {
        obs.source_record_id
        for obs in synthetic_corpus
        if obs.evidence_class != EvidenceClass.MASS
    }
    assert training_ids.isdisjoint(non_mass_ids)


# --- P1 (2026-07-27 audit follow-up): qa_status gates training eligibility -


def _mass_obs(**overrides: object) -> Observation:
    fields = dict(
        source_record_id="src_test_MASS_000001",
        source_id="src_test",
        evidence_class="MASS",
        latitude=11.9,
        longitude=-117.0,
        abundance_kg_m2=14.6,
        observation_or_prediction="observed",
        is_open=True,
        qa_status="pending",
    )
    fields.update(overrides)
    return Observation(**fields)


def test_flagged_row_is_excluded_from_training() -> None:
    flagged = _mass_obs(qa_status="flagged")
    assert not flagged.is_training_eligible()
    assert FixtureSampleSource([flagged]).get_training_samples() == []


def test_failed_row_is_excluded_from_training() -> None:
    failed = _mass_obs(qa_status="fail")
    assert not failed.is_training_eligible()
    assert FixtureSampleSource([failed]).get_training_samples() == []


def test_pending_and_pass_rows_are_included_in_training() -> None:
    pending = _mass_obs(source_record_id="src_test_MASS_000001", qa_status="pending")
    passed = _mass_obs(source_record_id="src_test_MASS_000002", qa_status="pass")
    training_samples = FixtureSampleSource([pending, passed]).get_training_samples()
    assert {obs.source_record_id for obs in training_samples} == {
        "src_test_MASS_000001",
        "src_test_MASS_000002",
    }


def test_real_failed_box_core_is_absent_from_training_samples() -> None:
    """The concrete case D5.3 exists for: SO268/1_12-2 ("GER Trial; failed")
    must never appear in get_training_samples() output, even though it's a
    perfectly well-formed MASS row with a real abundance_kg_m2."""
    from engine.prospectivity.ingestion.corpus_builder import build_corpus

    corpus = build_corpus()
    sample_source = FixtureSampleSource(corpus)
    training_event_ids = {obs.event_id for obs in sample_source.get_training_samples()}
    assert "SO268/1_12-2" not in training_event_ids
