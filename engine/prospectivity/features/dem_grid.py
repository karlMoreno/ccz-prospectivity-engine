"""DemGrid — the loaded DEM plus its physical cell geometry.

This is the ONE place the CRS decision lives (E1.4 Preflight 3, approved
2026-07-28: strategy A, per-row longitude scaling). The DEM — synthetic today,
real GEBCO after Checkpoint 1 — is EPSG:4326: horizontal spacing in degrees,
elevation in metres. Every derivative recipe needs metres in both, so:

    dy_m        = res_y_deg * M_PER_DEG                     (constant N-S)
    dx_m[row]   = res_x_deg * M_PER_DEG * cos(lat[row])     (per-row E-W)

Per-row scaling makes the E-W spacing essentially exact everywhere on the
raster (residual < 0.1%, from within-cell latitude variation), where a single
reference latitude would be off by up to ~0.7% at this raster's N/S edges.
No reprojection: resampling would interpolate the elevations themselves and
break cell-level traceability to the source DEM.

`cell_size_ns_m` (== dy_m) is the ONE deterministic scalar used to resolve
Contract 3's metre-based windows into cell counts (window.py): the N-S cell
size is latitude-independent on a geographic raster, so the resolved window
never depends on where the raster sits. The E-W physical span of that window
then deviates from the N-S span by <= ~3% at study latitudes — recorded in
provenance, not hidden.

Recipes receive a DemGrid and never touch rasterio or degrees directly —
if a metric-CRS DEM ever arrives, this loader (not the recipes) changes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import rasterio
from affine import Affine

if TYPE_CHECKING:  # import-time cycle avoidance only; these are type hints
    from engine.prospectivity.domain.study_area import StudyArea
    from engine.prospectivity.domain.terrain import TerrainLayer
    from engine.prospectivity.terrain.source import TerrainSource

# Spherical approximation: metres per degree of latitude (and of longitude at
# the equator), WGS84 mean. Documented constant so every physical conversion
# in the engine agrees; the ~0.3% ellipsoidal variation in metres-per-degree
# of latitude is far below the geology's precision.
M_PER_DEG = 111_320.0


@dataclass(frozen=True)
class DemGrid:
    """The DEM array plus everything needed to compute in physical units."""

    values: np.ndarray  # (H, W) float64 elevation in metres (negative down)
    transform: Affine  # geotransform (for writing derived rasters)
    crs: str  # always "EPSG:4326" (load() enforces it)
    res_x_deg: float
    res_y_deg: float
    lat_per_row: np.ndarray  # (H,) cell-CENTRE latitudes, north to south
    dx_m_per_row: np.ndarray  # (H,) E-W cell size in metres (strategy A)
    dy_m: float  # N-S cell size in metres (constant)
    path: str
    content_hash: str  # sha256 of the source file bytes (provenance)

    @property
    def cell_size_ns_m(self) -> float:
        """The scalar cell size used for metres->cells window resolution."""
        return self.dy_m

    @classmethod
    def from_terrain_source(
        cls, terrain_source: "TerrainSource", study_area: "StudyArea"
    ) -> "DemGrid":
        """Convenience: run the STRATEGY, then bridge its layer.

        Equivalent to `from_terrain_layer(terrain_source.load(study_area))`.
        Use this when you hold the source; use `from_terrain_layer` when you
        already hold the layer — which is what `ProspectivityEngine` does.
        """
        return cls.from_terrain_layer(terrain_source.load(study_area))

    @classmethod
    def from_terrain_layer(cls, layer: "TerrainLayer") -> "DemGrid":
        """Bridge a TerrainLayer into a DemGrid — the missing link that made
        E1.4 bypass the TerrainSource seam (fixed 2026-07-29, E1.5 follow-up).

        The seam itself was never absent: `ProspectivityEngine._ingest` already
        calls `terrain_source.load(study_area)` and hands the resulting
        TerrainLayer to `feature_builder`. What was missing was any way for
        `features/` to CONSUME one, so `DemGrid.load(path)` read the raster
        directly and the interface for "where does the bathymetry come from"
        had a real consumer that ignored it. With this bridge, Phase 2's
        feature_builder takes the layer the engine already produced, and
        synthetic -> real GEBCO becomes a substitution AT the seam
        (Checkpoint 1): swap the injected TerrainSource, change nothing here
        and nothing in any recipe.

        The layer's own `content_hash` is verified against the bytes actually
        read, so a TerrainSource that reports a hash it didn't compute fails
        loudly rather than seeding provenance with a fiction.
        """
        if layer.path is None:
            raise ValueError(
                f"TerrainLayer {layer.name!r} has no path; DemGrid needs a readable raster"
            )
        grid = cls.load(Path(layer.path))
        if layer.content_hash is not None and layer.content_hash != grid.content_hash:
            raise ValueError(
                f"TerrainLayer.content_hash ({layer.content_hash}) does not match the "
                f"SHA-256 of the bytes actually read ({grid.content_hash}) — a layer "
                "must not report a hash it did not compute"
            )
        return grid

    @classmethod
    def load(cls, path: Path) -> "DemGrid":
        raw = Path(path).read_bytes()
        content_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
        with rasterio.open(path) as dataset:
            crs = dataset.crs.to_string() if dataset.crs else None
            if crs != "EPSG:4326":
                # Only geographic handling (strategy A) is implemented; a
                # metric or missing CRS silently treated as degrees would
                # corrupt every physical conversion downstream.
                raise ValueError(
                    f"DemGrid requires EPSG:4326 (got {crs!r}) — see dem_grid.py "
                    "for the approved CRS strategy"
                )
            transform = dataset.transform
            values = dataset.read(1).astype(np.float64)

        res_x_deg = transform.a
        res_y_deg = -transform.e
        north = transform.f
        height = values.shape[0]
        lat_per_row = north - (np.arange(height) + 0.5) * res_y_deg
        dx_m_per_row = res_x_deg * M_PER_DEG * np.cos(np.radians(lat_per_row))
        dy_m = res_y_deg * M_PER_DEG
        return cls(
            values=values,
            transform=transform,
            crs=crs,
            res_x_deg=res_x_deg,
            res_y_deg=res_y_deg,
            lat_per_row=lat_per_row,
            dx_m_per_row=dx_m_per_row,
            dy_m=dy_m,
            path=str(path),
            content_hash=content_hash,
        )

    def provenance(self) -> dict:
        """The DEM facts every covariate layer's provenance must carry.

        HASH.1 commit 2 (2026-08-22): NO PATH. This dict is quoted nine
        times in the feature-stack manifest's substance (once at `dem`, once
        per layer), and the caller-supplied path string made the stack's
        content_hash vary with the directory it was built from — and with
        relative-vs-absolute in the SAME directory (E2.4 audit row M). The
        path is a LOCATION, not an identity: two DEMs with identical bytes
        are one DEM, and `content_hash` already says which. The location is
        still recorded, once, OUTSIDE the hash
        (`FeatureStackManifest.dem_path`, the `generated_at` precedent)."""
        return {
            "content_hash": self.content_hash,
            "crs": self.crs,
            "resolution_deg": [self.res_x_deg, self.res_y_deg],
            "cell_size_ns_m": self.cell_size_ns_m,
            "shape": list(self.values.shape),
        }
