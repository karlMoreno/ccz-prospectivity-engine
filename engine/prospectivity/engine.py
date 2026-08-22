"""ProspectivityEngine — TEMPLATE METHOD.

The whole-run fixed sequence (alpha proposal §5/§10):

    ingest -> features -> CV -> predict -> uncertainty -> economics
        -> compare_to_ts6 -> manifest

Same composition-based Template Method style as IngestionPipeline: `run()`
never changes, but every step delegates to an injected Strategy
(TerrainSource, SampleSource, the Estimators in an EstimatorRegistry,
EconomicModel, TS6Reference), a Template Method of its own (the
CrossValidationRunner), or a plain callable (`feature_builder`; the manifest
emitter). Phase 0 wired the sequence and the seams; Phases 1–2 supplied real
strategies for ingestion, features, estimators and CV; Phases 3–4 supply
prediction surfaces, TS-6 comparison and economics.

E2.4 §2B REVISION (the Phase-0 revision protocol; Karl's §1C decision,
option (i)). BEFORE: the engine held ONE `estimator: Estimator` and a
`cross_validator: Callable[[features, target, Estimator], list[CVScore]]`
— one estimator, no coordinates, no fold record — so the CLAUDE.md rule
"always run the mean baseline alongside" lived in whichever caller
remembered it. AFTER: the engine holds an `EstimatorRegistry` (the baseline
is REQUIRED there — E2.1) and a `CrossValidationRunner` that iterates the
WHOLE registry per fold (never cherry-picks), routes each estimator's
design matrix by its declared `input_kind` (never by name — §2C), records
refusals per (design, fold, estimator), and emits the RunManifest with the
provenance chain asserted (§2D). `CrossValidator` is RETIRED; the
feature-building seam now yields the TrainingMatrix AND its manifest (the
E2.0 `assemble_training_matrix` shape), because the run manifest must chain
to the matrix artifact by hash, not by assumption.

    ┌───────────────────────────────────────────────────────────────────────┐
    │                        ProspectivityEngine.run()                         │
    │                                                                          │
    │  ingest ─► features ─► CV ─► fit+predict ─► compare_ts6 ─► economics ─► │
    │    │          │         │        (every estimator,   │          │         │
    │    ▼          ▼         ▼         routed by decl.)   ▼          ▼         │
    │ terrain_   feature_   cv_runner  registry.items()  ts6_ref +  economic_  │
    │ source +   builder    .run()     .fit/.predict()   compare_   model      │
    │ sample_    → (matrix,  → CVReport (paired)           to_ts6()  .apply()×N │
    │ source       manifest)                                          │         │
    │                                                                 ▼         │
    │                                  manifest_emitter(report, matrix, …)      │
    │                                   → RunManifest (+ ts6, economics)        │
    └───────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.results import (
    EconomicScenarioResult,
    RunManifest,
    TS6Agreement,
)
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.economics.model import EconomicModel
from engine.prospectivity.estimators.registry import EstimatorRegistry
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.training_matrix import TrainingMatrix, TrainingMatrixManifest
from engine.prospectivity.ts6.reference import TS6Reference, compare_to_ts6
from engine.prospectivity.validation.runner import (
    CrossValidationRunner,
    CVReport,
    emit_run_manifest,
    route,
)

FeatureBuilder = Callable[
    [TerrainLayer, list[Observation]], tuple[TrainingMatrix, TrainingMatrixManifest]
]
ManifestEmitter = Callable[..., RunManifest]  # emit_run_manifest's signature


class ProspectivityEngine:
    """Orchestrates one prospectivity run over injected Strategy collaborators."""

    def __init__(
        self,
        study_area: StudyArea,
        terrain_source: TerrainSource,
        sample_source: SampleSource,
        feature_builder: FeatureBuilder,
        cv_runner: CrossValidationRunner,
        estimators: EstimatorRegistry,
        ts6_reference: TS6Reference,
        economic_model: EconomicModel,
        scenario_configs: list[dict[str, Any]],
        seed: int = 0,
        # E3.4 (2B): the comparison returns a MAPPING, one agreement per
        # estimator — the manifest's ts6_agreement arity, Karl's decision.
        compare_to_ts6_fn: Callable[[Any, Any], dict[str, TS6Agreement]] = compare_to_ts6,
        manifest_emitter: ManifestEmitter = emit_run_manifest,
    ) -> None:
        runner_registry = getattr(cv_runner, "registry", None)
        if runner_registry is not None and runner_registry is not estimators:
            # E2.4 §2 review: otherwise an estimator could produce a
            # prediction surface, a TS-6 comparison and an economic scenario
            # without ever having been cross-validated — the separation
            # CLAUDE.md's "spatial CV is mandatory for any model claim"
            # exists to prevent.
            raise ValueError(
                "the CV runner cross-validates a DIFFERENT registry than the engine "
                "predicts with — every estimator that reaches a prediction must be the "
                "one that was cross-validated"
            )
        self._study_area = study_area
        self._terrain_source = terrain_source
        self._sample_source = sample_source
        self._feature_builder = feature_builder
        self._cv_runner = cv_runner
        self._estimators = estimators
        self._ts6_reference = ts6_reference
        self._economic_model = economic_model
        self._scenario_configs = scenario_configs
        self._seed = seed
        self._compare_to_ts6_fn = compare_to_ts6_fn
        self._manifest_emitter = manifest_emitter

    def run(self) -> RunManifest:
        terrain, samples = self._ingest()
        matrix, matrix_manifest = self._build_features(terrain, samples)
        cv_report = self._cross_validate(matrix)
        predictions = self._fit_predict(matrix)
        ts6_agreement = self._compare_to_ts6(predictions)
        economic_results = self._apply_economics(predictions)
        return self._emit_manifest(cv_report, matrix, matrix_manifest, ts6_agreement, economic_results)

    def _ingest(self) -> tuple[TerrainLayer, list[Observation]]:
        terrain = self._terrain_source.load(self._study_area)
        samples = self._sample_source.get_training_samples()
        return terrain, samples

    def _build_features(
        self, terrain: TerrainLayer, samples: list[Observation]
    ) -> tuple[TrainingMatrix, TrainingMatrixManifest]:
        return self._feature_builder(terrain, samples)

    def _cross_validate(self, matrix: TrainingMatrix) -> CVReport:
        return self._cv_runner.run(matrix, seed=self._seed)

    def _fit_predict(self, matrix: TrainingMatrix) -> dict[str, tuple[Any, Any]]:
        """Every registered estimator, routed by its declaration, fitted on
        the full matrix; the paired (mean, std) per estimator. Iterates
        `items()` — the same never-cherry-pick discipline as the runner."""
        self._estimators.assert_complete()
        predictions: dict[str, tuple[Any, Any]] = {}
        for name, estimator in self._estimators.items():
            features = route(estimator, matrix)
            estimator.fit(features, matrix.y)
            predictions[name] = estimator.predict(features)
        return predictions

    def _compare_to_ts6(self, predictions: dict[str, tuple[Any, Any]]) -> dict[str, TS6Agreement]:
        ts6_surface = self._ts6_reference.load()
        return self._compare_to_ts6_fn(predictions, ts6_surface)

    def _apply_economics(self, predictions: dict[str, tuple[Any, Any]]) -> list[EconomicScenarioResult]:
        return [
            self._economic_model.apply(predictions, scenario_config)
            for scenario_config in self._scenario_configs
        ]

    def _emit_manifest(
        self,
        cv_report: CVReport,
        matrix: TrainingMatrix,
        matrix_manifest: TrainingMatrixManifest,
        ts6_agreement: dict[str, TS6Agreement],
        economic_results: list[EconomicScenarioResult],
    ) -> RunManifest:
        manifest = self._manifest_emitter(cv_report, matrix=matrix, matrix_manifest=matrix_manifest)
        return manifest.model_copy(
            update={"ts6_agreement": ts6_agreement, "economic_results": economic_results}
        ).finalize()
