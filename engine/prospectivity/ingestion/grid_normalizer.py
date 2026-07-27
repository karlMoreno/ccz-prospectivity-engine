"""GridNormalizer — STRATEGY (one AbundanceNormalizer per evidence_class).

Implements normalization.yaml's GRID rule: keeps the compiled/interpolated
kg/m2 value as a regional prior (and, for TS-6, the benchmark surface —
Contract 6), but forces observation_or_prediction to "compiled" so it can
never be treated as an independent training station (AR-D03).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import ObservationOrPrediction, QualityGrade
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord


class GridNormalizer(AbundanceNormalizer):
    """GRID: prior/benchmark value, forced non-observed, never a training station."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        value = record.get("abundance_value_original")
        if value is not None:
            record["abundance_kg_m2"] = value
            record["derivation_formula"] = (
                "abundance_kg_m2 = abundance_value_original (compiled/interpolated prior)"
            )
        record["observation_or_prediction"] = ObservationOrPrediction.COMPILED.value
        record.setdefault("quality_grade", QualityGrade.C.value)
        return record
