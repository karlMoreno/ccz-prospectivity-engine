#!/usr/bin/env python3
"""
demo_alpha.py — the whole alpha, phase by phase, each with its input and output.

Companion: docs/DEMO.md holds the same steps as copy-paste commands, so the
demo is recreatable without this script. `demo.py` (Phase 1 only) remains the
deep-dive into ingestion; this script runs the full line:

  STEP 1  PHASE 1   two published .tab files  ->  the 108-row corpus (rebuilt live, byte-identical)
  STEP 2  PHASE 1   a declared-SYNTHETIC DEM  ->  the 8-covariate terrain stack
  STEP 3  PHASES 2-4  one command             ->  a complete run directory (the E5.5 harness)
  STEP 4  PHASE 2   the run's record          ->  spatial CV vs the baseline, and the guard REFUSING
  STEP 5  PHASE 3   the run's record          ->  paired prediction+uncertainty surfaces, TS-6 comparison
  STEP 6  PHASE 4   the run's record          ->  economic footprints and the scenario difference
  STEP 7  PHASE 5   the run directory         ->  verified by recomputation (hashes, links, verdict sets)
  STEP 8  PHASE 5   the run directory         ->  served: the API + the viewer, checked through the URL

Run from the repo root (after `pip install -e ".[dev]"`):

  python demo_alpha.py                    the whole demo; the viewer stays up until Ctrl+C
  python demo_alpha.py --pause            stop for Enter between steps (presenting)
  python demo_alpha.py --full             the harness's real default: all four CV designs (~150 s vs ~40 s)
  python demo_alpha.py --no-serve         skip step 8's server
  python demo_alpha.py --out outputs/demo where the run lands (default; gitignored)

HONESTY, FIRST: every surface this demo produces is computed on a SYNTHETIC
DEM against a SYNTHETIC TS-6 fixture with AUTHORED placeholder economics, and
the claim guard REFUSES to call any of it a validated claim. That refusal is
not a failure of the demo — it is the deliverable. The machinery is real; the
inputs await Checkpoints 1 (real bathymetry), 3 (digitized TS-6) and 4 (real
economics), and the day they land, the same commands produce the same record
with a different verdict.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
W = 78
PAUSE = False
PORT = 8765


# ---------------------------------------------------------------- presentation
def banner(step: int, phase: str, text: str) -> None:
    print("\n" + "=" * W)
    print(f"  STEP {step}  ({phase})  {text}")
    print("=" * W)


def io_line(kind: str, text: str) -> None:
    print(f"  {kind:<8} {text}")


def ok(text: str) -> None:
    print(f"  [OK]     {text}")


def info(text: str) -> None:
    print(f"           {text}")


def warn(text: str) -> None:
    print(f"  [!]      {text}")


def refused(text: str) -> None:
    print(f"  [REFUSED — correct]  {text}")


def cmd(text: str) -> None:
    print(f"  $ {text}")


def pause() -> None:
    if PAUSE:
        input("\n           -- press Enter --")


# ------------------------------------------------- STEP 1: Phase 1 — ingestion
def step1_corpus() -> None:
    banner(1, "PHASE 1", "Two published files in, the corpus out — rebuilt live")
    from engine.prospectivity.ingestion.corpus_builder import build_corpus, write_corpus_csv

    io_line("INPUT", "data/sources/*.tab — the two PANGAEA datasets, hash-verified on read")
    for tab in sorted((REPO / "data" / "sources").glob("*.tab")):
        info(f"  {tab.name}  ({tab.stat().st_size:,} B)")
    corpus = build_corpus()
    ok(f"built {len(corpus)} observation rows from the raw files")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        rebuilt = Path(tmp) / "rebuilt.csv"
        write_corpus_csv(corpus, rebuilt)
        committed = REPO / "data" / "corpus" / "master_observations.csv"
        if rebuilt.read_bytes() == committed.read_bytes():
            ok("byte-identical to the committed corpus — anyone who clones gets these numbers")
        else:
            warn("differs from the committed corpus (uncommitted changes?)")

    manifest = json.loads((REPO / "data" / "corpus" / "manifest.json").read_text())
    io_line("OUTPUT", "data/corpus/master_observations.csv + manifest.json")
    info(f"rows by evidence class: {manifest['rows_by_evidence_class']}")
    info(f"training-eligible: {manifest['training_eligible_count']} of 36 MASS rows "
         "(one box core is qa-flagged and the gate excludes it)")
    info("the rule the gate enforces: train on MASS only — COUNT/COVER/GRID never become kg/m²")
    pause()


# ------------------------------------------------- STEP 2: Phase 1 — terrain
def step2_terrain(work: Path) -> tuple[Path, Path]:
    banner(2, "PHASE 1", "A declared-SYNTHETIC DEM in, the 8-covariate stack out")
    from engine.prospectivity.features.stack import build_covariate_stack
    from engine.prospectivity.provenance.origin import DataOrigin
    from tests.fixtures.rasters import write_synthetic_bathymetry, write_synthetic_ts6_raster

    dem, ts6 = work / "dem.tif", work / "ts6.tif"
    write_synthetic_bathymetry(dem)
    write_synthetic_ts6_raster(ts6)
    io_line("INPUT", f"{dem.relative_to(REPO)} — SYNTHETIC by declaration (seeded generator; "
                     "real GEBCO replaces it at Checkpoint 1 with --dem-data-origin MEASURED)")
    written = build_covariate_stack(dem, work / "stack_preview", dem_data_origin=DataOrigin.SYNTHETIC)
    stack = json.loads(written["provenance"].read_text())
    io_line("OUTPUT", f"{len(stack['layers'])} covariate rasters + a content-hashed stack manifest")
    info("layers: " + ", ".join(layer["name"] for layer in stack["layers"]))
    info(f"stack content_hash: {stack['content_hash'][:32]}…  (path-free since HASH.1: the same "
         "bytes hash the same in any directory)")
    info("optional picture:  python -m engine.prospectivity.features.plot_stack "
         f"{dem.relative_to(REPO)} outputs/demo --dem-data-origin SYNTHETIC")
    pause()
    return dem, ts6


# --------------------------------- STEP 3: Phases 2–4 — the one-command harness
def step3_harness(work: Path, dem: Path, ts6: Path, full: bool) -> Path:
    banner(3, "PHASES 2–4", "One command: corpus + DEM in, a complete run directory out")
    from engine.prospectivity import harness

    out = work / "runs" / "demo"
    designs = None if full else "leave_one_cluster_out,leave_one_site_out,random_k_fold"
    argv = [
        "--dem", str(dem), "--dem-data-origin", "SYNTHETIC",
        "--ts6", str(ts6), "--ts6-data-origin", "SYNTHETIC",
        "--out", str(out), "--run-id", "demo",
    ] + ([] if designs is None else ["--designs", designs])
    io_line("INPUT", "the committed corpus, the DEM and the TS-6 fixture above")
    shown = [str(Path(a).relative_to(REPO)) if a.startswith(str(REPO)) else a for a in argv]
    cmd("python -m engine.prospectivity.harness " + " ".join(shown))
    if not full:
        info("(--full runs the harness's real default — all four CV designs, ~150 s; "
             "this demo run keeps three, ~40 s; the surfaces are identical either way)")
    t0 = time.perf_counter()
    code = harness.main(argv)
    assert code == 0
    files = [p for p in out.rglob("*") if p.is_file()]
    io_line("OUTPUT", f"{out.relative_to(REPO)} — {len(files)} files, "
                      f"{sum(p.stat().st_size for p in files):,} B, in {time.perf_counter() - t0:.0f} s")
    info("surfaces + sidecars, economics/ (18 rasters + record), export/ (browser-facing "
         "flat arrays), features/stack/, and run_manifest.json — the record of everything")
    pause()
    return out


# ------------------------------------------------- STEP 4: Phase 2, from the record
def step4_cv(out: Path) -> dict:
    banner(4, "PHASE 2", "Spatial cross-validation vs the baseline — and the guard REFUSING")
    manifest = json.loads((out / "run_manifest.json").read_text())
    io_line("INPUT", "the run's own record (run_manifest.json) — nothing recomputed here")

    rows = manifest["cv_scores"]
    designs = [d["name"] for d in manifest["cross_validation"]["designs"]]
    print()
    info(f"{'design':<24} {'estimator':<18} {'mean RMSE over folds (kg/m²)':>30}")
    for design in designs:
        for est in manifest["inputs"]["registry"]:
            values = [r["metric_value"] for r in rows
                      if r["cv_strategy"] == design and r["estimator_name"] == est
                      and r["metric_name"] == "rmse" and r["metric_value"] is not None]
            if values:
                info(f"{design:<24} {est:<18} {sum(values) / len(values):>30.2f}")
    info("across the two clusters (~991 km apart) kriging ≈ the baseline BY GEOMETRY — the fold")
    info("measures how much the clusters differ, not the models (the two-fold theorem, E2.4)")

    print()
    io_line("OUTPUT", "the claim verdict, per design — E2.5's guard, refusing for named reasons")
    for design, verdict in manifest["claim"]["verdicts"].items():
        failing = [p["precondition"] for p in verdict["preconditions"] if not p["passed"]]
        passing = sum(p["passed"] for p in verdict["preconditions"])
        refused(f"{design}: failing {failing}, passing {passing}")
    info("five of six preconditions PASS on the claim design — the guard discriminates; it is")
    info("not a blanket refusal. What fails is real: no acceptance gate existed before the")
    info("scores (the pre-registration clock), and the run is watermarked SYNTHETIC besides.")
    pause()
    return manifest


# ------------------------------------------------- STEP 5: Phase 3, from the record
def step5_surfaces(manifest: dict) -> None:
    banner(5, "PHASE 3", "Paired prediction + uncertainty surfaces, and the TS-6 comparison")
    io_line("INPUT", "the same record — the surfaces block and the TS-6 agreement")
    for name, s in manifest["surfaces"].items():
        info(f"{name:<18} mu [{s['mu_min']:.2f}, {s['mu_max']:.2f}]  sd [{s['sd_min']:.2f}, "
             f"{s['sd_max']:.2f}]  {s['n_distinct_values']} distinct values  "
             f"({s['n_predicted']} cells + {s['n_masked']} masked)")
    fit = manifest["surfaces"]["ordinary_kriging"]["full_data_fit"]
    info(f"kriging's fitted range: {fit['range_km']:.1f} km, AT the candidate ceiling (a lower "
         "bound) — only 34 of 2,880 cells sit within one range of any station")
    print()
    io_line("OUTPUT", "one agreement per estimator against the TS-6 raster")
    for name, a in manifest["ts6_agreement"].items():
        r = a["spatial_correlation"]
        info(f"{name:<18} mean diff {a['mean_difference']:+.2f}  rmse {a['rmse']:.2f}  "
             f"r {('undefined' if r is None else f'{r:.3f}')}")
    warn(f"benchmark caveat, from the record itself: {manifest['ts6_agreement']['ordinary_kriging']['benchmark_uncertainty_note']}")
    pause()


# ------------------------------------------------- STEP 6: Phase 4, from the record
def step6_economics(manifest: dict) -> None:
    banner(6, "PHASE 4", "Economic footprints and the scenario difference — placeholders, marked")
    io_line("INPUT", "Contract 4's two scenarios (AUTHORED placeholder cutoffs, illustrative only)")
    for s in manifest["economics"]["scenarios"]:
        c = s["cutoff"]
        info(f"{s['name']:<22} cutoff {c['value']} {c['units']}  (data_origin {c['data_origin']})")
    io_line("OUTPUT", "12 footprint rasters + 6 difference maps, all recorded and hash-verified")
    result = manifest["economic_results"][0]["footprints"]["ordinary_kriging"]["0.0"]
    info(f"every footprint: {result['n_minable']:,} of {result['n_predictable']:,} predictable "
         f"cells minable ({result['fraction_of_predictable']:.0%}) — and every difference map is EMPTY")
    info("that is a property of the placeholder cutoffs sitting below the training mean,")
    info("not of the seafloor; the record says so, twice, per artifact")
    for reason in manifest["economics"]["scenarios"][0]["watermark"]["reasons"]:
        warn(f"watermark reason '{reason['reason']}': UNLIFTED — lifts at {reason['lifted_by']}")
    pause()


# ------------------------------------------------- STEP 7: Phase 5 — verification
def step7_verify(out: Path) -> None:
    banner(7, "PHASE 5", "The run directory verified by recomputation — the CI job's own step")
    from engine.prospectivity.verify_run import verify

    io_line("INPUT", f"{out.relative_to(REPO)} — the directory, as bytes on disk")
    cmd(f"python -m engine.prospectivity.verify_run {out.relative_to(REPO)}")
    report = verify(out)
    io_line("OUTPUT", "every hash recomputed and compared to the record")
    ok(f"{report['output_files_verified']} output files hash exactly as the manifest records")
    ok(f"links recomputed from substance: {', '.join(report['links_recomputed'])}")
    ok(f"the verdict re-run per design matches the committed expectation "
       f"(it fails only if the sets MOVE — e.g. the day a checkpoint lands)")
    info(f"manifest content_hash: {report['content_hash'][:32]}…")
    pause()


# ------------------------------------------------- STEP 8: Phase 5 — the viewer
def step8_serve(out: Path, serve: bool) -> None:
    banner(8, "PHASE 5", "The run served: the read-only API and the viewer, checked through the URL")
    runs_root = out.parent
    url = f"http://127.0.0.1:{PORT}"
    io_line("INPUT", f"the runs root {runs_root.relative_to(REPO)} (the API refuses anything that is not a run)")
    cmd(f"CCZ_RUNS_ROOT={runs_root.relative_to(REPO)} uvicorn services.api.app:app --factory --port {PORT}")
    env = dict(os.environ, CCZ_RUNS_ROOT=str(runs_root))
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "services.api.app:app", "--factory",
         "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
        env=env, cwd=REPO,
    )
    try:
        import httpx2

        client = httpx2.Client(base_url=url, timeout=5.0)
        for _ in range(60):
            try:
                if client.get("/runs").status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            warn("the server did not come up; see its output above")
            return

        sys.path.insert(0, str(REPO))
        from deploy.verify_deployment import checks

        report = checks(lambda p: client.get(p), lambda p: client.post(p))
        io_line("OUTPUT", "the deployment checks, run through the URL (deploy/verify_deployment.py)")
        ok(f"the page serves with its {report['pins']}")
        ok(f"verdict through the URL: {report['verdict']['headline'][:70]}…")
        ok(f"layers: {report['layers']['n']} ({report['layers']['surface']} surface, "
           f"{report['layers']['economics']} economics) · no-information: {report['layers']['no_information']}")
        ok(f"stations: {report['layers']['stations']} · context: {', '.join(report['context'])}")
        ok(report["refusals"])
        print()
        print(f"  OPEN THE VIEWER:  {url}/")
        info("what to look at: the verdict banner (both halves, on load, nothing closes it);")
        info("the striped no-information region clearing only around the two station clusters;")
        info("the hatched mask, distinct from it; the paired σ in the legend and every hover;")
        info("switch the Layer to a footprint — the UNIFORM banner explains the identical maps")
        if serve:
            print()
            info("serving until Ctrl+C …")
            try:
                server.wait()
            except KeyboardInterrupt:
                pass
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


# ------------------------------------------------------------------------ main
def main() -> int:
    global PAUSE
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pause", action="store_true")
    parser.add_argument("--full", action="store_true", help="all four CV designs (the harness default, ~150 s)")
    parser.add_argument("--no-serve", action="store_true", help="skip step 8's server")
    parser.add_argument("--out", type=Path, default=REPO / "outputs" / "demo",
                        help="working directory (default outputs/demo — gitignored)")
    args = parser.parse_args()
    PAUSE = args.pause

    work = args.out.resolve()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    print("=" * W)
    print("  CCZ PROSPECTIVITY ENGINE — the alpha, phase by phase")
    print("  Every output below is WATERMARKED and the claim guard REFUSES — by design.")
    print("  The machinery is real; the honest inputs arrive at Checkpoints 1, 3 and 4.")
    print("=" * W)

    step1_corpus()
    dem, ts6 = step2_terrain(work)
    out = step3_harness(work, dem, ts6, args.full)
    manifest = step4_cv(out)
    step5_surfaces(manifest)
    step6_economics(manifest)
    step7_verify(out)
    step8_serve(out, serve=not args.no_serve)

    print("\n" + "=" * W)
    print("  Done. The record of everything above is one file:")
    print(f"    {out.relative_to(REPO)}/run_manifest.json")
    print("  The full test suite (676 tests) is the footnote:  pytest -q")
    print("=" * W)
    return 0


if __name__ == "__main__":
    sys.exit(main())
