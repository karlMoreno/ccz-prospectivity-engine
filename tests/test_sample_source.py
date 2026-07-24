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
