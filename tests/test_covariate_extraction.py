"""Covariate extraction at stations: nearest-cell sampling, the Contract 3
single-DEM guard, NaN carry (flag-never-drop), and the shared-cell
accounting (E2.0-2).

Guard-test shape, per the E2.0-2 preflight finding: every layer of ONE stack
copies the same `DemGrid.provenance()`, so a single stack is structurally
incapable of disagreeing with itself. The mixed-DEM tests therefore build
TWO stacks (different resolutions; different bytes at equal resolution) and
combine layers from both into one extraction — the real threat, which is
layers assembled across stacks, not a hand-edit inside one.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.extraction import (
    SAMPLING_METHOD_NEAREST_CELL,
    CovariateExtraction,
    Station,
    extract_covariates_at_stations,
    require_single_dem,
)
from engine.prospectivity.features.recipe import CovariateResult
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from tests.fixtures.rasters import write_synthetic_bathymetry, write_test_raster

WEST, NORTH, RES = -126.5, 14.7, 0.1  # the synthetic-DEM frame (rasters.py)


def _stack(dem_path: Path) -> tuple[DemGrid, list[CovariateResult]]:
    grid = DemGrid.load(dem_path)
    return grid, build_default_registry().build_all(grid)


def _known_dem(path: Path, height: int = 20, width: int = 20) -> None:
    """Deterministic integer-valued elevations: cell (r, c) holds
    -(4000 + r*width + c), exactly representable in float32, so a sampled
    value identifies its cell uniquely."""
    values = -(4000.0 + np.arange(height * width, dtype=np.float64).reshape(height, width))
    write_test_raster(path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=RES)


def _corpus_stations() -> list[Station]:
    return [
        Station.from_observation(obs)
        for obs in CorpusCsvSampleSource().get_training_samples()
    ]


# ------------------------------------------------------------- known value


def test_a_station_samples_the_value_of_its_containing_cell(tmp_path: Path) -> None:
    """Known-value: the station at (WEST + 2.35*RES, NORTH - 5.6*RES) lies in
    column 2, row 5 — hand arithmetic, written as literals. The expected
    depth is read from the raster with rasterio directly, independent of
    DemGrid and of the extraction code."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    station = Station("known_station", WEST + 2.35 * RES, NORTH - 5.6 * RES)
    extraction = extract_covariates_at_stations(grid, layers, [station])

    with rasterio.open(dem_path) as dataset:
        expected_depth = float(dataset.read(1)[5, 2])
    assert extraction.cells == ((5, 2),)
    depth_column = extraction.covariate_names.index("depth")
    assert extraction.values[0, depth_column] == expected_depth
    assert expected_depth == -(4000.0 + 5 * 20 + 2)  # the cell-unique encoding


def test_a_station_on_a_shared_cell_edge_resolves_deterministically_east(
    tmp_path: Path,
) -> None:
    """A station exactly on the boundary between columns 2 and 3 is
    equidistant to both cell centres; the documented tie-break (floor) puts
    it in column 3. The DEM here is 0.125-degree — an exact binary fraction —
    because on a 0.1-degree grid the boundary offset is not representable
    and float rounding, not the tie-break, decides (first observed as this
    very test failing at 0.1 degrees; the caveat is now in _nearest_cell's
    docstring)."""
    dem_path = tmp_path / "dem.tif"
    res = 0.125  # exact in binary floating point; 3*res offsets are exact too
    values = -(4000.0 + np.arange(20 * 20, dtype=np.float64).reshape(20, 20))
    write_test_raster(dem_path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=res)
    grid, layers = _stack(dem_path)

    station = Station("edge_station", WEST + 3.0 * res, NORTH - 5.5 * res)
    extraction = extract_covariates_at_stations(grid, layers, [station])

    assert extraction.cells == ((5, 3),)


# ------------------------------------------- shape / order / determinism


def test_all_35_stations_sample_all_8_covariates_in_registry_order(tmp_path: Path) -> None:
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    grid, layers = _stack(dem_path)

    extraction = extract_covariates_at_stations(grid, layers, _corpus_stations())

    assert extraction.values.shape == (35, 8)
    assert len(extraction.station_ids) == 35
    assert extraction.covariate_names == tuple(build_default_registry().names())
    # The LITERAL string, not the module's constant: comparing against
    # SAMPLING_METHOD_NEAREST_CELL would compare the recorded value to
    # itself, and the adversarial review demonstrated the constant mutated
    # to "bilinear" leaves the whole suite green. The recorded string is a
    # provenance value; its content is the claim.
    assert extraction.sampling_method == "nearest_cell"
    assert SAMPLING_METHOD_NEAREST_CELL == "nearest_cell"


def test_no_real_station_hits_a_nan_border_cell_on_the_synthetic_dem(tmp_path: Path) -> None:
    """The E1.4 preflight sized the synthetic extent to corpus bbox + 0.5
    degrees with a >=5-cell margin, so today NO station lands on a border
    cell — pinned here so a regenerated fixture that shrinks the margin
    fails this test instead of silently producing flagged rows. The
    carry-the-NaN path is therefore exercised ONLY by the constructed
    border-station test below, and the border situation must be re-reported
    when the real GEBCO DEM lands."""
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    grid, layers = _stack(dem_path)

    extraction = extract_covariates_at_stations(grid, layers, _corpus_stations())

    assert extraction.nan_stations == ()
    assert not np.isnan(extraction.values).any()
    # Geometry assertion, independent of NaN-carry behavior (review: under
    # the zero-fill mutation the two asserts above cannot distinguish "no
    # border stations" from "border NaNs were filled"): every station's cell
    # sits >= 5 cells from every raster edge, the margin rasters.py's extent
    # note promises.
    height, width = grid.values.shape
    for row, col in extraction.cells:
        assert 5 <= row < height - 5 and 5 <= col < width - 5, (row, col)


def test_real_corpus_occupancy_is_4_cells_with_groups_14_7_7_7(tmp_path: Path) -> None:
    """Pins the effective-sample-size headline on today's fixture: the 35
    stations occupy FOUR distinct cells (eastern 21-station cluster: 2 cells
    as 14+7; western 14-station cluster: 2 cells as 7+7), so every station
    shares its cell (shared_cell_count == 35) and any covariate model sees
    at most 4 distinct X rows. The independent-computation test below
    recomputes expectations at runtime and so tracks ANY occupancy; this
    literal pin is what fails if a corpus or fixture change silently
    collapses (or inflates) the effective sample size — same rationale as
    the border-count-0 pin above. Re-report on real GEBCO at Checkpoint 1,
    where ~460 m cells separate the stations."""
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    grid, layers = _stack(dem_path)

    extraction = extract_covariates_at_stations(grid, layers, _corpus_stations())

    assert extraction.distinct_cell_count == 4
    assert extraction.shared_cell_count == 35
    assert sorted(len(group) for group in extraction.cell_groups) == [7, 7, 7, 14]


def test_two_independent_extractions_are_identical_in_every_field(tmp_path: Path) -> None:
    """Full-state identity, iterated over dataclasses.fields so a field
    added later is covered automatically — CLAUDE.md testing convention 3
    ('identical' compares full state, not selected fields; the review found
    the first version compared 7 of 9). The border station makes
    nan_stations NON-empty, so its determinism is a real claim here rather
    than an empty-vs-empty comparison."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)
    stations = [
        Station("border_station", WEST + 0.5 * RES, NORTH - 0.5 * RES),
        Station("interior_station", WEST + 9.5 * RES, NORTH - 9.5 * RES),
    ]

    first = extract_covariates_at_stations(grid, layers, stations)
    second = extract_covariates_at_stations(grid, layers, stations)

    assert first.nan_stations  # the fixture can distinguish the claim
    for data_field in dataclasses.fields(CovariateExtraction):
        first_value = getattr(first, data_field.name)
        second_value = getattr(second, data_field.name)
        if isinstance(first_value, np.ndarray):
            assert np.array_equal(first_value, second_value, equal_nan=True), data_field.name
        else:
            assert first_value == second_value, data_field.name


# ------------------------------------------------- shared-cell accounting


def test_shared_cell_count_and_grouping_match_an_independent_computation(
    tmp_path: Path,
) -> None:
    """The occupancy is recomputed with rasterio's own point->cell indexing
    (a separate implementation of containing-cell) and collections.Counter —
    independent of extraction.py's arithmetic and grouping code."""
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    grid, layers = _stack(dem_path)
    stations = _corpus_stations()

    extraction = extract_covariates_at_stations(grid, layers, stations)

    with rasterio.open(dem_path) as dataset:
        expected_cells = {
            s.station_id: dataset.index(s.longitude, s.latitude) for s in stations
        }
    assert dict(zip(extraction.station_ids, extraction.cells)) == expected_cells

    occupancy = Counter(expected_cells.values())
    assert extraction.distinct_cell_count == len(occupancy)
    assert extraction.shared_cell_count == sum(n for n in occupancy.values() if n >= 2)
    expected_groups = tuple(
        tuple(sorted(sid for sid, cell in expected_cells.items() if cell == occupied))
        for occupied in sorted(occupancy)
    )
    assert extraction.cell_groups == expected_groups


def test_shared_cell_count_excludes_stations_alone_in_their_cell(tmp_path: Path) -> None:
    """Three stations: two in one cell, one alone. shared_cell_count must be
    2 — NOT 3. On the real corpus every station shares its cell, so
    shared_cell_count equals len(stations) there and a hardcode to
    len(stations) would pass every real-corpus assertion; only this mixed
    occupancy can tell the computed count from that hardcode (a fixture must
    distinguish the claim from its negation — CLAUDE.md testing
    conventions).

    SOLE OBSERVER (E2.0-1b convention): under the hardcode mutation
    (`shared_cell_count = len(stations)`, E2.0-2 mutation M3) this was the
    ONLY failing test in the suite — 284 others stayed green, including the
    independent-computation test, whose real-corpus occupancy makes the
    hardcode numerically true today."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    sharers = [
        Station("sharer_a", WEST + 5.30 * RES, NORTH - 5.30 * RES),
        Station("sharer_b", WEST + 5.70 * RES, NORTH - 5.70 * RES),  # same cell (5, 5)
    ]
    loner = Station("loner", WEST + 9.5 * RES, NORTH - 9.5 * RES)  # cell (9, 9)
    extraction = extract_covariates_at_stations(grid, layers, sharers + [loner])

    assert extraction.distinct_cell_count == 2
    assert extraction.shared_cell_count == 2
    assert extraction.cell_groups == (("sharer_a", "sharer_b"), ("loner",))


# -------------------------------------------------------- the single-DEM guard


def test_guard_refuses_layers_assembled_from_stacks_of_different_resolutions(
    tmp_path: Path,
) -> None:
    """The Section-1(b) mutation shape as a permanent test: two stacks at
    0.1 and 0.05 degrees, four layers taken from each, combined into one
    extraction — the Checkpoint-1 accident (synthetic layers mixed with
    GEBCO layers) in miniature. Must refuse naming dem.resolution_deg."""
    coarse_path, fine_path = tmp_path / "coarse.tif", tmp_path / "fine.tif"
    _known_dem(coarse_path)
    values = -(4000.0 + np.arange(40 * 40, dtype=np.float64).reshape(40, 40))
    write_test_raster(fine_path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=0.05)

    coarse_grid, coarse_layers = _stack(coarse_path)
    _, fine_layers = _stack(fine_path)
    mixed = coarse_layers[:4] + fine_layers[4:]

    with pytest.raises(ValueError, match=r"dem\.resolution_deg"):
        extract_covariates_at_stations(
            coarse_grid, mixed, [Station("s1", WEST + 2.5 * RES, NORTH - 5.5 * RES)]
        )


def test_guard_refuses_two_dems_of_equal_resolution_but_different_bytes(
    tmp_path: Path,
) -> None:
    """Same resolution is not enough: two different DEMs describe two
    different seafloors, so their layers are equally inadmissible in one
    matrix. Refusal names dem.content_hash and the layers on each side."""
    dem_a, dem_b = tmp_path / "a.tif", tmp_path / "b.tif"
    _known_dem(dem_a)
    write_synthetic_bathymetry(dem_b)  # same 0.1-degree frame, different bytes
    grid_a, layers_a = _stack(dem_a)
    _, layers_b = _stack(dem_b)
    mixed = layers_a[:4] + layers_b[4:]

    with pytest.raises(ValueError, match=r"dem\.content_hash") as excinfo:
        require_single_dem(mixed, grid_a)
    message = str(excinfo.value)
    assert "depth" in message and "tpi" in message  # a layer from each side, by name


def test_guard_refuses_a_sampling_grid_that_is_not_the_layers_dem(tmp_path: Path) -> None:
    """The layers agree with each other but the grid geolocating the
    stations is a different DEM — every sampled cell would be silently
    wrong, so this refuses too."""
    dem_a, dem_b = tmp_path / "a.tif", tmp_path / "b.tif"
    _known_dem(dem_a)
    write_synthetic_bathymetry(dem_b)
    _, layers_a = _stack(dem_a)
    grid_b = DemGrid.load(dem_b)

    with pytest.raises(ValueError, match="sampling grid"):
        extract_covariates_at_stations(
            grid_b, layers_a, [Station("s1", WEST + 2.5 * RES, NORTH - 5.5 * RES)]
        )


def test_guard_refuses_an_empty_layer_list_and_a_layer_without_dem_provenance(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="no covariate layers"):
        require_single_dem([])

    bare = CovariateResult(name="orphan", values=np.zeros((3, 3)), provenance={})
    with pytest.raises(ValueError, match="provenance\\['dem'\\]"):
        require_single_dem([bare])


# ------------------------------------------------- border / missing values


def test_a_station_on_a_border_cell_gets_flagged_nan_not_a_number(tmp_path: Path) -> None:
    """Flag-never-drop at extraction: a station in the DEM's outermost cell
    has NaN for every stencil covariate (nan_border policy) but a real depth
    (passthrough covers the full raster). The NaN is carried into `values`
    and the station is flagged by name with the affected covariates — never
    dropped, never zero-filled. A zero-fill would be invisible in aggregate,
    which is why this asserts np.isnan on the exact entries.

    SOLE OBSERVER (E2.0-1b convention): under the zero-fill mutation
    (`values = np.nan_to_num(values)` after sampling, E2.0-2 mutation M2)
    this was the ONLY failing test in the suite — 284 others stayed green,
    because no real corpus station lands on a border cell today. Weakening
    or deleting this test un-guards the no-zero-fill rule entirely."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    border = Station("border_station", WEST + 0.5 * RES, NORTH - 0.5 * RES)  # cell (0, 0)
    interior = Station("interior_station", WEST + 9.5 * RES, NORTH - 9.5 * RES)
    extraction = extract_covariates_at_stations(grid, layers, [border, interior])

    assert extraction.cells[0] == (0, 0)
    names = extraction.covariate_names
    depth_column = names.index("depth")
    slope_column = names.index("slope")

    assert not np.isnan(extraction.values[0, depth_column])  # passthrough survives
    assert np.isnan(extraction.values[0, slope_column])  # stencil border is NaN

    # EXACT tuple equality, not membership: the review's phantom-entry probe
    # (a fabricated, call-varying nan_stations entry appended whenever the
    # tuple was non-empty) passed the membership version of this test and
    # every other test in the file. Every stencil covariate is NaN at the
    # corner cell; only the passthrough depth survives.
    stencil_covariates = tuple(name for name in names if name != "depth")
    assert extraction.nan_stations == (("border_station", stencil_covariates),)
    assert extraction.station_ids == ("border_station", "interior_station")  # not dropped


def test_a_station_outside_the_dem_extent_is_refused_by_name(tmp_path: Path) -> None:
    """Off-raster is NOT a border case: no containing cell exists, so a
    quiet all-NaN row would hide a broken extent — the E1.4 preflight found
    the previous fixture containing 0 of 35 stations. Refuses loudly,
    naming the station."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    inside = Station("inside_station", WEST + 2.5 * RES, NORTH - 5.5 * RES)
    outside = Station("offgrid_station", WEST - 1.0, NORTH - 5.5 * RES)
    with pytest.raises(ValueError, match="offgrid_station"):
        extract_covariates_at_stations(grid, layers, [inside, outside])


def test_duplicate_layer_names_and_duplicate_station_ids_are_refused(
    tmp_path: Path,
) -> None:
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)
    station = Station("s1", WEST + 2.5 * RES, NORTH - 5.5 * RES)

    with pytest.raises(ValueError, match="duplicate covariate layer"):
        extract_covariates_at_stations(grid, layers + [layers[0]], [station])

    with pytest.raises(ValueError, match="duplicate station id"):
        extract_covariates_at_stations(grid, layers, [station, station])


def test_a_layer_whose_array_is_not_the_grids_geometry_is_refused_by_name(
    tmp_path: Path,
) -> None:
    """The record check alone cannot catch a stale/copied provenance beside
    a regenerated raster (review probe: a 6x6 array under a real layer's
    provenance passed the guard and silently sampled the wrong geometry, or
    died in an anonymous IndexError). The array-shape check refuses by
    name.

    SOLE OBSERVER (E2.0-1b convention): under mutation M5 (the shape check
    replaced with an empty list) this was the only failing test in the
    suite — no other test constructs a shape-mismatched layer."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    impostor = CovariateResult(
        name="slope",
        values=np.full((6, 6), 0.123),
        provenance=layers[1].provenance,  # a REAL layer's provenance, copied
    )
    swapped = [impostor if layer.name == "slope" else layer for layer in layers]

    with pytest.raises(ValueError, match=r"slope.*\(6, 6\)"):
        extract_covariates_at_stations(
            grid, swapped, [Station("s1", WEST + 2.5 * RES, NORTH - 5.5 * RES)]
        )


def test_a_station_with_non_finite_coordinates_is_refused_by_name(tmp_path: Path) -> None:
    """A NaN longitude used to die in an unnamed 'cannot convert float NaN
    to integer' (review probe); the refusal now names the station, matching
    the module's refuse-by-name standard."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    good = Station("good_station", WEST + 2.5 * RES, NORTH - 5.5 * RES)
    bad = Station("nan_station", float("nan"), NORTH - 5.5 * RES)
    with pytest.raises(ValueError, match="nan_station"):
        extract_covariates_at_stations(grid, layers, [good, bad])


def test_the_returned_values_array_is_read_only(tmp_path: Path) -> None:
    """The shared-cell and NaN accounting are computed from `values` at
    build time; a caller mutating the array afterwards would silently
    invalidate them (review finding). The array is frozen."""
    dem_path = tmp_path / "dem.tif"
    _known_dem(dem_path)
    grid, layers = _stack(dem_path)

    extraction = extract_covariates_at_stations(
        grid, layers, [Station("s1", WEST + 2.5 * RES, NORTH - 5.5 * RES)]
    )
    with pytest.raises(ValueError, match="read-only"):
        extraction.values[0, 0] = 123456.0
