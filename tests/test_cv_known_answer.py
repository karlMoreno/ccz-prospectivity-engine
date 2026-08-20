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
random splitting buys it. Measured at seed 13 (8-fold, RF 100 trees):
baseline 0.814, kriging 0.568, RF 0.468 — the numbers E2.4 §3 published, and
they STAY published: they are a measurement at a stated seed, not a claim
about every field.

WHAT CHANGED AT P2.CLOSE (2026-08-20) AND WHY. Until now this file pinned
those magnitudes with ±0.02 point pins and three threshold assertions. A
40-seed sweep (field seed swept; k-fold, runner and RF seeds held at 0)
measured what each pin actually guards:

    claim                            holds at
    DIRECTION: krig ratio < base       40/40
    DIRECTION: RF   ratio < base       40/40
    base − RF   >= 0.15                39/40   (fails seed 4, by 0.0085)
    base − krig >= 0.15                34/40
    floor 0.75 <= base <= 1.0          29/40   (9 of 11 failures are base
                                                 slightly ABOVE 1.0)
    RF   <= 0.60                       21/40
    krig <= 0.65                       13/40
    the three ±0.02 point pins          1/40   (seed 13, by construction)

So the whole test was green at ONE of forty seeds. A suite that passed told
us the field had been drawn with seed 13 — not that random splitting inflates
anything. Everything except the DIRECTION is now computed and reported rather
than asserted; the sweep table lives in docs/walkthroughs/P2-closeout.md.
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


SPATIAL_MODELS = ("ordinary_kriging", "random_forest")

# The first four seeds plus the published one. A STATEABLE RULE, not a
# selection: the direction holds at all 40 seeds swept, so no choice of block
# can flatter it — and seed 4 is kept deliberately, because it is the one
# where the audit's proposed `base − RF >= 0.15` pin fails.
LEAKAGE_SEEDS = (1, 2, 3, 4, 13)


def leakage_ratios(seed: int) -> dict[str, float]:
    """rmse(random 8-fold) / rmse(leave-one-cluster-out), per estimator, on
    the planted two-cluster field at `seed`."""
    runner = CrossValidationRunner(
        splitters=[leave_one_cluster_out(linkage_km=30.0), RandomKFoldSplitter(k=8, seed=0)],
        registry=_registry(),
    )
    report = runner.run(two_cluster_field(seed=seed), seed=0)
    pooled = {d.name: d.pooled for d in report.designs}
    loco, rnd = pooled["leave_one_cluster_out"], pooled["random_k_fold"]
    for name in (MEAN_BASELINE_NAME, *SPATIAL_MODELS):
        assert loco[name]["n_folds_scored"] == 2 and rnd[name]["n_folds_scored"] == 8
    return {
        name: rnd[name]["metrics"]["rmse"].value / loco[name]["metrics"]["rmse"].value
        for name in (MEAN_BASELINE_NAME, *SPATIAL_MODELS)
    }


def _table(measured: dict[int, dict[str, float]]) -> str:
    lines = [f"{'seed':>5} {'baseline':>9} {'kriging':>9} {'RF':>9}"]
    for seed, r in sorted(measured.items()):
        lines.append(
            f"{seed:>5} {r[MEAN_BASELINE_NAME]:>9.4f} "
            f"{r['ordinary_kriging']:>9.4f} {r['random_forest']:>9.4f}"
        )
    return "\n".join(lines)


def test_random_k_fold_inflates_both_spatial_models_relative_to_the_baseline_at_every_sampled_seed() -> None:
    """ASSERTS THE DIRECTION ONLY, at five independently-drawn fields: each
    spatial model's random-vs-blocked RMSE ratio is strictly below the mean
    baseline's. That inequality IS the leakage claim — the baseline cannot
    leak spatial structure, so anything it gains from random folds is the
    cluster-mean shift, and a spatial model gaining MORE is the inflation.

    WHICH NEIGHBOURING CLAIM THE FIXTURE SEPARATES (the CLAUDE.md degeneracy
    rule): "random splitting inflates scores on autocorrelated data" from
    "this particular seed happened to inflate". A single-seed test cannot
    tell those apart — it is one draw, and the old version of this test was
    green at exactly one of forty. Running five independent fields is what
    makes the separation real; a docstring claiming it while testing one seed
    would be the assertion-shaped decoration this rule exists to catch.

    WHY THE MAGNITUDES ARE REPORTED AND NOT PINNED. Measured over 40 seeds
    (module docstring): the ratio ceilings hold at 13/40 and 21/40, the
    absolute gaps at 34/40 and 39/40, the ±0.02 point pins at 1/40, and even
    the baseline "floor" at 29/40. A threshold that fails on most seeds was
    pinning a coincidence, and a green suite on seed 13 was reporting the
    seed, not the phenomenon. THE AUDIT'S PROPOSED REMEDY IS NOT WHAT LANDED:
    it named `base − RF >= 0.15` as 8-of-8 safe on seeds 11–18, and that pin
    fails at seed 4 — which is in this test's own seed list, so adopting it
    would have left the suite red. Verified against the wider measurement,
    not against the finding that prompted it.

    The magnitudes are still COMPUTED, and travel in the failure message and
    in docs/walkthroughs/P2-closeout.md.
    """
    # THE SEPARATION ITSELF, GUARDED. Mutation-measured: with the pair-set
    # comparison alone, shrinking LEAKAGE_SEEDS to a single seed left the
    # test green — `expected` is derived from the same list, so both sides
    # shrink together and the multi-field property vanishes silently. That
    # would restore exactly the single-seed test this one replaced.
    assert len(set(LEAKAGE_SEEDS)) >= 4, (
        "this test's claim — the PHENOMENON, not the seed — rests on several "
        f"independently drawn fields; LEAKAGE_SEEDS is {LEAKAGE_SEEDS}"
    )
    measured = {seed: leakage_ratios(seed) for seed in LEAKAGE_SEEDS}
    # A POSITIVE FULL-STATE COMPARISON, not "no violations found" (CLAUDE.md
    # rule 3). Mutation-measured: with a `not ... <` check collected into a
    # violations list, breaking the COMPREHENSION's condition to `if False`
    # left the list empty and the test green — the direction assertion could
    # not fail. Comparing the set of pairs that DID invert against the set of
    # every pair examined fails both ways: a vacuous condition yields an
    # empty set, and a genuine inversion drops exactly the pair that broke.
    inverted = sorted(
        (seed, name)
        for seed, r in measured.items()
        for name in SPATIAL_MODELS
        if r[name] < r[MEAN_BASELINE_NAME]
    )
    expected = sorted((seed, name) for seed in LEAKAGE_SEEDS for name in SPATIAL_MODELS)
    assert inverted == expected, (
        "random k-fold must inflate BOTH spatial models relative to the baseline "
        f"at every sampled seed; missing {sorted(set(expected) - set(inverted))}"
        f"\n{_table(measured)}"
    )
    # the published seed-13 measurement, recomputed so the walkthrough's
    # numbers cannot silently drift from the code that produced them —
    # a WIDE band, because this pins the identity of the fixture, not the
    # magnitude of the effect (which the sweep showed is seed-dependent).
    published = measured[13]
    assert published[MEAN_BASELINE_NAME] == pytest.approx(0.814, abs=0.05)
    assert published["ordinary_kriging"] == pytest.approx(0.568, abs=0.05)
    assert published["random_forest"] == pytest.approx(0.468, abs=0.05)


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
