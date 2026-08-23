"""The READ-ONLY API (E5.1 commit 1) — it SERVES WHAT THE MANIFEST RECORDS.

    uvicorn services.api.app:app --factory   (with CCZ_RUNS_ROOT set), or
    python -m services.api.app <runs_root>

    runs_root/                      ◄── one or more run directories, each produced by
    ├── <run-a>/run_manifest.json        `python -m engine.prospectivity.harness` (E5.5)
    │   ├── *_prediction.tif …           and laid out as harness.RUN_LAYOUT states
    │   └── economics/ · features/
    └── <run-b>/…

    GET /runs                          every run, identified FROM ITS MANIFEST (run_id), never
    GET /runs/{run_id}                 from the directory name
    GET /runs/{run_id}/manifest        the record's BYTES, verbatim — a client can re-hash it
    GET /runs/{run_id}/cv-scores       cv_scores + cross_validation + the declarations
    GET /runs/{run_id}/ts6-agreement   the per-estimator mapping + the chain's benchmark link
    GET /runs/{run_id}/economics       the E4.3 block + economic_results + economic_differences
    GET /runs/{run_id}/claim           E2.5's verdicts as data, the design, the origin
    GET /runs/{run_id}/layers          THE LAYER CATALOG (commit 2; catalog.py) — 24 layers, the
                                       72-cell control grid, the verdict, the watermark forms
    GET /runs/{run_id}/files/{key}     ONLY a key in output_hashes; ETag = the recorded sha256

THREE RULES, each structural rather than a convention:

1. READ-ONLY OVER THE ROUTE TABLE. Only GET handlers are declared, and
   `tests/test_api.py` asserts it by enumerating `app.routes` — the
   framework's own table, never a list this module maintains — so a route
   added later with another method fails by name (the never-cherry-pick
   shape: enumerate from the registry, not from a declaration).

2. IT COMPUTES NOTHING, DERIVES NOTHING, RE-HASHES NOTHING. Every response is
   a field of the manifest as recorded, or the recorded bytes of a file the
   manifest names. A value the viewer needs that is not in the manifest is a
   MANIFEST question (E5.0 §3; E5.5 closed three), never something computed
   behind a URL — that would put a second source of truth at the edge of the
   system. The one thing checked at LOAD is that the directory IS a run: the
   manifest describes itself (`content_hash` recomputed once, the emitter's
   own `_require_self_consistent` rule — refusing a record that does not
   describe itself is not serving a derived value), it is EXTENDED (a CV-only
   manifest has no surfaces to serve), and every file it names exists. Files
   are not re-hashed; their recorded hash travels as the ETag.

3. THE FILES ENDPOINT RESOLVES FROM THE RECORD. A requested key is looked up
   in `output_hashes` BEFORE any path is formed, so a file that is on disk but
   not in the record (the covariate stack, an input raster, anything a
   traversal could name) is "not a recorded output" — the listing is not the
   record (E4.2's misplaced-raster lesson, read the other way round).

WHAT IT DEPENDS ON: a run directory exists only because E5.5 built the
harness — before it, every surface lived in a pytest tmp dir (E5.0 §0). The
API fails clearly on a directory that is not a run rather than serving an
empty catalog: a runs root with no run is refused, and so is a subdirectory
without a manifest, by name.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.harness import STACK_DIR
from services.api.catalog import build_catalog

MANIFEST_NAME = "run_manifest.json"
RUNS_ROOT_ENV = "CCZ_RUNS_ROOT"
MEDIA_TYPES = {".tif": "image/tiff", ".json": "application/json", ".yaml": "application/yaml"}


class NotARun(ValueError):
    """The directory handed to the API is not (or does not only hold) run
    directories the harness produced — refused by name, never served empty."""


@dataclass(frozen=True)
class LoadedRun:
    directory: Path
    raw_bytes: bytes  # the manifest's bytes, served verbatim
    raw: dict  # the same, parsed — every endpoint below is a field of this
    manifest: RunManifest
    catalog: dict  # E5.1 commit 2: built once at load, from the manifest and the record it names


def load_run(directory: Path) -> LoadedRun:
    path = directory / MANIFEST_NAME
    if not path.is_file():
        raise NotARun(f"{directory} holds no {MANIFEST_NAME} — not a run directory (E5.5's RUN_LAYOUT)")
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    manifest = RunManifest(**raw)
    if manifest.content_hash is None:
        raise NotARun(f"{path}: the manifest is not finalized (content_hash is None)")
    if manifest.compute_content_hash() != manifest.content_hash:
        raise NotARun(
            f"{path}: the manifest's content_hash does not match its own contents — it was "
            "mutated after finalize(); refusing to serve a record that does not describe itself"
        )
    if manifest.surfaces is None or manifest.provenance_chain is None:
        raise NotARun(
            f"{path}: the manifest is NOT EXTENDED (no surfaces, no provenance chain) — a "
            "CV-only record has no layers to serve; the viewer reads a directory the harness produced"
        )
    missing = [key for key in manifest.output_hashes if not (directory / key).is_file()]
    if missing:
        raise NotARun(
            f"{directory}: the manifest names {len(missing)} output file(s) that do not exist: "
            f"{missing[:5]} — a run directory is served whole or not at all"
        )
    return LoadedRun(directory=directory, raw_bytes=raw_bytes, raw=raw, manifest=manifest, catalog=build_catalog(raw, directory))


def load_runs(runs_root: Path) -> dict[str, LoadedRun]:
    runs_root = Path(runs_root)
    if not runs_root.is_dir():
        raise NotARun(f"{runs_root} is not a directory")
    candidates = sorted(p for p in runs_root.iterdir() if p.is_dir())
    if (runs_root / MANIFEST_NAME).is_file():
        raise NotARun(
            f"{runs_root} is itself a run directory — hand the API the directory that CONTAINS "
            "run directories (runs_root/<run>/run_manifest.json)"
        )
    if not candidates:
        raise NotARun(f"{runs_root} holds no run directories — nothing to serve, and an empty catalog would not say so")
    runs: dict[str, LoadedRun] = {}
    for directory in candidates:
        run = load_run(directory)  # a subdirectory that is not a run is refused, not skipped
        if run.manifest.run_id in runs:
            raise NotARun(
                f"two run directories carry run_id {run.manifest.run_id!r} "
                f"({runs[run.manifest.run_id].directory.name}, {directory.name}) — the URL key is the "
                "manifest's run_id and must be unique under one root"
            )
        runs[run.manifest.run_id] = run
    return runs


def _summary(run: LoadedRun) -> dict:
    m = run.manifest
    return {
        "run_id": m.run_id,
        "content_hash": m.content_hash,
        "schema_version": m.schema_version,
        "generated_at": run.raw.get("generated_at"),
        "data_origin": m.data_origin,
        "seed": m.seed,
        "claim_design": (m.claim or {}).get("design"),
        "estimators": list((m.inputs or {}).get("registry") or []),
        "designs": [d["name"] for d in (m.cross_validation or {}).get("designs", [])],
        "publishable": sorted({bool(s.get("publishable")) for s in (m.surfaces or {}).values()}),
        "n_output_files": len(m.output_hashes),
        "endpoints": [
            f"/runs/{m.run_id}/{part}"
            for part in ("manifest", "layers", "cv-scores", "ts6-agreement", "economics", "claim", "files/{key}")
        ],
    }


def create_app(runs_root: Path | str | None = None) -> FastAPI:
    root = Path(runs_root if runs_root is not None else os.environ.get(RUNS_ROOT_ENV, ""))
    if str(root) in ("", "."):
        raise NotARun(f"no runs root: pass one to create_app() or set {RUNS_ROOT_ENV}")
    runs = load_runs(root)  # refused here, at construction — never an empty catalog

    app = FastAPI(
        title="CCZ prospectivity engine — read-only run API",
        description="Serves what the run manifest records. Computes nothing. Every output is watermarked until Checkpoints 1/3/4.",
        version="E5.1",
    )

    def _run(run_id: str) -> LoadedRun:
        try:
            return runs[run_id]
        except KeyError:
            raise HTTPException(status_code=404, detail=f"no run {run_id!r}; known: {sorted(runs)}") from None

    @app.get("/runs")
    def list_runs() -> list[dict]:
        return [_summary(run) for run in runs.values()]

    @app.get("/runs/{run_id}")
    def run_summary(run_id: str) -> dict:
        return _summary(_run(run_id))

    @app.get("/runs/{run_id}/manifest")
    def manifest(run_id: str) -> Response:
        run = _run(run_id)
        return Response(
            content=run.raw_bytes,
            media_type="application/json",
            headers={"ETag": f'"{run.manifest.content_hash}"', "X-Content-Hash": run.manifest.content_hash},
        )

    @app.get("/runs/{run_id}/cv-scores")
    def cv_scores(run_id: str) -> dict:
        raw = _run(run_id).raw
        return {
            key: raw.get(key)
            for key in ("cv_scores", "cross_validation", "estimator_declarations", "claim_eligible_designs", "scores_first_visible", "scores_first_visible_note")
        }

    @app.get("/runs/{run_id}/ts6-agreement")
    def ts6_agreement(run_id: str) -> dict:
        raw = _run(run_id).raw
        return {
            "ts6_agreement": raw.get("ts6_agreement"),
            "ts6_benchmark": ((raw.get("provenance_chain") or {}).get("links") or {}).get("ts6_benchmark"),
        }

    @app.get("/runs/{run_id}/economics")
    def economics(run_id: str) -> dict:
        raw = _run(run_id).raw
        return {key: raw.get(key) for key in ("economics", "economic_results", "economic_differences")}

    @app.get("/runs/{run_id}/claim")
    def claim(run_id: str) -> dict:
        raw = _run(run_id).raw
        return {key: raw.get(key) for key in ("claim", "claim_eligible_designs", "data_origin")}

    @app.get("/runs/{run_id}/layers")
    def layers(run_id: str) -> dict:
        """THE LAYER CATALOG (commit 2) — see services/api/catalog.py."""
        return _run(run_id).catalog

    @app.get("/runs/{run_id}/files/{key:path}")
    def recorded_file(run_id: str, key: str) -> FileResponse:
        run = _run(run_id)
        digest = run.manifest.output_hashes.get(key)  # THE RECORD FIRST; no path is formed for an unknown key
        if digest is None:
            raise HTTPException(
                status_code=404,
                detail=f"{key!r} is not a recorded output of run {run_id!r} (output_hashes names "
                f"{len(run.manifest.output_hashes)} files; {MANIFEST_NAME} is at /manifest; "
                f"{STACK_DIR}/ is identified as one artifact by the stack hash and is not served per file)",
            )
        path = run.directory / key
        return FileResponse(
            path,
            media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream"),
            headers={"ETag": f'"{digest}"', "X-Content-Hash": digest},
        )

    return app


def app() -> FastAPI:  # uvicorn --factory entry: the root from the environment
    return create_app()


if __name__ == "__main__":
    import uvicorn

    if len(sys.argv) != 2:
        sys.exit(f"usage: python -m services.api.app <runs_root>   (or set {RUNS_ROOT_ENV} and use --factory)")
    uvicorn.run(create_app(sys.argv[1]), host="127.0.0.1", port=8000)
