# TRACK G — THE ACQUISITION PLAN (G.0)

Written 2026-08-23 (G.0, one commit: this file + `docs/BACKLOG.md`). This is
a PLAN, NOT AN ACQUISITION: nothing here downloads a file, digitizes a
figure, fills a contract slot, or lands under `data/`. The BACKLOG is the
spine — its §1 and §2 entries are consolidated here BY POINTER, closed by
NOTHING in this commit; each closes later on its own original box, in the
commit that closes it, per the file's own rules.

CONTEXT THAT CHANGED: Track E is complete to CP5a (pending deploy — Karl's).
Isaac delivers nothing. **Karl is doing Track G himself.** So every geology
item is re-labelled by what it actually demands:

- **[mechanical]** — a download, a recorded procedure, a hash. An evening.
- **[labor]** — digitizing, corpus assembly, per-row screening. Hours to days.
- **[judgment]** — a threshold, a comparability call, a target definition.
  The expensive kind: cheap to type, costly to get wrong, and the
  [GEOLOGY — ISAAC] tags in the contracts now all read as this.

Reading order: §0 (what was verified and what the prompt got wrong), §2 (the
slot inventory), §3 (the five dataset targets), §4 (sequencing — the
pre-registration clock outranks everything), §6 (what CP5b actually
requires). §1 records the ownership change; §5 the non-goals.

---

## §0 — Premises verified (and the corrections found)

The G.0 prompt instructed verification of every premise before planning,
citing its own poor base rate. Correct instruction: **six premises needed
correction or sharpening.** Everything below was checked against the repo
this session; file:line citations are current at this commit.

**Verified as stated:**

| Premise | Evidence |
|---|---|
| The source index exists and is titled "Path C" | `Proposals and contract V3/CCZ_Path_C_Primary_Source_Hunt_Index.md` — **TRACKED** (`git ls-files` confirms), so the prompt's commit-it-first branch does NOT fire |
| Scope reconciles: alpha = Path C **Phase A only** | The index's `RECOMMENDED INGESTION ORDER` lists Phase A as exactly 11 IDs — [01]–[06], [11], [12], [14], [18]–[19] — which is `source_queue.yaml`'s roster to the entry (its header: "CONTRACT 5 (v3) — Path C PHASE A source queue"). Phase B ([25]–[46], PDF extraction) and Phase C (targeted requests) are out of the alpha (BACKLOG §6:2241; alpha proposal §scope). **No dataset target below cites an out-of-scope tier.** GEBCO is not in the hunt index at all — it enters via Contract 5 directly (`src_bathymetry_primary`) |
| `source_queue.yaml` is the acquisition ledger | `license`/`accessed_date`/`content_hash`/`sampled_area_m2` filled on download per its own header; `src_bathymetry_primary` is null across `data_origin`/`title`/`url`/`is_open`/`license`/`content_hash` (lines 240–256). The plan uses this mechanism per source; no parallel ledger is invented |
| The [06]/[18] guards and the paired re-wiring | `_require_proven_measured` (`corpus_builder.py:116`) refuses anything not declared-MEASURED-with-matching-hash under `data/sources/`; both builders exist but are excluded from `REAL_ADAPTER_BUILDERS` (:294–307). `test_grid_rows_are_never_flagged_observed` re-activates by a runtime data-driven `pytest.skip` (`test_observation_schema.py:58`) the moment GRID rows exist. The corpus is single-source until [06] or [18] lands |
| The E5.5 probe's three refusals | BACKLOG §3:2074 — (a) UNCLASSIFIED ×10, (b) INVALID ×18 (`AUTHORED with author None` — the `author_inherited_from` gap), (c) the quoted-declaration false positive on `run_manifest.json` |
| `author_inherited_from` trigger | BACKLOG §3:1707 — "before the first economics raster committed under `data/`"; three options (a)/(b)/(c), Karl's call, "not (c) silently" |

**Corrections — the prompt's premises against the repo:**

1. **The slot homes.** `join_tolerance_km`, `mean_nodule_mass_g_source`, and
   `coordinate_tolerance_deg` are **Contract 7** (`normalization.yaml`)
   slots, not Contract 1's. Contract 1 (the schema) carries
   `abundance_basis` (enum wet|dry|unknown, `required: false` — the wet/dry
   gap's schema half). The inventory in §2 uses the correct homes.
2. **BACKLOG line references have drifted** (three verified instances):
   the normalization entry cites `:50`/`:86`/`:101` — the slots are at
   **:67/:103/:123**; and the [18] entry's `corpus_builder.py#L200` anchor
   now lands in [05]'s docstring — the [18] builder spans **:256–291**.
   Corrected in the BACKLOG in this commit, scoped to these verified claims.
3. **The pre-registration mechanism is four layers, and its date check is
   PER-RUN.** Verified in code: (a) the loader refuses an absent
   `acceptance_thresholds` field, (b) a value with no `data_origin`, (c)
   AUTHORED — or anything less real than LITERATURE — outright
   (`model_config.py:161–207`); (d) the claim guard's precondition 6
   (`an_acceptance_threshold_existed_before_the_scores`, `claim.py:312`)
   refuses `set_after_scores: true` by name and compares
   `declared_at > inputs.manifest.scores_first_visible` — **this run's**
   manifest. Consequence stated precisely because §4 rests on it: a
   threshold declared after a first real-data run would NOT be caught by
   the date check on a *later* re-run (whose `scores_first_visible` is
   newer than the declaration). The permanence is carried by the truthful
   `set_after_scores: true` declaration — which the guard refuses by name —
   and by the commit-as-witness convention the code itself states
   ("honest by convention, not by mechanism"). **The machinery cannot
   rescue a late gate; it can only refuse a dishonest one. Only sequencing
   keeps the declaration honestly false.**
4. **Populating `exclusions.geojson` needs more than a test update.** E4.1
   asserts the set is empty
   (`test_economics_contract.py:160`, `test_contracts_parse.py:72`,
   `test_economic_cutoff.py:124`) — that part is as the prompt says. But
   `CutoffEconomicModel` **refuses a non-empty exclusion set by name**
   ("rasterising exclusion polygons … is not built",
   `test_economic_cutoff.py:151`). The first APEI polygon therefore fires
   TWO Track-E tasks: the test updates AND the rasterisation path. §3.1
   schedules both.
5. **What the audit can and cannot see — probed both directions before
   being promised** (scratch tree against the real resolver, this session):
   a `.geojson` with in-file `data_origin` classifies; stripped →
   UNCLASSIFIED by name. A `.tif` needs the sidecar (`data_origin.yaml`,
   `files:` form); no sidecar → UNCLASSIFIED. DERIVED without a derivation
   → INVALID by name; LITERATURE without a citation → INVALID by name (the
   check fires today; the §3 gap is that no test observes the check
   itself). **And a MEASURED declaration passes the audit with no hash at
   all** — the resolver has no MEASURED-evidence branch; that proof lives
   in `_require_proven_measured` (corpus paths) and in the recorded hashes
   of `source_queue.yaml` / `services/api/context.py`. For datasets 1 and
   2 the hash discipline is the LEDGER's, not the audit's — stated here so
   nobody reads a clean audit as hash-verified.
6. **A new finding, not in the prompt:** the source index is tracked
   TWICE, byte-identically — `CCZ_Path_C_Primary_Source_Hunt_Index.md` and
   `Contracts_v3/CCZ_DATA_SOURCES.md` — with no pointer between them. Edit
   one and the other silently goes stale, and the second sits in the
   authoring-copies folder where a reader could take either as canonical.
   Recorded here; the dedup (a pointer header in one, or deleting one) is
   Karl's, cheap, any time.

---

## §1 — Ownership

BACKLOG §1's header read "Blocked on Track G (Isaac)". False since this
commit: **Isaac delivers nothing; Karl is Track G.** The section is
re-titled and its twelve entries re-owned to Karl-as-G in this commit, with
a changelog line.

The `[GEOLOGY — ISAAC]` tags inside the contracts are NOT touched:
contracts live under `data/`, outside this commit's fence, and a tag edit
is a version bump. From this commit those tags read as **"geology judgment,
Karl's"**; the textual cleanup rides the next legitimate version bump of
each contract (never a bump of its own). The tags' task-routing half keeps
working unchanged — they mark judgment sites, and the judge changed.

---

## §2 — The slot inventory

Every null / placeholder / judgment slot across the contracts, from the
files as they are, with the dataset task that fills it. The cross-check the
prompt asked for: **every slot maps to a task below, and every task fills
at least one slot** — with two slots that DO NOT EXIST yet and must be
ADDED (marked ⊕; each is a contract version bump, Karl's, scheduled with
its dataset).

| Contract | Slot | State today | Filled by |
|---|---|---|---|
| 2 (`study_area.geojson`) | the AOI geometry | placeholder 2° box, `placeholder: true` | §3.1 (decision) + CP1 (consequence) |
| 2 (`exclusions.geojson`) | exclusion features | `features: []`, empty on purpose, asserted empty by E4.1 | §3.1 |
| 5 (`source_queue.yaml`) | `src_bathymetry_primary` row (all null) + `src_deepdata_public_context` (`data_origin: null`) | prospective | §3.2 / §3.1 |
| 5 | per-source `license`/`accessed_date`/`content_hash`/`sampled_area_m2` | null across most entries | each download, §3.1–§3.4 |
| 7 (`normalization.yaml:67`) | `mean_nodule_mass_g_source` | null | §3.3 |
| 7 (`:103`) | `join_tolerance_km` | null — gates the [19] GRADE join | §3.3 |
| 7 (`:123`) | `coordinate_tolerance_deg` | 0.001 default, tune flag | §3.3 |
| 1 (schema:180) | `abundance_basis` | exists, optional, EMPTY on all 108 rows | §3.3 (⊕ make required — "unknown" admissible, empty not; Contract 1 bump, Karl) |
| 4 (`scenarios.yaml`) | both scenarios' cutoffs, prices, weights; `illustrative_only` | all placeholder, prices 0 | §3.5 |
| 4 | ⊕ recovery fraction, uncertainty treatment, price source, `cutoff_basis`, difference semantics (E4.0's five) | absent | §3.5 (contract bump, Karl) |
| 6 v4 (`ts6_reference.yaml`) | `source_figure`, `digitization_method`, `digitization_uncertainty`, `role_note`, `content_hash`, `comparison.acceptable_spatial_correlation` | all null; `raster_data_origin: DERIVED` decided (do not reopen) | §3.4 (the correlation gate: §4 step 0) |
| 8 (`model_config.yaml`) | `target_definition` | AUTHORED/`author: model`, `total_as_published` — the origin IS the provisional marker | §3.3 (the burial contradiction) |
| 8 | `acceptance_thresholds` | `value: null` — a declared absence | §4 step 0, before anything else |

Slots no dataset fills: none. Dataset lines mapping to no slot: none — the
spread-over-count rule (§3.3) is a queueing criterion, not a slot, and the
TID accounting (§3.2) lands in the `src_bathymetry_primary` row's notes and
Karl's §2 classification decision.

---

## §3 — The five dataset targets

Each: slots filled · BACKLOG entries consolidated (by pointer — closed
later on their own boxes) · sources with licence · procedure · origin class
+ evidence · what the audit sees (probed, §0.5) · the queue row completed ·
acceptance criteria · Track-E tasks FIRED (named, not performed) · riding
decisions, labelled.

### §3.1 — CCZ geometry + APEIs/exclusions  [mechanical + judgment]

**Slots:** Contract 2 both files; Contract 5 `src_deepdata_public_context`.
**Consolidates:** the §1 AOI entry (rewritten at the E3.0 approval —
trigger Checkpoint 1; recommendation "define it around where the data
actually sits"; the recorded warning that **99.00% of the current domain
lies beyond one fitted range**, so an AOI larger than the data is a choice
to publish mostly-mean cells); the §3 context-layer entry (E5.3 commit 2 —
its public-URL trigger already FIRED and is so recorded); the §2
classify-the-context-sources entry (its `src_deepdata_public_context`
half).

**Sources, per the context-layer entry's own located list:**
- Marine Regions **MRGID 64222**, layer
  `MarineRegions:isa_ccz_managementarea` — **CC-BY 4.0**, WFS download.
  Redistribution: CC-BY permits committing the file with attribution;
  confirm the attribution string at download and record it in
  `attribution_text`.
- The **ISA shapefiles** (exploration areas, reserved areas, APEIs —
  ISBA/17/LTC/7, ISBA/18/C/22, ISBA/26/C/58, ISBA/26/C/43) — **ISA
  copyright, NOT CC-BY**. Redistribution: READ THE TERMS AT DOWNLOAD; do
  not assume. If redistribution is not clearly permitted, the pattern is
  fetch-at-build with recorded hash (the PANGAEA pattern) rather than
  committing the file. This is a per-source answer, recorded per source.

**Procedure [mechanical]:** download each; sha256 each; fill the queue row
(`license`, `accessed_date`, `content_hash`); place under `data/context/`
(inside the audit's walk — in-file `data_origin` in the same edit, per the
authoring rule); register hash + `attribution_text` in
`services/api/context.py`.

**Origin + evidence [judgment, Karl's — recorded, not decided here]:** the
context-layer entry already poses it: a hashed download from an
authoritative publisher may be **MEASURED** (the corpus's relation to
PANGAEA) rather than the LITERATURE the AOI entry assumed — which would
also take the AOI off LITERATURE's zero-observer class. Probed (§0.5):
either class lands cleanly; a MEASURED declaration passes the audit
WITHOUT a hash, so the hash discipline is the queue row's and
`context.py`'s.

**Acceptance:** files hashed and attributed; the fixture rectangle
replaced the same day; the two riding decisions RECORDED with reasoning.

**Track-E tasks FIRED:** replace
`apps/web/context/ccz_management_area_FIXTURE.geojson` + `context.py`
wiring (the context entry's own step). IF (ii) populates exclusions: the
three empty-set test updates AND **the exclusion rasterisation path in
`CutoffEconomicModel`** — not built today; the first polygon is a refusal
by name (§0.4). IF (i) resolves the AOI: the production extent
configuration task (none exists — the extent is whatever DEM a run is
handed; at CP1 the AOI must supply the domain deliberately).

**Riding decisions:** (i) the AOI [judgment — the 99.00% warning is the
decision's cost function]; its origin class [judgment]; (ii) APEIs →
`exclusions.geojson` [judgment whether; mechanical doing]; redistribution
per source [mechanical: read the terms].

### §3.2 — Real bathymetry: GEBCO + TID  [mechanical]

**The single largest unlock on the board, mislabelled a Track-G
deliverable since Phase 0 — it is a public download.** Track E's side has
been unblocked since HASH.1.

**Slots:** Contract 5 `src_bathymetry_primary` (every field); the §2
GEBCO-classification decision. **Consolidates:** §1 "Real GEBCO bathymetry
(G1.1)"; §2 "GEBCO is not uniformly MEASURED" (the TID entry); §2
classify-the-context-sources (its bathymetry half); §1 covariates.yaml
geology questions (they come due HERE — this is the moment the answers
change covariates).

**Product and release:** the current GEBCO Grid release at download time
(GEBCO_2025 or newer), 15-arc-second, **plus its companion TID grid** —
one download session, both files, both hashed. Licence: GEBCO grids are
publicly distributable; record the release's actual terms text at download
as the `is_open` evidence (fill `license`, `title`, `url`,
`accessed_date`, `content_hash`).

**Procedure:** (1) dataset §3.1 first — the subset extent IS the AOI
decision, so this SEQUENCES SECOND; (2) download global or the
subset via GEBCO's download tool; keep the pristine download (hash in the
queue row) and derive the working subset with the command recorded — the
subset is DERIVED from the download, its derivation the recorded command;
(3) **the TID accounting as a first-class step, BEFORE any covariate is
interpreted**: per-cell counts of sounding-vs-altimetry classes over the
AOI. Terrain covariates over altimetry-predicted cells measure the
interpolation's smoothness, not the seafloor — predicted bathymetry is
smooth by construction at exactly the scales the recipes probe. The
accounting feeds Karl's classification decision (single label vs per-cell;
whether the training matrix needs a TID mask).

**Origin + evidence [judgment, Karl's — the §2 entry]:** MEASURED survey
product vs LITERATURE compiled grid vs per-cell; the honest answer may not
be a single label. Audit shape probed (§0.5): a `.tif` classifies via
sidecar; MEASURED passes without a hash (the queue row carries the proof).

**Acceptance:** both grids hashed in the queue row; TID accounting
reported; the classification decision recorded with the TID numbers in
hand; the harness runs `--dem <real.tif> --dem-data-origin <decided>`.

**The CP1 re-run's stated expectations — listed so results are
confirmations, not discoveries** (each already on record):
- The occupancy/ceiling/border pins go RED BY DESIGN — 35-in-4-cells, the
  0.348 ceiling, border 0 (the §3 Checkpoint-1 re-report entry: "each
  failure is the re-report trigger, not a defect").
- The 0.348 ceiling DISSOLVES on its stated expiry as ~460 m cells
  re-separate X — and the kriging exemption (kriging never saw the
  ceiling) disappears with it, so E2.4's model comparison reads differently
  after.
- The terrain watermark reason LIFTS; economics' reason stays (the
  two-reason design). `verify_run.EXPECTED_VERDICT_SETS` may move — update
  DELIBERATELY, IN THE SAME CHANGE as the data that moves it.
- Contract 3 v3's metre windows resolve UNCLAMPED for the first time
  (BACKLOG's own note); the 6° slope filter starts meaning something.
- The covariates.yaml geology questions come due: the physically
  meaningful neighborhood scale(s) in metres (`default_window_m: 1400` is
  an engineering stand-in), absolute depth vs relative relief [judgment].
- At ~1.96 M cells the flat-array exports need tiles: **TiTiler merges
  into the API** (E5.2.md's recorded design: `tiles_url` beside
  `data_url`, dict content, no schema move) — a Track-E task, FIRED here,
  not before its consumer exists.

**Track-E tasks FIRED:** `DemGrid.load`'s south-up/rotated-transform
refusal (BACKLOG §3:1783) — due BEFORE the real DEM enters a run; the
production extent configuration (with §3.1); the TID-mask decision's
consumer if Karl decides one; TiTiler; the CP1 re-report itself.

### §3.3 — The Phase-A open corpus  [labor + judgment]

The hard one. **Slots:** Contract 8 `target_definition`; Contract 7's
three parameters; Contract 1 `abundance_basis` (⊕ required); queue rows
for each wired source. **Consolidates:** §1 training-target entry (the
burial contradiction); §1 Dryad [06]; §1 spread-over-count; §1
normalization parameters; §1 download hygiene; the §1 wet/dry entry
(shared with §3.5).

**Step 1 — THE TARGET DEFINITION, its own step with a reading list, before
any new row lands [judgment].** The [05]-vs-[01] burial contradiction is
the concrete question, and the BACKLOG calls it "the one question in this
project a geologist can settle without new data." That geologist is now
Karl. The stakes: ~11× by mass at the worst event (SO268/2_149-1, surface
0.37 kg vs published 4.1 kg). The pattern is the lead: all six
disagreeing events sit on leg 2 while all fifteen leg-1 events reconcile
exactly; five of six UNDER-record; the two largest offenders record
`Depth sed 0.000` for every nodule — consistent with
depth-not-recorded-defaulting-to-zero, a per-leg recording-protocol
difference, not random error. Reading list: `P2.B-and-P2.A.md`
(method + traps), the two raw `.tab` files, Contract 8's header (the two
EXCLUDED dead ends, with evidence). **The [05] Depth-sed parsing hazard
(§3 entry) fires the moment this analysis is re-run** — the `">0.000"`
strings and the four-state zero. If resolved, `surface_only` enters the
enum as a new admissible value with a citation (the AUTHORED→LITERATURE
promotion); either way the answer feeds Contract 4's basis question.

**Step 2 — per new MASS source, QUESTIONS with verification steps, not
assumptions.** In scope (all Phase A): **[02] [03] [04]** (DOMES-family,
MASS, TRAIN) and **[06]** (Dryad, MASS — guard-blocked until a real file
lands under `data/sources/` with its hash in the queue row). Context
classes: **[11] [12] [14]** (COVER/COUNT covariates — never
training). **[18] [19]** are GRID — benchmark/prior, never stations
([18] is §3.4's; [19] rides here for the GRADE join only).
- **Sampler comparability [judgment with a stated basis]:** DOMES-era
  free-fall grabs vs box cores — training-MASS or context? TS-6's own
  caveat (grab-sampler bias, Section 3.1) is the reason this is a real
  question. The answer is per-source, recorded in the queue row.
- **Coordinate datum and precision** for 1970s–80s positions
  [mechanical to check, judgment to accept]; `coordinate_tolerance_deg`
  gets its tuned value here with a stated basis.
- **THE WET/DRY BASIS resolved per source at ingest** — Contract 1's
  `abundance_basis` is empty on all 108 rows, [01]'s own derivation note
  says "confirm wet/dry basis", unconfirmed. The [01] adapter writes what
  the source states; ⊕ Contract 1 makes the field required ("unknown"
  admissible, empty not) — a Contract-1 bump, Karl's.
- **`is_open` and `qa_status` per row**; only `is_open == true` enters a
  published run — licences gate publication (the ledger's own rule).
- **[19]'s GRADE join** gated on `join_tolerance_km` (fill with a stated
  basis) and built as a NEW PIPELINE STAGE, not a normalizer change —
  §7's GRADE-pass-through-by-design note says exactly this.
- **SPREAD OVER COUNT, sharpened with the number the paper turns on:**
  the variogram's zero-pair window is **13–986 km** (E2.2's empty bin —
  two ~12 km clusters, ~991 km apart, nothing between). Evaluate every
  candidate source by WHERE ITS STATIONS SIT relative to that window
  before by how many rows it adds. Ten stations inside the gap are worth
  more than a hundred in the existing clusters.

**Audit + guards:** every delivered file lands under `data/sources/` with
its hash filled — that is `_require_proven_measured`'s admissibility, and
wiring without it refuses by name (the [06] incident's honest reading:
"not mislabelled, unproven").

**Acceptance:** a defensible MASS count/coverage target proposed FROM WHAT
THE SOURCES CONTAIN (not asserted in advance), plus
`mean_nodule_mass_g_source` and `coordinate_tolerance_deg` with stated
bases.

**Track-E tasks FIRED (each has its own §3 BACKLOG box; every one's
trigger reads "before wiring [02][03][04]" or equivalent):** pipeline-level
row quarantine; the deterministic tie-break (`preference_rank`); the
datetime-format dedup fix; intra-batch duplicate detection; [06]
re-wiring (the paired step the guard enforces); the D3 GRID `source_id`
scoping check + Washburn dual-class fan-out test when [19] lands.

### §3.4 — The digitized TS-6 surface (Contract 6, CP3)  [labor + two judgments]

**Slots:** Contract 6 v4's six nulls. **Consolidates:** §1 "[18]" entry.
DERIVED is decided (TAX.1, `raster_data_origin: DERIVED`) — do not reopen.

**The procedure Contract 6 v4's requirements become:**
1. **Choose the product** (`source_figure`) — Fig 5 / Fig 8 / Fig 37–38 /
   the 0.1° grid tables (Section 3.2). [judgment #1 — tables, if usable,
   dominate figure-scraping on both error and re-runnability.]
2. **`digitization_method` specific enough to RE-RUN** — DERIVED's
   evidence (the contract's own words: "a one-word method does not
   evidence a DERIVED claim"): figure + edition, georeferencing procedure
   and residual, value-extraction procedure, contour/colour mapping
   assumed.
3. **`digitization_uncertainty` NON-NULL, as a PROCEDURE not a number:**
   propose repeat-digitization spread — digitize twice (ideally with a
   varied georeference), report the per-cell spread in kg/m² as the
   digitization error WE introduce (never TS-6's own uncertainty — the
   field's comment warns exactly this). E3.3's real path REFUSES while
   null.
4. **`role_note` resolved from null [judgment #2]:** `benchmark_only` is
   the contract's (PREFERRED) — defensible under Option-A terrain-only
   covariates so long as TS-6's MODELED GRID feeds no training rows;
   station-level appendix points, if §3.3 uses them, keep it non-circular
   per the contract's own PREFERRED case. Karl decides, on the basis of
   what §3.3 actually ingested.
5. `content_hash` filled at ingestion; the queue row `[18]` completed.

**Audit (probed, §0.5):** the `.tif` classifies via sidecar
DERIVED-with-derivation; stripping the derivation is refused by name.

**Honest hours:** georeference + extraction ~6–12 h for a figure (less if
the tables digitize), + 2–4 h for the repeat pass — [labor], with the two
judgments above embedded.

**Track-E tasks FIRED:** [18] corpus re-wiring (paired step; the builder's
own docstring adds: [18]'s queue entry declares LITERATURE, so re-wiring
also needs the §3 LITERATURE-admission-path decision — the corpus GRID
rows and the Contract-6 benchmark raster are TWO artifacts with two
classes, kept apart); `test_grid_rows_are_never_flagged_observed`
re-activates itself; the corpus stops being single-source; E3.3's real
comparison path runs for the first time → CP3.

### §3.5 — Two economic scenarios with real parameters (Contract 4, CP4)  [judgment]

**Slots:** every number in `scenarios.yaml`; ⊕ the five missing slots
(E4.0 §1, already sharpened in the BACKLOG's G4.1 ask — consolidated by
pointer, NOT duplicated here): recovery fraction, uncertainty treatment,
price source, **`cutoff_basis`** (the wet/dry gap's Contract-4 half), the
difference's semantics. **Consolidates:** §1 Contract-4 entry (with
G4.1's ask); §1 wet/dry entry (with §3.3); §2 uncited-README-numbers
entry.

**THE BRACKET REQUIREMENT, stated in advance (E4.1's measured finding):**
the placeholders (10.0 / 5.5) both sit below the corpus's own
distribution (11.6–26.8 kg/m², mean 19.5) and admit the whole predictable
domain under both scenarios — the difference map is EMPTY, and two
scenarios that bracket nothing do not do the one thing two scenarios
exist for. Real cutoffs must let the scenarios DISAGREE somewhere — or,
if defensible cutoffs still cover 100%, THAT IS A FINDING ABOUT GRADE,
stated in advance, not a bug to tune away.

**Origin discipline:** prices are LITERATURE with a source and date that
LOCATE the number; cutoffs are LITERATURE if cited, or AUTHORED
`author: karl` with the rationale recorded (admissible for scenario
values — the loader's AUTHORED refusal is Contract 8's gate, deliberately
asymmetric). `illustrative_only` flips false at CP4 and the watermark's
economics reason lifts.

**TWO §2/§3 ITEMS FIRE BEFORE THE FIRST CITED VALUE LANDS — schedule
both:**
1. **LITERATURE's zero-observer gap** (§3): its trigger reads "BEFORE
   TRACK G SUPPLIES ANY CITED VALUE." One negation fixture, Track E,
   small — sequenced at §4 step 0 so it precedes even the threshold
   citation.
2. **The uncited literature-shaped numbers in the contracts README**
   (§2): "~1.5–30 kg/m²" and "~2 g/cm³" — cite them or mark them
   authored engineering rationale; trigger "before a published run."

**Track-E tasks FIRED:** the difference maps become non-vacuous (E4.2's
uniformly-empty statements retire); `EXPECTED_VERDICT_SETS` moves
deliberately; the `author_inherited_from` decision (§3 entry) fires IF an
economics raster is ever committed under `data/` — options (a)/(b)/(c),
Karl's, "not (c) silently."

---

## §4 — Sequencing: the pre-registration clock outranks all others

**CONTRACT 8's `acceptance_thresholds` MUST BE FILLED BEFORE THE FIRST
REAL-DATA RUN.** If GEBCO lands and the harness runs first, the scores for
that data exist, and every threshold set afterward is post-hoc FOR THAT
DATA, permanently — the honest declaration becomes `set_after_scores:
true`, which the guard refuses BY NAME, so precondition 6 goes from
UNFILLED (fixable) to UNFIXABLE. The mechanism's own limit (§0.3: the
date check is per-run; permanence rides on the truthful declaration and
the commit witness) is precisely why sequencing is the only protection:
nothing downstream can restore a pre-registration that did not happen.
The same shape binds **`acceptable_spatial_correlation` (G3.2) before the
first real TS-6 comparison.** The §2 pre-registration entry is OPEN by
design ("a slot is not a threshold") — this plan is where it finally
schedules. What Track E may propose: candidate FORMS. What only Karl may
do: pick and declare one, with an admissible origin (LITERATURE with a
locating citation; MEASURED/DERIVED with evidence — DERIVED from the
scores it grades is post-hoc by construction, so in practice LITERATURE).

**Candidate threshold FORMS (not numbers), for step 0 [judgment, hours,
expensive to get wrong]:**
- (a) one metric + one margin over the mean baseline, per the contract's
  question (a): e.g. "`rmse_uplift ≥ X` on the within-site design" — the
  metric named from the runner's five, the number cited;
- (b) the two-part mapping the contract's questions (a)+(b) invite: the
  margin gate PLUS an explicit yes/no on "is the within-site gate
  sufficient for a claim?" (the across-cluster comparison cannot rank
  estimators on this geometry — the two-fold theorem);
- (c) for G3.2: a published agreement criterion for benchmark comparison
  (e.g. a cited "broadly consistent" spatial-correlation floor), origin
  LITERATURE.

**The dependency-honest order** (justified; the contracts do not contradict
it):

```
step 0  thresholds pre-registered (C8; G3.2)          [judgment, hours]
        + Track E: the LITERATURE-observer fixture
          (must precede the first cited value = the
           threshold's own citation)
   │
step 1  boundaries + AOI decided (extent, origin       [mechanical +
        class, exclusions question)                     judgment]
   │        └─ the subset extent IS the AOI, so:
step 2  GEBCO + TID cut to the AOI → CP1 re-run        [mechanical]
        (DemGrid south-up fix BEFORE the DEM enters;
         EXPECTED_VERDICT_SETS updates IN THE SAME
         CHANGE as the data that moves the verdict)
   │
   ├─ step 3  TS-6 digitization → CP3                  [labor + judgment]
   │          (independent of step 4; either order —
   │           each ends the corpus's single-source
   │           state via its paired re-wiring)
   ├─ step 4  corpus expansion                         [labor + judgment]
   │          (target definition FIRST — it decides
   │           what a MASS row means before new rows
   │           land; then per-source screening)
   │
step 5  real economics → CP4 → CP5b                    [judgment]
        (cutoff_basis needs step 4's basis answer;
         the bracket requirement needs the real
         corpus distribution to bracket)
```

Why this order and not another: 0 before 2/3/4/5 is the clock (above); 1
before 2 because the subset extent is the AOI decision; 3 and 4 are
mutually independent and both post-2 only in the weak sense that their
consequences (the comparison grid, the covariate values) are only
meaningful on real terrain — the acquisitions themselves can start any
time; 5 last because `cutoff_basis` depends on step 4's wet/dry answer
and the bracket requirement is evaluated against the expanded corpus's
distribution.

**Per step — what it closes (later, on the ORIGINAL boxes), what it
fires:**

| Step | Closes (in ITS closing commit, never now) | Fires (Track E) |
|---|---|---|
| 0 | (part of) §2 pre-registration entry's schedulable half — the entry itself stays open until a threshold with admissible origin lands | LITERATURE-observer fixture |
| 1 | §1 AOI entry; §3 context-layer entry; §2 classify-context-sources (half) | fixture-rectangle swap; `context.py` wiring; exclusions test updates + rasterisation IF (ii); extent config |
| 2 | §1 GEBCO entry; §2 GEBCO-TID entry; §2 classify (other half); §1 covariates questions | `DemGrid` south-up; CP1 re-report (§3 entry); `EXPECTED_VERDICT_SETS`; TiTiler; the CP5b standing-status text (§3 entry, partially) |
| 3 | §1 [18] entry; Contract 6's six nulls | [18] re-wiring + LITERATURE-admission decision; `test_grid_rows…` self-reactivates; E3.3 real path → CP3 |
| 4 | §1 training-target, Dryad, spread, normalization-params, download-hygiene entries; wet/dry (with 5) | quarantine, tie-break, tz-dedup, intra-batch dedup, [06] re-wiring, [19] join stage + tests |
| 5 | §1 Contract-4 entry; §1 wet/dry entry; §2 uncited-README entry; §1 LITERATURE-citations entry | difference maps non-vacuous; verdict sets move; `author_inherited_from` decision if committing rasters |

---

## §5 — What the plan is not

- **Not an acquisition.** Nothing lands under `data/` in this commit.
- **Not a taxonomy change.** The AOI's origin class and
  `author_inherited_from` are reported with recommendations, decided in
  their own tasks (the TAX.1 precedent: a taxonomy widening is its own
  commit, Karl's call).
- **Not a threshold.** §4 step 0 proposes FORMS; numbers arrive with
  citations, from Karl.
- **Not a re-litigation.** TS-6 is DERIVED; the two-watermark
  representation, the serving format, and the viewer stack stand.
- **Not a Phase-B/C expansion.** [25]–[46] and the request tier are named
  out-of-alpha (§0's scope check); nothing below plans them.

---

## §6 — CP5b, derived from the checkpoints

CP5b — the alpha LAUNCH — is, by the proposal's own definition, CP5a's
deployed machinery serving a run in which every watermark reason has
lifted because the facts changed: **CP1** (steps 1–2: real GEBCO on a
deliberately-chosen AOI, terrain reason lifts, the pins re-reported,
`EXPECTED_VERDICT_SETS` moved deliberately), **CP3** (step 3: the real
digitized TS-6 with non-null digitization uncertainty, the comparison
real), **CP4** (step 5: real economics, `illustrative_only: false`,
economics reason lifts) — plus the gates whose triggers read "before a
published run" and which a launch finally fires: the LITERATURE citations
located (§1), the precision/rounding decision (§2), lockfile pinning, the
wet/dry basis recorded end-to-end (Contract 1 required + Contract 4
`cutoff_basis`), and — for any model CLAIM beyond the maps — the step-0
thresholds, pre-registered before the first real scores existed. When all
of that is true, the page's standing-status text, the E5.4 banner, and
`EXPECTED_VERDICT_SETS` all change BECAUSE THE FACTS CHANGED — each
deliberately, in the commits that change them — and the deployed URL stops
being the alpha of the machinery and becomes the alpha.

---

*Suite: untouched by this commit (docs only). 676 passed, 2 skipped,
confirmed in the foreground this session before and after the edits.*
