"""Test-only AbundanceNormalizer (STRATEGY) implementations, one per evidence
class, close enough to normalization.yaml's real rules to prove the pipeline
enforces them end-to-end (E0.4/E0.5). Real normalizers are Phase 1 (E1.2).

data_origin: AUTHORED (author: unrecorded). SYNTHETIC_MEAN_NODULE_MASS_G is
"synthetic" in name only — a hand-picked constant, taxonomy-AUTHORED; the
misnomer is recorded rather than renamed (P2.0 decision).
"""

from __future__ import annotations

from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord
from engine.prospectivity.provenance.origin import AUTHOR_UNRECORDED, DataOrigin

DATA_ORIGIN = DataOrigin.AUTHORED
DATA_AUTHOR = AUTHOR_UNRECORDED

SYNTHETIC_MEAN_NODULE_MASS_G = 12.5  # [GEOLOGY — ISAAC placeholder]; fixture-only; AUTHORED, name notwithstanding


class FixtureMassNormalizer(AbundanceNormalizer):
    """MASS: kg_m2 = nodule_mass_kg / sampled_area_m2 (normalization.yaml MASS rule)."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        mass_kg = record.get("nodule_mass_kg")
        area_m2 = record.get("sampled_area_m2")
        if mass_kg is not None and area_m2:
            record["abundance_kg_m2"] = round(mass_kg / area_m2, 3)
            record["derivation_formula"] = "kg_m2 = nodule_mass_kg / sampled_area_m2"
            record["quality_grade"] = "A"
        return record


class FixtureCountNormalizer(AbundanceNormalizer):
    """COUNT: kg_m2 = density * mean_nodule_mass_g / 1000, ONLY with a recorded
    mean_nodule_mass_g — the normalization.yaml COUNT rule."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        count = record.get("nodule_count")
        area_m2 = record.get("sampled_area_m2")
        if count is None or not area_m2:
            return record
        density = count / area_m2
        record["nodule_density_m2"] = round(density, 3)
        record["mean_nodule_mass_g"] = SYNTHETIC_MEAN_NODULE_MASS_G
        record["abundance_kg_m2"] = round(density * SYNTHETIC_MEAN_NODULE_MASS_G / 1000, 3)
        record["derivation_formula"] = (
            "kg_m2 = (nodule_count / sampled_area_m2) * mean_nodule_mass_g / 1000"
        )
        record["quality_grade"] = "B"
        return record


class FixtureCoverNormalizer(AbundanceNormalizer):
    """COVER: HARD RULE — never produces abundance_kg_m2 (normalization.yaml)."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        record["abundance_kg_m2"] = None
        record.setdefault("quality_grade", "B")
        return record


class FixtureGridNormalizer(AbundanceNormalizer):
    """GRID: keeps the compiled value as a prior, never as an observed station."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        record["abundance_kg_m2"] = record.get("abundance_value_original")
        record["observation_or_prediction"] = "compiled"
        record["derivation_formula"] = "compiled 0.1deg-style grid value (prior only)"
        record["quality_grade"] = "C"
        return record
