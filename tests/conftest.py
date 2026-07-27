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
