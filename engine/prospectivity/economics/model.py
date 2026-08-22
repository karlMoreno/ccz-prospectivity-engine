"""EconomicModel — STRATEGY.

Turns a PredictionSurface into a minable-footprint raster for one scenario
from scenarios.yaml (Contract 4). Track E ships this mechanism only; every
number it reads is a Track-G-owned placeholder until Contract 4's
`illustrative_only` flags flip to false (Phase 4, integration checkpoint 4).
Two scenarios (MARKET_STANDARD, STRATEGIC_SUBSIDIZED) are both instances of
this one interface — a third scenario is a config addition, not a code change.

    ┌────────────────────────────────────────────┐
    │              EconomicModel (ABC)              │
    │  apply(prediction, scenario_config)            │
    │    -> EconomicScenarioResult                   │
    └────────────────────────────────────────────┘
        ▲                                ▲
  ┌────────────────────┐        ┌──────────────────────┐
  │ CutoffEconomicModel  │        │ (future) DollarValue  │   (Phase 4)
  │ grade_metric=abund.  │        │ EconomicModel          │
  └────────────────────┘        └──────────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from engine.prospectivity.domain.results import EconomicScenarioResult


class EconomicModel(ABC):
    """Applies one scenarios.yaml scenario to the prediction surfaces.

    E3.4 (2B sweep, 2026-08-22): the engine hands this seam the MAPPING of
    per-estimator `SurfaceResult`s E3.1+2 builds (paired mu/sd over the
    grid), not a `PredictionSurface` — that Phase-0 type has no producer.
    The annotation now says what arrives; Phase 4 decides what the model
    does with it (zero implementations today, PATTERNS.md §3.2).
    """

    @abstractmethod
    def apply(
        self, surfaces: Mapping[str, Any], scenario_config: dict[str, Any]
    ) -> EconomicScenarioResult:
        """Return the minable-footprint result for one scenario.

        Implementations must propagate `scenario_config["illustrative_only"]`
        into the result — the engine is never allowed to present a
        placeholder-cutoff footprint as a real one (CLAUDE.md "honesty over
        impressiveness").
        """
        raise NotImplementedError
