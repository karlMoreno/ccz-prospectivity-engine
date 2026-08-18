"""RandomForestEstimator — quantile regression forest with conditional-
distribution uncertainty (E2.3 §2; Karl's decision 2026-08-14, the measured
case in docs/walkthroughs/E2.3.md §1).

STRATEGY (third concrete Estimator under the E2.1 ABC): implements the
`_predict` hook — `predict()` is the ABC's final Template Method, so the
pairing validation (shape, finiteness, non-negative sd) runs on this
output by construction.

UNCERTAINTY SEMANTICS, stated so E2.4's table can be read: the paired sd is
the standard deviation of the CONDITIONAL DISTRIBUTION of y given X — the
y values retained in the leaves that X falls into, POOLED across all trees
with per-tree 1/leaf-size weights (Meinshausen 2006 eq. 5–7; quantile-
forest `aggregate_leaves_first=True, weighted_leaves=True`,
`max_samples_leaf=None`). That is a PREDICTIVE spread, the same question
the baseline's SD and kriging's variance answer. It is NOT the ensemble
spread (SD of per-tree means), which §1 measured at 2–4× too small on
rank-4 X because all trees fit the same four rows. The estimator also
exposes quantiles for interval reporting.

THE AGGREGATION SETTING IS LOAD-BEARING (E2.3 adversarial review, must-
fix): quantile-forest's `aggregate_leaves_first=False` computes each
TREE's quantile function and averages them — on any training set with
DISTINCT X rows every leaf holds one y, every per-tree quantile function
is flat, and the sd is IDENTICALLY ZERO; on rank-4 X it understated the
pooled sd by 17–31%. The pre-review code passed False, and the rank-4
fixtures were structurally blind to it (CLAUDE.md rule 4). Every sd-
defining setting is now recorded in `report().hyperparameters`, and a
distinct-X test pins sd > 0 near the planted noise.

DDOF CONVENTION, stated (review): the sd is the ddof=0 sd of the empirical
conditional distribution — an ECDF has no Bessel correction. E2.4
comparability caveat: at cell occupancy n this is ≈ √((n−1)/n) × a ddof=1
SD (−3.6% at n=14, −7.7% at n=7), so the RF column runs slightly below the
baseline's ddof=1 SD by convention, not by evidence.

TWO FACTS THAT BOUND WHAT THIS MODEL CAN CLAIM ON TODAY'S DATA (reported
in the walkthrough before this code; restated here because a consumer
reads the estimator, not the walkthrough):
  * n = 35, k = 8, and X has FOUR distinct rows (centered rank 3). The
    E2.0-3 ceiling R² = 0.348 BINDS this estimator: co-celled stations have
    identical X and different y — irreducible to any covariate model.
    Importance here is arithmetic over 4 examples. Kriging is exempt
    (coordinates); the asymmetry is on record in the E2.0 closeout.
  * All 8 covariates derive from one DEM: 12 of 28 pairs have |r| > 0.9
    (tpi/bpi at 1.00). Collinear features split credit unstably, so a
    single-seed importance ranking is noise wearing a bar chart — which is
    why `report()` carries importance PER SEED, and the walkthrough shows
    the rank churn.

THE OOB HARD RULE — structural, not documentary: out-of-bag resampling is
RANDOM resampling, which on autocorrelated data is spatial leakage — the
failure mode this project's methodology exists to refuse. OOB is therefore
never computed into a validation-facing field. If a caller asks for the
diagnostic (`compute_oob_diagnostic=True`) it is carried ONLY under
`oob_diagnostic_not_validation`, whose name and docstring say what it is,
and `RandomForestReport.validation_facing_fields()` — the structure E2.4's
provenance consumes — is asserted by test to contain no OOB-derived value
(mutation-verified). E2.5's refuse-to-validate guard re-asserts this at
claim time; this module makes it true at the source.

NO TUNING: no hyperparameter was optimized against any score — there is
no validation to tune against yet, and tuning against training fit is the
flattering direction. The non-defaults, each with its reason, all recorded
in `report().hyperparameters` (read back FROM the fitted forest, never
echoed from constructor literals — review): `n_estimators=500` (stability
of the retained-sample distribution; quantile-forest default 100);
`max_samples_leaf=None` (retain every training y per leaf — the QRF
definition; the default 1 retains one RANDOM sample per leaf per tree, and
quantile-forest's leaf-1 predict path POOLS across trees regardless of the
aggregation flag, which is why an early probe misread it as "closer to
truth" — mutation RF2 record, corrected); `aggregate_leaves_first=True` +
`weighted_leaves=True` (the pooled Meinshausen distribution — see above);
a 199-point quantile grid on [0.005, 0.995] for the moment integration
(the mean comes from quantile-forest's exact `quantiles="mean"`; the grid
sd is a piecewise-linear integral, 0.2–2% low on 7-sample cells — stated).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from quantile_forest import RandomForestQuantileRegressor

from engine.prospectivity.estimators.base import Estimator

UNCERTAINTY_METHOD = "qrf_conditional_distribution_sd"
UNCERTAINTY_SEMANTICS = (
    "ddof=0 sd of the conditional distribution of y given X: all training y "
    "retained in the leaves X falls into, POOLED across trees with per-tree "
    "1/leaf-size weights (Meinshausen 2006; quantile-forest max_samples_leaf="
    "None, aggregate_leaves_first=True, weighted_leaves=True) — a PREDICTIVE "
    "spread comparable to the baseline's SD and kriging's variance; NOT the "
    "ensemble spread of per-tree means (2-4x too small on rank-deficient X, "
    "E2.3 §1) and NOT the per-tree-quantile average (identically 0 on distinct "
    "X, E2.3 §2 review)"
)
QUANTILE_GRID = tuple(float(v) for v in np.linspace(0.005, 0.995, 199))

DEFAULT_QUANTILES = (0.05, 0.5, 0.95)


@dataclass(frozen=True)
class RandomForestReport:
    """Everything E2.4 must carry into run provenance (BACKLOG §3 runner
    obligations). `validation_facing_fields()` is the structure that feeds
    provenance; the OOB diagnostic is deliberately OUTSIDE it."""

    seed: int
    n_estimators: int
    hyperparameters: dict  # every non-default value, with the ONE stated reason
    uncertainty_method: str
    uncertainty_semantics: str
    n_training: int
    n_features: int
    feature_names: tuple[str, ...]
    distinct_x_rows: int  # the E2.0-3 fact, recomputed from the fitted X
    # Impurity importance PER SEED — {seed: (importance per feature)} — so a
    # consumer sees the churn, not one seed's bar chart.
    importance_by_seed: dict[int, tuple[float, ...]]
    # NOT VALIDATION. Out-of-bag R² is computed from RANDOM resampling, which
    # on autocorrelated data leaks spatial information across the "held-out"
    # boundary — the exact leakage spatial CV exists to prevent. Carried only
    # as an in-sample diagnostic under this honest name; excluded from
    # `validation_facing_fields()` by construction and by test. None unless
    # a caller explicitly asked for it.
    oob_diagnostic_not_validation: float | None = None

    def validation_facing_fields(self) -> dict:
        """The provenance-bound structure. Built by EXPLICIT allow-list, so a
        future field is not validation-facing until someone adds it here on
        purpose — and OOB can never arrive by omission."""
        return {
            "seed": self.seed,
            "n_estimators": self.n_estimators,
            "hyperparameters": dict(self.hyperparameters),
            "uncertainty_method": self.uncertainty_method,
            "uncertainty_semantics": self.uncertainty_semantics,
            "n_training": self.n_training,
            "n_features": self.n_features,
            "feature_names": list(self.feature_names),
            "distinct_x_rows": self.distinct_x_rows,
            "importance_by_seed": {
                int(seed): list(values) for seed, values in self.importance_by_seed.items()
            },
        }


class RandomForestEstimator(Estimator):
    """QRF behind the E2.1 ABC. `seed` is a constructor argument recorded in
    `report()` (E2.4 provenance, the same rule as kriging's parameters).
    `importance_seeds` are the EXTRA seeds importance is recomputed under to
    demonstrate (not assert) its instability; the prediction forest is
    always the one fitted under `seed`."""

    def __init__(
        self,
        *,
        seed: int = 0,
        n_estimators: int = 500,
        importance_seeds: tuple[int, ...] = (0, 1, 2, 3, 4),
        compute_oob_diagnostic: bool = False,
        feature_names: tuple[str, ...] | None = None,
    ) -> None:
        self._seed = int(seed)
        self._n_estimators = int(n_estimators)
        self._importance_seeds = tuple(int(s) for s in importance_seeds)
        self._compute_oob = bool(compute_oob_diagnostic)
        self._feature_names = feature_names
        self._forest: RandomForestQuantileRegressor | None = None
        self._X: np.ndarray | None = None
        self._importance_by_seed: dict[int, tuple[float, ...]] | None = None
        self._oob: float | None = None

    @staticmethod
    def _make_forest(seed: int, n_estimators: int, oob: bool) -> RandomForestQuantileRegressor:
        return RandomForestQuantileRegressor(
            n_estimators=n_estimators,
            random_state=seed,
            max_samples_leaf=None,  # the ONE non-default: retain all leaf samples (QRF definition)
            oob_score=oob,
        )

    def fit(self, features: Any, target: Any) -> None:
        X = np.asarray(features, dtype=np.float64)
        y = np.asarray(target, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError(f"features must be 2-D (n, k), got shape {X.shape}")
        if y.ndim != 1 or y.shape[0] != X.shape[0]:
            raise ValueError(f"target shape {y.shape} does not match features {X.shape}")
        if not (np.isfinite(X).all() and np.isfinite(y).all()):
            raise ValueError("non-finite feature or target — refusing to fit")
        if X.shape[0] < 2:
            raise ValueError(f"cannot fit a forest on {X.shape[0]} row(s)")
        if self._feature_names is not None and len(self._feature_names) != X.shape[1]:
            raise ValueError(
                f"{len(self._feature_names)} feature names for {X.shape[1]} columns"
            )

        # ATOMIC (the E2.2 lesson): compute into locals, assign once at the end.
        forest = self._make_forest(self._seed, self._n_estimators, self._compute_oob)
        forest.fit(X, y)
        importance: dict[int, tuple[float, ...]] = {}
        seeds = (self._seed,) + tuple(s for s in self._importance_seeds if s != self._seed)
        for s in seeds:
            f = forest if s == self._seed else self._make_forest(s, self._n_estimators, False).fit(X, y)
            importance[s] = tuple(float(v) for v in f.feature_importances_)
        oob = float(forest.oob_score_) if self._compute_oob else None

        self._forest = forest
        self._X = X
        self._importance_by_seed = importance
        self._oob = oob

    def _checked_features(self, features: Any, who: str) -> np.ndarray:
        if self._forest is None:
            raise ValueError(f"RandomForestEstimator.{who} called before fit")
        X = np.asarray(features, dtype=np.float64)
        if X.ndim != 2 or X.shape[1] != self._forest.n_features_in_:
            raise ValueError(
                f"{who} features must be (m, {self._forest.n_features_in_}), got {X.shape}"
            )
        if not np.isfinite(X).all():
            # Review: sklearn>=1.4 trees route NaN down a missing-value branch
            # learned on complete data and return a clean-looking number — RF
            # would be the one estimator emitting a finite prediction for a
            # nodata cell. Refuse by name, as fit does.
            raise ValueError(f"{who} features contain NaN/inf — refusing to predict on them")
        return X

    def _pooled_quantiles(self, X: np.ndarray, quantiles: list) -> np.ndarray:
        # aggregate_leaves_first=True + weighted_leaves=True IS the pooled
        # Meinshausen distribution (see module docstring: False averages
        # per-tree quantile functions and collapses to sd 0 on distinct X).
        return np.asarray(
            self._forest.predict(
                X, quantiles=quantiles, aggregate_leaves_first=True, weighted_leaves=True
            )
        )

    def _predict(self, features: Any) -> tuple[np.ndarray, np.ndarray]:
        X = self._checked_features(features, "predict")
        # Mean: quantile-forest's exact weighted mean of the pooled leaf
        # samples (equals sklearn's average-of-tree-means to ~1e-14 under
        # weighted_leaves=True). Sd: the ddof=0 sd of the pooled distribution,
        # integrated over a fine quantile grid (piecewise-linear; 0.2-2% low).
        mean = np.asarray(self._forest.predict(
            X, quantiles="mean", aggregate_leaves_first=True, weighted_leaves=True
        ), dtype=np.float64).reshape(-1)
        q = self._pooled_quantiles(X, list(QUANTILE_GRID)).reshape(X.shape[0], -1)
        sd = q.std(axis=1, ddof=0)
        return mean, sd

    def predict_quantiles(self, features: Any, quantiles: tuple[float, ...] = DEFAULT_QUANTILES) -> np.ndarray:
        """(m, len(quantiles)) conditional quantiles — the interval-reporting
        face of the same pooled distribution `predict()` summarizes. Always
        2-D (quantile-forest squeezes a single quantile; reshaped here)."""
        X = self._checked_features(features, "predict_quantiles")
        qs = [float(v) for v in quantiles]  # np.float32 is rejected by the library
        return self._pooled_quantiles(X, qs).reshape(X.shape[0], len(qs))

    def report(self) -> RandomForestReport:
        if self._forest is None or self._X is None or self._importance_by_seed is None:
            raise ValueError("report() called before fit")
        k = self._X.shape[1]
        names = self._feature_names or tuple(f"x{i}" for i in range(k))
        params = self._forest.get_params()  # read back, never echoed (review)
        return RandomForestReport(
            seed=int(params["random_state"]),
            n_estimators=len(self._forest.estimators_),
            hyperparameters={
                # Every sd-defining setting, so E2.4's provenance carries the
                # parameters that make UNCERTAINTY_METHOD true or false, not
                # only its name (review).
                "max_samples_leaf": params["max_samples_leaf"],
                "max_samples_leaf_reason": (
                    "None retains every training y per leaf — the QRF definition "
                    "(Meinshausen 2006); the default 1 retains one random sample per "
                    "leaf per tree. Principled, not tuned."
                ),
                "aggregate_leaves_first": True,
                "weighted_leaves": True,
                "aggregation_reason": (
                    "pooled Meinshausen distribution; False averages per-tree quantile "
                    "functions and collapses to sd 0 on distinct X (E2.3 review)"
                ),
                "quantile_grid": [QUANTILE_GRID[0], QUANTILE_GRID[-1], len(QUANTILE_GRID)],
                "sd_ddof": 0,
            },
            uncertainty_method=UNCERTAINTY_METHOD,
            uncertainty_semantics=UNCERTAINTY_SEMANTICS,
            n_training=int(self._X.shape[0]),
            n_features=k,
            feature_names=tuple(names),
            distinct_x_rows=int(np.unique(self._X, axis=0).shape[0]),
            importance_by_seed=dict(self._importance_by_seed),
            oob_diagnostic_not_validation=self._oob,
        )
