"""E3.1+2 commit 1 — the prediction grid and the domain mask.

The grid is INHERITED from the feature stack, never chosen, so these tests
are mostly identity assertions: the grid a surface is built on must be the
grid the covariates were computed on, cell for cell.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.surfaces.grid import PredictionGrid
from tests.fixtures.rasters import (
    GRID_HEIGHT,
    GRID_WIDTH,
    PIXEL_SIZE_DEG,
    WEST,
    NORTH,
    write_synthetic_bathymetry,
)


@pytest.fixture(scope="module")
def stack_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp = tmp_path_factory.mktemp("grid_stack")
    dem_path = tmp / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    return written["provenance"].parent


@pytest.fixture(scope="module")
def grid(stack_dir: Path) -> PredictionGrid:
    return PredictionGrid.from_stack(stack_dir)


def test_grid_identity_is_the_stacks_identity_not_a_configured_extent(
    grid: PredictionGrid, stack_dir: Path
) -> None:
    """THE GRID IS INHERITED. Every geometric field is compared against the
    stack's OWN rasters — not against constants restated here, which would
    pass while the grid drifted from the covariates it must align with.

    The one place constants ARE used is the fixture's extent, and the
    docstring says why that is a fixture and not a production configuration
    (E3.0 §2): there is no production extent anywhere in the repo.
    """
    manifest = json.loads((stack_dir / "provenance.json").read_text())
    with rasterio.open(stack_dir / f"{manifest['layers'][0]['name']}.tif") as layer:
        assert grid.transform == tuple(layer.transform)[:6]
        assert grid.crs == layer.crs.to_string()
        assert (grid.width, grid.height) == (layer.width, layer.height)

    assert grid.dem_content_hash == manifest["upstream_hashes"]["dem"]
    assert grid.stack_content_hash == manifest["content_hash"]
    assert grid.layer_names == tuple(layer["name"] for layer in manifest["layers"])

    # the fixture's extent, stated so a change to it is visible here
    assert (grid.width, grid.height) == (GRID_WIDTH, GRID_HEIGHT)
    assert grid.res_x_deg == pytest.approx(PIXEL_SIZE_DEG)
    assert grid.res_y_deg == pytest.approx(PIXEL_SIZE_DEG)
    assert grid.extent() == pytest.approx(
        [WEST, NORTH - GRID_HEIGHT * PIXEL_SIZE_DEG, WEST + GRID_WIDTH * PIXEL_SIZE_DEG, NORTH]
    )


def test_layer_order_follows_the_manifest_so_columns_cannot_permute(
    grid: PredictionGrid, stack_dir: Path
) -> None:
    """Read in MANIFEST order, not directory order. A glob sorts by filename
    — which for these eight layers is a DIFFERENT order — and would permute
    the covariate columns relative to the training matrix while every shape
    assertion still passed."""
    manifest = json.loads((stack_dir / "provenance.json").read_text())
    manifest_order = [layer["name"] for layer in manifest["layers"]]
    assert list(grid.layer_names) == manifest_order
    assert manifest_order != sorted(manifest_order), (
        "this test is only meaningful while the two orders differ; if the "
        "manifest ever happens to be alphabetical, it silently stops "
        "separating them"
    )
    # each plane is the raster of the layer the name points at
    for index, name in enumerate(grid.layer_names):
        with rasterio.open(stack_dir / f"{name}.tif") as dataset:
            expected = dataset.read(1).astype(np.float64)
        np.testing.assert_array_equal(grid.covariates[index], expected)


def test_the_mask_is_exactly_the_stacks_nan_union_and_masked_cells_are_counted(
    grid: PredictionGrid, stack_dir: Path
) -> None:
    """FLAG NEVER DROP: a cell where ANY covariate is NaN is undefined, and
    it is COUNTED rather than zero-filled or imputed.

    The expected mask is recomputed from the rasters on disk — a union over
    all eight layers — so this cannot pass by agreeing with itself.

    WHAT SEPARATES "ANY LAYER" FROM "SOME PARTICULAR LAYER": the eight layers
    do NOT share one NaN footprint (measured: depth 0, six windowed recipes
    264 each, BPI 520 — different window radii, E2.0-2), and the assertion
    below pins that. So a mask built from only `depth` would be all-True
    (0 != 520) and a mask built from only `slope` would be 264 != 520; both
    fail here. Note the union happens to EQUAL BPI's set, because BPI's
    2-cell ring contains the 1-cell rings — so this test separates the mask
    from a wrong SINGLE layer, not from BPI specifically."""
    per_layer = []
    for name in grid.layer_names:
        with rasterio.open(stack_dir / f"{name}.tif") as dataset:
            per_layer.append(np.isnan(dataset.read(1).astype(np.float64)))
    union = np.logical_or.reduce(per_layer)
    np.testing.assert_array_equal(grid.predictable, ~union)

    assert grid.n_cells == GRID_WIDTH * GRID_HEIGHT
    assert grid.n_masked == int(union.sum())
    assert grid.n_predictable == grid.n_cells - grid.n_masked
    assert 0 < grid.n_masked < grid.n_cells, (
        "the fixture must have SOME masked border and SOME predictable "
        "interior, or this test cannot distinguish a correct mask from an "
        "all-True or all-False one"
    )
    widths = {int(layer.sum()) for layer in per_layer}
    assert len(widths) > 1, (
        "the layers must NOT all share one NaN footprint here, or 'any layer' "
        "and 'this layer' would be indistinguishable"
    )


def test_cell_centres_are_centres_not_corners(grid: PredictionGrid) -> None:
    """A half-cell offset would shift every coordinate-driven surface by ~5.5
    km at 0.1° while leaving every shape assertion green."""
    centres = grid.cell_centres()
    assert centres.shape == (grid.n_cells, 2)
    # first cell centre sits half a cell inside the NW corner
    assert centres[0, 0] == pytest.approx(WEST + 0.5 * PIXEL_SIZE_DEG)
    assert centres[0, 1] == pytest.approx(NORTH - 0.5 * PIXEL_SIZE_DEG)
    # and the last sits half a cell inside the SE corner
    assert centres[-1, 0] == pytest.approx(WEST + (GRID_WIDTH - 0.5) * PIXEL_SIZE_DEG)
    assert centres[-1, 1] == pytest.approx(NORTH - (GRID_HEIGHT - 0.5) * PIXEL_SIZE_DEG)
    # every centre lies strictly inside the extent
    west, south, east, north = grid.extent()
    assert (centres[:, 0] > west).all() and (centres[:, 0] < east).all()
    assert (centres[:, 1] > south).all() and (centres[:, 1] < north).all()


def test_covariate_rows_are_row_major_and_aligned_with_cell_centres(
    grid: PredictionGrid,
) -> None:
    """The two routings must index the SAME cell at the same position, or a
    coordinate-driven and a covariate-driven surface would disagree about
    which place row k is."""
    rows = grid.covariate_rows()
    assert rows.shape == (grid.n_cells, len(grid.layer_names))
    for flat in (0, 1, grid.width, grid.n_cells - 1):
        r, c = divmod(flat, grid.width)
        np.testing.assert_array_equal(rows[flat], grid.covariates[:, r, c])


def test_two_reads_of_one_stack_are_identical_in_full_state(stack_dir: Path) -> None:
    """Determinism, compared over FULL STATE rather than selected fields
    (CLAUDE.md rule 3) — the arrays, the mask and the whole identity dict."""
    first, second = PredictionGrid.from_stack(stack_dir), PredictionGrid.from_stack(stack_dir)
    np.testing.assert_array_equal(first.covariates, second.covariates)
    np.testing.assert_array_equal(first.predictable, second.predictable)
    np.testing.assert_array_equal(first.cell_centres(), second.cell_centres())
    assert first.identity() == second.identity()


def test_grid_arrays_are_read_only(grid: PredictionGrid) -> None:
    """The TrainingMatrix convention: a consumer that mutated the cube in
    place would change every surface built afterwards."""
    for array in (grid.covariates, grid.predictable):
        with pytest.raises(ValueError):
            array[...] = 0


def test_layers_that_disagree_on_geometry_are_refused_by_name(
    stack_dir: Path, tmp_path: Path
) -> None:
    """One grid, or no grid. A layer on a different transform cannot be
    stacked into a cube whose (row, col) means one place."""
    import shutil

    broken = tmp_path / "broken"
    shutil.copytree(stack_dir, broken)
    manifest = json.loads((broken / "provenance.json").read_text())
    victim = manifest["layers"][1]["name"]
    with rasterio.open(broken / f"{victim}.tif") as dataset:
        profile, values = dataset.profile, dataset.read(1)
    profile["transform"] = rasterio.Affine(
        profile["transform"].a, 0.0, profile["transform"].c + 5.0,
        0.0, profile["transform"].e, profile["transform"].f,
    )
    with rasterio.open(broken / f"{victim}.tif", "w", **profile) as dataset:
        dataset.write(values, 1)

    with pytest.raises(ValueError, match=f"layer '{victim}' has grid"):
        PredictionGrid.from_stack(broken)
