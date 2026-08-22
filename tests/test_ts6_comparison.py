"""E3.3 commit 1 — resampling TS-6 to a common grid, the computed origin, and
the comparison's structural separation from the corpus.

STATED FIRST, per the walkthrough's own rule: the TS-6 raster in every test
here is a SYNTHETIC FIXTURE. Nothing below measures anything about TS-6 —
these tests exercise the comparison machinery.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.ts6.comparison import (
    ResampledTS6,
    comparison_origin,
    resample_ts6_to_grid,
)
from engine.prospectivity.domain.ts6 import TS6Surface
from tests.fixtures.rasters import (
    GRID_HEIGHT,
    GRID_WIDTH,
    PIXEL_SIZE_DEG,
    WEST,
    NORTH,
    FixtureTS6Reference,
    write_synthetic_ts6_raster,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_CSV = REPO_ROOT / "data" / "corpus" / "master_observations.csv"


@pytest.fixture(scope="module")
def grid(surface_assembly) -> PredictionGrid:
    return surface_assembly["grid"]


def _fixture_ts6(tmp_path: Path) -> TS6Surface:
    raster = tmp_path / "ts6.tif"
    write_synthetic_ts6_raster(raster)
    return FixtureTS6Reference(raster).load()


# ─────────────────────────────────────────────────────────── the resampling


def test_a_ts6_raster_already_on_our_grid_resamples_as_an_identity(
    tmp_path: Path, grid: PredictionGrid
) -> None:
    """Today's fixture shares the stack's grid, so the resample must be an
    identity — value-for-value, not merely close — and the provenance must
    SAY it was an identity rather than leaving a reader to infer it."""
    ts6 = _fixture_ts6(tmp_path)
    with rasterio.open(ts6.raster_path) as dataset:
        source = dataset.read(1).astype(np.float64)

    resampled = resample_ts6_to_grid(ts6, grid)
    np.testing.assert_array_equal(resampled.values, source)
    assert resampled.provenance["identity"] is True
    assert resampled.provenance["method"] == "nearest"
    assert "no upsampling" in resampled.provenance["upsampling_note"]
    assert resampled.provenance["ts6_content_hash"] == ts6.content_hash


def test_a_coarser_ts6_upsamples_into_blocks_that_invent_no_detail(
    tmp_path: Path, grid: PredictionGrid
) -> None:
    """WHICH NEIGHBOURING CLAIM THIS FIXTURE SEPARATES (the degeneracy rule):
    "nearest repeats compiled values" from "the resampler smooths between
    them". A 0.2° TS-6 raster resampled to the 0.1° grid must produce values
    drawn ONLY from the source's value set — bilinear would produce averages
    that appear in neither cell, and this assertion fails on them. A
    same-grid fixture cannot make that separation, because every method is an
    identity there.

    The provenance must also carry the upsampling caveat: the blocks are
    honestly coarse, not new information.
    """
    coarse = tmp_path / "ts6_coarse.tif"
    rng = np.random.default_rng(seed=3)
    values = (10.0 + rng.random((GRID_HEIGHT // 2, GRID_WIDTH // 2)) * 5.0).astype(
        "float32"
    )
    with rasterio.open(
        coarse,
        "w",
        driver="GTiff",
        height=GRID_HEIGHT // 2,
        width=GRID_WIDTH // 2,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(WEST, NORTH, PIXEL_SIZE_DEG * 2, PIXEL_SIZE_DEG * 2),
    ) as dataset:
        dataset.write(values, 1)
    ts6 = TS6Surface(
        title="coarse fixture",
        source_id="src_ts6_grid",
        raster_path=str(coarse),
        role_note="benchmark_only",
        data_origin="SYNTHETIC",
    )

    resampled = resample_ts6_to_grid(ts6, grid)
    source_values = set(np.unique(values.astype(np.float64)))
    resampled_values = set(np.unique(resampled.values[np.isfinite(resampled.values)]))
    assert resampled_values <= source_values, (
        "nearest may only REPEAT source values; a value outside the source set "
        "is invented detail"
    )
    # and the repeats are the 2×2 blocks coarseness implies
    assert np.array_equal(resampled.values[0::2, 0::2], resampled.values[1::2, 1::2])
    assert "REPEAT in blocks" in resampled.provenance["upsampling_note"]
    # THE NEGATIVE HALF OF THE IDENTITY FLAG. Mutation-measured: with only the
    # same-grid test asserting `identity is True`, hardcoding the flag to True
    # survived the suite — the coarse fixture is the one case that can refute
    # it, so it must say so.
    assert resampled.provenance["identity"] is False


def test_resampled_values_are_read_only(tmp_path: Path, grid: PredictionGrid) -> None:
    resampled = resample_ts6_to_grid(_fixture_ts6(tmp_path), grid)
    with pytest.raises(ValueError):
        resampled.values[...] = 0


# ─────────────────────────────────────────────────────── the computed origin


def test_the_comparisons_origin_is_computed_and_neither_input_can_launder_the_other() -> None:
    """Least-real wins, asserted in BOTH directions: a MEASURED TS-6 cannot
    launder a synthetic-DEM surface, and a MEASURED surface cannot launder a
    fixture benchmark. The all-MEASURED case is the positive control — without
    it, a function that returned SYNTHETIC unconditionally would pass the
    other three assertions."""
    assert comparison_origin("SYNTHETIC", "MEASURED") is DataOrigin.SYNTHETIC
    assert comparison_origin("MEASURED", "SYNTHETIC") is DataOrigin.SYNTHETIC
    assert comparison_origin("MEASURED", "DERIVED") is DataOrigin.DERIVED
    assert comparison_origin("MEASURED", "MEASURED") is DataOrigin.MEASURED


def test_an_undeclared_ts6_origin_is_refused_not_defaulted() -> None:
    """Declaration or nothing (P2.0d-3): a silent default here would let an
    undeclared benchmark pass as whatever flatters the comparison."""
    with pytest.raises(ValueError, match="no declared data_origin"):
        comparison_origin("SYNTHETIC", None)


# ─────────────────────────────── the comparison cannot feed the corpus


def test_the_comparison_path_cannot_feed_the_corpus(
    tmp_path: Path, grid: PredictionGrid
) -> None:
    """GRID is a benchmark class, never a training station (Contract 1) — as
    a TEST, not a comment, in the two ways that are mechanically observable:

    1. STRUCTURALLY: the comparison module's import graph contains nothing
       from `ingestion/` or `samples/` — the only code paths that write or
       select corpus rows. An import added later fails here by name.
    2. BEHAVIOURALLY, full state: the corpus CSV is byte-identical before and
       after a comparison runs (CLAUDE.md rule 3 — "unchanged" means the
       bytes, not selected fields).

    What this does NOT prove, said plainly: that no FUTURE module feeds TS-6
    values into training. It proves THIS path cannot, and the corpus
    invariants + `SampleSource`'s MASS-only gate hold the wider line.
    """
    module_names = [
        name
        for name in sys.modules
        if name.startswith("engine.prospectivity.ts6")
    ]
    forbidden = ("ingestion", "samples", "corpus")
    for name in module_names:
        module = sys.modules[name]
        imported = getattr(module, "__dict__", {})
        for value in imported.values():
            imported_module = getattr(value, "__module__", "") or ""
            for bad in forbidden:
                assert f"prospectivity.{bad}" not in imported_module, (
                    f"{name} reaches {imported_module} — the comparison must "
                    "not touch corpus machinery"
                )

    before = hashlib.sha256(CORPUS_CSV.read_bytes()).hexdigest()
    resample_ts6_to_grid(_fixture_ts6(tmp_path), grid)
    after = hashlib.sha256(CORPUS_CSV.read_bytes()).hexdigest()
    assert before == after
