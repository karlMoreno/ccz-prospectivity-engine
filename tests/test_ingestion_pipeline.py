"""E0.5 CI centerpiece: ingest synthetic sources -> corpus -> assert evidence
tagging survives the full fetch/adapt/normalize/validate/dedup/append
sequence (IngestionPipeline.run(), Template Method).

WHAT THESE TESTS CAN AND CANNOT SEE (renamed 2026-07-30, test-name audit).
The `synthetic_corpus` fixture builds its rows through `Observation(**record)`,
and `Observation` itself enforces the COVER / GRID / COUNT evidence-class rules
at construction (domain/observation.py::_enforce_evidence_class_discipline). So
a violation cannot reach these assertions — it raises during fixture setup
instead. What they genuinely prove is that the pipeline's output SATISFIES that
discipline end to end (i.e. the pipeline produces rows the domain type accepts,
and the expected classes are present), not that the rule is independently
upheld.

For checks that CAN observe a violation, see `test_corpus_invariants.py`: it
reads `data/corpus/master_observations.csv` as raw strings with no Pydantic in
the path, so a row written by anything that bypasses `Observation` is visible.
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


def test_pipeline_cover_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    cover_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COVER]
    assert cover_rows
    assert all(o.abundance_kg_m2 is None for o in cover_rows)


def test_pipeline_grid_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    grid_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.GRID]
    assert grid_rows
    assert all(
        o.observation_or_prediction != ObservationOrPrediction.OBSERVED for o in grid_rows
    )


def test_pipeline_count_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    count_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COUNT]
    assert count_rows
    for obs in count_rows:
        if obs.abundance_kg_m2 is not None:
            assert obs.mean_nodule_mass_g is not None


def test_synthetic_fixture_mass_rows_all_qualify_for_training(
    synthetic_corpus: list[Observation],
) -> None:
    """A property of THIS FIXTURE, not a general rule (renamed 2026-07-30).
    The old name, `test_mass_rows_are_training_eligible`, stated a rule that is
    false since P1 — a MASS row with qa_status fail/flagged is NOT
    training-eligible — and contradicted `test_sample_source.py`'s
    `test_flagged_row_is_excluded_from_training`, which asserts exactly that.
    """
    mass_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.MASS]
    assert mass_rows
    assert all(o.is_training_eligible() for o in mass_rows)
