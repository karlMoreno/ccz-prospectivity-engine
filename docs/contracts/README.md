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
                                             PHYSICAL rationale for 100 (added 2026-07-29,
                                             P3 — previously only the mechanical one was
                                             recorded): ~100 kg/m2 is ~1.7x the ~60 kg/m2
                                             close-packed monolayer limit (5 cm nodules,
                                             ~2 g/cm3 wet bulk density, ~60% areal
                                             packing). Published CCZ abundances run
                                             ~1.5-30 kg/m2 and this corpus tops out at
                                             26.8, so the bound rejects unit and
                                             transcription errors (a g/m2 value read as
                                             kg/m2, a misplaced decimal) without
                                             rejecting an extreme-but-physically-real
                                             reading. It is a PLAUSIBILITY ceiling, not a
                                             screening threshold — 45 (normalization.yaml)
                                             remains the soft bound that flags.
                                             schema_version 4 -> 5 (P2.0c, 2026-08-08):
                                             METADATA-ONLY origin markers — see the
                                             shared P2.0c note under this table.
2 study_area (+ exclusions)  FROZEN          no change.
                                             P2.0c origin declaration (2026-08-08),
                                             recorded HERE because study_area.geojson's
                                             SHA-256 is pinned in manifest.json
                                             (contract_versions.study_area_content_hash)
                                             and must not be edited for a marker:
                                             study_area.geojson — data_origin: AUTHORED,
                                             author: unrecorded (it also self-marks with
                                             "placeholder": true). exclusions.geojson is
                                             NOT hash-pinned and carries its own in-file
                                             data_origin/author fields.
3 covariates.yaml            FROZEN          Option-A enabled; Option-B disabled.
                                             registry_version 2 -> 3 (E1.4 preflight,
                                             2026-07-28): windowed recipes (roughness,
                                             tpi, bpi; recipe_version 1 -> 2) now take
                                             PHYSICAL DISTANCES IN METRES, resolved to
                                             cells at runtime from the DEM's actual
                                             resolution. At cell counts, the same
                                             recipe_version measured a ~33 km
                                             neighborhood on the 0.1-deg synthetic DEM
                                             but ~1.4 km on 15-arc-sec GEBCO (24x),
                                             silently. Metre values preserve the
                                             GEBCO-equivalent meaning of the old cell
                                             counts. Slope/aspect/curvature stay
                                             native-resolution 3x3 operators: never mix
                                             features from different DEM resolutions in
                                             one training matrix.
                                             registry_version 3 -> 4 (P2.0c): METADATA-
                                             ONLY origin markers — shared note below.
4 scenarios.yaml             FROZEN          structure same; cutoffs → real ranges.
                                             config_version 2 -> 3 (P2.0c): METADATA-
                                             ONLY origin markers — shared note below.
5 source_queue.yaml          EXPANDED        source_metadata → the PHASE-A SOURCE
  (was source_metadata)                      QUEUE: one entry per Phase-A source with
                                             evidence classes, license, is_open,
                                             sampled area, derivation. version 3.
                                             metadata_version 3 -> 4 (P2.0c): METADATA-
                                             ONLY origin markers — shared note below.
6 ts6_reference.yaml         MINOR           benchmark surface; note [18]/[19] GRID.
                                             reference_version 1 -> 2 (P2.0c): METADATA-
                                             ONLY origin markers — shared note below.
7 normalization.yaml         NEW             per-evidence-class → kg/m² POLICY the
                                             AbundanceNormalizer obeys. version 1.
                                             policy_version 1 -> 2 (P2.0c): METADATA-
                                             ONLY origin markers — shared note below.
```

**Shared P2.0c note (2026-08-08) — one cause for all six bumps above.** Every
value-bearing contract now declares its origin under the five-value taxonomy
in [`engine/prospectivity/provenance/origin.py`](../../engine/prospectivity/provenance/origin.py)
(`data_origin:` per entry where entries differ, a file-level declaration for
the remainder; `author:` wherever AUTHORED, `citation:` wherever LITERATURE).
**No parameter value, bound, enum, or semantic changed in any contract** —
Isaac's checkpoint re-sync is a read, not a review. A file's effective origin
is computed by `combine_origins` over its declarations, never hand-written.
The bumps move `contract_versions` in `data/corpus/manifest.json`, which
moves its `content_hash` — accounted in `docs/walkthroughs/P2.0.md` §c.

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
| 6 | TS-6 reference | `data/ts6/ts6_reference.yaml` (**v3**) (+ `ts6_abundance.tif`) | read via `TS6Reference`; compute agreement; **E3.3 must carry the digitization error into the comparison** | digitize the TS-6 surface; set `role_note`; **the raster is DERIVED (TAX.1 approval), so `digitization_method` is its EVIDENCE and must be specific enough to re-run** |
| 7 | Normalization policy | `data/config/normalization.yaml` | one `AbundanceNormalizer` per evidence class | confirm geology: areas, mean nodule mass, join tolerance |
| 8 | Model parameters | `data/config/model_config.yaml` (**v2**) | read via `engine/prospectivity/model_config.py`; E2.0 records `target_definition` (value + declared origin) in training-matrix provenance; **C8.1: reads `acceptance_thresholds`, REFUSES an AUTHORED gate outright (and anything less real than LITERATURE), and E2.5's precondition 6 gates every validated claim on it** | decide the training target (buried vs surface — P2.B's verdict fixed the current enum); a value with a citation promotes the field AUTHORED → LITERATURE. **Fill `acceptance_thresholds` (with a citation): (a) what margin over the mean baseline counts as credible uplift, and on which metric; (b) whether a within-cluster-only win passes. Read the slot's own comment first — the E2.4 scores already exist, so any threshold set now is post-hoc for this dataset** |

**Contract 8 (P2.A, 2026-08-09).** The seven-contract framing in the Phase-0
docs now reads EIGHT: Contracts 1–7 defined what a MASS row is, how it
normalises, and what screens it, but never what `abundance_kg_m2` MEANS as a
training target — a Phase-0 omission that surfaced when E2.0 needed to record
which y it trains on. Contract 8 holds Phase-2 modelling parameters (as
distinct from Contract 7's ingestion policy) and grows additively as Phase-2
tasks need them; its `target_definition` enum is fixed by P2.B's data verdict
(see the contract's own header for the excluded dead ends and their evidence).

**Contract 6 version 3 (TAX.1 approval, 2026-08-21)** records the TS-6
raster's ORIGIN CLASS as **DERIVED** — the prerequisite E3.0 §6 said must be
answered before E3.3, not during it. The file is not TS-6's surface; it is a
raster computed by us from a published figure by a recorded procedure, so its
values are a function of that figure and that procedure. MEASURED is refused
(we did not measure it, and hashing it would hash our own output); LITERATURE
is refused (the numbers are our reading of a printed surface, with
digitization error we introduce). **ADDITIVE** — no existing field moved, so
Track G's re-sync is a read. The consequence that DERIVED has an audit
observer while LITERATURE does not is a RELIEF, not a reason: a class chosen
for the convenience of its check is the failure the taxonomy exists to
prevent. Reasoning lives in the contract's own comment.

**Version 2 (C8.1, 2026-08-20)** adds `acceptance_thresholds`, closing P2.A's
deferral on its own stated condition — the field "arrives with E2.5's
refuse-to-validate guard", and E2.5 built the consumer. **The change is
ADDITIVE**: no existing field's value or semantics moved, so Track G's
re-sync is a READ, not a review. The field ships `value: null` with **no**
`data_origin` (there is no value to classify) and the loader keeps three
states apart — absent raises, null is "awaiting", populated returns value +
origin — while rejecting an AUTHORED gate outright. That last rule is the
deliberate OPPOSITE of `target_definition`'s: an AUTHORED target is a
recorded, swappable stand-in, whereas an AUTHORED threshold silently becomes
the verdict.

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
CP0  swap declared-SYNTHETIC/AUTHORED inputs → MEASURED (Contracts 1,5,7)  ← EARLY
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
