# DEMO — the alpha, phase by phase, with each phase's input and output

Two ways to run it:

- **One command:** `python demo_alpha.py` — every step below, ending with the
  viewer served at `http://127.0.0.1:8765/` (add `--pause` to present it,
  `--full` for all four CV designs, `--no-serve` to skip the server).
- **By hand:** the steps below, copy-paste, from the repo root. Each states
  its INPUT and OUTPUT so the pipeline's shape is visible: published files on
  the left, a verified, watermarked, *refused* run on the right.

`demo.py` (separate) remains the Phase-1 deep dive — one box core followed
through every station of the ingestion line.

**Read this first:** every surface below is computed on a SYNTHETIC DEM,
compared against a SYNTHETIC TS-6 fixture, cut by AUTHORED placeholder
economics — and the claim guard **refuses** to call any of it a validated
claim. That refusal is the deliverable. The demo shows real machinery
carrying honest labels; the honest *inputs* arrive at Checkpoints 1 (real
GEBCO bathymetry), 3 (digitized TS-6) and 4 (real economics), and the same
commands then produce the same record with a different verdict.

---

## 0. Setup (once)

**Input:** a clone of this repo. **Output:** a working environment.

```bash
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]" --only-binary=:all:
```

All commands below assume the venv is active (or prefix with `.venv/bin/`).

---

## 1. PHASE 1 — ingestion: two published files → the corpus

**Input:** `data/sources/*.tab` — the two PANGAEA datasets (SO268 box cores;
the per-nodule dataset), hash-verified on read: a byte changed in either file
is a refusal, not a warning.

```bash
python - <<'EOF'
from engine.prospectivity.ingestion.corpus_builder import build_corpus, write_corpus_csv
import tempfile, pathlib
corpus = build_corpus()
with tempfile.TemporaryDirectory() as tmp:
    rebuilt = pathlib.Path(tmp) / "rebuilt.csv"
    write_corpus_csv(corpus, rebuilt)
    same = rebuilt.read_bytes() == pathlib.Path("data/corpus/master_observations.csv").read_bytes()
print(len(corpus), "rows; byte-identical to the committed corpus:", same)
EOF
```

**Output:** the 108-row corpus (36 events × MASS/COUNT/COVER), byte-identical
to `data/corpus/master_observations.csv`. **What it shows:** reproducibility
(anyone who clones gets these numbers) and the evidence-class discipline —
35 of 36 MASS rows are training-eligible (one box core is qa-flagged);
COUNT/COVER/GRID never become kg/m². The full narrative: `python demo.py`.

---

## 2. PHASE 1 — terrain: a declared DEM → the 8-covariate stack

**Input:** a DEM **with a declared origin**. Today that is the seeded
synthetic generator (declared `SYNTHETIC`); at Checkpoint 1 it is real GEBCO,
same commands, `MEASURED`.

```bash
mkdir -p outputs/demo
python - <<'EOF'
from pathlib import Path
from tests.fixtures.rasters import write_synthetic_bathymetry, write_synthetic_ts6_raster
write_synthetic_bathymetry(Path("outputs/demo/dem.tif"))
write_synthetic_ts6_raster(Path("outputs/demo/ts6.tif"))
EOF
python -m engine.prospectivity.features.plot_stack outputs/demo/dem.tif outputs/demo --dem-data-origin SYNTHETIC
```

**Output:** 8 covariate rasters (depth, slope, aspect, roughness, curvatures,
TPI, BPI) with a content-hashed provenance manifest, and a plot
(`outputs/demo/covariate_stack_synthetic_dem.png`) with the 35 training
stations overlaid — watermarked SYNTHETIC because the declaration says so.

---

## 3. PHASES 2–4 — one command: everything → a complete run directory

**Input:** the committed corpus + the DEM and TS-6 raster above.

```bash
python -m engine.prospectivity.harness --dem outputs/demo/dem.tif --dem-data-origin SYNTHETIC --ts6 outputs/demo/ts6.tif --ts6-data-origin SYNTHETIC --out outputs/demo/runs/demo --run-id demo
```

(~150 s: the production registry — 500-tree quantile forest — and all four CV
designs. The harness's own summary prints the verdicts as it finishes.)

**Output:** `outputs/demo/runs/demo/` — 62 files, ~2.75 MB:

| what | where |
|---|---|
| paired prediction + uncertainty rasters, 3 estimators | `*_prediction.tif`, `*_uncertainty.tif` + sidecars |
| 12 economic footprints + 6 difference maps + the association record | `economics/` |
| browser-facing flat-array exports (the mask as `null`) | `export/` |
| the covariate stack it was all computed on | `features/stack/` |
| **the record of everything** — hashes, CV, verdicts, provenance chain | `run_manifest.json` |

---

## 4. PHASE 2 — read from the record: spatial CV, and the guard refusing

**Input:** `run_manifest.json` (nothing is recomputed).

```bash
python - <<'EOF'
import json
m = json.load(open("outputs/demo/runs/demo/run_manifest.json"))
for design, v in m["claim"]["verdicts"].items():
    failing = [p["precondition"] for p in v["preconditions"] if not p["passed"]]
    print(f"{design}: REFUSED — failing {failing}, passing {sum(p['passed'] for p in v['preconditions'])}")
EOF
```

**Output:** every design REFUSED, each for **named** reasons — the claim
design fails exactly one precondition (no acceptance gate existed before the
scores) and passes five; random k-fold additionally fails the
spatially-blocked requirement *by record*. **What it shows:** the guard
discriminates — it is not a blanket refusal — and across the two station
clusters (~991 km apart) kriging ≈ the baseline *by geometry*, which the
record frames as a measurement of the clusters, not of the models.

---

## 5. PHASE 3 — read from the record: paired surfaces and the TS-6 comparison

```bash
python - <<'EOF'
import json
m = json.load(open("outputs/demo/runs/demo/run_manifest.json"))
for name, s in m["surfaces"].items():
    print(f"{name:18} mu [{s['mu_min']:.2f}, {s['mu_max']:.2f}]  sd [{s['sd_min']:.2f}, {s['sd_max']:.2f}]  {s['n_distinct_values']} distinct")
a = m["ts6_agreement"]["ordinary_kriging"]
print("TS-6 (kriging): mean diff %+.2f, rmse %.2f —" % (a["mean_difference"], a["rmse"]), a["benchmark_uncertainty_note"])
EOF
```

**Output:** three paired surfaces (a prediction is never emitted without its
uncertainty — structural since E2.1), kriging's full-data variogram fit
(21.6 km range, at the candidate ceiling), and one TS-6 agreement per
estimator **carrying its own caveat**: the benchmark is a synthetic fixture,
so the agreement numbers measure nothing yet.

---

## 6. PHASE 4 — read from the record: economics, placeholders marked

```bash
python - <<'EOF'
import json
m = json.load(open("outputs/demo/runs/demo/run_manifest.json"))
for s in m["economics"]["scenarios"]:
    print(s["name"], "cutoff", s["cutoff"]["value"], s["cutoff"]["units"], "— origin", s["cutoff"]["data_origin"])
    for r in s["watermark"]["reasons"]:
        print("   reason", r["reason"], "UNLIFTED — lifts at", r["lifted_by"])
EOF
```

**Output:** two scenarios with AUTHORED placeholder cutoffs; every footprint
covers 100 % of the predictable domain and every difference map is empty — a
property of the placeholders' relation to the training mean, recorded with
its reason. Each artifact carries **two independent watermark reasons with
separate expiries** (terrain ↔ Checkpoint 1; economics ↔ Checkpoint 4).

---

## 7. PHASE 5 — verify the run directory by recomputation

**Input:** the run directory, as bytes on disk.

```bash
python -m engine.prospectivity.verify_run outputs/demo/runs/demo
```

**Output:** every output file's bytes re-hashed against the manifest, the
corpus and stack links recomputed from substance, and the claim verdict
re-run and compared to the committed expectation — the same step CI runs on
every push (`run-artifact` in `.github/workflows/ci.yml`, which uploads the
run directory as `run-<sha>`). It fails only if something *moved*.

---

## 8. PHASE 5 — serve it: the API and the viewer

**Input:** the runs root (the API refuses anything in it that is not a run).

```bash
CCZ_RUNS_ROOT=outputs/demo/runs .venv/bin/uvicorn services.api.app:app --factory --port 8765
```

Open **http://127.0.0.1:8765/** and look for, in order:

1. **The verdict banner** — on load, above the map, with the failing *and*
   passing precondition sets named. Nothing on the page can close it.
2. **The striped no-information region** — 2,846 of 2,880 predictable cells
   lie beyond one fitted variogram range of every station; the stripes clear
   only around the two station clusters. The map argues the data's geometry.
3. **The hatched mask** (no covariates) — visually distinct from both the
   ramp and the stripes.
4. **Hover anywhere** — the value arrives with its paired uncertainty and the
   uncertainty's *kind* (three estimators report three different kinds of σ).
5. **Switch Layer → Minable footprint** — the UNIFORM banner explains why
   every economics layer looks identical today, with the recorded counts.
6. **The context section** — the coastline (Natural Earth, public domain) and
   the REAL CCZ management area (Marine Regions MRGID 64222, CC-BY 4.0 — a
   curved white outline; it was a rectangle labelled FIXTURE until G.2,
   2026-08-25), each with its own origin and citation,
   never inheriting the run's watermark.
7. **The stations** — 35 white points, origin MEASURED, drawn over a surface
   whose origin is SYNTHETIC: the clearest single statement of what this
   project has and has not got.

Then check it the way a deployment is checked — through the URL:

```bash
python deploy/verify_deployment.py http://127.0.0.1:8765
```

---

## 9. Optional epilogues

- **The suite as the footnote:** `pytest -q` — 703 tests, ~2–5 min. *(676 until G.2, 2026-08-25.)*
- **CI:** every push runs the suite *and* builds the same run directory on
  GitHub's machines (`run-artifact`), verified by recomputation and uploaded
  as `run-<sha>` (30-day retention).
- **Deploy:** `deploy/README.md` — one container serving one pinned CI-built
  run; `docker compose up viewer` for the local rehearsal.
