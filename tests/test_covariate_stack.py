"""build_covariate_stack: end-to-end rasters + provenance sidecar, and
file-level determinism (the E1.3 corpus-CSV bar, applied to E1.4's rasters).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from engine.prospectivity.features.stack import build_covariate_stack
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


def test_stack_writes_all_eight_layers_and_provenance(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp_path / "stack")

    assert sorted(written) == sorted(EXPECTED_LAYERS + ["provenance"])
    for name in EXPECTED_LAYERS:
        assert written[name].exists()

    provenance = json.loads(written["provenance"].read_text())
    assert provenance["registry_version"] == 3
    assert provenance["dem"]["content_hash"].startswith("sha256:")
    assert [layer["name"] for layer in provenance["layers"]] == EXPECTED_LAYERS
    for layer in provenance["layers"]:
        assert layer["border_policy"]["name"] == "nan_border"
        assert "crs_strategy" in layer
        assert layer["dem"]["content_hash"] == provenance["dem"]["content_hash"]


def test_written_rasters_preserve_georeferencing_and_border_nans(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp_path / "stack")

    with rasterio.open(dem_path) as dem, rasterio.open(written["slope"]) as slope:
        assert slope.crs == dem.crs
        assert slope.transform == dem.transform
        assert slope.shape == dem.shape
        values = slope.read(1)
    assert np.isnan(values[0, :]).all()  # nan_border survived the round-trip
    assert not np.isnan(values[1:-1, 1:-1]).any()


def test_two_independent_builds_are_byte_identical(tmp_path: Path) -> None:
    """Rasters must be byte-identical. provenance.json is identical EXCEPT
    `generated_at` (a wall-clock timestamp, added when the sidecar moved onto
    ProvenanceArtifact) — so this asserts the stronger property instead:
    `content_hash` is computed over the substance with the timestamp excluded,
    so two independent builds must produce the SAME hash."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    first = build_covariate_stack(dem_path, tmp_path / "stack_a")
    second = build_covariate_stack(dem_path, tmp_path / "stack_b")

    for name in EXPECTED_LAYERS:
        assert first[name].read_bytes() == second[name].read_bytes(), name

    first_provenance = json.loads(first["provenance"].read_text())
    second_provenance = json.loads(second["provenance"].read_text())
    assert first_provenance["content_hash"] == second_provenance["content_hash"]
    assert first_provenance.pop("generated_at") != ""  # present
    second_provenance.pop("generated_at")
    assert first_provenance == second_provenance
