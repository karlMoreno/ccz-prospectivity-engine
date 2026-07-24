# CCZ Prospectivity Engine

## A Living, Open Modernization of ISA Technical Study No. 6 — Version 3.0
### (with an integrated Path C open-data acquisition plan)

**Status:** Technical proposal (major revision)
**What changed in v3:** v2 established *what* we build — an open, reproducible modernization of ISA Technical Study No. 6, with honest uncertainty, a TS-6 benchmark, and an economic layer TS-6 never had. v3 adds the missing half: ***how we actually get the data***. Because DeepData's resource layer is confidential, the sample corpus is assembled from **published, non-confidential sources** (PANGAEA, DOMES, NOAA/NCEI, contractor papers, image surveys). This document folds the **Path C source hunt** into the proposal as a phased acquisition plan, adds the ingestion/normalization machinery to turn 60+ heterogeneous sources into one clean corpus, and threads it through the contracts and the build phases.

**Authorship note:** Sections marked **`[GEOLOGY — ISAAC]`** are gaps for the domain expert. Everything else is engineering-specified, with safe defaults where a geology gap would block a decision.

---

# 1. The anchor: modernizing Technical Study No. 6 (recap)

**ISA Technical Study No. 6 (2010)** — *A Geological Model of Polymetallic Nodule Deposits in the CCZ* — is the artifact we modernize. It already:
- stated our exact thesis (predict grade/abundance from proxies where sampling is sparse),
- used real geostatistics (ordinary kriging + SIS) with error estimates,
- ran prospectivity modeling (weights-of-evidence, logistic regression, fuzzy logic, RBF net),
- and was *designed to be updated* ("No undisclosed or proprietary algorithms … available for updating as better data or better algorithms become available").

It is **not** an open, living, re-runnable tool; it has **no economic layer**; and it was built partly on **proprietary data we cannot reuse**. That gap is the product.

```
TS-6 (2010) IS…                      OUR ENGINE IS…
a static PDF report                  a re-runnable software tool
frozen at 2010 data                  updatable as open data arrives
pure geology                         geology + economic minability layer
built on mixed proprietary data      built on OPEN, published sources (Path C)
figures locked in a document         interactive maps + full provenance
```

**Product thesis:** *We turn TS-6's frozen 2010 model into open, living, reproducible software, add the economic layer, and rebuild it on an openly-assembled abundance corpus — then benchmark our result against TS-6 itself.*

---

# 2. Product definition

> **The CCZ Prospectivity Engine predicts polymetallic-nodule abundance (and, where data allow, metal grade) across a CCZ study area from an openly-sourced sample corpus and terrain/proxy covariates — with honest uncertainty, an economic minability layer, a provenance manifest, and a benchmark comparison to ISA TS-6 — delivered as a re-runnable tool.**

It answers, for any location: *how much resource?* (TS-6 answered — we reproduce), *how confident?* (we modernize), *why?* (we make explorable), and *worth recovering, under what economic regime?* (**new**).

---

# 3. The data reality, and why Path C — plus the five evidence classes

The whole project stands or falls on the sample corpus. Two hard facts shape it:

**Fact 1 — DeepData's resource layer is confidential.** Nodule abundance and grade — the exact ground-truth this engine predicts — are formally confidential under the ISA exploration regulations (ISBA/19/A/9 and related), and there is **no public API**. Even contractor *raw* box-core abundance is typically confidential (confirmed for the German BGR area, whose *biology* is public but whose *modelled nodule abundance* is "classified as being confidential"). So DeepData is **not** the sample source; it is only good for **public context layers** (APEI/contract polygons, environmental geochemistry).

**Fact 2 — a surprising amount of abundance data is genuinely open, but scattered.** Published papers, historic programs (DOMES, 1970s NOAA), and open repositories (PANGAEA, Dryad, Zenodo, Mendeley) expose real station/event-level nodule data. **Path C** is the disciplined harvest of these into one corpus. The Path C source hunt located **60+ sources across six tiers** (full catalog in Appendix A); this section defines the *methodology* that makes them usable.

### The five evidence classes (the central data-modeling idea)

Open "nodule data" is **not one thing**. Conflating the classes is the fastest way to poison the model, so every observation is tagged with exactly one:

```
[MASS]   measured nodule mass / concentration  → kg/m²   (the TRAINING TARGET)
[COUNT]  nodule count / density                → nodules/m²
[COVER]  visible nodule cover from imagery      → % cover
[GRID]   regional compiled/interpolated points/rasters (e.g. TS-6, Washburn)
[GRADE]  chemistry (Mn/Ni/Cu/Co) joinable to an abundance station
```

**Rules that follow directly (and become requirements in §14):**
- **[MASS] is the primary training target.** Everything is normalized *toward* kg/m², but only where physically valid.
- **Never silently convert [COVER] → kg/m².** Percent cover and recovered mass are different measurements; any cover→mass model is empirical, area-specific, and carries its own uncertainty. Cover enters the engine as a **covariate**, or via an explicitly-modelled, uncertainty-tracked conversion — never as a bare abundance value.
- **[COUNT] → [MASS] requires a mean-nodule-mass assumption** (available from individual-nodule datasets, e.g. SO268). Record the assumption and its uncertainty.
- **[GRID] points are predictions/compilations, not independent samples.** They are for regional priors and benchmarking (TS-6), never counted as ground-truth stations.
- **[GRADE] joins to abundance stations** by cruise/event/coordinates; it populates the optional metal columns (Contract 1) and feeds the economic layer.

This five-class discipline is itself a contribution: **nobody has assembled an open, evidence-typed, reproducible CCZ abundance training set.**

---

# 4. The tiered source catalog (summary)

Path C organizes sources into six tiers by *how usable* they are. Full catalog with links and per-source notes is **Appendix A**; here is the shape and the anchors:

```
TIER 1  INGEST NOW — direct numeric or derivable sample data
        SO268 box-core summary [01] (mass ×4 → kg/m²), DOMES floor-density
        [02] (already kg/m²), DOMES Piper [03], SO268 individual nodules [05],
        Dryad chamber [06], APEI-6 counts [07], Deep Sea Ventures legacy [08].
        → the first tables loaded; genuine station/event kg/m² or derivable.

TIER 2  OPEN IMAGE-FRAME cover/count + georeferenced seafloor data
        Amon 2016 UK-1 frames [11], APEI-6 cover gradient [12], SO268 OFOS
        imagery [13], GSR collector-site cover [14], KIOST/Zenodo sets [15-17].
        → covariates and cover evidence; NOT bare kg/m².

TIER 3  REGIONAL grids / maps / historic compilations  ([GRID])
        TS-6 [18] (our benchmark), Washburn 2021 0.5° resource points [19],
        GRID-Arendal map [20], USGS OFR 78-814 [21], USGS Bull. 1689-A [22],
        AOM/TOML technical reports [23-24].
        → priors + benchmark; label as compiled, never independent stations.

TIER 4  CONTRACTOR / NATIONAL papers with PRIMARY sample data
        BGR: Minerals 2021 [25], EIS [26], RWTH thesis (55 E1 cores) [27],
        Knobloch [28]. IOM: image-abundance [31], H22_NE [32], survey
        overviews [33-36]. Korea/KIOST [39-40]. Soviet [41-42]. IFREMER/
        NODINAUT [43-44]. GSR [45-46].
        → best abundance ranges + cutoff economics; often DIGITIZE/CONTACT.

TIER 5  METAL-GRADE datasets to JOIN to abundance stations
        Scripps chemistry [47], MANOP [48], SO268/collector chem [49-50],
        DOMES Site A AAS/NAA [51-52], NOAA/NCEI + CNEXO + Scripps [53-57],
        Korean sediment geochem [58], SO239 radioisotopes [59].

TIER 6  SPATIAL-REFERENCE + discovery hubs
        GSR contract-area ArcGIS layer [61], BGR marine-resources home [62],
        IOM history/publications [63].
```

The **highest-value, lowest-effort** anchors are the PANGAEA **SO268** and **DOMES** records (Tier 1 — real numeric kg/m² or trivially derivable) plus **TS-6/Washburn** (Tier 3 — the regional benchmark). The **largest remaining prize** is recovering the published-but-unattached input tables behind BGR/IOM/KIOST/GSR (Tier 4) via targeted requests.

---

# 5. The data-acquisition plan — three phases (this is "how we do it")

Path C's ingestion order is a three-phase workstream, run by Track G during project Phases 0–1 (see §16). Each phase has a clear cost profile and exit test.

```
PHASE A — ONE-DAY DOWNLOAD QUEUE   (cheap, fast, do first)
  Directly downloadable numeric data → ingest immediately.
  Queue: [01] SO268 box-core summary → [02] DOMES floor density →
         [03] DOMES Piper → [04] DOMES Site C → [05] SO268 individual
         nodules → [06] Dryad chamber → [11] Amon image table →
         [12] APEI-6 cover → [14] GSR Mendeley → [18]-[19] TS-6/Washburn grid.
  Output: the first populated master-catalog rows (kg/m² where [MASS];
          derived kg/m² where [DERIVE]; cover/count tagged as such).
  EXIT: a machine-readable corpus with ≥ (target) station/event kg/m²
        observations + the regional benchmark loaded. This alone may be
        enough to build the whole pipeline on REAL (not synthetic) data.

PHASE B — PDF & SUPPLEMENT EXTRACTION   (medium effort)
  Values live in figures/tables/supplements → extract + digitize.
  Targets: [25]-[28] BGR papers/thesis/EIS; [31]-[36] IOM; [39]-[40]
           Korea/KIOST; [41] Soviet; [43]-[44] IFREMER/NODINAUT;
           [23]-[24] commercial technical reports.
  Method: table extraction (Camelot/Tabula) for tabular PDFs;
          georeference + digitize contour maps only where no table exists;
          record figure/table id + digitization method as provenance.
  EXIT: BGR/IOM/Korea abundance ranges + cutoff economics captured;
        gaps in Phase-A coverage filled or explicitly marked as requests.

PHASE C — TARGETED DATA REQUESTS   (slow; only specific, non-confidential asks)
  Request ONLY clearly non-confidential tables that papers reference:
    • BGR: the 55 E1 box-core abundance/grade inputs (RWTH thesis) + wet/dry meta.
    • IOM: the 63 paired box-core/photo records (2020); the 13 H22_NE
      abundances (2025); the ~448–500-station input matrices.
    • KIOST: the free-fall-grab abundance table behind Lee & Kim (2004).
    • GSR/MiningImpact: observed kg/m² at B4S03/B6S02 + collector-trial stations.
    • IFREMER: NODINAUT/BIONOD station-level cover/count/mass already published.
  EXIT: any granted tables ingested with provenance; ungranted ones closed
        out as "unavailable" (not silently assumed). Corpus frozen for v1.
```

**Why phased this way:** Phase A converts effort into a *working real-data corpus* in about a day, which de-risks the entire engineering track immediately (no more waiting on synthetic fixtures). Phase B and C are strictly *additive* — the pipeline already runs on Phase-A data, so slow extraction and slower requests never block the build. This mirrors the two-track decoupling: the corpus grows through A→B→C while the engine is built in parallel.

---

# 6. Ingestion & normalization architecture (the machinery, with patterns)

Sixty-plus sources arrive in incompatible shapes (PANGAEA tab files, NOAA dBase, PDF tables, image-frame CSVs, ArcGIS FeatureServers). They must land in **one** schema, be normalized toward kg/m² *only where valid*, and be de-duplicated. Four classic patterns do this, chosen because they map onto the real problems:

```
// ADAPTER PATTERN — one SourceAdapter per source (or source family) converts
// that source's native format into the MasterObservation schema. WHY: the
// pipeline must not know that PANGAEA is tab-delimited, NOAA is dBase, or a
// BGR value came from a digitized figure. Add a source = add an adapter; the
// rest of the pipeline is untouched. (Directly parallels TerrainSource /
// SampleSource in the engine — program to the interface, not the format.)
//
// STRATEGY PATTERN — one AbundanceNormalizer per EVIDENCE CLASS decides how
// (or whether) to produce kg/m². WHY: [MASS] just rescales by sampled area;
// [COUNT] needs a mean-nodule-mass model; [COVER] must NOT be silently
// converted (it returns a covariate + an optional uncertainty-tracked
// estimate); [GRID] is flagged non-independent. Swapping conversion logic
// never touches ingestion or modeling.
//
// TEMPLATE METHOD — IngestionPipeline.run() fixes the sequence:
//   fetch → adapt → normalize → dedup → validate → append-to-corpus.
// WHY: every source is processed by the SAME honest steps in the SAME order,
// so no source can skip provenance capture or dedup.
//
// SPECIFICATION PATTERN — dedup and quality rules are composable predicates
// (isDuplicateOf, isValidStation, isIndependentSample). WHY: the CRITICAL
// DUPLICATE RULES (DOMES families, NOAA↔PANGAEA mirrors, nodules nested in
// events) are declarative, testable, and reusable rather than buried in ifs.

┌───────────────────────────────────────────────────────────────────────┐
│                     <<Template Method>> IngestionPipeline              │
│  + run(source) : void                                                  │
│    # fetch()          → raw bytes/rows (or a manual-extract handoff)    │
│    # adapt()          → SourceAdapter.to_master(raw)  ← ADAPTER         │
│    # normalize()      → AbundanceNormalizer.to_kg_m2(obs)  ← STRATEGY   │
│    # dedup()          → DuplicateSpec.filter(obs, corpus) ← SPECIFICATION│
│    # validate()       → QualitySpec.check(obs)           ← SPECIFICATION │
│    # append()         → master corpus (Contract 1 rows + provenance)   │
└───┬───────────────────────┬───────────────────────┬───────────────────┘
    │ uses                  │ uses                  │ uses
    ▼                       ▼                       ▼
┌──────────────┐     ┌────────────────────┐   ┌──────────────────────┐
│<<interface>> │     │<<interface>>       │   │<<interface>>         │
│SourceAdapter │     │AbundanceNormalizer │   │Specification         │
│+ to_master() │     │+ to_kg_m2(obs)     │   │+ is_satisfied(obs)   │
└──┬────────┬──┘     └──┬──────────┬──────┘   └──┬───────────────┬───┘
   ▼        ▼           ▼          ▼             ▼               ▼
Pangaea  NoaaDbase   MassNorm   CoverNorm    DuplicateSpec   QualitySpec
Adapter  Adapter    (×1/area)  (COVAR only, (DOMES families, (coords valid,
PdfTable ArcGIS      CountNorm   no bare      NOAA↔PANGAEA,   area known,
Adapter  Adapter    (needs mean  kg/m²)       nodules⊂event)  class tagged)
                     nodule mass) GridNorm
                                 (flag non-
                                  independent)
```

The **MasterObservation** they all produce is the master-catalog schema (Appendix B), which is a superset of Contract 1's `samples.csv`: the engine's `SampleSource` reads the `[MASS]` rows (with valid `abundance_kg_m2`) as training data; the other classes feed covariates, grade joins, or benchmarking.

---

# 7. What the ISA already learned (covariates + value ranges)

TS-6 ran the covariate experiment; we inherit the answer key (drives Option A/B in §9):

```
PROXY                     TS-6 FINDING                          USE
surface chlorophyll       best single metal-content predictor    Option B (proxy)
                          (~0.49 R² Mn); non-linear
sediment type             strongest OCCURRENCE correlate;         Option B (proxy)
                          siliceous favorable, calcareous not
bathymetric regime        2nd/3rd; abyssal hills favorable        Option B (from DEM)
CCD minus depth           improves Cu regression                  Option B (proxy)
terrain (slope/rough/     available free from any DEM             Option A (build first)
curvature/TPI/BPI)
```

Realistic value ranges (calibration + fixtures + economic anchoring):
```
Abundance:  region-wide mean ~5–7 kg/m² (TS-6, spans low areas), median ~5.5,
            max ~24–44; BGR Area E1 mean ~19 kg/m² wet (rich sub-area);
            GSR trial site ~20–24 kg/m² wet; IOM H22_NE ~10–20 kg/m² wet.
Grade (dry): Mn ~28–29%, Ni ~1.3%, Cu ~1.1%, Co ~0.22%.
Pattern:    richer center+north, poorer south/SW (all TS-6 SDSS methods agree).
Bias:       free-fall grab samplers UNDERestimate abundance → many values are
            lower bounds; record sample_method so this is modellable.
```

---

# 8. Product boundaries

**Will do:** ingest + evidence-type + normalize an open abundance corpus; predict abundance with uncertainty; economic minability (market vs strategic); provenance manifest; TS-6 benchmark; re-run as the corpus grows; port to other bodies later.

**Will not initially do:** invent new geostatistics; claim a confident "mine here" verdict; reproduce all four TS-6 SDSS methods in v1; use/redistribute confidential contractor data; convert cover→mass silently; ship the lunar port.

**Honesty boundary:** proxies are indirect and the corpus is a *blend* of evidence classes and eras; every output is a scenario estimate with quantified uncertainty, never ground truth.

---

# 9. System architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  OPEN SOURCES (Path C, Appendix A)                                        │
│  PANGAEA · DOMES · NOAA/NCEI · Dryad/Zenodo/Mendeley · contractor PDFs ·   │
│  image surveys · TS-6/Washburn grids · GEBCO bathymetry · DeepData PUBLIC  │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  INGESTION + NORMALIZATION  (§6: Adapter · Strategy · Template · Spec)     │
│  adapt → normalize-to-kg/m² (valid classes only) → dedup → validate →      │
│  MASTER CORPUS (evidence-typed, provenance per observation)               │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  QA + GRID ALIGNMENT   (reproject WGS84 · hash · license/is_open gate)     │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  FEATURE ENGINEERING   terrain (Option A) [+ proxies Option B]            │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  MODELING   ordinary kriging (TS-6 parity) · random forest · mean baseline │
│             — trains on [MASS] rows; [COVER]/[COUNT] as covariates         │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  VALIDATION (spatial CV + baseline + TS-6 benchmark) → PREDICT + UNCERTAINTY│
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ECONOMIC OVERLAY (market vs strategic) → minable + difference map         │
└───────────────┬────────────────────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  OUTPUT STORE + PROVENANCE MANIFEST → read-only API → thin web viewer      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 10. The portable core (design that makes modernization + the lunar port cheap)

```
// STRATEGY — TerrainSource, SampleSource, ProxySource, Estimator, EconomicModel,
// TS6Reference are interfaces with swappable implementations. Plus (new in v3)
// SourceAdapter + AbundanceNormalizer for ingestion. WHY: add a data source, a
// covariate, a model, or a whole new body (Moon) = add classes, not rewrites.
//
// TEMPLATE METHOD — two fixed sequences: IngestionPipeline.run() (§6) and
// ProspectivityEngine.run() (ingest→features→CV→predict→uncertainty→economics
// →compare_to_ts6→manifest). WHY: the same honest steps every time; nothing
// can skip spatial CV, provenance, or dedup.

           <<abstract>> ProspectivityEngine.run()  ← Template Method
   ┌──────────┬───────────┬────────────┬──────────┬───────────┐
   ▼          ▼           ▼            ▼          ▼           ▼
 Terrain    Sample      Proxy       Estimator  Economic    TS6
 Source     Source      Source                 Model       Reference
 (Bathy/    (MASS rows  (sediment/  (Kriging/  (Market/    (benchmark
  Lola)      from corpus chloro/CCD)  RF)       Strategic)   surface)
             ← §6 corpus)
```

v1 builds the CCZ + Option-A classes; Option-B proxies, the Moon classes, and additional `SourceAdapter`s attach through the same seams.

---

# 11. Technology stack

| Concern | Tools |
| --- | --- |
| Language | Python 3.11+ |
| **Ingestion (new)** | `pandas`; `pangaeapy` (PANGAEA DOIs → dataframes); `requests`; `Camelot`/`Tabula-py` (PDF tables); `pdfplumber`; QGIS (georeference/digitize maps); `openpyxl` (Dryad/xlsx) |
| Raster I/O / terrain | Rasterio; RichDEM / xarray-spatial |
| Kriging (TS-6 parity) | scikit-gstat / PyKrige |
| ML + CV | scikit-learn; spatial blocks via `verde` / GroupKFold |
| Vector data | GeoPandas + Shapely |
| Config validation | Pydantic (MasterObservation + contract schemas) |
| API + storage | FastAPI (read-only); COG rasters; PostGIS metadata; MinIO |
| Viewer (thin) | Next.js + MapLibre GL JS + deck.gl |
| Reproducibility | `uv`/pip-tools (hash-pinned); Docker; DVC (dataset versioning); Papermill; GitHub Actions; MkDocs |
| Licensing | MIT/Apache-2.0 (code); CC-BY (data outputs) |

No Kubernetes/queues/clusters; a CCZ run is minutes on a laptop.

---

# 12. Core domain model

```
Observation (MasterObservation)  ← one open record; superset of Contract 1
    ├── evidence_class            [MASS|COUNT|COVER|GRID|GRADE]
    ├── coords + water_depth + sample_method + sampled_area_m2
    ├── abundance_kg_m2 (+ *_original + basis wet/dry) | count | cover% | grade%
    ├── source provenance (id/doi/url/license/is_open/accessed) + derivation_formula
    └── observation_or_prediction + quality_grade + duplicate_group_id

StudyArea · TerrainLayer · ProxyLayer(Option B) · Model/ModelRun ·
PredictionResult(prediction+uncertainty+CV+TS6_agreement+economics) ·
EconomicScenario(new vs TS-6) · TS6Reference(benchmark) · ProvenanceManifest
```

The engine's `SampleSource` selects `evidence_class == MASS AND abundance_kg_m2 IS NOT NULL AND is_open`.

---

# 13. The economic overlay (the layer TS-6 never had)

```
// STRATEGY — EconomicModel is an interface; each scenario is an implementation.
// The same prediction surface is re-scored under different cutoffs without
// re-running the model.
prediction + scenario.params → minability(cell) = metric ≥ cutoff AND not
excluded (APEI) AND passes spatial filters → minable footprint → difference map.
```
Two scenarios: **MARKET_STANDARD** (commercial cutoff) and **STRATEGIC_SUBSIDIZED** (lower, supply-security cutoff). The **difference map** — ground only a strategic regime unlocks — is the headline output. Cutoffs anchor to real ranges (e.g. BGR "significant drop above 10 kg/m²"). `[GEOLOGY — ISAAC]` sets real values; placeholders ship watermarked "illustrative only."

---

# 14. Functional requirements

**Carried from v2:** PR-001 terrain/proxy ingestion · PR-002 sample ingestion + QA · PR-003 feature engineering · PR-004 modeling (kriging + RF + baseline) · PR-005 **spatial CV (mandatory)** · PR-006 prediction + paired uncertainty · PR-007 economic overlays · PR-008 TS-6 comparison · PR-009 provenance manifest · PR-010 read-only API + thin viewer · PR-011 reproducible run harness.

**New in v3 — data acquisition (DA series):**

## DA-01: Source adapters
For every ingested source, a `SourceAdapter` maps its native format into the MasterObservation schema. Adding a source must not modify the pipeline. Adapter records source id/DOI/url/license/`is_open`/accessed-date.

## DA-02: Evidence-class tagging (mandatory)
Every observation carries exactly one `evidence_class` ∈ {MASS, COUNT, COVER, GRID, GRADE}. No observation enters the corpus untagged.

## DA-03: Abundance normalization by class
A per-class `AbundanceNormalizer` produces `abundance_kg_m2` **only where physically valid**: [MASS] rescale by `sampled_area_m2` (e.g. box-core ×4 for 0.25 m²); [COUNT] via a recorded mean-nodule-mass model (+ uncertainty); [COVER] **must not** yield a bare kg/m² — it returns a covariate and, optionally, an explicitly-modelled estimate with its own uncertainty; [GRID] is flagged `observation_or_prediction = prediction/compiled` and excluded from training.

## DA-04: Provenance per observation
Every row records source, license, `is_open`, retrieval date, `abundance_*_original` + unit + basis (wet/dry), and `derivation_formula` where a value was computed. Only `is_open == true` rows may enter a PUBLISHED run.

## DA-05: Deduplication (Specification rules)
Composable `DuplicateSpec` predicates enforce the critical duplicate rules: DOMES publication families deduped by cruise+station+coords+date (not DOI); NOAA↔PANGAEA mirrors reconciled (retain both provenance links); individual nodules treated as nested within their box-core **event** (the event is the spatial sample); image cover never merged with recovered mass.

## DA-06: Evidence-class integrity in modeling
The modeling layer trains on [MASS] rows only; [COVER]/[COUNT] may be covariates; [GRID] may be a prior/benchmark. Any cover→mass conversion model is stored separately with its uncertainty and never overwrites an observed value.

## DA-07: Grade join
[GRADE] records join to abundance stations by station-id, else cruise+event+coords within a recorded tolerance; joins populate Contract-1 metal columns and feed the economic layer. Join method + tolerance recorded.

## DA-08: Corpus manifest + phase provenance
The corpus records which acquisition phase (A/B/C) each source came from, and for Phase-B digitized values, the figure/table id + digitization method. The run manifest references the corpus manifest so a third party can trace every training point to a source.

---

# 15. Non-functional requirements

- **Reproducibility:** per-run + per-corpus manifest; hash-pinned deps; CI runs the full loop on fixtures every push.
- **Scientific honesty:** spatial CV mandatory; mean baseline always; uncertainty always paired; evidence classes never conflated; economic maps print assumptions.
- **Open-data gate:** only `is_open == true` sources in a published run; confidential contractor/DeepData resource data excluded; TS-6/contractor figures used as benchmarks/inputs under fair use, not redistributed as datasets.
- **Provenance depth:** every training point traces to a source record and (if derived/digitized) its formula/figure.
- **Spatial consistency:** canonical EPSG:4326; one analysis grid; invalid geometries rejected.
- **Performance:** one CCZ run in minutes on a laptop.

---

# 16. Development phases and exit criteria

The engine phases (0–6) run in parallel with the data-acquisition phases (A/B/C). Data Phase A lands inside project Phase 0–1; B and C are additive and never block the build.

```
PROJECT PHASE 0 — specification + TS-6 study + DATA PHASE A
  [E] repo, Docker, the interfaces (incl. SourceAdapter/AbundanceNormalizer),
      synthetic fixtures, CI skeleton.
  [G] read TS-6; run DATA PHASE A (one-day download queue, §5) → first REAL
      corpus rows; pull public DeepData polygons; pick GEBCO bathymetry.
  EXIT: contracts frozen; a real (if small) [MASS] corpus + benchmark loaded;
        CCZ-first vs Moon-first decided on Phase-A yield.

PROJECT PHASE 1 — ingestion + features (one AOI) + DATA PHASE B begins
  [E] real SourceAdapters for the Phase-A sources; normalization + dedup +
      validation; terrain feature stack (Option A); plot corpus over the DEM.
  [G] DATA PHASE B (PDF/supplement extraction) → BGR/IOM/Korea abundance +
      cutoff economics; QA rules; covariate spec.
  EXIT: one AOI loads a real evidence-typed corpus; covariate stack versioned.

PROJECT PHASE 2 — modeling + spatial validation
  [E] kriging + RF + baseline; spatial blocked CV; refuse-to-validate guard.
  [G] credible metrics + acceptance thresholds; begin economic parameters.
  EXIT: spatially-honest CV scores; uplift over baseline.

PROJECT PHASE 3 — prediction + uncertainty + TS-6 comparison  (DATA PHASE C runs)
  [E] prediction + uncertainty COGs; compare_to_ts6; manifest emitter.
  [G] digitize TS-6 surface (Contract 6); DATA PHASE C targeted requests.
  EXIT: full run → prediction+uncertainty+TS-6 agreement+manifest.

PROJECT PHASE 4 — economic overlay (new layer)
  [E] EconomicModel + two scenarios (placeholders→real) + difference map.
  [G] real cutoffs/grades (anchored to Tier-4 ranges) + caveats.
  EXIT: two minable footprints + difference map with assumptions attached.

PROJECT PHASE 5 — delivery: API, viewer, docs, release
  EXIT: visitor opens AOI · sees prediction+uncertainty · switches scenarios ·
        sees TS-6 comparison · reads methodology · reaches manifest.

PROJECT PHASE 6 — Option B (TS-6 proxies) and/or lunar portability proof.
```

---

# 17. Funding strategy (open-core / grant-funded), sharpened

```
LAYER 1  open core — the engine + a living, open modernization of ISA TS-6,
         built on an openly-assembled abundance corpus (the credibility asset).
LAYER 2  grants — ocean science / open data / critical minerals. Pitch: "we
         openly re-analyze, on public sources, what the ISA's confidential
         model did privately — and we assembled the first open, evidence-typed
         CCZ abundance corpus." Potential collaborator: ISA or DeepData users.
LAYER 3  bespoke reproducible, uncertainty-quantified site reports.
LAYER 4  career return — resource-estimation artifact benchmarked against an
         intergovernmental model (geologist) + portable geospatial-ML + open
         data pipeline (engineer).
```
The corpus itself is publishable (CC-BY) and citable — a contribution independent of the engine.

---

# 18. Risks and mitigations

- **No usable open abundance corpus — #1 risk.** *Mitigation:* Data Phase A targets sources that are *already numeric* (SO268, DOMES) — genuine kg/m² or trivially derivable — so a real corpus exists after ~a day; Phases B/C add depth. If Phase A under-yields, flip to Moon-first (the engine is built on fixtures regardless).
- **Evidence-class contamination** (cover treated as mass, grid as stations). *Mitigation:* DA-02/03/06 + the AbundanceNormalizer strategy make conflation impossible by construction; cover→mass is never silent.
- **Double-counting duplicates** (DOMES families, NOAA↔PANGAEA, nodules⊂events). *Mitigation:* DA-05 Specification rules; dedup by cruise+station+coords+date, not DOI.
- **Digitization / derivation error** (Phase B maps, count→mass). *Mitigation:* record figure/table id + formula + uncertainty (DA-04/08); prefer tables over maps; treat derived values as lower-confidence `quality_grade`.
- **Request dependence** (Phase C tables may never arrive). *Mitigation:* Phase C is additive-only; ungranted asks are closed as "unavailable," never assumed; the engine ships on Phase A/B data.
- **Grab-sampler underestimation bias.** *Mitigation:* record `sample_method`; model/report it as a lower-bound caveat.
- **Overclaiming novelty vs TS-6.** *Mitigation:* claim only the true differentiators (open/living/reproducible tooling + economic layer + open-corpus re-analysis); the TS-6 agreement score keeps it honest.
- **Confidential-data / license violation.** *Mitigation:* `is_open` gate (DA-04); benchmarks used, not redistributed; per-source license recorded.

---

# 19. Recommended immediate objective

> **Run Data Phase A (the one-day download queue), assemble a real evidence-typed [MASS] corpus for one CCZ study area, and drive one ordinary-kriging run end-to-end — spatial CV, paired uncertainty, TS-6 benchmark, provenance manifest — from that real corpus.**

Do not begin with the economic layer, the viewer, Option-B proxies, Phase-C requests, or the lunar port. Once one honest, reproducible, TS-6-benchmarked CCZ prediction exists — built on an openly-sourced corpus behind clean adapter/estimator/economics interfaces — everything else attaches to a stable, credible core.

---

# Appendix A — Path C source catalog (condensed ingestion queue)

Flags: [NOW] direct numeric · [DERIVE] compute kg/m² · [SUPP] in supplements · [DIGITIZE] figures/maps · [CONTACT] request · [HUB] directory. Evidence: [MASS]/[COUNT]/[COVER]/[GRID]/[GRADE].

### Tier 1 — ingest now (direct numeric or derivable)
```
[01] SO268 box-core summary — PANGAEA 10.1594/PANGAEA.904967 — [NOW][MASS][COUNT][COVER]
     mass ×4 → kg/m² (0.25 m² cores); FIRST modern contractor-area table. CC BY-NC 4.0
[02] DOMES floor density (Fewkes 1980) — 10.1594/PANGAEA.878220 — [NOW][MASS] already kg/m². CC BY 3.0
[03] DOMES abundance+seafloor (Piper 1979) — 10.1594/PANGAEA.880886 — [NOW][MASS][COVER]. CC BY 3.0
[04] DOMES Site C size/weight (Sorem 1989) — 10.1594/PANGAEA.879534 — [DERIVE][MASS][COUNT]
[05] SO268 individual nodules (~9,000) — 10.1594/PANGAEA.904962 — [DERIVE] aggregate to event. CC BY-NC 4.0
[06] Dryad CCZ chamber + nodule abundance — 10.5061/dryad.tdz08kq6w — [NOW][MASS][DERIVE]
[07] APEI-6 box-core density (Durden) — 10.1007/s12526-017-0636-0 — [NOW][COUNT] 338 nod/m²
[08] Deep Sea Ventures / R.V. Prospector 1976 — 10.1594/PANGAEA.871493 — [NOW][COUNT][MASS][DIGITIZE]
[09][10] DOMES parent series — 10.1594/PANGAEA.878223 / .880888 — [HUB][DUPLICATE] provenance only
```
### Tier 2 — open image-frame cover/count + georeferenced
```
[11] Amon 2016 UK-1/EPIRB frames — nature.com/articles/srep30492 (PMC4965819) — [SUPP][COUNT][COVER]
[12] APEI-6 cover gradient (Simon-Lledó) — 10.1594/PANGAEA.893220 — [NOW][COVER]
[13] SO268 OFOS imagery — 10.1594/PANGAEA.935856 (children .935889/.935887) — [NOW][COVER][DERIVE]
[14] GSR collector-site cover — data.mendeley.com/datasets/7jst5wyc6j/1 — [NOW][COVER]. CC BY 4.0
[15] KIOST south-central CCZ — zenodo.org/records/17395318 — [NOW][COVER][HUB]
[16] Abyssal NE Pacific megafauna imagery — zenodo.org/records/7982462 — [NOW][COVER][HUB]
[17] DeepCCZ synthesis + nodule size — 10.5281/zenodo.4214934 — [NOW][COUNT][HUB]
```
### Tier 3 — regional grids / maps / historic compilations ([GRID], not independent stations)
```
[18] ISA TS-6 geological model — isa.org.jm/.../GeoMod.pdf — [GRID][DIGITIZE] — OUR BENCHMARK
[19] Washburn 2021 0.5° resource points — frontiersin.org 10.3389/fmars.2021.661685 — [SUPP][GRID]
[20] GRID-Arendal CCZ abundance map — grida.no/resources/7354 — [GRID][DIGITIZE] cross-check
[21] USGS OFR 78-814 — 10.3133/ofr78814 — [GRID][DIGITIZE]
[22] USGS Bull. 1689-A — pubs.usgs.gov/bul/1689a/report.pdf — [GRID][DIGITIZE] kg/m² tables
[23] AOM Area 1 tech report — sec.gov EDGAR d104064dex963 — [GRID][DIGITIZE][CONTACT]
[24] TOML CCZ project report — ResearchGate 309315120 — [GRID][DIGITIZE][CONTACT]
```
### Tier 4 — contractor/national papers with primary sample data
```
BGR: [25] Minerals 2021 mdpi.com/2075-163X/11/6/618 [MASS][DIGITIZE][CONTACT] — abundance + cutoff economics
     [26] BGR EIS (harvester test) bgr.bund.de …2025_Manganknollen…EIS [MASS][DIGITIZE]
     [27] RWTH thesis (55 E1 cores) publications.rwth-aachen.de/record/761787 [MASS][GRADE][DIGITIZE]
     [28] Knobloch predictive mapping 10.1007/978-3-319-52557-0_6 [MASS][GRID][DIGITIZE]
     [29][30] BGR hubs/logbook [HUB]
IOM: [31] image-abundance (63 paired) mdpi.com/2075-163X/10/3/263 [MASS][COVER][DIGITIZE][CONTACT]
     [32] H22_NE (13 stations, ~10–20 kg/m²) mdpi.com/2075-163X/15/2/154 [MASS][GRADE][SUPP]
     [33]-[36] IOM survey overviews (~448–500 stations) ResearchGate [MASS][GRADE][DIGITIZE][CONTACT]
     [37][38] IOM directory + 2024 cruise [HUB]
Korea:[39] Lee & Kim 2004 (free-fall grab) 10.1080/10641190490473434 [MASS][COVER][DIGITIZE][CONTACT]
     [40] KIOST/KODOS 1994 sciwatch.kiost.ac.kr/…/6460 [MASS][DIGITIZE]
Soviet:[41] Local variations 1992 sciencedirect …002532279290028G [MASS][GRADE][DIGITIZE]
     [42] Barash & Kruglikova stations 10.1594/PANGAEA.727500 [NOW][GRADE][HUB]
France:[43] IOC Tech Series 69 jodc.go.jp/…/149556e.pdf [COVER][COUNT][DIGITIZE][HUB]
     [44] NODINAUT recovery study (CiteSeerX PDF) [COUNT][COVER][DIGITIZE]
GSR: [45] Frontiers 2024 trial 10.3389/fmars.2024.1380530 [MASS][COVER][DIGITIZE] ~20–24 kg/m²
     [46] GSRNOD17 / De Smet ref 10.1525/elementa.2025.000016 [MASS][DIGITIZE][CONTACT]
```
### Tier 5 — metal-grade datasets to join to abundance stations
```
[47] Scripps chemistry 10.1594/PANGAEA.957326 · [48] MANOP 10.1594/PANGAEA.961506
[49] SO268/collector chem 10.1594/PANGAEA.960339 · [50] intl collector chem 10.1594/PANGAEA.961091
[51] DOMES Site A AAS 10.1594/PANGAEA.877894 · [52] DOMES Site A NAA 10.1594/PANGAEA.877895
[53] NOAA/NCEI Marine Minerals ngdc.noaa.gov/mgg/geology/mmdb.html [HUB][DUPLICATE]
[54] NCEI CD-ROM docs · [55] Scripps Mn Nodule file · [56] NCEI Scripps descriptions
[57] CNEXO worldwide compilation (data.gov) · [58] Korean sediment geochem 10.1594/PANGAEA.945266
[59] SO239 radioisotopes + station crosswalk 10.1594/PANGAEA.951145 · [60] Valdivia 1974 10.1594/PANGAEA.868735
```
### Tier 6 — spatial reference + discovery hubs
```
[61] GSR contract-area ArcGIS FeatureServer · [62] BGR marine resources home · [63] IOM history/publications
```

# Appendix B — Master catalog schema + critical duplicate rules

```
MASTER OBSERVATION (superset of Contract 1 samples.csv):
 source_record_id · source_title · source_url · source_doi · source_type ·
 source_accessed_date · license · is_open · cruise · expedition_leg ·
 contractor_or_area · station_id · event_id · sample_datetime_utc ·
 latitude · longitude · water_depth_m · sample_method · sampled_area_m2 ·
 evidence_class[MASS|COUNT|COVER|GRID|GRADE] ·
 abundance_value_original · abundance_unit_original · abundance_basis[wet|dry|unknown] ·
 nodule_mass_kg · abundance_kg_m2 · nodule_count · nodule_density_m2 ·
 visible_cover_percent · buried_nodule_count · mean_nodule_mass_g · median_nodule_size_mm ·
 cu_percent · ni_percent · co_percent · mn_percent · fe_percent ·
 derivation_formula · observation_or_prediction[observed|compiled|interpolated|modelled] ·
 quality_grade · duplicate_group_id · notes

CRITICAL DUPLICATE RULES (DA-05 Specifications):
 1. DOMES families [02][03][04][09][10] — dedupe by cruise+station/event+coords+date, not DOI.
 2. NOAA↔PANGAEA mirrors [53]-[57] — prefer clearest methods; retain both provenance links.
 3. Regional compilations [18]-[24] — label compiled/grid until a raw station is recovered.
 4. Individual nodules [05] are nested within box-core events [01] — the EVENT is the spatial sample.
 5. Image cover/count ≠ recovered mass — never silently convert; store any conversion model + its uncertainty separately.
```

# Appendix C — `[GEOLOGY — ISAAC]` open items

```
DATA ACQUISITION (Path C)
[ ] Run Data Phase A queue; populate MasterObservation rows; confirm [MASS] count.
[ ] Decide study area by data density (BGR E1/PA1 · SO239 footprint · IOM · DOMES).
[ ] For each [DERIVE] source, confirm sampled_area_m2 + wet/dry basis before computing kg/m².
[ ] Phase B: extract BGR/IOM/Korea abundance + cutoff economics from PDFs; record figure/table ids.
[ ] Phase C: draft the specific non-confidential table requests (BGR 55, IOM 63/13/500, KIOST, GSR, IFREMER).
SCIENCE
[ ] Final covariate list (Option A now; Option-B TS-6 proxies later).
[ ] Credible validation metrics + acceptable TS-6 agreement; interpret divergence.
[ ] Which evidence classes to admit as covariates vs excluded.
ECONOMICS
[ ] Grade units; metals driving value; realistic MARKET & STRATEGIC cutoffs (anchor to Tier-4 ranges); caveats.
INTERPRETATION
[ ] Sanity-check vs known geology AND vs TS-6; write the "modernizing TS-6" methodology chapter + impact narrative.
```

# Appendix D — inherited from TS-6 vs newly built

```
INHERITED / REPRODUCED                 NEWLY BUILT (our contribution)
core thesis (proxies where sparse)     open, living, re-runnable software
ordinary kriging                       honest spatial cross-validation
the proven covariates (§7)             OPEN, EVIDENCE-TYPED abundance corpus (Path C)
error/uncertainty estimation           reproducible-by-anyone provenance (per observation)
realistic ranges + spatial pattern     ECONOMIC minability layer (market vs strategic)
prospectivity concept                  ingestion machinery (Adapter/Strategy/Spec)
                                        explicit TS-6 agreement benchmark
                                        portability to other bodies (Moon)
```
