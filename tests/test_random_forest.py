"""RandomForestEstimator (E2.3 §2): determinism, the pairing path, the OOB
structural rule, the uncertainty semantics on a rank-4 fixture, and the
real-matrix end to end.

Fixture-degeneracy statements (CLAUDE.md rule 4), per fixture:
- RANK-4 fixture (4 distinct X rows, groups 14/7/7/7, y varying WITHIN
  groups): separates "the sd is the POOLED conditional distribution's
  spread" (ratio to true within-group sd0 0.99–1.00, asserted ±5%) from
  "the ensemble spread of tree means" (2.3–3.7× smaller ON THIS FIXTURE —
  measured here, not quoted from §1's different statistic) AND from "the
  per-tree-quantile average" (0.69–0.83× the truth — the pre-review
  defect, now outside the ±5% band). Group sizes UNEQUAL, means DISTINCT.
- DISTINCT-X fixture (the §1 known-answer generator, n=35, planted noise
  sd 1.0): the rank-4 fixture is structurally BLIND to the review's must-
  fix — with per-tree-quantile averaging the sd is identically 0 on any
  training set with distinct rows, and every rank-4 row is co-celled. This
  fixture separates "sd is a predictive spread" from "sd is 0".
- The OOB mutation fixture: `compute_oob_diagnostic=True` yields a REAL
  float, so an OOB value exists to leak — a fixture with OOB None could not
  distinguish "excluded by construction" from "absent". Its assertion walks
  the structure RECURSIVELY and diffs against an OOB-off twin (review: a
  top-level equality check missed a nested/derived value).
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.estimators.random_forest import (
    UNCERTAINTY_METHOD,
    RandomForestEstimator,
    RandomForestReport,
)
from engine.prospectivity.estimators.registry import (
    MEAN_BASELINE_NAME,
    REQUIRED_ESTIMATORS,
    build_default_registry,
)
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import (
    build_default_registry as build_covariate_registry,
)
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.training_matrix import assemble_training_matrix, matrix_watermark
from tests.fixtures.rasters import write_synthetic_bathymetry

REPO_ROOT = Path(__file__).resolve().parent.parent


def _rank4_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int]]:
    rng = np.random.default_rng(0)
    x_rows = rng.standard_normal((4, 8))
    groups = [14, 7, 7, 7]
    X = np.vstack([np.repeat(x_rows[g][None, :], n, axis=0) for g, n in enumerate(groups)])
    group_means = np.array([20.3, 21.7, 15.1, 20.2])
    y = np.concatenate([group_means[g] + rng.normal(0.0, 3.2, n) for g, n in enumerate(groups)])
    return X, y, x_rows, groups


def _fitted(**kwargs) -> tuple[RandomForestEstimator, np.ndarray, np.ndarray, np.ndarray, list[int]]:
    X, y, x_rows, groups = _rank4_fixture()
    rf = RandomForestEstimator(seed=0, n_estimators=200, importance_seeds=(0, 1, 2), **kwargs)
    rf.fit(X, y)
    return rf, X, y, x_rows, groups


# ------------------------------------------------------------- determinism


def test_two_fits_and_predictions_under_one_seed_are_identical_in_every_field() -> None:
    first, _, _, x_rows, _ = _fitted()
    second, _, _, _, _ = _fitted()
    mean_a, sd_a = first.predict(x_rows)
    mean_b, sd_b = second.predict(x_rows)
    assert np.array_equal(mean_a, mean_b)
    assert np.array_equal(sd_a, sd_b)
    assert np.array_equal(first.predict_quantiles(x_rows), second.predict_quantiles(x_rows))
    for data_field in dataclasses.fields(RandomForestReport):
        assert getattr(first.report(), data_field.name) == getattr(second.report(), data_field.name), (
            data_field.name
        )


def test_a_different_seed_changes_the_forest() -> None:
    """The negation of determinism-by-constant: seed 1 differs from seed 0."""
    X, y, x_rows, _ = _rank4_fixture()
    a = RandomForestEstimator(seed=0, n_estimators=100, importance_seeds=(0,))
    b = RandomForestEstimator(seed=1, n_estimators=100, importance_seeds=(1,))
    a.fit(X, y)
    b.fit(X, y)
    assert not np.array_equal(a.predict(x_rows)[1], b.predict(x_rows)[1])
    assert a.report().seed == 0 and b.report().seed == 1


# ------------------------------------------ pairing + uncertainty semantics


def test_rf_output_passes_the_pairing_template_and_sd_is_finite_non_negative() -> None:
    rf, X, _, x_rows, _ = _fitted()
    mean, sd = rf.predict(x_rows)
    assert mean.shape == sd.shape == (4,)
    assert np.isfinite(mean).all() and np.isfinite(sd).all()
    assert (sd >= 0).all()
    assert (sd > 0).all()  # within-group spread exists, so the sd is not degenerate


def test_uncertainty_is_the_pooled_conditional_sd_within_5pct_of_within_group_sd0() -> None:
    """The §1 semantics delivered, tightly: on the rank-4 fixture the paired
    sd matches the true within-group ddof=0 sd to ±5% per row (measured
    0.99–1.00×). The band EXCLUDES both neighbors: the ensemble spread of
    per-tree means (computed independently here; 2.3–3.7× smaller) and the
    per-tree-quantile average of the pre-review code (0.69–0.83× — the
    E2.3 must-fix). ddof=0 for the truth because an ECDF has no Bessel
    correction (the convention stated in the module docstring)."""
    rf, X, y, x_rows, groups = _fitted()
    _, sd = rf.predict(x_rows)
    starts = np.cumsum([0] + groups[:-1])
    true_sd = np.array([y[i : i + n].std(ddof=0) for i, n in zip(starts, groups)])
    per_tree = np.stack([t.predict(x_rows) for t in rf._forest.estimators_])
    ensemble_spread = per_tree.std(axis=0, ddof=1)
    for row in range(4):
        assert 0.95 * true_sd[row] < sd[row] < 1.05 * true_sd[row], (row, sd[row], true_sd[row])
        assert sd[row] > 2.0 * ensemble_spread[row], row


def test_on_distinct_x_rows_the_sd_is_a_predictive_spread_not_zero() -> None:
    """The must-fix's observer (rule 4 — the rank-4 fixture cannot see it):
    on the §1 known-answer field with DISTINCT X (n=35, planted noise sd
    1.0), every holdout sd is > 0 and the mean sd sits within 0.7–1.5 of the
    planted noise. Under per-tree-quantile averaging every sd here is
    exactly 0 (E2.3 mutation RF4)."""
    from tests.fixtures.known_answer import covariate_driven_field

    X, y = covariate_driven_field(35, 8, driving_column=3, coefficient=2.0, noise_sd=1.0, seed=42)
    X_hold, _ = covariate_driven_field(300, 8, driving_column=3, coefficient=2.0, noise_sd=1.0, seed=1042)
    rf = RandomForestEstimator(seed=0, n_estimators=200, importance_seeds=(0,))
    rf.fit(X, y)
    _, sd = rf.predict(X_hold)
    assert (sd > 0.05).all()
    assert 0.7 < sd.mean() < 1.5


def test_predictions_track_the_group_means_and_quantiles_bracket_them() -> None:
    rf, X, y, x_rows, groups = _fitted()
    mean, _ = rf.predict(x_rows)
    starts = np.cumsum([0] + groups[:-1])
    group_means = np.array([y[i : i + n].mean() for i, n in zip(starts, groups)])
    assert np.abs(mean - group_means).max() < 0.5
    q = rf.predict_quantiles(x_rows, quantiles=(0.05, 0.5, 0.95))
    assert (q[:, 0] < q[:, 1]).all() and (q[:, 1] < q[:, 2]).all()
    assert (q[:, 0] < group_means).all() and (group_means < q[:, 2]).all()


# ------------------------------------------------- the OOB structural rule


def test_validation_facing_fields_contain_no_oob_value_even_when_computed() -> None:
    """THE OOB HARD RULE, structural: with the diagnostic COMPUTED (a real
    float exists to leak), the provenance-bound structure carries no
    OOB-derived value — no key naming it, no value equal to it — while the
    honest-named field on the report does. Mutation-verified: adding
    `oob_diagnostic_not_validation` to validation_facing_fields fails this
    test BY NAME (E2.3 mutation RF3)."""
    rf_on, _, _, _, _ = _fitted(compute_oob_diagnostic=True)
    rf_off, _, _, _, _ = _fitted(compute_oob_diagnostic=False)
    report = rf_on.report()
    oob = report.oob_diagnostic_not_validation
    assert oob is not None and np.isfinite(oob)

    facing = report.validation_facing_fields()
    flat = json.dumps(facing, sort_keys=True).lower()
    assert "oob" not in flat and "out_of_bag" not in flat and "out-of-bag" not in flat
    # RECURSIVE leaf walk (review: a top-level check missed a nested value)
    # and a check that no leaf is a cheap derivation of the OOB float.
    def leaves(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                yield from leaves(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                yield from leaves(v)
        else:
            yield obj
    for leaf in leaves(facing):
        if isinstance(leaf, (int, float)) and not isinstance(leaf, bool):
            for derived in (oob, 1.0 - oob, 100.0 * oob, round(100.0 * oob, 1), -oob):
                assert not np.isclose(leaf, derived, rtol=0, atol=1e-12), (leaf, derived)
    # And the STRUCTURAL check: OOB on vs off, same seed, IDENTICAL provenance
    # structure — nothing validation-facing can have been computed from OOB.
    assert facing == rf_off.report().validation_facing_fields()
    assert rf_off.report().oob_diagnostic_not_validation is None


def test_oob_diagnostic_is_none_unless_explicitly_requested() -> None:
    rf, _, _, _, _ = _fitted()
    assert rf.report().oob_diagnostic_not_validation is None


# ------------------------------------------------------- report contents


def test_report_records_seed_hyperparameters_semantics_and_per_seed_importance() -> None:
    rf, X, _, _, _ = _fitted()
    report = rf.report()
    # Read back FROM the fitted forest (review: echoing constructor literals
    # let a mutated forest carry a FALSE provenance record; RF5/RF6 below).
    assert report.seed == rf._forest.get_params()["random_state"] == 0
    assert report.n_estimators == len(rf._forest.estimators_) == 200
    assert report.hyperparameters["max_samples_leaf"] == rf._forest.get_params()["max_samples_leaf"] is None
    assert report.hyperparameters["aggregate_leaves_first"] is True
    assert report.hyperparameters["weighted_leaves"] is True
    assert report.hyperparameters["sd_ddof"] == 0
    assert any(k.endswith("_reason") for k in report.hyperparameters)
    assert report.uncertainty_method == UNCERTAINTY_METHOD == "qrf_conditional_distribution_sd"
    assert "POOLED" in report.uncertainty_semantics and "ddof=0" in report.uncertainty_semantics
    assert set(report.importance_by_seed) == {0, 1, 2}
    for values in report.importance_by_seed.values():
        assert len(values) == 8 and abs(sum(values) - 1.0) < 1e-9
    # Per-seed means PER SEED: the tuples differ (review: a loop reusing the
    # seed-0 forest for every seed passed a key-set-only assertion), and
    # each equals a fresh forest built under that seed.
    imps = report.importance_by_seed
    assert imps[0] != imps[1] or imps[0] != imps[2]
    fresh = RandomForestEstimator._make_forest(2, 200, False).fit(X, _fitted()[2])
    assert np.allclose(imps[2], fresh.feature_importances_)
    assert report.distinct_x_rows == 4
    assert report.n_training == 35 and report.n_features == 8


def test_refusals_name_their_condition() -> None:
    rf = RandomForestEstimator(seed=0, n_estimators=10, importance_seeds=(0,))
    with pytest.raises(ValueError, match="before fit"):
        rf.predict(np.zeros((2, 8)))
    with pytest.raises(ValueError, match="2-D"):
        rf.fit(np.zeros(5), np.zeros(5))
    with pytest.raises(ValueError, match="does not match"):
        rf.fit(np.zeros((5, 2)), np.zeros(4))
    with pytest.raises(ValueError, match="non-finite"):
        rf.fit(np.array([[0.0, np.nan], [1.0, 2.0]]), np.zeros(2))
    named = RandomForestEstimator(seed=0, n_estimators=10, importance_seeds=(0,), feature_names=("a", "b"))
    with pytest.raises(ValueError, match="feature names"):
        named.fit(np.zeros((3, 3)), np.zeros(3))
    fitted, _, _, _, _ = _fitted()
    with pytest.raises(ValueError, match=r"\(m, 8\)"):
        fitted.predict(np.zeros((2, 3)))
    bad = np.zeros((2, 8)); bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="NaN/inf"):
        fitted.predict(bad)  # review: sklearn routes NaN silently otherwise
    with pytest.raises(ValueError, match="before fit"):
        rf.predict_quantiles(np.zeros((2, 8)))
    assert fitted.predict_quantiles(np.zeros((1, 8)), quantiles=(0.5,)).shape == (1, 1)


# ------------------------------------------------- real matrix end to end


def test_rf_runs_on_the_real_training_matrix_paired_finite_and_still_watermarked() -> None:
    """35 predictions, finite, paired; the matrix's SYNTHETIC computed origin
    is untouched by fitting a model on it (the watermark is a property of
    the inputs, not of what was fitted)."""
    with tempfile.TemporaryDirectory() as tmp:
        dem_path = Path(tmp) / "dem.tif"
        write_synthetic_bathymetry(dem_path)
        written = build_covariate_stack(dem_path, Path(tmp) / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
        stack_manifest = json.loads(written["provenance"].read_text())
        corpus_manifest = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
        grid = DemGrid.load(dem_path)
        layers = build_covariate_registry().build_all(grid)
        matrix, manifest = assemble_training_matrix(
            CorpusCsvSampleSource(), grid, layers, corpus_manifest, stack_manifest
        )

    rf = RandomForestEstimator(seed=0, n_estimators=200, importance_seeds=(0, 1, 2), feature_names=matrix.covariate_names)
    rf.fit(matrix.X, matrix.y)
    mean, sd = rf.predict(matrix.X)
    assert mean.shape == sd.shape == (35,)
    assert (sd > 0).all()  # co-celled stations have within-cell spread
    assert rf.report().distinct_x_rows == 4  # the E2.0-3 fact, recomputed
    # The walkthrough's claim as a guard (review): in-sample R² sits AT the
    # E2.0-3 ceiling (a full-depth forest memorizes the 4 cell means).
    ss_tot = ((matrix.y - matrix.y.mean()) ** 2).sum()
    r2 = 1 - ((matrix.y - mean) ** 2).sum() / ss_tot
    _, idx = np.unique(matrix.X, axis=0, return_inverse=True)
    cell_means = np.array([matrix.y[idx == g].mean() for g in range(4)])[idx]
    ceiling = 1 - ((matrix.y - cell_means) ** 2).sum() / ss_tot
    assert round(ceiling, 3) == 0.348
    assert r2 <= ceiling + 1e-3
    assert np.abs(mean - cell_means).max() < 0.2
    assert manifest.data_origin == "SYNTHETIC"
    assert matrix_watermark(manifest.data_origin) is not None


def test_random_forest_registers_and_the_baseline_stays_the_only_required() -> None:
    registry = build_default_registry()
    assert "random_forest" in registry.names()
    rf = registry.get("random_forest")
    assert isinstance(rf, RandomForestEstimator)
    assert REQUIRED_ESTIMATORS == (MEAN_BASELINE_NAME,)
    # The PRODUCTION instance carries no OOB even under its honest name
    # (review: nothing pinned this).
    X, y, _, _ = _rank4_fixture()
    rf.fit(X, y)
    assert rf.report().oob_diagnostic_not_validation is None
    assert not hasattr(rf._forest, "oob_score_")
