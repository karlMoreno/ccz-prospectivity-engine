"""CrossValidationRunner — TEMPLATE METHOD over FoldSplitter × EstimatorRegistry
(E2.4 §2; Karl's §1C decision: option (i)).

The fixed sequence, never overridden:

    registry.assert_complete()                         ← baseline REGISTERED
    for each splitter (design):
        assignment = splitter.split(matrix.coords)     ← deterministic, recorded
        assert_spatially_separated(… required_separation_km)   ← the leakage
                                                          assertion, per fold
        claim_eligible = assert_claim_eligible(assignment) did not refuse
        for each fold:
            for (name, estimator) in registry.items():  ← EVERY estimator,
                features = route(estimator, matrix)        never get(): a
                try: estimator.fit(features[train], y[train])   complete registry
                except ValueError: RECORD refusal, RETURN          ⇒ a RUN baseline
                try: estimator.predict(features[test])   ← ONLY the predict call
                except ValueError: RECORD refusal (phase=predict)  is inside this try
                score_predictions(...); estimator.provenance()     ← outside it: a
                                                                     failure here is a
                                                                     bug and propagates
            join every estimator's fold row to the BASELINE's fold row
        pool each estimator's scored folds (+ the baseline on the SAME folds)
    emit_run_manifest(report, matrix, matrix_manifest)  ← the provenance chain

THE EIGHT RUNNER OBLIGATIONS — BACKLOG §3 "E2.4 runner obligations" — are
implemented here, not paraphrased; the section is the specification:
  (1) iterate `registry.items()` — there is no `get()` call in this module;
      `assert_complete()` first, so REGISTERED ⇒ RUN.
  (2) the ONE shared instance is refit per fold; a refused fit is recorded
      per (design, fold, estimator) and `predict` is structurally
      unreachable after it — TWO separate `try` blocks, and the fit
      handler RETURNS, so the predict call below it cannot be reached
      (there is no `else:`; this docstring said there was until the E2.4
      audit, F-2 — the drift entered when the §2 review's predict-time
      refusal split one try/except/else into two blocks). The E2.2
      atomic-fit precedent, made a runner property. LIVE on the real data:
      kriging REFUSES the leave-one-cluster-out fold that trains on W (on a
      never-fitted instance, so nothing stale exists there) and, in
      leave-one-site-out, refuses fold 3 WHILE STILL HOLDING fold 2's
      28-station fit — that is the order that can falsify this, and no
      prediction is served from it.
  (3) the sd=0 policy is the metrics module's (decided at §1D); the runner
      passes every paired sd through unfloored and carries the counts.
  (4)(5)(6) each estimator's `provenance()` is recorded PER FOLD — kriging's
      report (range_at_candidate_ceiling beside range_km, floor twin,
      residual_dof, fitted/excluded bins with reasons, unsupported lags,
      alternative) and RF's `validation_facing_fields()` (never `_forest`).
  (7) `uncertainty_method` (the short key) and `uncertainty_semantics` (the
      sentence) are read from the estimator's DECLARATIONS: the key travels
      beside every sd-shaped number (every CVScore row, every result row),
      the sentence once per estimator in `estimator_declarations` and on
      every result row.
  (8) the theorem is the report's frame (§3); the runner frames nothing —
      it records `purpose` per design so the table can.

INPUT ROUTING IS A DECLARATION (E2.4 §2C): `route()` reads
`estimator.input_kind` — exhaustive dispatch with an explicit raise; no name
is ever matched.

REFUSALS ARE FIRST-CLASS: `status == "refused"` with the estimator's own
message and the PHASE it came from — a `ValueError` from `fit` (kriging's
"only 2 bin(s) survive") or from `predict` (RF's "QRF quantiles crossed",
kriging's "genuinely negative variance"). The baseline and the other
estimators still run on that fold. `ValueError` is this project's refusal
type; any OTHER exception is a BUG and propagates — deliberately, so a
TypeError never masquerades as a scientific refusal.

The pooled comparison for a refusing estimator is computed over ITS scored
folds, and the baseline comparison over the folds where BOTH scored (the
refused folds listed either way) — never over mismatched populations, and
never by aborting the run (E2.4 §2 review).
"""

from __future__ import annotations

import dataclasses
import math
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import numpy as np

from engine.prospectivity.domain.results import CVScore, RunManifest
from engine.prospectivity.provenance.environment import run_environment
from engine.prospectivity.estimators.base import INPUT_KINDS, Estimator
from engine.prospectivity.estimators.registry import (
    MEAN_BASELINE_NAME,
    REQUIRED_ESTIMATORS,
    EstimatorRegistry,
)
from engine.prospectivity.training_matrix import (
    TrainingMatrix,
    TrainingMatrixManifest,
    matrix_sha256,
)
from engine.prospectivity.validation.metrics import (
    METRIC_NAMES,
    SD_ZERO_POLICY,
    ZERO_TOL_REL,
    MetricValue,
    r2_pooled,
    rmse_ratio,
    rmse_uplift,
    score_predictions,
)
from engine.prospectivity.validation.splitter import (
    FoldAssignment,
    FoldSplitter,
    assert_claim_eligible,
    assert_spatially_separated,
    coords_fingerprint,
)

STATUS_SCORED = "scored"
STATUS_REFUSED = "refused"


def route(estimator: Estimator, matrix: TrainingMatrix) -> np.ndarray:
    """The design matrix an estimator consumes — BY ITS DECLARATION.
    Exhaustive over INPUT_KINDS with an explicit raise (house convention);
    a new kind arrives here WITH its estimator, never by name-matching."""
    kind = estimator.input_kind
    if kind == "covariates":
        return matrix.X
    if kind == "coordinates":
        return matrix.coords
    raise ValueError(  # pragma: no cover — the ABC refuses undeclared kinds at definition
        f"{type(estimator).__name__} declares input_kind={kind!r}, not one of {INPUT_KINDS}"
    )


@dataclass(frozen=True)
class FoldEstimatorResult:
    """One (design, fold, estimator): either SCORED (metrics, predictions,
    provenance) or REFUSED (the estimator's own message; no prediction was
    ever requested)."""

    design: str
    fold_name: str
    estimator_name: str
    status: str
    refusal: str | None
    refusal_phase: str | None  # "fit" | "predict" — set when status is refused
    n_train: int
    n_test: int
    min_train_test_km: float
    input_kind: str
    uncertainty_method: str
    uncertainty_semantics: str
    test_indices: tuple[int, ...]
    observed: tuple[float, ...]
    predicted_mean: tuple[float, ...] = ()
    predicted_sd: tuple[float, ...] = ()
    metrics: dict[str, MetricValue] = field(default_factory=dict)
    vs_baseline: dict[str, MetricValue] = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)

    def to_record(self) -> dict:
        return {
            "design": self.design,
            "fold_name": self.fold_name,
            "estimator_name": self.estimator_name,
            "status": self.status,
            "refusal": self.refusal,
            "refusal_phase": self.refusal_phase,
            "n_train": self.n_train,
            "n_test": self.n_test,
            "min_train_test_km": self.min_train_test_km,
            "input_kind": self.input_kind,
            "uncertainty_method": self.uncertainty_method,
            "uncertainty_semantics": self.uncertainty_semantics,
            "test_indices": list(self.test_indices),
            "observed": list(self.observed),
            "predicted_mean": list(self.predicted_mean),
            "predicted_sd": list(self.predicted_sd),
            "metrics": {k: v.to_record() for k, v in self.metrics.items()},
            "vs_baseline": {k: v.to_record() for k, v in self.vs_baseline.items()},
            "provenance": _jsonable(self.provenance),
        }


@dataclass(frozen=True)
class DesignResult:
    name: str
    purpose: str
    spatially_blocked: bool
    claim_eligible: bool
    claim_eligibility_note: str
    required_separation_km: float
    # fold name -> the min train/test separation MEASURED from the
    # coordinates by the leakage assertion (not the splitter's own record).
    measured_separations_km: dict[str, float]
    assignment: FoldAssignment
    results: tuple[FoldEstimatorResult, ...]
    pooled: dict[str, dict[str, Any]]  # estimator -> pooled record

    def to_record(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "spatially_blocked": self.spatially_blocked,
            "claim_eligible": self.claim_eligible,
            "claim_eligibility_note": self.claim_eligibility_note,
            "required_separation_km": self.required_separation_km,
            "measured_min_separation_km": min(self.measured_separations_km.values()),
            "measured_separations_km": dict(self.measured_separations_km),
            "assignment": self.assignment.to_record(),
            "results": [r.to_record() for r in self.results],
            "pooled": _jsonable(self.pooled),
        }


@dataclass(frozen=True)
class CVReport:
    designs: tuple[DesignResult, ...]
    registry_names: tuple[str, ...]
    baseline_name: str
    seed: int
    n_rows: int
    estimator_declarations: dict[str, dict[str, str]]

    def claim_eligible_designs(self) -> list[str]:
        return [d.name for d in self.designs if d.claim_eligible]


def _jsonable(value: Any) -> Any:
    """Native-Python, JSON-serializable view of nested records (MetricValue,
    numpy scalars/arrays, tuples, dataclasses)."""
    if isinstance(value, MetricValue):
        return value.to_record()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_jsonable(v) for v in value.tolist()]
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            # E2.4 §2 review: pydantic renders a non-finite nested in a dict
            # field as `null`, indistinguishable from "not recorded". An
            # estimator reporting inf/NaN is a defect to surface, not to
            # serialize away — the MetricValue posture, one layer out.
            raise ValueError(
                f"a non-finite value ({value!r}) reached run provenance — refusing to "
                "serialize it as a silent null; the estimator that produced it must "
                "report the condition by name"
            )
        return number
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


class CrossValidationRunner:
    """See the module docstring: the Template Method and the obligations."""

    def __init__(
        self,
        *,
        splitters: Sequence[FoldSplitter],
        registry: EstimatorRegistry,
        baseline_name: str = MEAN_BASELINE_NAME,
    ) -> None:
        if not splitters:
            raise ValueError("CrossValidationRunner needs at least one FoldSplitter")
        names = [s.name for s in splitters]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate design names among splitters: {names}")
        if baseline_name not in REQUIRED_ESTIMATORS:
            # E2.4 §2 review: the floor's ROLE is defined by the registry's
            # REQUIRED_ESTIMATORS (CLAUDE.md's mandated baseline), not by a
            # caller-supplied string — otherwise "uplift over baseline"
            # could quietly mean "uplift over the random forest" while
            # obligation 1 stayed formally satisfied.
            raise ValueError(
                f"baseline_name {baseline_name!r} is not in REQUIRED_ESTIMATORS "
                f"{REQUIRED_ESTIMATORS} — the comparison floor is the registry's "
                "mandated baseline, never an arbitrary registered estimator"
            )
        self._splitters = tuple(splitters)
        self._registry = registry
        self._baseline_name = baseline_name

    @property
    def registry(self) -> EstimatorRegistry:
        """The estimators this runner cross-validates — exposed so a caller
        (engine.py) can assert it is the SAME registry it predicts with."""
        return self._registry

    # ------------------------------------------------------------ the template

    def run(self, matrix: TrainingMatrix, *, seed: int) -> CVReport:
        registry = self._registry
        registry.assert_complete()  # (1) baseline REGISTERED — and routing declared
        if self._baseline_name not in registry.names():
            raise ValueError(
                f"baseline {self._baseline_name!r} is not registered ({registry.names()}) — "
                "every fold's comparison needs its floor"
            )
        y = np.asarray(matrix.y, dtype=np.float64)
        declarations = {
            name: {
                "class": type(est).__qualname__,
                "input_kind": est.input_kind,
                "uncertainty_method": est.uncertainty_method,
                "uncertainty_semantics": est.uncertainty_semantics,
            }
            for name, est in registry.items()
        }
        designs = []
        for splitter in self._splitters:
            designs.append(self._run_design(splitter, matrix, y))
        return CVReport(
            designs=tuple(designs),
            registry_names=tuple(registry.names()),
            baseline_name=self._baseline_name,
            seed=int(seed),
            n_rows=int(y.shape[0]),
            estimator_declarations=declarations,
        )

    def _run_design(self, splitter: FoldSplitter, matrix: TrainingMatrix, y: np.ndarray) -> DesignResult:
        assignment = splitter.split(matrix.coords)
        required = float(splitter.required_separation_km)
        if assignment.spatially_blocked and required <= 0.0:
            # E2.4 §2 review: the two declarations must not contradict each
            # other. "My folds are spatially blocked" and "I guarantee no
            # separation" cannot both be true, and it is the FIRST that makes
            # a design claim-eligible.
            raise ValueError(
                f"design {splitter.name!r} declares spatially_blocked=True but "
                f"required_separation_km={required} — a blocked design must guarantee a "
                "positive train/test separation, or declare itself unblocked"
            )
        # Original requirement 4 — the spatial-leakage assertion, per fold,
        # at the buffer the DESIGN states (0.0 = disjointness only, stated).
        # The MEASUREMENTS come back so the manifest records what was
        # measured, not what the splitter claimed.
        measured_separations = assert_spatially_separated(
            assignment, matrix.coords, min_separation_km=required
        )
        try:
            assert_claim_eligible(assignment)
            claim_eligible, note = True, "spatially blocked: may back a claim (E2.5 decides)"
        except ValueError as refusal:
            claim_eligible, note = False, str(refusal)

        results: list[FoldEstimatorResult] = []
        for fold in assignment.folds:
            train = np.asarray(fold.train_indices, dtype=int)
            test = np.asarray(fold.test_indices, dtype=int)
            fold_rows: dict[str, FoldEstimatorResult] = {}
            for name, estimator in self._registry.items():  # (1): never get()
                fold_rows[name] = self._fit_score(
                    splitter.name, fold.name, fold.min_train_test_km, name, estimator,
                    matrix, y, train, test,
                )
            # Join every estimator to the BASELINE for the SAME fold (req. 1).
            if self._baseline_name not in fold_rows:  # structurally impossible via items(); named anyway
                raise ValueError(
                    f"the baseline {self._baseline_name!r} did not run on fold {fold.name!r} of "
                    f"{splitter.name!r} — no model row can be compared without its floor"
                )
            baseline_row = fold_rows[self._baseline_name]
            for name, row in fold_rows.items():
                results.append(self._with_baseline(row, baseline_row))

        pooled = self._pool(splitter.name, results)
        return DesignResult(
            name=splitter.name,
            purpose=splitter.purpose,
            spatially_blocked=assignment.spatially_blocked,
            claim_eligible=claim_eligible,
            claim_eligibility_note=note,
            required_separation_km=required,
            measured_separations_km=dict(measured_separations),
            assignment=assignment,
            results=tuple(results),
            pooled=pooled,
        )

    def _fit_score(
        self,
        design: str,
        fold_name: str,
        min_sep: float,
        name: str,
        estimator: Estimator,
        matrix: TrainingMatrix,
        y: np.ndarray,
        train: np.ndarray,
        test: np.ndarray,
    ) -> FoldEstimatorResult:
        features = route(estimator, matrix)  # (2C) by declaration
        base = dict(
            design=design,
            fold_name=fold_name,
            estimator_name=name,
            n_train=int(train.size),
            n_test=int(test.size),
            min_train_test_km=float(min_sep),
            input_kind=estimator.input_kind,
            uncertainty_method=estimator.uncertainty_method,
            uncertainty_semantics=estimator.uncertainty_semantics,
            test_indices=tuple(int(i) for i in test),
            observed=tuple(float(v) for v in y[test]),
        )
        try:
            estimator.fit(features[train], y[train])  # (2): refit per fold, shared instance
        except ValueError as refusal:
            # RECORDED, and predict is unreachable from here: a refused refit
            # leaves the instance holding the PREVIOUS fold's state (atomic
            # fit), and nothing below runs.
            return FoldEstimatorResult(
                status=STATUS_REFUSED, refusal=str(refusal), refusal_phase="fit", **base
            )
        try:
            mean, sd = estimator.predict(features[test])  # the ABC's pairing template
        except ValueError as refusal:
            # A refusal at PREDICT time is equally first-class (E2.4 §2
            # review): RF's crossed-quantile refusal and kriging's
            # negative-variance refusal are scientific verdicts about THIS
            # fold, not reasons to lose every other design's results.
            return FoldEstimatorResult(
                status=STATUS_REFUSED, refusal=str(refusal), refusal_phase="predict", **base
            )
        mean = np.asarray(mean, dtype=np.float64).reshape(-1)
        sd = np.asarray(sd, dtype=np.float64).reshape(-1)
        metrics = score_predictions(y[test], mean, sd)  # (3): sd passed through unfloored
        return FoldEstimatorResult(
            status=STATUS_SCORED,
            refusal=None,
            refusal_phase=None,
            predicted_mean=tuple(float(v) for v in mean),
            predicted_sd=tuple(float(v) for v in sd),
            metrics=metrics,
            provenance=_jsonable(estimator.provenance()),  # (4)(5)(6)
            **base,
        )

    @staticmethod
    def _with_baseline(row: FoldEstimatorResult, baseline: FoldEstimatorResult) -> FoldEstimatorResult:
        if row.estimator_name == baseline.estimator_name:
            return row  # the floor is not compared to itself
        if row.status != STATUS_SCORED or baseline.status != STATUS_SCORED:
            return row
        vs = {
            "rmse_uplift": rmse_uplift(row.metrics["rmse"], baseline.metrics["rmse"]),
            "rmse_ratio": rmse_ratio(row.metrics["rmse"], baseline.metrics["rmse"]),
        }
        return dataclasses.replace(row, vs_baseline=vs)

    def _pool(self, design: str, results: Sequence[FoldEstimatorResult]) -> dict[str, dict[str, Any]]:
        """Per estimator: every per-fold metric recomputed over the
        CONCATENATED held-out predictions of its SCORED folds, plus
        r2_pooled (never per fold), plus the baseline pooled over the SAME
        folds so a refusing estimator is compared on its own population."""
        by_est: dict[str, list[FoldEstimatorResult]] = {}
        for r in results:
            by_est.setdefault(r.estimator_name, []).append(r)
        baseline_rows = {r.fold_name: r for r in by_est.get(self._baseline_name, [])}
        pooled: dict[str, dict[str, Any]] = {}
        for name, rows in by_est.items():
            scored = [r for r in rows if r.status == STATUS_SCORED]
            refused = [r for r in rows if r.status == STATUS_REFUSED]
            record: dict[str, Any] = {
                "n_folds": len(rows),
                "n_folds_scored": len(scored),
                "n_folds_refused": len(refused),
                "folds_refused": [r.fold_name for r in refused],
                "refusals": {r.fold_name: r.refusal for r in refused},
                "uncertainty_method": rows[0].uncertainty_method,
                "uncertainty_semantics": rows[0].uncertainty_semantics,
            }
            if not scored:
                record["metrics"] = {}
                record["note"] = "refused on every fold — nothing to pool"
                pooled[name] = record
                continue
            obs = np.concatenate([np.asarray(r.observed) for r in scored])
            mean = np.concatenate([np.asarray(r.predicted_mean) for r in scored])
            sd = np.concatenate([np.asarray(r.predicted_sd) for r in scored])
            metrics = score_predictions(obs, mean, sd)
            metrics["r2_pooled"] = r2_pooled(obs, mean)
            record["n_pooled"] = int(obs.size)
            record["metrics"] = metrics
            # The baseline on the folds where BOTH scored — the only
            # comparable population (E2.4 §2 review: restricting only the
            # baseline side produced mismatched n and ABORTED the whole run
            # when the baseline refused a fold this estimator scored).
            if name != self._baseline_name:
                shared = [
                    r for r in scored
                    if baseline_rows.get(r.fold_name) is not None
                    and baseline_rows[r.fold_name].status == STATUS_SCORED
                ]
                dropped = [r.fold_name for r in scored if r not in shared]
                if not shared:
                    record["vs_baseline_note"] = (
                        "no fold was scored by both this estimator and the baseline — "
                        "no comparable population exists for an uplift"
                    )
                else:
                    same = [baseline_rows[r.fold_name] for r in shared]
                    e_obs = np.concatenate([np.asarray(r.observed) for r in shared])
                    e_mean = np.concatenate([np.asarray(r.predicted_mean) for r in shared])
                    e_sd = np.concatenate([np.asarray(r.predicted_sd) for r in shared])
                    e_metrics = score_predictions(e_obs, e_mean, e_sd)
                    b_obs = np.concatenate([np.asarray(r.observed) for r in same])
                    b_mean = np.concatenate([np.asarray(r.predicted_mean) for r in same])
                    b_sd = np.concatenate([np.asarray(r.predicted_sd) for r in same])
                    b_metrics = score_predictions(b_obs, b_mean, b_sd)
                    b_metrics["r2_pooled"] = r2_pooled(b_obs, b_mean)
                    record["baseline_on_same_folds"] = b_metrics
                    # Obligation 7: these are the BASELINE's sd-derived
                    # numbers, so they carry the BASELINE's semantics, not
                    # the estimator's, even nested inside its record.
                    record["baseline_uncertainty_method"] = same[0].uncertainty_method
                    record["baseline_uncertainty_semantics"] = same[0].uncertainty_semantics
                    record["n_pooled_vs_baseline"] = int(e_obs.size)
                    record["folds_excluded_from_comparison"] = dropped
                    record["vs_baseline"] = {
                        "rmse_uplift": rmse_uplift(e_metrics["rmse"], b_metrics["rmse"]),
                        "rmse_ratio": rmse_ratio(e_metrics["rmse"], b_metrics["rmse"]),
                    }
            pooled[name] = record
        return pooled


# ------------------------------------------------------------------ emitter


def flat_scores(report: CVReport) -> list[CVScore]:
    """The flat (design, fold, estimator, metric) table — every row beside the
    baseline's value for the same design/fold/metric, with the estimator's
    declared `uncertainty_method` key (obligation 7; the sentence it names is
    in `estimator_declarations`). Refused rows appear ONCE
    per metric with status naming the refusal, never silently absent."""
    rows: list[CVScore] = []
    for design in report.designs:
        baseline = {
            r.fold_name: r for r in design.results if r.estimator_name == report.baseline_name
        }
        for r in design.results:
            b = baseline.get(r.fold_name)
            metric_names = list(METRIC_NAMES) + (list(r.vs_baseline) if r.vs_baseline else [])
            for metric in metric_names:
                n_sd_zero = n_sd_zero_wrong = None
                if r.status == STATUS_REFUSED:
                    value, status = None, f"refused at {r.refusal_phase}: {r.refusal}"
                else:
                    mv = r.metrics.get(metric) or r.vs_baseline.get(metric)
                    value, status = mv.value, mv.status
                    details = mv.details or {}
                    n_sd_zero = details.get("n_sd_zero")
                    n_sd_zero_wrong = details.get("n_sd_zero_wrong")
                if b is None or b.status == STATUS_REFUSED or metric not in b.metrics:
                    b_value = None
                    b_status = (
                        "baseline refused" if b is not None and b.status == STATUS_REFUSED
                        else "not a baseline metric" if metric in ("rmse_uplift", "rmse_ratio")
                        else "baseline row missing"
                    )
                else:
                    b_value, b_status = b.metrics[metric].value, b.metrics[metric].status
                rows.append(
                    CVScore(
                        estimator_name=r.estimator_name,
                        cv_strategy=design.name,
                        fold_name=r.fold_name,
                        metric_name=metric,
                        metric_value=value,
                        metric_status=status,
                        baseline_metric_value=b_value,
                        baseline_metric_status=b_status,
                        uncertainty_method=r.uncertainty_method,
                        n_test=r.n_test,
                        n_sd_zero=n_sd_zero,
                        n_sd_zero_wrong=n_sd_zero_wrong,
                    )
                )
    return rows


def emit_run_manifest(
    report: CVReport,
    *,
    matrix: TrainingMatrix,
    matrix_manifest: TrainingMatrixManifest,
    run_id: str | None = None,
    scores_first_visible: datetime | None = None,
    generator: str = "engine.prospectivity.validation.runner.emit_run_manifest",
) -> RunManifest:
    """Assemble the RunManifest (E2.4 §2D). THE CHAIN IS ASSERTED, NOT COPIED:
    the training-matrix hash written into `upstream_hashes` must equal BOTH
    the manifest's recorded `matrix_sha256` AND the hash re-derived from the
    arrays actually handed in — a manifest that does not describe this
    matrix is refused by name. The corpus and feature-stack hashes are
    quoted from the matrix manifest's own upstream record, so one lookup
    reaches all three (E2.5 condition 5). `data_origin` is the matrix's
    COMPUTED origin (never declared here); the watermark derives from it."""
    if matrix_manifest.content_hash is None:
        raise ValueError("training-matrix manifest is not finalized (content_hash is None)")
    # The manifest's own identity must still describe its own contents: it is
    # a MUTABLE pydantic model, so a field edited after finalize() (a
    # data_origin quietly promoted to MEASURED, say) would otherwise be
    # quoted here as fact (E2.4 §2 review).
    if matrix_manifest.compute_content_hash() != matrix_manifest.content_hash:
        raise ValueError(
            "the training-matrix manifest's content_hash does not match its own contents — "
            "it was mutated after finalize(); refusing to quote a record that does not "
            "describe itself"
        )
    recomputed = matrix_sha256(matrix)
    if recomputed != matrix_manifest.matrix_sha256:
        raise ValueError(
            f"the training matrix handed to the run ({recomputed}) is not the one its "
            f"manifest describes ({matrix_manifest.matrix_sha256}) — refusing to chain a "
            "run manifest to a matrix artifact that does not describe its inputs"
        )
    if matrix.coords.shape[0] != report.n_rows:
        raise ValueError(
            f"CV report covers {report.n_rows} rows but the matrix has {matrix.coords.shape[0]}"
        )
    # …and the report must have been COMPUTED on these coordinates, in this
    # row order: every fold assignment carries the fingerprint of what it was
    # split from, so a report computed on another matrix of the same size
    # cannot be chained to this artifact (E2.4 §2 review).
    fingerprint = coords_fingerprint(matrix.coords)
    for design in report.designs:
        recorded = design.assignment.coords_sha256
        if recorded is not None and recorded != fingerprint:
            raise ValueError(
                f"design {design.name!r} was split from coordinates {recorded} but the "
                f"matrix handed to the emitter fingerprints as {fingerprint} — this CV "
                "report was not computed on this matrix"
            )
    upstream = dict(matrix_manifest.upstream_hashes)
    missing = [k for k in ("corpus", "feature_stack") if not upstream.get(k)]
    if missing:
        raise ValueError(
            f"training-matrix manifest lacks upstream hash(es) {missing} — the run cannot "
            "chain to the corpus and feature stack"
        )
    manifest = RunManifest(
        run_id=run_id or str(uuid.uuid4()),
        seed=report.seed,
        inputs={
            "training_matrix": {
                "matrix_sha256": matrix_manifest.matrix_sha256,
                "n_stations": matrix_manifest.n_stations,
                "n_covariates": matrix_manifest.n_covariates,
                "covariate_names": list(matrix_manifest.covariate_names),
                "coord_columns": list(matrix_manifest.coord_columns),
                "target_definition": dict(matrix_manifest.target_definition),
                "sampling_method": matrix_manifest.sampling_method,
                "shared_cell_count": matrix_manifest.shared_cell_count,
                "distinct_cell_count": matrix_manifest.distinct_cell_count,
                "cell_groups": [list(g) for g in matrix_manifest.cell_groups],
            },
            "registry": list(report.registry_names),
            "baseline": report.baseline_name,
            "designs": [d.name for d in report.designs],
            "metric_names": list(METRIC_NAMES) + ["r2_pooled (pooled only)", "rmse_uplift", "rmse_ratio"],
            "sd_zero_policy": SD_ZERO_POLICY,
            "zero_tolerance_rel": ZERO_TOL_REL,
            # E3.4 commit 3 (BACKLOG §3, trigger fired): the software
            # environment is an INPUT and sits inside the substance hash.
            "environment": run_environment(),
        },
        cv_scores=flat_scores(report),
        scores_first_visible=scores_first_visible or datetime.now(UTC),
        data_origin=matrix_manifest.data_origin,
        generator=generator,
        derivation=(
            "CrossValidationRunner.run() over the training matrix named in inputs, then "
            "emit_run_manifest(); every score is score_predictions() on one fold's held-out "
            "rows (engine/prospectivity/validation/metrics.py), and data_origin is the "
            "matrix manifest's COMPUTED origin, not a declaration"
        ),
        estimator_declarations={k: dict(v) for k, v in report.estimator_declarations.items()},
        cross_validation={
            "designs": [d.to_record() for d in report.designs],
            "n_rows": report.n_rows,
        },
        claim_eligible_designs=report.claim_eligible_designs(),
        contract_versions=dict(matrix_manifest.contract_versions),
        upstream_hashes={
            "training_matrix": matrix_manifest.content_hash,
            "corpus": upstream["corpus"],
            "feature_stack": upstream["feature_stack"],
        },
    )
    manifest.finalize()
    return manifest


def run_watermark(manifest: RunManifest) -> str | None:
    """The run's watermark DERIVES from its computed origin at render time —
    the training matrix's rule, reused (P2.0d-3 posture: default-ON; absence
    of a clean origin watermarks)."""
    from engine.prospectivity.training_matrix import matrix_watermark

    return matrix_watermark(manifest.data_origin)
