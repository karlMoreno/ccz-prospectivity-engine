"""MassNormalizer — STRATEGY (one AbundanceNormalizer per evidence_class).

Implements normalization.yaml's MASS rule (Contract 7): if the source already
reported abundance in kg/m2, pass it through; otherwise derive it from
recovered nodule mass over the sampled footprint. MASS is the only evidence
class SampleSource ever trains on (CLAUDE.md, AR-D02) — this is the one
normalizer whose output feeds the model directly.
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import AbundanceBasis, QualityGrade
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord

# Unit strings this codebase's adapters use for "already kg/m2" (see
# regional_grid_adapter.py / tests/fixtures/adapters.py: "kg_m2").
_ALREADY_KG_M2_UNITS = {"kg_m2", "kg/m2"}


def _append_derivation_formula(record: RawRecord, formula: str) -> None:
    """D8-C (2026-07-27 review): APPEND rather than overwrite. Some adapters
    (e.g. NoduleAggregateAdapter) already write derivation_formula to
    document their own aggregation math (nodule_mass_kg = sum of measured
    masses, etc.) before this normalizer ever runs — a bare overwrite would
    silently discard that upstream provenance."""
    existing = record.get("derivation_formula")
    record["derivation_formula"] = f"{existing}; {formula}" if existing else formula


class MassNormalizer(AbundanceNormalizer):
    """MASS: pass through if already kg/m2, else kg_m2 = nodule_mass_kg / sampled_area_m2."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        unit = (record.get("abundance_unit_original") or "").strip().lower()
        already_reported = record.get("abundance_value_original")
        if unit in _ALREADY_KG_M2_UNITS and already_reported is not None:
            record["abundance_kg_m2"] = already_reported
            _append_derivation_formula(record, "abundance_kg_m2 = abundance_value_original (already kg/m2)")
            record.setdefault("abundance_basis", AbundanceBasis.UNKNOWN.value)
            record.setdefault("quality_grade", QualityGrade.A.value)
            return record

        mass_kg = record.get("nodule_mass_kg")
        area_m2 = record.get("sampled_area_m2")
        # Explicit `is not None` + `> 0`, not truthiness: a bare `and area_m2`
        # would treat a (schema-legal, if physically nonsensical) area_m2=0.0
        # the same as a missing area, silently skipping the row instead of
        # avoiding the ZeroDivisionError on purpose.
        if mass_kg is not None and area_m2 is not None and area_m2 > 0:
            record["abundance_kg_m2"] = mass_kg / area_m2
            _append_derivation_formula(record, "abundance_kg_m2 = nodule_mass_kg / sampled_area_m2")
            record.setdefault("quality_grade", QualityGrade.A.value)
        return record
