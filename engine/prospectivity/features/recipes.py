"""The 8 enabled Option-A recipes (Contract 3 v3) — concrete STRATEGIES.

One class per contract `recipe` string. Windowed recipes (roughness, tpi,
bpi) take physical distances in metres and resolve them per-DEM via
window.py; slope/aspect/curvature are native-resolution 3x3 operators by
definition (see the contract's v3 comment) and carry no window parameter.

Each __init__ validates its params dict STRICTLY (unknown or missing keys
raise) so a contract edit that renames a parameter fails loudly at registry
construction, never silently computes something else.
"""

from __future__ import annotations

import numpy as np

from engine.prospectivity.features._stencils import (
    annulus_offsets,
    horn_gradients,
    square_offsets,
    stacked_neighbors,
    zevenbergen_thorne_derivatives,
)
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipe import CovariateRecipe
from engine.prospectivity.features.window import ResolvedWindow, resolve_radius, resolve_square_window


def _require_params(name: str, params: dict, expected: set[str]) -> None:
    if set(params) != expected:
        raise ValueError(
            f"Recipe {name!r} expects params {sorted(expected)}, got {sorted(params)} — "
            "contract and implementation have drifted"
        )


class DepthRecipe(CovariateRecipe):
    """`passthrough`: the DEM value itself. Neighborhood is the single cell,
    so the border policy is trivially satisfied (no NaN rim)."""

    RECIPE = "passthrough"
    RECIPE_VERSION = 1

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, set())

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        return grid.values.copy()


class HornSlopeRecipe(CovariateRecipe):
    """`horn_slope`: Horn (1981) 3x3 gradient magnitude, degrees.
    Native-resolution operator — the 3x3 stencil is the definition."""

    RECIPE = "horn_slope"
    RECIPE_VERSION = 1

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, {"units"})
        if params["units"] != "degrees":
            raise ValueError(f"horn_slope only implements units=degrees, contract says {params['units']!r}")
        self._params = dict(params)

    def _params_requested(self) -> dict:
        return dict(self._params)

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        p, q = horn_gradients(grid)
        return np.degrees(np.arctan(np.hypot(p, q)))


class HornAspectRecipe(CovariateRecipe):
    """`horn_aspect`: downslope azimuth, degrees clockwise from north
    [0, 360). Flat cells (p == q == 0 exactly) get `undefined_flat_as`."""

    RECIPE = "horn_aspect"
    RECIPE_VERSION = 1

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, {"units", "undefined_flat_as"})
        if params["units"] != "degrees":
            raise ValueError(f"horn_aspect only implements units=degrees, contract says {params['units']!r}")
        self._params = dict(params)

    def _params_requested(self) -> dict:
        return dict(self._params)

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        p, q = horn_gradients(grid)
        # Downslope direction is (-p, -q); azimuth measured clockwise from
        # north = atan2(east_component, north_component).
        aspect = np.degrees(np.arctan2(-p, -q)) % 360.0
        flat = (p == 0.0) & (q == 0.0)
        aspect = np.where(flat, float(self._params["undefined_flat_as"]), aspect)
        return np.where(np.isnan(p) | np.isnan(q), np.nan, aspect)


class RoughnessRecipe(CovariateRecipe):
    """`std_dev_elevation`: population stdev (ddof=0) of elevation over the
    resolved square window. Windowed: metres -> cells at runtime."""

    RECIPE = "std_dev_elevation"
    RECIPE_VERSION = 2

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, {"window_m"})
        self._window_m = float(params["window_m"])

    def _params_requested(self) -> dict:
        return {"window_m": self._window_m}

    def _resolve_windows(self, grid: DemGrid) -> dict[str, ResolvedWindow]:
        return {"window": resolve_square_window(self._window_m, grid.cell_size_ns_m)}

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        offsets = square_offsets(resolved["window"].cells)
        return stacked_neighbors(grid.values, offsets).std(axis=0, ddof=0)


class ProfileCurvatureRecipe(CovariateRecipe):
    """`zevenbergen_thorne_profile`: curvature along the slope direction,
    1/m. Sign convention: positive = convex-up (ridge/dome), negative =
    concave (channel/basin); flat cells (p = q = 0) are 0 by convention.
    Native-resolution operator (3x3 central differences)."""

    RECIPE = "zevenbergen_thorne_profile"
    RECIPE_VERSION = 1

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, set())

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        p, q, r, s, t = zevenbergen_thorne_derivatives(grid)
        denominator = p**2 + q**2
        with np.errstate(invalid="ignore", divide="ignore"):
            curvature = -(r * p**2 + 2.0 * s * p * q + t * q**2) / denominator
        return np.where(denominator == 0.0, 0.0, curvature)


class PlanCurvatureRecipe(CovariateRecipe):
    """`zevenbergen_thorne_plan`: contour (across-slope) curvature, 1/m.
    Same sign convention and flat handling as profile. Native-resolution."""

    RECIPE = "zevenbergen_thorne_plan"
    RECIPE_VERSION = 1

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, set())

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        p, q, r, s, t = zevenbergen_thorne_derivatives(grid)
        denominator = p**2 + q**2
        with np.errstate(invalid="ignore", divide="ignore"):
            curvature = -(t * p**2 - 2.0 * s * p * q + r * q**2) / denominator
        return np.where(denominator == 0.0, 0.0, curvature)


class TpiRecipe(CovariateRecipe):
    """`topographic_position_index`: cell minus mean(window), window
    INCLUSIVE of the centre cell (Contract 3's own definition). Windowed."""

    RECIPE = "topographic_position_index"
    RECIPE_VERSION = 2

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, {"window_m"})
        self._window_m = float(params["window_m"])

    def _params_requested(self) -> dict:
        return {"window_m": self._window_m}

    def _resolve_windows(self, grid: DemGrid) -> dict[str, ResolvedWindow]:
        return {"window": resolve_square_window(self._window_m, grid.cell_size_ns_m)}

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        offsets = square_offsets(resolved["window"].cells)
        return grid.values - stacked_neighbors(grid.values, offsets).mean(axis=0)


class BpiRecipe(CovariateRecipe):
    """`bathymetric_position_index`: cell minus mean(annulus), radii in
    metres resolved at runtime. If the resolved outer radius does not exceed
    the inner (possible when both clamp on a coarse DEM), outer is bumped to
    inner + 1 and marked clamped — an empty annulus is never computed."""

    RECIPE = "bathymetric_position_index"
    RECIPE_VERSION = 2

    def __init__(self, name: str, params: dict) -> None:
        super().__init__(name)
        _require_params(name, params, {"inner_radius_m", "outer_radius_m"})
        self._inner_m = float(params["inner_radius_m"])
        self._outer_m = float(params["outer_radius_m"])
        if self._outer_m <= self._inner_m:
            raise ValueError(f"bpi outer_radius_m ({self._outer_m}) must exceed inner_radius_m ({self._inner_m})")

    def _params_requested(self) -> dict:
        return {"inner_radius_m": self._inner_m, "outer_radius_m": self._outer_m}

    def _resolve_windows(self, grid: DemGrid) -> dict[str, ResolvedWindow]:
        inner = resolve_radius(self._inner_m, grid.cell_size_ns_m)
        outer = resolve_radius(self._outer_m, grid.cell_size_ns_m)
        if outer.cells <= inner.cells:
            outer = ResolvedWindow(
                requested_m=outer.requested_m,
                cell_size_m=outer.cell_size_m,
                cells=inner.cells + 1,
                clamped=True,
            )
        return {"inner_radius": inner, "outer_radius": outer}

    def _compute(self, grid: DemGrid, resolved: dict[str, ResolvedWindow]) -> np.ndarray:
        offsets = annulus_offsets(resolved["inner_radius"].cells, resolved["outer_radius"].cells)
        return grid.values - stacked_neighbors(grid.values, offsets).mean(axis=0)
