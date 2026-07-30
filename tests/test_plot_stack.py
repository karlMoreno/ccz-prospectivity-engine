"""Smoke coverage for the E1.4 plot deliverable path (plot_stack.py).

Exists because CI was green with plot_stack never imported (2026-07-29
dependency-hygiene review): a break in the plotting path — matplotlib API
drift, corpus/registry wiring, provenance shape — would ship silently. These
tests assert the artifacts are produced and structurally sound, never the
visual output.

Deliberately NO importorskip/skipif on matplotlib: it is a required [dev]
dependency locally and in CI, and a conditional skip here would recreate the
exact silent-green gap this file closes. plot_stack.py selects the Agg
backend itself, so this runs headless without any workflow configuration.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.prospectivity.features.plot_stack import PLOT_FILENAME, plot_covariate_stack
from engine.prospectivity.features.stack import build_covariate_stack
from tests.fixtures.rasters import write_synthetic_bathymetry


def test_plot_renders_a_nontrivial_png(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    png_path = plot_covariate_stack(dem_path, tmp_path / "plots")
    assert png_path == tmp_path / "plots" / PLOT_FILENAME
    assert png_path.exists()
    # A blank/failed render compresses far smaller; the real 3x3 panel figure
    # over the noisy synthetic DEM is well over this.
    assert png_path.stat().st_size > 100_000


def test_provenance_sidecar_carries_the_review_critical_keys(tmp_path: Path) -> None:
    """The keys a reviewer needs to see what was ACTUALLY computed: requested
    metres AND resolved cells AND the clamp flag (Contract 3 v3), the CRS
    strategy, and the DEM's sha256 identity."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp_path / "stack")

    provenance = json.loads(written["provenance"].read_text())
    assert provenance["dem"]["content_hash"].startswith("sha256:")

    roughness = next(layer for layer in provenance["layers"] if layer["name"] == "roughness")
    window = roughness["resolved_windows"]["window"]
    assert window["requested_m"] == 1400.0
    assert isinstance(window["cells"], int) and window["cells"] >= 3
    assert window["clamped"] is True  # the coarse synthetic DEM clamps, by design
    assert "per_row_longitude_scaling" in roughness["crs_strategy"]
