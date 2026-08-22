"""OrdinaryKrigingEstimator — the TS-6-parity spatial estimator (E2.2 §2).

STRATEGY (second concrete Estimator under the E2.1 ABC): implements the
`_predict` hook — `predict()` is the ABC's final Template Method, so the
pairing validation (shape, finiteness, non-negative sd) runs on this
output whether this class likes it or not. That is the E2.1 rogue-override
fix working as designed.

FOR THIS ESTIMATOR, `features` ARE COORDINATES — an (n, 2) block in
(longitude, latitude) order (the TrainingMatrix.coords convention), or
planar (x, y) under `coordinate_system="planar"`, which exists solely so
the known-answer fixture (planar units by design) can test the same
arithmetic the corpus (geographic km) uses. E2.4's runner passes
`matrix.coords` here and `matrix.X` to covariate estimators — recorded in
this docstring because the ABC's signature cannot say it.

THE ORDINARY KRIGING SYSTEM (the classic place implementations go wrong is
the Lagrange row — it is what distinguishes OK from simple kriging):

    [ Γ   1 ] [ w ]   [ γ₀ ]      Γᵢⱼ = γ(dᵢⱼ), γ(0) = 0 on the diagonal
    [ 1ᵀ  0 ] [ μ ] = [ 1  ]      prediction   = wᵀ y
                                  OK variance  = wᵀ γ₀ + μ

γ(0) = 0 exactly (VariogramModel's convention) is what makes OK an EXACT
interpolator at data locations even with a nonzero nugget: at a datum the
right-hand side equals that datum's Γ column, so w is the indicator vector
and the variance collapses to 0.

HONEST FAR-FIELD BEHAVIOUR, not a defect to tune away: with a fitted range
far shorter than the inter-cluster distance (ours: ≤13 km vs ~991 km),
kriging correctly reverts toward the local mean far from data, with
variance approaching the sill — and then EXCEEDING it: OK's far-field
variance is sill + Lagrange term (only simple kriging converges to the
sill exactly). Do not force a long range to make a prediction map look
smooth; the reversion IS the honest output. Two consequences for E2.4's
one-table comparison (carried from E2.1's baseline docstring, now
load-bearing): (1) kriging's far-field uncertainty sits ABOVE the fitted
sill (pinned by test — the Lagrange term made observable); (2) the
baseline's sample SD is biased LOW relative to the sill under our
two-cluster geometry (E[s²] = sill − mean pairwise covariance). So the
two "uncertainties far from data" are NOT the same number, and the table
must be read knowing why.

ANISOTROPY — DECLINED, EXPLICITLY: with 35 points in two ~12 km clusters,
directional binning would produce bins of 2–3 pairs (the omnidirectional
2–4 km bin already holds only 4). A documented refusal, not an oversight;
revisit only when between-cluster sources land (BACKLOG §1 geographic-
spread item).

REPORTABLE STATE for E2.4's provenance (`report()`): the fitted model and
the spherical alternative, the bin table the fit saw, every excluded bin
with its reason, the unsupported lag ranges, the ceiling flag, and the
decisions in force — so any consumer of a prediction can see the model
was extrapolating between the clusters.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.variogram import (
    DEFAULT_BIN_EDGES_KM,
    FittedVariogram,
    bin_pairs,
    empirical_variogram,
    fit_variogram,
    pairwise_distances_km,
)
from engine.prospectivity.provenance.geometry import haversine_km

COORDINATE_SYSTEMS = ("geographic_lonlat", "planar")

UNCERTAINTY_SEMANTICS = (
    "sqrt of the ordinary-kriging variance — a MODEL MOMENT under the fitted "
    "variogram: 0 at a datum (exact interpolator), rising with distance from data "
    "toward the sill and then EXCEEDING it by the Lagrange (mean-estimation) term "
    "far-field. Comparable to but not the same kind of number as the baseline's "
    "sample SD or QRF's quantile half-width."
)
NO_STRUCTURE_VERDICT = (
    "no structure: the fitter's honest verdict is partial_sill == 0 and range == 0 "
    "(a pure-nugget model), so kriging reverts to the training mean everywhere — "
    "baseline-equivalent by the fitter's own verdict, not a tie to be tallied (E2.4 "
    "§1B framing; a per-fold analogue of the two-fold geometry theorem)"
)


@dataclass(frozen=True)
class KrigingReport:
    """Everything E2.4 must carry into run provenance (BACKLOG §3 notes the
    obligation; this task only exposes it)."""

    used_model_family: str
    nugget: float
    partial_sill: float
    sill: float
    range_km: float
    # RANGE UNCONSTRAINED FROM ABOVE when True: the fit sat at the candidate
    # ceiling — on the real corpus the 10–13 km bin is still rising at the
    # edge of support, so the honest fitted answer is not "the range is R"
    # but "the range exceeds what 13 km of support can resolve." Sits NEXT
    # TO range_km so a run-manifest reader cannot see one without the other.
    range_at_candidate_ceiling: bool
    range_below_first_supported_lag: bool  # nugget/sill split unidentifiable
    used_weighted_sse: float  # the used fit's SSE — comparable to alternative's
    residual_dof: int  # fitted bins − 3; 0 = unfalsifiable near-interpolation
    alternative: FittedVariogram  # the spherical fit (with ITS SSE), reported not used
    fitted_bins: tuple  # (lo, hi, pairs, semivariance) rows the fit SAW
    excluded_bins: tuple  # ((lo, hi, pairs), reason) rows it refused
    unsupported_km: tuple  # zero-pair lag ranges — the extrapolation zone
    min_pairs: int
    max_fit_lag_km: float | None
    coordinate_system: str
    n_training: int


class OrdinaryKrigingEstimator(Estimator):
    """Ordinary kriging with a fitted isotropic variogram (exponential
    used; spherical fitted and reported as the alternative — Karl's E2.2
    decision 3). Defaults encode decisions 1 and 2; the known-answer tests
    override them with fixture-appropriate planar values.

    DECLARATIONS (E2.4 §2C / obligation 7): consumes "coordinates" — for
    this estimator, features ARE coordinates (module docstring); the runner
    routes TrainingMatrix.coords here by reading this class attribute,
    never by matching the registry name."""

    input_kind: ClassVar[str] = "coordinates"
    # TAX.1 (2026-08-21): SYNTHETIC's evidence is a generator path AND (a seed
    # OR a determinism basis). This estimator has NO seed because it needs
    # none, so it declares the basis — and the basis must name the MECHANISM,
    # not assert the property.
    determinism_basis: ClassVar[str] = (
        "ordinary kriging solves a closed-form linear system (the OK system "
        "matrix plus a Lagrange multiplier) over a variogram fitted by "
        "weighted least squares on a FIXED candidate range grid; there is no "
        "sampling, no shuffling and no RNG at fit or predict time, so the "
        "output is a function of the inputs alone"
    )
    uncertainty_method: ClassVar[str] = "sqrt_ordinary_kriging_variance"
    uncertainty_semantics: ClassVar[str] = UNCERTAINTY_SEMANTICS

    def __init__(
        self,
        *,
        bin_edges_km: tuple[float, ...] = DEFAULT_BIN_EDGES_KM,
        min_pairs: int = 30,
        max_fit_lag_km: float | None = 13.0,
        coordinate_system: str = "geographic_lonlat",
    ) -> None:
        if coordinate_system not in COORDINATE_SYSTEMS:
            raise ValueError(
                f"coordinate_system {coordinate_system!r} not in {COORDINATE_SYSTEMS}"
            )
        self._bin_edges_km = bin_edges_km
        self._min_pairs = min_pairs
        self._max_fit_lag_km = max_fit_lag_km
        self._coordinate_system = coordinate_system
        self._coords: np.ndarray | None = None
        self._y: np.ndarray | None = None
        self._fit: FittedVariogram | None = None
        self._alternative: FittedVariogram | None = None
        self._system_matrix: np.ndarray | None = None

    # ------------------------------------------------------------ distances

    def _distances_to_data(self, targets: np.ndarray) -> np.ndarray:
        """(n_targets, n_data) distance matrix in the fitted units."""
        assert self._coords is not None
        if self._coordinate_system == "planar":
            deltas = targets[:, None, :] - self._coords[None, :, :]
            return np.sqrt((deltas**2).sum(axis=2))
        return np.array(
            [
                [
                    haversine_km(t[1], t[0], d[1], d[0])
                    for d in self._coords
                ]
                for t in targets
            ]
        )

    def _pairwise_matrix(self, coords: np.ndarray) -> np.ndarray:
        """(n, n) data-to-data distances in the fitted units. Takes coords
        explicitly (not self._coords) so fit() can build the system before
        committing any state."""
        if self._coordinate_system == "planar":
            deltas = coords[:, None, :] - coords[None, :, :]
            return np.sqrt((deltas**2).sum(axis=2))
        n = coords.shape[0]
        condensed = pairwise_distances_km(coords)
        matrix = np.zeros((n, n))
        i, j = np.triu_indices(n, k=1)
        matrix[i, j] = condensed
        matrix[j, i] = condensed
        return matrix

    # ------------------------------------------------------------------ fit

    def fit(self, features: Any, target: Any) -> None:
        coords = np.asarray(features, dtype=np.float64)
        y = np.asarray(target, dtype=np.float64)
        if coords.ndim != 2 or coords.shape[1] != 2:
            raise ValueError(
                f"OrdinaryKrigingEstimator features must be (n, 2) coordinates "
                f"({self._coordinate_system}), got {coords.shape} — for this "
                "estimator, features ARE coordinates (see module docstring)"
            )
        if y.ndim != 1 or y.shape[0] != coords.shape[0]:
            raise ValueError(f"target shape {y.shape} does not match coords {coords.shape}")
        if not np.isfinite(y).all() or not np.isfinite(coords).all():
            raise ValueError("non-finite coordinate or target — refusing to fit")
        if coords.shape[0] < 3:
            raise ValueError(f"cannot krige {coords.shape[0]} point(s); need >= 3")

        # ATOMIC FIT (E2.2 review must-fix): every piece of state is computed
        # into locals and assigned in ONE block only after every refusal has
        # had its chance. Previously a refused REFIT left the new model +
        # coords + y beside the OLD system matrix — a chimera that predicted
        # silently wrong numbers, and E2.4's runner refits the ONE shared
        # registry instance per fold.
        n = coords.shape[0]
        i, j = np.triu_indices(n, k=1)
        if self._coordinate_system == "planar":
            deltas = coords[:, None, :] - coords[None, :, :]
            pair_d = np.sqrt((deltas**2).sum(axis=2))[i, j]
            # The SAME binning as the geographic path (review: a duplicated
            # inline loop here skipped edge validation and had an untested ½).
            empirical = bin_pairs(pair_d, 0.5 * (y[i] - y[j]) ** 2, self._bin_edges_km)
        else:
            empirical = empirical_variogram(coords, y, self._bin_edges_km)

        fit = fit_variogram(
            empirical,
            family="exponential",
            min_pairs=self._min_pairs,
            max_fit_lag_km=self._max_fit_lag_km,
        )
        alternative = fit_variogram(
            empirical,
            family="spherical",
            min_pairs=self._min_pairs,
            max_fit_lag_km=self._max_fit_lag_km,
        )
        if fit.model.sill == 0.0:
            # Named for what it IS (review: this used to fall through to the
            # singularity check and blame duplicate coordinates — a wrong
            # diagnosis with a remedy that cannot work).
            raise ValueError(
                "fitted variogram is identically zero — the target is constant "
                "(every semivariance 0), so ordinary kriging is undefined; the mean "
                "baseline is the only estimator for this data"
            )

        # The OK system matrix, built once per fit. Duplicate locations make
        # it singular — refuse by name rather than dying in LinAlgError at
        # predict time (real corpus minimum pair distance: 0.054 km).
        pair_matrix = self._pairwise_matrix(coords)
        gamma_matrix = fit.model.gamma(pair_matrix)
        np.fill_diagonal(gamma_matrix, 0.0)
        system = np.zeros((n + 1, n + 1))
        system[:n, :n] = gamma_matrix
        system[n, :n] = 1.0
        system[:n, n] = 1.0
        if np.linalg.matrix_rank(system) < n + 1:
            raise ValueError(
                "ordinary kriging system is singular — duplicate (or numerically "
                "coincident) station coordinates; deduplicate before fitting"
            )

        self._fit = fit
        self._alternative = alternative
        self._coords = coords
        self._y = y
        self._system_matrix = system

    # -------------------------------------------------------------- predict

    def _predict(self, features: Any) -> tuple[np.ndarray, np.ndarray]:
        if self._fit is None or self._coords is None or self._y is None:
            raise ValueError("OrdinaryKrigingEstimator.predict called before fit")
        targets = np.asarray(features, dtype=np.float64)
        if targets.ndim != 2 or targets.shape[1] != 2:
            raise ValueError(
                f"predict features must be (m, 2) coordinates, got {targets.shape}"
            )
        n = self._coords.shape[0]
        gamma0 = self._fit.model.gamma(self._distances_to_data(targets))  # (m, n)
        rhs = np.ones((n + 1, targets.shape[0]))
        rhs[:n, :] = gamma0.T
        solution = np.linalg.solve(self._system_matrix, rhs)  # (n+1, m)
        weights = solution[:n, :]
        lagrange = solution[n, :]
        mean = weights.T @ self._y
        # OK variance = wᵀγ₀ + μ. Float noise at exact data locations is
        # ±1e-15-scale; a GENUINELY negative variance means an invalid model
        # reached the solve (VariogramModel now refuses those at
        # construction, but a tolerance-BOUNDED clamp is the belt to that
        # brace — the review showed an unbounded clamp rendering a real
        # negative variance as sd = 0, false certainty). Noise is clamped;
        # anything below -1e-8·sill is refused by name.
        variance = np.einsum("nm,mn->m", weights, gamma0) + lagrange
        floor = -1e-8 * max(self._fit.model.sill, 1e-300)
        if (variance < floor).any():
            raise ValueError(
                f"ordinary kriging produced a genuinely negative variance "
                f"(min {float(variance.min()):.3e} vs noise floor {floor:.1e}) — the "
                "fitted variogram is not conditionally negative definite; refusing "
                "rather than clamping to a false certainty"
            )
        sd = np.sqrt(np.clip(variance, 0.0, None))
        return mean, sd

    # --------------------------------------------------------------- report

    def provenance(self) -> dict:
        """`report()` as a JSON-able dict (BACKLOG §3 obligations 4 and 5):
        every KrigingReport field, including `range_at_candidate_ceiling`
        beside `range_km`, `range_below_first_supported_lag`, `residual_dof`,
        the fitted bins the fit SAW, every excluded bin WITH its reason, the
        unsupported lag ranges, and the spherical alternative — plus the
        declared semantics and, when the fit found no structure, the
        explicit verdict (NO_STRUCTURE_VERDICT) so a per-fold reader sees
        "reverts to the training mean" and not a bare pair of zeros."""
        report = self.report()
        out = dataclasses.asdict(report)
        # Obligation 5 made unmissable (E2.4 §2 review): the artifact writer
        # serializes with sort_keys=True, which puts the floor twin BETWEEN
        # `range_at_candidate_ceiling` and `range_km`. A reader must not have
        # to reassemble the caveat from neighbouring keys, so the honest
        # sentence is emitted as ONE value as well.
        out["range_km_reported"] = (
            f"{report.range_km:.4g} km"
            + (" — AT THE CANDIDATE CEILING: unconstrained from above, the range exceeds "
               "what the supported lags can resolve" if report.range_at_candidate_ceiling else "")
            + (" — AT OR BELOW THE FIRST SUPPORTED LAG: the nugget/partial-sill split is "
               "unidentifiable" if report.range_below_first_supported_lag else "")
            + (f" (residual dof {report.residual_dof}"
               + ("; 0 = an unfalsifiable near-interpolation" if report.residual_dof == 0 else "")
               + ")")
        )
        out["uncertainty_method"] = self.uncertainty_method
        out["uncertainty_semantics"] = self.uncertainty_semantics
        out["no_structure"] = report.partial_sill == 0.0 and report.range_km == 0.0
        out["verdict"] = NO_STRUCTURE_VERDICT if out["no_structure"] else (
            "structured fit; range_at_candidate_ceiling=%s (True = unconstrained from "
            "above: the range exceeds what the supported lags can resolve)"
            % report.range_at_candidate_ceiling
        )
        return out

    def report(self) -> KrigingReport:
        if self._fit is None or self._alternative is None or self._coords is None:
            raise ValueError("report() called before fit")
        model = self._fit.model
        return KrigingReport(
            used_model_family=model.family,
            nugget=model.nugget,
            partial_sill=model.partial_sill,
            sill=model.sill,
            range_km=model.range_km,
            range_at_candidate_ceiling=self._fit.range_at_candidate_ceiling,
            range_below_first_supported_lag=self._fit.range_below_first_supported_lag,
            used_weighted_sse=self._fit.weighted_sse,
            residual_dof=self._fit.residual_dof,
            alternative=self._alternative,
            fitted_bins=tuple(
                (b.lag_lo_km, b.lag_hi_km, b.pair_count, b.semivariance, b.mean_lag_km)
                for b in self._fit.fitted_bins
            ),
            excluded_bins=tuple(
                ((b.lag_lo_km, b.lag_hi_km, b.pair_count), reason)
                for b, reason in self._fit.excluded_bins
            ),
            unsupported_km=self._fit.unsupported_km,
            min_pairs=self._min_pairs,
            max_fit_lag_km=self._max_fit_lag_km,
            coordinate_system=self._coordinate_system,
            n_training=int(self._coords.shape[0]),
        )
