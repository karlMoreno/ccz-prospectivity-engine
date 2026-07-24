"""TerrainLayer — one terrain/covariate raster (bathymetry, or a Contract 3 recipe output)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TerrainLayer(BaseModel):
    """Metadata + reference for one raster layer.

    Deliberately holds a *path* to the raster rather than the array itself —
    loading/reprojection is the TerrainSource strategy's job (terrain/source.py);
    this type just describes what a layer is and where it came from.
    """

    model_config = ConfigDict(extra="forbid")

    name: str  # e.g. "bathymetry", "slope", "roughness", "tpi"
    source_id: str | None = None
    crs: str = "EPSG:4326"
    resolution_deg: float | None = None
    path: str | None = None
    recipe: str | None = None  # covariates.yaml `recipe` (e.g. "horn_slope")
    recipe_version: int | None = None  # covariates.yaml `recipe_version`
    content_hash: str | None = None
