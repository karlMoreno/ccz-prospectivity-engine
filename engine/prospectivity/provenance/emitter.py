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

THE CHAIN'S KNOWN LIMIT IS IN THE OUTPUT. The E2.4 audit (row M) measured
that `FeatureStackManifest`'s substance embeds the caller-supplied DEM path
string nine times, so of the run's three upstream hashes only the CORPUS is
verifiable off the machine that wrote it (BACKLOG §3, trigger before
Checkpoint 1). That is not this task's to fix — but a chain that claims more
than it delivers is exactly the defect that entry exists to prevent, so the
limit is stated in `provenance_chain`, where a manifest reader meets it,
and not only in a doc. Measured here for the first time: the limit REACHES
EVERY OUTPUT FILE, because each raster's tags and each sidecar carry the
stack hash (`test_run_manifest_extension.py` pins this; when the BACKLOG
fix lands, that test goes red and this block's claim must change with it).

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
from engine.prospectivity.validation.runner import matrix_sha256

SURFACE_KINDS = ("prediction", "uncertainty")

# THE LIMIT, stated where a manifest reader meets it.
CHAIN_LIMIT_NOTE = (
    "Every hash in this chain was RECOMPUTED from its artifact at emission and "
    "is checkable on the machine that wrote it. Off that machine, ONLY the corpus "
    "link is verifiable: FeatureStackManifest's substance embeds the caller-"
    "supplied DEM path string (nine times), so the feature_stack hash — and "
    "everything that quotes it: the training_matrix hash, this run's "
    "content_hash, every raster's tags and every sidecar — changes with the "
    "directory the stack was built from, for reasons unrelated to the terrain. "
    "Recorded in docs/BACKLOG.md §3 (trigger: before Checkpoint 1). A reader "
    "elsewhere can verify ORIGIN for the corpus and CONSISTENCY for the rest."
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

    def _record_output(path: Path, digest: str) -> None:
        if path.name in output_hashes and output_hashes[path.name] != digest:
            raise _refuse(f"two written files share the basename {path.name!r} with different bytes")
        output_hashes[path.name] = digest

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

        surfaces_block[name] = {
            **result.summary(),
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
                "verifiable_off_machine": False,
                "why": (
                    "the substance embeds the caller-supplied DEM path string nine times "
                    "(E2.4 audit row M; BACKLOG §3, trigger before Checkpoint 1)"
                ),
            },
            "training_matrix": {
                "content_hash": matrix_manifest.content_hash,
                "matrix_sha256": recomputed_matrix,
                "recomputed_from": "the matrix arrays (matrix_sha256) and the manifest's substance",
                "agrees_with": ["run.upstream_hashes.training_matrix", "run.inputs.training_matrix.matrix_sha256"],
                "verifiable_off_machine": False,
                "why": (
                    "quotes the feature_stack hash; matrix_sha256 over the arrays itself "
                    "reproduces (native byte order — same-endianness hosts)"
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
                "verifiable_off_machine": False,
                "why": (
                    "every raster's tags and every sidecar carry the stack hash, so the "
                    "feature_stack limit reaches every output file (measured at E3.4)"
                ),
            },
        },
        "verifiable_off_machine": ["corpus"],
        "limit": CHAIN_LIMIT_NOTE,
    }

    extended = base.model_copy(
        update={
            "ts6_agreement": {name: agreements[name] for name in sorted(agreements)},
            "economic_results": list(economic_results),
            "output_hashes": dict(sorted(output_hashes.items())),
            "prediction_grid": grid.identity(),
            "surfaces": surfaces_block,
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
