"""Comparison metrics for the CV runner — the metric SET and every division
policy, decided at design time (E2.4 §1D; BACKLOG §3 runner obligation 3,
LIVE).

THE SET, and why each is in it:

    rmse            √mean(e²)         e = predicted − observed (kg/m²)
    mae             mean|e|           the robust twin; separates from RMSE
                                      when errors are uneven
    mean_error      mean(e)           SIGNED bias — across the two clusters
                                      this IS the theorem's measurement:
                                      "cluster A's mean vs cluster B's
                                      values" (obligation 8c)
    coverage_1sigma mean(|e| ≤ sd)    does the paired uncertainty MEAN
                                      anything? nominal 0.683 for a ±1σ
                                      interval UNDER NORMALITY (baseline
                                      SD, kriging sd). For QRF the scored
                                      interval is mean ± (q84−q16)/2, which
                                      equals [q16, q84] (68% by
                                      construction) only when the leaf
                                      population is symmetric about its
                                      mean — so the nominal is Gaussian and
                                      is LABELLED so; the semantics column
                                      (obligation 7) is what makes the
                                      three coverages readable side by side
    standardized_rmse  √mean(z²), z = e/sd — 1.0 when the sd is honest;
                                      > 1 over-confident, < 1 under-
                                      confident. DIVIDES BY sd → policy
                                      below.
    r2 (POOLED)     1 − Σe²/Σ(y−ȳ)²  over ALL held-out predictions of a
                                      design, so RF's held-out number can be
                                      read against the 0.348 in-sample
                                      ceiling. DIVIDES BY SS_tot → policy
                                      below. NEVER per fold: a leave-one-out
                                      fold has one test point and SS_tot = 0.
    rmse_uplift     rmse_baseline − rmse_estimator (kg/m²; > 0 beats the
                                      floor). A DIFFERENCE — no division.
    rmse_ratio      rmse_estimator / rmse_baseline — DIVIDES → policy below.

NOT in the set, and why: CRPS / log score assume a distributional form the
three sd semantics do not share (a quantile half-width is not a Gaussian
σ); interval score at other levels would need quantiles the baseline and
kriging do not report. Coverage at ±1σ is the honest common denominator.

THE sd = 0 POLICY (obligation 3 — written while the real-matrix count is
0 of 35 and PINNED, so this is insurance whose trigger is visible).
"sd == 0" and "e == 0" are NUMERICAL, not bitwise (§1 review): a
constant-y baseline's `std(ddof=1)` is ~1e-17, not 0.0, whenever the mean
is not exactly representable, and quantile-forest's weighted mean of a
single-valued leaf population can sit 1 ulp off the constant — a bitwise
`== 0.0` would miss the first source entirely and flag the second as
confidently WRONG. Both are defined through ZERO_TOL_REL = 1e-9 relative
to the point's scale max(|observed|, |predicted|): one part in 10⁹ is
floating-point noise for kg/m² values, twelve orders of magnitude below
any measured abundance difference — a numerical equality, NOT a
statistical tolerance, and stated in every result's details.

  * a point with sd ≈ 0 and e ≈ 0 is a CORRECT CERTAIN prediction:
    z = 0, covered — it contributes normally;
  * a point with sd ≈ 0 and |e| > tol is a CONFIDENTLY-WRONG prediction:
    z is infinite. `standardized_rmse` then reports value = None with
    status naming the count ("undefined: k confidently-wrong sd=0
    point(s)"), and ALWAYS carries n_sd_zero and n_sd_zero_wrong so the
    reader sees why. It NEVER drops those points to produce a finite,
    flattering number — dropping them excludes exactly the points where
    the model is most wrong about itself. The finite RMS over the sd > 0
    points is carried under the honest name `value_sd_positive_only`, so
    no information is lost and no headline is flattering.
  * coverage: covered iff |e| ≤ max(sd, tol) — the same numerical zero, so
    a correct-certain point 1 ulp off is covered; no division anywhere.

Value = None + a named status is JSON-honest. Verified on the pinned stack
(pydantic 2.13.4): `model_dump_json()` renders an inf as `null`
(`ser_json_inf_nan="null"`); `model_dump(mode="json")` keeps a TYPED float
field's inf, which `json.dumps` then writes as the non-standard `Infinity`,
but renders an inf nested inside a dict/Any-typed field — the shape a
`to_record()` dict takes in a manifest — as `null`. Silent either way. A
status string survives serialization and the substance hash unchanged;
`details` values are finiteness-guarded too (a non-finite finite-part is
recorded as None with its own note).

OTHER DIVISIONS, named: `r2_pooled` is undefined (status names it) when
n < 2 or the held-out y are CONSTANT — detected as max(y) == min(y), never
as a float SS_tot == 0.0 (a constant vector whose mean is not exactly
representable has SS_tot ~1e-34, and 1 − SSE/1e-34 is a silent absurdity —
§1 review); `rmse_ratio` is undefined when the baseline RMSE is exactly 0
(a perfect floor — status names it; a near-zero baseline gives a large but
truthful ratio, and both comparison metrics refuse rmse values scored on
different n).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

METRIC_NAMES: tuple[str, ...] = (
    "rmse",
    "mae",
    "mean_error",
    "coverage_1sigma",
    "standardized_rmse",
)
POOLED_METRIC_NAMES: tuple[str, ...] = ("r2_pooled",)
COMPARISON_METRIC_NAMES: tuple[str, ...] = ("rmse_uplift", "rmse_ratio")

SD_ZERO_POLICY = (
    "zero is NUMERICAL: sd <= ZERO_TOL_REL*max(|y|,|p|) and |error| <= the same tolerance; "
    "sd~0 & error~0: correct-certain, z=0, covered, counted normally; "
    "sd~0 & |error|>tol: confidently-wrong, standardized_rmse value=None with a status "
    "naming the count (never dropped, never floored); n_sd_zero and n_sd_zero_wrong "
    "always carried; finite RMS over sd>0 points carried as value_sd_positive_only"
)
STATUS_OK = "ok"
# The numerical zero (see the module docstring): relative to the point's
# scale, max(|observed|, |predicted|). One part in 10^9. NOT a statistical
# tolerance — a floating-point equality for kg/m² values.
ZERO_TOL_REL = 1e-9


@dataclass(frozen=True)
class MetricValue:
    """One metric on one set of predictions. `value` is None exactly when
    `status` != "ok", and the status NAMES why — a reader never sees a
    bare null."""

    name: str
    value: float | None
    status: str
    n: int
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (self.value is None) != (self.status != STATUS_OK):
            raise ValueError(
                f"MetricValue {self.name!r}: value None must pair with a non-ok status "
                f"and vice versa (value={self.value!r}, status={self.status!r})"
            )
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError(
                f"MetricValue {self.name!r} carries a non-finite value {self.value!r} — a "
                "non-finite metric must be reported as value=None with a named status "
                "(serialized, an inf becomes null or the non-standard Infinity, silently)"
            )

    def to_record(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "status": self.status,
            "n": self.n,
            "details": dict(self.details),
        }


def _errors(observed: Any, predicted: Any) -> np.ndarray:
    y = np.asarray(observed, dtype=np.float64)
    p = np.asarray(predicted, dtype=np.float64)
    if y.ndim != 1 or p.shape != y.shape:
        raise ValueError(f"observed {y.shape} and predicted {p.shape} must be matching 1-D")
    if y.size == 0:
        raise ValueError("no predictions to score")
    if not (np.isfinite(y).all() and np.isfinite(p).all()):
        raise ValueError("non-finite observed/predicted value — refusing to score")
    return p - y  # SIGN CONVENTION: predicted − observed; positive = over-prediction


def rmse(observed: Any, predicted: Any) -> MetricValue:
    e = _errors(observed, predicted)
    return MetricValue("rmse", float(np.sqrt(np.mean(e**2))), STATUS_OK, int(e.size))


def mae(observed: Any, predicted: Any) -> MetricValue:
    e = _errors(observed, predicted)
    return MetricValue("mae", float(np.mean(np.abs(e))), STATUS_OK, int(e.size))


def mean_error(observed: Any, predicted: Any) -> MetricValue:
    e = _errors(observed, predicted)
    return MetricValue(
        "mean_error",
        float(np.mean(e)),
        STATUS_OK,
        int(e.size),
        {"sign_convention": "predicted - observed; positive = over-prediction"},
    )


def _zero_tolerance(observed: np.ndarray, predicted: np.ndarray) -> np.ndarray:
    """Per-point numerical-zero threshold: ZERO_TOL_REL × max(|y|, |p|)."""
    return ZERO_TOL_REL * np.maximum(np.abs(observed), np.abs(predicted))


def _checked_sd(sd: Any, n: int) -> np.ndarray:
    s = np.asarray(sd, dtype=np.float64)
    if s.shape != (n,):
        raise ValueError(f"sd shape {s.shape} does not match {n} predictions")
    if not np.isfinite(s).all() or (s < 0).any():
        raise ValueError("sd must be finite and non-negative — the pairing template guarantees this")
    return s


def coverage_1sigma(observed: Any, predicted: Any, sd: Any) -> MetricValue:
    e = _errors(observed, predicted)
    s = _checked_sd(sd, e.size)
    tol = _zero_tolerance(np.asarray(observed, dtype=np.float64), np.asarray(predicted, dtype=np.float64))
    # |e| <= max(sd, tol): a correct-certain point 1 ulp off is covered; a
    # confidently-wrong one is not. No division anywhere.
    covered = np.abs(e) <= np.maximum(s, tol)
    return MetricValue(
        "coverage_1sigma",
        float(np.mean(covered)),
        STATUS_OK,
        int(e.size),
        {
            "nominal_if_gaussian": 0.6827,
            "nominal_note": (
                "0.6827 is the ±1σ nominal UNDER NORMALITY (baseline SD, kriging sd); "
                "QRF's scored interval is mean ± (q84−q16)/2, which is [q16, q84] only "
                "for a symmetric leaf population — read with the semantics column"
            ),
            "n_sd_zero": int((s <= tol).sum()),
            "zero_tolerance_rel": ZERO_TOL_REL,
        },
    )


def standardized_rmse(observed: Any, predicted: Any, sd: Any) -> MetricValue:
    """√mean(z²) with the sd=0 policy above (obligation 3)."""
    e = _errors(observed, predicted)
    s = _checked_sd(sd, e.size)
    tol = _zero_tolerance(np.asarray(observed, dtype=np.float64), np.asarray(predicted, dtype=np.float64))
    sd_zero = s <= tol  # the NUMERICAL zero (module docstring)
    wrong_certain = sd_zero & (np.abs(e) > tol)
    n_zero, n_wrong = int(sd_zero.sum()), int(wrong_certain.sum())
    positive = ~sd_zero
    finite_part: float | None = None
    finite_note = "no sd>0 points"
    if positive.any():
        candidate = float(np.sqrt(np.mean((e[positive] / s[positive]) ** 2)))
        if math.isfinite(candidate):
            finite_part, finite_note = candidate, "RMS of z over the sd>0 points"
        else:
            finite_note = "overflowed to non-finite over the sd>0 points — recorded as None"
    details: dict[str, Any] = {
        "nominal": 1.0,
        "sd_zero_policy": SD_ZERO_POLICY,
        "zero_tolerance_rel": ZERO_TOL_REL,
        "n_sd_zero": n_zero,
        "n_sd_zero_wrong": n_wrong,
        "value_sd_positive_only": finite_part,
        "value_sd_positive_only_note": finite_note,
    }
    if n_wrong:
        return MetricValue(
            "standardized_rmse",
            None,
            f"undefined: {n_wrong} confidently-wrong sd=0 point(s) (infinite z) — see details",
            int(e.size),
            details,
        )
    # sd≈0 & e≈0 contribute z=0 by policy.
    z = np.zeros_like(e)
    z[positive] = e[positive] / s[positive]
    value = float(np.sqrt(np.mean(z**2)))
    if not math.isfinite(value):
        return MetricValue(
            "standardized_rmse", None, "undefined: z overflowed to non-finite", int(e.size), details
        )
    return MetricValue("standardized_rmse", value, STATUS_OK, int(e.size), details)


def r2_pooled(observed: Any, predicted: Any) -> MetricValue:
    """Pooled over ALL held-out predictions of a design — never per fold."""
    e = _errors(observed, predicted)
    y = np.asarray(observed, dtype=np.float64)
    if y.size < 2:
        return MetricValue("r2_pooled", None, "undefined: fewer than 2 held-out points", int(y.size))
    if y.max() == y.min():
        # Constant y detected on the VALUES, never via a float SS_tot == 0.0
        # (a constant whose mean is not exactly representable has SS_tot
        # ~1e-34 and would yield an absurd finite R² with status ok).
        return MetricValue(
            "r2_pooled", None, "undefined: held-out y are constant (SS_tot = 0)", int(y.size)
        )
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    value = float(1.0 - np.sum(e**2) / ss_tot)
    if not math.isfinite(value):
        return MetricValue("r2_pooled", None, "undefined: non-finite R² (SS_tot underflow)", int(y.size))
    return MetricValue("r2_pooled", value, STATUS_OK, int(y.size))


def rmse_uplift(rmse_estimator: MetricValue, rmse_baseline: MetricValue) -> MetricValue:
    """rmse_baseline − rmse_estimator: kg/m², positive beats the floor. A
    difference; no division. Both inputs must be OK rmse values."""
    for m in (rmse_estimator, rmse_baseline):
        if m.name != "rmse" or m.value is None:
            raise ValueError(f"rmse_uplift needs two ok rmse values, got {m.name!r}/{m.status!r}")
    if rmse_estimator.n != rmse_baseline.n:
        raise ValueError(
            f"rmse_uplift: estimator rmse over n={rmse_estimator.n} vs baseline over "
            f"n={rmse_baseline.n} — not the same held-out set (per-fold baseline pairing)"
        )
    return MetricValue(
        "rmse_uplift",
        float(rmse_baseline.value - rmse_estimator.value),
        STATUS_OK,
        rmse_estimator.n,
        {"sign_convention": "baseline - estimator; positive = beats the baseline"},
    )


def rmse_ratio(rmse_estimator: MetricValue, rmse_baseline: MetricValue) -> MetricValue:
    for m in (rmse_estimator, rmse_baseline):
        if m.name != "rmse" or m.value is None:
            raise ValueError(f"rmse_ratio needs two ok rmse values, got {m.name!r}/{m.status!r}")
    if rmse_estimator.n != rmse_baseline.n:
        raise ValueError(
            f"rmse_ratio: estimator rmse over n={rmse_estimator.n} vs baseline over "
            f"n={rmse_baseline.n} — not the same held-out set (per-fold baseline pairing)"
        )
    if rmse_baseline.value == 0.0:
        return MetricValue(
            "rmse_ratio",
            None,
            "undefined: baseline rmse is 0 (a perfect floor) — nothing to divide by",
            rmse_estimator.n,
        )
    return MetricValue(
        "rmse_ratio",
        float(rmse_estimator.value / rmse_baseline.value),
        STATUS_OK,
        rmse_estimator.n,
        {"reading": "< 1 beats the baseline"},
    )


def score_predictions(observed: Any, predicted: Any, sd: Any) -> dict[str, MetricValue]:
    """Every per-fold metric in METRIC_NAMES on one (observed, predicted, sd)
    triple — the runner calls this per (fold, estimator). Returns exactly
    METRIC_NAMES, in order (a completeness test pins the set)."""
    return {
        "rmse": rmse(observed, predicted),
        "mae": mae(observed, predicted),
        "mean_error": mean_error(observed, predicted),
        "coverage_1sigma": coverage_1sigma(observed, predicted, sd),
        "standardized_rmse": standardized_rmse(observed, predicted, sd),
    }
