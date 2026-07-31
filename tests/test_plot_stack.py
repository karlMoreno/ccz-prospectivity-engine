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

EVERY TEST IN THIS FILE MUST EXERCISE THE PLOT PATH (2026-07-30, test-name
audit). `test_provenance_sidecar_carries_the_review_critical_keys` used to
live here but called `build_covariate_stack`, never `plot_covariate_stack` —
so one of this file's two tests never touched plot_stack.py at all, inflating
apparent plot coverage in exactly the way this file exists to prevent. It now
lives in `test_covariate_stack.py`, where it belongs.
"""

from __future__ import annotations

from pathlib import Path

from engine.prospectivity.features.plot_stack import PLOT_FILENAME, plot_covariate_stack
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
