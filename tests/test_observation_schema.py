"""Observation validates the real corpus CSV, and structurally cannot
represent the forbidden evidence-class conflations (CLAUDE.md
scientific-integrity rules, enforced in domain/observation.py).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER_CORPUS_CSV = REPO_ROOT / "data" / "corpus" / "master_observations.csv"


def load_observations_from_csv(path: Path) -> list[Observation]:
    frame = pd.read_csv(path)
    frame = frame.astype(object).where(pd.notnull(frame), None)
    return [Observation(**row) for row in frame.to_dict(orient="records")]


def test_master_observations_csv_validates_against_schema() -> None:
    observations = load_observations_from_csv(MASTER_CORPUS_CSV)
    assert len(observations) > 0


def test_every_row_has_a_tagged_evidence_class() -> None:
    for obs in load_observations_from_csv(MASTER_CORPUS_CSV):
        assert obs.evidence_class in EvidenceClass


def test_cover_rows_never_carry_abundance_kg_m2() -> None:
    observations = load_observations_from_csv(MASTER_CORPUS_CSV)
    cover_rows = [o for o in observations if o.evidence_class == EvidenceClass.COVER]
    assert cover_rows, "fixture CSV should contain at least one COVER example row"
    assert all(o.abundance_kg_m2 is None for o in cover_rows)


def test_grid_rows_are_never_flagged_observed() -> None:
    observations = load_observations_from_csv(MASTER_CORPUS_CSV)
    grid_rows = [o for o in observations if o.evidence_class == EvidenceClass.GRID]
    assert grid_rows, "fixture CSV should contain at least one GRID example row"
    assert all(o.observation_or_prediction != ObservationOrPrediction.OBSERVED for o in grid_rows)


def test_cover_row_with_abundance_kg_m2_is_rejected() -> None:
    """Regression test for the #1 sacred rule: this must fail loudly, not
    silently poison the corpus (CLAUDE.md "if you find yourself writing
    cover->mass into abundance_kg_m2, that is a bug — stop")."""
    with pytest.raises(ValidationError, match="COVER row carries a bare abundance_kg_m2"):
        Observation(
            source_record_id="BAD001",
            source_id="src_synthetic_cover",
            evidence_class=EvidenceClass.COVER,
            longitude=-126.0,
            latitude=12.0,
            visible_cover_percent=30.0,
            abundance_kg_m2=5.0,  # the bug this test exists to catch
            observation_or_prediction=ObservationOrPrediction.OBSERVED,
            is_open=True,
            qa_status="pending",
        )


def test_grid_row_flagged_observed_is_rejected() -> None:
    with pytest.raises(ValidationError, match="observation_or_prediction=observed"):
        Observation(
            source_record_id="BAD002",
            source_id="src_synthetic_grid",
            evidence_class=EvidenceClass.GRID,
            longitude=-126.0,
            latitude=12.0,
            abundance_kg_m2=5.0,
            observation_or_prediction=ObservationOrPrediction.OBSERVED,
            is_open=True,
            qa_status="pending",
        )


def test_count_row_needs_mean_nodule_mass_to_carry_abundance() -> None:
    with pytest.raises(ValidationError, match="mean_nodule_mass_g"):
        Observation(
            source_record_id="BAD003",
            source_id="src_synthetic_boxcore",
            evidence_class=EvidenceClass.COUNT,
            longitude=-126.0,
            latitude=12.0,
            nodule_count=100,
            abundance_kg_m2=2.0,  # no mean_nodule_mass_g recorded
            observation_or_prediction=ObservationOrPrediction.OBSERVED,
            is_open=True,
            qa_status="pending",
        )


def test_grade_row_never_carries_abundance_kg_m2() -> None:
    with pytest.raises(ValidationError, match="GRADE row carries abundance_kg_m2"):
        Observation(
            source_record_id="BAD004",
            source_id="src_synthetic_boxcore",
            evidence_class=EvidenceClass.GRADE,
            longitude=-126.0,
            latitude=12.0,
            mn_pct=28.0,
            abundance_kg_m2=5.0,
            observation_or_prediction=ObservationOrPrediction.OBSERVED,
            is_open=True,
            qa_status="pending",
        )
