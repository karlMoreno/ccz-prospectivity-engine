"""build_covariate_stack: end-to-end rasters + provenance sidecar, and
file-level determinism (the E1.3 corpus-CSV bar, applied to E1.4's rasters).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from tests.fixtures.rasters import write_synthetic_bathymetry

EXPECTED_LAYERS = [
    "depth",
    "slope",
    "aspect",
    "roughness",
    "profile_curvature",
    "plan_curvature",
    "tpi",
    "bpi",
]


def _expected_border_width(layer_provenance: dict) -> int:
    """How wide this layer's NaN rim must be, read from the layer's OWN
    declared provenance rather than assumed:

      passthrough        -> 0 (single-cell neighborhood)
      resolved annulus   -> the outer radius in cells
      resolved window    -> half the odd window edge
      fixed 3x3 stencil  -> 1 (Horn / Zevenbergen-Thorne, no window param)
    """
    if layer_provenance["recipe"] == "passthrough":
        return 0
    windows = layer_provenance.get("resolved_windows") or {}
    if "outer_radius" in windows:
        return int(windows["outer_radius"]["cells"])
    if "window" in windows:
        return int(windows["window"]["cells"]) // 2
    return 1


def test_stack_writes_all_eight_layers_and_provenance(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(
        dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.SYNTHETIC
    )

    assert sorted(written) == sorted(EXPECTED_LAYERS + ["provenance"])
    for name in EXPECTED_LAYERS:
        assert written[name].exists()

    provenance = json.loads(written["provenance"].read_text())
    assert provenance["registry_version"] == 4
    assert provenance["dem"]["content_hash"].startswith("sha256:")
    assert [layer["name"] for layer in provenance["layers"]] == EXPECTED_LAYERS
    for layer in provenance["layers"]:
        assert layer["border_policy"]["name"] == "nan_border"
        assert "crs_strategy" in layer
        assert layer["dem"]["content_hash"] == provenance["dem"]["content_hash"]

    # P2.0c origin counts: declared for the DEM, COMPUTED for the layers —
    # combine(DERIVED, SYNTHETIC) = SYNTHETIC, so a synthetic DEM's features
    # never launder into DERIVED.
    assert provenance["dem_data_origin"] == "SYNTHETIC"
    assert provenance["layers_by_data_origin"] == {"SYNTHETIC": len(EXPECTED_LAYERS)}


def test_layers_from_a_measured_dem_are_derived_not_measured(tmp_path: Path) -> None:
    """The negation fixture for the combine: with a SYNTHETIC DEM,
    combine(DERIVED, SYNTHETIC) equals the DEM origin, so those tests cannot
    tell combining from copying. A MEASURED DEM separates them — layers must
    come out DERIVED (combine), never MEASURED (copy). This is the Checkpoint-1
    laundering direction: real GEBCO's derived layers must not claim MEASURED."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(
        dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.MEASURED
    )
    provenance = json.loads(written["provenance"].read_text())
    assert provenance["dem_data_origin"] == "MEASURED"
    assert provenance["layers_by_data_origin"] == {"DERIVED": len(EXPECTED_LAYERS)}


def test_build_covariate_stack_rejects_an_unknown_dem_origin_label(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    with pytest.raises(ValueError, match="FABRICATED"):
        build_covariate_stack(dem_path, tmp_path / "stack", dem_data_origin="FABRICATED")


def test_written_rasters_preserve_georeferencing_and_border_nans(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(
        dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.SYNTHETIC
    )

    with rasterio.open(dem_path) as dem:
        dem_crs, dem_transform, dem_shape = dem.crs, dem.transform, dem.shape

    provenance = json.loads(written["provenance"].read_text())
    by_name = {layer["name"]: layer for layer in provenance["layers"]}

    # Strengthened 2026-07-30: this checked `slope` only, 1 of 8, while the
    # name says "rasters". Every written layer must preserve georeferencing AND
    # honour the border policy — where each layer's OWN rim width is derived
    # from its declared provenance, not assumed uniform. (A first cut assumed a
    # 1-cell rim everywhere and failed on bpi, whose annulus outer radius is 2
    # cells on this DEM. The raster was right; the assumption was wrong.)
    for name in EXPECTED_LAYERS:
        with rasterio.open(written[name]) as layer:
            assert layer.crs == dem_crs, name
            assert layer.transform == dem_transform, name
            assert layer.shape == dem_shape, name
            values = layer.read(1)

        rim = _expected_border_width(by_name[name])
        if rim == 0:
            assert not np.isnan(values).any(), name
            continue
        assert np.isnan(values[:rim, :]).all(), name  # nan_border round-tripped
        assert np.isnan(values[-rim:, :]).all(), name
        assert not np.isnan(values[rim:-rim, rim:-rim]).any(), name


def test_the_same_dem_bytes_in_two_directories_produce_identical_rasters_and_the_same_stack_hash(
    tmp_path: Path,
) -> None:
    """REBUILT at HASH.1 commit 2 (2026-08-22). The previous version built
    both stacks from ONE dem_path and varied only the OUTPUT directory — the
    axis the manifest never recorded — and so passed since E1.4 while the
    DEM path sat nine times inside the substance (E2.4 audit row M(b):
    coverage-that-isn't under PROVENANCE.md's most-cited invariant). This
    one varies the DEM PATH: the same bytes copied into a second directory
    must give byte-identical rasters and the SAME content_hash, with the
    manifests identical apart from the two hash-excluded fields that are
    allowed to differ — `generated_at` and `dem_path`."""
    dem_a = tmp_path / "here" / "synthetic.tif"
    dem_b = tmp_path / "elsewhere" / "synthetic.tif"
    dem_a.parent.mkdir(); dem_b.parent.mkdir()
    write_synthetic_bathymetry(dem_a)
    shutil.copyfile(dem_a, dem_b)
    assert dem_a.read_bytes() == dem_b.read_bytes() and dem_a.resolve().parent != dem_b.resolve().parent
    first = build_covariate_stack(dem_a, tmp_path / "stack_a", dem_data_origin=DataOrigin.SYNTHETIC)
    second = build_covariate_stack(dem_b, tmp_path / "stack_b", dem_data_origin=DataOrigin.SYNTHETIC)

    for name in EXPECTED_LAYERS:
        assert first[name].read_bytes() == second[name].read_bytes(), name
    a = json.loads(first["provenance"].read_text())
    b = json.loads(second["provenance"].read_text())
    assert a["content_hash"] == b["content_hash"]
    assert a["dem_path"] != b["dem_path"] and a["dem_path"].endswith("here/synthetic.tif")
    differing = {k for k in a if a[k] != b[k]}
    assert differing == {"generated_at", "dem_path"}
    assert "path" not in a["dem"] and all("path" not in layer["dem"] for layer in a["layers"])
    assert a["schema_version"] == 2


def test_a_relative_and_an_absolute_path_to_the_same_dem_produce_the_same_stack_hash(
    tmp_path: Path, monkeypatch
) -> None:
    """The audit found this broke TODAY in the SAME directory: the manifest
    recorded whatever string the caller passed. Pinned separately from the
    two-directory property — a mutation that keeps the resolved parent in
    the substance passes this and fails the other; one that keeps
    `isabs` fails this and passes the other."""
    dem = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem)
    monkeypatch.chdir(tmp_path)
    relative = build_covariate_stack(Path("synthetic.tif"), tmp_path / "stack_rel", dem_data_origin=DataOrigin.SYNTHETIC)
    absolute = build_covariate_stack(dem.resolve(), tmp_path / "stack_abs", dem_data_origin=DataOrigin.SYNTHETIC)
    a = json.loads(relative["provenance"].read_text())
    b = json.loads(absolute["provenance"].read_text())
    assert a["dem_path"] == "synthetic.tif" and Path(b["dem_path"]).is_absolute()
    assert a["content_hash"] == b["content_hash"]


def test_two_different_dems_still_produce_different_stack_hashes(tmp_path: Path) -> None:
    """THE NEGATION: a fix that made every stack hash identically would pass
    the two properties above. Same geometry, same names, different values."""
    from tests.fixtures.rasters import GRID_HEIGHT, GRID_WIDTH, NORTH, PIXEL_SIZE_DEG, WEST, write_test_raster

    dem_a = tmp_path / "a.tif"
    write_synthetic_bathymetry(dem_a)
    dem_b = tmp_path / "b.tif"
    write_test_raster(
        dem_b, (-4200.0 + np.arange(GRID_HEIGHT * GRID_WIDTH, dtype="float32").reshape(GRID_HEIGHT, GRID_WIDTH) * 0.01),
        west=WEST, north=NORTH, pixel_size_deg=PIXEL_SIZE_DEG,
    )
    a = json.loads(build_covariate_stack(dem_a, tmp_path / "stack_a", dem_data_origin=DataOrigin.SYNTHETIC)["provenance"].read_text())
    b = json.loads(build_covariate_stack(dem_b, tmp_path / "stack_b", dem_data_origin=DataOrigin.SYNTHETIC)["provenance"].read_text())
    assert a["upstream_hashes"]["dem"] != b["upstream_hashes"]["dem"]
    assert a["content_hash"] != b["content_hash"]


def test_provenance_sidecar_carries_the_review_critical_keys(tmp_path: Path) -> None:
    """The keys a reviewer needs to see what was ACTUALLY computed: requested
    metres AND resolved cells AND the clamp flag (Contract 3 v3), the CRS
    strategy, and the DEM's sha256 identity.

    Moved here from test_plot_stack.py (2026-07-30, test-name audit): it calls
    build_covariate_stack, never plot_covariate_stack, so sitting in the plot
    file made plot coverage look like two tests when only one exercised the
    plot path."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(
        dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.SYNTHETIC
    )

    provenance = json.loads(written["provenance"].read_text())
    assert provenance["dem"]["content_hash"].startswith("sha256:")

    roughness = next(layer for layer in provenance["layers"] if layer["name"] == "roughness")
    window = roughness["resolved_windows"]["window"]
    assert window["requested_m"] == 1400.0
    assert isinstance(window["cells"], int) and window["cells"] >= 3
    assert window["clamped"] is True  # the coarse synthetic DEM clamps, by design
    assert "per_row_longitude_scaling" in roughness["crs_strategy"]
