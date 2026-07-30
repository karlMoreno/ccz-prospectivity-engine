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

Last consolidated: 2026-07-29 (through E1.4, dependency hygiene, the P3
contract-hygiene batch, and the provenance-manifest work). **27 open items**:
§1 Track G 10, §2 Karl 1, §3 Engineering 11, §4 Phase-2 risks 2, §6 later
phases 3. §5 is fully closed.

---

## 1. Blocked on Track G (Isaac)

- [ ] **Buried nodules: total vs surface abundance as the training target.**
  `[01]` reports buried count separately (mean ~12% of an event's count, max
  ~73%) and its published total mass INCLUDES buried nodules; surface
  collectors cannot recover them, so a model trained on total abundance and
  an economics layer assuming recoverable abundance disagree by up to ~3× at
  some stations. `[01]` gives no buried mass, so surface-only is not
  derivable by subtraction from `[01]` alone; `[05]`'s depth columns may
  allow it for some events. Owner: G (with Karl for the target definition).
  Trigger: **before Phase-2 target definition**; also feeds Contract 4.
  Detail: review discussion 2026-07-28; buried counts in
  `data/sources/SO268-bc-nodules-summary-PANGAEA-904967.tab`.
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
  inline).
- [ ] **Contract 4 real economics.** `scenarios.yaml` is entirely
  `illustrative_only: true` with `[GEOLOGY — ISAAC]` tags on cutoffs,
  composition, and price sources; the engine watermarks output until
  flipped. Owner: G. Trigger: Checkpoint 4. Detail:
  [scenarios.yaml:10](../data/economics/scenarios.yaml#L10)–78.

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
  `dedup_rules.py::is_satisfied_by`, merge-notes record "unranked, used
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
- [ ] **Intra-batch duplicate detection.** `DuplicateStationSpecification`
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
