"""FileTerrainSource — STRATEGY (the production half of the TerrainSource seam).

Until E5.5 the only TerrainSource implementation lived in
`tests/fixtures/rasters.py`, so the composition could run end to end only
from inside a test. The run harness (`engine/prospectivity/harness.py`) needs
a terrain source an operator can point at a file, and the house rule is
already written at the E1.4 plot entry point: THE DEM IS PASSED IN, engine
code never generates one and never imports `tests.*`.

    ┌────────────────┐        ┌────────────────────────────────────────┐
    │  TerrainSource  │◄───────┤ FileTerrainSource(path, data_origin=…)  │  this module
    │     (ABC)       │        │   hash ← the bytes; resolution ← the     │
    │  .load(area)    │        │   raster; origin ← the CALLER'S          │
    │  -> TerrainLayer│        │   DECLARATION (never the file's name)    │
    └────────────────┘        └────────────────────────────────────────┘
                              ┌────────────────────────────────────────┐
                              │ FixtureTerrainSource  (tests only)      │
                              └────────────────────────────────────────┘

THE ORIGIN IS DECLARED, NEVER INFERRED (P2.0d-3, declaration or nothing). A
synthetic DEM and real GEBCO bathymetry are the SAME class with a different
declaration — `SYNTHETIC` today, `MEASURED` at Checkpoint 1 — which is the
substitution the two-track design wants: swapping the terrain is a new
argument, not a new class. An undeclared origin is refused HERE, by name,
before any stack is built (the feature builder refuses it too; this source
simply cannot be constructed without one, so the refusal has the earliest
possible site).

WHAT IS READ FROM THE FILE AND WHAT IS NOT. The content hash and the pixel
size come from the bytes and the geotransform — a constant here would have
labelled a 15-arc-second GEBCO grid 0.1° (the fixture's size) at Checkpoint
1. The CRS must already be EPSG:4326: this source does not reproject, and
says so rather than silently accepting a raster whose coordinates the
recipes would misread.
"""

from __future__ import annotations

from pathlib import Path

import rasterio

from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.terrain.source import TerrainSource

CANONICAL_CRS = "EPSG:4326"
DEFAULT_SOURCE_ID = "src_bathymetry_primary"  # Contract 5's bathymetry entry
DEFAULT_LAYER_NAME = "bathymetry"


def _require_declared(data_origin: DataOrigin | str | None, what: str) -> DataOrigin:
    if data_origin is None:
        raise ValueError(
            f"{what} declares no data_origin — declaration or nothing (P2.0d-3): the "
            "origin of an input file is never inferred from its name or path, and a "
            "silent default would label real GEBCO synthetic or a fixture real. Declare "
            f"one of {[m.value for m in DataOrigin]}."
        )
    try:
        return DataOrigin(data_origin)
    except ValueError:
        raise ValueError(
            f"{what} declares data_origin {data_origin!r}, not one of "
            f"{[m.value for m in DataOrigin]}"
        ) from None


class FileTerrainSource(TerrainSource):
    """A bathymetry raster on disk, with its origin declared by the caller."""

    def __init__(
        self,
        raster_path: Path | str,
        *,
        data_origin: DataOrigin | str | None,
        source_id: str = DEFAULT_SOURCE_ID,
        name: str = DEFAULT_LAYER_NAME,
    ) -> None:
        self._raster_path = Path(raster_path)
        self._data_origin = _require_declared(data_origin, f"terrain raster {self._raster_path.name!r}")
        self._source_id = source_id
        self._name = name

    def load(self, study_area: StudyArea) -> TerrainLayer:
        path = self._raster_path
        if not path.is_file():
            raise FileNotFoundError(f"terrain raster {path} is not a file")
        with rasterio.open(path) as dataset:
            crs = dataset.crs.to_string() if dataset.crs is not None else None
            transform = dataset.transform
        if crs != CANONICAL_CRS:
            raise ValueError(
                f"terrain raster {path.name!r} is in CRS {crs!r}, not {CANONICAL_CRS} — this "
                "source does not reproject; supply the DEM in the canonical CRS"
            )
        res_x, res_y = abs(transform.a), abs(transform.e)
        if abs(res_x - res_y) > 1e-12:
            raise ValueError(
                f"terrain raster {path.name!r} has non-square cells ({res_x} x {res_y} deg) — "
                "TerrainLayer records one resolution_deg, and a single number would misstate it"
            )
        return TerrainLayer(
            name=self._name,
            source_id=self._source_id,
            crs=crs,
            path=str(path),
            content_hash=file_sha256(path),  # the bytes, never a placeholder
            resolution_deg=float(res_x),  # the geotransform, never a constant
            data_origin=self._data_origin.value,  # the DECLARATION
        )
