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

import numpy as np
import rasterio
from affine import Affine

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
        """The DEM facts every covariate layer's provenance must carry."""
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "crs": self.crs,
            "resolution_deg": [self.res_x_deg, self.res_y_deg],
            "cell_size_ns_m": self.cell_size_ns_m,
            "shape": list(self.values.shape),
        }
