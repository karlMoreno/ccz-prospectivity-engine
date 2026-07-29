"""CountNormalizer — STRATEGY (one AbundanceNormalizer per evidence_class).

Implements normalization.yaml's COUNT rule: kg_m2 = nodule_density_m2 *
mean_nodule_mass_g / 1000, and ONLY when mean_nodule_mass_g is present on the
row itself. normalization.yaml gestures at a source-level mean-mass lookup
(`mean_nodule_mass_g_source`), but that field is unset and source_queue.yaml
has no structured field for it (confirmed with the engineer of record,
2026-07-27) — so this normalizer looks at the row only. When mean_nodule_mass_g
is absent, abundance_kg_m2 stays blank and the row remains a COUNT covariate;
count->mass is an assumption, and this normalizer never substitutes a
literature default to manufacture one (CLAUDE.md scientific-integrity rules).
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import QualityGrade
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord


class CountNormalizer(AbundanceNormalizer):
    """COUNT: kg/m2 only via a mean_nodule_mass_g recorded on this row."""

    def normalize(self, record: RawRecord) -> RawRecord:
        record = dict(record)
        density = record.get("nodule_density_m2")
        mean_mass_g = record.get("mean_nodule_mass_g")
        if density is not None and mean_mass_g is not None:
            record["abundance_kg_m2"] = density * mean_mass_g / 1000
            formula = (
                "abundance_kg_m2 = nodule_density_m2 * mean_nodule_mass_g / 1000 "
                "(count->mass is an assumption; see quality_grade)"
            )
            # D8-C (2026-07-27 review): APPEND, don't overwrite -- some
            # adapters (e.g. NoduleAggregateAdapter) already document their
            # own aggregation math in derivation_formula before this
            # normalizer runs; a bare overwrite would discard it.
            existing = record.get("derivation_formula")
            record["derivation_formula"] = f"{existing}; {formula}" if existing else formula
            record.setdefault("quality_grade", QualityGrade.B.value)
        return record
