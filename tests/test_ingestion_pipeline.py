"""E0.5 CI centerpiece: ingest synthetic sources -> corpus -> assert evidence
tagging survives the full fetch/adapt/normalize/validate/dedup/append
sequence (IngestionPipeline.run(), Template Method).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation


def test_synthetic_sources_ingest_into_a_tagged_corpus(synthetic_corpus: list[Observation]) -> None:
    assert len(synthetic_corpus) > 0
    assert all(obs.evidence_class in EvidenceClass for obs in synthetic_corpus)


def test_corpus_contains_every_evidence_class_the_fixtures_produce(
    synthetic_corpus: list[Observation],
) -> None:
    classes_present = {obs.evidence_class for obs in synthetic_corpus}
    assert classes_present == {
        EvidenceClass.MASS,
        EvidenceClass.COUNT,
        EvidenceClass.COVER,
        EvidenceClass.GRID,
    }


def test_cover_rows_in_the_corpus_never_carry_abundance_kg_m2(
    synthetic_corpus: list[Observation],
) -> None:
    cover_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COVER]
    assert cover_rows
    assert all(o.abundance_kg_m2 is None for o in cover_rows)


def test_grid_rows_in_the_corpus_are_never_observed(synthetic_corpus: list[Observation]) -> None:
    grid_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.GRID]
    assert grid_rows
    assert all(
        o.observation_or_prediction != ObservationOrPrediction.OBSERVED for o in grid_rows
    )


def test_count_rows_only_carry_abundance_with_a_recorded_mean_mass(
    synthetic_corpus: list[Observation],
) -> None:
    count_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COUNT]
    assert count_rows
    for obs in count_rows:
        if obs.abundance_kg_m2 is not None:
            assert obs.mean_nodule_mass_g is not None


def test_mass_rows_are_training_eligible(synthetic_corpus: list[Observation]) -> None:
    mass_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.MASS]
    assert mass_rows
    assert all(o.is_training_eligible() for o in mass_rows)
