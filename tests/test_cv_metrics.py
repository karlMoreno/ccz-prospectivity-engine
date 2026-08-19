"""E2.4 §1D — the metric set and its division policies, on a hand-computed
fixture.

Fixture (CLAUDE.md rule 4): observed y = [10, 12, 15, 9, 20], predicted
p = [11, 10, 15, 12, 14] → errors (p − y) = [1, −2, 0, 3, −6]. On it
RMSE = √10 = 3.1623, MAE = 2.4, median|e| = 2.0, ME = −0.8: FOUR different
numbers, so a swap among RMSE / MAE / ME cannot pass (on symmetric ±c
errors RMSE = MAE = c and ME = 0 coincide) and the mean→median swap in MAE
— its named "robust twin" — is visible (the earlier fixture's |e| =
[1,2,0,3,4] had mean = median = 2.0, a blindness the §1 review found).
sd = [2, 1, 0, 3, 5] puts one CORRECT-CERTAIN point (sd 0, e 0) in the
set, separating "sd=0 contributes z=0" from "sd=0 is dropped" (dropping it
changes n from 5 to 4 and the RMS accordingly), and sd' = [2, 0, 0, 3, 5]
adds one CONFIDENTLY-WRONG point.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from engine.prospectivity.validation.metrics import (
    METRIC_NAMES,
    SD_ZERO_POLICY,
    MetricValue,
    coverage_1sigma,
    mae,
    mean_error,
    r2_pooled,
    rmse,
    rmse_ratio,
    rmse_uplift,
    score_predictions,
    standardized_rmse,
)

Y = [10.0, 12.0, 15.0, 9.0, 20.0]
P = [11.0, 10.0, 15.0, 12.0, 14.0]
SD = [2.0, 1.0, 0.0, 3.0, 5.0]
SD_WRONG_CERTAIN = [2.0, 0.0, 0.0, 3.0, 5.0]


def test_rmse_mae_and_mean_error_are_hand_computed_and_distinct() -> None:
    assert rmse(Y, P).value == pytest.approx(math.sqrt(10.0))
    assert mae(Y, P).value == pytest.approx(2.4)  # median|e| would be 2.0
    me = mean_error(Y, P)
    assert me.value == pytest.approx(-0.8)
    assert "predicted - observed" in me.details["sign_convention"]
    for m in (rmse(Y, P), mae(Y, P), me):
        assert m.status == "ok" and m.n == 5


def test_coverage_counts_a_correct_certain_point_as_covered_and_divides_by_nothing() -> None:
    cov = coverage_1sigma(Y, P, SD)
    # |e| <= sd: [1<=2 T, 2<=1 F, 0<=0 T, 3<=3 T, 6<=5 F] -> 3/5
    assert cov.value == pytest.approx(0.6)
    assert cov.details["n_sd_zero"] == 1 and cov.details["nominal_if_gaussian"] == pytest.approx(0.6827)
    assert "symmetric" in cov.details["nominal_note"]  # the QRF caveat travels with the number
    # a point that WAS covered (e=3, sd=3) becomes uncovered when its sd is 0
    # while its error is not — no division involved
    assert coverage_1sigma(Y, P, [2.0, 1.0, 0.0, 0.0, 5.0]).value == pytest.approx(0.4)


def test_standardized_rmse_hand_computed_with_the_correct_certain_point_contributing_z0() -> None:
    m = standardized_rmse(Y, P, SD)
    # z = [0.5, -2, 0 (policy), 1, -1.2]; z² = [0.25, 4, 0, 1, 1.44]; mean = 6.69/5
    assert m.value == pytest.approx(math.sqrt(6.69 / 5.0))
    assert m.status == "ok" and m.n == 5
    assert m.details["n_sd_zero"] == 1 and m.details["n_sd_zero_wrong"] == 0
    assert m.details["sd_zero_policy"] == SD_ZERO_POLICY
    # the finite part over sd>0 points is carried too: [0.25, 4, 1, 1.44] over 4
    assert m.details["value_sd_positive_only"] == pytest.approx(math.sqrt(6.69 / 4.0))


def test_standardized_rmse_is_undefined_by_name_when_an_sd_zero_point_is_wrong_and_is_never_dropped() -> None:
    """The obligation-3 observer: a confidently-wrong point makes the
    headline None with a status naming the count; the counts and the
    sd>0-only RMS are carried; the value is NOT a finite number computed
    over the other four (which is what silent dropping would produce)."""
    m = standardized_rmse(Y, P, SD_WRONG_CERTAIN)
    assert m.value is None
    assert "1 confidently-wrong sd=0" in m.status
    assert m.details["n_sd_zero"] == 2 and m.details["n_sd_zero_wrong"] == 1
    # points 0, 3, 4 have sd>0: z² = 0.25, 1, 1.44
    assert m.details["value_sd_positive_only"] == pytest.approx(math.sqrt(2.69 / 3.0))
    assert m.n == 5  # the wrong point still counts toward n


def test_the_numerical_zero_treats_ulp_noise_as_zero_for_both_live_sd_zero_sources() -> None:
    """The two LIVE sources of sd=0 do not produce bitwise zeros: a constant-y
    baseline's std(ddof=1) is ~1e-17 when the mean is not exactly
    representable, and QRF's weighted mean of a single-valued leaf can sit
    1 ulp off its constant. Both must land in the sd≈0 branch; a 1-ulp
    residual is correct-certain, not confidently-wrong."""
    y = np.array([19.6] * 7)  # a real corpus abundance, seven times
    baseline_sd = float(y.std(ddof=1))
    assert 0.0 < baseline_sd < 1e-14  # the point: ~3.8e-15, NOT bitwise zero
    one_ulp = y + 4e-15  # ~1 ulp above 19.6
    assert (one_ulp != y).all()
    # correct-certain to within float noise: z-RMS 0, all covered, all sd≈0
    m = standardized_rmse(y, one_ulp, [baseline_sd] * 7)
    assert m.value == 0.0 and m.details["n_sd_zero"] == 7 and m.details["n_sd_zero_wrong"] == 0
    assert coverage_1sigma(y, one_ulp, [baseline_sd] * 7).value == 1.0
    # confidently wrong under the same ~1e-15 sd: undefined by name, not a
    # finite astronomically-large z with status ok
    m2 = standardized_rmse(y, y + 0.05, [baseline_sd] * 7)
    assert m2.value is None and "7 confidently-wrong" in m2.status
    assert coverage_1sigma(y, y + 0.05, [baseline_sd] * 7).value == 0.0
    # a genuinely small but real sd (5e-6 relative) is NOT zero
    m3 = standardized_rmse(y, y + 0.05, [1e-4] * 7)
    assert m3.status == "ok" and m3.details["n_sd_zero"] == 0


def test_r2_pooled_hand_computed_and_undefined_by_name_for_constant_or_single_y() -> None:
    # SSE = 1+4+0+9+36 = 50; ȳ = 13.2; SS_tot = 78.8
    assert r2_pooled(Y, P).value == pytest.approx(1.0 - 50.0 / 78.8)
    const = r2_pooled([5.0, 5.0, 5.0], [4.0, 6.0, 5.0])
    assert const.value is None and "SS_tot = 0" in const.status
    # a constant whose mean is NOT exactly representable (SS_tot ~1e-34, not
    # 0.0) must reach the same named status, not an absurd finite R²
    unrepresentable = r2_pooled([19.6] * 7, [20.0] * 7)  # SS_tot ~1e-28, not 0.0
    assert unrepresentable.value is None and "constant" in unrepresentable.status
    single = r2_pooled([5.0], [4.0])
    assert single.value is None and "fewer than 2" in single.status


def test_rmse_uplift_is_a_difference_and_rmse_ratio_names_the_zero_baseline_policy() -> None:
    est = rmse(Y, P)  # √10
    base = rmse(Y, [13.2] * 5)  # baseline = mean of Y; errors 3.2,1.2,-1.8,4.2,-6.8
    assert base.value == pytest.approx(math.sqrt(78.8 / 5.0))
    up = rmse_uplift(est, base)
    assert up.value == pytest.approx(base.value - est.value) and up.value > 0
    assert rmse_ratio(est, base).value == pytest.approx(est.value / base.value)
    perfect = rmse(Y, Y)
    ratio = rmse_ratio(est, perfect)
    assert ratio.value is None and "baseline rmse is 0" in ratio.status
    with pytest.raises(ValueError, match="two ok rmse values"):
        rmse_uplift(mae(Y, P), base)
    with pytest.raises(ValueError, match="not the same held-out set"):
        rmse_uplift(est, rmse(Y[:4], P[:4]))
    with pytest.raises(ValueError, match="not the same held-out set"):
        rmse_ratio(est, rmse(Y[:4], P[:4]))


def test_metric_value_refuses_a_bare_null_and_a_non_finite_value() -> None:
    with pytest.raises(ValueError, match="value None must pair"):
        MetricValue("x", None, "ok", 1)
    with pytest.raises(ValueError, match="value None must pair"):
        MetricValue("x", 1.0, "undefined: whatever", 1)
    with pytest.raises(ValueError, match="non-finite"):
        MetricValue("x", float("inf"), "ok", 1)
    record = json.loads(json.dumps(standardized_rmse(Y, P, SD_WRONG_CERTAIN).to_record()))
    assert record["value"] is None and record["status"].startswith("undefined")


def test_score_predictions_returns_exactly_the_declared_metric_set_in_order() -> None:
    scored = score_predictions(Y, P, SD)
    assert tuple(scored) == METRIC_NAMES
    assert all(v.name == k for k, v in scored.items())


def test_score_predictions_values_equal_the_standalone_metrics_and_keep_the_sign_convention() -> None:
    """The runner calls score_predictions per (fold, estimator); its VALUES
    must be the standalone functions' values with the arguments in the
    right order — a swapped (observed, predicted) would flip mean_error's
    sign, and mean_error IS the theorem's measurement (obligation 8c)."""
    scored = score_predictions(Y, P, SD)
    expected = {
        "rmse": rmse(Y, P),
        "mae": mae(Y, P),
        "mean_error": mean_error(Y, P),
        "coverage_1sigma": coverage_1sigma(Y, P, SD),
        "standardized_rmse": standardized_rmse(Y, P, SD),
    }
    assert scored == expected  # full MetricValue equality, every field
    assert scored["mean_error"].value == pytest.approx(-0.8)  # predicted − observed
    swapped = score_predictions(P, Y, SD)
    assert swapped["mean_error"].value == pytest.approx(+0.8)
    assert swapped["rmse"] == scored["rmse"] and swapped["mae"] == scored["mae"]  # symmetric ones


def test_scoring_refuses_shape_mismatch_non_finite_and_bad_sd_by_name() -> None:
    with pytest.raises(ValueError, match="matching 1-D"):
        rmse(Y, P[:-1])
    with pytest.raises(ValueError, match="non-finite"):
        rmse(Y, [1.0, 2.0, np.nan, 4.0, 5.0])
    with pytest.raises(ValueError, match="sd shape"):
        coverage_1sigma(Y, P, SD[:-1])
    with pytest.raises(ValueError, match="non-negative"):
        standardized_rmse(Y, P, [1.0, -1.0, 1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="no predictions"):
        rmse([], [])
