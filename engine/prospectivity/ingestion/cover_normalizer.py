"""CoverNormalizer — STRATEGY (one AbundanceNormalizer per evidence_class).

Implements normalization.yaml's COVER rule — the hard rule that most protects
the model (CLAUDE.md): visible_cover_percent is a covariate, and this
normalizer NEVER writes abundance_kg_m2, no matter what the row carries
(even a stray abundance_value_original from a mislabeled source stays unused).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import QualityGrade
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord


class CoverNormalizer(AbundanceNormalizer):
    """COVER: never produces abundance_kg_m2 — hard rule."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        record["abundance_kg_m2"] = None
        record.setdefault("quality_grade", QualityGrade.B.value)
        return record
