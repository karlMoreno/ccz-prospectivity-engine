"""E3.1+2 commit 2 — the surface builder.

Every downstream number comes from here, so these tests carry the adversarial
weight of the task. The load-bearing one is
`test_kriging_interpolates_near_data_measured_only_at_the_34_cells_that_can_show_it`:
99% of this surface is the training mean, so a test that sampled the domain
uniformly would find a constant and pass on a broken interpolator.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
from engine.prospectivity.estimators.random_forest import RandomForestEstimator
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME, EstimatorRegistry
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.surfaces.builder import build_surfaces, route_grid
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.training_matrix import assemble_training_matrix
from tests.fixtures.rasters import write_synthetic_bathymetry

REPO_ROOT = Path(__file__).resolve().parent.parent
FITTED_RANGE_KM = 21.611  # the full-35 fit; see the range_at_candidate_ceiling caveat
EARTH_RADIUS_KM = 6371.0088


def _min_distance_km(points: np.ndarray, stations: np.ndarray) -> np.ndarray:
    lon1, lat1 = np.radians(points[:, 0])[:, None], np.radians(points[:, 1])[:, None]
    lon2, lat2 = np.radians(stations[:, 0])[None, :], np.radians(stations[:, 1])[None, :]
    h = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return (2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(h, 0, 1)))).min(axis=1)


@pytest.fixture(scope="module")
def assembly(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """The real corpus and the real 35-station matrix over the synthetic DEM
    stack — the production shape, built once."""
    tmp = tmp_path_factory.mktemp("surfaces")
    dem_path = tmp / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    stack_manifest = json.loads(written["provenance"].read_text())
    corpus_manifest = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
    dem_grid = DemGrid.load(dem_path)
    layers = build_default_registry().build_all(dem_grid)
    matrix, _ = assemble_training_matrix(
        CorpusCsvSampleSource(), dem_grid, layers, corpus_manifest, stack_manifest
    )
    grid = PredictionGrid.from_stack(written["provenance"].parent)
    return {"grid": grid, "matrix": matrix}


def _registry(feature_names: tuple[str, ...], trees: int = 100) -> EstimatorRegistry:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", OrdinaryKrigingEstimator())
    registry.register(
        "random_forest",
        RandomForestEstimator(
            seed=0, n_estimators=trees, importance_seeds=(0,), feature_names=feature_names
        ),
    )
    return registry


@pytest.fixture(scope="module")
def surfaces(assembly: dict) -> dict:
    grid, matrix = assembly["grid"], assembly["matrix"]
    return build_surfaces(grid, matrix, _registry(grid.layer_names))


# ───────────────────────────────────────────────────────── routing and coverage


def test_every_registered_estimator_gets_a_surface_and_none_is_cherry_picked(
    surfaces: dict, assembly: dict
) -> None:
    """ITERATE names(). A builder that skipped an estimator would be choosing
    which model gets reported, and the choice would be invisible."""
    expected = set(_registry(assembly["grid"].layer_names).names())
    assert set(surfaces) == expected
    assert len(expected) == 3


def test_routing_is_by_declaration_so_each_estimator_gets_the_block_it_declares(
    assembly: dict,
) -> None:
    """input_kind, never the name (C8.1's mechanism). Kriging declares
    "coordinates" and must receive 2 columns; RF declares "covariates" and
    must receive all 8. Asserting the COLUMN COUNT is what separates the two
    blocks — a router that returned covariates for both would still return an
    array of the right length."""
    grid = assembly["grid"]
    registry = _registry(grid.layer_names)
    kriging = route_grid(registry.get("ordinary_kriging"), grid)
    forest = route_grid(registry.get("random_forest"), grid)
    assert kriging.shape == (grid.n_cells, 2)
    assert forest.shape == (grid.n_cells, len(grid.layer_names)) and forest.shape[1] == 8
    np.testing.assert_array_equal(kriging, grid.cell_centres())
    np.testing.assert_array_equal(forest, grid.covariate_rows())


def test_an_estimator_declaring_an_unknown_input_kind_is_refused_by_name(
    assembly: dict,
) -> None:
    class Rogue:
        input_kind = "entrails"

    with pytest.raises(ValueError, match="declares input_kind='entrails'"):
        route_grid(Rogue(), assembly["grid"])  # type: ignore[arg-type]


def test_masked_cells_are_nan_in_both_surfaces_and_are_counted_not_filled(
    surfaces: dict, assembly: dict
) -> None:
    """FLAG NEVER DROP, carried through to the output: the 520 border cells
    where a covariate is NaN are NaN in mu AND in sd, never zero-filled."""
    grid = assembly["grid"]
    for name, result in surfaces.items():
        assert np.isnan(result.mu[~grid.predictable]).all(), name
        assert np.isnan(result.sd[~grid.predictable]).all(), name
        assert np.isfinite(result.mu[grid.predictable]).all(), name
        assert np.isfinite(result.sd[grid.predictable]).all(), name
        assert result.n_predicted == grid.n_predictable == 2880
        assert result.n_masked == grid.n_masked == 520


# ───────────────────────────────────────────────────── the paired-uncertainty gate


class _BadPair(Estimator):
    """A stub whose (mu, sd) pair is broken in a chosen way. Every shipped
    estimator returns a well-formed pair, so a stub is the only way to reach
    these refusals at all."""

    input_kind = "coordinates"
    uncertainty_method = "stub"
    uncertainty_semantics = "stub"

    def __init__(self, mode: str) -> None:
        self._mode = mode

    def fit(self, features: Any, target: Any) -> None:
        self._mean = float(np.mean(target))

    def _predict(self, features: Any) -> tuple[np.ndarray, np.ndarray]:
        n = np.asarray(features).shape[0]
        if self._mode == "nonfinite_sd":
            return np.zeros(n), np.full(n, np.nan)
        if self._mode == "negative_sd":
            return np.zeros(n), np.full(n, -1.0)
        if self._mode == "mismatched_pair":
            return np.zeros(n), np.zeros(n + 1)
        # WRONG LENGTH but a PERFECTLY WELL-FORMED PAIR — the one shape the
        # ABC cannot catch, because it never sees how many cells were asked
        # for.
        return np.zeros(n - 1), np.zeros(n - 1)

    def provenance(self) -> dict:
        return {}


@pytest.mark.parametrize(
    "mode, message, owner",
    [
        ("nonfinite_sd", "non-finite std", "Estimator.predict (the ABC)"),
        ("negative_sd", "negative std", "Estimator.predict (the ABC)"),
        ("mismatched_pair", "shapes must match exactly", "Estimator.predict (the ABC)"),
        ("wrong_length", "requested cells", "build_surfaces"),
    ],
)
def test_a_broken_prediction_pair_is_refused_and_the_refusal_comes_from_its_owner(
    assembly: dict, mode: str, message: str, owner: str
) -> None:
    """UNCERTAINTY IS ALWAYS PAIRED — and this test records WHERE each half of
    that guarantee lives, because the builder deliberately does not repeat the
    ABC's checks.

    `Estimator.predict()` is a final Template Method that already refuses a
    non-pair, a None member, a shape-mismatched pair, a non-finite std and a
    negative std. The builder re-checking them would be unreachable code with
    a test that appeared to exercise it — the coverage-that-isn't defect C8.1
    removed from the claim guard for exactly this reason. It was in the first
    draft of this builder and the ABC's refusals are what exposed it.

    THE ONE CHECK THE BUILDER OWNS is the last row: a correctly-paired result
    of the WRONG LENGTH passes every ABC check and would misalign every value
    against the grid. Only the caller knows how many cells it asked for.
    """
    registry = EstimatorRegistry()
    # the baseline is required by `assert_complete` — without it the registry
    # refuses before the builder reaches any prediction at all
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("stub", _BadPair(mode))
    with pytest.raises(ValueError, match=message):
        build_surfaces(assembly["grid"], assembly["matrix"], registry)
    assert owner  # documented in the parametrisation, asserted by the match above


def test_zero_width_sd_cells_are_counted_and_not_floored(surfaces: dict) -> None:
    """E2.3's rule carried to the grid: a zero-width uncertainty is REPORTED,
    never floored — flooring converts under-information into confidence.
    Measured today: 0 for all three estimators, pinned so the day it changes
    is a visible finding.

    THIS TEST CANNOT DISTINGUISH THE COUNT FROM A HARDCODED ZERO, and says so
    rather than implying otherwise: every real count here IS zero, the same
    degeneracy E2.0-2 found when `shared_cell_count == len(stations)` was
    numerically true on the real corpus. Mutation-measured — replacing the
    count with a literal 0 leaves this green. The separating test is
    `test_the_zero_width_count_is_computed_not_assumed` below, which uses a
    constructed surface where the count is NOT zero."""
    for name, result in surfaces.items():
        assert result.n_sd_zero == int((result.sd[np.isfinite(result.sd)] == 0.0).sum()), name
        assert result.n_sd_zero == 0, name


class _SomeZeroWidth(Estimator):
    """Returns a KNOWN number of exactly-zero sd values — the constructed
    mixed case the real surfaces cannot supply."""

    input_kind = "coordinates"
    uncertainty_method = "stub"
    uncertainty_semantics = "stub"
    n_zeros = 7

    def fit(self, features: Any, target: Any) -> None:
        self._mean = float(np.mean(target))

    def _predict(self, features: Any) -> tuple[np.ndarray, np.ndarray]:
        n = np.asarray(features).shape[0]
        sd = np.ones(n)
        sd[: self.n_zeros] = 0.0
        return np.full(n, self._mean), sd

    def provenance(self) -> dict:
        return {}


def test_the_zero_width_count_is_computed_not_assumed(assembly: dict) -> None:
    """THE SEPARATING FIXTURE. On the real surfaces every zero-width count is
    0, so a hardcoded 0 is indistinguishable from the computation (measured:
    that mutation survives the test above). Here exactly 7 cells carry sd == 0,
    so a hardcode fails and only a real count passes."""
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("stub", _SomeZeroWidth())
    built = build_surfaces(assembly["grid"], assembly["matrix"], registry)
    assert built["stub"].n_sd_zero == _SomeZeroWidth.n_zeros
    assert built[MEAN_BASELINE_NAME].n_sd_zero == 0, (
        "and the baseline in the SAME build must still report zero — a count "
        "that returned 7 for every estimator would also pass a single-surface "
        "assertion"
    )


# ─────────────────────────────────────────────────────────────────── chunking


def test_a_chunked_build_is_byte_identical_to_an_unchunked_one(assembly: dict) -> None:
    """Chunking is an OPTIMISATION and must be a no-op. Byte-identical, not
    close: a chunk boundary that shifted a prediction by 1e-12 would still be
    a defect, and `allclose` would hide it."""
    grid, matrix = assembly["grid"], assembly["matrix"]
    whole = build_surfaces(grid, matrix, _registry(grid.layer_names))
    chunked = build_surfaces(grid, matrix, _registry(grid.layer_names), chunk_size=137)
    assert set(whole) == set(chunked)
    for name in whole:
        np.testing.assert_array_equal(whole[name].mu, chunked[name].mu)
        np.testing.assert_array_equal(whole[name].sd, chunked[name].sd)
    assert 137 < grid.n_predictable, "the chunk size must actually split the work"


# ──────────────────────────────────── the test that must target the 34 cells


def test_kriging_interpolates_near_data_measured_only_at_the_34_cells_that_can_show_it(
    surfaces: dict, assembly: dict
) -> None:
    """THE SELECTION IS THE POINT, and this docstring exists to say why.

    99% of this surface is the training mean (E3.0 §4b, confirmed at commit
    2: 99.62% of predictable cells lie within 0.5 kg/m² of it), and only 34 of
    2,880 predictable cells can show interpolation at all. A 200-cell uniform
    sample contains ONE of them — measured.

    THE BLINDNESS IS REAL BUT NOT WHERE THE TASK PROMPT SAID, and this
    docstring records the measurement rather than the expectation:

      * mu half — replacing kriging's prediction with the training mean
        everywhere fails RELATION 2 here, but a uniform "the surface varies"
        probe ALSO catches it (real max|mu−mean| over a uniform sample is
        0.3183, mutated 0.0). The prompt predicted this mutation would slip
        past a uniform test; it does not.
      * sd half — clamping sd to its far-field ceiling destroys near-data
        certainty while leaving the far field untouched. It fails RELATION 1
        here, and a uniform probe CANNOT see it: 97.57% of cells already sit
        within 0.01 of that ceiling, so the sampled field is near-identical
        before and after.

    So the targeted selection is load-bearing for the sd half specifically.

    WHICH NEIGHBOURING CLAIM THIS SEPARATES (the degeneracy rule): "kriging
    interpolates" from "kriging returns a constant". Only the 34 predictable
    cells within one fitted range of a station can distinguish them.

    The assertions are RELATIONAL, not magnitude pins — the seed-pin lesson
    from P2.CLOSE. Both are entailed by ordinary kriging's structure: variance
    grows with distance from data, and the surface departs from the mean only
    where data pulls it.
    """
    grid, matrix = assembly["grid"], assembly["matrix"]
    kriging = surfaces["ordinary_kriging"]
    predictable = grid.predictable.ravel()
    distance = _min_distance_km(grid.cell_centres()[predictable], np.asarray(matrix.coords))
    near = distance <= FITTED_RANGE_KM
    far = ~near

    assert int(near.sum()) == 34, (
        "the informative set is 34 cells; if this changes the geometry changed "
        "and every claim resting on it must be re-measured"
    )
    assert far.sum() > 2000, "and the far set must dominate, or the point is moot"

    mu = kriging.mu.ravel()[predictable]
    sd = kriging.sd.ravel()[predictable]
    mean = float(matrix.y.mean())

    # RELATION 1 — kriging is MORE CERTAIN near data. Disjoint, in fact:
    # every near cell's sd is below every far cell's.
    assert sd[near].max() < sd[far].min()
    # RELATION 2 — the surface DEPARTS from the mean only where data pulls it.
    assert np.abs(mu[near] - mean).max() > np.abs(mu[far] - mean).max()


def test_the_far_field_is_the_training_mean_with_its_variance_at_the_ceiling(
    surfaces: dict, assembly: dict
) -> None:
    """The other half of the same fact, and the phase's headline number:
    beyond one fitted range kriging has no information and says so."""
    grid, matrix = assembly["grid"], assembly["matrix"]
    kriging = surfaces["ordinary_kriging"]
    predictable = grid.predictable.ravel()
    mu = kriging.mu.ravel()[predictable]
    sd = kriging.sd.ravel()[predictable]
    mean = float(matrix.y.mean())

    within_half = np.abs(mu - mean) < 0.5
    assert within_half.mean() > 0.99, (
        f"{100 * within_half.mean():.2f}% of predictable cells within 0.5 kg/m² "
        "of the training mean — E3.0 §4b predicted ~99%"
    )
    at_ceiling = np.abs(sd - sd.max()) < 0.01
    assert at_ceiling.mean() > 0.95, (
        f"{100 * at_ceiling.mean():.2f}% of cells sit at the far-field variance "
        "ceiling; kriging reports no information over almost the whole domain"
    )


def test_rf_surface_lies_inside_the_training_y_range_not_the_cell_mean_hull(
    surfaces: dict, assembly: dict
) -> None:
    """E3.0 §4(a) PREDICTED THE WRONG BOUND, and this test records the right
    one so the error cannot be re-made.

    E3.0 reasoned: four distinct training X rows -> each tree has at most 4
    leaves -> every prediction is a weighted average of the four CELL MEANS
    -> every surface value lies in [15.143, 21.657]. **Measured: [15.091,
    21.681], outside that interval at both ends.** Two steps of the reasoning
    are wrong:

      1. `mu` is quantile-forest's weighted mean of the POOLED LEAF SAMPLES —
         individual training y values — not an average of cell means;
      2. under bootstrap resampling a leaf holds a RESAMPLED SUBSET of a
         cell's stations, whose mean is not that cell's mean.

    The entailed bound is therefore [min(y), max(y)] = [11.6, 26.8], which the
    measured surface respects. This is a property of the aggregation, so it
    holds for any tree count.
    """
    y = np.asarray(assembly["matrix"].y)
    forest = surfaces["random_forest"]
    values = forest.mu[np.isfinite(forest.mu)]
    assert values.min() >= y.min() and values.max() <= y.max()
    # and the refuted bound is genuinely violated — pinned so a future reader
    # does not "restore" it
    assert values.min() < 15.143 or values.max() > 21.657


def test_rf_surface_is_not_four_plateaus(surfaces: dict) -> None:
    """The other half of E3.0 §4(a)'s error. It predicted "a small number of
    plateaus (order 10^0-10^1)"; the measured surface has ~10^3 distinct
    values, because a prediction depends on the LEAF-ASSIGNMENT PATTERN across
    all trees — which varies cell by cell — not on which of four training
    rows a cell resembles. Asserted loosely as an ORDER, not pinned to a
    count that would move with the tree count."""
    distinct = surfaces["random_forest"].summary()["n_distinct_values"]
    assert distinct > 100, distinct
