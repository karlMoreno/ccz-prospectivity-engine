"""GradeNormalizer — STRATEGY (one AbundanceNormalizer per evidence_class).

Implements normalization.yaml's GRADE rule: chemistry only. This normalizer
never writes abundance_kg_m2 — it only carries mn/ni/cu/co_pct through as
already mapped by the SourceAdapter. (The station-join logic normalization.yaml
describes — by station_id, else cruise+event+coords within join_tolerance_km
— is a corpus-assembly concern for a later task; this normalizer's contract
is narrower: never invent a mass value for a grade-only row.)
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import QualityGrade
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord


class GradeNormalizer(AbundanceNormalizer):
    """GRADE: chemistry only, never abundance_kg_m2."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        record["abundance_kg_m2"] = None
        record.setdefault("quality_grade", QualityGrade.B.value)
        return record
