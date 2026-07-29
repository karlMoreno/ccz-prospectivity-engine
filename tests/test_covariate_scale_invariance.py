"""Test 2: scale invariance — the test that would have caught the 24x bug.

The same physical window, applied to two DEMs of different resolution, must
resolve to the SAME physical neighborhood size (different cell counts). Under
v2's cell-count contract this was impossible: 3 cells was 3 cells at any
resolution, so the measured neighborhood silently scaled with the DEM.

Mutation-verified (E1.4, by hand): replacing resolve_square_window's
conversion with a fixed `cells = 3` makes these tests fail on the effective_m
comparison. Both resolutions here resolve WITHOUT clamping, per the approved
implementation note — a clamped window would exercise the minimum, not the
conversion.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipes import BpiRecipe, RoughnessRecipe
from tests.fixtures.rasters import write_test_raster

FINE_RES_DEG = 0.002  # 222.64 m N-S cells
COARSE_RES_DEG = 0.006  # 667.92 m N-S cells
WINDOW_M = 2003.76  # exactly 9 fine cells and 3 coarse cells


def _grid(tmp_path: Path, res_deg: float, name: str) -> DemGrid:
    path = tmp_path / name
    values = np.full((24, 24), -4200.0)
    write_test_raster(path, values, west=-126.0, north=14.0, pixel_size_deg=res_deg)
    return DemGrid.load(path)


def test_same_physical_window_resolves_to_same_physical_size_across_resolutions(
    tmp_path: Path,
) -> None:
    fine = _grid(tmp_path, FINE_RES_DEG, "fine.tif")
    coarse = _grid(tmp_path, COARSE_RES_DEG, "coarse.tif")
    recipe = RoughnessRecipe("roughness", {"window_m": WINDOW_M})

    fine_window = recipe.build(fine).provenance["resolved_windows"]["window"]
    coarse_window = recipe.build(coarse).provenance["resolved_windows"]["window"]

    assert not fine_window["clamped"] and not coarse_window["clamped"]
    assert fine_window["cells"] == 9
    assert coarse_window["cells"] == 3
    assert fine_window["cells"] != coarse_window["cells"]  # conversion DID adapt
    assert fine_window["effective_m"] == pytest.approx(coarse_window["effective_m"], rel=1e-12)
    assert fine_window["effective_m"] == pytest.approx(WINDOW_M, rel=1e-12)


def test_bpi_radii_are_scale_invariant_too(tmp_path: Path) -> None:
    fine = _grid(tmp_path, FINE_RES_DEG, "fine.tif")
    coarse = _grid(tmp_path, COARSE_RES_DEG, "coarse.tif")
    recipe = BpiRecipe("bpi", {"inner_radius_m": 667.92, "outer_radius_m": WINDOW_M})

    fine_windows = recipe.build(fine).provenance["resolved_windows"]
    coarse_windows = recipe.build(coarse).provenance["resolved_windows"]

    for label in ("inner_radius", "outer_radius"):
        assert not fine_windows[label]["clamped"]
        assert not coarse_windows[label]["clamped"]
        assert fine_windows[label]["effective_m"] == pytest.approx(
            coarse_windows[label]["effective_m"], rel=1e-12
        )
    assert fine_windows["outer_radius"]["cells"] == 9
    assert coarse_windows["outer_radius"]["cells"] == 3
