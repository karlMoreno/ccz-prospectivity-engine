"""ProspectivityEngine.run() (TEMPLATE METHOD) calls its fixed sequence in
order, regardless of what the injected strategies do. Phase 0 has no real
Estimator/EconomicModel yet, so this proves the *sequence*, not the science —
that's Phase 2-4.
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.results import CVScore, EconomicScenarioResult, TS6Agreement
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.economics.model import EconomicModel
from engine.prospectivity.engine import ProspectivityEngine
from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.ts6.reference import TS6Reference


def _study_area() -> StudyArea:
    return StudyArea(
        area_id="test_area",
        name="Test AOI",
        geometry={
            "type": "Polygon",
            "coordinates": [[[-127, 11], [-125, 11], [-125, 13], [-127, 13], [-127, 11]]],
        },
    )


def test_run_calls_steps_in_the_documented_order() -> None:
    call_order: list[str] = []

    class StubTerrainSource(TerrainSource):
        def load(self, study_area: StudyArea) -> TerrainLayer:
            call_order.append("ingest:terrain")
            return TerrainLayer(name="bathymetry")

    class StubSampleSource(SampleSource):
        def load_observations(self) -> list[Observation]:
            call_order.append("ingest:samples")
            return [
                Observation(
                    source_record_id="STUB001",
                    source_id="src_synthetic_boxcore",
                    evidence_class=EvidenceClass.MASS,
                    longitude=-126.0,
                    latitude=12.0,
                    abundance_kg_m2=5.0,
                    observation_or_prediction=ObservationOrPrediction.OBSERVED,
                    is_open=True,
                    qa_status="pending",
                )
            ]

    def stub_feature_builder(terrain, samples):
        call_order.append("features")
        return "features", "target"

    def stub_cross_validator(features, target, estimator):
        call_order.append("cv")
        return [
            CVScore(
                estimator_name="stub",
                cv_strategy="spatial_blocked",
                metric_name="rmse",
                metric_value=1.0,
            )
        ]

    class StubEstimator(Estimator):
        def fit(self, features, target) -> None:
            call_order.append("fit")

        def _predict(self, features):
            # E2.1: predict() became the ABC's Template Method (pairing
            # validation); stubs implement the hook, same as before the
            # revision but under the hook's name.
            call_order.append("predict")
            return "mean", "std"

    class StubTS6Reference(TS6Reference):
        def load(self) -> TS6Surface:
            call_order.append("ts6:load")
            return TS6Surface(title="stub", source_id="src_ts6_grid", raster_path="stub.tif")

    def stub_compare_to_ts6(prediction, ts6_surface) -> TS6Agreement:
        call_order.append("ts6:compare")
        return TS6Agreement(spatial_correlation=0.5)

    class StubEconomicModel(EconomicModel):
        def apply(self, prediction, scenario_config) -> EconomicScenarioResult:
            call_order.append(f"economics:{scenario_config['scenario_name']}")
            return EconomicScenarioResult(
                scenario_name=scenario_config["scenario_name"], illustrative_only=True
            )

    engine = ProspectivityEngine(
        study_area=_study_area(),
        terrain_source=StubTerrainSource(),
        sample_source=StubSampleSource(),
        feature_builder=stub_feature_builder,
        cross_validator=stub_cross_validator,
        estimator=StubEstimator(),
        ts6_reference=StubTS6Reference(),
        economic_model=StubEconomicModel(),
        scenario_configs=[
            {"scenario_name": "MARKET_STANDARD"},
            {"scenario_name": "STRATEGIC_SUBSIDIZED"},
        ],
        seed=42,
        compare_to_ts6_fn=stub_compare_to_ts6,
    )

    manifest = engine.run()

    assert call_order == [
        "ingest:terrain",
        "ingest:samples",
        "features",
        "cv",
        "fit",
        "predict",
        "ts6:load",
        "ts6:compare",
        "economics:MARKET_STANDARD",
        "economics:STRATEGIC_SUBSIDIZED",
    ]
    assert manifest.seed == 42
    assert manifest.ts6_agreement is not None
    assert manifest.ts6_agreement.spatial_correlation == 0.5
    assert len(manifest.economic_results) == 2
