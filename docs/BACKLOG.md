# BACKLOG — single source of truth for open items

This file consolidates every deliberately-deferred item that previously lived
scattered across walkthrough docs, contract `[GEOLOGY — ISAAC]` tags, code
docstrings, and review chat. Rules of the file:

- **Add an entry whenever work is deliberately deferred** — in the same
  commit that defers it.
- **Closing an item = checking it off** (`[x]`) **in the commit that closed
  it**, then (periodically) moving it to *Recently closed*.
- Sections group by **who is blocked / what unblocks it**, not severity —
  the file answers "what can I work on right now?" at a glance.
- Every entry cites where the detail lives (`file:line` or walkthrough §) so
  it is verifiable. Do not add entries that trace to nothing.

Last consolidated: 2026-07-30 (through **Phase-1 closeout Tasks A–D**); 2 items
added 2026-08-08 (origin-audit latents, P2.0a′), 3 more 2026-08-08 (P2.0c
evidence gaps + deferred README fix), 1 more 2026-08-09 (P2.0d-2 review:
LITERATURE admission path); README fix closed 2026-08-09 (P2.0d-3); 2 more
added 2026-08-09 from the planning transcript (contract change_class; GEBCO
TID); 1 more 2026-08-10 (P2.B follow-up: [05] depth parsing hazard).
**37 open items**: §1 Track G 11, §2 Karl 5, §3
Engineering 16, §4 Phase-2 risks 2, §6 later phases 3. §5 is fully closed.
Two of the three E1.5 reverse-audit findings are already closed (combinators
deleted, `TerrainSource` wired); `CorpusCsvSampleSource` remains, for Phase 2.

---

## 1. Blocked on Track G (Isaac)

- [ ] **Training target: awaiting Track G — contract slot exists, does NOT
  block Track E** (reframed 2026-08-09, P2.B + P2.A). Contract 8
  (`data/config/model_config.yaml`) now holds `target_definition`, provisional
  default `total_as_published` declared AUTHORED/`author: model` — the origin
  IS the provisional marker, and Isaac's value-with-citation arrives as the
  AUTHORED→LITERATURE promotion. P2.B **measured** what was estimated:
  `[01]`'s published mass includes buried nodules and the disagreement
  reaches **~11× by mass** at SO268/2_149-1 (surface 0.37 kg vs published
  4.1 kg; the old ~3× figure was a pre-P2.B estimate). Surface-only is NOT
  currently derivable: `[05]`'s per-nodule `Depth sed` column contradicts
  `[01]`'s published buried counts on **6 of 36 events, all SO268/2** (worst:
  2_182-1 records 0 buried vs 24 published; 2_116-1 0 vs 15), 15 events
  carry an unknown-depth nodule, and only 20/36 events derive cleanly. The
  concrete Track G question is therefore: **resolve the [05]-vs-[01] burial
  contradiction on those six events** — and the PATTERN is the lead
  (2026-08-10): all six sit on **SO268/2** while all 15 SO268/1 events
  reconcile exactly (6 of the 21 leg-2 events disagree); five of six
  UNDER-record burial in [05], and the two largest offenders (2_116-1,
  2_182-1) record `Depth sed 0.000` for **every** nodule while [01]
  publishes 15 and 24 buried — consistent with depth-not-recorded defaulting
  to zero on those events, not with random error. The exception, 2_95-2,
  OVER-records (6 vs 4) and is the one leg-2 event using the `">0.000"`
  notation. Working hypothesis: a per-leg (or per-team) recording-protocol
  difference — **the one question in this project a geologist can settle
  without new data**. If resolved, `surface_only` enters the enum as a new
  admissible value. Owner: G (with Karl for the definition). Trigger: any
  time; also feeds Contract 4. Detail:
  [P2.B-and-P2.A.md](walkthroughs/P2.B-and-P2.A.md);
  [model_config.yaml](../data/config/model_config.yaml) header; the parsing
  hazard for anyone re-running the analysis is §3 ("[05] Depth sed parsing
  hazard").
- [ ] **Study area / AOI scope.** 108 of 114 corpus rows fall outside
  `study_area.geojson`'s Phase-0 placeholder (E1.4 preflight confirmed 0/35
  training points on the placeholder AOI). Options: AOI = sampled areas
  only; AOI = full CCZ with distance-growing uncertainty; or defer.
  Recommendation: defer, then define the AOI around where the data actually
  sits. Owner: G + Karl. Trigger: before Phase-2 prediction surfaces.
  Detail: [data/aoi/study_area.geojson](../data/aoi/study_area.geojson);
  E1.4.md §1.
- [ ] **Real Dryad `[06]` data.** Removed from `REAL_ADAPTER_BUILDERS` in P1
  as fabricated; `_require_production_path()` blocks re-wiring until a real
  file exists under `data/`. Owner: G downloads, E re-wires. Trigger: real
  Dryad file delivered. Detail:
  [corpus_builder.py:168](../engine/prospectivity/ingestion/corpus_builder.py#L168);
  E1.3.md §13.
- [ ] **Real TS-6 `[18]` digitization (Contract 6).** Same P1b guard as
  `[06]`; `ts6_reference.yaml`'s method/figure/role_note/metrics fields are
  all `null` awaiting the digitization decisions. **The corpus is
  single-source until this or `[06]` lands.** One test re-activates itself
  when wired (`test_grid_rows_are_never_flagged_observed`). Owner: G.
  Trigger: Checkpoint 3. Detail:
  [corpus_builder.py:200](../engine/prospectivity/ingestion/corpus_builder.py#L200);
  [ts6_reference.yaml:51](../data/ts6/ts6_reference.yaml#L51)–82; E1.3.md §15.
- [ ] **Real GEBCO bathymetry (G1.1).** Synthetic DEM everywhere until
  Checkpoint 1; `src_bathymetry_primary`'s title/license are `null`. The
  metre-based windows (Contract 3 v3) only resolve unclamped on the real
  DEM. Owner: G. Trigger: Checkpoint 1. Detail:
  [data/bathymetry/README.md](../data/bathymetry/README.md);
  [source_queue.yaml:205](../data/sources/source_queue.yaml#L205), :227.
- [ ] **Geographic spread over row count.** The corpus is two clusters of
  ~12 km extent separated by ~991 km. When queueing further Phase-A sources,
  prioritise stations BETWEEN the clusters over more stations inside them —
  spread constrains the model more than n does. Owner: G. Trigger: next
  source-queue pass. Detail: review discussion 2026-07-28; cluster geometry
  visible in `outputs/e1.4/covariate_stack_synthetic_dem.png`.
- [ ] **normalization.yaml geology parameters.** `mean_nodule_mass_g_source`
  ([normalization.yaml:50](../data/config/normalization.yaml#L50)),
  `join_tolerance_km` (:86, blocks the GRADE join), and the
  `coordinate_tolerance_deg` tune flag (:101). Owner: G. Trigger: :50/:101
  any time; :86 before `[19]` wiring.
- [ ] **covariates.yaml geology questions — now in real distances.** The
  physically meaningful neighborhood scale(s) for nodule formation
  ([covariates.yaml:54](../docs/contracts/covariates.yaml#L54), metres/km
  since v3, not cells) and absolute depth vs relative relief (:71). Safe
  defaults stand. Owner: G. Trigger: any time before Phase-2 modeling
  hardens. 
- [ ] **source_queue.yaml download hygiene.** `license`, `accessed_date`,
  `content_hash`, `sampled_area_m2` are `null` across most entries — filled
  on download per the contract's own header. Only `is_open=true` sources may
  enter a published run, so licenses gate publication. Owner: G. Trigger:
  each download. Detail:
  [source_queue.yaml:42](../data/sources/source_queue.yaml#L42)–227 (tagged
  inline). **P2.0c addendum, NARROWED by P2.0d-2 (2026-08-09):** the
  consequence is now BUILT — `_require_proven_measured` refuses anything not
  declared-MEASURED-with-a-recorded-hash-matching-the-bytes, so the seven
  prospective declarations ([02][03][04][06][11][12][14]) are harmless: wiring
  any of them refuses with `content_hash: null` named until the hash is
  filled from the downloaded bytes ([01]/[05]'s were filled and verified in
  P2.0d-2 — the template). What remains open here is the original download
  hygiene: fill license/accessed_date/content_hash per download.
- [ ] **Contract 4 real economics.** `scenarios.yaml` is entirely
  `illustrative_only: true` with `[GEOLOGY — ISAAC]` tags on cutoffs,
  composition, and price sources; the engine watermarks output until
  flipped. Owner: G. Trigger: Checkpoint 4. Detail:
  [scenarios.yaml:10](../data/economics/scenarios.yaml#L10)–78.
- [ ] **LITERATURE citations that fail the locate-the-number bar** (P2.0c;
  the bar: document + table/section/page — "TS-6" alone is insufficient).
  Labels carried as LITERATURE with the gap recorded, not guessed closed and
  not downgraded: the four `ts6_finding` strings in
  [covariates.yaml](../docs/contracts/covariates.yaml) (candidate entries;
  each now says "table/page NOT LOCATED"); depth's `geology_note` 4,100–4,200 m
  claim (:71); the TS-6 anchors quoted in
  [scenarios.yaml](../data/economics/scenarios.yaml) comments (baseline
  grades, abundance distribution). Owner: G (locate in TS-6), with Karl.
  Trigger: any time; before a published run. Detail:
  [2026-08-08-origin-vocabulary-audit.md](audits/2026-08-08-origin-vocabulary-audit.md)
  §4; walkthrough P2.0.md §c.

## 2. Decisions needed (Karl)

- [x] **Authoring-copy schema — declared HISTORICAL** (Option B, your call
  2026-07-29). A `$HISTORICAL_ARTIFACT` header now states it is the Phase-0
  frozen artifact, that `docs/contracts/` is authoritative, and that
  `abundance_kg_m2.maximum` was later raised 45 → 100 in schema v4 with the
  rationale in the contracts README. **No field value changed** — preserving
  what was frozen was the point.
- [x] **`CLAUDE.md` "Current status" refreshed** (2026-07-29): Phase 1 Track E
  complete through E1.4, corpus state (108 / 35 / single-source), next task,
  and a pointer to this file for open items. The stale "do not jump ahead to
  Phase 1" warning now guards Phase 2 instead.
- [ ] **Precision/rounding rule for computed `abundance_kg_m2`.**
  Normalizers deliberately don't round (normalization.yaml specifies no
  precision), so full float precision lands in the corpus CSV. Decide
  whether the contract should state a precision. Owner: Karl (contract
  change if yes). Trigger: before a published corpus. Detail: E1.2.md:153.
- [ ] **Classify the two context sources under the origin taxonomy.**
  `src_bathymetry_primary` (GEBCO-class bathymetry: MEASURED survey product
  vs LITERATURE compiled grid — it interpolates between soundings) and
  `src_deepdata_public_context` (published regulatory polygons). Both carry
  `data_origin: null` in
  [source_queue.yaml](../data/sources/source_queue.yaml) with `[KARL]`
  comments; the bathymetry decision drives Checkpoint-1 watermark derivation
  (P2.0d derives the watermark from the DEM's declared origin). Owner: Karl
  (+ G). Trigger: at download / before Checkpoint 1. Detail: walkthrough
  P2.0.md §c.
- [ ] **Contract `change_class` — the version scheme cannot say
  "nothing changed".** `*_version` means both "the structure changed" and
  "re-sync at the next checkpoint": P2.0c bumped SEVEN contracts for zero
  semantic change, so Isaac now has seven version changes to re-sync that
  mean nothing — exactly the noise the freeze existed to prevent. Proposal:
  a required `change_class: metadata|semantic` on every bump, or a separate
  revision counter for non-semantic changes. Owner: Karl + E. Trigger:
  before the next metadata-shaped addition. (Recorded 2026-08-09 from the
  planning transcript — this is the item the P2.0 closeout flagged as
  existing nowhere in the repo; it now does.) Detail:
  [docs/contracts/README.md](../docs/contracts/README.md) shared P2.0c note;
  walkthrough P2.0.md §c.
- [ ] **GEBCO is not uniformly MEASURED — the classification may be
  per-cell, and the Phase-2 consequence matters more than the label.**
  GEBCO's global grid mixes shipborne soundings with depth PREDICTED from
  satellite altimetry, and much of the abyssal CCZ is the latter; GEBCO
  ships a companion TID (Type Identifier) grid labelling the source class
  per cell — which is why `src_bathymetry_primary`'s `data_origin` is still
  null (see the classify-the-context-sources item above) and why the honest
  answer may not be a single label. The consequence: roughness, TPI and BPI
  computed over altimetry-predicted cells measure the INTERPOLATION's
  smoothness, not the seafloor's — predicted bathymetry is smooth by
  construction at exactly the scales those recipes probe — so mixing
  predicted and sounded cells in one training matrix is a subtler version
  of the DEM-resolution rule Contract 3 v3 already forbids. Decision, not
  defect: record, assess TID coverage of the study area, decide the
  classification and whether E2.0's matrix needs a TID mask. Owner: Karl +
  Track G. Trigger: before Checkpoint 1. Detail: planning transcript
  2026-08-09; [covariates.yaml:37](../docs/contracts/covariates.yaml#L37)
  (the never-mix rule this echoes).
- [ ] **Uncited literature-shaped numbers in the contracts README.** The
  100 kg/m² ceiling rationale asserts "published CCZ abundances run
  ~1.5–30 kg/m²" and "~2 g/cm³ wet bulk density" with no citation —
  LITERATURE if cited, AUTHORED as written (origin-audit §4). Decide:
  supply citations (with G) or explicitly mark them authored engineering
  rationale. Owner: Karl (+ G for sources). Trigger: any time before a
  published run. Detail:
  [2026-08-08-origin-vocabulary-audit.md](audits/2026-08-08-origin-vocabulary-audit.md)
  §4; [docs/contracts/README.md:24](../docs/contracts/README.md#L24)–37.

## 3. Engineering (Track E)

- [ ] **Pipeline-level row quarantine.** One malformed row aborts the whole
  batch at Pydantic validation — worse than dropping, and it contradicts
  flag-never-drop. It also makes D6 partly unreachable: negative
  `sampled_area_m2` crashes at `Field(ge=0)` before `qa_status="fail"` can
  be written. Survivable with two clean PANGAEA files; will bite when the
  DOMES sources land (older digitised data is where malformed rows live).
  Owner: E. Trigger: **before wiring `[02][03][04]`**. Detail: E1.3.md §13
  (fix 3 caveat).
- [ ] **Deterministic tie-break to replace first-encountered.** P2's written
  proposal: contract-driven `preference_rank` in `source_queue.yaml`
  (implements rule 2's "prefer clearest methods" literally), lexicographic
  `source_id` as documented fallback, third branch in
  `dedup_rules.py::resolve`, merge-notes record "unranked, used
  fallback". Needed before DOMES families / NOAA-PANGAEA mirrors land — they
  collide by design with no quality-grade asymmetry. Owner: E (+ G ranks).
  Trigger: **before wiring `[02][03][04]` or mirrors**. Detail: E1.3.md §14.
- [ ] **Enforce the DEM-resolution rule in code.** Contract 3 v3 states
  features from different DEM resolutions must never be mixed in one
  training matrix (slope/aspect/curvatures are native-resolution operators —
  no version bump can make them comparable). Nothing enforces it; a check at
  training-matrix assembly comparing each layer's recorded
  `dem.resolution_deg` would. Owner: E. Trigger: **Phase-2 training-matrix
  task**. Detail:
  [covariates.yaml:37](../docs/contracts/covariates.yaml#L37)–45 (v3
  comment); provenance already carries the resolution.
- [ ] **Smoothed synthetic DEM.** Current fixture is uncorrelated noise:
  derivative covariates are noise-of-noise and a stencil-axis bug has places
  to hide; a Gaussian-smoothed field makes plots interpretable. Known-value
  plane tests cover correctness — this is diagnostic value only. Owner: E.
  Trigger: any time; cheap. Detail:
  [rasters.py:65](../tests/fixtures/rasters.py#L65).
- [ ] **Verify D3's GRID `source_id` scoping when `[19]` lands.** A TS-6
  cell and a Washburn cell at the same coordinates must BOTH survive
  (independent compiled products, rule 4). The unit test exists with
  hand-built rows; verify against the real pair. Owner: E. Trigger: `[19]`
  wired. Detail: E1.3.md §10.
- [ ] **Washburn dual-class fan-out untested.** `[19]` carries GRID + GRADE
  in one row; `build_records` supports multiple `EvidenceClassMapping`s but
  no test exercises a two-class source. Owner: E. Trigger: `[19]` wired
  (same batch as the item above). Detail: phase-0-and-E1.1.md:729.
- [x] **Specification combinators deleted** (2026-07-29). Zero production
  composition sites, and the shipped Specification is stateful so composition
  would have made evaluation order load-bearing. ABC kept. Writing the
  idempotency test this motivated **found a real bug**: the merge re-appended
  provenance links on a repeat call, and a `build_corpus()` re-run made a row
  record itself as its own duplicate — invisible to the length-only idempotency
  test. Both fixed and guarded. Detail: [PATTERNS.md](PATTERNS.md) §3.1.
- [x] **`TerrainSource` wired, not deleted** (2026-07-29). Added
  `DemGrid.from_terrain_layer()` / `from_terrain_source()` — the seam was never
  absent (the engine already called `terrain_source.load()`), `features/` just
  had no way to consume a `TerrainLayer`. The bridge verifies the layer's
  reported hash against the bytes read, and both
  `content_hash="sha256:synthetic-fixture"` placeholders (terrain AND ts6) are
  replaced by real computed hashes. Synthetic → real GEBCO is now a substitution
  at the seam. Detail: [PATTERNS.md](PATTERNS.md) §3.2.
- [ ] **`CorpusCsvSampleSource` never implemented.** `SampleSource` has zero
  production subclasses; the MASS-only rule reaches production only via
  `Observation.is_training_eligible()`, and the corpus is read directly. Phase
  2's training matrix is the natural consumer. Owner: E. Trigger: Phase-2
  training-matrix task. Detail: [PATTERNS.md](PATTERNS.md) §3.2;
  phase-0-and-E1.1.md:703.
- [ ] **[05] Depth sed parsing + interpretation hazard — silent, and it
  FABRICATES findings, which is worse than hiding them.** Two layers:

  **Layer 1, parsing.** The column mixes floats with the STRING values
  `">0.000"`/`">0.100"` (23 nodules: SO268/1_27-1 ×7, SO268/1_28-1 ×11,
  SO268/2_95-2 ×5), so a naive `to_numeric(errors="coerce")` silently drops
  23 BURIED nodules into NaN — inflating surface mass AND, since 18 of the
  23 sit on leg 1, inventing false [05]-vs-[01] disagreements on two events
  that actually reconcile. P2.B's first pass produced exactly that phantom
  at 1_27-1 — a fabricated data-quality finding is the kind of thing that
  would have gone in front of Isaac. Also `Sample ID` has nulls: row counts
  must use group size.

  **Layer 2, interpretation — `0.000` carries two incompatible meanings, so
  the states are FOUR, and the two that collide are the ones that matter:**

  ```
    Depth sed value    what it might mean       detectable from [05]?
    ─────────────────────────────────────────────────────────────────
    0.000              genuinely at surface     no ─┐ indistinguishable
    0.000              depth never recorded     no ─┘ from within [05]
    ">0.000"           buried, depth bounded    yes
    (blank)            unknown                  yes
  ```

  The only separator is the EXTERNAL cross-check — a cross-source
  validation rule, not a parsing rule: **if [01] publishes buried nodules
  for an event where [05] records `0.000` throughout (2_116-1: 15 published;
  2_182-1: 24 published), the zeros are unrecorded, not surface.** Without
  this rule an adapter can parse all the states correctly and still read 24
  buried nodules as sitting on the surface. Under the taxonomy: a `0.000`
  meaning "not recorded," read as "surface," is an AUTHORED assumption
  wearing MEASURED's label — exactly what the guard family exists to
  refuse, arriving through the data rather than through a declaration.

  **No live exposure (grep-verified 2026-08-10):** nothing committed parses
  these columns — `Depth sed` appears in engine/ and tests/ only as literal
  header text inside two verbatim fixture excerpts; the [05] adapter maps
  event/mass/dimensions/Elevation only, and the corpus takes
  `mean_nodule_mass_g` + provenance from [05], nothing else. A trap for
  future work, not a defect in anything committed.

  Owner: E. Trigger: **before any code parses [05]'s depth columns** (an
  adapter extension, or re-running the §1 contradiction analysis). Detail:
  [P2.B-and-P2.A.md](walkthroughs/P2.B-and-P2.A.md) §P2.B (method + traps);
  raw value counts in `data/sources/SO268-bc-nodules-PANGAEA-904962.tab`.
- [ ] **Datetime format mismatch silently blocks dedup.** `sample_datetime_utc`
  is compared for exact equality, so a timezone-AWARE value (`"…T00:00:00Z"`)
  never matches the naive one the current adapters produce (`2019-03-06 00:00`)
  even though they denote the same instant — the pair reads as a disagreement
  and the merge refuses to fire. Found 2026-07-30 while writing the fail-row
  collision test.
  **THE FAILURE MODE IS SILENT — this is why it should be fixed rather than
  deferred again.** Nothing raises. The two rows simply don't match, so both
  are admitted, and the corpus gains **duplicate stations that look like
  independent samples**: the row count rises, `training_eligible_count` rises,
  and the same physical station is weighted twice in any model fitted on it.
  A missed dedup is indistinguishable from correct behaviour by inspection —
  only a targeted test, or noticing an implausible station count, would reveal
  it. Contrast a format error that raises, which is self-reporting.
  Not a production defect today (no wired source emits a Z-suffixed timestamp,
  and `test_reconciliation.py`'s key-format guard pins `[01]`/`[05]`
  agreement), but the DOMES/NOAA families span eras and formats and will hit
  it. Normalise to a single tz convention at adapt time, or compare instants
  rather than objects. Owner: E. Trigger: **before wiring `[02][03][04]` or
  the NOAA mirrors**. Detail:
  [dedup_rules.py](../engine/prospectivity/ingestion/dedup_rules.py)
  `_same_station`; `test_corpus_builder.py` collision test's own comment.
- [ ] **Intra-batch duplicate detection.** `DuplicateResolutionPolicy`
  only checks candidates against the existing corpus — two duplicate rows in
  the SAME adapter fetch don't catch each other. None of the wired sources
  have that shape; DOMES might. Owner: E. Trigger: before wiring
  `[02][03][04]`. Detail: E1.3.md §8.
- [ ] **`source_id` foreign-key enforcement.** The schema declares
  `source_id` → `source_queue.yaml` but nothing checks it; a typo'd
  `source_id` on a real adapter passes silently. Owner: E. Trigger: before
  the next real adapter lands. Detail: phase-0-and-E1.1.md:760.
- [ ] **Lockfile is macOS-arm64 only.** `requirements.lock` records the
  local resolved set; CI re-resolves independently (freeze output is
  platform-tagged). Acceptable for the alpha with pinned ranges — but the
  divergence is why CI stayed green on a netcdf4 that cannot install on
  arm64. Revisit hash-pinning (uv/pip-tools) before a published run. Owner:
  E. Trigger: pre-publication. Detail:
  [requirements.lock:1](../requirements.lock#L1)–5;
  phase-0-and-E1.1.md:755.
- [x] **Corpus provenance manifest (JSON)** — built 2026-07-29 after three
  deferrals. `data/corpus/manifest.json`, populated by a `ProvenanceRecorder`
  (OBSERVER) on `IngestionPipeline`, with the three-artifact boundary and the
  chaining rule defined in
  [docs/contracts/PROVENANCE.md](contracts/PROVENANCE.md). Records absorbed
  sources (`[05]` now visible), `training_eligible_count` (35) separate from
  admitted (108), AOI containment (108/108 outside), and the pairwise-distance
  structure (2 clusters, 974 km support gap).
- [ ] **Dependency versions into the provenance manifest.** The manifest
  claims to pin everything about a run; the dependency lock hash should sit
  alongside contract versions. Owner: E. Trigger: Phase-3 manifest emitter.
  Detail: review discussion 2026-07-29; `engine.py` `RunManifest`.
- [ ] **Corpus CSV bytes are not hash-pinned by any manifest field.** The
  corpus manifest records `corpus_path`, row counts, and its own
  substance-hash, but nothing hashes `master_observations.csv`'s bytes — so
  PROVENANCE.md's chaining rule currently traces a prediction to a
  DESCRIPTION of the corpus rather than to the corpus bytes, and a hand-edit
  to the CSV breaks no recorded hash (only a rebuild's full-state idempotency
  comparison would surface the drift). Own task with its own reasoning,
  deliberately NOT part of P2.0 — it changes the manifest shape for a
  different reason than origin does. Owner: E. Trigger: own task; before a
  published run (natural fit: the Phase-3 manifest work above). Detail:
  [2026-08-08-origin-vocabulary-audit.md](audits/2026-08-08-origin-vocabulary-audit.md)
  §6; [docs/contracts/PROVENANCE.md](contracts/PROVENANCE.md).
- [ ] **Admission path for proven LITERATURE sources ([18]/[19]).** The
  P2.0d-2 guard admits only proven MEASURED, so `[18]` (correctly declared
  LITERATURE — a compiled product) can never re-wire into the CORPUS through
  `corpus_builder`, no matter what Track G delivers; same for `[19]`. It
  fails loudly, and it contradicts the older re-wiring language (now
  annotated in corpus_builder's docstrings). Decide: the benchmark enters
  via the Contract 6 `TS6Reference` seam rather than as corpus rows (the
  likely answer — Contract 6 already routes `ts6_abundance.tif` there), or
  the guard gains an origin-appropriate evidence path for hash-proven
  LITERATURE. Owner: E + Karl. Trigger: Checkpoint 3 ([18] wiring). Detail:
  P2.0.md §d-2; found by the d-2 adversarial review.
- [x] **samples README false blanket claim — FIXED in P2.0d-3** (pulled
  forward from the doc-consistency pass). The README now lists all four
  files, describes `so268_nodules_sample.csv` accurately (verbatim excerpt,
  CC-BY-NC-4.0, PANGAEA.904962, attribution), and names the
  `data_origin.yaml` sidecar as the authoritative side for origins. Detail:
  [2026-08-08-origin-vocabulary-audit.md](audits/2026-08-08-origin-vocabulary-audit.md)
  §5.
- [ ] **CI hygiene (minor).** `MPLBACKEND: Agg` not set (currently harmless
  — `plot_stack.py` sets Agg itself); install step uses bare `pip` rather
  than `python -m pip`, inconsistent with the README's canonical form.
  Owner: E. Trigger: next CI edit. Detail:
  [ci.yml:24](../.github/workflows/ci.yml#L24).

## 4. Phase 2 method risks (record now, decide at Phase-2 kickoff)

- [ ] **Variogram support gap.** Every observation pair is either <13 km or
  ~991 km apart — nothing in between. Ordinary kriging's variogram cannot be
  empirically estimated across the range it must predict over; any curve
  through the gap is extrapolation, not estimation. Affects whether kriging
  is defensible as the TS-6-parity method; raises the mean baseline's
  importance. Owner: E + G. Trigger: Phase-2 kickoff (E2.2). Detail: review
  discussion 2026-07-28; cluster geometry per the E1.4 plot.
- [ ] **Spatial CV fold structure.** With two real clusters, honest spatial
  CV reduces to leave-one-cluster-out with n=2 folds. Decide how to REPORT
  that limitation rather than papering over it with random blocks inside
  clusters. Owner: E + Karl. Trigger: Phase-2 kickoff (E2.x spatial CV).
  Detail: review discussion 2026-07-28.

## 5. Contract hygiene (the P3 batch — COMPLETE 2026-07-29)

- [x] **`[05]` row-count claim.** Corrected to "1,658 rows / 36 events" with
  the correction's source (the downloaded PANGAEA.904962 file) recorded
  inline — P3, 2026-07-29. Detail:
  [source_queue.yaml:92](../data/sources/source_queue.yaml#L92).
- [x] **Physical rationale for the 100 kg/m² ceiling.** Added to the
  contract-1 row: ~1.7× the ~60 kg/m² close-packed monolayer limit, and why
  the bound catches unit/transcription errors without rejecting a real
  extreme — P3, 2026-07-29. Detail:
  [docs/contracts/README.md](../docs/contracts/README.md) contract-1 row.
- [x] **D5.4 test + Fragment fixture.** Fourth event `SO268/2_116-1`
  excerpted verbatim (Samples 31/47 "Fragment" with mass, plus plain Sample
  2); two tests now name D5.4 — the Fragment case and the
  Broken-with-mass case — P3, 2026-07-29. Detail:
  [test_nodule_aggregate_adapter.py](../tests/test_nodule_aggregate_adapter.py).
- [x] **`[09]`/`[10]` in rule text but not registered.** Rule 1's prose now
  states inline that they are not registered Phase-A sources, with a note
  that the rule is a generic key-match needing no specific IDs — P3,
  2026-07-29. Detail:
  [normalization.yaml:96](../data/config/normalization.yaml#L96).
- [x] **`CLAUDE.md` contract-path mismatch** (was §2). Both references now
  name the real layout: `docs/contracts/` + `data/` canonical, `Proposals and
  contract V3/Contracts_v3/` authoring. The adjacent alpha-proposal path was
  wrong in the same way and was corrected too — P3, 2026-07-29.

## 6. Scheduled for later phases (not blocked — just not yet)

- [ ] **Option-B covariates** (`sediment_type`, `surface_chlorophyll`,
  `ccd_minus_depth`, `bathymetric_regime`) — the TS-6-proven proxies, Phase
  6. Registry + tests actively keep them out until then. Detail:
  [covariates.yaml:123](../docs/contracts/covariates.yaml#L123)–158.
- [ ] **Postgres/PostGIS** — parked until Phase 5; `database/` holds
  `.gitkeep`s only. Detail: phase-0-and-E1.1.md:723.
- [ ] **Phase B (PDF extraction) and Phase C (targeted requests) source
  tiers** — out of the alpha entirely. Detail: alpha proposal §scope;
  CLAUDE.md scope discipline.

## 7. Closed decisions, recorded for reference (not open items)

- **Window anisotropy (≤~3%) — accepted, not corrected.** Metre windows
  resolve from the N-S cell size; the E-W physical span deviates ≤~3% at
  study latitudes. Recorded in every layer's provenance (`crs_strategy`).
  Detail: E1.4.md §6;
  [recipe.py:52](../engine/prospectivity/features/recipe.py#L52).
- **5th reconciliation residual — documented, not fixed.** `SO268/2_205-2`:
  `[01]` did not add its 16 sub-5g nodules to its published count, though 11
  other events did include theirs, so D5.1's "counts include sub-5g nodules"
  is usually-but-not-always true. A source inconsistency found while writing
  the reconciliation test and verified against both raw files — kept visible
  rather than absorbed by loosening a tolerance. Moved here from §5 (P3,
  2026-07-29): it is a finding, not pending work. Detail: E1.3.md §12 D;
  [test_reconciliation.py](../tests/test_reconciliation.py).
- **GRADE pass-through by design.** `GradeNormalizer` passes GRADE rows
  through unjoined: the station join is corpus-assembly logic, not
  per-record normalization (E1.2 decision). When the join is built (with
  `[19]`, once `join_tolerance_km` is resolved — §1), it arrives as a new
  pipeline stage, not a normalizer change. Detail: E1.2.md §6;
  [test_corpus_builder.py:106](../tests/test_corpus_builder.py#L106).

---

## Recently closed

- [x] **Specification retired for an honest policy object** (Task D / Option
  C2, 2026-07-30). `DuplicateStationSpecification` →
  `DuplicateResolutionPolicy` with a **pure** `resolve(candidate) ->
  Resolution` (`Admit` / `AlreadyPresent` / `AbsorbInto` / `Replace`);
  `IngestionPipeline._dedup` applies the decision. The `Specification` ABC is
  deleted — zero implementations, combinators already gone. Idempotency became
  structural (the `AlreadyPresent` variant; no write branch for it), and the
  manifest's ~20 lines of attribution inference — where the attribution bug
  lived — are gone, because the recorder now observes each decision including
  which source a `Replace` displaced. Corpus CSV byte-identical; manifest
  substantively unchanged. Detail: [PATTERNS.md](PATTERNS.md) §3.0.
- [x] **Test-name audit, fully closed** (Tasks A + B, 2026-07-30). All 17
  findings addressed: 7 assertions strengthened (each mutation-verified), 9
  tests renamed to match their bodies, 1 misplaced test moved out of
  `test_plot_stack.py`. The 18th, `test_contracts_parse.py:24`, was
  deliberately skipped — already covered by `test_covariate_registry.py`.
  Task A also surfaced a live defect (fail-verdict erasure under dedup) and a
  latent one (naive-vs-aware datetime blocking dedup, now §3). The durable fix
  is the new **Testing conventions** section in
  [CLAUDE.md](../CLAUDE.md) — three rules, each citing the finding that
  motivated it.
- [x] **E1.5** test traceability audit: three real gaps found and filled —
  corpus rules were asserted through the model that enforces them, three-way
  evidence-class agreement was missing the schema leg, and reachability was
  untested. 8 new tests, 5 mutations run. Pattern audit in
  [PATTERNS.md](PATTERNS.md); table in
  [walkthroughs/E1.5.md](walkthroughs/E1.5.md).
- [x] Provenance architecture: three chained artifacts on a shared Layer
  Supertype base, `docs/contracts/PROVENANCE.md` defining the boundary, and
  the corpus manifest built on it. The reversed-order test caught a real
  attribution defect (admitted counted from appends, not from the finished
  corpus) — fixed before landing.
- [x] P3 contract hygiene: `[05]` row count, the 100 kg/m² physical rationale,
  D5.4 Fragment fixture + tests, the `[09]`/`[10]` note, and `CLAUDE.md`'s
  contract paths — `618488e`.
- [x] Plot-coverage gap: `plot_stack` smoke tests added (was zero coverage,
  CI green without exercising the deliverable) — `1080e03`.
- [x] pangaeapy moved to the `[fetch]` extra; netcdf4/cftime orphans
  removed; `requirements.lock` + `requires-python <3.12` — `9b3a276`.
- [x] Contract 3 v2→v3: metre-based windows (the 24× neighborhood defect),
  runtime resolution with clamp provenance, scale-invariance test
  mutation-verified — `b3ae97c`.
- [x] CRS strategy A (per-row longitude scaling) implemented in `DemGrid`;
  physical-unit known-value tests — `b3ae97c`.
- [x] Synthetic DEM extent regenerated over the real corpus bbox (was 0/35
  training points on-raster; now 35/35) — `b3ae97c`.
- [x] `[06]` Dryad and `[18]` TS-6 unwired as fabricated data;
  `_require_production_path()` structural guard (P1, P1b) — `f0b3b1a`.
- [x] `qa_status` now gates training eligibility (flagged failed box core
  `SO268/1_12-2` excluded; 35 of 36 MASS rows train) — P1, `f0b3b1a`.
- [x] D8-F: `[01]` made authoritative for MASS + COUNT explicitly;
  survivorship order-dependence removed and guard-tested by full-build
  reversal (P2) — `f0b3b1a`.
- [x] D5: real `[05]` PANGAEA.904962 wired (1,658 nodules / 36 events);
  D5.1 settled — `mean_nodule_mass_g` divides by weighed count, validated
  against the published 11.5–26.6 kg/m² band — `354622e`.
- [x] D1/D4: dedup merge gap-fills instead of discarding; provenance links
  recorded in both survivor directions — `354622e`.
