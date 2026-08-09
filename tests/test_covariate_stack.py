"""build_covariate_stack: end-to-end rasters + provenance sidecar, and
file-level determinism (the E1.3 corpus-CSV bar, applied to E1.4's rasters).
"""

from __future__ import annotations

import json
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


def test_two_independent_builds_produce_identical_rasters_and_substance(
    tmp_path: Path,
) -> None:
    """Renamed 2026-07-30: "byte_identical" stopped being true of the sidecar
    when it moved onto ProvenanceArtifact and gained `generated_at`.

    Rasters must be byte-identical. provenance.json is identical EXCEPT
    `generated_at` (a wall-clock timestamp, added when the sidecar moved onto
    ProvenanceArtifact) — so this asserts the stronger property instead:
    `content_hash` is computed over the substance with the timestamp excluded,
    so two independent builds must produce the SAME hash."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    first = build_covariate_stack(
        dem_path, tmp_path / "stack_a", dem_data_origin=DataOrigin.SYNTHETIC
    )
    second = build_covariate_stack(
        dem_path, tmp_path / "stack_b", dem_data_origin=DataOrigin.SYNTHETIC
    )

    for name in EXPECTED_LAYERS:
        assert first[name].read_bytes() == second[name].read_bytes(), name

    first_provenance = json.loads(first["provenance"].read_text())
    second_provenance = json.loads(second["provenance"].read_text())
    assert first_provenance["content_hash"] == second_provenance["content_hash"]
    assert first_provenance.pop("generated_at") != ""  # present
    second_provenance.pop("generated_at")
    assert first_provenance == second_provenance


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
