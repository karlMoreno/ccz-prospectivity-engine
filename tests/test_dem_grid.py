"""DemGrid: the approved CRS strategy (Preflight 3, strategy A — per-row
longitude scaling) and the physical cell geometry every recipe consumes.
Every expected value below is INDEPENDENT physical arithmetic (degrees x
111,320 m/deg x cos(latitude)), never read back from the code under test.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.features.dem_grid import DemGrid
from tests.fixtures.rasters import write_test_raster

RES_DEG = 0.01
NORTH = 14.0
WEST = -126.0


def _write_grid(tmp_path: Path, values: np.ndarray, crs: str = "EPSG:4326") -> Path:
    path = tmp_path / "dem.tif"
    write_test_raster(path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=RES_DEG, crs=crs)
    return path


def test_load_reads_shape_resolution_and_crs(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    assert grid.values.shape == (6, 4)
    assert grid.res_x_deg == pytest.approx(RES_DEG)
    assert grid.res_y_deg == pytest.approx(RES_DEG)
    assert grid.crs == "EPSG:4326"
    assert grid.content_hash.startswith("sha256:")


def test_lat_per_row_is_cell_centres(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    for row in range(6):
        assert grid.lat_per_row[row] == pytest.approx(NORTH - (row + 0.5) * RES_DEG)


def test_dx_m_varies_per_row_with_cos_latitude(tmp_path: Path) -> None:
    """Strategy A: E-W cell size shrinks with cos(latitude), row by row."""
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    for row in range(6):
        lat = NORTH - (row + 0.5) * RES_DEG
        expected = RES_DEG * 111_320.0 * math.cos(math.radians(lat))
        assert grid.dx_m_per_row[row] == pytest.approx(expected, rel=1e-12)
    # Rows must actually differ — a single reference latitude would fail here.
    assert grid.dx_m_per_row[0] != grid.dx_m_per_row[-1]


def test_dy_m_is_constant_from_ns_resolution(tmp_path: Path) -> None:
    grid = DemGrid.load(_write_grid(tmp_path, np.full((6, 4), -4200.0)))
    assert grid.dy_m == pytest.approx(RES_DEG * 111_320.0, rel=1e-12)
    assert grid.cell_size_ns_m == grid.dy_m


def test_non_geographic_crs_is_rejected(tmp_path: Path) -> None:
    """A metric CRS silently treated as degrees would corrupt every physical
    conversion — the loader must refuse, not guess."""
    path = _write_grid(tmp_path, np.full((6, 4), -4200.0), crs="EPSG:3857")
    with pytest.raises(ValueError, match="EPSG:4326"):
        DemGrid.load(path)


# --- E1.5 follow-up: the TerrainSource STRATEGY seam ------------------------


def test_from_terrain_source_loads_through_the_strategy_seam(tmp_path: Path) -> None:
    """The wiring that makes synthetic -> real GEBCO a substitution at the seam
    (Checkpoint 1) rather than an edit to every caller: swap the injected
    TerrainSource, change nothing in DemGrid or any recipe."""
    from engine.prospectivity.domain.study_area import StudyArea
    from tests.fixtures.rasters import FixtureTerrainSource, write_synthetic_bathymetry

    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    study_area = StudyArea(
        area_id="test_area",
        name="Test AOI",
        geometry={
            "type": "Polygon",
            "coordinates": [[[-127, 11], [-125, 11], [-125, 13], [-127, 13], [-127, 11]]],
        },
    )

    via_seam = DemGrid.from_terrain_source(FixtureTerrainSource(dem_path), study_area)
    directly = DemGrid.load(dem_path)

    assert via_seam.content_hash == directly.content_hash
    assert via_seam.values.tobytes() == directly.values.tobytes()
    assert via_seam.crs == "EPSG:4326"


def test_fixture_terrain_source_reports_a_real_computed_hash_not_a_placeholder(
    tmp_path: Path,
) -> None:
    """The placeholder this replaces ("sha256:synthetic-fixture") is exactly
    the kind of fake provenance the manifest work exists to eliminate. Being
    synthetic is recorded in the layer's name, never by faking a hash."""
    import hashlib

    from tests.fixtures.rasters import FixtureTerrainSource, write_synthetic_bathymetry

    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    layer = FixtureTerrainSource(dem_path).load(study_area=None)  # type: ignore[arg-type]

    expected = "sha256:" + hashlib.sha256(dem_path.read_bytes()).hexdigest()
    assert layer.content_hash == expected
    assert "synthetic-fixture" not in layer.content_hash


def test_from_terrain_source_rejects_a_layer_whose_hash_it_did_not_compute(
    tmp_path: Path,
) -> None:
    """A TerrainSource that reports a hash not matching the bytes read must
    fail loudly — otherwise provenance is seeded with a fiction and every
    downstream artifact quotes it."""
    from engine.prospectivity.domain.terrain import TerrainLayer
    from engine.prospectivity.terrain.source import TerrainSource
    from tests.fixtures.rasters import write_synthetic_bathymetry

    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)

    class _LyingTerrainSource(TerrainSource):
        def load(self, study_area) -> TerrainLayer:  # type: ignore[override]
            return TerrainLayer(
                name="bathymetry",
                path=str(dem_path),
                content_hash="sha256:" + "0" * 64,
            )

    with pytest.raises(ValueError, match="does not match"):
        DemGrid.from_terrain_source(_LyingTerrainSource(), study_area=None)  # type: ignore[arg-type]


def test_from_terrain_source_rejects_a_layer_with_no_path(tmp_path: Path) -> None:
    from engine.prospectivity.domain.terrain import TerrainLayer
    from engine.prospectivity.terrain.source import TerrainSource

    class _PathlessTerrainSource(TerrainSource):
        def load(self, study_area) -> TerrainLayer:  # type: ignore[override]
            return TerrainLayer(name="bathymetry")

    with pytest.raises(ValueError, match="no path"):
        DemGrid.from_terrain_source(_PathlessTerrainSource(), study_area=None)  # type: ignore[arg-type]


def test_from_terrain_layer_is_what_the_engine_seam_produces(tmp_path: Path) -> None:
    """The bridge Phase 2's feature_builder will use: ProspectivityEngine
    already hands a TerrainLayer to feature_builder, so consuming a LAYER (not
    a source, not a path) is the shape that closes the bypass."""
    from engine.prospectivity.domain.terrain import TerrainLayer
    from tests.fixtures.rasters import write_synthetic_bathymetry

    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    layer = TerrainLayer(name="bathymetry", path=str(dem_path))

    grid = DemGrid.from_terrain_layer(layer)
    assert grid.content_hash == DemGrid.load(dem_path).content_hash


# ── G.3 commit 3: the axis-aligned/north-up assertion (BACKLOG §3, E2.0-2) ──


def _write_with_transform(tmp_path: Path, transform) -> Path:
    import rasterio

    path = tmp_path / "odd.tif"
    with rasterio.open(
        path, "w", driver="GTiff", height=6, width=4, count=1,
        dtype="float32", crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(np.full((6, 4), -4200.0, dtype="float32"), 1)
    return path


def test_a_rotated_transform_is_refused_naming_its_shear_terms(tmp_path: Path) -> None:
    """The E2.0-2 probe's failure mode: shear terms non-zero loaded silently
    with normal-looking res values and every geolocation wrong. Now refused
    at load, with b and d in the message."""
    from affine import Affine

    rotated = Affine(RES_DEG, 0.003, WEST, 0.003, -RES_DEG, NORTH)
    with pytest.raises(ValueError, match=r"rotation/shear terms b=0\.003, d=0\.003"):
        DemGrid.load(_write_with_transform(tmp_path, rotated))


def test_a_south_up_transform_is_refused_naming_orientation_not_window_math(tmp_path: Path) -> None:
    """South-up (e > 0) used to die later in the windowed recipes blaming
    'window_m and cell_size_m must be positive' — the wrong thing by name.
    Now refused at load, naming the orientation."""
    from affine import Affine

    south_up = Affine(RES_DEG, 0.0, WEST, 0.0, RES_DEG, NORTH - 6 * RES_DEG)
    with pytest.raises(ValueError, match="north-up orientation"):
        DemGrid.load(_write_with_transform(tmp_path, south_up))


def test_the_real_gebco_subset_passes_the_orientation_assertion_whenever_present() -> None:
    """Today's actual GEBCO_2026 subset satisfies the load-time predicate
    (verified north-up, shear-free at G.3) — an assertion that happens to
    pass today is still the observer for tomorrow's file. Checks the SAME
    predicate DemGrid.load enforces, on the real file's transform via
    rasterio directly, because DemGrid.load would also read the full 144 MB
    band. Skips by name when the gitignored raster is absent."""
    import rasterio

    real = Path(__file__).resolve().parents[1] / "data" / "bathymetry" / "gebco_2026_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif"
    if not real.is_file():
        pytest.skip("gitignored GEBCO raster not present locally")
    with rasterio.open(real) as src:
        t = src.transform
    assert t.b == 0.0 and t.d == 0.0 and t.a > 0.0 and t.e < 0.0
