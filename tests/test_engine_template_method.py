"""ProspectivityEngine.run() (TEMPLATE METHOD) calls its fixed sequence in
order, regardless of what the injected strategies do. Phase 0 proved the
*sequence*; E2.4 §2B revised the seams (a registry + a CV runner instead of
one estimator + a callable); E3.4 revised them again (a FeatureBundle, the
claim guard, the surface builder and writer, the extender) — the stubs here
stand in for every collaborator, and the assertion is still the ORDER, not
the science (that is each task's own tests, and `test_engine_run.py` for the
real composition end to end).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

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
from engine.prospectivity.features.bundle import FeatureBundle
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.training_matrix import TrainingMatrix, TrainingMatrixManifest
from engine.prospectivity.ts6.reference import TS6Reference
from engine.prospectivity.validation.claim import ClaimVerdict
from engine.prospectivity.validation.runner import CVReport

EXPECTED_ORDER = [
    "ingest:terrain",
    "ingest:samples",
    "features",
    "cv",
    "manifest:emit",
    "claim:leave_one_site_out",
    "surfaces:build",
    "surfaces:write",
    "ts6:load",
    "ts6:compare",
    "economics:MARKET_STANDARD",
    "economics:STRATEGIC_SUBSIDIZED",
    "economics:write:MARKET_STANDARD",
    "economics:write:STRATEGIC_SUBSIDIZED",
    "manifest:extend",
]


def _scenario(name: str, index: int):
    from engine.prospectivity.economics.contract import ScenarioConfig
    from engine.prospectivity.model_config import DeclaredField

    return ScenarioConfig(
        name=name, index=index, description="stub", illustrative_only=True,
        cutoff=DeclaredField(value="1.0", data_origin="AUTHORED", author="unrecorded"),
        cost_model={}, caveats=(),
    )


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


class _StubEstimator(Estimator):
    # E2.4 §2C: the declarations are required to be declarable at all.
    input_kind = "covariates"
    uncertainty_method = "stub"
    uncertainty_semantics = "stub"

    def fit(self, features, target) -> None: ...

    def _predict(self, features):
        return np.zeros(len(features)), np.zeros(len(features))

    def provenance(self) -> dict:
        return {}


def _engine(call_order: list[str], tmp_path: Path, **overrides) -> ProspectivityEngine:
    class StubTerrainSource(TerrainSource):
        def load(self, study_area: StudyArea) -> TerrainLayer:
            call_order.append("ingest:terrain")
            return TerrainLayer(name="bathymetry")

    class StubSampleSource(SampleSource):
        def load_observations(self) -> list[Observation]:
            call_order.append("ingest:samples")
            return [
                Observation(
                    source_record_id="STUB001", source_id="src_synthetic_boxcore",
                    evidence_class=EvidenceClass.MASS, longitude=-126.0, latitude=12.0,
                    abundance_kg_m2=5.0, observation_or_prediction=ObservationOrPrediction.OBSERVED,
                    is_open=True, qa_status="pending",
                )
            ]

    def stub_feature_builder(terrain, samples) -> FeatureBundle:
        call_order.append("features")
        matrix, manifest = _tiny_matrix()
        return FeatureBundle(
            matrix=matrix, matrix_manifest=manifest, grid=object(),  # type: ignore[arg-type]
            stack_manifest={"layers_by_data_origin": {"SYNTHETIC": 1}, "dem_data_origin": "SYNTHETIC"},
            corpus_manifest={}, cell_area_m2=np.ones((1, 1)),
        )

    class StubRunner:
        def run(self, matrix, *, seed):
            call_order.append("cv")
            return CVReport(designs=(), registry_names=(MEAN_BASELINE_NAME,), baseline_name=MEAN_BASELINE_NAME, seed=seed, n_rows=3, estimator_declarations={})

    def stub_emitter(report, *, matrix, matrix_manifest, run_id, generator):
        call_order.append("manifest:emit")
        return RunManifest(
            run_id="stub", seed=report.seed, generator=generator,
            cross_validation={"designs": [{"name": "leave_one_site_out"}]},
        ).finalize()

    def stub_claim(manifest, *, design, feature_stack_manifest):
        call_order.append(f"claim:{design}")
        return ClaimVerdict(design=design, results=(), watermark=None, data_origin=None)

    def stub_builder(grid, matrix, registry):
        call_order.append("surfaces:build")
        return {MEAN_BASELINE_NAME: "surface"}

    def stub_writer(result, grid, output_dir, *, data_origin, verdict):
        call_order.append("surfaces:write")
        return {"prediction": Path("p.tif"), "uncertainty": Path("u.tif")}

    class StubTS6Reference(TS6Reference):
        def load(self) -> TS6Surface:
            call_order.append("ts6:load")
            return TS6Surface(title="stub", source_id="src_ts6_grid", raster_path="stub.tif")

    def stub_compare(surfaces, grid, ts6_surface, origin) -> dict[str, TS6Agreement]:
        call_order.append("ts6:compare")
        # E3.4 (2B): one agreement PER ESTIMATOR, keyed by name.
        return {MEAN_BASELINE_NAME: TS6Agreement(estimator_name=MEAN_BASELINE_NAME, spatial_correlation=0.5)}

    class _StubFootprints:
        def __init__(self, name: str) -> None:
            self._name = name

        def record(self, raster_files=None) -> EconomicScenarioResult:
            return EconomicScenarioResult(scenario_name=self._name, footprints={"stub": {"0": {"raster_file": (raster_files or {}).get(("stub", 0.0))}}})

    def stub_footprint_writer(footprints, grid, surfaces, output_dir, *, claim_verdict):
        call_order.append(f"economics:write:{footprints._name}")
        return {("stub", 0.0): Path(f"footprint__{footprints._name}.tif")}

    class StubEconomicModel(EconomicModel):
        def apply(self, inputs, scenario):
            call_order.append(f"economics:{scenario.name}")
            return _StubFootprints(scenario.name)

    def stub_extender(base, **kwargs):
        call_order.append("manifest:extend")
        return base.model_copy(
            update={"ts6_agreement": dict(kwargs["agreements"]), "economic_results": list(kwargs["economic_results"])}
        ).finalize()

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, _StubEstimator())
    kwargs = dict(
        study_area=_study_area(), terrain_source=StubTerrainSource(), sample_source=StubSampleSource(),
        feature_builder=stub_feature_builder, cv_runner=StubRunner(), estimators=registry,
        ts6_reference=StubTS6Reference(), economic_model=StubEconomicModel(),
        scenario_configs=[_scenario("MARKET_STANDARD", 0), _scenario("STRATEGIC_SUBSIDIZED", 1)],
        output_dir=tmp_path, claim_design="leave_one_site_out", seed=42,
        compare_to_ts6_fn=stub_compare, manifest_emitter=stub_emitter, manifest_extender=stub_extender,
        claim_evaluator=stub_claim, surface_builder=stub_builder, surface_writer=stub_writer,
        footprint_writer=stub_footprint_writer,
    )
    return ProspectivityEngine(**{**kwargs, **overrides})  # type: ignore[arg-type]


def test_run_calls_steps_in_the_documented_order(tmp_path: Path) -> None:
    call_order: list[str] = []
    manifest = _engine(call_order, tmp_path).run()
    assert call_order == EXPECTED_ORDER
    assert manifest.seed == 42
    assert manifest.ts6_agreement is not None
    assert manifest.ts6_agreement[MEAN_BASELINE_NAME].spatial_correlation == 0.5
    assert len(manifest.economic_results) == 2
    assert manifest.economic_results[0].footprints["stub"]["0"]["raster_file"] == "footprint__MARKET_STANDARD.tif"
    assert (tmp_path / "run_manifest.json").is_file()


def test_the_claim_guard_runs_on_the_cv_record_before_any_surface_is_built(tmp_path: Path) -> None:
    """The ORDER that carries a rule: the guard reads E2.4's finished record
    and the writer marks surfaces with its verdict, so `manifest:emit` and
    every `claim:*` must precede `surfaces:build` — separated from "the steps
    all ran" by asserting positions, not membership."""
    call_order: list[str] = []
    _engine(call_order, tmp_path).run()
    assert call_order.index("manifest:emit") < call_order.index("claim:leave_one_site_out") < call_order.index("surfaces:build") < call_order.index("surfaces:write")
    assert call_order.index("surfaces:write") < call_order.index("ts6:compare") < call_order.index("manifest:extend")


def test_a_claim_design_the_run_did_not_execute_is_refused_by_name(tmp_path: Path) -> None:
    call_order: list[str] = []
    with pytest.raises(ValueError, match=r"claim_design 'random_k_fold' is not a design this run executed"):
        _engine(call_order, tmp_path, claim_design="random_k_fold").run()
    assert "surfaces:build" not in call_order  # refused BEFORE any surface was built
    with pytest.raises(ValueError, match=r"claim_design is required"):
        _engine([], tmp_path, claim_design="")


def test_a_runner_over_a_different_registry_than_the_engine_predicts_with_is_refused(tmp_path: Path) -> None:
    """E2.4 §2 review: an estimator must not reach a surface without having
    been cross-validated."""
    class RunnerWithRegistry:
        registry = EstimatorRegistry()

        def run(self, matrix, *, seed): ...

    with pytest.raises(ValueError, match=r"cross-validates a DIFFERENT registry"):
        _engine([], tmp_path, cv_runner=RunnerWithRegistry())
