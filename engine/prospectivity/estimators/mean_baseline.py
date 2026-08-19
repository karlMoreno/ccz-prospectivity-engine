"""MeanBaselineEstimator — the mandatory baseline (E2.1).

STRATEGY (concrete): the first production Estimator. Predicts the training
mean everywhere; uncertainty is the training standard deviation.

SD, NOT STANDARD ERROR — the decision, stated: the uncertainty paired with
a PREDICTION at a new location answers "how spread out are values around
the mean" (SD), not "how well is the mean itself estimated" (SE = SD/√n).
A kriging variance far from data approaches the SILL — the process
variance, the SD's role — and the baseline must be comparable to that at
E2.4's comparison table, or baseline-vs-kriging uncertainty columns would
be answering two different questions. SE shrinks with n toward a false
confidence about individual locations; a 36th station is not easier to
predict because the mean of 35 is well estimated.

Two honesty caveats on that sill correspondence (E2.1 review), recorded so
the argument is not overstated: (1) ORDINARY kriging's variance far from
data exceeds the sill by the Lagrange (mean-estimation) term; the iid
analogue is SD·√(1+1/n) — +1.4% at n=35. Plain SD is kept for
hand-computability; the correspondence is approximate, not exact. (2)
Under positive spatial correlation the sample SD is biased LOW relative to
the sill (E[s²] = sill − mean pairwise covariance), and our 35 stations
sit in two tight clusters — a caveat for reading E2.4, not a code change.

ddof=1 (sample SD): the training set is a sample of the field, not the
field. Stated because the hand-computed tests depend on it.

Constant y yields SD = 0 legitimately (a uniform barren patch is a valid
sample); the division hazard that creates for z-score/CRPS-style metrics
belongs to E2.4's first divider, which must name the sd=0 case (BACKLOG §3
E2.4-runner entry).
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

from engine.prospectivity.estimators.base import Estimator

UNCERTAINTY_SEMANTICS = (
    "sample SD of the training y (ddof=1) — a SAMPLE MOMENT: how spread out the "
    "field's values are around the training mean. Constant everywhere; it does not "
    "grow with distance from data (ordinary kriging's does, by the Lagrange term) "
    "and under positive spatial correlation it is biased LOW relative to the sill."
)


class MeanBaselineEstimator(Estimator):
    """Predicts the training mean everywhere, with the training SD as the
    paired uncertainty. Ignores feature VALUES by construction — only the
    number of rows requested matters — which is exactly what makes it the
    floor every covariate- or coordinate-driven model must beat.

    DECLARATIONS (E2.4 §2C / obligation 7): consumes "covariates" — it reads
    only the row count, and TrainingMatrix.X is the block whose rows ARE the
    stations; declared rather than "any" so the runner has one routing rule
    with no special case."""

    input_kind: ClassVar[str] = "covariates"
    uncertainty_method: ClassVar[str] = "sample_sd_ddof1"
    uncertainty_semantics: ClassVar[str] = UNCERTAINTY_SEMANTICS

    def __init__(self) -> None:
        self._mean: float | None = None
        self._sd: float | None = None

    def fit(self, features: Any, target: Any) -> None:
        y = np.asarray(target, dtype=np.float64)
        if y.ndim != 1:
            raise ValueError(
                f"target must be one-dimensional, got shape {y.shape} — the baseline "
                "fits y alone"
            )
        if y.size < 2:
            raise ValueError(
                f"cannot fit the baseline on {y.size} row(s): the sample SD (ddof=1) "
                "is undefined below n=2, and a silent NaN uncertainty is the failure "
                "mode this refusal exists to prevent"
            )
        if not np.isfinite(y).all():
            # isfinite, not isnan (E2.1 review): an inf target passed the old
            # NaN check and produced mean=inf, sd=NaN silently — the exact
            # failure mode the n<2 refusal above names. The matrix refuses
            # NaN covariates upstream, but that is a NaN policy, not a
            # finiteness policy; this is defense-in-depth for a bypassed
            # matrix either way.
            raise ValueError(
                "target contains NaN or infinity — the E2.0-3 matrix refuses NaN "
                "upstream, so a non-finite value arriving here means the matrix "
                "was bypassed"
            )
        self._mean = float(y.mean())
        self._sd = float(y.std(ddof=1))

    def _predict(self, features: Any) -> tuple[np.ndarray, np.ndarray]:
        if self._mean is None or self._sd is None:
            raise ValueError("MeanBaselineEstimator.predict called before fit")
        # Row count = len(features): the leading dimension of a 2-D block
        # (the TrainingMatrix's X is always 2-D). Caveat, stated: a bare 1-D
        # vector's len() counts its ELEMENTS, so one station's covariate
        # vector would be misread as k stations — pass (1, k), not (k,).
        try:
            n = len(features)
        except TypeError:
            raise ValueError(
                f"MeanBaselineEstimator.predict needs features with a length "
                f"(the row count); got {type(features).__name__}"
            ) from None
        return (
            np.full(n, self._mean, dtype=np.float64),
            np.full(n, self._sd, dtype=np.float64),
        )

    def provenance(self) -> dict:
        """The fitted floor, as data: the training mean IS the across-cluster
        measurement (obligation 8c — "cluster A's mean against cluster B's
        values"), so it must be readable per fold, not recomputed."""
        if self._mean is None or self._sd is None:
            raise ValueError("provenance() called before fit")
        return {
            "training_mean": self._mean,
            "training_sd_ddof1": self._sd,
            "uncertainty_method": self.uncertainty_method,
            "uncertainty_semantics": self.uncertainty_semantics,
        }
