"""The 8 Option-A recipes: known values in PHYSICAL units, border policy,
determinism, and clamp provenance.

The known-value oracles are physical-distance arithmetic written directly in
the tests (e.g. a plane dropping 100 m over 10 km must slope at
atan(100/10,000) = 0.5729 degrees) — deliberately NOT cell-index arithmetic,
which would pass even if degrees were never converted to metres.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipes import (
    BpiRecipe,
    DepthRecipe,
    HornAspectRecipe,
    HornSlopeRecipe,
    PlanCurvatureRecipe,
    ProfileCurvatureRecipe,
    RoughnessRecipe,
    TpiRecipe,
)
from engine.prospectivity.features.registry import build_default_registry
from tests.fixtures.rasters import write_synthetic_bathymetry, write_test_raster

RES_DEG = 0.01
NORTH = 14.0
WEST = -126.0
M_PER_DEG = 111_320.0
DY_M = RES_DEG * M_PER_DEG  # 1113.2 m N-S cell size at this resolution


def _grid(tmp_path: Path, values: np.ndarray, name: str = "dem.tif") -> DemGrid:
    path = tmp_path / name
    write_test_raster(path, values.astype("float64"), west=WEST, north=NORTH, pixel_size_deg=RES_DEG)
    return DemGrid.load(path)


def _ns_plane(rows: int = 12, cols: int = 10, drop_per_10km_m: float = 100.0) -> np.ndarray:
    """Elevation falling southward at `drop_per_10km_m` per 10 km — the
    physically-defined test surface. Per-row drop = dy_m * gradient."""
    gradient = drop_per_10km_m / 10_000.0
    row_indices = np.arange(rows)[:, np.newaxis]
    return -4000.0 - row_indices * (DY_M * gradient) * np.ones((rows, cols))


def _interior(values: np.ndarray, ring: int = 1) -> np.ndarray:
    return values[ring:-ring, ring:-ring]


# --- Test 4 (known values in physical units) --------------------------------


def test_slope_of_plane_dropping_100m_over_10km_is_0_573_degrees(tmp_path: Path) -> None:
    grid = _grid(tmp_path, _ns_plane())
    slope = HornSlopeRecipe("slope", {"units": "degrees"}).build(grid).values
    expected = math.degrees(math.atan(100.0 / 10_000.0))  # 0.5729... physical oracle
    assert np.allclose(_interior(slope), expected, atol=1e-9)


def test_east_west_slope_varies_per_row_with_latitude(tmp_path: Path) -> None:
    """Strategy A pinned at recipe level: the same per-column drop is a
    slightly STEEPER slope at higher latitude (shorter E-W metres). A single
    reference latitude would produce identical rows and fail here."""
    drop_per_column_m = 5.0
    columns = np.arange(10)[np.newaxis, :]
    grid = _grid(tmp_path, -4000.0 - drop_per_column_m * columns * np.ones((12, 10)))
    slope = HornSlopeRecipe("slope", {"units": "degrees"}).build(grid).values
    for row in range(1, 11):
        lat = NORTH - (row + 0.5) * RES_DEG
        dx_m = RES_DEG * M_PER_DEG * math.cos(math.radians(lat))
        expected = math.degrees(math.atan(drop_per_column_m / dx_m))
        assert np.allclose(slope[row, 1:-1], expected, atol=1e-9)
    interior_row_means = [slope[row, 1:-1].mean() for row in range(1, 11)]
    assert np.ptp(interior_row_means) > 1e-7  # rows genuinely differ


def test_aspect_points_downslope_south_and_east(tmp_path: Path) -> None:
    params = {"units": "degrees", "undefined_flat_as": -1}
    south_dipping = _grid(tmp_path, _ns_plane(), name="south.tif")
    aspect = HornAspectRecipe("aspect", params).build(south_dipping).values
    assert np.allclose(_interior(aspect), 180.0, atol=1e-9)

    columns = np.arange(10)[np.newaxis, :]
    east_dipping = _grid(tmp_path, -4000.0 - 5.0 * columns * np.ones((12, 10)), name="east.tif")
    aspect = HornAspectRecipe("aspect", params).build(east_dipping).values
    assert np.allclose(_interior(aspect), 90.0, atol=1e-9)


def test_aspect_of_flat_terrain_is_the_contract_sentinel(tmp_path: Path) -> None:
    grid = _grid(tmp_path, np.full((8, 8), -4200.0))
    aspect = HornAspectRecipe("aspect", {"units": "degrees", "undefined_flat_as": -1}).build(grid).values
    assert (_interior(aspect) == -1.0).all()


def test_curvatures_of_a_plane_are_zero(tmp_path: Path) -> None:
    grid = _grid(tmp_path, _ns_plane())  # tilted, so p,q != 0: real code path
    profile = ProfileCurvatureRecipe("profile_curvature", {}).build(grid).values
    plan = PlanCurvatureRecipe("plan_curvature", {}).build(grid).values
    assert np.allclose(_interior(profile), 0.0, atol=1e-15)
    assert np.allclose(_interior(plan), 0.0, atol=1e-15)


def test_curvatures_of_a_dome_are_positive(tmp_path: Path) -> None:
    """Sign convention: convex-up (dome) => positive, both curvatures."""
    rows, cols = np.mgrid[0:13, 0:13]
    dome = -4000.0 - 0.05 * ((rows - 6.0) ** 2 + (cols - 6.0) ** 2)
    grid = _grid(tmp_path, dome)
    profile = ProfileCurvatureRecipe("profile_curvature", {}).build(grid).values
    plan = PlanCurvatureRecipe("plan_curvature", {}).build(grid).values
    interior_mask = np.zeros_like(dome, dtype=bool)
    interior_mask[1:-1, 1:-1] = True
    interior_mask[6, 6] = False  # apex: p = q = 0 -> defined as 0
    assert (profile[interior_mask] > 0).all()
    assert (plan[interior_mask] > 0).all()
    assert profile[6, 6] == 0.0 and plan[6, 6] == 0.0


def test_roughness_of_uniform_gradient_is_analytic(tmp_path: Path) -> None:
    """3x3 window on a uniform N-S gradient: values {z+d, z, z-d} three of
    each -> population stdev d*sqrt(2/3), with d from physical metres."""
    grid = _grid(tmp_path, _ns_plane())
    window_m = 3 * DY_M  # resolves to exactly 3 cells, no clamp
    result = RoughnessRecipe("roughness", {"window_m": window_m}).build(grid)
    per_row_drop = DY_M * (100.0 / 10_000.0)
    expected = per_row_drop * math.sqrt(2.0 / 3.0)
    assert np.allclose(_interior(result.values), expected, atol=1e-9)
    assert result.provenance["resolved_windows"]["window"]["cells"] == 3
    assert not result.provenance["resolved_windows"]["window"]["clamped"]


def test_tpi_is_zero_on_a_plane_and_positive_on_a_bump(tmp_path: Path) -> None:
    window_m = 3 * DY_M
    plane = _grid(tmp_path, _ns_plane(), name="plane.tif")
    tpi = TpiRecipe("tpi", {"window_m": window_m}).build(plane).values
    assert np.allclose(_interior(tpi), 0.0, atol=1e-9)

    bumped_values = np.full((9, 9), -4200.0)
    bumped_values[4, 4] += 10.0
    bumped = _grid(tmp_path, bumped_values, name="bump.tif")
    tpi = TpiRecipe("tpi", {"window_m": window_m}).build(bumped).values
    # Contract definition: cell minus mean(window INCLUSIVE) = 10 - 10/9.
    assert tpi[4, 4] == pytest.approx(10.0 - 10.0 / 9.0)
    assert tpi[4, 3] == pytest.approx(-10.0 / 9.0)


def test_bpi_is_zero_on_a_plane(tmp_path: Path) -> None:
    grid = _grid(tmp_path, _ns_plane())
    result = BpiRecipe("bpi", {"inner_radius_m": DY_M, "outer_radius_m": 2 * DY_M}).build(grid)
    assert np.allclose(_interior(result.values, ring=2), 0.0, atol=1e-9)


def test_depth_is_the_dem_passthrough(tmp_path: Path) -> None:
    grid = _grid(tmp_path, _ns_plane())
    depth = DepthRecipe("depth", {}).build(grid).values
    assert np.array_equal(depth, grid.values)


# --- Test 5 (border policy: nan_border) -------------------------------------


def test_border_cells_are_nan_exactly_to_the_neighborhood_radius(tmp_path: Path) -> None:
    """The declared policy: a cell is NaN iff its full neighborhood leaves
    the raster — a 1-cell ring for 3x3 stencils, a 2-cell ring for the
    2-cell-radius BPI annulus, and no ring at all for passthrough depth."""
    grid = _grid(tmp_path, _ns_plane())

    slope = HornSlopeRecipe("slope", {"units": "degrees"}).build(grid).values
    ring = np.ones_like(slope, dtype=bool)
    ring[1:-1, 1:-1] = False
    assert np.isnan(slope[ring]).all() and not np.isnan(slope[~ring]).any()

    roughness = RoughnessRecipe("roughness", {"window_m": 3 * DY_M}).build(grid).values
    assert np.isnan(roughness[ring]).all() and not np.isnan(roughness[~ring]).any()

    bpi = BpiRecipe("bpi", {"inner_radius_m": DY_M, "outer_radius_m": 2 * DY_M}).build(grid).values
    ring2 = np.ones_like(bpi, dtype=bool)
    ring2[2:-2, 2:-2] = False
    assert np.isnan(bpi[ring2]).all() and not np.isnan(bpi[~ring2]).any()

    depth = DepthRecipe("depth", {}).build(grid).values
    assert not np.isnan(depth).any()


def test_every_recipe_declares_the_border_policy_in_provenance(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    for result in build_default_registry().build_all(DemGrid.load(dem_path)):
        assert result.provenance["border_policy"]["name"] == "nan_border"


# --- Test 1 (determinism) ---------------------------------------------------


def test_every_recipe_is_byte_deterministic(tmp_path: Path) -> None:
    """Same DEM in, byte-identical array out — for all 8, via two
    independently constructed registries."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    first = build_default_registry().build_all(DemGrid.load(dem_path))
    second = build_default_registry().build_all(DemGrid.load(dem_path))
    assert [r.name for r in first] == [r.name for r in second]
    for result_a, result_b in zip(first, second):
        assert result_a.values.tobytes() == result_b.values.tobytes()


# --- Clamp provenance (approved Preflight-2 note: clamping on the coarse
# --- synthetic DEM is by design and must be RECORDED, not hidden) -----------


def test_clamped_windows_on_the_coarse_synthetic_dem_are_recorded(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)  # 0.1 deg cells: ~11,132 m N-S
    grid = DemGrid.load(dem_path)
    registry = build_default_registry()

    roughness = registry.build("roughness", grid).provenance["resolved_windows"]["window"]
    assert roughness["requested_m"] == 1400.0
    assert roughness["cells"] == 3
    assert roughness["clamped"] is True

    bpi = registry.build("bpi", grid).provenance["resolved_windows"]
    assert bpi["inner_radius"]["clamped"] is True and bpi["inner_radius"]["cells"] == 1
    # Outer also clamps (0.2 cells raw -> 1), then bumps past inner to 2.
    assert bpi["outer_radius"]["clamped"] is True and bpi["outer_radius"]["cells"] == 2


def test_slope_rejects_units_the_implementation_does_not_have(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="degrees"):
        HornSlopeRecipe("slope", {"units": "radians"})
