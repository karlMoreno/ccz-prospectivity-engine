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
TID); 1 more 2026-08-10 (P2.B follow-up: [05] depth parsing hazard);
1 closed + 1 added 2026-08-13 (E2.0-1: `CorpusCsvSampleSource` closed,
estimator known-answer fixtures added); 1 closed + 3 added 2026-08-14
(E2.0-2: DEM-resolution rule enforced; added audit coverage boundary,
sole-observer hygiene pass, and the review-found DemGrid rotated/south-up
transform gap); 1 added 2026-08-14 (E2.0-3: Checkpoint-1 re-report of
occupancy/ceiling/border + the kriging exemption); 1 added 2026-08-14
(E2.1 review: E2.4 runner obligations); 1 closed 2026-08-14 (E2.1-3:
known-answer fixtures built); 1 added 2026-08-14 (E2.2 §2 review INCIDENT:
review-against-committed-state procedure); E2.4 runner-obligations entry
extended to seven at E2.3 (RF report fields; the uncertainty-semantics
column), then to eight at the E2.3 closeout (obligation 3 marked LIVE;
the two-fold geometry theorem); 1 added at the E2.3 closeout (§2: the
pre-registration clock).
2 closed at the E2.X disposition audit (2026-08-14: the two §4 Phase-2
risks, both addressed by E2.2/E2.3 and re-dispositioned); 2 triggers
refreshed (coverage boundary, sole-observer hygiene — "after E2.0" had
expired); the review-workflow entry gained its second layer.
1 added 2026-08-18 (E2.4 §1: the P2.C doc-consistency batch, landing a
transcript-only deferral); §4's fold-structure item re-closed on its
ORIGINAL box (the audit had added a checked twin — deleted).
1 closed 2026-08-19 (E2.4 §2: the runner-obligations entry — box checked on
the ORIGINAL entry, no twin).
**41 open items** (recounted from the boxes): §1 Track G 11, §2 Karl 7, §3
Engineering 20, §4 Phase-2 risks 0 (both closed), §6 later phases 3. §5 is
fully closed.
All three E1.5 reverse-audit findings are now closed (combinators deleted,
`TerrainSource` wired, `CorpusCsvSampleSource` implemented in E2.0-1).

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
- [ ] **THE PRE-REGISTRATION CLOCK — record before the E2.4 scores exist
  (E2.3 closeout, 2026-08-14).** E2.4 produces the comparison scores. The
  moment they exist in a walkthrough, every acceptance threshold set
  afterward is POST-HOC FOR THIS DATASET, PERMANENTLY — and Contract 8's
  loader (`model_config.py`) refuses an AUTHORED value outside its
  admissible set, and `acceptance_thresholds` has no slot yet (it "arrives
  with E2.5" per the contract header), so Track E cannot pre-register one
  even if it wanted to. That design is correct; the SEQUENCING must
  therefore be honest rather than fixed:
  - **E2.4 runs anyway.** Its scores are measurements under the SYNTHETIC
    watermark, and E2.5's refuse-to-validate is the RECORDED VERDICT, not
    a gap — "no pre-registered gate existed when these scores were
    computed" is itself the honest output.
  - **E2.4's run manifest must DATE SCORE VISIBILITY:** a
    `scores_first_visible` timestamp (or equivalent) in the RunManifest,
    so that if Track G ever supplies thresholds, the Contract 8 field can
    carry `set_after_scores: true` TRUTHFULLY rather than by
    reconstruction. (This is one deliberate exception to the artifacts'
    "no wall-clock in the substance hash" rule — the DATE is the fact
    being recorded; keep it OUT of `content_hash` like `generated_at`, but
    IN the artifact.) **Being outside the hash, the timestamp is MUTABLE
    METADATA — honest by convention, not by mechanism; nothing detects a
    hand-edited timestamp. The AUTHORITATIVE date is the COMMIT that
    introduced the scores, and the field's own description must say so
    (E2.4-PRE, 2026-08-14).**
  - **The nuance, stated so it survives:** for RF the synthetic-era scores
    are noise-scores (X is synthetic noise on 4 distinct rows) and a later
    threshold is only weakly contaminated by them. But KRIGING fits real
    coordinates against real y — its scores are REAL measurements today
    (E2.2: real local structure at 0–13 km) — so for kriging specifically
    the post-hoc contamination is REAL, not synthetic-era-only. A
    threshold set after seeing kriging's scores is post-hoc in the full
    sense, and the manifest dating is what makes that CHECKABLE rather
    than arguable.
  - **THE E2.5 TRIPWIRE (Karl, E2.X approval, 2026-08-14):** E2.5 is
    expected to be predominantly ASSEMBLY of refusals that already exist —
    Contract 8's loader refusing AUTHORED thresholds, E2.4's
    `scores_first_visible`, the pre-registration verdict ("no
    pre-registered gate existed when these scores were computed"). If E2.5
    turns out to require substantial NEW machinery, **STOP and investigate
    what leaked upstream before building it: the SIZE of E2.5 is itself a
    diagnostic.** (Placed here rather than in the runner-obligations entry
    because the components E2.5 assembles are the ones this entry names.)
  Owner: Karl + E. Trigger: E2.4's manifest design, and again whenever
  Track G engages on thresholds; the tripwire fires at E2.5's design.
  Detail:
  [model_config.yaml](../data/config/model_config.yaml) header (the
  `acceptance_thresholds` slot); [P2.B-and-P2.A.md](walkthroughs/P2.B-and-P2.A.md)
  ("arrives with E2.5"); E2.3 closeout in [E2.3.md](walkthroughs/E2.3.md).
- [ ] **P2.C — doc-consistency fixes (the deferral LANDED, E2.4 §1,
  2026-08-18).** This batch was deferred in the Phase-2 planning
  transcript with no landing spot — the exact shape the deferral rule
  (CLAUDE.md workflow conventions) forbids; the E2.4 handoff named it
  ("P2.C doc fixes … P2.D datetime dedup") and only P2.D had an entry
  (§3, datetime). Each item below was RE-VERIFIED against the repo at E2.4
  §1 by independent read-only checks with citations re-opened by a second
  pass — the states are current facts, not transcript memory. One item was
  pulled forward into E2.4 §1 itself: `CLAUDE.md`'s "Do not jump ahead to
  Phase 2" line (an ACTIVE countermand, not stale decoration) plus the
  minimal status refresh (1E-b). The full refresh stays here.
  - **README status — and PUSH FIRST.** `README.md:16–25` still says
    "Phase 1, Track E complete through E1.4" (corpus 108/35 counts are
    still correct) and `:18` still says "dedup Specifications" — retired
    for `DuplicateResolutionPolicy` at `c07ab80` (2026-07-30); truth:
    Phase 2 through E2.3. `main` is **47 commits
    ahead of `origin/main`** (remote at `b3ae97c`, E1.4) — so the GitHub
    README is staler still. Verify the push state, push, THEN rewrite.
  - **BACKLOG AOI denominator.** `docs/BACKLOG.md` §1 "Study area / AOI
    scope" reads "108 of 114 corpus rows fall outside" — the 114 counted
    the 6 fabricated in-box `[06]`/`[18]` rows removed in P1/P1b, and was
    already wrong the day this file was created; the manifest's
    `study_area_containment` is 108/108, `fraction_outside` 1.0 (and
    §3's E1.5 item + `provenance.md:84` already say 108 of 108). Fix: "all
    108 of 108 (100%)".
  - **`covariates.yaml` title vs version.** `docs/contracts/covariates.yaml:1`
    still reads "CONTRACT 3 (v2)" while `registry_version: 4` (line 57;
    README row, `contract_versions.py`, `features/stack.py` and three tests
    all agree on 4 — the header prose narrates both bumps, only the title
    was never touched at 2→3 or 3→4). Docs-only: title → "(v4)". The
    Contracts_v3 authoring copy is a genuine v2 and stays.
  - **Handoff Task A–D closeout paragraph.** No handoff names the
    2026-07-30 Phase-1 closeout Tasks A–D (`23f22f7` A, `16a6c3d` B,
    `5f95129` C, Task D / Option C2); `HANDOFF_claude_code_phase2.md`
    carries their RESULTS anonymously (202 tests, `DuplicateResolutionPolicy`,
    Specification retired, fail-terminal-on-merge, testing conventions,
    datetime item) while pointing a fresh session at E1.5.md as "most
    recent state". Add the paragraph, or point at BACKLOG "Recently
    closed" (which names them).
  - **"Blocked on" framing → contract-slot framing.** The last live
    instance was `CLAUDE.md` "Current status" ("needs a decision on the
    training target first") — FIXED at E2.4 §1 (1E-b). BACKLOG §1's item
    already carries the contract-slot framing; the section title "Blocked
    on Track G" remains as a grouping label (still true for the other ten
    items). Sweep `docs/` once more at fix time for any survivor outside
    the historical `prompts/` and `handoffs/` records.
  - **`docs/` prose contradicting the origin taxonomy.** Ten hits in three
    groups: (a) `PATTERNS.md:329` and `walkthroughs/E1.5.md:232` say a
    layer's synthetic-ness "is recorded in the layer's name" — since
    P2.0d-3 it is the DECLARED `TerrainLayer.data_origin` (the fixture's
    layer is literally named "bathymetry"; `tests/fixtures/rasters.py:116–118`);
    (b) BACKLOG §1's `[06]`/`[18]` entries (~lines 89–98) describe the gate
    as `_require_production_path()` / "a real file under `data/`" and `[18]`
    as re-wirable — the gate is `_require_proven_measured` (declared
    MEASURED + hash over real bytes) and `[18]` is declared LITERATURE, so it
    cannot enter through `corpus_builder` at all (§3's admission-path item
    already says so); (c) scattered "real"/"synthetic" used as if origin
    followed from a filename — including `docs/contracts/README.md:163`
    ("swap SYNTHETIC sources → REAL Phase-A downloads"), where the
    checkpoint plan's shorthand predates the vocabulary. Fix by pointing
    each at the declaration.
  - **CI comment.** `.github/workflows/ci.yml:3–6` (unchanged since Phase 0,
    `4160546`) says CI runs "the full pipeline end-to-end on synthetic
    fixtures … over the synthetic sources in `data/fixtures/native/`"; what
    runs is `pytest -v` over all 376 tests, which execute the REAL
    production ingestion path (`build_corpus()` over the two hash-verified
    PANGAEA `.tab` files in `data/sources/`), read the committed real
    108-row corpus, and assemble the real 35-station training matrix over a
    synthetic DEM. Rewrite the comment to say what runs; the CLAUDE.md
    reproducibility line it quotes ("CI runs the full pipeline end-to-end
    on synthetic fixtures every push") needs the same correction.
  - **BACKLOG obligation 6 names a field that cannot exist.** The verbatim
    obligation text lists `sd_ddof` among RF's sd-defining hyperparameters;
    E2.3-4 replaced the ddof moment with the (q84−q16)/2 half-width, so the
    real field is `hyperparameters.sd_mapping`. The verbatim text stays; the
    supersession is recorded on the entry's closure line (E2.4 §2, F18) —
    fold it into the next re-statement of the obligations rather than
    editing a quoted block.
  - **`SESSION_STATE.md` fate — [KARL — DECIDE: update / supersede with a
    pointer / delete].** It is a Phase-0 + E1.1 checkpoint (names `4160546`,
    "44 passed", next task E1.2), 52 commits and eight walkthroughs behind;
    its only inbound references are the 2026-08-08 origin audit (:70, :165 —
    the latter already flags it stale). Nothing else reads it.
  Owner: Karl + E. Trigger: before Phase-2 closeout or before the repo is
  shown to anyone, whichever comes first. Detail: this entry's citations;
  [E2.4.md](walkthroughs/E2.4.md) §0 finding C.
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

- [ ] **Review workflows must run against a COMMITTED state or a copy —
  never against the sole uncommitted copy of the work under review**
  (INCIDENT, E2.2 §2 review, 2026-08-14). A reviewer is a READER; one
  that writes to the work it then approves is grading its own
  restoration. What happened (per the workflow's own logs): reviewer
  `review:math` ran `git checkout -- engine/prospectivity/estimators/
  variogram.py` to undo its own mutation probe, forgetting the file's
  baseline was UNCOMMITTED — this reverted the file to the committed
  report-only version and destroyed the uncommitted fitter (~178 lines);
  it then rewrote the file from its session-start read. What
  verification COULD establish: the restoration Write is byte-identical
  (sha256 `ed6c9ee7…`) to a `cp` backup an independent reviewer
  (`review:fixtures`) took at review start BEFORE any mutation; the suite
  and the real-corpus fit reproduce to 16 digits. What it could NOT: no
  committed object existed to diff against — "matches" means matches two
  reviewers' independent copies, not git. Residual risk: small (two
  independent byte-identical copies), not zero. The fix is PROCEDURAL,
  not code: commit or stash before an adversarial review launches, or
  point reviewers at a worktree. P2.0c and E2.0-2 sequenced this
  correctly (work staged/committed before review); this session inverted
  the order — the E2.1 and E2.2 reviews both ran on sole uncommitted
  copies. **TWO LAYERS, both recorded now so whoever does this later knows
  the second exists (E2.X disposition audit, ledger row 15):**
  **(a)** commit or stash before an adversarial review launches, or point
  reviewers at a worktree — E2.3-2 did this (WIP commit `efc683a` before
  the review; the reviewers left the tree clean and said so).
  **(b)** a reviewer that probes by MUTATION takes a `cp` copy before its
  first write and restores by `cp`, verifying with `cmp` — NEVER by
  `git checkout`, which is not undo against a file git does not hold. This
  is not hypothetical: in the E2.2 review the `review:math` agent ran
  `git checkout -- variogram.py` to undo its own mutation and its log
  records the realization ONE COMMAND LATE ("git checkout would revert to
  committed version, losing the uncommitted fitter!"), while the
  `review:fixtures` agent independently did it right — `cp` backup at
  review start, every restore `cmp`-verified — and that backup is what
  made the restoration byte-verifiable. Both layers go into every future
  review prompt's instructions verbatim (E2.3-2's prompt carried (a); (b)
  is added from here). Owner: Karl + E. Trigger: **before the next
  adversarial review runs.** Detail: [E2.2.md](walkthroughs/E2.2.md) §2
  "Review incident".

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
- [x] **DEM-resolution rule enforced in code** (2026-08-14, E2.0-2).
  `require_single_dem()` in
  [extraction.py](../engine/prospectivity/features/extraction.py) refuses,
  naming layers and field, on any `dem.resolution_deg` OR
  `dem.content_hash` disagreement across layers — and verifies the sampling
  grid against the layers' DEM, since a mismatched geotransform mislocates
  every station silently. Built against the real threat: one stack copies
  one `DemGrid.provenance()` into all 8 layers and cannot disagree with
  itself, so the guard (and its mutation) target layers assembled from
  DIFFERENT stacks — the Checkpoint-1 synthetic→GEBCO transition shape.
  Detail: [E2.0.md](walkthroughs/E2.0.md) §E2.0-2.
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
- [x] **`CorpusCsvSampleSource` implemented** (2026-08-13, E2.0-1).
  [`samples/corpus_csv.py`](../engine/prospectivity/samples/corpus_csv.py):
  CSV → NaN-to-None → `Observation` per row, gate inherited from the ABC and
  not reimplemented. 108 loaded / 35 eligible, matching `manifest.json`.
  Three mutations run; the is_open one showed the new constructed closed-row
  test is that gate's SOLE observer (every real corpus row is is_open=true).
  Detail: [walkthroughs/E2.0.md](walkthroughs/E2.0.md) §E2.0-1;
  [PATTERNS.md](PATTERNS.md) §3.2 resolution note.
- [x] **Known-answer fixtures for the estimators — BUILT 2026-08-14
  (E2.1-3).** [tests/fixtures/known_answer.py](../tests/fixtures/known_answer.py):
  SYNTHETIC-declared (generator import path + explicit per-call seeds;
  audit acceptance probed both directions — declaration stripped, the
  origin audit failed naming the file), with `gaussian_process_field`
  (stated exponential model, parameterized range/sill/nugget/seed),
  `covariate_driven_field` (one named driving column), `grid_layout` (the
  well-supported point set), and `empirical_semivariance` (the measuring
  stick, deliberately not a fitter). The prohibition survives in the
  module docstring: the synthetic DEM is NEVER made to correlate with real
  abundance. E2.1 proved with it exactly: baseline recovery, determinism,
  and coarse variogram consistency incl. the pure-nugget case; the
  E2.2/E2.3/E2.4 recoveries are listed in the docstring as deferred
  consumers. Detail: [E2.1.md](walkthroughs/E2.1.md) §3. Original entry
  follows for the record:
  (recorded at E2.0-1; built
  at E2.1 where the `Estimator` interface first exists). The problem: the
  corpus carries real abundance while every covariate is computed on a
  synthetic DEM, so a Phase-2 model trained today learns real y against
  noise. The expected and honest result is that no model beats the mean
  baseline — but that result is indistinguishable from a broken estimator.
  The real corpus can tell us the pipeline runs; it cannot tell us the
  arithmetic is right. The fix: a separate known-answer test fixture in
  `tests/fixtures/`, declared SYNTHETIC with generator import path and
  seed(s) per the origin taxonomy — a TEST FIXTURE, never a corpus and never
  an input to a claim (the same move E1.4 makes one layer down: covariate
  tests assert a plane dropping 100 m over 10 km gives slope 0.5729°, not
  "output is not null"). **EXPLICITLY NOT THIS: do not make the synthetic
  DEM correlate with the real abundance values.** That would produce a
  corpus where y genuinely depends on X and make every subsequent model
  result uninterpretable — did the model work, or did it find a relationship
  we planted? Under the taxonomy that corpus is AUTHORED wearing real data's
  shape. The known answers to plant, one per estimator task:
  - mean baseline — hand-computed mean and SD (already in E2.1's spec);
  - kriging — exactness at data locations; recovery of a planted variogram
    range and sill on a WELL-SUPPORTED layout (a grid, not our two
    clusters); and a pure-nugget case that should fit a near-zero range and
    revert to the mean;
  - random forest — one covariate genuinely drives y, seven are noise;
    importance must rank the real one first. Run at n=35 AND at n=500: if
    the planted signal is only recoverable at n=500, that is a quantitative
    statement about what our actual dataset can support — stronger than
    E2.3's qualitative caveat;
  - spatial CV — a field with a KNOWN correlation range, then confirm random
    k-fold reports better scores than leave-one-cluster-out on the same
    data, turning "random k-fold leaks on autocorrelated data" from a
    methodological claim into a measured number in our own suite.

  Owner: E. Trigger: E2.1, as the shared fixture E2.2–E2.4 each add their
  own known-answer case against.
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
- [ ] **demo.py's swallowed TypeError — a demo that can silently show the
  wrong image** (E2.X disposition audit, ledger row 5; noted at the E2.0-2
  review and never recorded). `demo.py` (untracked, repo root; deliberately
  left so — it hand-types values outside the audit's walk) step 6 calls
  `plot_covariate_stack()` with NO arguments; the signature requires
  `dem_path`, `output_dir`, `dem_data_origin`, so it raises `TypeError`,
  which the step's bare `except` swallows before globbing `outputs/**/*.png`
  and opening whatever it finds — a STALE figure from an earlier run, with
  no indication that regeneration failed. The wrapper built for it
  (`regenerate_default_stack_plot`) was deleted at E2.0-2 §0 because
  demo.py never called it. Hazard: a presentation shows an image the
  demo did not produce and cannot vouch for — the unlabeled-scientific-
  looking-output class. Fix before the next presentation: call
  `plot_covariate_stack(dem_path, output_dir, dem_data_origin=…)` with
  real arguments and let a failure be visible, or delete step 6. Owner:
  Karl (the file is his, untracked). Trigger: **before demo.py is next
  presented.** Detail: `demo.py` step 6 (`step_plot`); E2.0.md §E2.0-2
  housekeeping.
- [ ] **CI hygiene (minor).** `MPLBACKEND: Agg` not set (currently harmless
  — `plot_stack.py` sets Agg itself); install step uses bare `pip` rather
  than `python -m pip`, inconsistent with the README's canonical form.
  Owner: E. Trigger: next CI edit. Detail:
  [ci.yml:24](../.github/workflows/ci.yml#L24).
- [ ] **The origin audit's coverage boundary is narrower than the authoring
  rule it enforces** (recorded at E2.0-2). CLAUDE.md's authoring rule says
  "any new file containing values" declares its origin, but
  `test_data_origin_audit.py` walks only `data/` and `tests/fixtures/` — so
  a value-bearing file anywhere else is structurally invisible to the
  audit. Demonstrated case: `demo.py` (untracked, repo root) hand-types
  abundance values (12.0/−118.0, 19.4, 500 kg/m², …) with no declaration
  and nothing can fail on it. CLAUDE.md asserts something the mechanism
  does not deliver: either the rule narrows to match the walk, or the walk
  widens to match the rule. Recommendation: WIDEN — `git ls-files` already
  enumerates everything; the change is the walk's root plus per-entry
  exclusions. Correction to the E2.0-2 prompt's expectation, verified
  2026-08-14: `SYNTHETIC_MEAN_NODULE_MASS_G` lives in
  [tests/fixtures/normalizers.py:19](../tests/fixtures/normalizers.py#L19),
  INSIDE the walk and already declared AUTHORED — the genuinely uncovered
  ground is `engine/` modules and repo-root scripts, where a widened walk
  should expect legitimately-AUTHORED engineering constants to surface and
  need declarations or exclusions. Owner: E. Trigger: **before Phase-2
  closeout (Checkpoint 2)** — refreshed at the E2.X disposition audit
  (ledger row 21); the original "after E2.0" had silently expired. Detail:
  [test_data_origin_audit.py](../tests/test_data_origin_audit.py) (walk
  roots); CLAUDE.md "Data origin" (the authoring rule).
- [x] **E2.4 runner obligations** (recorded at E2.1, from its adversarial
  review — three conditions the CV runner must satisfy, none enforceable
  before it exists). (1) `assert_complete()` makes the baseline REGISTERED,
  not run: the runner must iterate `EstimatorRegistry.names()` — never
  cherry-pick via `get()` — so a complete registry implies a run baseline;
  the registry header states exactly this division. (2) The registry hands
  out ONE shared stateful instance per name (unlike the stateless
  normalizer/covariate registries it mirrors): the runner must refit per
  fold or build fresh instances per fold (`build_default_registry()` per
  run is the cheap discipline) — an E2.2 kriging fit that caches partial
  state would otherwise leak across folds silently. (3) **LIVE, not
  hypothetical (E2.3 closeout, 2026-08-14).** Written when sd=0 meant "the
  baseline on constant y" — a constructed edge. QRF's zero-width
  predictions make it a real MECHANISM on real data: any training row
  whose pooled leaf population is single-valued has q16 == q84 and sd ==
  0, and the pairing template passes it (non-negative). Evidence: the
  real-matrix count is **0 of 35 today** (every cell has ≥ 7 distinct y),
  pinned in `test_random_forest.py`, so a corpus change that produces a
  single-valued cell is a visible finding, not a silent 0 — but the
  mechanism exists now, and any E2.4 metric that divides by uncertainty
  WILL hit sd=0 the moment it does. Therefore the first dividing metric's
  sd=0 handling must be decided AT DESIGN TIME in E2.4, not discovered
  when the division throws — or worse, does not throw: a metric that
  silently drops sd=0 points is excluding exactly the points where the
  model is most wrong about itself. Constant-y baseline (uniform barren)
  remains the second, legitimate source. (4) Added
  at E2.2: kriging's reportable state
  (`OrdinaryKrigingEstimator.report()` — fitted + alternative models, the
  bin table the fit SAW, every excluded bin with its reason, the
  unsupported 13–986 km lag range) must reach the RUN PROVENANCE — E2.2
  only exposes it; a prediction whose consumer cannot see the model was
  extrapolating between the clusters is exactly the
  unlabeled-scientific-looking-output defect the watermark family exists
  to prevent. (5) `range_at_candidate_ceiling` MUST be carried NEXT TO the
  fitted `range_km` in the run manifest (Karl, E2.2 §2 pre-commit): the
  real-data fit put the range at the candidate ceiling — the 10–13 km bin
  (γ 23.4, above the total variance 15.1) is still rising at the edge of
  support — so the honest answer is not "the range is R" but "the range
  exceeds what 13 km of support can resolve"; a manifest reader must see
  "unconstrained from above" beside the number, not in a walkthrough they
  may never open. Same for its floor twin
  `range_below_first_supported_lag` and `residual_dof`. (6) Added at
  E2.3: RF's `report().validation_facing_fields()` — seed, n_estimators
  and every sd-defining hyperparameter READ BACK from the fitted forest
  (`max_samples_leaf`, `aggregate_leaves_first`, `weighted_leaves`, the
  quantile grid, `sd_ddof`), the uncertainty method + its stated
  semantics, `distinct_x_rows`, and importance PER SEED — joins kriging's
  reportable state; the runner consumes `report()` and NEVER reaches
  around it to `_forest` (which can still be asked for OOB). The
  honest-named `oob_diagnostic_not_validation` may be carried ONLY under
  that name and never in a validation-facing field — E2.5's guard
  re-asserts this at claim time. (7) THE UNCERTAINTY-SEMANTICS COLUMN
  (Karl, E2.3 decision 5): the comparison table MUST carry an
  uncertainty-semantics column, because the three estimators now report
  three different KINDS of number — a sample moment (baseline SD, ddof=1),
  a model moment (√kriging variance, exceeding the sill far-field by the
  Lagrange term), and a quantile half-width (QRF `(q84−q16)/2`,
  `uncertainty_method = "qrf_half_width_q16_q84"`). A table that prints
  three "sd" columns without saying so invites a reader to compare them as
  one quantity. Each estimator's `report()` names its semantics; the runner
  prints them beside the numbers. Also carry RF's
  `zero_width_training_predictions` (0 of 35 today) — a zero paired
  uncertainty on real data is a red flag to show, never to floor.
  **(8) THE TWO-FOLD GEOMETRY THEOREM — E2.4 design input, on record
  BEFORE the runner is written so the report cannot mistake geometry for
  a finding (E2.3 closeout, 2026-08-14).** Leave-one-cluster-out with
  exactly two clusters is TWO folds:

  ```
    fold A: train E-cluster (21) → predict W-cluster (14), ~991 km away
    fold B: train W-cluster (14) → predict E-cluster (21)
  ```

  With the fitted range ≤ 13 km (E2.2: 21.6 km AT the candidate ceiling,
  unconstrained from above — but nowhere near 991), kriging at 991 km
  reverts to the training cluster's local mean with variance ≈ sill +
  Lagrange term (E2.2 measured this on real data: mid-gap prediction
  19.29 vs mean 19.53, variance 25.3 > sill 21.4). Therefore ACROSS
  clusters, **kriging ≈ baseline BY CONSTRUCTION** — the across-cluster
  comparison measures exactly one thing, cluster A's mean versus cluster
  B's values, and CANNOT distinguish the estimators. Consequences the
  E2.4 prompt must carry: (a) "kriging ≈ baseline across clusters" is a
  geometry theorem, not a model finding, and the report must frame it as
  such; (b) the WITHIN-cluster gate — spatial blocking inside a cluster —
  is the only place kriging can beat the baseline on this data, which
  makes the E2.1 registry docstring's registered-vs-executed separation
  and any two-gate design load-bearing rather than decorative; (c) the
  across-cluster fold is still worth running and reporting, because "the
  two clusters differ by X" is itself a measurement — it is just not a
  model comparison. Cross-reference: §4 "Spatial CV fold structure"
  (the n=2-folds limitation, recorded 2026-07-28) — this item is WHY the
  n=2 across-cluster fold cannot rank estimators, not only that it is
  small. Owner: E.
  Trigger: E2.4. Detail:
  [registry.py](../engine/prospectivity/estimators/registry.py) header;
  [mean_baseline.py](../engine/prospectivity/estimators/mean_baseline.py)
  docstring; [kriging.py](../engine/prospectivity/estimators/kriging.py)
  `KrigingReport`; E2.1/E2.2 review records in
  [E2.1.md](walkthroughs/E2.1.md) / [E2.2.md](walkthroughs/E2.2.md).
  **CLOSED — IMPLEMENTED at E2.4 §2 (2026-08-19); the box is checked on THIS
  entry and no twin was added beside it (the lesson §1 took from §4).** All
  eight are properties of `engine/prospectivity/validation/runner.py`'s
  `CrossValidationRunner`, each with a named test and a mutation that fails
  it — the where-each-lands table is in [E2.4.md](walkthroughs/E2.4.md) §2.
  In brief: (1) the runner's only way into the registry is `items()` (no
  `get()` anywhere in the module) after `assert_complete()`; (2) the shared
  instance is refit per fold and a refusal — at `fit` OR at `predict` — is
  RECORDED with its phase while the prediction call sits out of reach; (3)
  the sd=0 policy was decided at §1D and its counts reach both the structured
  record and the flat table; (4)(5) kriging's full `report()` reaches run
  provenance per fold, with the ceiling flag beside `range_km` and — because
  the artifact writer sorts keys — also as one `range_km_reported` sentence;
  (6) RF contributes exactly `validation_facing_fields()`, and no OOB-derived
  value appears anywhere in the manifest even with the diagnostic computed;
  (7) `uncertainty_method` + `uncertainty_semantics` are enforced CLASS
  declarations carried beside every sd-shaped number, including the
  baseline's own numbers nested in another estimator's pooled record; (8)
  the theorem frames the report, and the LIVE LOCO case (kriging refuses
  train-W, is baseline-exact on train-E) is pinned. **Supersession inside
  obligation 6's VERBATIM text:** it names `sd_ddof`, which E2.3-4 replaced
  with the (q84−q16)/2 half-width — the field that satisfies it is
  `hyperparameters.sd_mapping = "half_width_(q84-q16)/2"`. The quoted text
  stays as quoted; the correction rides here and in the P2.C batch (§2
  review finding F18).
- [ ] **Checkpoint 1: re-report the cell occupancy, the R² ceiling, and the
  border situation on real GEBCO** (recorded at E2.0-3). Three
  literal-pinned facts and one reading rule are true of the 0.1° synthetic
  fixture and will all change when ~460 m cells arrive: (1) the occupancy —
  35 stations in 4 cells, groups 14+7+7+7, `shared_cell_count` 35
  (`test_covariate_extraction.py` pins); (2) the covariate-model R² ceiling
  0.348 recomputed from `cell_groups` + y
  (`test_training_matrix.py` pins); (3) border count 0 (pinned; the
  carry-the-NaN and matrix-refusal paths are sole-observed by constructed
  fixtures until a real station sits near an edge). And re-read the
  kriging-exemption paragraph ([E2.0.md](walkthroughs/E2.0.md) closeout):
  the ceiling binds covariate-driven models only — kriging predicts from
  coordinates and never sees it — an asymmetry that DISAPPEARS as the cells
  shrink and X re-separates, so E2.4's model comparison reads differently
  before and after. Expect all these pins to fail on the GEBCO stack; each
  failure is the re-report trigger, not a defect. Owner: E. Trigger:
  Checkpoint 1 (real GEBCO wired). Detail: E2.0.md §E2.0-2/§E2.0-3 +
  closeout.
- [ ] **`DemGrid.load` accepts rotated and south-up geotransforms it cannot
  handle** (found by the E2.0-2 adversarial review's probes; pre-existing
  in committed code, deliberately not fixed inside E2.0-2's scope). A
  rotated EPSG:4326 transform (shear terms non-zero) loads without
  complaint, `res_x/res_y` look normal, and every downstream geolocation is
  silently wrong (probe: extraction and rasterio disagreed (5,5) vs (5,4));
  a south-up transform (`e > 0`) loads with a negative `dy_m` and dies
  later in the windowed recipes with a message naming the wrong thing
  ("window_m and cell_size_m must be positive"). A one-line
  axis-aligned/north-up assertion in `DemGrid.load` closes both with an
  honest message. No current exposure: GEBCO and the synthetic fixture are
  axis-aligned north-up. Owner: E. Trigger: before Checkpoint 1 (the next
  new DEM entering the system). Detail:
  [dem_grid.py](../engine/prospectivity/features/dem_grid.py)
  `load()`; E2.0-2 review record in
  [E2.0.md](walkthroughs/E2.0.md) §E2.0-2.
- [ ] **Sole-observer hygiene pass** (recorded at E2.0-2; convention
  established in E2.0-1b: a SOLE OBSERVER warning in the test's own
  docstring, with its mutation evidence — the person tempted to weaken a
  test is reading the test, not a module header). Candidates already
  documented as single-observer in prior mutation tables but carrying no
  in-file warning: the SYNTHETIC and DERIVED evidence-check negation
  fixtures (P2.0d-2 §0.1, each "FAILED alone"); d-3's render-level
  bytes-differ test ("the ONLY test that catches" a plot bypassing the
  watermark helper); and P2.0c review mutations #9 (layer-origin copy) and
  #10 (hardcoded composition), where the record names one catching test
  without stating whether others also failed — those two need their
  mutations re-run to establish the fact before any docstring claims it.
  E2.0-2's two new sole observers (border-NaN, shared-cell hardcode)
  already carry the warning in-file and are NOT part of this pass. E2.2's
  three (border-NaN, shared-cell hardcode, shape-mismatch) and E2.3's
  (RF10's injected-crossing observer) likewise carry theirs. Owner: E.
  Trigger: **before Phase-2 closeout (Checkpoint 2)** — refreshed at the
  E2.X disposition audit (ledger row 7); the original "after E2.0" had
  silently expired. Detail:
  [E2.0.md](walkthroughs/E2.0.md) §E2.0-1b "Other known single-observer
  cases"; P2.0.md mutation tables.

## 4. Phase 2 method risks (record now, decide at Phase-2 kickoff)

- [x] **Variogram support gap — CONFRONTED at E2.2, re-dispositioned at the
  E2.X audit (ledger row 21).** Every observation pair is either <13 km or
  ~991 km apart — nothing in between. E2.2 §1 REPORTED it (595 pairs, ZERO
  in 13–986 km), Karl's decisions 1–3 encoded it (min 30 pairs per bin; the
  fit sees 0–13 km ONLY; exponential + spherical, nugget fitted), and the
  fitter RECORDS it: the unsupported 13–986 km range, every excluded bin
  with its reason, and `range_at_candidate_ceiling` beside the fitted
  range. What remains is not this item but its consequence — the two-fold
  geometry theorem (§3 runner obligation 8): across the clusters kriging ≈
  baseline BY CONSTRUCTION. Original text: "any curve through the gap is
  extrapolation, not estimation" — now a recorded property of every fit,
  not a risk. Detail: [E2.2.md](walkthroughs/E2.2.md) §1–§2.
- [x] **Spatial CV fold structure.** With two real clusters, honest spatial
  CV reduces to leave-one-cluster-out with n=2 folds. Decide how to REPORT
  that limitation rather than papering over it with random blocks inside
  clusters. Owner: E + Karl. Trigger: Phase-2 kickoff (E2.x spatial CV).
  Detail: review discussion 2026-07-28.
  **CLOSED — ANSWERED at the E2.3 closeout, re-dispositioned at the E2.X
  audit (ledger row 21), box checked at E2.4 §1 (2026-08-18; the audit
  had closed it by adding a checked twin beside this open original — the
  twin is deleted, this is the one entry).** The answer is stronger than
  a reporting choice: the two-fold geometry theorem (§3 runner obligation
  8) says the across-cluster fold structurally CANNOT rank the estimators,
  so it is reported as a measurement ("the two clusters differ by X") and
  the within-cluster gate is the only model comparison. E2.4-PRE carried
  this into the tracked prompt (`562d9a7`); E2.4 §1 measured the
  within-cluster consequence (kriging cannot refit on strictly-within-
  cluster folds — [E2.4.md](walkthroughs/E2.4.md) §1B). Detail:
  obligation 8; [phase2_prompts.md](prompts/phase2_prompts.md) E2.4.

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
