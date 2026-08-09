"""Synthetic bathymetry + TS-6 rasters (E0.4) round-trip through rasterio and
their Fixture Strategy wrappers (FixtureTerrainSource / FixtureTS6Reference).
"""

from __future__ import annotations

from pathlib import Path

import rasterio

from engine.prospectivity.domain.study_area import StudyArea
from tests.fixtures.rasters import FixtureTerrainSource, FixtureTS6Reference


def _study_area() -> StudyArea:
    return StudyArea(
        area_id="test_area",
        name="Test AOI",
        geometry={
            "type": "Polygon",
            "coordinates": [[[-127, 11], [-125, 11], [-125, 13], [-127, 13], [-127, 11]]],
        },
    )


def test_synthetic_bathymetry_is_a_valid_raster(synthetic_bathymetry_path: Path) -> None:
    with rasterio.open(synthetic_bathymetry_path) as dataset:
        assert dataset.count == 1
        assert dataset.crs.to_string() == "EPSG:4326"
        assert (dataset.read(1) < 0).all()


def test_fixture_terrain_source_returns_a_terrain_layer(synthetic_bathymetry_path: Path) -> None:
    terrain_source = FixtureTerrainSource(synthetic_bathymetry_path)
    layer = terrain_source.load(_study_area())
    assert layer.name == "bathymetry"
    assert layer.path == str(synthetic_bathymetry_path)


def test_fixture_terrain_layer_declares_synthetic_origin(synthetic_bathymetry_path: Path) -> None:
    """P2.0d-3: the layer carries a DECLARATION sourced from the module's own
    P2.0c marker (rasters.DATA_ORIGIN) — never inferred from the layer's
    name. This is what downstream watermarks derive from; an undeclared
    layer (data_origin None) watermarks as NOT DECLARED, default-on."""
    layer = FixtureTerrainSource(synthetic_bathymetry_path).load(_study_area())
    assert layer.data_origin == "SYNTHETIC"


def test_synthetic_ts6_raster_is_a_valid_raster(synthetic_ts6_raster_path: Path) -> None:
    """Strengthened 2026-07-30 to match its bathymetry sibling above: "is a
    valid raster" now checks band count and CRS, not only the value range."""
    with rasterio.open(synthetic_ts6_raster_path) as dataset:
        assert dataset.count == 1
        assert dataset.crs.to_string() == "EPSG:4326"
        assert (dataset.read(1) > 0).all()


def test_fixture_ts6_reference_returns_a_benchmark_surface(
    synthetic_ts6_raster_path: Path,
) -> None:
    ts6_reference = FixtureTS6Reference(synthetic_ts6_raster_path)
    surface = ts6_reference.load()
    assert surface.role_note == "benchmark_only"
    assert surface.raster_path == str(synthetic_ts6_raster_path)
