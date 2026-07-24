"""AbundanceNormalizer — STRATEGY.

One normalizer per evidence_class, each implementing its rule from
normalization.yaml (Contract 7). Swapping conversion logic for one class never
touches ingestion or the model — the golden rule from Contract 7 applies
uniformly: `abundance_kg_m2` is produced ONLY where physically valid; when a
class cannot yield a defensible kg/m2, the normalizer must return the record
with `abundance_kg_m2` left as `None`, not a computed guess.

    ┌─────────────────────────────────────────┐
    │          AbundanceNormalizer (ABC)         │
    │  normalize(record: RawRecord) -> RawRecord  │
    └─────────────────────────────────────────┘
       ▲          ▲          ▲          ▲          ▲
    ┌──────┐  ┌───────┐  ┌───────┐  ┌──────┐  ┌───────┐
    │ MASS  │  │ COUNT  │  │ COVER  │  │ GRID  │  │ GRADE  │   (all Phase 1, E1.2)
    └──────┘  └───────┘  └───────┘  └──────┘  └───────┘
      x1/area  x mean_mass  NEVER     prior_only  chemistry
                                       flagged      join only
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.ingestion.source_adapter import RawRecord


class AbundanceNormalizer(ABC):
    """Converts one evidence class's raw record into a (possibly still
    kg/m2-less) record, per its normalization.yaml rule."""

    @abstractmethod
    def normalize(self, record: RawRecord) -> RawRecord:
        """Return `record` with `abundance_kg_m2` and `derivation_formula` set
        wherever this evidence class's rule allows it, and left `None`
        otherwise. Must never invent a value the evidence class forbids
        (COVER, GRADE: always `None`; GRID: prior-only, flagged non-observed).
        """
        raise NotImplementedError
