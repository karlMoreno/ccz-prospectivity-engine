"""CovariateRecipe — STRATEGY + TEMPLATE METHOD (Contract 3, E1.4).

STRATEGY: each Contract 3 recipe (horn_slope, std_dev_elevation, ...) is one
interchangeable class behind this interface — adding covariate #9 means
adding a class and a contract entry, never touching the pipeline (CLAUDE.md:
"adding X means adding a class, not rewriting the pipeline").

TEMPLATE METHOD: `build()` fixes the sequence every recipe must follow —
resolve metre windows -> compute -> attach provenance — so no concrete recipe
can skip the provenance step or resolve windows its own way. Subclasses fill
exactly two hooks (`_resolve_windows`, `_compute`).

    ┌───────────────────────────────────────────────┐
    │            CovariateRecipe (ABC)               │
    │  build(grid):            <- TEMPLATE METHOD    │
    │    resolved = _resolve_windows(grid)  <- hook  │
    │    values   = _compute(grid, resolved) <- hook │
    │    + provenance (versions, windows, border,    │
    │      CRS strategy, DEM identity)               │
    └───────────────────────────────────────────────┘
        ▲          ▲            ▲
   DepthRecipe  HornSlope...  BpiRecipe   (recipes.py — one per contract recipe)

Provenance records BOTH the requested physical distance and the resolved cell
window (Contract 3 v3): a reader sees what was actually computed, not just
what was asked for — including `clamped: true` on a DEM too coarse for the
request (expected on the synthetic DEM, by design).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.window import ResolvedWindow

# The ONE border policy, applied by every recipe via _stencils._neighbor:
BORDER_POLICY = {
    "name": "nan_border",
    "description": (
        "cells whose full neighborhood extends past the raster edge are NaN; "
        "no edge padding, no shrunken windows"
    ),
}

# The ONE approved CRS handling (Preflight 3, strategy A) — implemented in
# dem_grid.py, stated here so every layer's provenance carries it:
CRS_STRATEGY = (
    "per_row_longitude_scaling: EPSG:4326 degrees -> metres via "
    "dx_m[row] = res_x_deg * 111320 * cos(lat_row), dy_m = res_y_deg * 111320; "
    "windows resolved from the N-S cell size (E-W span deviates <= ~3% at "
    "study latitudes)"
)


@dataclass(frozen=True)
class CovariateResult:
    """One computed covariate layer: the array plus its full provenance."""

    name: str
    values: np.ndarray
    provenance: dict


class CovariateRecipe(ABC):
    """One Contract 3 recipe. Class constants mirror the contract entry and
    are cross-checked against it by the registry — bumping the contract's
    recipe_version without changing the code (or vice versa) fails loudly."""

    RECIPE: ClassVar[str]  # contract `recipe` string, e.g. "horn_slope"
    RECIPE_VERSION: ClassVar[int]  # contract `recipe_version`

    def __init__(self, name: str) -> None:
        self._name = name  # contract `name`, e.g. "slope"

    @property
    def name(self) -> str:
        return self._name

    def build(self, grid: DemGrid) -> CovariateResult:  # TEMPLATE METHOD
        """Fixed sequence: resolve windows -> compute -> provenance. Final —
        concrete recipes override the hooks, never this."""
        resolved = self._resolve_windows(grid)
        values = self._compute(grid, resolved)
        provenance = {
            "name": self._name,
            "recipe": self.RECIPE,
            "recipe_version": self.RECIPE_VERSION,
            "params_requested": self._params_requested(),
            "resolved_windows": {label: window.provenance() for label, window in resolved.items()},
            "border_policy": BORDER_POLICY,
            "crs_strategy": CRS_STRATEGY,
            "dem": grid.provenance(),
        }
        return CovariateResult(name=self._name, values=values, provenance=provenance)

    def _resolve_windows(self, grid: DemGrid) -> dict[str, ResolvedWindow]:
        """Hook: metres -> cells for this recipe's neighborhood parameters.
        Default: no windowed parameters (fixed-stencil / passthrough
        recipes)."""
        return {}

    def _params_requested(self) -> dict:
        """Hook: the contract params as requested (physical units)."""
        return {}

    @abstractmethod
    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        """Hook: the deterministic math. Must honour BORDER_POLICY (use
        _stencils helpers and NaN propagates correctly by construction)."""
        raise NotImplementedError
