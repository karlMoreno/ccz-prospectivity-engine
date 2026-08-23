"""ProspectivityEngine — TEMPLATE METHOD.

The whole-run fixed sequence (alpha proposal §5/§10):

    ingest -> features -> CV -> manifest -> claim -> predict+uncertainty
        -> write -> compare_to_ts6 -> economics -> extend manifest

Same composition-based Template Method style as IngestionPipeline: `run()`
never changes, but every step delegates to an injected Strategy
(TerrainSource, SampleSource, the Estimators in an EstimatorRegistry,
EconomicModel, TS6Reference), a Template Method of its own (the
CrossValidationRunner), or a plain callable (`feature_builder`, the surface
builder and writer, the claim evaluator, the manifest emitter and extender).
Phase 0 wired the sequence and the seams; Phases 1–2 supplied real
strategies for ingestion, features, estimators and CV; Phase 3 supplied
prediction surfaces, the writer, the TS-6 comparison and the extended
manifest; Phase 4 supplies economics.

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
provenance chain asserted (§2D). `CrossValidator` is RETIRED.

E3.4 REVISION (the same protocol, 2026-08-22). BEFORE: `_fit_predict`
predicted at the 35 TRAINING locations (E3.0 §1: no grid existed anywhere
in `engine/`), `_compare_to_ts6` handed that dict to a Phase-0 stub that
raised, the feature seam returned `(matrix, manifest)`, and the manifest
was finalized with ONE `ts6_agreement`. AFTER:

  * the feature seam returns a `FeatureBundle` — matrix, its manifest, the
    PREDICTION GRID read from the SAME stack, and the stack and corpus
    manifests the guard and the emitter recompute the chain from
    (features/bundle.py says why one call and not two seams);
  * the CV record is emitted BEFORE any surface exists and E2.5's guard is
    evaluated on it for EVERY design — the writer marks each surface with
    the verdict of the design the caller DECLARED (`claim_design`, a
    required argument: the guard's unit is (run, design), E3.1+2 §3, and
    choosing the design silently here is exactly what E3.4 must not do);
  * `_fit_predict` builds paired surfaces over the grid for every estimator
    (E3.1+2's `build_surfaces`), the writer emits them with the three
    watermark carriers, the comparison returns ONE AGREEMENT PER ESTIMATOR
    (E3.3's `compare_all_to_ts6`), and `extend_run_manifest` records all of
    it with every chain link recomputed;
  * the Phase-0 `ts6.reference.compare_to_ts6` stub is RETIRED (it had no
    implementation and its signature could not express "all of them").

    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                          ProspectivityEngine.run()                             │
    │                                                                               │
    │ ingest ─► features ─► CV ─► manifest ─► claim ─► surfaces ─► write ─► ts6 ─►  │
    │   │         │          │       │           │         │          │       │     │
    │   ▼         ▼          ▼       ▼           ▼         ▼          ▼       ▼     │
    │ terrain_  feature_   cv_     emit_run_  evaluate_  build_    write_  ts6_ref  │
    │ source +  builder    runner  manifest   claim per  surfaces  surface +compare │
    │ sample_   → Feature  .run()  (E2.4,     design     (every    (COG +  _all_    │
    │ source      Bundle   → CV    the chain  (E2.5)     estimator, 3       to_ts6  │
    │                      Report  asserted)             paired)   carriers)(E3.3)  │
    │                                                                               │
    │  ─► economics (EconomicModel.apply × N, Phase 4) ─► export (E5.2) ─► extend   │
    │        → RunManifest (+ surfaces · ts6_agreement mapping · claim · chain)     │
    │        → <output_dir>/run_manifest.json                                       │
    └──────────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.domain.results import (
    EconomicDifferenceResult,
    EconomicScenarioResult,
    RunManifest,
    TS6Agreement,
)
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.economics.contract import ScenarioConfig
from engine.prospectivity.economics.model import (
    EconomicInputs,
    EconomicModel,
    FootprintDifference,
    ScenarioFootprints,
)
from engine.prospectivity.economics.writer import write_difference, write_footprints
from engine.prospectivity.estimators.registry import EstimatorRegistry
from engine.prospectivity.export.flat import EXPORT_DIR, export_layers
from engine.prospectivity.features.bundle import FeatureBundle
from engine.prospectivity.provenance.emitter import extend_run_manifest
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.samples.source import SampleSource
from engine.prospectivity.surfaces.builder import SurfaceResult, build_surfaces
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import compute_surface_origin, write_surface
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.ts6.comparison import compare_all_to_ts6
from engine.prospectivity.ts6.reference import TS6Reference
from engine.prospectivity.validation.claim import ClaimVerdict, evaluate_claim
from engine.prospectivity.validation.runner import (
    CrossValidationRunner,
    CVReport,
    emit_run_manifest,
)

MANIFEST_NAME = "run_manifest.json"
ECONOMICS_DIR = "economics"  # E4.2: the economics rasters' own directory under output_dir
GENERATOR = "engine.prospectivity.engine.ProspectivityEngine.run"

FeatureBuilder = Callable[[TerrainLayer, list[Observation]], FeatureBundle]
ManifestEmitter = Callable[..., RunManifest]  # emit_run_manifest's signature
ManifestExtender = Callable[..., RunManifest]  # extend_run_manifest's signature
ClaimEvaluator = Callable[..., ClaimVerdict]  # evaluate_claim's signature
SurfaceBuilder = Callable[..., Mapping[str, SurfaceResult]]  # build_surfaces' signature
SurfaceWriter = Callable[..., Mapping[str, Path]]  # write_surface's signature
FootprintWriter = Callable[..., Mapping[tuple[str, float], Path]]  # write_footprints' signature
DifferenceWriter = Callable[..., Mapping[tuple[str, float], Path]]  # write_difference's signature
LayerExporter = Callable[..., Mapping[str, Path]]  # export_layers' signature (E5.2)
# (surfaces, grid, ts6_surface, surface_data_origin) -> one agreement per estimator
TS6Comparer = Callable[[Mapping[str, SurfaceResult], PredictionGrid, TS6Surface, DataOrigin], Mapping[str, TS6Agreement]]


def _default_compare(
    surfaces: Mapping[str, SurfaceResult], grid: PredictionGrid, ts6: TS6Surface, origin: DataOrigin
) -> Mapping[str, TS6Agreement]:
    return compare_all_to_ts6(surfaces, grid, ts6, surface_data_origin=origin)


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
        scenario_configs: Sequence[ScenarioConfig],
        *,
        output_dir: Path | str,
        claim_design: str,
        difference_pairs: Sequence[tuple[str, str]] = (),
        seed: int = 0,
        run_id: str | None = None,
        compare_to_ts6_fn: TS6Comparer = _default_compare,
        manifest_emitter: ManifestEmitter = emit_run_manifest,
        manifest_extender: ManifestExtender = extend_run_manifest,
        claim_evaluator: ClaimEvaluator = evaluate_claim,
        surface_builder: SurfaceBuilder = build_surfaces,
        surface_writer: SurfaceWriter = write_surface,
        footprint_writer: FootprintWriter = write_footprints,
        difference_writer: DifferenceWriter = write_difference,
        layer_exporter: LayerExporter = export_layers,
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
        if not claim_design:
            raise ValueError(
                "claim_design is required: E2.5's guard is keyed on (run, design), and the "
                "design a claim rests on is the caller's DECLARATION, recorded in the "
                "manifest — never chosen by the engine"
            )
        self._study_area = study_area
        self._terrain_source = terrain_source
        self._sample_source = sample_source
        self._feature_builder = feature_builder
        self._cv_runner = cv_runner
        self._estimators = estimators
        self._ts6_reference = ts6_reference
        self._economic_model = economic_model
        self._scenario_configs = tuple(scenario_configs)
        self._difference_pairs = tuple(difference_pairs)
        self._output_dir = Path(output_dir)
        self._claim_design = claim_design
        self._seed = seed
        self._run_id = run_id
        self._compare_to_ts6_fn = compare_to_ts6_fn
        self._manifest_emitter = manifest_emitter
        self._manifest_extender = manifest_extender
        self._claim_evaluator = claim_evaluator
        self._surface_builder = surface_builder
        self._surface_writer = surface_writer
        self._footprint_writer = footprint_writer
        self._difference_writer = difference_writer
        self._layer_exporter = layer_exporter

    def run(self) -> RunManifest:
        terrain, samples = self._ingest()
        bundle = self._build_features(terrain, samples)
        cv_report = self._cross_validate(bundle.matrix)
        base = self._emit_manifest(cv_report, bundle)
        verdicts = self._evaluate_claims(base, bundle)
        surfaces = self._fit_predict(bundle)
        written = self._write_surfaces(surfaces, bundle, verdicts)
        ts6_surface, agreements = self._compare_to_ts6(surfaces, bundle)
        footprints, differences = self._apply_economics(surfaces, bundle)
        economic_results, economic_differences = self._write_economics(
            footprints, differences, surfaces, bundle, verdicts
        )
        self._export_layers(written, bundle)
        return self._extend_manifest(
            base, bundle, surfaces, written, ts6_surface, agreements, verdicts,
            economic_results, economic_differences,
        )

    def _ingest(self) -> tuple[TerrainLayer, list[Observation]]:
        terrain = self._terrain_source.load(self._study_area)
        samples = self._sample_source.get_training_samples()
        return terrain, samples

    def _build_features(self, terrain: TerrainLayer, samples: list[Observation]) -> FeatureBundle:
        return self._feature_builder(terrain, samples)

    def _cross_validate(self, matrix) -> CVReport:
        return self._cv_runner.run(matrix, seed=self._seed)

    def _emit_manifest(self, cv_report: CVReport, bundle: FeatureBundle) -> RunManifest:
        """E2.4's record, finished BEFORE any surface exists: the claim guard
        reads it to decide how the surfaces are marked."""
        return self._manifest_emitter(
            cv_report,
            matrix=bundle.matrix,
            matrix_manifest=bundle.matrix_manifest,
            run_id=self._run_id,
            generator=GENERATOR,
        )

    def _evaluate_claims(self, base: RunManifest, bundle: FeatureBundle) -> dict[str, ClaimVerdict]:
        """E2.5's guard for EVERY design the run executed — iterate, never
        pick. The claim design must be among them."""
        designs = [d["name"] for d in base.cross_validation.get("designs", [])]
        if self._claim_design not in designs:
            raise ValueError(
                f"claim_design {self._claim_design!r} is not a design this run executed "
                f"({designs}) — a claim cannot rest on a design the run did not cross-validate"
            )
        return {
            design: self._claim_evaluator(
                base, design=design, feature_stack_manifest=bundle.stack_manifest
            )
            for design in designs
        }

    def _fit_predict(self, bundle: FeatureBundle) -> Mapping[str, SurfaceResult]:
        """Every registered estimator, fitted on the full matrix and predicted
        over every predictable grid cell as a PAIRED (mu, sd) surface —
        `build_surfaces` iterates the registry and routes by declaration."""
        return self._surface_builder(bundle.grid, bundle.matrix, self._estimators)

    def _surface_origin(self, bundle: FeatureBundle) -> DataOrigin:
        """COMPUTED from the stack's layer origins and the matrix's origin —
        never declared here (the emitter recomputes the same and compares)."""
        layer_origins = list(bundle.stack_manifest.get("layers_by_data_origin", {}))
        return compute_surface_origin(
            combine_origins(layer_origins).value, bundle.matrix_manifest.data_origin
        )

    def _write_surfaces(
        self,
        surfaces: Mapping[str, SurfaceResult],
        bundle: FeatureBundle,
        verdicts: Mapping[str, ClaimVerdict],
    ) -> dict[str, Mapping[str, Path]]:
        origin = self._surface_origin(bundle)
        verdict = verdicts[self._claim_design]
        return {
            name: self._surface_writer(
                surfaces[name], bundle.grid, self._output_dir, data_origin=origin, verdict=verdict
            )
            for name in sorted(surfaces)
        }

    def _compare_to_ts6(
        self, surfaces: Mapping[str, SurfaceResult], bundle: FeatureBundle
    ) -> tuple[TS6Surface, Mapping[str, TS6Agreement]]:
        ts6_surface = self._ts6_reference.load()
        agreements = self._compare_to_ts6_fn(
            surfaces, bundle.grid, ts6_surface, self._surface_origin(bundle)
        )
        return ts6_surface, agreements

    def _apply_economics(
        self, surfaces: Mapping[str, SurfaceResult], bundle: FeatureBundle
    ) -> tuple[dict[str, ScenarioFootprints], list[FootprintDifference]]:
        """E4.1: every scenario over every estimator's surface, then every
        Contract 4 difference pair — iterate, never pick. The two declared
        facts the watermark derives from travel in the inputs: the stack's
        DEM origin and (per scenario) the illustrative flag."""
        inputs = EconomicInputs(
            surfaces=surfaces,
            grid=bundle.grid,
            cell_area_m2=bundle.cell_area_m2,
            dem_data_origin=bundle.stack_manifest.get("dem_data_origin"),
            surface_data_origin=self._surface_origin(bundle).value,
        )
        footprints: dict[str, ScenarioFootprints] = {}
        for scenario in self._scenario_configs:
            footprints[scenario.name] = self._economic_model.apply(inputs, scenario)
        differences = []
        for a, b in self._difference_pairs:
            if a not in footprints or b not in footprints:
                raise ValueError(
                    f"difference pair ({a!r}, {b!r}) names a scenario this run did not apply "
                    f"({sorted(footprints)})"
                )
            differences.append(self._economic_model.difference(footprints[a], footprints[b]))
        return footprints, differences

    def _write_economics(
        self,
        footprints: Mapping[str, ScenarioFootprints],
        differences: list[FootprintDifference],
        surfaces: Mapping[str, SurfaceResult],
        bundle: FeatureBundle,
        verdicts: Mapping[str, ClaimVerdict],
    ) -> tuple[list[EconomicScenarioResult], list[EconomicDifferenceResult]]:
        """E4.2: the footprint and difference rasters, through E3.1+2's
        writer, marked by the DECLARED claim design's verdict like the
        surfaces; the records then carry each raster's basename. They land
        in `<output_dir>/economics/` — their own directory with their own
        sidecars — so the surfaces' directory listing (which the manifest's
        `output_hashes` is checked against in full) is untouched until E4.3
        records the economics block."""
        verdict = verdicts[self._claim_design]
        economics_dir = self._output_dir / ECONOMICS_DIR
        results = []
        for name in footprints:
            written = self._footprint_writer(
                footprints[name], bundle.grid, surfaces, economics_dir, claim_verdict=verdict
            )
            results.append(footprints[name].record({key: path.name for key, path in written.items()}))
        recorded_differences = []
        for difference in differences:
            a, b = difference.pair
            written = self._difference_writer(
                difference, footprints[a], footprints[b], bundle.grid, surfaces, economics_dir,
                claim_verdict=verdict,
            )
            recorded_differences.append(difference.record({key: path.name for key, path in written.items()}))
        return results, recorded_differences

    def _export_layers(self, written: Mapping[str, Mapping[str, Path]], bundle: FeatureBundle) -> Mapping[str, Path]:
        """E5.2: the browser-facing flat-array export of every written raster
        — the surface pairs from what the writer returned, the economics
        rasters from E4.2's association record — into `<output_dir>/export/`,
        BEFORE the manifest is extended so the emitter verifies each export
        against the pixels and hashes it under `export/<basename>`."""
        return self._layer_exporter(
            self._output_dir, surfaces_written=written,
            economics_dir=self._output_dir / ECONOMICS_DIR, grid=bundle.grid,
        )

    def _extend_manifest(
        self,
        base: RunManifest,
        bundle: FeatureBundle,
        surfaces: Mapping[str, SurfaceResult],
        written: Mapping[str, Mapping[str, Path]],
        ts6_surface: TS6Surface,
        agreements: Mapping[str, TS6Agreement],
        verdicts: Mapping[str, ClaimVerdict],
        economic_results: list[EconomicScenarioResult],
        economic_differences: list[EconomicDifferenceResult],
    ) -> RunManifest:
        manifest = self._manifest_extender(
            base,
            matrix=bundle.matrix,
            matrix_manifest=bundle.matrix_manifest,
            corpus_manifest=bundle.corpus_manifest,
            stack_manifest=bundle.stack_manifest,
            grid=bundle.grid,
            surfaces=surfaces,
            written=written,
            ts6=ts6_surface,
            agreements=agreements,
            verdicts=verdicts,
            claim_design=self._claim_design,
            economic_results=economic_results,
            economic_differences=economic_differences,
            economics_dir=self._output_dir / ECONOMICS_DIR,
            exports_dir=self._output_dir / EXPORT_DIR,
        )
        self._output_dir.mkdir(parents=True, exist_ok=True)
        (self._output_dir / MANIFEST_NAME).write_text(manifest.to_json())
        return manifest
