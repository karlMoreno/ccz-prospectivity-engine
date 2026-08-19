"""TrainingMatrix + TrainingMatrixManifest — assembly and its provenance
(E2.0-3).

Glue over the three seams that already exist (the corpus_builder/stack.py
precedent — orchestration, not a new pattern): `SampleSource` supplies the
35 training rows, `extract_covariates_at_stations` supplies X with its
guard and shared-cell accounting, Contract 8's `target_definition()` says
what y MEANS. `TrainingMatrixManifest` is LAYER SUPERTYPE reuse — the
fourth `ProvenanceArtifact`, not a new pattern.

    CorpusCsvSampleSource ──► 35 Observations, sorted by source_record_id
          │                        │
          │                        ▼
    DemGrid + 8 layers ──► extract_covariates_at_stations  (guard inside)
          │                        │  NaN anywhere? ──► REFUSE by name
          ▼                        ▼
    Contract 8 target ──► TrainingMatrix (X 35×8 · y 35 · coords 35×2 · ids)
    (DeclaredField:            │
     value + origin)           ▼
                     TrainingMatrixManifest
                       upstream {corpus, feature_stack} · target value+origin
                       sampling_method · shared_cell_count · cell_groups
                       matrix_sha256 · data_origin = combine(corpus, stack)

NaN POLICY — REFUSE, decision made (alternative recorded): a matrix with a
hole is a matrix whose extent question has not been answered. On real GEBCO
a station near the raster edge is a thing to KNOW ABOUT and fix — the
extent, or the station's admissibility — not a row that quietly vanishes
from n=35, where losing two stations is a 6% data loss that would never
show as an error. Exclusion-with-a-record was considered and declined: it
converts an extent defect into a bookkeeping entry, and flag-never-drop
elsewhere in this project flags rows that stay IN the data — an excluded
matrix row is dropped by another name. Imputation is fabrication and was
never on the table.

WHY A FOURTH ARTIFACT (and not fields on RunManifest) — the class docstring
carries the full argument; the short form: the corpus hash and the stack
hash are both INVARIANT to the target definition, so without a
matrix-level record the one decision that defines what the model predicts
has no identity in the provenance chain.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.extraction import (
    CovariateExtraction,
    Station,
    extract_covariates_at_stations,
)
from engine.prospectivity.features.recipe import CovariateResult
from engine.prospectivity.model_config import DeclaredField, load_model_config, target_definition
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.contract_versions import contract_versions
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.samples.source import SampleSource

# The one target this module knows how to assemble y for. Exhaustive
# dispatch with an explicit raise (house convention): a NEW admissible value
# arriving via Contract 8 (e.g. surface_only, if Track G resolves the
# six-event burial contradiction) must be wired HERE deliberately, never
# absorbed silently.
_TARGET_COLUMNS = {"total_as_published": "abundance_kg_m2"}

COORD_COLUMNS = ("longitude", "latitude")

# Origins whose COMPUTED presence in a matrix still traces every value to a
# measurement this repo holds: MEASURED (degenerate — a matrix is always a
# computation) and DERIVED (computed from MEASURED inputs — the intended
# Checkpoint-1 state). Everything else watermarks. See matrix_watermark.
_CLEAN_MATRIX_ORIGINS = (DataOrigin.MEASURED, DataOrigin.DERIVED)

MATRIX_WATERMARK_TEMPLATE = (
    "TRAINING MATRIX ORIGIN {origin} — non-scientific; no model claim may "
    "cite it. (Computed by combine_origins over corpus and feature-stack "
    "origins; a synthetic or authored input taints every derived number.)"
)


@dataclass(frozen=True)
class TrainingMatrix:
    """The assembled model input. Arrays are read-only (the E2.0-2 rule:
    accounting computed at build time must not be invalidatable by a caller
    mutating state afterwards). Row order is sorted source_record_id —
    stable and stated, never CSV encounter order."""

    station_ids: tuple[str, ...]
    covariate_names: tuple[str, ...]  # X column order
    X: np.ndarray  # (n_stations, n_covariates) float64
    y: np.ndarray  # (n_stations,) float64 — meaning per manifest.target_definition
    coords: np.ndarray  # (n_stations, 2) float64, columns COORD_COLUMNS
    coord_columns: tuple[str, str] = COORD_COLUMNS


class TrainingMatrixManifest(ProvenanceArtifact):
    """The FOURTH provenance artifact (docs/contracts/PROVENANCE.md), between
    FeatureStackManifest and RunManifest.

    Why a fourth artifact rather than folding these fields into RunManifest:
    the corpus hash and the feature-stack hash are both INVARIANT to the
    target definition, so two matrices built on different y would present
    IDENTICAL upstream_hashes. Contract 8 does not close this on its own —
    the contract file is not hashed into either upstream artifact — so
    without a matrix-level record, the one decision that defines what the
    model predicts has no identity in the provenance chain. The alternative
    considered: fold into RunManifest, on the grounds that a matrix is 1:1
    with a run. Declined — 1:1 only by convention, nothing enforces it, and
    the moment two runs share a matrix the record is in the wrong place.
    PROVENANCE.md's stated principle is that artifacts are separated by
    LIFETIME.

    `target_definition` records the VALUE and its DECLARED ORIGIN together
    (Contract 8's DeclaredField) — the value alone loses the caveat, and the
    AUTHORED→LITERATURE promotion (Isaac's citation arriving) legitimately
    changes this artifact's content_hash.

    `cell_groups` is recorded, not just `shared_cell_count`: the grouping is
    what lets anyone recompute the covariate-model R² ceiling (0.348 on
    today's fixture) next to any model score, and it changes at Checkpoint 1
    when the cells shrink. A count alone cannot reconstruct the ceiling.

    `data_origin` is COMPUTED by combine_origins over the corpus and stack
    origins — never declared by hand (P2.0's rule: file- and run-level
    origins are computed, and a real corpus does not launder a synthetic
    terrain).

    `matrix_sha256` hashes the matrix's canonical bytes (ids, names, X, y,
    coords), so this manifest's content_hash covers the actual numbers, not
    only their description.
    """

    target_definition: dict[str, str | None]
    sampling_method: str
    shared_cell_count: int
    distinct_cell_count: int
    cell_groups: list[list[str]] = Field(default_factory=list)
    n_stations: int
    n_covariates: int
    covariate_names: list[str] = Field(default_factory=list)
    coord_columns: list[str] = Field(default_factory=list)
    matrix_sha256: str
    data_origin: str


def matrix_watermark(data_origin: DataOrigin | str | None) -> str | None:
    """The watermark for a training matrix's COMPUTED origin, or None for a
    clean matrix. DEFAULT-ON, same posture as P2.0d-3's `dem_watermark`:
    clean UNLESS the origin proves measured lineage, never watermark IF
    synthetic. An undeclared origin stamps; an unknown label raises.

    Deliberate divergence from `dem_watermark`, stated so nobody "unifies"
    them wrongly: `dem_watermark` stamps DERIVED because for a DECLARED
    INPUT, DERIVED means the terrain was not actually measured. Here the
    origin is COMPUTED over inputs, and a matrix is by construction a
    derivation — combine(MEASURED corpus, DERIVED-from-MEASURED features)
    is DERIVED, the intended clean state at Checkpoint 1. Keying on the
    computed origin (not on the DEM declaration alone) is what keeps a
    synthetic CORPUS stamped even under a real GEBCO DEM.
    """
    if data_origin is None:
        return MATRIX_WATERMARK_TEMPLATE.format(origin="NOT DECLARED")
    origin = DataOrigin(data_origin)
    if origin in _CLEAN_MATRIX_ORIGINS:
        return None
    return MATRIX_WATERMARK_TEMPLATE.format(origin=origin.value)


def _require_keys(manifest: dict, keys: tuple[str, ...], name: str) -> None:
    missing = [key for key in keys if key not in manifest]
    if missing:
        raise ValueError(
            f"{name} is missing required field(s) {missing} — refusing to assemble "
            "a matrix over an artifact that cannot prove its identity or origin"
        )


def _manifest_origin(counts_by_origin: dict, name: str) -> DataOrigin:
    """The artifact-level origin computed from a manifest's recorded
    origin-composition counts — combine over the keys, never a hand-pick."""
    if not counts_by_origin:
        raise ValueError(f"{name} records an empty origin composition — no silent origin")
    return combine_origins(list(counts_by_origin))


def _matrix_sha256(
    station_ids: tuple[str, ...],
    covariate_names: tuple[str, ...],
    X: np.ndarray,
    y: np.ndarray,
    coords: np.ndarray,
) -> str:
    """Canonical hash of the matrix content: identity columns as UTF-8,
    arrays as C-order float64 bytes. Deterministic across machines."""
    digest = hashlib.sha256()
    digest.update("\x1f".join(station_ids).encode("utf-8"))
    digest.update("\x1f".join(covariate_names).encode("utf-8"))
    for array in (X, y, coords):
        digest.update(np.ascontiguousarray(array, dtype=np.float64).tobytes())
    return "sha256:" + digest.hexdigest()


def matrix_sha256(matrix: TrainingMatrix) -> str:
    """The canonical content hash of a TrainingMatrix — the SAME computation
    the manifest records, exposed so a downstream artifact (E2.4's
    RunManifest) can RE-DERIVE it from the arrays it was actually handed and
    refuse a manifest that does not describe them (2D: never a literal)."""
    return _matrix_sha256(
        matrix.station_ids, matrix.covariate_names, matrix.X, matrix.y, matrix.coords
    )


def assemble_training_matrix(
    sample_source: SampleSource,
    grid: DemGrid,
    layers: list[CovariateResult] | tuple[CovariateResult, ...],
    corpus_manifest: dict,
    stack_manifest: dict,
    *,
    target: DeclaredField | None = None,
) -> tuple[TrainingMatrix, TrainingMatrixManifest]:
    """Assemble the training matrix and its manifest.

    `corpus_manifest` / `stack_manifest` are the parsed upstream artifacts
    (data/corpus/manifest.json; the stack's provenance.json) — the source of
    the upstream hashes and origin compositions. `target` is a testability
    seam (build_default_registry precedent); production callers omit it and
    get Contract 8 via `target_definition()`.
    """
    _require_keys(
        corpus_manifest,
        ("content_hash", "training_eligible_count", "admitted_rows_by_data_origin"),
        "corpus manifest",
    )
    _require_keys(
        stack_manifest,
        ("content_hash", "layers_by_data_origin", "upstream_hashes"),
        "stack manifest",
    )

    # The stack manifest handed in must describe the DEM actually being
    # sampled — extraction's guard covers layers↔grid; this covers
    # manifest↔grid, or upstream_hashes would chain to the wrong stack.
    recorded_dem = (stack_manifest.get("upstream_hashes") or {}).get("dem")
    if recorded_dem != grid.content_hash:
        raise ValueError(
            f"stack manifest upstream dem hash ({recorded_dem!r}) does not match the "
            f"sampling grid's content hash ({grid.content_hash!r}) — the manifest "
            "describes a different stack than the layers being sampled"
        )

    target = target if target is not None else target_definition()
    if target.value not in _TARGET_COLUMNS:
        raise ValueError(
            f"no assembly rule for target_definition {target.value!r} — this module "
            f"knows {sorted(_TARGET_COLUMNS)}. A new admissible value arrives via "
            "Contract 8 WITH its assembly rule here, never by improvisation."
        )
    target_column = _TARGET_COLUMNS[target.value]

    observations: list[Observation] = sorted(
        sample_source.get_training_samples(), key=lambda obs: obs.source_record_id
    )
    expected = corpus_manifest["training_eligible_count"]
    if len(observations) != expected:
        raise ValueError(
            f"sample source yielded {len(observations)} training rows but the corpus "
            f"manifest records training_eligible_count={expected} — the corpus and its "
            "manifest disagree; rebuild before assembling a matrix on either"
        )

    stations = [Station.from_observation(obs) for obs in observations]
    extraction: CovariateExtraction = extract_covariates_at_stations(grid, layers, stations)

    # NaN POLICY — REFUSE (decision made; rationale in the module docstring).
    if extraction.nan_stations:
        detail = "; ".join(
            f"{station_id}: {list(covariates)}"
            for station_id, covariates in extraction.nan_stations
        )
        raise ValueError(
            f"NaN covariates at {len(extraction.nan_stations)} station(s) — {detail}. "
            "A matrix with a hole is a matrix whose extent question has not been "
            "answered: fix the DEM extent or the station's admissibility. Refusing "
            "to assemble (never excluded, never imputed)."
        )

    y = np.array([getattr(obs, target_column) for obs in observations], dtype=np.float64)
    coords = np.array(
        [[obs.longitude, obs.latitude] for obs in observations], dtype=np.float64
    )
    X = extraction.values  # already read-only, station order == sorted order
    y.flags.writeable = False
    coords.flags.writeable = False

    matrix = TrainingMatrix(
        station_ids=extraction.station_ids,
        covariate_names=extraction.covariate_names,
        X=X,
        y=y,
        coords=coords,
    )

    corpus_origin = _manifest_origin(
        corpus_manifest["admitted_rows_by_data_origin"], "corpus manifest"
    )
    stack_origin = _manifest_origin(stack_manifest["layers_by_data_origin"], "stack manifest")
    data_origin = combine_origins([corpus_origin, stack_origin])

    versions = dict(contract_versions())
    versions["model_config_version"] = load_model_config()["model_config_version"]

    manifest = TrainingMatrixManifest(
        target_definition={
            "value": target.value,
            "data_origin": target.data_origin,
            "author": target.author,
        },
        sampling_method=extraction.sampling_method,
        shared_cell_count=extraction.shared_cell_count,
        distinct_cell_count=extraction.distinct_cell_count,
        cell_groups=[list(group) for group in extraction.cell_groups],
        n_stations=len(matrix.station_ids),
        n_covariates=len(matrix.covariate_names),
        covariate_names=list(matrix.covariate_names),
        coord_columns=list(matrix.coord_columns),
        matrix_sha256=_matrix_sha256(
            matrix.station_ids, matrix.covariate_names, matrix.X, matrix.y, matrix.coords
        ),
        data_origin=data_origin.value,
        contract_versions=versions,
        upstream_hashes={
            "corpus": corpus_manifest["content_hash"],
            "feature_stack": stack_manifest["content_hash"],
        },
    )
    manifest.finalize()
    return matrix, manifest
