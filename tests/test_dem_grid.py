"""DemGrid: the approved CRS strategy (Preflight 3, strategy A — per-row
longitude scaling) and the physical cell geometry every recipe consumes.
Every expected value below is INDEPENDENT physical arithmetic (degrees x
111,320 m/deg x cos(latitude)), never read back from the code under test.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.features.dem_grid import DemGrid
from tests.fixtures.rasters import write_test_raster

RES_DEG = 0.01
NORTH = 14.0
WEST = -126.0


def _write_grid(tmp_path: Path, values: np.ndarray, crs: str = "EPSG:4326") -> Path:
    path = tmp_path / "dem.tif"
    write_test_raster(path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=RES_DEG, crs=crs)
    return path


def test_load_reads_shape_resolution_and_crs(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    assert grid.values.shape == (6, 4)
    assert grid.res_x_deg == pytest.approx(RES_DEG)
    assert grid.res_y_deg == pytest.approx(RES_DEG)
    assert grid.crs == "EPSG:4326"
    assert grid.content_hash.startswith("sha256:")


def test_lat_per_row_is_cell_centres(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    for row in range(6):
        assert grid.lat_per_row[row] == pytest.approx(NORTH - (row + 0.5) * RES_DEG)


def test_dx_m_varies_per_row_with_cos_latitude(tmp_path: Path) -> None:
    """Strategy A: E-W cell size shrinks with cos(latitude), row by row."""
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    for row in range(6):
        lat = NORTH - (row + 0.5) * RES_DEG
        expected = RES_DEG * 111_320.0 * math.cos(math.radians(lat))
        assert grid.dx_m_per_row[row] == pytest.approx(expected, rel=1e-12)
    # Rows must actually differ — a single reference latitude would fail here.
    assert grid.dx_m_per_row[0] != grid.dx_m_per_row[-1]


def test_dy_m_is_constant_from_ns_resolution(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    assert grid.dy_m == pytest.approx(RES_DEG * 111_320.0, rel=1e-12)
    assert grid.cell_size_ns_m == grid.dy_m


def test_non_geographic_crs_is_rejected(tmp_path: Path) -> None:
    """A metric CRS silently treated as degrees would corrupt every physical
    conversion — the loader must refuse, not guess."""
    path = _write_grid(tmp_path, np.full((6, 4), -4200.0), crs="EPSG:3857")
    with pytest.raises(ValueError, match="EPSG:4326"):
        DemGrid.load(path)
