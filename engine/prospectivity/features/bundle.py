"""FeatureBundle / StackFeatureBuilder — the engine's feature seam (E3.4).

E2.4 §2B made `ProspectivityEngine`'s `feature_builder` return
`(TrainingMatrix, TrainingMatrixManifest)`. Phase 3 needs more from the same
step — and needs it from the SAME stack the matrix was sampled from:

    terrain (TerrainLayer) + samples ──► StackFeatureBuilder ──► FeatureBundle
                                             │                      matrix · matrix_manifest
                        build_covariate_stack┤                      grid (PredictionGrid)
                        assemble_training_matrix                    stack_manifest
                        PredictionGrid.from_stack                   corpus_manifest
                                             │
                        ONE stack, read twice: sampled at the 35 stations for
                        the matrix, read whole as the prediction grid.

WHY A BUNDLE AND NOT A SECOND SEAM: the grid must be the stack's own grid
(E3.1+2 §1 — no resampling, no interpolation between E1.4's values and the
model's inputs), and the claim guard and the manifest emitter need the stack
and corpus manifests to RECOMPUTE the chain. A separate `grid_builder` seam
could be handed a different stack than the matrix came from, and nothing
would notice until the emitter refused (it would: it compares the grid's
stack hash to the matrix manifest's). Producing all five from one call makes
the mismatch unrepresentable rather than merely refused.

THE TERRAIN'S ORIGIN IS A DECLARATION (P2.0d-3): `TerrainLayer.data_origin`
is what the stack records as the DEM's origin, and an undeclared one is
refused here BY NAME rather than defaulted — declaration or nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.training_matrix import (
    TrainingMatrix,
    TrainingMatrixManifest,
    assemble_training_matrix,
)

DEFAULT_CORPUS_MANIFEST = (
    find_repo_root(Path(__file__).resolve()) / "data" / "corpus" / "manifest.json"
)


@dataclass(frozen=True)
class FeatureBundle:
    """Everything the feature step produces from ONE stack, carried together.

    `cell_area_m2` (E4.1): the per-cell area in m², (H, W), computed from
    `DemGrid` — the ONE home of the CRS decision (per-row E-W scaling,
    strategy A) — and carried here DELIBERATELY rather than reconstructed
    from the transform at an economics call site. E4.0 §4 found nothing on
    `PredictionGrid` could give `minable_area_m2`; this is the one seam
    addition that fixes it."""

    matrix: TrainingMatrix
    matrix_manifest: TrainingMatrixManifest
    grid: PredictionGrid
    stack_manifest: dict
    corpus_manifest: dict
    cell_area_m2: np.ndarray


class _ObservationsSampleSource(SampleSource):
    """The engine's already-selected training samples, re-presented through
    the SampleSource seam `assemble_training_matrix` takes. The inherited
    gate re-applies — idempotently, since every row handed in already
    passed it — so the MASS-only rule still has exactly one implementation."""

    def __init__(self, observations: list[Observation]) -> None:
        self._observations = list(observations)

    def load_observations(self) -> list[Observation]:
        return list(self._observations)


class StackFeatureBuilder:
    """The production feature builder: build the stack from the terrain
    layer's DEM, sample it into the training matrix, read it whole as the
    prediction grid.

    `output_dir` is where the stack is written (`<output_dir>/stack/`); the
    E2.4 `run_cv` composition, made a callable the engine can be handed.
    """

    def __init__(self, output_dir: Path | str, *, corpus_manifest_path: Path = DEFAULT_CORPUS_MANIFEST) -> None:
        self._output_dir = Path(output_dir)
        self._corpus_manifest_path = Path(corpus_manifest_path)

    def __call__(self, terrain: TerrainLayer, samples: list[Observation]) -> FeatureBundle:
        if not terrain.path:
            raise ValueError(
                f"terrain layer {terrain.name!r} carries no path — the feature stack is "
                "computed from a DEM file, and there is none to compute it from"
            )
        if terrain.data_origin is None:
            raise ValueError(
                f"terrain layer {terrain.name!r} declares no data_origin — the stack records "
                "the DEM's DECLARED origin and refuses to default one (declaration or nothing, "
                "P2.0d-3): a silent default would label real GEBCO synthetic or a fixture real"
            )
        dem_path = Path(terrain.path)
        written = build_covariate_stack(
            dem_path, self._output_dir / "stack", dem_data_origin=terrain.data_origin
        )
        stack_manifest = json.loads(written["provenance"].read_text())
        corpus_manifest = json.loads(self._corpus_manifest_path.read_text())
        dem_grid = DemGrid.load(dem_path)
        layers = build_default_registry().build_all(dem_grid)
        matrix, matrix_manifest = assemble_training_matrix(
            _ObservationsSampleSource(samples), dem_grid, layers, corpus_manifest, stack_manifest
        )
        grid = PredictionGrid.from_stack(written["provenance"].parent)
        cell_area_m2 = cell_areas_m2(dem_grid)
        if cell_area_m2.shape != (grid.height, grid.width):
            raise ValueError(
                f"cell areas {cell_area_m2.shape} do not match the prediction grid "
                f"{(grid.height, grid.width)} — the stack and the DEM disagree"
            )
        return FeatureBundle(
            matrix=matrix,
            matrix_manifest=matrix_manifest,
            grid=grid,
            stack_manifest=stack_manifest,
            corpus_manifest=corpus_manifest,
            cell_area_m2=cell_area_m2,
        )


def cell_areas_m2(dem_grid: DemGrid) -> np.ndarray:
    """(H, W) cell areas from DemGrid's metre geometry: the E-W size varies
    by row (cos latitude), the N-S size is constant. Read-only."""
    areas = np.outer(dem_grid.dx_m_per_row, np.ones(dem_grid.values.shape[1])) * dem_grid.dy_m
    areas = np.ascontiguousarray(areas, dtype=np.float64)
    areas.flags.writeable = False
    return areas
