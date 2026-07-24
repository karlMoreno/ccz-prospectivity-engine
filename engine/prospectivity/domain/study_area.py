"""StudyArea — the AOI geometry (Contract 2: study_area.geojson + exclusions.geojson)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExclusionZone(BaseModel):
    """One polygon subtracted from the minable footprint (APEI, regulatory, ...)."""

    model_config = ConfigDict(extra="forbid")

    exclusion_id: str
    name: str
    kind: str = Field(..., description="apei | regulatory | other")
    source_id: str | None = None
    geometry: dict[str, Any]


class StudyArea(BaseModel):
    """One CCZ AOI. Geometry is stored as a raw GeoJSON geometry dict (WGS84 /
    EPSG:4326 per RFC 7946, per Contract 2) and converted to a shapely shape
    lazily via `.shapely_geometry()` so importing this module never requires
    geopandas — only shapely, which is on the approved stack.
    """

    model_config = ConfigDict(extra="forbid")

    area_id: str
    name: str
    geometry: dict[str, Any]
    exclusions: list[ExclusionZone] = Field(default_factory=list)

    def shapely_geometry(self):
        from shapely.geometry import shape

        return shape(self.geometry)

    @classmethod
    def from_geojson_feature(cls, feature: dict[str, Any]) -> "StudyArea":
        props = feature.get("properties", {})
        return cls(
            area_id=props.get("area_id", "unknown"),
            name=props.get("name", ""),
            geometry=feature["geometry"],
        )
