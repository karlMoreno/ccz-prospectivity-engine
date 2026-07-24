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

GRID_SIZE = 20
PIXEL_SIZE_DEG = 0.1
# Matches study_area.geojson's placeholder AOI (-127..-125 lon, 11..13 lat).
WEST, NORTH = -127.0, 13.0


def _write_synthetic_raster(path: Path, values: np.ndarray) -> None:
    transform = from_origin(WEST, NORTH, PIXEL_SIZE_DEG, PIXEL_SIZE_DEG)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype=values.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dataset:
        dataset.write(values, 1)


def write_synthetic_bathymetry(path: Path) -> None:
    rng = np.random.default_rng(seed=0)
    depths = -4000.0 - rng.random((GRID_SIZE, GRID_SIZE)) * 400.0
    _write_synthetic_raster(path, depths.astype("float32"))


def write_synthetic_ts6_raster(path: Path) -> None:
    rng = np.random.default_rng(seed=1)
    abundance = 4.0 + rng.random((GRID_SIZE, GRID_SIZE)) * 4.0
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
