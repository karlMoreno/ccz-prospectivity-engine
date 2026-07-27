"""Real AbundanceNormalizer (STRATEGY, E1.2) tests: one test per class's
normalization.yaml formula, run directly against a hand-built RawRecord (no
adapter/pipeline involved) — plus the two hard-rule regression tests and the
NormalizerRegistry (REGISTRY) completeness/screening tests.
"""

from __future__ import annotations

import pytest

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.ingestion.cover_normalizer import CoverNormalizer
from engine.prospectivity.ingestion.count_normalizer import CountNormalizer
from engine.prospectivity.ingestion.grade_normalizer import GradeNormalizer
from engine.prospectivity.ingestion.grid_normalizer import GridNormalizer
from engine.prospectivity.ingestion.mass_normalizer import MassNormalizer
from engine.prospectivity.ingestion.normalizer_registry import (
    NormalizerRegistry,
    apply_screening,
    build_default_registry,
)


def _record(**fields: object) -> dict:
    base = {
        "source_id": "src_test",
        "source_record_id": "src_test_000001",
        "latitude": 10.0,
        "longitude": -120.0,
        "is_open": True,
        "qa_status": "pending",
        "observation_or_prediction": "observed",
    }
    base.update(fields)
    return base


# --- MassNormalizer -----------------------------------------------------


def test_mass_normalizer_derives_kg_m2_from_mass_and_area() -> None:
    record = _record(evidence_class="MASS", nodule_mass_kg=2.5, sampled_area_m2=0.25)
    result = MassNormalizer().normalize(record)
    assert result["abundance_kg_m2"] == pytest.approx(10.0)
    assert result["derivation_formula"] == "abundance_kg_m2 = nodule_mass_kg / sampled_area_m2"
    assert result["quality_grade"] == "A"


def test_mass_normalizer_passes_through_when_already_kg_m2() -> None:
    record = _record(
        evidence_class="MASS",
        abundance_value_original=7.2,
        abundance_unit_original="kg_m2",
    )
    result = MassNormalizer().normalize(record)
    assert result["abundance_kg_m2"] == 7.2
    assert "already kg/m2" in result["derivation_formula"]


# --- CountNormalizer ------------------------------------------------------


def test_count_normalizer_computes_with_recorded_mean_mass() -> None:
    record = _record(
        evidence_class="COUNT",
        nodule_density_m2=8.0,
        mean_nodule_mass_g=50.0,
    )
    result = CountNormalizer().normalize(record)
    assert result["abundance_kg_m2"] == pytest.approx(8.0 * 50.0 / 1000)
    assert result["quality_grade"] == "B"


def test_count_normalizer_without_mean_mass_leaves_abundance_blank() -> None:
    """Required regression: no mean_nodule_mass_g -> blank, never a substituted default."""
    record = _record(evidence_class="COUNT", nodule_density_m2=8.0)
    result = CountNormalizer().normalize(record)
    assert result.get("abundance_kg_m2") is None
    assert "derivation_formula" not in result


# --- CoverNormalizer -------------------------------------------------------


def test_cover_normalizer_never_sets_abundance_kg_m2() -> None:
    """Required: fails if a COVER row ever gets a non-null abundance_kg_m2,
    even when abundance_value_original is already populated on the row."""
    record = _record(
        evidence_class="COVER",
        visible_cover_percent=35.0,
        abundance_value_original=12.0,
        abundance_unit_original="kg_m2",
    )
    result = CoverNormalizer().normalize(record)
    assert result["abundance_kg_m2"] is None


# --- GridNormalizer ---------------------------------------------------------


def test_grid_normalizer_keeps_value_and_forces_compiled() -> None:
    record = _record(
        evidence_class="GRID",
        abundance_value_original=15.5,
        observation_or_prediction="observed",  # a mislabeled source row
    )
    result = GridNormalizer().normalize(record)
    assert result["abundance_kg_m2"] == 15.5
    assert result["observation_or_prediction"] == "compiled"
    assert result["quality_grade"] == "C"


# --- GradeNormalizer ---------------------------------------------------------


def test_grade_normalizer_never_sets_abundance_kg_m2() -> None:
    """Regression, mirroring the COVER rule: GRADE never gets abundance_kg_m2
    even when abundance_value_original is already populated on the row."""
    record = _record(
        evidence_class="GRADE",
        mn_pct=22.0,
        ni_pct=1.1,
        abundance_value_original=9.0,
        abundance_unit_original="kg_m2",
    )
    result = GradeNormalizer().normalize(record)
    assert result["abundance_kg_m2"] is None
    assert result["mn_pct"] == 22.0  # chemistry fields pass through untouched


# --- NormalizerRegistry (REGISTRY) -----------------------------------------


def test_registry_completeness_covers_every_evidence_class() -> None:
    registry = build_default_registry()
    registry.assert_complete()  # must not raise
    for evidence_class in EvidenceClass:
        record = _record(evidence_class=evidence_class.value)
        registry.normalize(record)  # must not KeyError for any registered class


def test_registry_assert_complete_fails_loudly_when_a_class_is_missing() -> None:
    registry = NormalizerRegistry()
    registry.register(EvidenceClass.MASS, MassNormalizer())
    with pytest.raises(ValueError, match="COUNT"):
        registry.assert_complete()


def test_registry_normalize_raises_for_an_unregistered_class() -> None:
    registry = NormalizerRegistry()
    registry.register(EvidenceClass.MASS, MassNormalizer())
    record = _record(evidence_class="COVER")
    with pytest.raises(KeyError):
        registry.normalize(record)


# --- screening bounds (Contract 7) -----------------------------------------


def test_screening_flags_out_of_range_abundance_without_dropping_it() -> None:
    record = _record(evidence_class="MASS", abundance_kg_m2=99.0, qa_status="pending")
    result = apply_screening(record)
    assert result["qa_status"] == "flagged"
    assert result["abundance_kg_m2"] == 99.0  # flagged, not dropped


def test_screening_leaves_in_range_values_unflagged() -> None:
    record = _record(evidence_class="MASS", abundance_kg_m2=10.0, qa_status="pending")
    result = apply_screening(record)
    assert result["qa_status"] == "pending"


def test_registry_normalize_applies_screening_after_the_class_rule() -> None:
    registry = build_default_registry()
    record = _record(evidence_class="MASS", nodule_mass_kg=20.0, sampled_area_m2=0.25)  # -> 80 kg/m2, in bounds
    out_of_bounds = registry.normalize(record)
    assert out_of_bounds["abundance_kg_m2"] == pytest.approx(80.0)
    assert out_of_bounds["qa_status"] == "flagged"  # 80 > screening max of 45
