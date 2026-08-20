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

import pytest

from engine.prospectivity.features.plot_stack import (
    PLOT_FILENAME,
    SYNTHETIC_WATERMARK,
    UNDECLARED_WATERMARK,
    dem_watermark,
    plot_covariate_stack,
)
from engine.prospectivity.provenance.origin import DataOrigin
from tests.fixtures.rasters import write_synthetic_bathymetry


def test_plot_renders_a_nontrivial_png(tmp_path: Path) -> None:
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    png_path = plot_covariate_stack(
        dem_path, tmp_path / "plots", dem_data_origin=DataOrigin.SYNTHETIC
    )
    assert png_path == tmp_path / "plots" / PLOT_FILENAME
    assert png_path.exists()
    # A blank/failed render compresses far smaller; the real 3x3 panel figure
    # over the noisy synthetic DEM is well over this.
    assert png_path.stat().st_size > 100_000


def test_watermark_is_default_on_and_only_measured_renders_clean() -> None:
    """The P2.0d-3 rule per declaration. The SYNTHETIC string is pinned
    byte-for-byte to the pre-d-3 hardcoded text — a refactor of where the
    claim comes from, not what it says. MEASURED is the ONLY clean render;
    an undeclared origin gets the loud not-declared stamp (never a raise);
    any other declared origin is named; a malformed label raises."""
    assert dem_watermark(DataOrigin.SYNTHETIC) == SYNTHETIC_WATERMARK
    assert SYNTHETIC_WATERMARK == (
        "SYNTHETIC DEM (seeded noise; illustrative only. "
        "Real GEBCO bathymetry arrives at Integration Checkpoint 1.)"
    )
    assert dem_watermark(DataOrigin.MEASURED) is None
    assert dem_watermark(None) == UNDECLARED_WATERMARK
    assert "ORIGIN NOT DECLARED" in UNDECLARED_WATERMARK
    assert "DERIVED" in (dem_watermark(DataOrigin.DERIVED) or "")
    with pytest.raises(ValueError, match="FABRICATED"):
        dem_watermark("FABRICATED")


def test_rendered_plot_actually_consumes_the_declaration(tmp_path: Path) -> None:
    """The render-level observer (d-2 precedent: helper tests alone cannot
    catch a plot that ignores the helper and hardcodes the old suptitle).
    Same DEM, three declarations — the PNGs must differ pairwise, because
    the watermark and panel label differ. A plot that ignores the origin
    renders all three identically and fails here.

    SOLE OBSERVER (measured at P2.CLOSE, 2026-08-20, over the full 471-test suite): bypassing the watermark helper in the renderer
    (`watermark = dem_watermark(declared)` -> `watermark = None`) fails this
    test and nothing else — 1 of 471. The helper-level tests still pass,
    because the helper still WORKS; what only this test sees is whether the
    rendered bytes actually USED it. That is the whole d-2 lesson, and it is
    why deleting this test would leave the watermark verified in principle
    and unobserved in practice."""
    dem_path = tmp_path / "synthetic.tif"
    write_synthetic_bathymetry(dem_path)
    renders = {}
    for label, origin in (
        ("synthetic", DataOrigin.SYNTHETIC),
        ("measured", DataOrigin.MEASURED),
        ("undeclared", None),
    ):
        path = plot_covariate_stack(
            dem_path, tmp_path / label, dem_data_origin=origin
        )
        renders[label] = path.read_bytes()
    assert renders["synthetic"] != renders["measured"]
    assert renders["measured"] != renders["undeclared"]
    assert renders["synthetic"] != renders["undeclared"]
