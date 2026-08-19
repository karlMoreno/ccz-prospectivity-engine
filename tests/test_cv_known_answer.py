"""E2.4 — the known-answer LEAKAGE number (spec: "random k-fold vs
leave-one-cluster-out on the same known-range field, the leakage measured
as a NUMBER in our own suite").

Fixture (SYNTHETIC, tests.fixtures.known_answer; seeds at the call sites):
two 8×8 grids at 1.5 km spacing, 60 km apart (planar km → lon/lat at the
equator, where 1° = 111.19 km and E–W = N–S to cos(lat) ≈ 1), y drawn from
a Gaussian process with EXPONENTIAL covariance, effective range 8 km, sill
10, nugget 0.5, mean 10 (seed 13). The range is ≪ the 50 km gap and ≫ the
1.5 km spacing — so across the clusters kriging must revert to the training
mean (the theorem, on the fixture) and under random k-fold every held-out
point has trained neighbours inside the range (the leak).

THE NUMBER: rmse(random 8-fold) / rmse(leave-one-cluster-out), per
estimator. The mean baseline cannot leak spatial structure — only the
cluster-mean shift — so ITS ratio is the honest floor of "how much easier
random folds are"; a spatial model's ratio below that is the INFLATION
random splitting buys it. Measured at this seed (8-fold, RF 100 trees):
baseline 0.814, kriging 0.568, RF 0.468 (the walkthrough reports them; the
pins below carry margins so the claim, not the fourth decimal, is guarded).
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
from engine.prospectivity.estimators.random_forest import RandomForestEstimator
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME, EstimatorRegistry
from engine.prospectivity.training_matrix import TrainingMatrix
from engine.prospectivity.validation.runner import STATUS_SCORED, CrossValidationRunner
from engine.prospectivity.validation.splitter import RandomKFoldSplitter, leave_one_cluster_out
from tests.fixtures.known_answer import gaussian_process_field, grid_layout

KM_PER_DEG = 111.19
FIELD_SEED = 13
RANGE_KM, SILL, NUGGET = 8.0, 10.0, 0.5


def two_cluster_field(seed: int = FIELD_SEED) -> TrainingMatrix:
    a = grid_layout(8, spacing=1.5)
    b = grid_layout(8, spacing=1.5, origin=(60.0, 0.0))
    km = np.vstack([a, b])
    y = gaussian_process_field(km, variogram_range=RANGE_KM, sill=SILL, nugget=NUGGET, seed=seed, mean=10.0)
    lonlat = km / KM_PER_DEG  # lon = x, lat = y; planar km ≈ great-circle km this close to (0, 0)
    X = km.copy()
    for arr in (X, y, lonlat):
        arr.flags.writeable = False
    return TrainingMatrix(tuple(f"p{i}" for i in range(len(y))), ("x_km", "y_km"), X, y, lonlat)


def _registry() -> EstimatorRegistry:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", OrdinaryKrigingEstimator())
    registry.register("random_forest", RandomForestEstimator(seed=0, n_estimators=100, importance_seeds=(0,), feature_names=("x_km", "y_km")))
    return registry


def test_random_k_fold_inflates_spatial_models_against_leave_one_cluster_out_on_a_known_range_field() -> None:
    matrix = two_cluster_field()
    runner = CrossValidationRunner(
        splitters=[leave_one_cluster_out(linkage_km=30.0), RandomKFoldSplitter(k=8, seed=0)],
        registry=_registry(),
    )
    report = runner.run(matrix, seed=0)
    pooled = {d.name: d.pooled for d in report.designs}
    loco, rnd = pooled["leave_one_cluster_out"], pooled["random_k_fold"]
    for name in (MEAN_BASELINE_NAME, "ordinary_kriging", "random_forest"):
        assert loco[name]["n_folds_scored"] == 2 and rnd[name]["n_folds_scored"] == 8
    ratio = {
        name: rnd[name]["metrics"]["rmse"].value / loco[name]["metrics"]["rmse"].value
        for name in (MEAN_BASELINE_NAME, "ordinary_kriging", "random_forest")
    }
    # the honest floor: the baseline's ratio is the cluster-mean shift only
    assert 0.75 <= ratio[MEAN_BASELINE_NAME] <= 1.0, ratio
    # the inflation: random folds make the spatial models look >= 15 points
    # (of ratio) better than the floor can explain
    assert ratio["ordinary_kriging"] <= 0.65, ratio
    assert ratio["random_forest"] <= 0.60, ratio
    assert ratio[MEAN_BASELINE_NAME] - ratio["ordinary_kriging"] >= 0.15, ratio
    assert ratio[MEAN_BASELINE_NAME] - ratio["random_forest"] >= 0.15, ratio
    # measured at this seed: 0.814 / 0.568 / 0.468 (reported, pinned loosely)
    assert ratio[MEAN_BASELINE_NAME] == pytest.approx(0.814, abs=0.02)
    assert ratio["ordinary_kriging"] == pytest.approx(0.568, abs=0.02)
    assert ratio["random_forest"] == pytest.approx(0.468, abs=0.02)


def test_across_the_synthetic_clusters_kriging_reverts_to_the_training_mean_the_theorem_on_the_fixture() -> None:
    """Range 8 km ≪ 50 km gap: on BOTH LOCO folds kriging's held-out RMSE
    and bias equal the baseline's to within the Lagrange-term noise, and
    the min train–test separation is the gap — the theorem, with a known
    range and no real-data caveats."""
    matrix = two_cluster_field()
    report = CrossValidationRunner(splitters=[leave_one_cluster_out(linkage_km=30.0)], registry=_registry()).run(matrix, seed=0)
    design = report.designs[0]
    assert min(f.min_train_test_km for f in design.assignment.folds) == pytest.approx(49.5, abs=0.1)
    base = {r.fold_name: r for r in design.results if r.estimator_name == MEAN_BASELINE_NAME}
    for r in design.results:
        if r.estimator_name != "ordinary_kriging":
            continue
        assert r.status == STATUS_SCORED and r.provenance["range_km"] < 30.0
        b = base[r.fold_name]
        assert abs(r.metrics["rmse"].value - b.metrics["rmse"].value) < 0.05 * b.metrics["rmse"].value
        assert abs(r.metrics["mean_error"].value - b.metrics["mean_error"].value) < 0.2
    loco_k = design.pooled["ordinary_kriging"]["metrics"]["rmse"].value
    loco_b = design.pooled[MEAN_BASELINE_NAME]["metrics"]["rmse"].value
    assert loco_k == pytest.approx(loco_b, rel=0.02)
