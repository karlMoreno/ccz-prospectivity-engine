"""Shared pytest fixtures: synthetic sources -> ingested corpus, and synthetic
rasters, so the CI-proving tests (E0.5) don't each re-wire the pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.normalizer_registry import NormalizerRegistry
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from tests.fixtures.adapters import (
    FixtureBoxcoreAdapter,
    FixtureCoverAdapter,
    FixtureGridAdapter,
)
from tests.fixtures.normalizers import (
    FixtureCountNormalizer,
    FixtureCoverNormalizer,
    FixtureGridNormalizer,
    FixtureMassNormalizer,
)
from tests.fixtures.rasters import write_synthetic_bathymetry, write_synthetic_ts6_raster

REPO_ROOT = Path(__file__).resolve().parent.parent
NATIVE_DIR = REPO_ROOT / "data" / "fixtures" / "native"


def _build_fixture_normalizer_registry() -> NormalizerRegistry:
    # These E0.4/E0.5 fixture sources never emit GRADE, so GRADE is left
    # unregistered here on purpose (NormalizerRegistry.normalize only needs a
    # class actually present in a record's evidence_class).
    registry = NormalizerRegistry()
    registry.register(EvidenceClass.MASS, FixtureMassNormalizer())
    registry.register(EvidenceClass.COUNT, FixtureCountNormalizer())
    registry.register(EvidenceClass.COVER, FixtureCoverNormalizer())
    registry.register(EvidenceClass.GRID, FixtureGridNormalizer())
    return registry


NORMALIZERS = _build_fixture_normalizer_registry()


@pytest.fixture
def synthetic_corpus() -> list[Observation]:
    """Runs all three synthetic source families through IngestionPipeline and
    returns the resulting master corpus — the E0.5 CI centerpiece."""
    corpus: list[Observation] = []
    adapters = [
        FixtureBoxcoreAdapter(NATIVE_DIR / "synthetic_boxcore_native.csv"),
        FixtureCoverAdapter(NATIVE_DIR / "synthetic_cover_native.csv"),
        FixtureGridAdapter(NATIVE_DIR / "synthetic_grid_native.csv"),
    ]
    for adapter in adapters:
        IngestionPipeline(adapter=adapter, normalizers=NORMALIZERS, corpus=corpus).run()
    return corpus


@pytest.fixture
def synthetic_bathymetry_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_bathymetry.tif"
    write_synthetic_bathymetry(path)
    return path


@pytest.fixture
def synthetic_ts6_raster_path(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_ts6.tif"
    write_synthetic_ts6_raster(path)
    return path


@pytest.fixture(scope="session")
def surface_assembly(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """E3.1+2: the real corpus and 35-station matrix over the synthetic-DEM
    stack, with all three surfaces built once and shared read-only.

    Session-scoped because building the stack and fitting the forest is the
    slowest thing in the suite, and both the builder and the writer tests
    need the same artefacts.
    """
    import json as _json
    from pathlib import Path as _Path

    from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
    from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
    from engine.prospectivity.estimators.random_forest import RandomForestEstimator
    from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME, EstimatorRegistry
    from engine.prospectivity.features.dem_grid import DemGrid
    from engine.prospectivity.features.registry import build_default_registry
    from engine.prospectivity.features.stack import build_covariate_stack
    from engine.prospectivity.provenance.origin import DataOrigin
    from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
    from engine.prospectivity.surfaces.builder import build_surfaces
    from engine.prospectivity.surfaces.grid import PredictionGrid
    from engine.prospectivity.training_matrix import assemble_training_matrix
    from tests.fixtures.rasters import write_synthetic_bathymetry

    root = _Path(__file__).resolve().parent.parent
    tmp = tmp_path_factory.mktemp("surface_assembly")
    dem_path = tmp / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    stack_manifest = _json.loads(written["provenance"].read_text())
    corpus_manifest = _json.loads((root / "data" / "corpus" / "manifest.json").read_text())
    dem_grid = DemGrid.load(dem_path)
    layers = build_default_registry().build_all(dem_grid)
    matrix, matrix_manifest = assemble_training_matrix(
        CorpusCsvSampleSource(), dem_grid, layers, corpus_manifest, stack_manifest
    )
    grid = PredictionGrid.from_stack(written["provenance"].parent)
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", OrdinaryKrigingEstimator())
    registry.register(
        "random_forest",
        RandomForestEstimator(
            seed=0, n_estimators=100, importance_seeds=(0,), feature_names=grid.layer_names
        ),
    )
    return {
        "grid": grid,
        "matrix": matrix,
        "matrix_manifest": matrix_manifest,
        "stack_manifest": stack_manifest,
        "surfaces": build_surfaces(grid, matrix, registry),
    }
