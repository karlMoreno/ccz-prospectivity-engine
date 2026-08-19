"""ProspectivityEngine.run() (TEMPLATE METHOD) calls its fixed sequence in
order, regardless of what the injected strategies do. Phase 0 proved the
*sequence*; E2.4 §2B revised the seams (a registry + a CV runner instead of
one estimator + a callable), so the stubs here now stand in for a
CrossValidationRunner, an EstimatorRegistry, and the manifest emitter — the
assertion is still the ORDER, not the science (that is E2.4's own tests).
"""

from __future__ import annotations

import numpy as np

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.results import EconomicScenarioResult, RunManifest, TS6Agreement
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.economics.model import EconomicModel
from engine.prospectivity.engine import ProspectivityEngine
from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME, EstimatorRegistry
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.training_matrix import TrainingMatrix, TrainingMatrixManifest
from engine.prospectivity.ts6.reference import TS6Reference
from engine.prospectivity.validation.runner import CVReport


def _study_area() -> StudyArea:
    return StudyArea(
        area_id="test_area",
        name="Test AOI",
        geometry={
            "type": "Polygon",
            "coordinates": [[[-127, 11], [-125, 11], [-125, 13], [-127, 13], [-127, 11]]],
        },
    )


def _tiny_matrix() -> tuple[TrainingMatrix, TrainingMatrixManifest]:
    X = np.zeros((3, 1)); y = np.array([1.0, 2.0, 3.0]); coords = np.array([[-126.0, 12.0], [-126.1, 12.0], [-126.2, 12.0]])
    for a in (X, y, coords):
        a.flags.writeable = False
    matrix = TrainingMatrix(("a", "b", "c"), ("x0",), X, y, coords)
    manifest = TrainingMatrixManifest(
        target_definition={"value": "total_as_published", "data_origin": "AUTHORED", "author": "model"},
        sampling_method="stub", shared_cell_count=0, distinct_cell_count=3, cell_groups=[],
        n_stations=3, n_covariates=1, covariate_names=["x0"], coord_columns=["longitude", "latitude"],
        matrix_sha256="sha256:stub", data_origin="SYNTHETIC",
        upstream_hashes={"corpus": "sha256:c", "feature_stack": "sha256:f"},
    ).finalize()
    return matrix, manifest


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
        return _tiny_matrix()

    class StubRunner:
        def run(self, matrix, *, seed):
            call_order.append("cv")
            return CVReport(designs=(), registry_names=(MEAN_BASELINE_NAME,), baseline_name=MEAN_BASELINE_NAME, seed=seed, n_rows=3, estimator_declarations={})

    class StubEstimator(Estimator):
        # E2.4 §2C: the declarations are required to be declarable at all.
        input_kind = "covariates"
        uncertainty_method = "stub"
        uncertainty_semantics = "stub"

        def fit(self, features, target) -> None:
            call_order.append("fit")

        def _predict(self, features):
            # E2.1: predict() became the ABC's Template Method (pairing
            # validation); stubs implement the hook, same as before the
            # revision but under the hook's name.
            call_order.append("predict")
            return np.zeros(len(features)), np.zeros(len(features))

        def provenance(self) -> dict:
            return {}

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

    def stub_emitter(report, *, matrix, matrix_manifest):
        call_order.append("manifest")
        return RunManifest(run_id="stub", seed=report.seed).finalize()

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, StubEstimator())
    engine = ProspectivityEngine(
        study_area=_study_area(),
        terrain_source=StubTerrainSource(),
        sample_source=StubSampleSource(),
        feature_builder=stub_feature_builder,
        cv_runner=StubRunner(),  # type: ignore[arg-type]
        estimators=registry,
        ts6_reference=StubTS6Reference(),
        economic_model=StubEconomicModel(),
        scenario_configs=[
            {"scenario_name": "MARKET_STANDARD"},
            {"scenario_name": "STRATEGIC_SUBSIDIZED"},
        ],
        seed=42,
        compare_to_ts6_fn=stub_compare_to_ts6,
        manifest_emitter=stub_emitter,
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
        "manifest",
    ]
    assert manifest.seed == 42
    assert manifest.ts6_agreement is not None
    assert manifest.ts6_agreement.spatial_correlation == 0.5
    assert len(manifest.economic_results) == 2
