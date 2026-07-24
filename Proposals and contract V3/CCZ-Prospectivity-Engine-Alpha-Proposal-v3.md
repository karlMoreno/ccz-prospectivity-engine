# CCZ Prospectivity Engine — Alpha Proposal v3

## Independent-Track Build Plan — TS-6 Modernization on a Path C **Phase A** Open Corpus

**Version:** 3.0
**Status:** Alpha implementation proposal
**Relationship to other documents:** Narrows *CCZ Prospectivity Engine Proposal v3* to a first buildable, publishable release. It keeps the two-track (engineer/geologist) concurrent structure, the "modernize ISA Technical Study No. 6" framing, and the evidence-class discipline — and it **scopes data acquisition to Path C Phase A only** (the one-day numeric/derivable download queue). Phase B (PDF/supplement extraction) and Phase C (targeted requests) are explicitly out of the alpha.

**Authorship note:** Sections marked **`[GEOLOGY — ISAAC]`** are gaps for the domain expert. Everything else is engineering-specified, with safe defaults where a geology gap would block a decision.

---

# 1. What this alpha is

The **CCZ Prospectivity Engine Alpha** openly reproduces and modernizes one facet of **ISA Technical Study No. 6 (2010)**: for one CCZ study area, it assembles an **open, evidence-typed abundance corpus from Path C Phase A**, predicts nodule abundance with **ordinary kriging** (TS-6's own method), runs **spatial cross-validation**, produces a **paired uncertainty surface**, **benchmarks the result against the TS-6 2010 surface**, adds an **economic minability layer** (market vs strategic) TS-6 never had, and emits a **provenance manifest** — all re-runnable from one command and served through a thin web viewer.

```
PHASE-A OPEN CORPUS → INGEST/NORMALIZE → FEATURES → KRIGING (TS-6 parity)
   → SPATIAL-CV → PREDICT + UNCERTAINTY → TS-6 BENCHMARK → ECONOMIC OVERLAY
   → MANIFEST → VIEWER
        ▲                                      ▲                ▲
   open, numeric,                   (the layer TS-6 lacked)   evidence-typed:
   real data on                                              train on [MASS] only
   day one
```

The alpha is deliberately narrow. It does **not** attempt Path C Phase B/C, Option-B proxies, cover→mass modeling, image computer-vision, multiple study areas, the lunar port, or full TS-6 parity (all four SDSS methods).

## 1.1 The organizing principle: two independent tracks (unchanged, still holds)

```
TRACK E — ENGINEER                       TRACK G — GEOLOGIST
pipeline, ingestion machinery, API,       Phase-A data run, QA, science
viewer                                    parameters, TS-6 study
        │                                        │
        │        both build against              │
        └──────►  SHARED CONTRACTS  ◄────────────┘
                  (interfaces + file schemas, Phase 0)

Track E builds the whole machine on SYNTHETIC fixtures → never waits for real data.
Track G runs Phase A + produces DATA/SPEC artifacts → never waits for the pipeline.
They meet at INTEGRATION CHECKPOINTS to swap fixture → real.
```

**Why Phase A strengthens the two-track model:** Phase A is a *download queue of already-numeric or trivially-derivable* sources (PANGAEA SO268, DOMES, etc.). Track G can produce a **real** corpus in roughly a day, so the usual "waiting on real data" risk nearly vanishes — Track E swaps synthetic fixtures for the real corpus at the very first checkpoint instead of near the end.

---

# 2. Alpha objective

> **Assemble a Path C Phase-A open, evidence-typed [MASS] corpus for one CCZ area; predict nodule abundance with ordinary kriging + spatial CV + uncertainty; benchmark against the TS-6 2010 surface; add a market-vs-strategic economic overlay; and publish it as a reproducible tool with a manifest — through a thin viewer.**

---

# 3. Alpha scope

## 3.1 The alpha WILL include

### Data (Path C Phase A only)
- Ingest the **Phase A queue**: numeric/derivable sources — SO268 box-core summary `[01]`, DOMES floor density `[02]`, DOMES Piper `[03]`, DOMES Site C `[04]`, SO268 individual nodules `[05]`, Dryad chamber `[06]`, Amon image table `[11]`, APEI-6 cover `[12]`, GSR Mendeley cover `[14]`, TS-6/Washburn regional grid `[18]`/`[19]`.
- **Evidence-class tagging** of every observation (`MASS`/`COUNT`/`COVER`/`GRID`/`GRADE`).
- **Normalization to kg/m² only where valid** ([MASS] rescale by sampled area; [COUNT] via recorded mean-nodule-mass; **[COVER] never silently converted**; [GRID] flagged non-independent).
- A **master corpus** (evidence-typed, provenance per observation) that supersedes the simple sample file.
- Public bathymetry (GEBCO-class) + public DeepData context polygons (APEI/contract areas).

### Engine
- One `TerrainSource` (CCZ bathymetry) + reprojection + hashing.
- `SampleSource` selecting **[MASS] rows with valid `abundance_kg_m2` and `is_open`**.
- Terrain feature stack (Option A: slope, roughness, curvature, TPI, BPI).
- Estimators behind one interface: **ordinary kriging (TS-6 parity)** + random forest + mean baseline.
- **Spatially blocked** cross-validation with baseline comparison.
- Prediction + paired uncertainty surfaces (COGs).
- **TS-6 comparison** (agreement metric vs the digitized 2010 surface).
- One `EconomicModel` with two scenarios (market + strategic) + difference map.
- A provenance manifest (records spatial CV, TS-6 comparison, and the **corpus manifest**).

### Delivery
- Read-only FastAPI (runs, manifest, rasters, CV scores, TS-6 agreement).
- Thin Next.js viewer (prediction, uncertainty toggle, scenario switch + difference, TS-6 comparison view, manifest link).
- One-command / parameterized-notebook run harness.
- CI running the full loop on fixture data every push.
- Methodology + data-source docs, including a "modernizing TS-6" chapter and the **Phase-A corpus provenance**.

## 3.2 The alpha will NOT include
- **Path C Phase B** (PDF/supplement extraction: BGR/IOM/Korea papers) or **Phase C** (targeted data requests).
- Option-B TS-6 proxies (sediment/chlorophyll/CCD) — designed for, not built (Phase 6).
- **Cover→mass conversion modeling** — [COVER] is ingested and tagged, used only as a covariate/context, never converted to a bare kg/m² value.
- Image computer-vision annotation of OFOS imagery.
- Full TS-6 parity (SIS, WofE, fuzzy logic, RBF net); more than one study area; the lunar port; user accounts beyond one admin.
- Any use/redistribution of confidential contractor or DeepData resource data.

## 3.3 Completion definition
```
For one CCZ area, a run produces:
├── a Phase-A open [MASS] corpus (evidence-typed, provenance per observation)
├── prediction surface (COG)
├── uncertainty surface (COG)
├── spatial-CV scores + mean-baseline comparison
├── TS-6 agreement score (vs the 2010 surface)
├── minable-footprint rasters for two economic scenarios + difference map
└── a provenance manifest (run + corpus) sufficient to reproduce everything

…and a visitor can: open the area · see prediction + uncertainty · switch
economic scenarios · see the TS-6 comparison · read the methodology + corpus
provenance · reach the manifest.
```

---

# 4. The two tracks in detail

## 4.1 Track E — Engineer (full technical ownership)
Everything that is code and can be built entirely on synthetic fixtures:
```
- engine package (interfaces, Template Method run())
- INGESTION machinery for Phase A: SourceAdapter per source-family +
  AbundanceNormalizer per evidence class + dedup (Specification) + validate
- terrain feature engineering (Option A)
- estimators (ordinary kriging, random forest, mean baseline)
- spatial cross-validation
- uncertainty computation
- TS-6 comparison MECHANISM (consumes G's digitized surface)
- economic overlay MECHANISM (not the numbers)
- provenance manifest emitter (run + corpus)
- read-only FastAPI + thin Next.js viewer
- run harness + CI + fixtures; repo, Docker, migrations
```
**Track E never needs real geology to progress.** Synthetic sources (a fake box-core table, a fake cover table, a synthetic TS-6 raster) that match the contracts exercise the entire machine, including the adapters and normalizers.

## 4.2 Track G — Geologist (data + science ownership)
Everything that is data, parameters, and judgment, produced as **artifacts**:
```
- READ TS-6 cover to cover → proven covariates, data sources, thresholds, biases
- RUN PATH C PHASE A: download the queue, populate the master corpus
  (kg/m² where [MASS]; derive where [DERIVE]; tag cover/count/grid honestly)
- for each [DERIVE] source, confirm sampled_area_m2 + wet/dry basis before
  computing kg/m² (fill the normalization contract)
- assemble public bathymetry (GEBCO-class) + public DeepData polygons + metadata
- define QA rules, credible validation metrics, acceptable TS-6 agreement
- DIGITIZE the TS-6 2010 abundance surface for the AOI (Contract 6)
- supply real economic parameters (Contract 4), anchored to real ranges
- interpret results vs known geology AND vs TS-6; write the methodology
```
**Track G never needs the finished pipeline to progress.**

### 4.2.1 Evidence-class discipline (the rule that keeps the corpus honest)
Every observation carries exactly one class; conflation is the fastest way to poison the model.
```
[MASS]   kg/m²         → the TRAINING TARGET (the only class the model trains on)
[COUNT]  nodules/m²    → covariate; → kg/m² ONLY via a recorded mean-nodule-mass model
[COVER]  % cover       → covariate; NEVER silently converted to kg/m²
[GRID]   compiled/interp→ prior + TS-6 benchmark; NEVER counted as an independent station
[GRADE]  Mn/Ni/Cu/Co   → joins to abundance stations; fills metal columns + economics
```

## 4.3 What connects them: the (updated) shared contracts
See §6. The coupling is still just files + interfaces agreed in Phase 0. v3 upgrades Contract 1 to the **master-observation schema**, expands Contract 5 into the **Phase-A source queue**, and adds **Contract 7 (normalization policy)** — all without changing how the tracks interact.

---

# 5. Architecture (alpha)

```
┌───────────────────────────────┬──────────────────────────────────────────┐
│  TRACK G ARTIFACTS            │   TRACK E MACHINE                          │
│  (Phase-A data + specs)       │   (code)                                  │
├───────────────────────────────┼──────────────────────────────────────────┤
│ Phase-A downloads ─────────►  │  SourceAdapter(×family)  ← ADAPTER         │
│  (SO268, DOMES, …)            │        │                                  │
│ master_observations.csv ───►  │  AbundanceNormalizer     ← STRATEGY        │
│  (evidence-typed)             │  (per evidence class)                     │
│ source_queue.yaml  ────────►  │  Dedup + Validate        ← SPECIFICATION   │
│ normalization.yaml ────────►  │        │                                  │
│ study_area.geojson ────────►  │        ▼                                  │
│ bathymetry.tif ────────────►  │  MASTER CORPUS ([MASS] rows → SampleSource)│
│ ts6_surface.tif ───────────►  │        │                                  │
│ scenarios.yaml ────────────►  │  ProspectivityEngine.run()                │
│ covariates.yaml (Option A)    │   ├── terrain features                    │
│ qa_rules / metrics (spec)     │   ├── kriging + RF + baseline             │
│                               │   ├── spatial CV + baseline               │
│                               │   ├── predict + uncertainty               │
│                               │   ├── compare_to_ts6()                    │
│                               │   ├── economic overlay                    │
│                               │   └── manifest (run + corpus)             │
│                               │        │                                  │
│                               │        ▼   COGs + manifest → API → viewer  │
└───────────────────────────────┴──────────────────────────────────────────┘
```

```
// PATTERNS (why the two-track split survives the ingestion complexity):
// ADAPTER        one SourceAdapter per Phase-A source-family → master schema.
//                Track E writes adapters against SYNTHETIC sources; Track G's
//                real downloads drop into the same schema.
// STRATEGY       one AbundanceNormalizer per evidence class (MASS/COUNT/COVER/
//                GRID). Swapping conversion logic never touches ingestion/model.
// TEMPLATE METHOD IngestionPipeline.run(): fetch→adapt→normalize→dedup→validate
//                →append, and ProspectivityEngine.run() — fixed honest sequences.
// SPECIFICATION  dedup + quality rules as composable predicates (DOMES families,
//                nodules⊂events, cover≠mass) — declarative and testable.
```

---

# 6. The seven contracts (updated for Phase A)

**Bottom line: the six v2 contracts carry forward; Contract 1 is upgraded to the master-observation schema, Contract 5 becomes the Phase-A source queue, and Contract 7 (normalization policy) is new. Nothing already built is discarded.**

```
CONTRACT                    STATUS         WHAT CHANGES FOR THE ALPHA
──────────────────────────────────────────────────────────────────────────────
1 master_observations.csv   UPGRADED       samples.csv becomes the MASTER schema:
  + schema.json                            evidence_class + derivation fields +
                                           per-observation provenance. Superset of
                                           the old sample file; abundance-only rows
                                           still valid. schema_version 3.
2 study_area.geojson         FROZEN         no change
  + exclusions
3 covariates.yaml            FROZEN         Option-A enabled; Option-B TS-6 proxies
                             (structural)   disabled (Phase 6). registry_version 2.
4 scenarios.yaml             FROZEN         structure same; cutoffs anchored to real
                             (structural)   ranges. config_version 2.
5 source_queue.yaml          EXPANDED       source_metadata becomes the PHASE-A
  (was source_metadata)                     SOURCE QUEUE: one entry per Phase-A
                                            source with evidence classes, license,
                                            is_open, sampled_area, derivation.
                                            metadata_version 3.
6 ts6_reference.yaml         MINOR          benchmark surface; note [18]/[19] are
                                            also GRID priors. reference_version 1.
7 normalization.yaml         NEW            per-evidence-class → kg/m² POLICY: the
                                            rules the AbundanceNormalizer obeys and
                                            Track G validates. policy_version 1.
```

Field-level deltas and the new files are generated alongside this proposal (`phase0-contracts-v3/`).

---

# 7. Technology stack (alpha subset)

| Layer | Tools |
| --- | --- |
| Engine | Python 3.11+, Rasterio, NumPy, RichDEM/xarray-spatial, scikit-gstat/PyKrige (kriging), scikit-learn (RF + CV), GeoPandas/Shapely, Pydantic, pytest |
| **Phase-A ingestion** | `pandas`; **`pangaeapy`** (PANGAEA DOIs → dataframes for `[01]`–`[05]`,`[12]`); `requests` (Dryad `[06]`, Mendeley `[14]`, ArcGIS layers); `openpyxl` (xlsx); Pydantic (MasterObservation validation) |
| TS-6 compare | Rasterio + NumPy/scipy (resample to common grid; spatial correlation + mean-difference) |
| API + storage | FastAPI (read-only), COG, PostGIS (metadata), MinIO |
| Viewer | Next.js + TypeScript, MapLibre GL JS + deck.gl, TanStack Query, ECharts/Plotly |
| Reproducibility | uv/pip-tools (hash-pinned), Docker, DVC, Papermill, GitHub Actions, MkDocs |
| Track G tools | QGIS (TS-6 georeference/digitize; polygon handling), spreadsheets, Markdown |

Out of scope for the alpha: PDF-table extraction (Camelot/Tabula — that's Phase B), image CV, Redis/queues/Kubernetes/clusters, any upload-and-compute web backend.

---

# 8. Functional requirements (alpha subset)

**Carried from the engine (PR series):**
```
AR-P01  Terrain ingestion (one CCZ bathymetry grid, reproject, hash)
AR-P02  Sample selection ([MASS] rows w/ valid abundance_kg_m2 + is_open)
AR-P03  Terrain feature engineering (Option A; versioned)
AR-P04  Modeling (ORDINARY KRIGING [TS-6 parity] + random forest + mean baseline)
AR-P05  Spatial cross-validation (blocked; baseline reported; mandatory)
AR-P06  Prediction + uncertainty (paired COGs)
AR-P07  TS-6 comparison (agreement metric vs digitized 2010 surface)
AR-P08  Economic overlay (two scenarios + difference map; caveats)
AR-P09  Provenance manifest (run + corpus; records spatial CV + TS-6 compare)
AR-P10  Results API + thin viewer (incl. TS-6 comparison view)
AR-P11  Reproducible run harness (one command / parameterized notebook)
```

**New — Phase-A data acquisition (AR-D series, the alpha subset of v3's DA series):**
```
AR-D01  Source adapters — one SourceAdapter per Phase-A source-family maps native
        format → master-observation schema; adding a source doesn't modify the
        pipeline; adapter records source id/DOI/url/license/is_open/accessed-date.
AR-D02  Evidence-class tagging (mandatory) — every observation carries exactly one
        of {MASS, COUNT, COVER, GRID, GRADE}; none enters the corpus untagged.
AR-D03  Normalization by class — AbundanceNormalizer produces abundance_kg_m2 ONLY
        where valid: [MASS] rescale by sampled_area_m2 (e.g. box-core ×4 @0.25 m²);
        [COUNT] via recorded mean-nodule-mass (+ uncertainty); [COVER] returns a
        covariate, NEVER a bare kg/m²; [GRID] flagged prediction/compiled, excluded
        from training. Obeys normalization.yaml (Contract 7).
AR-D04  Provenance + dedup — per-observation provenance (source, license, is_open,
        original value/unit/basis, derivation_formula); Specification dedup rules
        (DOMES families by cruise+station+coords+date not DOI; individual nodules
        nested within box-core EVENTS; cover never merged with mass).
AR-D05  Corpus manifest — records that every training point is Phase-A + is_open,
        with its source; the run manifest references the corpus manifest.
```

Each AR-D maps to a v3 DA requirement, so nothing built in the alpha is throwaway.

---

# 9. Non-functional requirements (alpha)
```
Reproducibility    per-run + per-corpus manifest; hash-pinned deps; CI full-loop
                   on fixtures every push
Scientific honesty spatial CV mandatory; mean baseline always; uncertainty always
                   paired; evidence classes never conflated; cover never →kg/m²;
                   economic maps print assumptions + "illustrative only" until real
Open-data gate     only is_open=true sources enter a published run; confidential
                   contractor/DeepData resource data excluded
Provenance depth   every training point traces to a Phase-A source (+ derivation)
Determinism        same inputs + seed → stable outputs; seeds in manifest
Spatial            canonical EPSG:4326; one analysis grid; invalid geometries rejected
Performance        one CCZ run in minutes on a laptop
```

---

# 10. Development plan — two concurrent tracks (Phase A woven into Phase 0–1)

Phases each have a **Track E lane** and a **Track G lane** that proceed simultaneously; the dependency is always on a **contract**, never on the other person. Each phase ends with an **integration checkpoint** (fixture → real). ~2 weeks/phase at 8–12 hrs/week each.

---

## Phase 0 — Contracts + TS-6 study + Path C Phase A (joint start)

### Joint tasks
```
J0.1  Upgrade Contract 1 → master-observation schema (+ evidence_class, derivation)
J0.2  Confirm Contract 2 (geometry) unchanged
J0.3  Confirm Contract 3 (covariates: Option-A enabled, Option-B disabled)
J0.4  Confirm Contract 4 (economics) structure; agree watermark behavior
J0.5  Expand Contract 5 → Phase-A source_queue.yaml (the 10-source queue)
J0.6  Confirm Contract 6 (ts6_reference); note [18]/[19] GRID role
J0.7  Create Contract 7 (normalization.yaml) — per-class → kg/m² policy
J0.8  Create repo, licenses, docs skeleton; tag contracts v3-contracts
```

### Track E lane
```
E0.1  Scaffold engine package + Docker Compose (Postgres/PostGIS + MinIO)
E0.2  Define domain types (Observation/EvidenceClass, StudyArea, TerrainLayer,
      TS6Reference, results)
E0.3  Define interfaces: TerrainSource, SampleSource, Estimator, EconomicModel,
      TS6Reference, SourceAdapter, AbundanceNormalizer — empty but frozen
E0.4  SYNTHETIC sources (fake box-core [MASS], fake cover [COVER], synthetic TS-6
      raster) matching the contracts; synthetic TerrainSource
E0.5  CI skeleton: ingest synthetic sources → corpus → assert evidence tagging
```
*Depends only on: Contracts 1,2,5,6,7. Real data not required.*

### Track G lane
```
G0.1  Read TS-6; extract proven covariates, sources, thresholds, biases → docs/geology/
G0.2  RUN PATH C PHASE A: download the queue [01]-[06],[11],[12],[14],[18],[19];
      populate master_observations.csv (kg/m² where [MASS]; DERIVE where flagged;
      tag COVER/COUNT/GRID). ← THE #1 GATE, but low-risk (numeric downloads)
G0.3  For each [DERIVE] source, record sampled_area_m2 + wet/dry basis in
      normalization.yaml (e.g. SO268 0.25 m² → ×4; SO268 individual nodules →
      aggregate to event)
G0.4  Pick the study area by Phase-A data density; draft study_area.geojson
G0.5  Pull public DeepData polygons (APEI/contract areas) + Contract-5 metadata;
      pick GEBCO bathymetry
G0.6  Begin QA-rules spec (docs/geology/qa_rules.md)
```
*Depends only on: Contracts 1,2,5,7, the TS-6 PDF, and the public sources. Pipeline not required.*

### Exit criteria
```
Seven contracts agreed + committed. A REAL Phase-A [MASS] corpus exists (even if
small) with evidence tags + provenance. Study area chosen by data density.
CCZ-first vs Moon-first decided on Phase-A yield.
```

### Integration checkpoint 0 (early!)
```
Swap SYNTHETIC sources → the REAL Phase-A downloads (Contracts 1,5,7). The corpus
now holds real evidence-typed observations. This happens at the START, because
Phase A is a fast numeric download — the whole point of scoping to Phase A.
```

---

## Phase 1 — Ingestion adapters + features (one AOI)

### Track E lane
```
E1.1  Real SourceAdapters for the Phase-A families (PANGAEA tab via pangaeapy;
      Dryad/Mendeley xlsx/csv; regional grid) → master schema
E1.2  AbundanceNormalizer per class (MASS ×1/area; COUNT via mean mass; COVER→
      covariate only; GRID→prediction flag) reading normalization.yaml
E1.3  Dedup (Specification) + validation; build the master corpus
E1.4  Terrain feature recipes (Option A; deterministic, versioned); plot corpus
      [MASS] points over the DEM
E1.5  Unit tests: evidence tagging, normalization correctness, dedup rules
```
*Runs on real corpus OR synthetic. Not blocked by Track G.*

### Track G lane
```
G1.1  Assemble the REAL bathymetry grid (GEBCO-class) + metadata (is_open=true)
G1.2  Finalize QA-rules spec (screening thresholds; grab-sampler bias note)
G1.3  Covariate-selection spec: confirm Option A; list Option-B TS-6 proxies for later
G1.4  First pass QA of the Phase-A corpus (flag duplicates/outliers; never delete)
```

### Integration checkpoint 1
```
Swap synthetic DEM → real bathymetry.tif. Feature stack runs on real terrain;
corpus [MASS] rows train the model. Any schema mismatch surfaces here, via CI.
```

---

## Phase 2 — Modeling + spatial validation
### Track E lane
```
E2.1  Estimator interface + mean baseline
E2.2  ORDINARY KRIGING (variogram + kriging variance) — TS-6 parity
E2.3  Random forest (+ uncertainty via quantiles/ensemble)
E2.4  Spatially-blocked cross-validation; CV reporting vs baseline
E2.5  Refuse-to-validate guard if spatial CV didn't run
```
### Track G lane
```
G2.1  Credible validation metrics + acceptance thresholds (docs/geology/metrics.md)
G2.2  Variogram expectations / plausible spatial range (advisory)
G2.3  Begin gathering real economic parameters (metals, grade units, cutoffs)
```
### Integration checkpoint 2
```
Run kriging + RF + baseline on the REAL Phase-A corpus with spatial CV. Track G
reviews: credible uplift over baseline? plausible variogram? Feedback = spec update.
```

---

## Phase 3 — Prediction + uncertainty + TS-6 comparison
### Track E lane
```
E3.1  Prediction surface (grid) → COG
E3.2  Paired uncertainty surface → COG
E3.3  compare_to_ts6(): resample both to a common grid; agreement (spatial
      correlation + mean difference) vs the digitized TS-6 surface
E3.4  Provenance manifest emitter (run + corpus; records spatial CV + TS-6 compare)
```
### Track G lane
```
G3.1  DIGITIZE the TS-6 2010 abundance surface for the AOI → ts6_abundance.tif +
      fill Contract 6 (set role_note: benchmark_only vs reproduction_check)
G3.2  Define acceptable TS-6 agreement + how to interpret divergence
```
### Integration checkpoint 3
```
Swap synthetic TS-6 raster → real digitized ts6_abundance.tif. Full run yields
prediction + uncertainty + TS-6 agreement + manifest. Does our surface match
TS-6's center/north-rich pattern?
```

---

## Phase 4 — Economic overlay (the new layer)
### Track E lane
```
E4.1  EconomicModel reading Contract 4; two scenarios (market + strategic) with
      PLACEHOLDER values + "illustrative only" marker
E4.2  Minable-footprint rasters + scenario difference map
E4.3  Ensure prediction + uncertainty + TS-6 agreement + economics all flow into
      the manifest
```
### Track G lane
```
G4.1  Deliver real economic scenario config (Contract 4): grade units, metal
      weights, market cutoff, strategic cutoff, exclusions, caveats (anchored to
      real ranges)
G4.2  Write caveats text for economic maps
G4.3  Draft the methodology narrative incl. "modernizing TS-6" + Phase-A provenance
```
### Integration checkpoint 4
```
Swap placeholder scenarios.yaml → real config. Economic maps reflect real cutoffs;
"illustrative only" removed. Manifest describes a fully real, TS-6-benchmarked run.
```

---

## Phase 5 — Delivery: API, viewer, docs, release
### Track E lane
```
E5.1  Read-only FastAPI (runs, manifest, rasters, CV scores, TS-6 agreement)
E5.2  Thin Next.js viewer: prediction, uncertainty toggle, scenario switch +
      difference, TS-6 comparison view, manifest link
E5.3  Papermill / one-command run harness
E5.4  CI end-to-end on fixture data green
E5.5  Deploy (static COGs + small API host); Sentry on
```
### Track G lane
```
G5.1  Finalize methodology + data-source docs (incl. the Phase-A corpus provenance
      + the "modernizing TS-6" chapter)
G5.2  Geological interpretation of the prediction (vs known geology AND vs TS-6)
G5.3  Advise which results are appropriate to show publicly
G5.4  Draft the impact narrative for grants ("open, evidence-typed CCZ corpus +
      living modernization of ISA TS-6")
```
### Integration checkpoint 5 (= alpha launch)
```
The viewer shows the REAL prediction + uncertainty + real economic scenarios + the
TS-6 comparison, linked to a real manifest, with the Phase-A corpus provenance and
methodology published alongside. Alpha is live.
```

---

## Phase 6 (optional, post-alpha) — grow beyond Phase A
```
[E/G] Path C Phase B (PDF/supplement extraction: BGR/IOM/Korea) → more [MASS] rows;
      and/or Option-B TS-6 proxies via ProxySource; and/or lunar portability proof.
```

---

# 11. Dependency map (why nothing blocks)

```
                 CONTRACTS (Phase 0, frozen structure)
   1 master obs │ 2 geometry │ 3 covariates │ 4 economics │ 5 source-queue │ 6 ts6 │ 7 norm
        ▲             ▲            ▲             ▲              ▲             ▲       ▲
 TRACK E  builds to schema (incl. SYNTHETIC sources + a synthetic ts6 raster)
 TRACK G  runs Phase A + fills real files (corpus, bathymetry, digitized ts6, economics)

Track E's ONLY upstream dependency = the contracts (not Track G's progress).
Track G's ONLY upstream dependency = the contracts + the TS-6 PDF + public sources.
Integration = swap fixture → real file. Never a logic merge.
```

**Rule of thumb:** if either person is ever "waiting on the other," the plan has been violated — keep building against fixtures/placeholders and integrate at the next checkpoint. Because Phase A is a fast numeric download, the real-corpus swap happens at **checkpoint 0** (the start), not the end.

---

# 12. Repository structure (alpha)

```
ccz-prospectivity-engine/
├── engine/                       # TRACK E
│   └── prospectivity/
│       ├── domain/               # Observation/EvidenceClass, StudyArea, results
│       ├── ingestion/            # SourceAdapter + AbundanceNormalizer + dedup   ← NEW
│       ├── terrain/ · samples/ · features/
│       ├── estimators/           # kriging, random_forest, mean_baseline
│       ├── validation/ · uncertainty/
│       ├── ts6/                  # TS6Reference + compare_to_ts6()
│       ├── economics/            # EconomicModel + scenarios
│       ├── provenance/           # manifest emitter (run + corpus)
│       └── engine.py             # Template Method run()
├── services/api/                 # TRACK E — read-only FastAPI
├── apps/web/                     # TRACK E — thin Next.js viewer
├── database/                     # TRACK E — Alembic, fixtures
├── data/                         # TRACK G artifacts land here
│   ├── corpus/                   # master_observations.csv (Contract 1)          ← NEW
│   ├── sources/                  # source_queue.yaml (Contract 5) + downloads     ← NEW
│   ├── config/                   # normalization.yaml (Contract 7)               ← NEW
│   ├── aoi/ · bathymetry/ · economics/
│   ├── ts6/                      # digitized TS-6 surface + ts6_reference.yaml
│   └── fixtures/                 # synthetic sources for CI
├── docs/
│   ├── contracts/                # the seven contracts (JOINT)
│   ├── methodology/ · data-sources/ · geology/ · decisions/
├── infrastructure/ · scripts/
├── docker-compose.yml · Makefile · README.md
```

---

# 13. Testing strategy (alpha)

## Track E
```
Unit:        adapter→schema conformance, evidence tagging, normalization per class
             (incl. COVER-never-converts), dedup rules, feature determinism,
             estimator interface, spatial-CV correctness, TS-6 metric, manifest,
             economic-config parsing, is_open gate
Integration: full run() on FIXTURE sources (synthetic box-core + cover + ts6)
End-to-end:  ingest → normalize → corpus → features → model → CV → predict +
             uncertainty → TS-6 compare → economics → manifest, in CI every push
```

## Track G
```
Data QA:  master_observations.csv passes QA rules; only is_open sources; each
          [DERIVE] row has sampled_area + basis; no [COVER] row has a bare kg/m²
Sanity:   real-data run reviewed vs metrics.md and vs the TS-6 surface/pattern
```

The **fixture end-to-end test is the concurrency safety net**: CI runs the whole loop (ingestion + normalization + a synthetic TS-6 comparison) on synthetic sources, so Track E refactors freely and any schema/normalization mismatch surfaces at the checkpoint, not silently.

---

# 14. Dataset target for launch

```
1 CCZ study area (real geometry) + APEIs/exclusions   ← PUBLIC DeepData polygons
1 real bathymetry grid (is_open=true)                 ← PUBLIC GEBCO-class
A Phase-A OPEN corpus:
   • [MASS] station/event kg/m² from SO268 [01] + DOMES [02][03] (+ [04][05]
     derived) + Dryad [06]   ← the model's training points
   • [COVER]/[COUNT] from [11][12][14]                ← covariates/context only
   • [GRID] priors from TS-6 [18] + Washburn [19]     ← benchmark/prior, not stations
   (target [MASS] count/coverage: [GEOLOGY — ISAAC], per metrics.md)
The DIGITIZED TS-6 2010 abundance surface (Contract 6)
2 economic scenarios with real parameters (anchored to real ranges)
```

Quality + reproducibility over record count. One honest, evidence-typed, TS-6-benchmarked area beats several sloppy ones.

---

# 15. Funding hook (carried, sharpened)

```
Open engine + one citable CCZ prospectivity map that MODERNIZES ISA TS-6, built on
the FIRST open, evidence-typed CCZ abundance corpus (Phase A)  [open data license]
        ▼
A methodology preprint: "a living, open modernization of ISA Technical Study No. 6,
on an openly-assembled abundance corpus"   ← Track G leads
        ▼
Grants (ocean science, open data, critical minerals); we openly re-analyze, on
public sources, what the ISA's confidential model did privately
        ▼
Career return: resource-estimation artifact benchmarked against an intergovernmental
model (geologist) + portable geospatial-ML + open data pipeline (engineer)
```

---

# 16. Risks and mitigations

## Risk: Phase-A corpus too thin  — the #1 risk (much reduced by scoping to Phase A)
Phase A targets sources that are *already numeric or trivially derivable* (SO268, DOMES), so a real [MASS] corpus should exist after ~a day. **Mitigation:** G0.2 gate; if [MASS] density is too low for one area, either (a) pick the area with the densest Phase-A coverage (DOMES sites are well-sampled), or (b) flip to Moon-first (engine already built on fixtures). Phase B/C would add depth *later* but are out of the alpha.

## Risk: evidence-class contamination (cover treated as mass, grid as stations)
**Mitigation:** AR-D02/D03 + the AbundanceNormalizer strategy + Contract 7 make conflation impossible by construction; [COVER] never yields a bare kg/m²; [GRID] never trains.

## Risk: double-counting duplicates (DOMES families, nodules⊂events)
**Mitigation:** AR-D04 Specification rules; dedup by cruise+station+coords+date, not DOI; the event is the spatial sample, not each nodule.

## Risk: derivation error ([DERIVE] sources: area/basis, count→mass)
**Mitigation:** every [DERIVE] row records sampled_area_m2 + wet/dry basis + derivation_formula (Contract 7 + AR-D04); derived values carry lower quality_grade.

## Risk: circular validation if TS-6's modeled grid is also a sample source
**Mitigation:** prefer [MASS] station data for training and keep TS-6 as the benchmark; if only the modeled grid is available, label the comparison a reproduction check (Contract 6 role_note).

## Risk: dishonest validation
**Mitigation:** mandatory spatial CV + always-on baseline (AR-P05); manifest proves both ran.

## Risk: overselling certainty / contested economics
**Mitigation:** uncertainty always paired; economic maps print caveats; "illustrative only" until real; difference-map framing shows comparisons, not a verdict.

## Risk: confidential-data / license violation
**Mitigation:** is_open gate (AR-D05); confidential contractor/DeepData resource data excluded; TS-6/grids used as benchmark/prior, not redistributed.

---

# 17. Launch checklist

## Engine (Track E)
```
[ ] Phase-A adapters + normalizers green; corpus builds from real downloads
[ ] Evidence tagging enforced; no [COVER] row carries a bare kg/m²
[ ] Full run() green on the real corpus
[ ] Ordinary kriging (TS-6 parity) + RF + mean baseline all run
[ ] Spatial CV runs and is recorded in the manifest
[ ] TS-6 comparison runs and agreement is recorded
[ ] Prediction + uncertainty COGs produced
[ ] Two economic scenarios + difference map produced
[ ] Manifest (run + corpus) reproduces the run from inputs
[ ] is_open gate enforced; fixture end-to-end CI passes
[ ] API + viewer deployed (incl. TS-6 comparison view)
```

## Data + science (Track G)
```
[ ] TS-6 read; findings extracted into docs/geology/
[ ] Phase A run; master_observations.csv populated + QA'd; only is_open sources
[ ] Every [DERIVE] row has sampled_area + basis + formula (normalization.yaml)
[ ] TS-6 2010 surface digitized + Contract 6 filled (role_note set)
[ ] Real economic parameters delivered (placeholders removed)
[ ] Methodology + data-source docs published (incl. Phase-A provenance + TS-6 chapter)
[ ] Geological interpretation written (vs geology AND vs TS-6)
[ ] Impact narrative drafted for grants
```

## Joint
```
[ ] Seven contracts match what was actually built
[ ] Output data license stated (CC-BY corpus + maps); no confidential redistribution
[ ] "Illustrative only" markers removed where real data replaced placeholders
```

---

# 18. Final recommendation

Build and launch this first:

> **One CCZ study area, turned into a spatially-cross-validated nodule-abundance map (ordinary kriging, TS-6 parity) on a Path C Phase-A open, evidence-typed corpus — with an uncertainty surface, a TS-6 benchmark, two economic scenarios, and a reproducible manifest — served through a thin viewer, with the "modernizing TS-6" methodology and corpus provenance published alongside.**

Structure the work as **two decoupled tracks bound only by seven frozen contracts**: the engineer builds the whole machine (including the ingestion adapters and normalizers) on synthetic sources, while the geologist runs Path C Phase A, digitizes the TS-6 surface, and sets the economics — integrating at checkpoints where fixtures are swapped for real files, starting at checkpoint 0. Do not expand to Path C Phase B/C, Option-B proxies, multiple areas, or the lunar port before this single honest, TS-6-benchmarked slice is live.

The alpha's strategic value is that it produces, early, two hard-to-fake assets at once:

```
(1) THE FIRST OPEN, EVIDENCE-TYPED, REPRODUCIBLE CCZ NODULE-ABUNDANCE CORPUS
    (Path C Phase A), AND
(2) AN OPEN, UNCERTAINTY-QUANTIFIED, SPATIALLY-VALIDATED PREDICTION BENCHMARKED
    AGAINST THE ISA'S OWN 2010 MODEL, WITH AN ECONOMIC LAYER THAT MODEL NEVER HAD.
```

Once that exists behind clean interfaces, Phase B/C corpus growth, the TS-6-proven proxies, richer economics, grant funding, and the lunar port all attach to a stable, credible core.

---

# Appendix — Path C Phase A source queue (the alpha's data scope)

```
ID   SOURCE                              EVIDENCE          HANDLING IN ALPHA
─────────────────────────────────────────────────────────────────────────────────
[01] SO268 box-core summary (PANGAEA)    MASS,COUNT,COVER  MASS×4→kg/m² (0.25 m²) = TRAIN
[02] DOMES floor density (PANGAEA)       MASS              already kg/m² = TRAIN
[03] DOMES Piper abundance (PANGAEA)     MASS,COVER        kg/m² = TRAIN; cover=covariate
[04] DOMES Site C size/weight (PANGAEA)  MASS,COUNT        DERIVE (need area) → TRAIN if valid
[05] SO268 individual nodules (PANGAEA)  MASS,COUNT        aggregate to EVENT (not per nodule)
[06] Dryad chamber/nodule workbooks      MASS,DERIVE       TRAIN if station+area recoverable
[11] Amon UK-1/EPIRB image table         COUNT,COVER       covariate/context only
[12] APEI-6 cover gradient (PANGAEA)     COVER             covariate/context only
[14] GSR Mendeley cover                   COVER             covariate/context only
[18] ISA TS-6 grid                        GRID              BENCHMARK (Contract 6) + prior
[19] Washburn 2021 0.5° resource points   GRID              regional prior, NOT a station
─────────────────────────────────────────────────────────────────────────────────
TRAIN = [MASS] rows the model learns from.  Cover/count = covariates.  GRID = benchmark/prior.
Phase B ([25]-[46]) and Phase C (targeted requests) are OUT of the alpha.
```

# Appendix — contract change summary (hand to Isaac)

```
WHAT ISAAC NEEDS TO KNOW ABOUT THE CONTRACTS (v3, Phase A)

Nothing we built is thrown away. The structure holds. Specifically:
  • Contract 1: samples.csv becomes the MASTER schema — each row now carries an
    evidence_class (MASS/COUNT/COVER/GRID/GRADE) and, if a value was computed, how.
    Your abundance rows still work; you just tag what kind of evidence each is.
  • Contract 2: unchanged.
  • Contract 3: unchanged (Option-A terrain now; TS-6 proxies later).
  • Contract 4: unchanged shape; cutoffs anchored to real numbers.
  • Contract 5: becomes the PHASE-A SOURCE QUEUE — the 10 sources you download
    first, each with its license, is_open, evidence types, and (for derivable
    ones) the sampled area and how to get kg/m².
  • Contract 6: the TS-6 benchmark surface (unchanged); note [18]/[19] are also
    regional priors, never independent stations.
  • Contract 7 (NEW): the normalization POLICY — the rules for turning raw values
    into kg/m² (box-core ×4; count needs mean nodule mass; cover NEVER becomes a
    bare kg/m²; grids are priors). You confirm the geology in these rules.

Your biggest NEW job for the alpha: run Path C PHASE A (a one-day download of
numeric datasets), populate the master corpus with honest evidence tags, and
digitize the TS-6 2010 map for our study area. No PDF-mining or data requests yet —
that's Phase B/C, which we deliberately deferred.
```
