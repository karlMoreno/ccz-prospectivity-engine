# HANDOFF — Claude Code, Phase 5 Track E complete, CP5a pending Karl

Paste at the start of a fresh session. This is a summary, not a source of
truth. `CLAUDE.md`, `docs/BACKLOG.md`, `docs/PATTERNS.md`,
`docs/walkthroughs/`, `docs/audits/` and the contract files win over
anything here. Written 2026-08-23 at the end of the Phase-5 session; the
repo may have moved since.

## First actions

1. Read `CLAUDE.md`. The conventions and the defect inventory both grew this
   phase — the newest corollary (the fresh-run look) was earned twice in two
   days.
2. Read `docs/BACKLOG.md` and the Phase-5 walkthroughs: `E5.5.md`, `E5.1.md`,
   `E5.2.md`, `E5.3.md`, `E5.4.md`, `E5.6-7.md` (its §5 is the phase
   closeout). `docs/DEMO.md` + `demo_alpha.py` are the fastest way to see the
   whole thing run.
3. Run the suite IN THE FOREGROUND; report the count. Last confirmed: **676
   passed, 2 skipped**. Wall-clock varied 141–378 s across runs this phase
   without explanation — a measurement on record, not a mystery to re-derive.
4. Check `git log origin/main..HEAD | wc -l`. At handoff time `origin/main`
   was at `ff5f2a7` (E2.4-3) — **the push is the single biggest pending
   action** and it is Karl's.
5. Report anything here the repo contradicts. Every handoff so far has
   carried at least one premise that did not survive checking; this one will
   too.

## State

Track E is complete through Phase 5. Every phase boundary was approved
except CP5a, which is a checkpoint, not a task — it is PENDING KARL (ledger
row, 2026-08-23).

```
  Phase 2   ✓  estimators, spatial CV, refuse-to-validate        (audited)
  Phase 3   ✓  surfaces, TS-6 comparison, manifest emitter
  HASH.1    ✓  shape-tolerant hashing; path-dependence 11 → 0
  Phase 4   ✓  economics: model, footprints, manifest block
  Phase 5   ✓  E5.5 harness → E5.1 API+catalog → E5.2 export →
               E5.3 viewer → E5.4 honesty surface → E5.6 CI job →
               E5.7 deploy definition + verification
  ────────────────────────────────────────────────────────────────
  CP5a      ←  PENDING KARL: push → CI's first run → host →
               verify through the PUBLIC URL → ledger row
  CP5b      =  alpha launch: needs CP1 (GEBCO) + CP3 (TS-6) + CP4
               (economics); the deployed URL is the alpha of the
               MACHINERY, the launch is CP5b
```

Suite trajectory across Phase 5: 611 → 624 (E5.5) → 635 (E5.1) → 648 (E5.2)
→ 665 (E5.3) → 672 (E5.4) → 676 (E5.6/E5.7). Schema: `RunManifest` at 4
(E5.5 added `training_stations`; both committed historical hashes held —
`0227d6df…`, `e3ac1561…`, pinned by literal).

## KARL'S QUEUE — nothing on it is Track E's to do

1. **Push `main`.** CI then runs Phases 3–5 for the first time AND the new
   `run-artifact` job (the harness twice in two trees, verified by
   `engine/prospectivity/verify_run.py`, uploaded as `run-<sha>`, 30 days).
   What to look for on its first run: the job prints CI's GDAL and the
   environment block. If `content_hash` or raster hashes differ from a local
   run but the VERDICT SETS, corpus link and stack link hold, that is
   HASH.1's recorded limit behaving (GDAL bytes; `inputs.environment` in the
   hash BY DESIGN). If substance differs, the job fails — a real finding.
2. **Choose the host, deploy, verify.** `deploy/README.md` has the proposal
   (one host for both — the API serves the page; Fly.io ≈ $2–3/mo or Render
   $7/mo warm; the account/DNS are yours). Build the image from the CI
   artifact (`deploy/run/`, gitignored), then run
   `python deploy/verify_deployment.py <public-url>` AND the fresh-run look
   through that URL, reported. The Docker image build is UNTESTED (the
   daemon was not running); the image's exact CMD was rehearsed as a process
   and every check passed at the rehearsal URL.
3. **Close CP5a in the ledger** (or name what blocked it). The row exists as
   "pending Karl" with the gate spelled out.
4. **The context-layer data task** (BACKLOG §3): Marine Regions MRGID 64222
   + the ISA shapefiles — download, hash, classify, wire into
   `services/api/context.py`. Its trigger FIRED: the public URL would ship
   the FIXTURE rectangle (labelled as one). Two decisions ride on it:
   whether the CCZ polygon resolves the AOI (and whether a hashed download
   from an authoritative publisher is MEASURED, not LITERATURE), and whether
   the APEIs populate `exclusions.geojson`.
5. **Confirm one reading:** the "before a published run" BACKLOG entries
   (LITERATURE citations, the precision rule, lockfile pinning, wet/dry
   basis) were read as NOT fired by a watermarked, refused run that says so
   in its title. That reading is recorded in the CP5a ledger row for you to
   confirm or override.

## What Phase 5 built, one line each — verify, then lean on it

- **E5.5** — `python -m engine.prospectivity.harness`: one command, the
  PRODUCTION registry only (read back per fold: `{500}`), a 62-file /
  2.75 MB run directory whose layout is a stated contract (`RUN_LAYOUT`),
  determinism measured in two trees. Plus three manifest additions the
  viewer needed: `full_data_fit` (kriging range 21.611 km AT the candidate
  ceiling — was prose-only), `sd_min/sd_max`, `training_stations` (35, origin
  MEASURED, kept apart from the run's SYNTHETIC).
- **E5.1** — the read-only API (read-only over the ROUTE TABLE; eight
  not-a-run refusals by name; files served only by `output_hashes` key) and
  the layer catalog (resolved from the manifest, never a filename; the
  72-cell grid with THREE states — 18 present + 54 not-applicable + 0
  absent naive, 24 canonical; the watermark asymmetry kept; the verdict
  once).
- **E5.2** — flat-array exports (Karl's decision, measured: 700× smaller
  than polygons), the mask as `null` (`allow_nan=False`; a browser rejects
  the bare NaN token Python emits), origin and the source's watermark form
  in the file body, verified against the PIXELS by the emitter, hashed under
  `export/`.
- **E5.3** — ONE static page, MapLibre 5.24.0 + deck.gl 9.3.10, SRI hashes
  RECORDED in `services/api/web.py` and asserted without a network; NO tile
  basemap (zero coastline features intersect the extent — vendored public-
  domain coastline instead); driven by a SERVED PRESENTATION MODEL
  (`GET /runs/{id}/viewer` — the named exception to "the API computes
  nothing": bins/labels/states are rendering decisions, rule in its body,
  nothing written back); context layers as a SECOND CLASS (own origin,
  outline only, never in the catalog, FIXTURE rectangle that says so).
- **E5.4** — the honesty surface, all content in the model, the page renders
  verbatim: the verdict banner with failing AND passing sets (no dismiss
  path exists), per-layer reasons in the layer's own form, the paired σ
  never hideable ((c)+; σ-as-saturation DECLINED — three kinds of σ in one
  channel), the no-information hatch on every layer (2,846 of 2,880
  predictable cells, derived in the model from recorded values, the two
  labels per layer), the uniform rasters explained. Thirteen dispositions,
  zero LOOKING.
- **E5.6/E5.7** — above, in Karl's queue.

## The rules this phase earned — all in CLAUDE.md, all with evidence

- **THE FRESH-RUN LOOK IS PART OF THE TASK** (corollary, entered at the
  E5.4 approval, ×2): E5.3's page labelled a present layer "absent" (logic
  lived in the untested page → moved into the tested model as `neighbours`);
  E5.4's `fitBounds` inside `map.once("load")` registered after the event
  had fired — SUCCESS-SHAPED SILENCE, the empty-background-output shape in
  JavaScript. Do the look every time a task touches the page; report
  "nothing" explicitly.
- **The no-duplication constraint has a working form:** the SERVED
  presentation model. The page computes nothing about the run; the one
  stated exception is `cell_index` (three lines of transform math on mouse
  events), pinned in Python against the raster's own georeferencing.
- **"The viewer is catalog-driven; the catalog is not yet data-driven"** —
  the generality boundary sits in `catalog.py`'s constants (BACKLOG §3,
  trigger: the first second dataset). Don't generalize speculatively.
- **The unreachable-check sub-pattern is at ×3** and the newest instance was
  found BY MUTATION in this phase's own code (E5.2's X9: the emitter's
  null-set gate below its array check). Ask what already covers a check
  before writing it; the ground truth goes OUTSIDE the chain.
- **Mutation-harness hygiene:** zsh word-splitting bit twice (`$FILES`,
  `$target`) — explicit arrays and `set -u`, confirm each mutation applied,
  `cmp`-verify each restore, and read WHICH layer answered (E5.2's X1–X8
  were all caught by the emitter at fixture setup, not by the tests named).
- **The verdict must not move silently:** `verify_run.EXPECTED_VERDICT_SETS`
  is the committed expectation (both halves). The day CP1/CP3/CP4 land, that
  constant, the page's standing-status metadata (BACKLOG, CP5b entry) and
  the E5.4 banner all change BECAUSE THE FACTS CHANGED — each deliberately.

## Findings on record — measure, don't rediscover

- 99.62 % of kriging's domain is within 0.5 kg/m² of the 19.53 mean; **34
  cells** within one fitted range (= 2,846 of 2,880 beyond it — the hatch's
  number, derived in the model, E3.1-2's count exactly).
- RF production surface [15.091, 21.681], 1,842 distinct values, 500 trees
  read back; the light registry's is a DIFFERENT artifact ([14.982, 22.041],
  1,218) — the harness cannot produce it.
- Exports: 454,742 B raw / 46,076 B gzip over 21 layers (kriging pair
  45,974 B pinned by literal); CP1 at ~1.96 M cells needs tiles (TiTiler
  merges into the API; the catalog gains `tiles_url` beside `data_url`, dict
  content, no schema move — not before its consumer exists).
- Float32-vs-float64 rounding at 3 dp differs in ~1–2 of 2,880 cells on a
  boundary — exports are verified against the RASTER's pixels.
- CI job cost ≈ 5–6 min (two production runs at ~150 s each plus install).

## Checkpoint 1 readiness (when GEBCO lands)

The same harness command with `--dem-data-origin MEASURED` and the real
file. Expect and do not "fix": the occupancy/ceiling/border pins go red by
design (BACKLOG §3 re-report entry), the terrain watermark reason LIFTS
while economics stays, `EXPECTED_VERDICT_SETS` may move (update
deliberately), and `DemGrid.load`'s south-up assertion (one line, BACKLOG)
is due BEFORE the new DEM enters.

## Tracked at the last minute — and one caveat that rides on it

Karl committed the previously-untracked set himself during this session's
usage-limit gap (`58b6b8e "Demo phase2"`): `demo.py`, the commercial
improvement proposal, `scratch/`, and `.claude/launch.json`. **The caveat:**
the tracked `launch.json` contains ABSOLUTE `/private/tmp/...` scratchpad
paths (the `api-viewer` runs root and the `deployed` rehearsal root) that
exist only for the session that wrote them — on a fresh boot or another
machine those configs point at nothing and the dev servers will refuse to
start (correctly, by the not-a-run refusal). Fix when next touched: point
them at `outputs/demo/runs` (which `demo_alpha.py` produces) or re-generate.
`deploy/run/` is gitignored by design and stays so.
