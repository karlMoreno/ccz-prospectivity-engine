# Phase 0 — The Seven Contracts (v3, TS-6 modernization on a Path C Phase-A corpus)

These files are the **only** coupling between the two development tracks. Once frozen, the engineer (Track E) builds the whole pipeline — including the Phase-A ingestion adapters and normalizers — against them using synthetic fixtures, and the geologist (Track G) runs Path C **Phase A** and fills real data/parameters that satisfy them. **Neither waits on the other.** Integration is "swap a fixture/placeholder for a real file," validated by CI, never a logic merge.

**What changed from v2 (six → seven contracts):** the Path C data plan makes the corpus first-class. **Nothing from v2 was discarded** — every change is additive or an upgrade.

```
CONTRACT                     v3 STATUS      WHAT CHANGED
──────────────────────────────────────────────────────────────────────────────
1 master_observations        UPGRADED       samples.csv → MASTER schema: every row
  (.csv + .schema.json)                      carries evidence_class + provenance +
                                             derivation fields. Superset; abundance
                                             rows still valid. schema_version 3 -> 4
                                             (E1.3 review, 2026-07-27): abundance_kg_m2's
                                             own maximum raised 45 -> 100. At 45 it
                                             exactly matched normalization.yaml's TS-6
                                             screening ceiling, so a value the screening
                                             step should have flagged instead failed
                                             Pydantic validation first -- qa_status=
                                             "flagged" was never reachable for this one
                                             field. Widened to match the headroom
                                             mn/ni/cu/co_pct already had over their own
                                             screening bounds. No other field changed.
2 study_area (+ exclusions)  FROZEN          no change
3 covariates.yaml            FROZEN          Option-A enabled; Option-B disabled.
4 scenarios.yaml             FROZEN          structure same; cutoffs → real ranges.
5 source_queue.yaml          EXPANDED        source_metadata → the PHASE-A SOURCE
  (was source_metadata)                      QUEUE: one entry per Phase-A source with
                                             evidence classes, license, is_open,
                                             sampled area, derivation. version 3.
6 ts6_reference.yaml         MINOR           benchmark surface; note [18]/[19] GRID.
7 normalization.yaml         NEW             per-evidence-class → kg/m² POLICY the
                                             AbundanceNormalizer obeys. version 1.
```

## Why contracts, in design-pattern terms

```text
// The contracts are the concrete form of the STRATEGY seams in the engine, now
// extended to INGESTION. Each interface has two sides that depend only on the
// contract, not on each other's progress — "program to an interface," across people.

                    THE SEVEN CONTRACTS (frozen structure in Phase 0)
   ┌──────┬────────┬───────────┬───────────┬─────────────┬────────┬───────────────┐
   │  1   │   2    │     3     │     4     │      5      │   6    │      7        │
   │master│geometry│covariates │ economics │source-queue │ ts6-ref│ normalization │
   │ obs  │        │           │           │ (Phase A)   │        │ (NEW)         │
   └──┬───┴───┬────┴─────┬─────┴─────┬─────┴──────┬──────┴───┬────┴──────┬────────┘
      │       │          │           │            │          │           │
 E ───┼───────┼──────────┼───────────┼────────────┼──────────┼───────────┤
 (code)│Sample│Terrain   │Feature    │Economic    │Source-   │TS6Ref     │Abundance
      │Source │Source    │recipes    │Model       │Adapter   │+ compare  │Normalizer
      ▼       ▼          ▼           ▼            ▼          ▼           ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │  IngestionPipeline.run()  →  MASTER CORPUS  →  ProspectivityEngine.run() │
   │  (Template Method: adapt→normalize→dedup→validate→append, then model)    │
   └────────────────────────────────────────────────────────────────────────┘
      ▲       ▲          ▲           ▲            ▲          ▲           ▲
 G ───┼───────┼──────────┼───────────┼────────────┼──────────┼───────────┤
 (fills│master│study_area│covariates │scenarios   │Phase-A   │digitized  │policy
  real)│_obs  │.geojson  │.yaml(OptB)│.yaml vals  │downloads │ts6_*.tif  │params
```

## The files

| # | Contract | File(s) | Track E does | Track G does |
|---|----------|---------|--------------|--------------|
| 1 | Master observations | `data/corpus/master_observations.csv` + `docs/contracts/master_observations.schema.json` | loader + evidence-class validation; SampleSource selects MASS rows | run Phase A → populate evidence-typed rows + provenance |
| 2 | AOI geometry | `data/aoi/study_area.geojson` (+ `exclusions.geojson`) | clip/align grid | real study area (public DeepData polygons OK) |
| 3 | Covariate registry | `docs/contracts/covariates.yaml` | implement Option-A recipes; version them | enable/source Option-B TS-6 proxies later |
| 4 | Economic config | `data/economics/scenarios.yaml` | read into `EconomicModel`; watermark while illustrative | real cutoffs (real ranges); flip `illustrative_only` |
| 5 | Phase-A source queue | `data/sources/source_queue.yaml` | one `SourceAdapter` per entry; enforce `is_open` gate | download the queue; fill license/area/hash/accessed |
| 6 | TS-6 reference | `data/ts6/ts6_reference.yaml` (+ `ts6_abundance.tif`) | read via `TS6Reference`; compute agreement | digitize the TS-6 surface; set `role_note` |
| 7 | Normalization policy | `data/config/normalization.yaml` | one `AbundanceNormalizer` per evidence class | confirm geology: areas, mean nodule mass, join tolerance |

> **Data-access reality:** DeepData's nodule **abundance/grade layer is CONFIDENTIAL** with **no public API** — so it is **not** the sample source. The **Phase-A queue** (Contract 5) draws abundance from open PANGAEA/DOMES/Dryad datasets; DeepData's **public** polygons + **GEBCO** bathymetry are context only. Phase B/C are out of the alpha.

## Evidence-class discipline (the rule the corpus enforces)

```text
[MASS]  kg/m²        → the ONLY class the model trains on
[COUNT] nodules/m²   → covariate; → kg/m² only via recorded mean nodule mass
[COVER] % cover      → covariate; NEVER silently converted to kg/m²
[GRID]  compiled     → prior + TS-6 benchmark; NEVER an independent station
[GRADE] Mn/Ni/Cu/Co  → joins to abundance stations; fills metals + economics
```

## Integration checkpoints (fixture → real)

```text
CP0  swap SYNTHETIC sources → REAL Phase-A downloads   (Contracts 1,5,7)  ← EARLY
     (Phase A is a fast numeric download, so the real-corpus swap happens at the START)
CP1  swap synthetic DEM      → real bathymetry.tif      (Contracts 2,5)
CP2  run kriging + RF + baseline on the REAL corpus with spatial CV        (spec feedback)
CP3  swap synthetic ts6 raster → real digitized ts6_abundance.tif          (Contract 6)
CP4  swap placeholder economics → real scenarios.yaml                      (Contract 4)
CP5  publish: real maps + manifest + TS-6 comparison + corpus provenance (alpha launch)
```

## What "frozen" means
- The **structure** of these seven files is fixed in Phase 0. Track E builds against it with confidence.
- The **contents** fill in at checkpoints: Contract 5 downloads, Contract 1 rows, Contract 6 raster, Contract 4 values; Contract 3 Option-B enabled later.
- Any change to a file's **structure** bumps its `*_version`, is noted here, and re-syncs at the next checkpoint.

## Phase 0 done-checklist (v3)

```text
[ ] Both people have read all seven files and agree on the schemas
[ ] master_observations.schema.json (v3) validates the EXAMPLE rows in the CSV (CI wired)
[ ] evidence_class enforced; the [COVER] example row has BLANK abundance_kg_m2
[ ] study_area.geojson loads in QGIS and in the pipeline (placeholder ok)
[ ] covariates.yaml Option-A enabled agreed as the Phase-2 target; Option-B noted
[ ] scenarios.yaml parses; watermark-on-illustrative agreed
[ ] source_queue.yaml: the 10 Phase-A sources present; is_open gate agreed;
    output_license (data + code) set in repo LICENSE
[ ] normalization.yaml: per-class rules agreed; COVER-never-converts confirmed;
    box-core area + mean-nodule-mass source noted
[ ] ts6_reference.yaml agreed; Track E can stub a synthetic ts6 raster
[ ] Track G has started reading TS-6 AND has run (or scheduled) the Phase-A download
[ ] Contracts committed under docs/contracts + data/ and tagged v3-contracts
```

Once green, the tracks separate and run concurrently per Alpha Proposal v3 §10.
