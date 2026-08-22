"""Synthetic bathymetry + TS-6 rasters (E0.4). Generated on the fly via
rasterio + numpy rather than committed as binary fixtures, so the repo stays
free of tracked .tif blobs while still exercising TerrainSource/TS6Reference
end-to-end in CI.

data_origin: SYNTHETIC — the ONE module in this repo meeting the strict
definition: deterministic generators (write_synthetic_bathymetry seed=0,
write_synthetic_ts6_raster seed=1) with the import path recorded here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.ts6.reference import TS6Reference

DATA_ORIGIN = DataOrigin.SYNTHETIC
# SYNTHETIC's evidence, machine-readable (P2.0d-2 §0.1): the generator import
# path and seeds are what separate a seeded generator from hand-typed values
# under a "synthetic_" filename — the terminology collision in origin.py.
DATA_GENERATOR = "tests.fixtures.rasters"
DATA_SEEDS = (0, 1)  # write_synthetic_bathymetry seed=0; write_synthetic_ts6_raster seed=1

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
    """Test-only TerrainSource (STRATEGY). The DEM is synthetic, but its
    content_hash is REAL: computed from the actual file bytes, not the
    "sha256:synthetic-fixture" placeholder this used to hardcode (removed
    2026-07-29, E1.5 follow-up).

    Why it matters for a fixture: `DemGrid.from_terrain_source` verifies the
    layer's reported hash against the bytes it reads, so a placeholder would
    either have to be special-cased (defeating the check for everyone) or
    would fail. A fixture that lies about provenance is exactly what the
    manifest work exists to eliminate — being synthetic is recorded in the
    layer's own name/notes, never by faking a hash.
    """

    def __init__(self, raster_path: Path) -> None:
        self._raster_path = raster_path

    def load(self, study_area: StudyArea) -> TerrainLayer:
        return TerrainLayer(
            name="bathymetry",
            source_id="src_bathymetry_primary",
            path=str(self._raster_path),
            content_hash=file_sha256(self._raster_path),
            resolution_deg=PIXEL_SIZE_DEG,
            # The DECLARATION (P2.0d-3), from this module's own P2.0c marker —
            # never inferred from the layer's name.
            data_origin=DATA_ORIGIN.value,
        )


class FixtureTS6Reference(TS6Reference):
    """Test-only TS6Reference (STRATEGY). Real computed content_hash, same
    reasoning as FixtureTerrainSource above — this carried the identical
    "sha256:synthetic-fixture" placeholder and was fixed in the same pass
    (2026-07-29), since leaving one of two identical fakes in place would just
    reintroduce the problem at Checkpoint 3."""

    def __init__(self, raster_path: Path) -> None:
        self._raster_path = raster_path

    def load(self) -> TS6Surface:
        return TS6Surface(
            title="Synthetic TS-6 benchmark (fixture)",
            source_id="src_ts6_grid",
            raster_path=str(self._raster_path),
            role_note="benchmark_only",
            content_hash=file_sha256(self._raster_path),
            # The DECLARATION (P2.0d-3 rule): this is the synthetic fixture,
            # and it says so — the comparison's origin is computed FROM this.
            data_origin="SYNTHETIC",
        )
