"""ProspectivityEngine — TEMPLATE METHOD.

The whole-run fixed sequence (alpha proposal §5/§10):

    ingest -> features -> CV -> predict -> uncertainty -> economics
        -> compare_to_ts6 -> manifest

Same composition-based Template Method style as IngestionPipeline: `run()`
never changes, but every step delegates to an injected Strategy
(TerrainSource, SampleSource, Estimator, EconomicModel, TS6Reference) or a
plain callable (`feature_builder`, since covariates.yaml already makes
feature recipes data-driven rather than a class hierarchy — see features/).
Phase 0 wires the sequence and the seams; Phase 1-4 supply real strategies.
Until then, running this with real (non-stub) strategies simply surfaces
each strategy's own NotImplementedError — the sequence itself is what Phase 0
proves correct (see tests/test_engine_template_method.py).

    ┌────────────────────────────────────────────────────────────────────┐
    │                       ProspectivityEngine.run()                       │
    │                                                                        │
    │  ingest ─► features ─► CV ─► fit+predict ─► uncertainty ─► compare_ts6 │
    │    │          │         │         │              │             │      │
    │    ▼          ▼         ▼         ▼              ▼             ▼      │
    │ terrain_    feature_  estimator estimator    estimator    ts6_ref +   │
    │ source +    builder   .fit/                  .predict()   compare_to_ │
    │ sample_               predict()               (paired)    ts6()       │
    │ source                                                                 │
    │                                                        └──► economics │
    │                                                                │       │
    │                                                                ▼       │
    │                                                        economic_model  │
    │                                                        .apply() x N    │
    │                                                                │       │
    │                                                                ▼       │
    │                                                        manifest (assembled, not a Strategy) │
    └────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.results import (
    CVScore,
    EconomicScenarioResult,
    RunManifest,
    TS6Agreement,
)
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.economics.model import EconomicModel
from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.ts6.reference import TS6Reference, compare_to_ts6

FeatureBuilder = Callable[[TerrainLayer, list[Observation]], tuple[Any, Any]]
CrossValidator = Callable[[Any, Any, Estimator], list[CVScore]]


class ProspectivityEngine:
    """Orchestrates one prospectivity run over injected Strategy collaborators."""

    def __init__(
        self,
        study_area: StudyArea,
        terrain_source: TerrainSource,
        sample_source: SampleSource,
        feature_builder: FeatureBuilder,
        cross_validator: CrossValidator,
        estimator: Estimator,
        ts6_reference: TS6Reference,
        economic_model: EconomicModel,
        scenario_configs: list[dict[str, Any]],
        seed: int = 0,
        compare_to_ts6_fn: Callable[[Any, Any], TS6Agreement] = compare_to_ts6,
    ) -> None:
        self._study_area = study_area
        self._terrain_source = terrain_source
        self._sample_source = sample_source
        self._feature_builder = feature_builder
        self._cross_validator = cross_validator
        self._estimator = estimator
        self._ts6_reference = ts6_reference
        self._economic_model = economic_model
        self._scenario_configs = scenario_configs
        self._seed = seed
        self._compare_to_ts6_fn = compare_to_ts6_fn

    def run(self) -> RunManifest:
        terrain, samples = self._ingest()
        features, target = self._build_features(terrain, samples)
        cv_scores = self._cross_validate(features, target)
        prediction, uncertainty = self._fit_predict(features, target)
        ts6_agreement = self._compare_to_ts6(prediction)
        economic_results = self._apply_economics(prediction)
        return self._emit_manifest(cv_scores, ts6_agreement, economic_results)

    def _ingest(self) -> tuple[TerrainLayer, list[Observation]]:
        terrain = self._terrain_source.load(self._study_area)
        samples = self._sample_source.get_training_samples()
        return terrain, samples

    def _build_features(
        self, terrain: TerrainLayer, samples: list[Observation]
    ) -> tuple[Any, Any]:
        return self._feature_builder(terrain, samples)

    def _cross_validate(self, features: Any, target: Any) -> list[CVScore]:
        return self._cross_validator(features, target, self._estimator)

    def _fit_predict(self, features: Any, target: Any) -> tuple[Any, Any]:
        self._estimator.fit(features, target)
        mean, std = self._estimator.predict(features)
        return mean, std

    def _compare_to_ts6(self, prediction: Any) -> TS6Agreement:
        ts6_surface = self._ts6_reference.load()
        return self._compare_to_ts6_fn(prediction, ts6_surface)

    def _apply_economics(self, prediction: Any) -> list[EconomicScenarioResult]:
        return [
            self._economic_model.apply(prediction, scenario_config)
            for scenario_config in self._scenario_configs
        ]

    def _emit_manifest(
        self,
        cv_scores: list[CVScore],
        ts6_agreement: TS6Agreement,
        economic_results: list[EconomicScenarioResult],
    ) -> RunManifest:
        return RunManifest(
            run_id=str(uuid.uuid4()),
            generated_at=datetime.now(UTC),
            seed=self._seed,
            cv_scores=cv_scores,
            ts6_agreement=ts6_agreement,
            economic_results=economic_results,
        )
