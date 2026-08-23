"""extend_run_manifest — the Phase-3 extension of the run manifest (E3.4).

E2.4 emits the RunManifest (`validation/runner.py: emit_run_manifest`): fold
assignment, per-fold per-estimator scores, both estimators' reportable
state, and the chained upstream hashes. This module EXTENDS that artifact
with what Phase 3 produced, and it is an extension rather than a second
emitter on purpose — the CV record is finished before any surface exists,
and the claim guard reads it to decide how the surfaces are marked.

    RunManifest (E2.4, the CV record) ─────────────┐
    corpus manifest · stack manifest · matrix ─────┤  every link RECOMPUTED
    PredictionGrid · SurfaceResult × N ────────────┤  from the artifact it
    the written files (rasters + sidecars) ────────┼──► names, never copied
    TS6Surface · TS6Agreement × N (E3.3) ──────────┤  from a record
    ClaimVerdict × designs (E2.5) ─────────────────┘
                          │
                          ▼
           RunManifest + surfaces · ts6_agreement (mapping) · claim
                       · provenance_chain · output_hashes  → finalize()

THE CHAIN IS ASSERTED, NOT RECORDED. Corpus → feature stack → training
matrix → run → surfaces: each hash written below is RECOMPUTED from the
actual artifact at emission — the corpus manifest's substance, the stack
manifest's substance, the matrix arrays, the raster bytes (whose values are
re-read and compared to the in-memory surfaces), the benchmark raster's
bytes — and refused BY NAME when any two records of the same fact disagree.
A literal copied from an upstream record would be quoted as fact by the
artifact that quotes it; the E2.4 §2D posture, applied to every link.

THE CHAIN'S LIMITS ARE IN THE OUTPUT, AND ONE OF THEM IS GONE. Until HASH.1
commit 2 (2026-08-22) `FeatureStackManifest`'s substance embedded the
caller-supplied DEM path nine times, so only the CORPUS link was verifiable
off the machine that wrote it; E3.4 measured ELEVEN hash values moving with
the directory and recorded them in `provenance_chain.path_dependent_hashes`
with two tests pinned to go red when the fix landed. They did, and the block
now records what is true: the emitter ASSERTS at emission that no `path`
key sits under the stack's `dem` or any `layers[*].dem` (refusing by name
otherwise), records the count the two-directory tests MEASURE (zero), and
states the limits that REMAIN — `matrix_sha256` is native-byte-order
(same-endianness hosts), raster bytes across GDAL versions are unmeasured,
and the run's `inputs.environment` makes its content_hash machine-specific
BY DESIGN (E3.4 commit 3). A statement of a limit must not outlive it.

E2.5's VERDICT IS DATA, NOT PROSE. `claim` carries every design's verdict —
each precondition, pass AND fail, by name — plus the design the caller
DECLARED as the basis of the claim. Today the guard refuses on every design
(no pre-registered threshold; and schemes A and random k-fold are
claim-ineligible by record), and the run is watermarked because its origin
is SYNTHETIC. That refusal is this emitter's honest output, not a gap.

WHAT THIS MODULE DOES NOT DO: decide anything. It never picks an estimator
(every surface is recorded, every agreement is recorded, keyed by name),
never picks a design (every verdict is recorded; the claim design is an
argument the caller declares, recorded as such), and never infers an origin
(the surface origin is recomputed with `combine_origins` and compared to
what the writer recorded).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import rasterio

from engine.prospectivity.domain.results import (
    EconomicDifferenceResult,
    EconomicScenarioResult,
    RunManifest,
    TS6Agreement,
)
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.features.stack import FeatureStackManifest
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.corpus_manifest import CorpusManifest
from engine.prospectivity.provenance.origin import combine_origins
from engine.prospectivity.surfaces.builder import SurfaceResult
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import SIDECAR_NAME, compute_surface_origin
from engine.prospectivity.training_matrix import TrainingMatrix, TrainingMatrixManifest
from engine.prospectivity.validation.claim import ClaimVerdict
from engine.prospectivity.validation.runner import _jsonable, matrix_sha256

SURFACE_KINDS = ("prediction", "uncertainty")
_REPO_ROOT = Path(__file__).resolve().parents[3]

# THE LIMITS, stated where a manifest reader meets them (HASH.1 commit 2).
CHAIN_LIMIT_NOTE = (
    "Every hash in this chain was RECOMPUTED from its artifact at emission. Since "
    "HASH.1 (2026-08-22) the feature-stack substance embeds NO path — the DEM's "
    "location is recorded outside the hash (dem_path) — so the stack, matrix and "
    "surface identities no longer move with the directory a run was built from; "
    "`path_dependent_hashes.count` is what the two-directory tests measure (0). "
    "WHAT REMAINS: matrix_sha256 and coords fingerprints hash native byte order "
    "(portable across same-endianness hosts only); raster bytes across GDAL "
    "versions are not measured; and this run's content_hash includes "
    "inputs.environment BY DESIGN, so it identifies inputs AND environment — two "
    "machines with different installed versions hash differently, which is right."
)

CLAIM_NOTE = (
    "E2.5's guard, evaluated for EVERY design the run executed, each precondition "
    "pass or fail BY NAME. The verdict is a property of the RUN and a DESIGN, not "
    "of an estimator (E3.1+2 §3, measured), so one verdict per design is the "
    "truth as the guard computes it; `design` is the basis the caller DECLARED "
    "for the claim — recorded, never chosen here. A surface written under a "
    "failing verdict is marked non-publishable in its own tags (writer.py)."
)


def _refuse(message: str) -> ValueError:
    return ValueError(message)


def _require_self_consistent(artifact, name: str) -> None:
    """A ProvenanceArtifact whose content_hash no longer describes its own
    contents was mutated after finalize(); refuse to quote it (the E2.4 §2
    review's rule, re-applied to every artifact this emitter reads)."""
    if artifact.content_hash is None:
        raise _refuse(f"the {name} is not finalized (content_hash is None)")
    if artifact.compute_content_hash() != artifact.content_hash:
        raise _refuse(
            f"the {name}'s content_hash does not match its own contents — it was "
            "mutated after finalize(); refusing to quote a record that does not "
            "describe itself"
        )


def _require_equal(fact: str, **records: str | None) -> str:
    """Several records of ONE fact must agree; name every disagreeing record."""
    values = {k: v for k, v in records.items()}
    distinct = set(values.values())
    if len(distinct) != 1 or None in distinct:
        detail = ", ".join(f"{k}={v!r}" for k, v in values.items())
        raise _refuse(f"the {fact} is recorded inconsistently: {detail}")
    return next(iter(distinct))


def _nan_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return a.shape == b.shape and bool(np.array_equal(a, b, equal_nan=True))


def _verify_raster(
    path: Path, kind: str, name: str, result: SurfaceResult, grid: PredictionGrid
) -> dict:
    """One written raster: exists BY NAME, values re-read and compared to the
    in-memory surface, tags compared to the grid and the estimator. Returns
    its identity (basename + recomputed sha256)."""
    if not path.is_file():
        raise _refuse(
            f"the {kind} surface for estimator {name!r} is missing: {path} does not "
            "exist — a manifest cannot record a hash for a file that was not written"
        )
    expected = (result.mu if kind == "prediction" else result.sd).astype(np.float32)
    with rasterio.open(path) as dataset:
        values = dataset.read(1)
        tags = dataset.tags()
        geometry = (tuple(dataset.transform)[:6], dataset.width, dataset.height)
    if not _nan_equal(values, expected):
        raise _refuse(
            f"the {kind} raster for {name!r} ({path.name}) does not hold the in-memory "
            "surface's values — refusing to record a hash for a file that describes "
            "a different surface"
        )
    if geometry != (grid.transform, grid.width, grid.height):
        raise _refuse(
            f"the {kind} raster for {name!r} has grid {geometry!r}, not the prediction "
            f"grid's {(grid.transform, grid.width, grid.height)!r}"
        )
    _require_equal(
        f"stack hash on {path.name}",
        raster_tag=tags.get("grid_stack_content_hash"),
        prediction_grid=grid.stack_content_hash,
    )
    _require_equal(
        f"estimator name on {path.name}", raster_tag=tags.get("estimator_name"), surface=name
    )
    _require_equal(f"surface kind on {path.name}", raster_tag=tags.get("surface_kind"), expected=kind)
    return {"file": path.name, "sha256": file_sha256(path)}


def _verify_sidecar(path: Path, name: str, result: SurfaceResult, grid: PredictionGrid) -> dict:
    if not path.is_file():
        raise _refuse(f"the provenance sidecar for estimator {name!r} is missing: {path}")
    record = json.loads(path.read_text())
    if record.get("surface") != result.summary():
        raise _refuse(
            f"the sidecar for {name!r} records a surface summary that differs from the "
            "in-memory surface's — the file does not describe this run"
        )
    if record.get("grid") != grid.identity():
        raise _refuse(f"the sidecar for {name!r} records a grid identity that is not this grid's")
    return record


def extend_run_manifest(
    base: RunManifest,
    *,
    matrix: TrainingMatrix,
    matrix_manifest: TrainingMatrixManifest,
    corpus_manifest: Mapping,
    stack_manifest: Mapping,
    grid: PredictionGrid,
    surfaces: Mapping[str, SurfaceResult],
    written: Mapping[str, Mapping[str, Path]],
    ts6: TS6Surface,
    agreements: Mapping[str, TS6Agreement],
    verdicts: Mapping[str, ClaimVerdict],
    claim_design: str,
    economic_results: Sequence[EconomicScenarioResult] = (),
    economic_differences: Sequence[EconomicDifferenceResult] | None = None,
    economics_dir: Path | str | None = None,
) -> RunManifest:
    """Extend the CV-stage RunManifest with Phase 3's outputs, asserting every
    link of the provenance chain by recomputation. Returns a NEW finalized
    manifest; `base` is not mutated.

    `written` is `write_surface`'s return per estimator (`{"prediction",
    "uncertainty", "provenance", "origin_sidecar"}` → Path). `verdicts` is
    one `evaluate_claim` result per design; `claim_design` names the one the
    caller declares as the claim's basis.
    """
    # ---- 0. the base record describes itself and has not been extended
    _require_self_consistent(base, "run manifest")
    if base.surfaces is not None or base.provenance_chain is not None:
        raise _refuse(
            f"run {base.run_id!r} has already been extended — extending twice would "
            "record one run's surfaces as two runs' provenance"
        )

    # ---- 1. the training matrix: arrays, manifest, and the run's quotation
    _require_self_consistent(matrix_manifest, "training-matrix manifest")
    recomputed_matrix = matrix_sha256(matrix)
    _require_equal(
        "training matrix's array hash",
        recomputed_from_arrays=recomputed_matrix,
        matrix_manifest=matrix_manifest.matrix_sha256,
        run_manifest_inputs=base.inputs.get("training_matrix", {}).get("matrix_sha256"),
    )
    _require_equal(
        "training-matrix artifact hash",
        matrix_manifest=matrix_manifest.content_hash,
        run_manifest_upstream=base.upstream_hashes.get("training_matrix"),
    )

    # ---- 2. the corpus: substance recomputed from the committed record
    corpus_hash = _require_equal(
        "corpus hash",
        recomputed_from_substance=CorpusManifest(**corpus_manifest).compute_content_hash(),
        corpus_manifest=corpus_manifest.get("content_hash"),
        matrix_manifest_upstream=matrix_manifest.upstream_hashes.get("corpus"),
        run_manifest_upstream=base.upstream_hashes.get("corpus"),
    )

    # E3.4 commit 3 — THE CORPUS BYTES. The corpus manifest describes the
    # corpus; nothing hashes master_observations.csv itself (BACKLOG §3, the
    # own-task entry that changes CorpusManifest's shape). Until that lands
    # the RUN pins the bytes it was trained from, recomputed here from the
    # file the corpus manifest names, so a hand-edit to the CSV changes this
    # record even though it changes no upstream hash.
    corpus_csv = _REPO_ROOT / str(corpus_manifest.get("corpus_path") or "")
    if not corpus_manifest.get("corpus_path") or not corpus_csv.is_file():
        raise _refuse(
            f"the corpus manifest names corpus_path {corpus_manifest.get('corpus_path')!r}, "
            "which is not a file — the run cannot pin the corpus bytes it was trained from"
        )
    corpus_csv_hash = file_sha256(corpus_csv)

    # HASH.1 commit 2: the stack substance must be PATH-FREE, asserted here
    # rather than assumed — a path that crept back under `dem` would make
    # every downstream hash directory-dependent again, silently.
    dem_records = [("dem", stack_manifest.get("dem") or {})] + [
        (f"layers[{i}].dem", (layer or {}).get("dem") or {})
        for i, layer in enumerate(stack_manifest.get("layers") or [])
    ]
    path_bearing = [where for where, record in dem_records if "path" in record]
    if path_bearing:
        raise _refuse(
            f"the feature-stack manifest embeds a DEM path at {path_bearing} — since "
            "HASH.1 the stack substance is path-free (the location lives in dem_path, "
            "outside the hash); a path inside it makes every downstream hash vary with "
            "the directory the run was built from"
        )

    # ---- 3. the feature stack: substance recomputed; the grid is ITS grid
    stack_hash = _require_equal(
        "feature-stack hash",
        recomputed_from_substance=FeatureStackManifest(**stack_manifest).compute_content_hash(),
        stack_manifest=stack_manifest.get("content_hash"),
        matrix_manifest_upstream=matrix_manifest.upstream_hashes.get("feature_stack"),
        run_manifest_upstream=base.upstream_hashes.get("feature_stack"),
        prediction_grid=grid.stack_content_hash,
    )
    dem_hash = _require_equal(
        "DEM hash",
        stack_manifest_upstream=(stack_manifest.get("upstream_hashes") or {}).get("dem"),
        prediction_grid=grid.dem_content_hash,
    )

    # ---- 4. the surfaces: every cross-validated estimator, every file, by name
    registry = list(base.inputs.get("registry") or [])
    for label, names in (("surfaces", surfaces), ("written files", written), ("agreements", agreements)):
        if set(names) != set(registry):
            raise _refuse(
                f"the {label} cover estimators {sorted(names)} but the run cross-validated "
                f"{sorted(registry)} — every estimator that reaches a surface must be the "
                "one that was cross-validated, and every cross-validated estimator must "
                "reach one (never cherry-picked)"
            )
    layer_origins = list((stack_manifest.get("layers_by_data_origin") or {}).keys())
    if not layer_origins:
        raise _refuse("the stack manifest records no layers_by_data_origin — the surface origin cannot be recomputed")
    expected_origin = compute_surface_origin(
        combine_origins(layer_origins).value, matrix_manifest.data_origin
    )

    surfaces_block: dict[str, dict] = {}
    output_hashes: dict[str, str] = {}
    origin_sidecars: set[Path] = set()

    def _record_output(path: Path, digest: str, key: str | None = None) -> None:
        # keyed by basename; the economics subdirectory passes its one constant
        # relative component explicitly (economics/<basename>) — never a run directory
        key = key or path.name
        if key in output_hashes and output_hashes[key] != digest:
            raise _refuse(f"two written files share the key {key!r} with different bytes")
        output_hashes[key] = digest

    for name in sorted(surfaces):
        result = surfaces[name]
        files = written[name]
        rasters = {}
        for kind in SURFACE_KINDS:
            path = Path(files[kind]) if kind in files else Path(f"<no {kind} path recorded for {name}>")
            rasters[kind] = _verify_raster(path, kind, name, result, grid)
            _record_output(path, rasters[kind]["sha256"])
        sidecar_path = Path(files.get("provenance", f"<no sidecar path recorded for {name}>"))
        sidecar = _verify_sidecar(sidecar_path, name, result, grid)
        if sidecar.get("data_origin") != expected_origin.value:
            raise _refuse(
                f"the sidecar for {name!r} declares data_origin {sidecar.get('data_origin')!r} "
                f"but combine_origins over the stack and matrix gives {expected_origin.value!r} "
                "— the written origin is not the computed one"
            )
        if sidecar.get("rasters") != {kind: rasters[kind]["file"] for kind in SURFACE_KINDS}:
            raise _refuse(f"the sidecar for {name!r} names rasters other than the ones written")
        sidecar_digest = file_sha256(sidecar_path)
        _record_output(sidecar_path, sidecar_digest)
        if "origin_sidecar" in files:
            origin_sidecars.add(Path(files["origin_sidecar"]))

        agreement = agreements[name]
        if agreement.estimator_name != name:
            raise _refuse(
                f"the agreement recorded under {name!r} identifies itself as "
                f"{agreement.estimator_name!r} — an agreement must describe the surface it is keyed by"
            )
        _require_equal(
            f"benchmark hash in {name}'s agreement",
            agreement_resampling=(agreement.resampling or {}).get("ts6_content_hash"),
            ts6_surface=ts6.content_hash,
        )

        # E5.5 commit 2 — THE FULL-DATA FIT. `build_surfaces` has recorded
        # each estimator's `provenance()` at the full-matrix fit since
        # E3.1+2 and nothing carried it: the manifest's per-fold fits live in
        # `cross_validation`, and the full-data variogram the no-information
        # contour depends on existed only in a walkthrough (E5.0 §3). An
        # estimator that reports no fitted state cannot be recorded as a
        # surface whose model a reader can see — refused by name.
        if not result.provenance:
            raise _refuse(
                f"the surface for {name!r} carries no estimator provenance — the full-data "
                "fit must be recordable (kriging's variogram, RF's read-back hyperparameters, "
                "the baseline's moments), or a reader cannot see the model behind the map"
            )
        surfaces_block[name] = {
            **result.summary(),
            "full_data_fit": _jsonable(result.provenance),
            "data_origin": expected_origin.value,
            "watermark": sidecar.get("watermark"),
            "publishable": sidecar.get("publishable"),
            "rasters": rasters,
            "sidecar": {"file": sidecar_path.name, "sha256": sidecar_digest},
        }

    for path in sorted(origin_sidecars):
        if not path.is_file():
            raise _refuse(f"the origin sidecar {path} ({SIDECAR_NAME}) is missing")
        _record_output(path, file_sha256(path))

    # ---- 5. the benchmark: identity recomputed from its bytes
    if ts6.content_hash is None:
        raise _refuse("the TS-6 surface carries no content_hash — its identity cannot be asserted")
    ts6_hash = _require_equal(
        "TS-6 raster hash",
        recomputed_from_bytes=file_sha256(Path(ts6.raster_path)),
        ts6_surface=ts6.content_hash,
    )

    # ---- 6. the verdicts: every design, never cherry-picked; the declared basis
    designs = [d["name"] for d in (base.cross_validation or {}).get("designs", [])]
    if set(verdicts) != set(designs):
        raise _refuse(
            f"verdicts cover designs {sorted(verdicts)} but the run executed {sorted(designs)} — "
            "E2.5's guard is recorded for every design or the record chooses one silently"
        )
    if claim_design not in verdicts:
        raise _refuse(
            f"claim_design {claim_design!r} is not a design this run executed ({sorted(designs)})"
        )
    for design, verdict in verdicts.items():
        if verdict.design != design:
            raise _refuse(f"the verdict recorded under {design!r} was evaluated for {verdict.design!r}")
        if verdict.data_origin != base.data_origin:
            raise _refuse(
                f"the verdict for {design!r} was evaluated on a run with data_origin "
                f"{verdict.data_origin!r}, not this run's {base.data_origin!r}"
            )

    provenance_chain = {
        "rule": (
            "every link below was RECOMPUTED from the artifact it names at emission "
            "and compared against every record of the same fact; none was copied"
        ),
        "links": {
            "corpus": {
                "content_hash": corpus_hash,
                "recomputed_from": "CorpusManifest substance (data/corpus/manifest.json)",
                "agrees_with": ["training_matrix.upstream_hashes.corpus", "run.upstream_hashes.corpus"],
                "verifiable_off_machine": True,
                "why": "the corpus manifest is committed and its substance embeds no path",
                "csv_file": corpus_csv.name,
                "csv_sha256": corpus_csv_hash,
                "csv_note": (
                    "the corpus BYTES, recomputed from the file corpus_path names; no upstream "
                    "artifact records this hash yet (BACKLOG §3), so it agrees with nothing "
                    "and pins the run to the bytes it was trained from"
                ),
            },
            "feature_stack": {
                "content_hash": stack_hash,
                "dem_content_hash": dem_hash,
                "recomputed_from": "FeatureStackManifest substance (<stack>/provenance.json)",
                "agrees_with": [
                    "training_matrix.upstream_hashes.feature_stack",
                    "run.upstream_hashes.feature_stack",
                    "prediction_grid.stack_content_hash",
                ],
                "verifiable_off_machine": True,
                "why": (
                    "since HASH.1 the substance embeds no path (asserted at emission); "
                    "it depends on the DEM bytes, the contract and registry versions, "
                    "and the recipes — the same everywhere"
                ),
                # the DEM's LOCATION is deliberately NOT quoted here: this block is
                # inside the run's substance, and a path in it would put the
                # directory back into the run hash one artifact downstream (found
                # by measuring the two-tree diff at HASH.1 commit 2: it did)
            },
            "training_matrix": {
                "content_hash": matrix_manifest.content_hash,
                "matrix_sha256": recomputed_matrix,
                "recomputed_from": "the matrix arrays (matrix_sha256) and the manifest's substance",
                "agrees_with": ["run.upstream_hashes.training_matrix", "run.inputs.training_matrix.matrix_sha256"],
                "verifiable_off_machine": "same-endianness hosts",
                "why": (
                    "quotes the now-portable feature_stack hash; matrix_sha256 hashes the "
                    "arrays in native byte order, so it reproduces across same-endianness "
                    "hosts and is not measured beyond them"
                ),
            },
            "ts6_benchmark": {
                "content_hash": ts6_hash,
                "source_id": ts6.source_id,
                "raster_file": Path(ts6.raster_path).name,
                "role_note": ts6.role_note,
                "data_origin": ts6.data_origin,
                "recomputed_from": "the benchmark raster's bytes",
                "agrees_with": ["ts6_agreement.*.resampling.ts6_content_hash"],
                "verifiable_off_machine": "not measured — a synthetic fixture today; G3.1 delivers the real raster",
            },
            "surfaces": {
                "files": len(output_hashes),
                "recomputed_from": (
                    "the written bytes; raster values re-read and compared to the in-memory "
                    "surfaces; sidecar summaries compared to the in-memory surfaces and grid"
                ),
                "agrees_with": ["output_hashes", "surfaces.*.rasters", "surfaces.*.sidecar"],
                "verifiable_off_machine": "directory-independent; cross-GDAL-version byte identity not measured",
                "why": (
                    "every raster's tags and every provenance sidecar quote the stack hash, "
                    "which no longer moves with the directory; whether the COG driver writes "
                    "identical bytes under another GDAL version has not been measured"
                ),
            },
        },
        "verifiable_off_machine": ["corpus", "feature_stack", "training_matrix (same-endianness)"],
        # THE FORMER LIMIT'S SCOPE, still a number: E3.4 measured 11 hash values
        # moving with the directory; HASH.1 commit 2 removed the path from the
        # stack substance and the two-directory tests now measure 0. The emitter
        # records the count it can stand behind — the assertion above is what
        # lets it say 0 rather than assume it.
        "path_dependent_hashes": {
            "count": 0,
            "was": 11,
            "basis": (
                "the feature-stack substance embeds no path (asserted at emission: no "
                "'path' key under dem or layers[*].dem); every downstream hash quotes "
                "the stack hash or the DEM bytes, neither of which depends on the directory"
            ),
            "measured_by": [
                "tests/test_run_manifest_extension.py::test_the_path_dependent_hash_count_equals_the_measured_two_directory_difference",
                "tests/test_engine_run.py::test_the_same_bytes_in_a_different_tree_reproduce_the_science_and_nothing_that_quotes_the_stack_hash",
            ],
            "remaining_limits": [
                "matrix_sha256 / coords fingerprints: native byte order (same-endianness hosts)",
                "raster bytes across GDAL versions: not measured",
                "inputs.environment is inside the run's content_hash by design (E3.4 commit 3)",
            ],
        },
        "limit": CHAIN_LIMIT_NOTE,
    }

    # ---- 6b. E5.5 commit 2 — THE TRAINING STATIONS, from the matrix object
    # this run was built on (its arrays are what `matrix_sha256` above was
    # recomputed from, so the chain already ties them to the manifest and the
    # base; no second check is made here — one below a structural guarantee
    # would be the unreachable-check sub-pattern). The coordinates are
    # CORPUS values, so the block's origin is the corpus's — combined over
    # the origins the corpus manifest admitted rows under — and NOT the
    # matrix's computed origin, which is the covariates' (SYNTHETIC today).
    corpus_origins = list((corpus_manifest.get("admitted_rows_by_data_origin") or {}).keys())
    if not corpus_origins:
        raise _refuse("the corpus manifest records no admitted_rows_by_data_origin — the stations' origin cannot be computed")
    coords = np.asarray(matrix.coords, dtype=float)
    if coords.shape != (len(matrix.station_ids), 2):
        raise _refuse(
            f"the training matrix carries {len(matrix.station_ids)} station ids and coordinates "
            f"of shape {coords.shape} — one (lon, lat) pair per station, or the record misaligns them"
        )
    training_stations = {
        "n": len(matrix.station_ids),
        "coord_columns": list(matrix.coord_columns),
        "station_ids": list(matrix.station_ids),
        "coordinates": {
            sid: [float(coords[i, 0]), float(coords[i, 1])] for i, sid in enumerate(matrix.station_ids)
        },
        "data_origin": combine_origins(corpus_origins).value,
        "origin_note": (
            "the CORPUS's origin (combine_origins over admitted_rows_by_data_origin): the "
            "coordinates are corpus values; the run's data_origin is the training matrix's, "
            "which the covariates taint"
        ),
        "source": (
            "the TrainingMatrix object this run was built on (CorpusCsvSampleSource -> "
            "assemble_training_matrix; station_ids and coords are inside matrix_sha256) — "
            "recorded so a viewer never re-implements the training gate against the CSV"
        ),
        "matrix_sha256": recomputed_matrix,
    }

    # ---- 7. E4.3 — the economics rasters, RESOLVED FROM E4.2's RECORD and
    # verified by recomputation; the block and the chain link
    economics_block = None
    if economics_dir is not None:
        economics_block = _verify_economics(
            Path(economics_dir),
            economic_results,
            economic_differences or (),
            expected_surface_origin=expected_origin.value,
            dem_data_origin=stack_manifest.get("dem_data_origin"),
            record_output=_record_output,
        )
        provenance_chain["links"]["economics"] = {
            "files": economics_block["n_files"],
            "recomputed_from": (
                "every raster's bytes (sha256) against the association record's; each "
                "raster's tags against its record entry (kind, scenario, estimator, z, "
                "counts); each record entry against the manifest's own economic_results; "
                "the origin by combine_origins; the terrain reason from the stack's "
                "declared DEM origin"
            ),
            "agrees_with": ["output_hashes (economics/*)", "economics.rasters", "economic_results.*.footprints.*.raster_file"],
            "verifiable_off_machine": "directory-independent; cross-GDAL-version byte identity not measured",
            "why": (
                "the same limit as the surfaces — the rasters quote the stack hash, which no "
                "longer moves with the directory (HASH.1); no path enters the block"
            ),
        }

    extended = base.model_copy(
        update={
            "economics": economics_block,
            "ts6_agreement": {name: agreements[name] for name in sorted(agreements)},
            "economic_results": list(economic_results),
            "economic_differences": (
                list(economic_differences) if economic_differences is not None else None
            ),
            "output_hashes": dict(sorted(output_hashes.items())),
            "prediction_grid": grid.identity(),
            "surfaces": surfaces_block,
            "training_stations": training_stations,
            "claim": {
                "design": claim_design,
                "verdicts": {design: verdicts[design].to_record() for design in sorted(verdicts)},
                "note": CLAIM_NOTE,
            },
            "provenance_chain": provenance_chain,
        }
    )
    extended.finalize()
    return extended


# ═══════════════════════════════════════════════ E4.3: the economics block

ECONOMICS_DIR_NAME = "economics"
ASSOCIATION_NAME = "economics.footprints.json"
ORIGIN_SIDECAR_NAME = "data_origin.yaml"
WATERMARK_REASONS_NOTE = (
    "two INDEPENDENT reasons with SEPARATE expiry conditions — terrain lifts at "
    "Checkpoint 1 (real bathymetry), economic_parameters at Checkpoint 4 (real Contract "
    "4 values) — and fixing one leaves the other; the computed data_origin beside them "
    "is correct and lossy, which is why they are recorded per reason"
)


def _verify_economics(
    economics_dir: Path,
    results: Sequence[EconomicScenarioResult],
    differences: Sequence[EconomicDifferenceResult],
    *,
    expected_surface_origin: str,
    dem_data_origin: str | None,
    record_output,
) -> dict:
    """E4.3: assemble the economics block by RESOLVING E4.2's association
    record and VERIFYING every claim in it by recomputation — never by
    re-deriving from filenames and never by trusting a record unhashed.

    What is recomputed: each raster's sha256 from its bytes (== the record's);
    each raster's tags (== the record's kind/scenario/estimator/z and counts);
    the set of rasters the manifest's own results name (== the record's ==
    the directory's .tif files, counted); each scenario's origin by
    combine_origins over the surfaces' computed origin and the cutoff's
    declared origin (== the result's == the record's — the laundering
    direction); the terrain reason's lifted state from the stack's declared
    DEM origin. The association record and the origin sidecar are then
    hashed into output_hashes, so the record the block resolved from is a
    link the chain HAS, not one it claims.
    """
    import rasterio

    from engine.prospectivity.provenance.origin import DataOrigin

    association_path = economics_dir / ASSOCIATION_NAME
    if not association_path.is_file():
        raise _refuse(
            f"the economics directory {economics_dir.name!r} carries no {ASSOCIATION_NAME} — "
            "the manifest resolves every economics raster FROM that record and cannot "
            "record a block without it"
        )
    record = json.loads(association_path.read_text())
    entries: dict[str, dict] = record.get("files") or {}
    on_disk = sorted(p.name for p in economics_dir.iterdir() if p.suffix == ".tif")
    if sorted(entries) != on_disk:
        raise _refuse(
            f"the association record names {len(entries)} raster(s) but the directory holds "
            f"{len(on_disk)}: only in record {sorted(set(entries) - set(on_disk))}, only on "
            f"disk {sorted(set(on_disk) - set(entries))} — a record that disagrees with the "
            "directory is the E4.2 misplaced-output catch recurring"
        )

    # the manifest's OWN results name the rasters: every named file must be in the record, and vice versa
    named: dict[str, tuple] = {}
    for result in results:
        for estimator, by_z in result.footprints.items():
            for z, summary in by_z.items():
                file = summary.get("raster_file")
                if not file:
                    raise _refuse(
                        f"scenario {result.scenario_name!r} records no raster_file for "
                        f"{estimator!r} at z={z} — a footprint without a file was computed and not written"
                    )
                named[file] = ("footprint", result.scenario_name, estimator, float(z), result)
    for difference in differences:
        for estimator, by_z in difference.footprints.items():
            for z, summary in by_z.items():
                file = summary.get("raster_file")
                if not file:
                    raise _refuse(
                        f"difference {difference.pair} records no raster_file for {estimator!r} at z={z}"
                    )
                named[file] = ("difference", tuple(difference.pair), estimator, float(z), difference)
    if set(named) != set(entries):
        raise _refuse(
            f"the manifest's results name {len(named)} economics raster(s) and the record "
            f"holds {len(entries)}: named but not recorded {sorted(set(named) - set(entries))}, "
            f"recorded but not named {sorted(set(entries) - set(named))}"
        )

    rasters_block: dict[str, dict] = {}
    for file in sorted(entries):
        entry = entries[file]
        kind, who, estimator, z, owner = named[file]
        path = economics_dir / file
        if not path.is_file():
            raise _refuse(f"the {kind} raster {file!r} is missing from {economics_dir.name!r}")
        digest = file_sha256(path)
        _require_equal(f"sha256 of {file}", recomputed_from_bytes=digest, association_record=entry.get("sha256"))
        with rasterio.open(path) as dataset:
            tags = dataset.tags()
            values = dataset.read(1)
        _require_equal(f"kind of {file}", raster_tag=tags.get("kind"), record=entry.get("kind"), manifest=kind)
        _require_equal(f"estimator of {file}", raster_tag=tags.get("estimator"), record=entry.get("estimator"), manifest=estimator)
        _require_equal(f"z of {file}", raster_tag=str(float(tags.get("z", "nan"))), record=str(float(entry.get("z"))), manifest=str(z))
        if kind == "footprint":
            _require_equal(f"scenario of {file}", raster_tag=tags.get("scenario"), record=entry.get("scenario"), manifest=who)
            n_minable = int(np.nansum(values == 1.0))
            _require_equal(
                f"n_minable of {file}",
                recomputed_from_values=str(n_minable),
                raster_tag=tags.get("n_minable"),
                record=str(entry.get("n_minable")),
                manifest=str(owner.footprints[estimator][str(z) if str(z) in owner.footprints[estimator] else f"{z:g}"]["n_minable"]),
            )
            origin_expected = combine_origins([expected_surface_origin, owner.cutoff["data_origin"]]).value
            _require_equal(
                f"data_origin of {file}",
                recomputed_by_combine_origins=origin_expected,
                raster_tag=tags.get("data_origin"),
                record=entry.get("data_origin"),
                manifest=owner.data_origin,
            )
        else:
            _require_equal(f"scenario_a of {file}", raster_tag=tags.get("scenario_a"), record=entry.get("scenario_a"), manifest=who[0])
            _require_equal(f"scenario_b of {file}", raster_tag=tags.get("scenario_b"), record=entry.get("scenario_b"), manifest=who[1])
            n_only_b = int(np.nansum(values == 2.0))
            _require_equal(
                f"n_only_b of {file}",
                recomputed_from_values=str(n_only_b),
                raster_tag=tags.get("n_only_b"),
                record=str((entry.get("counts") or {}).get("only_b")),
                manifest=str(owner.footprints[estimator][str(z) if str(z) in owner.footprints[estimator] else f"{z:g}"]["n_minable"]),
            )
            _require_equal(f"data_origin of {file}", raster_tag=tags.get("data_origin"), record=entry.get("data_origin"), manifest=owner.data_origin)
        # THE TWO REASONS, per artifact: the record's verdict must equal the manifest's,
        # and the terrain reason's state must be what the stack's declared origin implies
        verdict = entry.get("watermark") or {}
        reasons = {r.get("reason"): r for r in verdict.get("reasons", [])}
        if set(reasons) != {"terrain", "economic_parameters"}:
            raise _refuse(f"{file}'s record carries reasons {sorted(reasons)} — both independent reasons must be present")
        terrain_should_lift = dem_data_origin is not None and DataOrigin(dem_data_origin) is DataOrigin.MEASURED
        _require_equal(
            f"terrain reason of {file}",
            derived_from_stack_dem_origin=str(terrain_should_lift),
            record=str(reasons["terrain"].get("lifted")),
            manifest=str({r["reason"]: r["lifted"] for r in owner.watermark["reasons"]}["terrain"]),
        )
        _require_equal(
            f"economic_parameters reason of {file}",
            record=str(reasons["economic_parameters"].get("lifted")),
            manifest=str({r["reason"]: r["lifted"] for r in owner.watermark["reasons"]}["economic_parameters"]),
        )
        record_output(path, digest, key=f"{ECONOMICS_DIR_NAME}/{file}")
        rasters_block[file] = {
            "kind": kind,
            "scenario": who if kind == "footprint" else None,
            "pair": list(who) if kind == "difference" else None,
            "estimator": estimator,
            "z": z,
            "sha256": digest,
            "counts": {k: entry[k] for k in ("n_minable", "n_predictable", "fraction_of_predictable", "area_m2") if k in entry}
            if kind == "footprint"
            else {**(entry.get("counts") or {}), "difference_fraction_of_predictable": entry.get("difference_fraction_of_predictable"), "area_m2": entry.get("area_m2")},
            "watermark": {r["reason"]: {"lifted": r["lifted"], "lifted_by": r["lifted_by"]} for r in verdict.get("reasons", [])},
        }

    association_digest = file_sha256(association_path)
    record_output(association_path, association_digest, key=f"{ECONOMICS_DIR_NAME}/{ASSOCIATION_NAME}")
    origin_sidecar = economics_dir / ORIGIN_SIDECAR_NAME
    if not origin_sidecar.is_file():
        raise _refuse(f"the economics directory carries no {ORIGIN_SIDECAR_NAME} — its rasters are unclassified to the audit")
    record_output(origin_sidecar, file_sha256(origin_sidecar), key=f"{ECONOMICS_DIR_NAME}/{ORIGIN_SIDECAR_NAME}")

    return {
        "directory": ECONOMICS_DIR_NAME,
        "n_files": len(rasters_block) + 2,
        "n_footprint_rasters": sum(1 for r in rasters_block.values() if r["kind"] == "footprint"),
        "n_difference_rasters": sum(1 for r in rasters_block.values() if r["kind"] == "difference"),
        "association": {"file": ASSOCIATION_NAME, "sha256": association_digest, "resolved_from": "the record, not the filenames"},
        "scenarios": [
            {
                "name": r.scenario_name,
                "cutoff": r.cutoff,  # the DeclaredField shape: value WITH its declared origin
                "grade_metric": r.grade_metric,
                "confidence_levels": r.confidence_levels,
                "data_origin": r.data_origin,
                "watermark": r.watermark,
            }
            for r in results
        ],
        "difference_fraction_of_predictable": {
            "->".join(d.pair): {est: {z: s["fraction_of_predictable"] for z, s in by_z.items()} for est, by_z in d.footprints.items()}
            for d in differences
        },
        "rasters": rasters_block,
        "watermark_note": WATERMARK_REASONS_NOTE,
    }
