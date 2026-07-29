"""Synthetic bathymetry + TS-6 rasters (E0.4). Generated on the fly via
rasterio + numpy rather than committed as binary fixtures, so the repo stays
free of tracked .tif blobs while still exercising TerrainSource/TS6Reference
end-to-end in CI.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.ts6.reference import TS6Reference

PIXEL_SIZE_DEG = 0.1
# SYNTHETIC extent, E1.4 Preflight 1 (2026-07-28): covers the REAL corpus's 35
# training-eligible MASS points (lon -125.93..-117.01, lat 11.84..14.12) plus a
# 0.5-degree margin. The previous extent matched study_area.geojson's
# placeholder AOI (-127..-125, 11..13) and contained ZERO corpus points, which
# made any corpus-over-DEM deliverable unproducible. study_area.geojson itself
# is deliberately NOT changed here — the real AOI is a separate open decision.
# Depth values remain random noise (seeded, reproducible): synthetic, never to
# be mistaken for real bathymetry.
WEST, NORTH = -126.5, 14.7
GRID_WIDTH = 100  # -> east edge -116.5
GRID_HEIGHT = 34  # -> south edge 11.3


def write_test_raster(
    path: Path,
    values: np.ndarray,
    west: float,
    north: float,
    pixel_size_deg: float,
    crs: str = "EPSG:4326",
) -> None:
    """Parameterized raster writer for E1.4's covariate tests: hand-built
    elevation arrays at chosen origins/resolutions (known-value, border and
    scale-invariance cases need specific physical geometries)."""
    transform = from_origin(west, north, pixel_size_deg, pixel_size_deg)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype=values.dtype,
        crs=crs,
        transform=transform,
    ) as dataset:
        dataset.write(values, 1)


def _write_synthetic_raster(path: Path, values: np.ndarray) -> None:
    write_test_raster(path, values, west=WEST, north=NORTH, pixel_size_deg=PIXEL_SIZE_DEG)


def write_synthetic_bathymetry(path: Path) -> None:
    rng = np.random.default_rng(seed=0)
    depths = -4000.0 - rng.random((GRID_HEIGHT, GRID_WIDTH)) * 400.0
    _write_synthetic_raster(path, depths.astype("float32"))


def write_synthetic_ts6_raster(path: Path) -> None:
    # Shares the DEM's extent on purpose: the TS-6 benchmark comparison
    # (Phase 4) only makes sense where benchmark and prediction overlap.
    rng = np.random.default_rng(seed=1)
    abundance = 4.0 + rng.random((GRID_HEIGHT, GRID_WIDTH)) * 4.0
    _write_synthetic_raster(path, abundance.astype("float32"))


class FixtureTerrainSource(TerrainSource):
    def __init__(self, raster_path: Path) -> None:
        self._raster_path = raster_path

    def load(self, study_area: StudyArea) -> TerrainLayer:
        return TerrainLayer(
            name="bathymetry",
            source_id="src_bathymetry_primary",
            path=str(self._raster_path),
            content_hash="sha256:synthetic-fixture",
        )


class FixtureTS6Reference(TS6Reference):
    def __init__(self, raster_path: Path) -> None:
        self._raster_path = raster_path

    def load(self) -> TS6Surface:
        return TS6Surface(
            title="Synthetic TS-6 benchmark (fixture)",
            source_id="src_ts6_grid",
            raster_path=str(self._raster_path),
            role_note="benchmark_only",
            content_hash="sha256:synthetic-fixture",
        )
