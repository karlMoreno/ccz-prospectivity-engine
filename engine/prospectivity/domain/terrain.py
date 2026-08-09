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
    # P2.0d-3: the layer's DECLARED origin (the CLAUDE.md data-origin
    # vocabulary; engine/prospectivity/provenance/origin.py), set by the
    # TerrainSource that produced it from the P2.0c markers — NEVER inferred
    # from name/title/path, the defect class the taxonomy replaced. None
    # means undeclared: downstream watermarks default ON (absence of proof
    # produces a watermark, never a clean render).
    data_origin: str | None = None
