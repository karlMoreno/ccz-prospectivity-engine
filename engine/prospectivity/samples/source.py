"""SampleSource — STRATEGY.

Swappable "where do the corpus observations come from" implementation (a CSV
corpus today, a database later). But the MASS-only training rule (CLAUDE.md
"Train on MASS only" / AR-P02) is not a strategy choice — it must hold no
matter which SampleSource is plugged in. So it is implemented ONCE here, as a
concrete method on the ABC, in terms of one abstract hook
(`load_observations`) that subclasses must supply. A subclass cannot
accidentally leak COUNT/COVER/GRID/GRADE rows into training even if it tried.

    ┌───────────────────────────────────────────┐
    │              SampleSource (ABC)             │
    │  load_observations() -> list[Observation]   │  <- abstract (per-strategy)
    │  get_training_samples() -> list[Observation] │  <- concrete, FROZEN rule:
    │      evidence_class == MASS                  │     evidence_class MASS
    │      AND abundance_kg_m2 is not None          │     AND abundance_kg_m2 present
    │      AND is_open                              │     AND is_open
    └───────────────────────────────────────────┘
              ▲                          ▲
    ┌─────────────────────┐   ┌───────────────────────┐
    │ CorpusCsvSampleSrc   │   │ FixtureSampleSource     │
    │ (Phase 1, real)      │   │ (tests only)            │
    └─────────────────────┘   └───────────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.observation import Observation


class SampleSource(ABC):
    """Produces the observation pool, then filters it to training-eligible rows."""

    @abstractmethod
    def load_observations(self) -> list[Observation]:
        """Return every observation this source knows about, of any evidence class."""
        raise NotImplementedError

    def get_training_samples(self) -> list[Observation]:
        """AR-P02, frozen: MASS rows with a valid abundance_kg_m2 and is_open=true.

        Not overridable — the evidence-class discipline must survive every
        SampleSource implementation, not just the careful ones.
        """
        return [obs for obs in self.load_observations() if obs.is_training_eligible()]
