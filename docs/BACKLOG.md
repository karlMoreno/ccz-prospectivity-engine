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
1 added 2026-08-19 (E2.4 §3: the feature-stack manifest hashes absolute
paths, so no downstream artifact identity is portable — found by the run
manifest's own chain assertion); 2 more added 2026-08-19 at the E2.4 audit
(the leakage test's non-seed-robust magnitude pins; nothing observes the
walkthrough's own tables); 1 more at E2.5 (Contract 8's acceptance_thresholds
slot — the structural change the guard did not make unilaterally).
1 entry REWRITTEN + 4 CONSOLIDATED INTO 1 at the E2.5 approval (2026-08-19):
the `acceptance_thresholds` entry became Karl's decision to ADD the slot, and
the four items each due "at Phase-2 closeout" — P2.C, the F-6 table residue,
the leakage test's seed-fragile pins, the sole-observer pass — became §3's
single **Phase-2 closeout batch**, since E2.5 IS that closeout and all four
would otherwise have expired there one at a time. No twins: the four boxes
were removed, their bodies moved whole, and §2 keeps a pointer, not a box.
1 CLOSED 2026-08-20 (C8.1: Contract 8's `acceptance_thresholds` slot — box
checked on the ORIGINAL entry, no twin; the §2 pre-registration entry stays
OPEN, because a slot is not a threshold). The same commit corrected the §2
TRIPWIRE bullet that asserted a loader refusal which did not exist — the
source the E2.5 prompt inherited its false premise from, left standing by the
E2.5 approval's own correction pass over that entry.
1 CLOSED + 2 ADDED at P2.CLOSE (2026-08-20): the **Phase-2 closeout batch**
and all four of its sub-items are done; the two additions are findings its
own premise checks turned up and which were deliberately NOT fixed inside a
closeout — the theorem test's seed-calibrated tolerances, and LITERATURE's
missing evidence observer (§3). Net 41 − 1 + 2 = 42.
1 ADDED at the P2.CLOSE approval (2026-08-20): the two C8.1 date labels left
in `model_config.yaml` by that commit's docs-only fence.
2 ADDED at the E3.0 approval (2026-08-21), both DECISIONS rather than defects:
revisit COG at Checkpoint 1 (the format is inert at 3,400 cells and nothing
installed can validate it), and E3.3's descriptive-r-with-N_eff posture. The
AOI entry was REWRITTEN in the same commit — its trigger had expired ("before
Phase-2 prediction surfaces", a phase that ended producing none) and its
gating claim is disproved by E3.0 §2.
3 ADDED at E3.1+2 (2026-08-21), all found by the task's own probes rather
than by review: surface outputs cannot be committed under `data/` as they
stand (the origin audit sees them and refuses); E2.5's guard cannot produce a
per-estimator verdict; and `compare_to_ts6`'s type is undecided because the
manifest's TS-6 arity is singular — reported rather than picked, per the
task's instruction.
2 ADDED at the E3.1+2 approval (2026-08-21): Karl's DECISION to widen
SYNTHETIC's evidence rule (its own commit, before E3.3, with the `.tif`
classification gap riding along), and the two engine-side date labels that
commit's docs-only fence could not reach.
2 ADDED at the TAX.1 approval (2026-08-22), both CONSEQUENCES of Karl's TS-6
origin decision (Contract 6 v3, `raster_data_origin: DERIVED`) rather than
defects: E3.3 must carry the digitization error, and `digitization_method` is
now DERIVED's evidence and cannot be answered in one word.
2 CLOSED at TAX.1 (2026-08-21): SYNTHETIC's evidence rule widened
(`5d97735`) and the written rasters classified (`c6938a0`). **LITERATURE's
zero-observer gap is deliberately UNTOUCHED** — separate rule, separate
observer, its own live trigger (before Track G supplies any cited value);
folding it in would have meant changing a rule and its observer in one commit.
2 CLOSED + 1 ADDED at E3.3 (2026-08-22): the r-with-N_eff decision and the
digitization-error propagation are built (`1c159f3`, `1febedc`); the addition
is Contract 6's `digitization_uncertainty` SLOT, found ABSENT where the
prompt said null — a structural change that is Karl's, with its consumer
already built (the C8.1 sequence, one contract over).
1 ADDED-AND-CLOSED + 1 ADDED at E5.5 commit 2 (2026-08-22): the full-data
variogram parameters existed only in E3.1-2.md's prose (E5.0 §3's finding;
E5.0 was read-only and could not land the entry, so it is written here
closed, with its commit) — and the honesty-surface inputs that are STILL
prose-only after the three additions, for E5.4 to decide on. The count
header was last recounted at E3.3 (49); recounted from the boxes now.
1 ADDED at E5.5 commit 3 (2026-08-22): what committing a run directory under
`data/` requires, found by PROBING the audit on a staged production run —
including a new observation about the deep unrecorded scan (a QUOTED
declaration reads as a new use).
1 ADDED at E5.3 commit 2 (2026-08-23): the context-layer data task with its
two riding decisions (the AOI; the APEIs and exclusions.geojson). 1 ADDED at
E5.3 commit 3: the catalog is not yet data-driven (trigger: a second dataset).
1 CLOSED at E5.4 (2026-08-23): the honesty inputs still prose-only, each
decided; E5.4's disposition table added no deferral. 1 ADDED at E5.7
(2026-08-23): the page's standing status must change with the facts (CP5b);
the context-layer entry's public-URL trigger reported FIRED.
6 ADDED at G.0 (2026-08-23): the acquisition-sequence entries (step 0 +
datasets 1–5) at the top of §1, each a POINTER to
[docs/plans/TRACK-G.md](plans/TRACK-G.md) consolidating existing entries and
closing NONE — closes land on the ORIGINAL boxes in their closing commits.
§1 RE-TITLED AND RE-OWNED in the same commit: Isaac delivers nothing; Karl
is doing Track G himself (the [GEOLOGY — ISAAC] tags inside contracts are
untouched — a tag edit is a version bump; they now read as "geology
judgment, Karl's", cleanup riding each contract's next legitimate bump).
Two stale detail refs corrected against the files, scoped to the claims
verified: the normalization.yaml slots are at :67/:103/:123 (the entry said
:50/:86/:101) and the [18] guard anchor is corpus_builder.py:256–291 (the
entry said #L200, which now lands in [05]'s docstring).
3 CLOSED at G.3 (2026-08-24), each on its original box: §1 GEBCO (delivered
— GEBCO_2026 + TID, DERIVED, the ledger row the committed record; the
harness NOT run, CP1 blocked on G.0-step0 by the clock), §2 GEBCO-TID (the
accounting artifact; no training-matrix mask needed — all 35 stations on
multibeam, the per-cluster confound refuted), §3 DemGrid south-up (both
refusals, mutation-verified). The §2 classify-context-sources entry's
bathymetry HALF is decided (DERIVED) and its box stays open for the
deepdata half; the G.0-2 sequence box stays open for the CP1 re-run. Also
at G.3: the Phase-0 gitignore tif rules had matched NOTHING (trailing
comments are part of a gitignore pattern) — fixed, proven by check-ignore.
1 ADDED at the G.3 approval (2026-08-24): §3's configs-the-suite-never-
exercises entry — the class named in CLAUDE.md at ×3 (ci.yml/E5.6, the
gitignore tif rules/G.3, `.claude/launch.json` — whose fix had lived only
in the Phase-5 handoff, an open item outside this file, against its own
rule). Same commit: the ledger row's licence record CORRECTED to carry all
THREE of the terms' obligations (the missing one: "Not mislead others or
misrepresent The GEBCO Grid or its source") — G.3's own correction had
OVERSHOT, inferring absence from an inexact paraphrase; correction-drift
instance (o), the count derived. No contract version bump: a value/comment
fill within an existing entry, the same class as the original
fill-on-download.
1 CLOSED + 3 ADDED at G.2 (2026-08-25): the **AOI entry** closes on its
ORIGINAL box (no twin — the original text continues under the checked box,
the pattern G.3 used), Karl's option (b): the CCZ management area is the AOI
and the coverage denominator, `fraction_outside` 1.0 becomes 0.0, and
`aoi_coverage` (RunManifest schema 5) joins the AOI, the stations and the
fitted range. The three additions are consequences found by measuring, not
defects invented: Contract 2 cannot declare a change class (it has no version
field, so its hash is its only signal — the sharpest instance of §2's
`change_class` entry); whether the AOI should BOUND the grid, the question
behind the README line G.2 struck (the mask can only shrink, so a smaller AOI
would be the first thing here able to discard supported cells); and the
committed corpus manifest now diverging from every fresh build in four fields
at once, only one of which is about the AOI. The APEIs/`exclusions.geojson`
half is REPORTED, not closed — a different publisher, a different licence,
and two Track-E steps.
1 ADDED at the G.2 APPROVAL (2026-08-25), and four entries CORRECTED rather
than closed. The addition is §3's **seven live sites still calling the AOI a
placeholder or the context layer a fixture** — every one a false statement in
LIVE CODE (two of them reaching an emitted artifact and a served page), all
outside that commit's docs-only fence, grouped so the sweep happens once (the
E3.1+2 precedent). The corrections, all found by a verification pass over
G.2's OWN output: the context-layer entry is HALF DONE and its E5.3-era
33.8×/2.96% figures are STRUCK (the comparison was bounding-box-vs-extent, not
just the numbers — correction-drift (q)); the LITERATURE-observer entry's
deadline is recorded as EXPIRED AT G.3 (2026-08-24, one day before the arrival
it predicted) with the gap RE-MEASURED at 0 of 703 and the reason it cannot
close by adding well-formed members; the classify-context-sources entry is
NARROWED (the CCZ half answered LITERATURE on its own new row, the APEI half
open); and the AOI's origin question inside the context entry is DECIDED.
1 CLOSED at OBS.1 (2026-08-26): **LITERATURE's evidence observer**, on its
ORIGINAL box and recorded as CLOSING OVERDUE — its deadline lapsed at G.3
(2026-08-24) and was missed twice before a re-measurement found it. The
mutation score went 0 of 703 → 1 of 704. OBS.1 also swept EVERY open entry's
trigger and the result is why the class is now named in CLAUDE.md: **30 of 62
triggers name something adjacent to rather than required by the work, 24 name
a condition ALREADY TRUE today, and 9 say "any time" — a priority wearing a
trigger's clothes.** Only 3 entries survived refutation as genuinely doable
now (#43 here, plus `claim.py`'s NameError branch and the pre-registration
timestamp-in-the-hash entry, both of whose defects the sweep REPRODUCED LIVE).
No entries were re-triggered or fixed by that sweep — it reports only.
1 ADDED at TID.2 (2026-08-26): the SWOT **vertical gravity gradient as a
covariate in its own right** — a genuine scientific idea (gravity reveals
basement structure beneath sediment, and abundance is thought to relate to
sediment thickness) held OUT OF SCOPE with its reasoning, because it is a new
data source, a new contract slot, a new licence and a covariate needing its
own justification. Its trigger is written per the OBS.1 rule and the honest
half applies: it could NOT be done today, so it is a real trigger rather than
a priority wearing one.
**62 open items** (recounted from the boxes, 2026-08-26, TID.2): §1
Track G 16, §2 Karl 5, §3 Engineering 38, §4 Phase-2 risks 0 (both
closed), §6 later phases 3. §5 is fully closed.
All three E1.5 reverse-audit findings are now closed (combinators deleted,
`TerrainSource` wired, `CorpusCsvSampleSource` implemented in E2.0-1).

---

## 1. Track G acquisition queue (Karl-as-G)

*Re-titled and re-owned at G.0 (2026-08-23); was "Blocked on Track G
(Isaac)". Isaac delivers nothing — Karl is doing Track G himself, so
nothing in this section is "blocked on" anyone: it is the acquisition
queue, sequenced by [docs/plans/TRACK-G.md](plans/TRACK-G.md). Owner lines
below read "Karl (as G)" — the as-G marks work that is geology judgment or
data labor, as distinct from Karl's §2 engineering-side decisions.*

**THE G.0 ACQUISITION SEQUENCE** — six sequence entries; each consolidates
existing entries BY POINTER and closes none (constituent boxes close on
themselves, in the commits that close them). The one hard rule: **step 0
precedes ANY real-data run** — the pre-registration clock
([TRACK-G.md](plans/TRACK-G.md) §4).

- [ ] **G.0-step0 — pre-register the thresholds, before anything else.**
  Contract 8 `acceptance_thresholds` + Contract 6
  `acceptable_spatial_correlation` (G3.2), filled with an admissible
  origin BEFORE the harness ever runs on real data — after that, the
  precondition goes from unfilled to unfixable. Candidate FORMS (not
  numbers): TRACK-G.md §4. Paired Track-E step: the LITERATURE-observer
  fixture (§3 entry; its trigger "before Track G supplies any cited value"
  fires at this step's own citation). Consolidates by pointer: the §2
  pre-registration entry (which stays open — a slot is not a threshold).
  Owner: Karl (as G) [judgment]. Trigger: NOW; hard-before G.0-2.
- [ ] **G.0-1 — CCZ geometry + APEIs/exclusions.** Marine Regions MRGID
  64222 (CC-BY 4.0) + the ISA shapefiles (ISA copyright — read the
  redistribution terms per source, commit vs fetch-at-build). Fills
  Contract 2 (both files' content decisions) and the
  `src_deepdata_public_context` row. Riding decisions (Karl): the AOI, its
  origin class, whether APEIs populate `exclusions.geojson` (the first
  polygon needs the not-yet-built rasterisation path in
  `CutoffEconomicModel`, not just the E4.1 test updates — TRACK-G.md
  §0.4). Consolidates by pointer: the AOI entry below, the §3
  context-layer entry, half the §2 classify-context-sources entry. Owner:
  Karl (as G) [mechanical + judgment]. Trigger: fired (the public-URL
  fixture-rectangle trigger); sequence position 1.
- [ ] **G.0-2 — GEBCO + TID → Checkpoint 1.** The current GEBCO release +
  its companion TID grid, one session, both hashed into
  `src_bathymetry_primary`; subset extent = the G.0-1 AOI; TID per-cell
  accounting BEFORE any covariate is interpreted. The CP1 re-run's
  expectations are STATED in TRACK-G.md §3.2 so results are confirmations
  (pins red by design; terrain reason lifts; `EXPECTED_VERDICT_SETS`
  moves deliberately, in the same change as the data). `DemGrid` south-up
  fix (§3) lands BEFORE the DEM enters. Consolidates by pointer: the
  GEBCO entry below, the §2 GEBCO-TID entry, the covariates.yaml
  questions below. Owner: Karl (as G) [mechanical; the classification
  judgment]. Trigger: after G.0-0 and G.0-1. *ACQUISITION HALF DONE at G.3
  (2026-08-24): files delivered, DERIVED declared, ledger row filled, TID
  accounting produced, DemGrid assertion landed — G.3.md. Karl sequenced
  the download before G.0-0/G.0-1 (the downloaded box is a SUPERSET of any
  plausible AOI, so the AOI decision is deferred, not violated). This box
  stays open for the CP1 re-run, which remains BLOCKED on G.0-step0 (the
  thresholds — `acceptance_thresholds.value` is null, checked at G.3).*
- [ ] **G.0-3 — the digitized TS-6 surface → Checkpoint 3.** Contract 6
  v4's six nulls as a procedure: product choice, a re-runnable
  `digitization_method` (DERIVED's evidence), `digitization_uncertainty`
  by repeat-digitization spread (E3.3's real path refuses while null),
  `role_note` decided on what G.0-4 actually ingested. Paired Track-E:
  [18] re-wiring (+ the LITERATURE-admission decision its builder
  docstring names); `test_grid_rows_are_never_flagged_observed`
  self-reactivates. Consolidates by pointer: the [18] entry below.
  Owner: Karl (as G) [labor + two judgments; ~6–12 h + 2–4 h repeat
  pass]. Trigger: after G.0-0; independent of G.0-4.
- [ ] **G.0-4 — the Phase-A open corpus.** Target definition FIRST (the
  [05]-vs-[01] burial contradiction — the one question a geologist can
  settle without new data, and that geologist is now Karl; the Depth-sed
  parsing hazard fires the moment the analysis is re-run). Then
  per-source screening of [02][03][04] and [06] (guard-blocked until a
  real file + hash lands), with the spread-over-count rule sharpened to
  the 13–986 km zero-pair window. Wet/dry basis per source at ingest
  (Contract 1 `abundance_basis` ⊕ required — Karl's bump). Consolidates
  by pointer: the training-target, Dryad, spread, normalization-params
  and download-hygiene entries below. Owner: Karl (as G)
  [labor + judgment]. Trigger: after G.0-0; independent of G.0-3.
- [ ] **G.0-5 — real economics → Checkpoint 4 → CP5b.** G4.1's sharpened
  ask (the Contract-4 entry below — not duplicated here) + the five ⊕
  slots + `cutoff_basis`; the BRACKET REQUIREMENT stated in advance (real
  cutoffs must let the scenarios disagree somewhere, or 100% coverage is
  a stated finding about grade). Before the first cited value: the
  LITERATURE-observer fixture (G.0-step0's paired step) and the §2
  uncited-README-numbers entry. Consolidates by pointer: the Contract-4
  and wet/dry entries below, the §2 uncited-README entry. Owner: Karl
  (as G) [judgment]. Trigger: last — needs G.0-4's basis answer and the
  expanded corpus's distribution.

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
  admissible value. Owner: Karl (as G; the definition too — G.0-4's first
  step). Trigger: any
  time; also feeds Contract 4. Detail:
  [P2.B-and-P2.A.md](walkthroughs/P2.B-and-P2.A.md);
  [model_config.yaml](../data/config/model_config.yaml) header; the parsing
  hazard for anyone re-running the analysis is §3 ("[05] Depth sed parsing
  hazard").
- [x] **Study area / AOI scope — CLOSED at G.2 (2026-08-25).** Karl's
  decision was G.2-PRE option **(b): two concepts, kept apart.** The AOI is
  the region the project is ABOUT — externally defined, never moving as the
  corpus grows, and THE DENOMINATOR for coverage; where the model may EMIT
  values is a different question the code already answered (`PredictionGrid
  .from_stack` inherits the feature stack's extent, `manifest.prediction_grid`
  records it per run). `data/aoi/study_area.geojson` now holds the real CCZ
  management area (Marine Regions MRGID 64222, declared LITERATURE in-file,
  ledger row `src_ccz_boundary_marineregions`), and `aoi_coverage` in the run
  manifest joins the AOI, the stations and the fitted range into the one
  number this turns on: **0.036% of the 11,399,939 km2 AOI lies within one
  fitted range of any station (4,125 km2), the range itself at its candidate
  ceiling so that is a LOWER BOUND; the predictable domain is 3.04% of the
  zone.** `fraction_outside` went from 1.0 to **0.0** — measured, not assumed.
  *(a) lost* because the manifest would have kept saying what the extent WAS
  without ever saying anyone chose it; *(c), the data-defined boundary the
  planning conversation had been arguing for, lost ON A MEASUREMENT*:
  `study_area_content_hash` is in `contract_versions`, which is in
  `LEGACY_HASHED_FIELDS` and not in `HASH_EXCLUDED_FIELDS`, so a polygon
  regenerated as the corpus grows moves EVERY future run's `content_hash` and
  the denominator with it. Still open and NOT closed here: the APEIs into
  `exclusions.geojson` (§3's context-layer entry — a different publisher, a
  different licence, and two Track-E steps because E4.1 asserts the exclusion
  set is empty). Detail: [G.2.md](walkthroughs/G.2.md);
  `engine/prospectivity/provenance/coverage.py`.
  *(original entry)* ALL **108 of 108** corpus rows fall
  outside `study_area.geojson`'s Phase-0 placeholder — `fraction_outside`
  1.0 in `data/corpus/manifest.json` (E1.4 preflight confirmed 0/35 training
  points on the placeholder AOI). *Corrected at P2.CLOSE, 2026-08-20: this
  read "108 of 114", a denominator that counted the 6 fabricated in-box
  `[06]`/`[18]` rows removed in P1/P1b — so it was already wrong the day
  this file was created.*

  **THE AOI DOES NOT GATE PREDICTION SURFACES — the covariates' DOMAIN OF
  DEFINITION does** (rewritten at the E3.0 approval, 2026-08-21; E3.0 §2
  verified every clause below against the repo). The old wording implied the
  AOI blocked Phase 3, and its trigger read "before Phase-2 prediction
  surfaces" — a trigger that EXPIRED when Phase 2 ended without producing
  any. What is actually true:

  * A prediction surface can exist only where its inputs exist. RF needs all
    eight covariates at every predicted cell; outside the feature stack's
    extent they are not extrapolated, they are UNDEFINED. So the alpha's
    prediction domain IS the stack's extent — a domain-of-definition fact,
    not a geology decision.
  * **NOTHING FILTERS ON THE AOI TODAY.** `FixtureTerrainSource.load()`
    ACCEPTS the `study_area` argument and DISCARDS it; the only read anywhere
    is `corpus_manifest.py:381`'s containment count, whose own note says
    "Descriptive only… nothing filters rows on it."
  * **AND THERE IS NO PRODUCTION EXTENT CONFIGURATION EITHER.** The extent is
    a property of whatever DEM the run is handed; today the only DEM is
    `tests/fixtures/rasters.py` (100 x 34 @ 0.1°, lon [−126.5, −116.5], lat
    [11.3, 14.7]). "corpus bbox + 0.5°" describes that FIXTURE, not a
    configured domain.

  **CONTRACT-SLOT FRAMING.** The AOI is Contract 2 (`study_area.geojson`),
  and it is a SLOT Track E already reads through `StudyArea` — Track E does
  not wait on it, it builds against the shape. What Track G fills is the
  polygon; what changes when they do is which cells a surface is emitted for.

  **THE DECISION BECOMES REAL AT CHECKPOINT 1**, and that is the trigger: a
  global GEBCO DEM stops bounding anything, so the extent no longer supplies
  a domain by accident and the AOI must supply it deliberately. Options
  unchanged: AOI = sampled areas only; AOI = full CCZ with distance-growing
  uncertainty; or defer again. Recommendation still: define it around where
  the data actually sits. **Note before choosing: 99.00% of the CURRENT
  domain already lies beyond one fitted variogram range of any station**
  (E3.0 §4b) — an AOI larger than the data is a choice to publish mostly-mean
  cells. Owner: **Karl (as G; G.0-1). Trigger: Checkpoint 1** (or any earlier moment a
  non-fixture DEM enters a run). Detail:
  [data/aoi/study_area.geojson](../data/aoi/study_area.geojson); E1.4.md §1;
  [PHASE3-track-E-prompts.md](prompts/PHASE3-track-E-prompts.md) §2.
- [ ] **Real Dryad `[06]` data.** Removed from `REAL_ADAPTER_BUILDERS` in P1
  as fabricated; `_require_proven_measured()` blocks re-wiring until a real
  file exists under `data/`. Owner: Karl (as G) downloads, E re-wires
  (G.0-4). Trigger: real
  Dryad file delivered. Detail:
  [corpus_builder.py:234](../engine/prospectivity/ingestion/corpus_builder.py#L234);
  E1.3.md §13.
- [ ] **Real TS-6 `[18]` digitization (Contract 6).** Same P1b guard as
  `[06]`; `ts6_reference.yaml`'s method/figure/role_note/metrics fields are
  all `null` awaiting the digitization decisions. **The corpus is
  single-source until this or `[06]` lands.** One test re-activates itself
  when wired (`test_grid_rows_are_never_flagged_observed`). Owner: Karl
  (as G; G.0-3). Trigger: Checkpoint 3. Detail:
  [corpus_builder.py:256](../engine/prospectivity/ingestion/corpus_builder.py#L256)–291
  *(ref corrected at G.0, 2026-08-23: the old #L200 anchor now lands in
  [05]'s docstring)*;
  [ts6_reference.yaml:51](../data/ts6/ts6_reference.yaml#L51)–82; E1.3.md §15.
- [x] **Real GEBCO bathymetry (G1.1) — DELIVERED at G.3 (2026-08-24).**
  GEBCO_2026 CCZ subset (N25/S0/W-160/E-110, 15 arc-sec) + its TID
  companion, in `data/bathymetry/` (rasters untracked per the Phase-0 rule
  — whose gitignore pattern had matched NOTHING since Phase 0, trailing
  comments; fixed and proven at G.3). The ledger row is the committed
  record: DERIVED by GEBCO's own "information product" wording, both
  sha256s, the subset bbox, licence verified against the shipped terms PDF.
  **The synthetic DEM remains the CI DEM and the harness has NOT run on the
  real files — CP1 is blocked on G.0-step0 (thresholds), by the clock.**
  *(original entry)* Synthetic DEM everywhere until
  Checkpoint 1; `src_bathymetry_primary`'s title/license are `null`. The
  metre-based windows (Contract 3 v3) only resolve unclamped on the real
  DEM. Owner: Karl (as G; G.0-2 — a public download, mislabelled a
  deliverable since Phase 0). Trigger: Checkpoint 1. Detail:
  [data/bathymetry/README.md](../data/bathymetry/README.md);
  [G.3.md](walkthroughs/G.3.md);
  [source_queue.yaml:205](../data/sources/source_queue.yaml#L205), :227.
- [ ] **Geographic spread over row count.** The corpus is two clusters of
  ~12 km extent separated by ~991 km. When queueing further Phase-A sources,
  prioritise stations BETWEEN the clusters over more stations inside them —
  spread constrains the model more than n does. Owner: Karl (as G;
  G.0-4's queueing rule, sharpened there to the 13–986 km zero-pair
  window). Trigger: next
  source-queue pass. Detail: review discussion 2026-07-28; cluster geometry
  visible in `outputs/e1.4/covariate_stack_synthetic_dem.png`.
- [ ] **normalization.yaml geology parameters.** `mean_nodule_mass_g_source`
  ([normalization.yaml:67](../data/config/normalization.yaml#L67)),
  `join_tolerance_km` (:103, blocks the GRADE join), and the
  `coordinate_tolerance_deg` tune flag (:123) *(refs corrected at G.0,
  2026-08-23: the entry said :50/:86/:101, drifted)*. Owner: Karl (as G;
  G.0-4). Trigger: :67/:123
  any time; :103 before `[19]` wiring.
- [ ] **covariates.yaml geology questions — now in real distances.** The
  physically meaningful neighborhood scale(s) for nodule formation
  ([covariates.yaml:54](../docs/contracts/covariates.yaml#L54), metres/km
  since v3, not cells) and absolute depth vs relative relief (:71). Safe
  defaults stand. Owner: Karl (as G; due at G.0-2 — the moment the
  answers change covariates). Trigger: any time before Phase-2 modeling
  hardens. 
- [ ] **source_queue.yaml download hygiene.** `license`, `accessed_date`,
  `content_hash`, `sampled_area_m2` are `null` across most entries — filled
  on download per the contract's own header. Only `is_open=true` sources may
  enter a published run, so licenses gate publication. Owner: Karl (as G;
  every G.0 download). Trigger:
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
  flipped. Owner: Karl (as G; G.0-5). Trigger: Checkpoint 4. Detail:
  [scenarios.yaml:10](../data/economics/scenarios.yaml#L10)–78.
  **G4.1's ASK, SHARPENED by E4.1 (2026-08-22) — what the consumer actually
  needs, now that it exists** (`economics/cutoff.py`; the
  `acceptance_thresholds` / `digitization_uncertainty` precedent: a slot
  arrives when its consumer exists, not before):
  * **THE TWO SCENARIOS BRACKET NOTHING on today's surfaces** — measured,
    not assumed (`test_economic_cutoff.py`): kriging sits within 0.5 kg/m²
    of the 19.5 kg/m² training mean over 99.62% of the domain and RF's
    plateaus lie in [15.1, 21.7], so cutoffs of 10.0 and 5.5 both admit
    the WHOLE predictable domain (2,880 of 2,880 cells, 347,707 km²) at
    z = 0 AND z = 1, and the difference map is EMPTY for every estimator.
    This is a property of the cutoffs' relation to the training mean, not
    of the seafloor — and it means the placeholders do not do the one thing
    two scenarios exist for. The ask: cutoffs that bracket the corpus's own
    distribution (11.6–26.8 kg/m², mean 19.5), or a stated reason the
    bracket should sit below it (the TS-6 anchors quoted in the comments
    are from a different, grab-sampler-biased distribution — the file's
    own caveat says so).
  * **Five slots Contract 4 does not have, each with a consumer now or
    named** (E4.0 §1): (a) a RECOVERY FRACTION — `cost_model` carries a
    recovery *cost*, not a recoverable share, so "abundance × recovery" has
    no parameter; (b) the UNCERTAINTY TREATMENT — Decision 2's confidence
    levels are a model default (`z ∈ {0, 1}`), not a contract value;
    (c) a PRICE SOURCE — `price_usd_per_tonne: 0` with nowhere to cite
    from, so `dollar_value` refuses by name; (d) the WET/DRY BASIS the
    cutoff is on (the separate entry below — a Contract 1 gap too);
    (e) the difference's semantics, today a comment. Owner: Karl (as G:
    values; the slots his engineering-side call). Trigger: Checkpoint 4,
    and (d) before any published run.
- [ ] **THE WET/DRY BASIS IS RECORDED NOWHERE, AND IT NOW HAS A LIVE
  CONSUMER** (found at E4.0 §1, confirmed at E4.1 commit 2, 2026-08-22;
  deferred rather than invented — a basis picked here would be an AUTHORED
  value in a training target). What each source actually says, verified:
  Contract 1 has `abundance_basis` (enum wet | dry | unknown, NOT
  required); the corpus's 108 rows leave it EMPTY — not even "unknown";
  `source_queue.yaml` `[01]`'s own derivation note reads "reported directly
  (kg/m2); **confirm wet/dry basis**" — unconfirmed at the source;
  `normalization.yaml:57` says "record wet/dry basis; do not silently mix
  bases"; Contract 8's `target_definition` (`total_as_published`) names no
  basis; and Contract 4's `grade_units: kg_m2` "must match the sample
  unit" with NO basis slot, while its cutoffs are anchored to TS-6's
  distribution, whose basis is also unstated. So the model compares a
  cutoff in kg/m² of SOMETHING against a target in kg/m² of SOMETHING
  ELSE-OR-THE-SAME, and nothing in the repo can say which. **Two
  contracts, one gap:** Contract 1 should REQUIRE `abundance_basis`
  ("unknown" is an admissible answer; empty is not) and the `[01]` adapter
  should write what the source states; Contract 4 needs a `cutoff_basis`
  beside `grade_units`. Owner: Karl (as G: the [01] basis and TS-6's;
  both slots his engineering-side call — G.0-4 + G.0-5).
  **Trigger: before any published run; before Checkpoint 4.**
  Detail: [E4.1.md](walkthroughs/E4.1.md) §2.
  **UPDATE 2026-08-28 (WET.1) — the gap STAYS OPEN; one attempt to close it
  from the primary sources returned AMBIGUOUS.** [03] and [04] were tested
  against each other over their 19 shared RP-8-OC-76 Leg 9 box cores, on the
  hypothesis that [04] is dry+salt-free and [03] Table 8 wet+salted. Piper's
  Table 9 caption (p. 458, verified) says its column-9 average "was lowered by
  20% to give a nodule concentration on a dry-weight and salt-free basis",
  which predicts a ratio [04]/[03] of 0.80. **Observed median 0.800 (n=17,
  geomean 0.810, 95% CI 0.696–0.950, excluding 1.00) — on the predicted value,
  and still not decisive**, because the ratios span 0.593–1.220 (2.06×) around
  a constant a basis conversion cannot vary, and because [03]'s own Table 9
  prints "-" in the box-core Weight column for box cores 11 and 23 while
  Table 8 prints values for them — so **Table 8's Concentration column is not
  uniformly a weighed box-core mass**, and a method offset of the same size and
  direction as the basis offset is riding in the same number. `abundance_basis`
  therefore stays UNRECORDED for [03] and [04] rather than guessed.
  **VERDICT ACCEPTED 2026-08-28: AMBIGUOUS** (not a failure — the distribution
  was shown and a confound was correctly refused as a confirmation). The
  distribution in full, ratio [04]-derived / [03] Table 8 per shared box core:
  `BC6 0.925 · BC7 0.593 · BC8 0.958 · BC9 0.667 · BC10 0.782 · BC11 1.240 ·
  BC12 1.029 · BC13 1.220 · BC15 0.834 · BC16 0.760 · BC18 1.020 · BC19 0.800 ·
  BC20 0.719 · BC21 0.631 · BC22 0.696 · BC23 2.414 · BC24 0.863 · BC27 0.950 ·
  BC28 0.605`.
  **SUPERSEDED IN PART, same day (WET.1 commit 2):** the confound is now derived
  to its floor — [03] Table 8 is `0.08 × Coverage × Diameter` throughout, so the
  ratio above compares a balance reading against a photograph and is not evidence
  about basis at all. See the entry below for what the gap now is, per source.
- [ ] **Close the wet/dry gap on the DOMES family — REVISED 2026-08-28 (WET.1
  commit 2): the step this entry used to name is UNDER-POWERED, and for [03]
  Table 8 the gap is INAPPLICABLE rather than open.** As first written, this
  entry named "transcribe [03] Table 9's Weight column and re-run the ratio" as
  the closing step. Two derivations changed that. **(a)** [03] Table 8's
  Concentration column reproduces as `0.08 × Coverage% × Diameter_cm` for
  **75 of the 79** rows that print both inputs (single-constant admissible
  interval [0.07995, 0.08007]; Sites A and B reproduce with no exceptions), and
  Piper's own Techniques section (p. 439) says the abundances "were estimated
  from photographs of box cores" — so **Table 8 contains no mass measurement
  anywhere**, and a wet/dry question is a category error against it.
  `abundance_basis` cannot be filled for Table 8 with any value, `"unknown"`
  included. **(b)** Table 9's Weight column is printed to **1 kg/m²** — ±0.5,
  i.e. **±16.7% at its minimum (3), ±4.5% at its median (11), ±2.5% at its
  maximum (20)** against a 20% effect. Resolution alone does not sink it (the
  effect is 4.4× the noise at the median); what sinks it is that the comparison
  would weigh **[04]'s unstated basis against [03]'s unstated basis** — two
  unknowns, one equation, unable to say which side is dry. **Marked
  UNDER-POWERED, not pending.**
  **The gap, per source:** [03] Table 8 → **INAPPLICABLE (closed as
  not-well-posed)**; [03] Table 9 col 9 → **ANSWERED** (dry, salt-free, by its
  own caption); [03] Table 9 col 7 → **OPEN**, protocol unstated; [04] Table 1
  → **OPEN**, protocol unstated. **What would actually close the two OPEN ones:
  a document stating a drying/weighing protocol for either side** — first
  candidate **Sorem et al. 1979a** (pp. 475–527 of the same Plenum volume as
  [03]; the chapter [04] Table 1 is drawn from), **not on disk**.
  **RETRIEVAL ATTEMPTED 2026-09-01 AND NOT OBTAINED** — SpringerLink paywalled (303
  to auth), HathiTrust 403, no open copy found; Crossref returned metadata only.
  **The gap therefore stays OPEN, not resolved by default** — the fallback would be
  to guess a drying protocol, which is what this entry exists to refuse. Routes are
  logged so the next attempt does not repeat them:
  [RETRIEVAL-LOG.md](data-sources/RETRIEVAL-LOG.md) §1. **Highest-value remaining
  route: CU Boulder ILL for the volume** — it yields this chapter *and* a clean
  copy of Table 8; not attempted here because it needs Karl's institutional
  sign-in. Plus, still,
  a stated basis for TS-6's own distribution — the other half of the same gap,
  carried in the entry above. Owner: Karl (as G). **Trigger: acquisition of
  Sorem et al. 1979a — this one is a real trigger**, because unlike the
  superseded step 1 the work genuinely cannot proceed without it.
  Detail: [WET.1.md](walkthroughs/WET.1.md) §9, §11.
- [ ] **[03]'s `evidence_classes` and `data_origin` are wrong after WET.1 §9 —
  two contract-bearing fields, flagged not changed** (found and deferred at
  WET.1 commit 2, 2026-08-28). The PANGAEA dataset catalogued as `[03]` *is*
  Table 8 — its own citation line reads "(Table 8, pages 454-455)". Since that
  table's Concentration column is a closed form over Coverage and Diameter
  (§9), (a) `evidence_classes: [MASS, COVER]` would admit **79 computed rows
  into a training target as if they were weighings**, and (b) `data_origin:
  MEASURED` fails TAX.1's own rule — what the artifact IS decides its class, and
  a column computed from two measured inputs is **DERIVED** (the Coverage and
  Diameter columns stay MEASURED). Both left as-is deliberately: changing either
  moves a field the production guard reads, which is Karl's call, not a
  recording task's. Owner: Karl (as G). **Trigger: before wiring [03] into any
  adapter** — the fields are inert until then and wrong the moment they are not.
  Detail: [WET.1.md](walkthroughs/WET.1.md) §9, §12.
  **HALF CLOSED at WET.4 (2026-09-01).** `data_origin` is **CORRECTED
  MEASURED → DERIVED**, with the derivation formula and its inputs' origins now
  in the row's `derivation` field — the evidence DERIVED requires. It is stable
  under the still-open M.W. question, because `combine_origins` returns the
  least-real input and MEASURED + DERIVED = DERIVED, so no resolution of WET.2's
  P4 class can move it back. Paired Track-E re-wiring landed in the same commit:
  two tests in `tests/test_corpus_builder.py`, both mutation-verified.
  **The correction removed a live latent hazard, not a cosmetic one:** before it,
  [03] was refused by `_require_proven_measured` *only* because its
  `content_hash` was null. That refusal would have vanished the moment Track G
  downloaded the file and filled the hash — a routine, expected action — silently
  admitting 79 computed rows as measurements. The refusal is now on the origin
  and is unconditional; `test_the_derived_refusal_does_not_depend_on_pending_hash_evidence`
  pins exactly that by giving the entry a real matching hash and asserting it is
  still refused.
  **`evidence_classes` REMAINS OPEN — the task's STOP condition fired.** COVER is
  settled and correct. MASS cannot be removed: doing so would assert that no row
  of Table 8 is a mass, and WET.2's 24 Moana Wave rows (P4) returned UNRESOLVED
  with NO DISCRIMINATOR AVAILABLE, so they may be weighings. What is established
  is that MASS is wrong for the other 87 rows. **What would close it:** the same
  evidence the P4 entry names — a Moana Wave DOMES abundance source. Failing
  that, whoever wires [03] must narrow the list to `[COVER]` in the wiring commit
  itself; the invariant test
  `test_each_wired_adapter_produces_exactly_the_classes_its_source_queue_entry_declares`
  compares adapter output against this list and fails loudly if they disagree.
  Owner: Karl (as G). **Trigger: resolution of the P4 class, or the commit that
  wires [03] — whichever comes first.** Detail:
  [WET.1.md](walkthroughs/WET.1.md) §27–§30.
- [ ] **`dangling_sidecar_entries` is VACUOUS on the real tree** (found at G3.1,
  2026-09-01, by a mutation that was expected to fail and did not). The check
  iterates `rel_paths` for files named `data_origin.yaml`, but
  `tracked_subject_files()` **strips sidecars from that list by construction**
  (`_is_the_sidecar_mechanism`), so the loop body never executes and the function
  returns `[]` unconditionally. **Measured:** zero sidecars appear in the audit
  subject list while **six** are tracked under `data/` and `tests/fixtures/`. The
  unit test at `tests/test_data_origin_audit.py:790` passes a synthetic
  `[SIDECAR_NAME]` list and does exercise the logic; the real-tree assertion at
  `:787` **cannot fail**. Proven by adding a sidecar entry naming the untracked
  `ts6_abundance.tif` — the audit passed. This is the coverage-that-isn't shape the
  audit module's own header warns about, inside the audit module. **Not fixed at
  G3.1** — a test-mechanism defect is not part of landing a digitization, and
  bundling it is what that task forbade. **The fix is one line** (pass the tracked
  sidecar list, or stop stripping sidecars before this check), plus a negation
  fixture so it can fail. Owner: E. **Trigger: none — this is a PRIORITY, not a
  trigger.** The defect is complete and the remedy needs nothing that does not
  exist. Detail: [G3.1.md](walkthroughs/G3.1.md) §6.
- [ ] **Nothing in the TS-6 comparison path reads `is_open`, so the benchmark's
  licence gate is a declaration without a consumer** (found and deferred at G3.1,
  2026-09-01). [18] is now `is_open: false` with an ALL RIGHTS RESERVED licence
  string, because ISA Technical Study No. 6 is all rights reserved and the
  digitized raster must not enter a published run. What enforces that today: the
  queue file's own header rule, the new observer
  `test_ts6_is_not_open_so_it_cannot_enter_a_published_run` (which pins the
  declaration), and `role_note: benchmark_only` (refused when null). **What does
  not: any code.** `grep is_open engine/prospectivity/ts6/` returns nothing;
  `is_open` flows only through the ingestion adapters into per-row metadata, and
  [18] has no adapter. So a run could load the benchmark raster with no code
  consulting the licence flag. **What would close it:** a gate in the comparison
  or harness path that refuses a non-open benchmark in a run marked publishable —
  the same shape as the existing origin watermark, one field over. Owner: Karl
  (whether to gate) + E (the gate). **Trigger: before any published run.** Detail:
  [G3.1.md](walkthroughs/G3.1.md) §7.
- [ ] **DECIDE: may [04] take its position from [03] Table 10?** (open decision,
  filed at POS.1, 2026-09-01, at the moment the measurement was handed over
  undecided. **POS.1 measured the option; it did not take it.**) [04] carries a
  weighed mass over a stated 0.25 m² and **no coordinates**. [03] Table 10 (printed
  p. 464) is the only per-core coordinate record in either document.
  **What POS.1 measured that bears on the decision:**
  **(a) Availability — total.** 21 of 21 [04] data cores have a coordinate in
  Table 10 on the station+box-core key, including `9-14` and `19-25`, the two
  incomplete-recovery cores Table 8 omits.
  **(b) Quality — sufficient.** 0.1 arcmin printed → ±92.6 m lat / ±89.4 m lon,
  worst case 129 m, which is **6.5% of the narrowest 2 km lag bin**; the shortest
  observed separation (1.27 km) exceeds it ~10×.
  **(c) One source defect that must be handled first.** Table 10's core `3-8`
  prints `126°59.3'`, 104.1 km from the Site C centroid with a depth that says it
  belongs in the cluster; read `125°59.3'` it sits 3.2 km from `1-6`. Re-read at
  1400 dpi — **printed that way, a defect in [03]**. **CONFIRMED at POS.1a by this
  chapter's own Figure 6**, the Site C box-core map: it plots `Box 8 / Sta 3` inside
  the survey area at a measured **125°59.5′ W**, agreeing with the one-digit fix to
  0.2′ (~360 m), while the printed `126°59.3′` lies **47′ (~85 km) west of the
  figure's own western edge** — unplottable on its own survey map. **So correcting
  `3-8` is now the cheap option and excluding it (which costs 20 pairs) is no longer
  the only safe route.** Choosing between them is part of this decision; POS.1a did
  not choose, and the transcription still carries `126` as printed.
  **(d) What it would buy.** 190 pairs (20 cores), separations 1.27–26.68 km, every
  bin populated to 13 km and 63 pairs at 13–26.7 km — extending lag support into
  the bottom of the recorded 13–986 km zero-pair window, though not closing it.
  **(e) What it would collide with.** [04] is a **subset** of [03] and adds no
  station [03] lacks. **[02] and [04] share 19 physical box cores.** If [02] later
  enters as MASS alongside [04], those 19 are double-counted without a dedup rule.
  **THE PROVENANCE QUESTION THIS OPENS, and the reason it is a decision and not a
  wiring task:** a row whose abundance is MEASURED from [04] and whose position is
  MEASURED from a *different publication* has **two origins in one row**, and the
  corpus has no per-field provenance today — `data_origin` is per source, and
  `combine_origins` returns the least-real input, which would make the whole row's
  origin a single label over two different provenances. Deciding "yes" therefore
  implies either a per-field provenance mechanism or an explicit recorded decision
  that a borrowed coordinate does not change the row's origin. Neither exists.
  Owner: Karl (as G — the geology call) + E (any mechanism it implies).
  **Trigger: before [04] is wired into any adapter.** The measurement is complete
  and needs nothing further; only the decision is outstanding. Detail:
  [POS.1.md](walkthroughs/POS.1.md).
- [ ] **Two Figure 38 verification checks are BLOCKED on the absent render**
  (found and deferred at G3.2, 2026-09-01, at the moment each check stopped).
  **(1) The georeference linearity residual was never measured.** The sidecar records
  finding 11 vertical and 5 horizontal graticule lines while pinning 2 per axis as
  anchors, so **9 vertical and 3 horizontal interior lines are available as residual
  checks and none has been evaluated**. The gate — *max residual > one output cell
  means the recorded `digitization_method` is wrong* — is therefore **UNEVALUATED,
  NOT PASSED**. **(2) The nodata seam's cause is unidentified** (see the entry
  below). Both need the render: `ts6fig/f38_hi-080.png` is absent and `pdftoppm`,
  `pdftocairo` and `gs` are all missing. A different rasterizer will not do — the
  georeference constants are poppler-specific (see the re-runnability entry below).
  **What would let them run:** the same thing that closes re-runnability — archive
  the 400-dpi render and hash it, or install poppler and re-derive the four
  graticule constants from a fresh render. Owner: Karl (as G).
  **Trigger: whenever the render is produced** — both checks should run in that same
  session, before the method is trusted as re-runnable. Detail:
  [G3.2.md](walkthroughs/G3.2.md) Checks 1 and 2.
- [ ] **Nodata seam in the TS-6 raster at column 149 (−145.05°) — a known defect
  with an unidentified cause** (found at G3.2, 2026-09-01). 3 valid cells against
  neighbours of 73 and 77, so **72 cells lost, 0.246% of the 29,252 valid cells**;
  only rows 52/54/57 survive. **No other graticule column shows any depletion** —
  all eleven were checked and every other one is flat. The obvious causes were
  tested and ruled out: every graticule falls exactly on an output-cell boundary
  (5° / 0.1° = 50 cells), 236 other columns share the same 6-px sampling window,
  and the −145° line actually sits in **column 150, which is full at 77** — the seam
  is one column west of it. So something occupies render px 1727–1732 that is not at
  the other ten lines, and naming it needs the render. **The fix is therefore NOT
  confined to an identifiable parameter and nothing was applied.** Magnitude is
  small and bounded; this is a completeness defect, not a correctness one. Owner:
  Karl (as G). **Trigger: whenever the render is produced.** Detail:
  [G3.2.md](walkthroughs/G3.2.md) Check 2.
- [ ] **The "ISA, 2012" versus TS-6 citation question for [19] — OPEN, and it had no
  entry until now** (filed at G3.2, 2026-09-01; the task premise said this question
  "keeps its BACKLOG entry" and **there was none anywhere in the repo**, so the
  corroboration below had nothing to be distinguished from). [19]'s own metadata
  reads *"Nodule Abundance (kg/m2) obtained from **ISA, 2012** (2009 year) and
  proprietary information (2018 year)"*, while [18] is **ISA Technical Study No. 6
  (2010)** — different years on their face. **G3.2 produced geometric CORROBORATION,
  not resolution:** [19]'s open-year (2009) subset ends at −119.25 (cell centre;
  0.5° grid, so edge −119.00) against the Figure 38 raster's −118.80 — **0.20–0.45°,
  less than one of [19]'s own cells** — while its proprietary 2018 subset stops
  704 km away. Two surfaces sharing an eastern limit is evidence of a shared source;
  it is **not identification of that source**. "ISA, 2012" could be a later ISA
  publication reproducing the same surface, a different technical study, or a
  mis-citation. **What would close it:** locating the ISA 2012 publication [19]
  cites and comparing its abundance surface against TS-6's Figure 38. Owner: Karl
  (as G). **Trigger: before [19]'s GRID rows are used to corroborate [18], or
  vice versa** — the two must not be treated as independent until this is settled.
  Detail: [G3.2.md](walkthroughs/G3.2.md) Check 6.
- [ ] **[19] declares `is_open: true` but its own metadata says 426 of its 2,790
  nodule-abundance rows are "proprietary information"** (found in passing at G3.2,
  2026-09-01; flagged, NOT changed — `is_open` is contract-bearing and the licence
  discipline reads it, and correcting it was outside that task). The split is by the
  `Year` column: **2009 rows (n=2,364) from "ISA, 2012"**, an open citable source;
  **2018 rows (n=426) from "proprietary information"**. A single row-level flag
  cannot be true of both halves. **What would close it:** either restrict [19]'s
  ingestion to the 2009 subset and keep `is_open: true`, or split the declaration.
  Note this interacts with the licence gap already recorded for [18] — nothing in
  the comparison path reads `is_open` anyway. Owner: Karl (as G). **Trigger: before
  [19] is wired.** Detail: [G3.2.md](walkthroughs/G3.2.md) Check 6.
- [ ] **The Figure 38 digitization is re-runnable only IN PRINCIPLE — its input
  render is absent and its georeference is tied to one renderer** (found at the
  G3.1 review, 2026-09-01, and deferred at the moment the commit was made).
  `data/ts6/digitize_fig38.py` reads `SRC = 'ts6fig/f38_hi-080.png'`, a 400-dpi
  render of `tstudy6.pdf` that **exists nowhere** — not in the repo, not under
  `~/CCZ/downloads/ts6/`. (The committed `ts6_fig38_digitized.png`, 9,162 bytes, is
  an output preview, not the input.) The script also writes to
  `OUT = '/mnt/user-data/outputs'`, a sandbox path that does not exist here.
  **Two things stand between "recorded method" and "re-runnable method":**
  (a) **poppler is not installed on this machine** — `pdftoppm` is absent — so the
  render named in `digitization_method` cannot currently be produced at all; and
  (b) **the georeference constants are renderer-specific.** `X0=754.5, X1=4017.5,
  Y0=736.5, Y1=2127.0` are pixel positions read off *poppler's* 400-dpi
  rasterization. **A different rasterizer invalidates them even at the same dpi**,
  because sub-pixel placement and anti-aliasing differ between engines — and the
  extraction is an RGB-tolerance match (`TOL = 26`) over anti-aliased fills, so it
  is sensitive to exactly that. Re-rendering with PyMuPDF or Ghostscript instead
  would silently shift every cell boundary rather than fail loudly.
  **What is NOT at risk:** the deliverable itself. The raster, the arrays and the
  sidecar are committed or hashed, the raster matches the midpoint array
  cell-for-cell (29,252 valid cells) and its recorded `content_hash` matches its
  bytes, and the sidecar's repeat-digitization measurement (99.31% / 98.73% class
  agreement at 300/500 dpi) already bounds the tracing error. This entry is about
  **regenerating** the surface, not trusting the one in hand.
  **What would close it:** either archive the 400-dpi render itself beside the
  script and hash it, or install poppler and re-derive the four graticule constants
  from a freshly produced render, recording both the poppler version and the
  render's hash in the sidecar. The second is better — it makes the method
  self-contained — and it is the one that must happen if the render is ever
  produced by a different engine. Owner: Karl (as G). **Trigger: before anyone
  needs to re-run or re-render the digitization** — including the six verification
  checks, if any of them requires going back to the image. Detail:
  [G3.1.md](walkthroughs/G3.1.md) §1, §9.
- [ ] **Contract 6's `source_id: src_isa_ts6` is a dangling reference** (noticed at
  G3.1, 2026-09-01, while filling the contract; not fixed there because changing a
  contract field is its own decision). `data/ts6/ts6_reference.yaml` names
  `source_id: src_isa_ts6  # -> Contract 5 entry`, and **Contract 5 has no such
  entry** — the TS-6 row is `src_ts6_grid` [18]. `FileTS6Reference` already hard-codes
  the correct one (`DEFAULT_SOURCE_ID = "src_ts6_grid"`), so nothing is broken
  today; the contract simply points at a source id that does not exist. Fix is
  either renaming the field's value to `src_ts6_grid` or adding the entry, and it
  should carry a `reference_version` note. Owner: Karl. **Trigger: none — a
  PRIORITY.** Detail: [G3.1.md](walkthroughs/G3.1.md) §9.
- [ ] **[14]'s `area_percent` denominator is not determinable from the deposit**
  (found and deferred at AREA.1, 2026-09-01, at the moment the STOP condition
  fired). [14] carries three area-related columns. Two are now settled: every
  per-m² density column is computed against **`Export_Area`** (verified by
  recomputation — 239/239 exact, max diff 1.8e-15; `image_area_m2` matches 0/239),
  and that fixes `image_area_m2` as the raw frame (mean 4.447 m²) and `Export_Area`
  as the analysed sub-area (mean 2.513 m², a fixed 56.50% of the frame). **Which of
  the two `area_percent` was computed against is unresolved, and nothing on disk
  can resolve it:** the R script never assigns `area_percent` (all 13 occurrences
  are reads) and never mentions either area column; the workbook contains **zero
  formulas**; the deposit's own `Metadata.docx` states that *"intermediate
  data-processing steps performed prior to creation of this dataset are not
  included in this repository"*; the numerator (a nodule area) is **not a published
  column** under either denominator; and `Export_Area / image_area_m2` is a
  **constant 0.5650 on all 279 rows**, so the two candidates differ only by a global
  ×1.7699 and no internal-consistency check can separate them even in principle.
  Recorded OPEN rather than inferred, per the task's own STOP condition.
  **Cost today: none.** [14] is COVER/COVARIATE and is never converted to kg/m², so
  no consumer reads `area_percent`'s scale. **It becomes live the moment
  `area_percent` is compared against another source's cover fraction** — [11] Amon
  or [12] APEI-6 — since 1.77× exceeds the between-site differences such a
  comparison would be looking for. **What would close it:** the intermediate
  processing the metadata says was withheld — the image-annotation export that
  produced the nodule areas — or a statement from the authors; failing either, the
  paper's own methods section (Philbert, Purser, Böhringer & Thomsen, *Asymmetric
  recovery of benthic megafauna after a polymetallic nodule mining trial in the
  CCZ*), which is **not on disk**. Owner: Karl (as G). **Trigger: before
  `area_percent` is compared against any other source's cover fraction** — a real
  trigger; until then the ambiguity is inert. Detail:
  [AREA.1.md](walkthroughs/AREA.1.md) §1–§2.
- [ ] **The [02]-vs-[03] event disagreement is asserted but unverified in this
  repo** (carried into the record at WET.3, 2026-08-31, and deferred at the moment
  it was carried). WET.3 recorded an **author-overlap linkage** between [02]
  (Fewkes et al. 1980, USBM OFR 108-80) and the chapter behind [04] (Sorem et al.
  1979a) — verified from both PDFs, including that the chapter is **cited two
  different ways**, with W. R. Reinhart present in Piper 1979's reference list
  (p. 473) and absent from Sorem 1989's (p. 200). The linkage is a caution against
  counting [02] as independent corroboration of [03]/[04]. **The counterweight — that
  [02] and [03] disagree on their shared events, which would show they are not the
  same measurements — was carried from the task prompt and NOT established here**,
  because analysing [02]'s data was out of scope. No record in this repo asserts it
  either: [03]'s queue row says only "Compare events against [02] before dedup
  (DOMES family, rule 1)", which sets up the comparison without having run it.
  **What would settle it:** the event-level comparison that note already calls for —
  match [02]'s DOMES Site A/B/C box-core kg/m² against [03] Table 8's rows on
  station/box-core, and report agreement or disagreement per shared event. Note
  before running it that WET.2 showed Table 8's values are **photographic estimates,
  not weighings**, so a disagreement would be expected and would say nothing about
  [02]'s basis. Owner: Karl (as G). **Trigger: none — this is a PRIORITY, not a
  trigger.** Both sources' data are already on disk. Detail:
  [WET.1.md](walkthroughs/WET.1.md) §24.
- [ ] **[03] Table 8's 24 Moana Wave rows are UNRESOLVABLE from sources on disk**
  (found and deferred at WET.2, 2026-08-30, at the moment the discriminator search
  returned empty). WET.1 §9's constant fit covers only rows printing both Coverage
  and Average Diameter (79 rows). **32 of Table 8's 111 rows do not**, and the larger block —
  **24 rows, coinciding EXACTLY with the caption's "M.W. Series ... collected by the
  R/V MOANA WAVE"** (set identity, 24 == 24) — prints neither input and carries
  non-zero Concentrations. Nothing establishes whether those values are weighings,
  box-core photo estimates with unprinted inputs, or bottom-photograph estimates;
  the Techniques section (p. 439) describes all three methods and attributes none
  of them to the M.W. series. **`abundance_basis` for these 24 rows is recorded
  UNRESOLVED — deliberately distinct from INAPPLICABLE** (asserts no mass exists;
  correct for the 78 fit-domain rows) **and from OPEN** (asserts a mass exists whose
  basis is unstated; correct for [04] Table 1 and [03] Table 9 col 7). For P4 we do
  not know the values are masses at all, so `"unknown"` would over-claim.
  **Bounded discriminator search, all four tests reported with their power** (detail
  in [WET.1.md](walkthroughs/WET.1.md) §17): (A) reachability under the fitted
  equation — 24/24 reachable within Table 8's own printed input ranges, median 30
  distinct (Coverage, Diameter) pairs per printed value, so **no power**;
  (B) last-decimal-digit signature against the fit-domain rows — 6/24 end in `.0`
  against 11/78, exact binomial **p = 0.112**, and structurally blind besides, since
  a weighed and a computed mass printed to one decimal share the same support;
  (C) other tables in [03] carrying the same cores — **`MOANA`/`M.W.` occur on
  pp. 454–455 only**, i.e. inside Table 8 itself; Table 9 is RP-8-OC-76 and Site C
  only, Table 10 is station-boxcore chemistry with no M.W. label, Table 6 is
  sediment leachate; and [04] shares not one core with the series; (D) prose stating
  a method — none. **Outcome: NO DISCRIMINATOR AVAILABLE.**
  **What would resolve it:** a document reporting the R/V *Moana Wave* DOMES
  box-core work with its abundance method — the cruise reports for `M.W.8`,
  `M.W.13A/13B` and `M.W.16`, or whichever companion chapter of Bischoff & Piper
  (eds.) covers the Moana Wave stations. **None is on disk.** **Sorem et al. 1979a —
  the most likely of them — was attempted 2026-09-01 and NOT obtained** (SpringerLink
  paywalled, HathiTrust 403; metadata only via Crossref), so P4 stays UNRESOLVED and
  nothing was settled by default: [RETRIEVAL-LOG.md](data-sources/RETRIEVAL-LOG.md)
  §1. Failing that, the 24
  rows stay UNRESOLVED permanently and must never be admitted as MASS.
  **HAZARD to carry into any such attempt:** the `M.W.13A`/`13B` box-core numbers
  run 2–12, and **seven of them (6, 7, 8, 9, 10, 11, 12) collide numerically with
  Table 9's RP-8-OC-76 box-core numbers** — a lookup on "Site C box core N" returns
  an *Oceanographer* weight for a *Moana Wave* row. This is WET.1 §3's recurrence
  hazard one level down. Owner: Karl (as G). **Trigger: acquisition of a Moana Wave
  DOMES cruise/abundance source** — a real trigger; the work cannot proceed without
  one. Detail: [WET.1.md](walkthroughs/WET.1.md) §14–§18.
- [ ] **[03] Table 8's printed averages do not recompute from its printed rows —
  the source has DROPPED ROWS** (found at WET.1 commit 2, 2026-08-28; a defect
  of the source, not of the transcription — row counts were confirmed twice,
  by image reads and by clustering the PDF's own word positions). Sites **A and
  C fail on all three columns**, Site B on Coverage only. Implied denominators
  against printed row counts: A 28/27, 26/25, 28/27 — **exactly one more row on
  all three columns**, and the bounds that row must satisfy are mutually
  consistent (coverage ≤13%, diameter ≤0.5 cm, concentration ≤2.7 kg/m², itself
  consistent with §9's formula at 0.52) — one near-barren core present in the
  averages and absent from the table. C: 40/39, 40–41/38, **54/50** — at least
  four rows. B Coverage implies **19–20 against 21 printed**, the only column
  running the other way; recorded, not explained. Table 8's working set held
  **≥116 rows against the 111 it prints**. **The 19 cores used in the WET.1 join
  sit entirely inside Site C**, the worst-affected site — the join is unharmed
  (it uses per-row values, never the printed averages), but this bounds how far
  the source can be trusted to have printed what it computed. Consequence to
  decide: whether a source that cannot reproduce its own averages should carry a
  `qa_status` below the default. Owner: Karl (as G). **Trigger: none — this is a
  PRIORITY, not a trigger.** The finding is complete; only the disposition is
  open. Detail: [WET.1.md](walkthroughs/WET.1.md) §10.
- [ ] **LITERATURE citations that fail the locate-the-number bar** (P2.0c;
  the bar: document + table/section/page — "TS-6" alone is insufficient).
  Labels carried as LITERATURE with the gap recorded, not guessed closed and
  not downgraded: the four `ts6_finding` strings in
  [covariates.yaml](../docs/contracts/covariates.yaml) (candidate entries;
  each now says "table/page NOT LOCATED"); depth's `geology_note` 4,100–4,200 m
  claim (:71); the TS-6 anchors quoted in
  [scenarios.yaml](../data/economics/scenarios.yaml) comments (baseline
  grades, abundance distribution). Owner: Karl (as G — locate in TS-6;
  fires before G.0-5's first cited value).
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
- [ ] **Classify the two context sources under the origin taxonomy —
  BATHYMETRY HALF DECIDED at G.3 (2026-08-24): DERIVED**, by GEBCO's own
  "information product" wording (neither of this entry's two candidate
  labels; the row's comment carries the reasoning, the terms PDF is tracked
  as the evidence). The Checkpoint-1 watermark will derive from DERIVED.
  **The `src_deepdata_public_context` half stays OPEN** (G.0-1's riding
  decision — the MEASURED-not-LITERATURE question for a hashed download
  from an authoritative publisher). **NARROWED at G.2 (2026-08-25): that
  question is now ANSWERED for the CCZ management area — LITERATURE, on a new
  row `src_ccz_boundary_marineregions`, because the artifact is a boundary
  DECREED in ISBA instruments with no measurement in its lineage.
  `src_deepdata_public_context` was deliberately NOT repurposed for it: that
  row is ISA DeepData (the APEI / contract polygons), a different publisher
  under a different licence, and merging them would have left the APEI source
  with no row at all. So what stays open here is the APEI half only.**
  *(original entry)*
  `src_bathymetry_primary` (GEBCO-class bathymetry: MEASURED survey product
  vs LITERATURE compiled grid — it interpolates between soundings) and
  `src_deepdata_public_context` (published regulatory polygons). Both carry
  `data_origin: null` in
  [source_queue.yaml](../data/sources/source_queue.yaml) with `[KARL]`
  comments; the bathymetry decision drives Checkpoint-1 watermark derivation
  (P2.0d derives the watermark from the DEM's declared origin). Owner: Karl
  (+ G). Trigger: at download / before Checkpoint 1. Detail: walkthrough
  P2.0.md §c; [G.3.md](walkthroughs/G.3.md) §1.
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
- [x] **GEBCO is not uniformly MEASURED — CLOSED at G.3 (2026-08-24), all
  three asks done:** RECORDED (the TID grid delivered and hashed beside the
  bathymetry, its own DERIVED declaration); ASSESSED
  (`data/bathymetry/tid_accounting.json`: study extent 45.131% direct /
  54.869% predicted over a strongly bimodal survey-block field, per-row
  distribution shipped, swath-edge adjacencies counted); DECIDED (the
  file-level class is DERIVED — the per-cell distinction lives in the
  accounting artifact, machine-readable for the honesty surface; and **no
  training-matrix TID mask is needed for the current corpus** — all 35
  training stations, both clusters, sit on TID 11 multibeam, so nothing
  mixes predicted and sounded cells in the matrix; the 54.9%-predicted
  caveat belongs to the SURFACES and rides the artifact). *(original
  entry)* **the classification may be
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
  loader (`model_config.py`) refuses a value outside its admissible set —
  **regardless of origin; corrected at the E2.5 approval, which found this
  sentence describing the admissible-set check as an AUTHORED refusal, the
  same conflation the E2.5 prompt's inventory made one level up** — and
  `acceptance_thresholds` HAS A SLOT as of C8.1 (2026-08-20,
  `model_config_version` 2) — it had none when this entry was written, and
  the loader now refuses an AUTHORED gate outright, so Track E STILL cannot
  pre-register one: the slot is Track G's to fill, with a citation.

  **THIS ENTRY STAYS OPEN — confirmed at the C8.1 approval (2026-08-20).**
  A SLOT IS NOT A THRESHOLD. C8.1 built the place a gate goes and the refusals
  that keep a bad one out; it did not create a gate, and it could not have.
  The admissible origins are LITERATURE, MEASURED and DERIVED: LITERATURE
  needs a citation that LOCATES the number, MEASURED needs a file and its
  hash — neither is Track E's to produce. DERIVED is the one Track E could
  technically declare, by computing a threshold from data; but a gate derived
  from the very scores it grades is post-hoc BY CONSTRUCTION, so the taxonomy
  permits it while the clock below forbids it. That is the pairing that makes
  this entry load-bearing rather than redundant with the loader. **The post-hoc caveat above
  is now PERMANENT for this dataset**: E2.4's scores are committed and dated,
  so no threshold set from here is pre-registered for these numbers, in the
  full sense for kriging and weakly for RF. Closing this entry would require a
  threshold that predates the scores, which no future work can produce.

  That design is correct; the SEQUENCING must
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
    ~~Contract 8's loader refusing AUTHORED thresholds~~, E2.4's
    `scores_first_visible`, the pre-registration verdict ("no
    pre-registered gate existed when these scores were computed").
    **CORRECTED AT C8.1 (2026-08-20): the struck clause was FALSE when
    written** — stated 2026-08-14, committed 2026-08-18 (`009835e`), one day
    before E2.5. No such refusal existed, and
    no `acceptance_thresholds` slot existed either — P2.A had deliberately
    deferred both. THIS LINE IS THE SOURCE of the correction-drift instance
    the E2.5 approval recorded at "a task prompt's premises": the E2.5
    prompt did not invent the claim, it INHERITED it from here. The
    approval's correction pass over this very entry fixed a different
    sentence (the admissible-set conflation, above) and left this one
    standing — **the fix landed in the right entry, on the wrong
    sentence.** C8.1 built the refusal, so the clause is now true; it is
    struck rather than silently updated, because a premise that was false
    for five days is a fact about how this repo fails, and quietly making
    it accurate would delete the evidence. If E2.5
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
*(P2.C — the doc-consistency batch — moved to §3's* **Phase-2 closeout
batch** *at the E2.5 approval, 2026-08-19. It is not a §2 box any more;
its two `[KARL — DECIDE]` sub-items are called out in the batch header.)*

- [ ] **Uncited literature-shaped numbers in the contracts README.** The
  100 kg/m² ceiling rationale asserts "published CCZ abundances run
  ~1.5–30 kg/m²" and "~2 g/cm³ wet bulk density" with no citation —
  LITERATURE if cited, AUTHORED as written (origin-audit §4). Decide:
  supply citations (with G) or explicitly mark them authored engineering
  rationale. Owner: Karl (+ G for sources). Trigger: any time before a
  published run. Detail:
  [2026-08-08-origin-vocabulary-audit.md](audits/2026-08-08-origin-vocabulary-audit.md)
  §4; [docs/contracts/README.md:24](../docs/contracts/README.md#L24)–37.

- [x] **`RunManifest.content_hash` COVERS THE SHAPE: adding a field re-hashes
  every committed run manifest — decide the policy** — **DECIDED at the E3.4
  approval (Karl, 2026-08-22): SHAPE-TOLERANT. The task is in §3 ("the hash
  scheme becomes shape-tolerant"), with the reasoning, the losing argument,
  what it does not fix, and the trigger.** *(original entry)* (found at E3.4 commit 1,
  2026-08-22, the moment the four new fields turned
  `test_the_committed_artifact_hash_verifies_against_its_own_contents` red).
  `substance()` is `model_dump()` minus the excluded names, defaults
  included, so a new `None`-defaulted field changes the canonical JSON of an
  artifact emitted before the field existed. **What E3.4 did:** RE-STAMPED
  `data/runs/e2.4/run_manifest.json` mechanically — reloaded under the new
  shape, `finalize()`d, written back: four `null` lines and
  `content_hash sha256:7f6c7fae… → sha256:e3ac1561…`, every other byte
  identical (the commit shows exactly that; `generated_at`,
  `scores_first_visible` and the path-dependent upstream hashes untouched,
  which a regeneration would have moved). The artifact test's docstring
  records it. **What needs Karl's word:** whether that is the standing
  policy (each shape change re-stamps committed artifacts, diff on record)
  or whether the hash scheme should become shape-tolerant (e.g. hash only
  fields that are set, or version the shape) — the second changes the
  semantics of every artifact's hash and was NOT made unilaterally.
  **BOTH COSTS, recorded (E3.4 prompt §6):** re-stamping means a PROVENANCE
  RECORD THAT CHANGES AFTER THE FACT — in tension with what the chain is
  for, and survivable only because the commit shows the diff is the shape's;
  shape-tolerant hashing means TWO MANIFESTS WITH DIFFERENT SHAPES CAN HASH
  IDENTICALLY, so the hash stops identifying the schema and a reader can no
  longer tell from the hash which fields a record was able to carry. The
  path-hash fix (§3) will force the same choice again, so it should be
  decided BEFORE then rather than under it. Owner: Karl.
  **Trigger: before the path-hash fix, or the next RunManifest field.**
  Detail: [E3.4.md](walkthroughs/E3.4.md) §1; `domain/results.py` docstring.

## 3. Engineering (Track E)

- [ ] **ANY process that mutates the tree — reviewer, harness, or the session
  itself — takes a verified copy first and restores by `cp`** (E2.2 §2 review
  INCIDENT 2026-08-14; **WIDENED at the E2.4 audit, row N, 2026-08-19, after a
  SECOND incident of the same shape**). The rule used to bind "review
  workflows"; both incidents were mutating processes with broken restores and
  the second was **the session's own mutation harness**, which the old scoping
  did not reach.

  **THE RULE, in four steps — (b) is the one whose absence caused the second
  incident:**
  1. **(a) Take a copy before the first write.**
  2. **(b) VERIFY THE COPY EXISTS AND MATCHES before mutating anything.** A
     backup command that fails silently leaves you mutating with no undo, and
     you will not find out until the restore is a no-op.
  3. **(c) Restore by `cp`, never `git checkout`** — `git checkout` is not undo
     against a file git does not hold, and it is not undo against uncommitted
     work at all. (If the work IS committed first — the layer-(a) discipline
     below — `git checkout` becomes safe, and that is the better setup.)
  4. **(d) `cmp`-verify the restore**, and confirm the tree is clean.
  A fifth step earned at E2.4: **verify the mutation actually CHANGED the
  file** — a no-op edit makes the probe pass vacuously, which is
  indistinguishable from a guard working.

  **INCIDENT 1 (E2.2 §2, 2026-08-14) — a reviewer.** `review:math` ran
  `git checkout -- engine/prospectivity/estimators/variogram.py` to undo its own
  mutation probe, forgetting the file's baseline was UNCOMMITTED; this reverted
  the file to the committed report-only version and destroyed the uncommitted
  fitter (~178 lines), which it then rewrote from its session-start read. What
  verification COULD establish: the restoration is byte-identical (sha256
  `ed6c9ee7…`) to a `cp` backup an independent reviewer (`review:fixtures`) had
  taken BEFORE any mutation, and the suite and the real-corpus fit reproduce to
  16 digits. What it could NOT: no committed object existed to diff against.
  Recovered by RECONSTRUCTION, not from a verified backup.

  **INCIDENT 2 (E2.4 §2, 2026-08-19) — the session's own harness.** The
  mutation loop was written `for f in $FILES` with `FILES` an unquoted scalar;
  **zsh does not word-split it**, so `cp` never made a single backup, `restore`
  was a no-op, and all 16 mutations ACCUMULATED in the tree. Detected only
  because the suite went red and stayed red. Recovered by hand-inverting all 16
  string replacements, confirming the suite returned to its exact prior count,
  and re-running the batch against a committed baseline. Again
  RECONSTRUCTION, not restoration — and this time no independent copy existed
  at all.

  **The discipline exists; it just was not written down as binding.** E2.4's
  AUDIT harness did it correctly and is the worked example: it cloned the repo
  at HEAD into a scratch directory and ran every mutation there (so no audit
  write could touch the tree the read-only lenses were reading), and its helper
  refused to proceed unless the backup existed and was byte-identical, refused
  a no-op mutation, and `cmp`-verified every restore with a final
  `git status --short` check. `E2.3-2` and `E2.4 §2` also satisfied the
  layer-(a) discipline (WIP commit `efc683a` / `ff2d0c6` before the review
  launched, reviewers left the tree clean and said so).

  **Two layers, both still binding, now for any mutating process:**
  **(a)** commit or stash before an adversarial review or a mutation batch
  launches, or point it at a worktree or a clone — with a committed baseline,
  `git checkout` restore is safe and is the preferred setup;
  **(b)** absent that, the four steps above, with the verify-the-copy step
  treated as the load-bearing one.
  Both go into every future review AND harness prompt verbatim. Owner: Karl + E.
  Trigger: **before the next adversarial review OR mutation batch runs** — this
  entry has now been triggered twice and widened once; a third instance means
  the rule is being written down but not read. Detail:
  [E2.2.md](walkthroughs/E2.2.md) §2 "Review incident";
  [E2.4.md](walkthroughs/E2.4.md) §2 (the harness incident, recorded in the
  review record);
  [2026-08-19-e2.4-implementation-audit.md](audits/2026-08-19-e2.4-implementation-audit.md)
  row N.

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
- [x] **Dependency versions into the provenance manifest.** The manifest
  claims to pin everything about a run; the dependency lock hash should sit
  alongside contract versions. Owner: E. Trigger: Phase-3 manifest emitter.
  Detail: review discussion 2026-07-29; `engine.py` `RunManifest`.
  **DONE at E3.4 commit 3 (2026-08-22) — the trigger fired when E3.4 built
  the emitter and was found by reading this file AFTER commit 2, not
  before: `provenance/environment.py: run_environment()` records the
  lockfile's sha256 (recomputed from the committed file), the interpreter,
  the approved stack's INSTALLED versions (read from `importlib.metadata`,
  never from the lock) and GDAL's, under `inputs.environment` in EVERY run
  manifest (`emit_run_manifest`), INSIDE the content hash because they are
  inputs. Consequence, stated: two machines with different installed
  versions now hash differently — which is right, and which means CI (Linux)
  and this laptop (the lock is macOS-arm64 only) will not share run hashes.**
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
  **E3.4 commit 3 (2026-08-22) took the RUN-LEVEL half:** the extended
  manifest's `provenance_chain.links.corpus.csv_sha256` is the CSV's bytes,
  recomputed from the file `corpus_path` names, so a hand-edit to the corpus
  changes the run record — and the link SAYS it agrees with nothing upstream
  yet. **Still open, as the own task it was declared to be:** the
  CorpusManifest-level pin (the shape change), so the chain traces to the
  bytes at the corpus stage rather than only at the run that consumed them.
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
- [x] **ADD Contract 8's `acceptance_thresholds` slot — DECIDED by Karl at the
  E2.5 approval (2026-08-19); DONE at C8.1 the NEXT day (2026-08-20).** Landed exactly as
  decided: `value: null`, no `data_origin`, `[GEOLOGY — ISAAC]`,
  `model_config_version` **1 → 2** with the contracts-README note. The loader
  got both refusals P2.A specified (a value with no origin; an AUTHORED gate
  — widened to "less real than LITERATURE", derived from the taxonomy's own
  realness order rather than hand-listed), and the guard's verdict on today's
  data is UNCHANGED: same passing set, same failing set, `eligible False` —
  only the route moved from ABSENT to NULL. Detail:
  [C8.1.md](walkthroughs/C8.1.md). **What it does NOT close: the
  pre-registration entry in §2** — a slot is not a threshold, and the
  post-hoc caveat below is now permanent for this dataset.
  The original decision, for the record: Shape, as decided: the
  field arrives with `value: null`, **no `data_origin` — because there is no
  value to classify** (the deliberate contrast with `target_definition`, whose
  provisional `AUTHORED` / `author: model` origin IS its marker per P2.A);
  tagged `[GEOLOGY — ISAAC]` for task routing; `model_config_version` **1 → 2**
  with the contracts-README note, since adding a field is a structural change.
  (The approving prompt called this "the TYPE 2 slot P2.A specified"; that
  label is not a term this repo carries — P2.A draws the distinction without
  naming it — so the shape is recorded here and the label is not.)

  **Rationale, on the record:** the guard's REFUSAL is identical whether the
  field is absent or explicitly null — E2.5 verified both paths — so this is
  not about the refusal. **The contract is Track G's INTERFACE, and a slot
  that does not exist cannot be filled by the person whose job it is to fill
  it.** P2.A deferred the field on the rule that "a field with no consumer is
  a field nobody has tested the meaning of"; E2.5 built the consumer
  (`model_config.acceptance_thresholds` + `validation/claim.py` precondition
  6), so the condition P2.A set is now met.

  **The loader work this needs** — what P2.A specified and the E2.5 prompt's
  inventory wrongly assumed was already built: **"null, awaiting
  classification" and "classified" are DIFFERENT STATES**, and the accessor
  must keep them apart (it already does — absent, null and populated are three
  distinct refusals). And **an AUTHORED acceptance threshold is REJECTED
  OUTRIGHT rather than recorded** — a threshold Track E invented is Track E
  grading its own work. E2.5's guard already refuses it; the contract must not
  offer AUTHORED as an admissible origin for this field.

  **E2.5's guard needs no change beyond reading the slot** — the accessor and
  precondition 6 are written against exactly this shape.

  **The post-hoc caveat that rides with it:** E2.4's scores are already
  visible, so any threshold VALUE set from now on is post-hoc for this
  dataset, permanently — and for kriging in the full sense (real coordinates,
  real y). The honest path is a threshold cited from the literature or
  derived, never chosen after looking. Owner: E (the slot + loader) + Karl
  (the structural bump). **Trigger: the next task.** Detail:
  [E2.5.md](walkthroughs/E2.5.md) §0 and §2;
  [P2.B-and-P2.A.md](walkthroughs/P2.B-and-P2.A.md) ("One field,
  deliberately"); `data/config/model_config.yaml` header; §2's
  pre-registration-clock entry above.

- [ ] **Two C8.1 date labels in `data/config/model_config.yaml` still read
  2026-08-19; C8.1 committed 2026-08-20** (`58ca461`). Lines 18 (the
  version-history block) and 81 (the `acceptance_thresholds` comment).
  Comment-only, no structural change and no version bump. **Deferred rather
  than fixed at the P2.CLOSE approval only because that commit was fenced to
  docs/CLAUDE.md/BACKLOG** — every other site was corrected there. Owner: E.
  **Trigger: the next commit that touches `model_config.yaml` for any
  reason.** Detail: [C8.1.md](walkthroughs/C8.1.md) (its own §0 documents the
  stated-vs-committed distinction this violates).
- [ ] **REVISIT COG AT CHECKPOINT 1 — the format is inert at today's grid, and
  nothing installed can validate it** (decided by Karl at the E3.0 approval,
  2026-08-20; **no dependency added, and none needed to WRITE**).
  **What was measured, not assumed:** GDAL **3.9.2** / rasterio **1.4.1**, COG
  driver **present**. Probed both ways — at 2048×2048 the driver produces
  `tiled=True`, 512×512 blocks, overviews `[2, 4]`; **at the actual 100×34
  grid it produces `tiled=True`, overviews `[]`, an 18.5 KiB file over a 13.3
  KiB payload** — smaller than ONE 512×512 float32 block (1 MiB). Range
  requests and overviews, the entire point of the format, are inert at that
  size.
  **And nothing installed can validate COG-ness:** `rio_cogeo`, `osgeo.gdal`
  and `validate_cloud_optimized_geotiff` are all unimportable. rasterio can
  observe driver, `tiled`, `block_shapes`, `overviews()`, CRS, transform,
  dtype and nodata — it CANNOT observe the IFD/byte-layout ordering that
  actually makes a GeoTIFF cloud-optimized. **A native test would verify the
  STRUCTURE without verifying the PROPERTY, so claiming COG-ness would be a
  claim with a partial observer** — which is why E3.1+2 writes with the COG
  driver, asserts only the observable fields, and **claims no COG-ness in the
  manifest or the tags.**
  **What is deferred, and why it needs Checkpoint 1 specifically:** a global
  GEBCO grid makes the format mean something (overviews generate, tiles get
  fetched), and `rio-cogeo`'s evidence — maintenance state, transitive deps,
  license, lockfile delta — can be gathered **with network access**, which
  this session did not have. It is NOT in `requirements.lock` today (45
  lines, 0 matches). Owner: E + Karl (a dependency is Karl's call).
  **Trigger: Checkpoint 1**, or the first time a surface exceeds one 512×512
  block. Detail:
  [PHASE3-track-E-prompts.md](prompts/PHASE3-track-E-prompts.md) (E3.0
  approval block; E3.1+2 commit 1).

- [x] **E3.3 REPORTS r WITH N_eff AND NO p-VALUE — DONE at E3.3 commit 2
  (2026-08-22, `1febedc`).** The reasoning IS in the output: `INFLATION_NOTE`
  travels in every agreement and a test asserts it verbatim; the
  interpretation string carries the "NOT distinguishable from zero" reading,
  which today's kriging-vs-fixture comparison emits (r = +0.026 inside the
  noise scale). N_eff is Clifford–Richardson-style over binned empirical
  correlograms, with the two-sided known-answer (smooth pair < N/10,
  white-noise pair > N/2). **One nuance the entry's N_eff ≈ 2 expectation did
  not carry:** against today's WHITE-NOISE fixture the formula honestly
  reports n_eff ≈ N — the collapse needs BOTH surfaces smooth, which is the
  real-TS-6 case ([E3.3.md](walkthroughs/E3.3.md) §2). *(original entry)*
  A correlation between two spatially autocorrelated surfaces is inflated
  because the effective number of independent observations is far below the
  cell count. On the common grid that is **3,400 cells carrying df ≈ 3,398**,
  which is fiction. A geometric bound gives **N_eff ≈ 278** if the surface
  varied everywhere; it does not — **kriging is constant over 99% of the
  domain and the ~34 signal-carrying cells fall in TWO clusters, so N_eff ≈
  2.** For RF, N_eff is bounded by its handful of plateaus.
  **The decision:** descriptive r, N_eff printed beside it, **no p-value** —
  at N_eff ≈ 2 no significance test is meaningful, and a corrected test would
  turn p < 0.001 into p ≈ 0.6, which is more honest inference over the same
  emptiness.
  **THE LIMIT, which must travel with the number: a correction adjusts
  DEGREES OF FREEDOM; IT CANNOT MANUFACTURE INFORMATION.** The real problem is
  that one surface is constant over 99% of its own domain, and no test
  corrects for that.
  **Tooling, verified rather than assumed:** Clifford–Richardson (1989) and
  Dutilleul (1993) are the standard corrections and both are hand-implementable
  over numpy (the lag structure over 3,400 cells is 5.8M pairs — seconds).
  `scipy` **1.17.1** is importable but arrives TRANSITIVELY via scikit-learn
  and is **not a declared dependency** — using it directly needs a
  `pyproject.toml` entry. `statsmodels`, `esda`, `libpysal`, `pysal`: **not
  installed**. Owner: E. **Trigger: E3.3 commit 2** (implement a correction
  only if a test is ever demanded). Detail:
  [PHASE3-track-E-prompts.md](prompts/PHASE3-track-E-prompts.md) E3.3.

- [ ] **Two E3.1+2 date labels in `engine/prospectivity/surfaces/` still read
  2026-08-20; the commits landed 2026-08-21** (`abd7516`…`8d81986`).
  `grid.py:23` (the extent correction) and `writer.py:29` (the per-surface
  limit note). Comment/docstring only, no behaviour. **Deferred rather than
  fixed at the E3.1+2 approval only because that commit was fenced to
  CLAUDE.md and docs/** — the 13 doc-side labels were corrected there.
  **This is the same residue the P2.CLOSE approval left in
  `model_config.yaml`, and the THIRD occurrence of the stated-vs-landed gap
  overall.** Owner: E. **Trigger: the next commit that touches either file** —
  which is the taxonomy commit above, since it edits the sidecar's evidence.
  Detail: [E3.1-2.md](walkthroughs/E3.1-2.md).

- [x] **WIDEN SYNTHETIC'S EVIDENCE RULE — DONE at TAX.1 (2026-08-21,
  `5d97735`), and the `.tif` gap closed with it (`c6938a0`).** Two commits,
  split because a taxonomy rule reviewed alongside its first consumer is not
  reviewable; commit 1 left the suite at 502, proving every existing SYNTHETIC
  declaration still passes and none that failed now passes. The loophole is
  closed at `MIN_DETERMINISM_BASIS_CHARS = 40` with its trade-off and its
  blind spot stated at the constant, and the bare-basis refusal is probed end
  to end against a staged output directory, not only in a unit test. 4/4 and
  5/5 mutations, each by name. Detail: [TAX.1.md](walkthroughs/TAX.1.md).
  *(original entry, for the record)*
  **The new rule:** SYNTHETIC requires *a generator import path, AND a seed OR
  a recorded determinism basis*, where "deterministic, no seed" is an
  admissible basis **when the generator is genuinely seedless**.

  **WHY THIS IS NOT A LOOSENING, recorded because it looks like one:** it
  replaces an UNSATISFIABLE requirement with a satisfiable one carrying the
  same information — what produced this artifact, and what makes it
  reproducible. **The current state is the proof.** A SYNTHETIC-by-inheritance
  surface has no seed when its estimator has none (ordinary kriging is
  deterministic and records none); the artifact exists; it does not satisfy
  the rule. **A rule that cannot be honestly satisfied is not a strict rule,
  it is an unenforceable one.** E3.1+2's writer returning `None` rather than
  fabricating a `0` was correct — a fabricated seed satisfies the check by
  LYING to it, which is the exact failure the taxonomy exists to prevent.

  **THE LOOPHOLE TO CLOSE IN THAT TASK:** a determinism basis with no content
  — a bare `"deterministic"` string — would be the new unenforceable rule.
  **The basis must name WHAT makes it deterministic** (e.g. "closed-form
  solve over a fixed variogram fit; no RNG in the path"), and the audit test
  is what must observe that.

  **SCOPE, all in the one commit:** `CLAUDE.md`'s evidence table (the
  data-origin section's SYNTHETIC bullet); `origin.py`'s requirement if it is
  encoded there; the resolver's SYNTHETIC check in
  `tests/test_data_origin_audit.py`; **and the audit test as the OBSERVER of
  the widened rule** — probe both directions, as C8.1 did.
  **RIDING WITH IT: the `.tif` classification gap.** The written rasters are
  UNCLASSIFIED (binary, no in-file marker; the audit does not treat an
  adjacent sidecar as one). Same commit, same trigger — the options are in
  the entry below.
  Owner: E + Karl (the taxonomy). **Trigger: BEFORE E3.3**, since E3.3 writes
  artifacts too and would otherwise inherit an unsatisfiable rule. Detail:
  [E3.1-2.md](walkthroughs/E3.1-2.md) §3.

- [x] **Surface OUTPUTS can now be committed under `data/` — DONE at TAX.1
  (2026-08-21, `c6938a0`).** Both halves closed: the rasters are classified by
  the audit's own `data_origin.yaml` `files:` mapping (an association the
  AUDIT resolves, not a naming convention), and the seed rule is widened so a
  SYNTHETIC-by-inheritance surface can evidence itself. **Two further gaps the
  end-to-end probe found and fixed:** the `.json` sidecar declared itself
  SYNTHETIC without carrying its own evidence, and `data_origin.yaml` was
  itself unclassified because sidecar exclusion was a per-path list — made
  generic. Probed both directions: zero unclassified / zero invalid with
  declarations, both rasters refused by name with a bare basis.
  *(original entry, for the record)* (found at E3.1+2 commit 3, 2026-08-21, by
  probing `test_data_origin_audit.py` against a staged output directory —
  the probe the task required, and it found a real defect plus two open
  questions).
  **What the probe measured.** The audit's walk is `git ls-files -- data
  tests/fixtures`, so outputs under `data/` ARE seen once tracked — the
  coverage boundary is not where it was assumed. Staged, it returned:
  * `SYNTHETIC without a generator import path` and `without a recorded seed`
    for the sidecar — **a real defect, FIXED in that commit**: the sidecar now
    carries `generator` and `seed`.
  * `ordinary_kriging_prediction.tif` / `_uncertainty.tif` **UNCLASSIFIED** —
    binary files carry no in-file marker and the audit does not treat an
    adjacent sidecar as one.
  * `SYNTHETIC without a recorded seed` STILL, for kriging specifically:
    `_seed_of` returns None because **ordinary kriging is deterministic and
    records no seed**, and the writer refuses to fabricate a 0 that would
    satisfy the audit while naming a seed nothing used.

  **THE OPEN QUESTION IS A TAXONOMY ONE, not a plumbing one.** SYNTHETIC's
  evidence rule ("the generator's import path AND seed(s)") was written for
  GENERATED FIXTURES. A prediction surface is SYNTHETIC BY INHERITANCE — it is
  synthetic because the DEM upstream is, not because a seeded generator
  produced it here — so the evidence that would actually locate its
  synthetic-ness is the DEM's generator and seed, which the writer does not
  hold (it holds the DEM's content hash). Options: (a) an exclusion entry for
  output directories, with the sidecar as the marker of record; (b) a marker
  convention that lets a sidecar classify its sibling rasters; (c) widen
  SYNTHETIC's evidence rule to admit an upstream hash for inherited
  synthetic-ness. **(c) is a taxonomy change and needs Karl.**
  **Nothing is broken today: E3.1+2 commits no outputs.** Owner: E + Karl.
  **Trigger: the first commit that writes a surface into `data/`** — which is
  E3.4 if it commits an example run, and Checkpoint 1 otherwise. Detail:
  [E3.1-2.md](walkthroughs/E3.1-2.md) §3.

- [ ] **E2.5's guard cannot produce a PER-ESTIMATOR verdict, and E3.1+2 asked
  it to** (found at E3.1+2 commit 3, 2026-08-21; the writer's signature was
  built to express it, so nothing is blocked today).
  `evaluate_claim` is keyed on `(RunManifest, design)`. **Four of its six
  preconditions** — paired-uncertainty, single-DEM, provenance-chain,
  pre-registered-threshold — are properties of the RUN; the remaining two are
  properties of a DESIGN. **None is a property of an ESTIMATOR**, so the guard
  cannot today return a verdict that differs between kriging's surface and
  RF's, even though their claim-relevant facts genuinely differ (RF depends on
  synthetic covariates; kriging is coordinate-only and its scores are real
  measurements).
  `write_surface` takes ONE VERDICT PER SURFACE so the shape is expressible
  the day the guard gains that granularity; a caller passing the same verdict
  to every surface is reporting the truth as the guard currently computes it.
  **THE QUESTION IS WHICH DIRECTION TO RESOLVE IT, and it is genuinely open
  both ways** (framing added at the E3.1+2 approval, 2026-08-21): either the
  guard's unit becomes `(run, design, estimator)` — an E2.5 structural change
  — **or the run-level verdict is CORRECT and the writer's signature is the
  thing that should narrow.** There is a real argument for the second: claim
  eligibility as E2.5 defines it is a property of the EVIDENCE BEHIND A RUN
  (was CV spatially blocked, does a threshold predate the scores), and none of
  those becomes true for kriging and false for RF. What genuinely differs
  between estimators is the WATERMARK — RF's synthetic-covariate dependence
  vs kriging's coordinate-only — and the watermark is already computed per
  surface, separately from eligibility. **So the honest default is that the
  guard is right and the writer is over-general**; the entry stays open
  because that is an argument, not a measurement. Karl's call. Owner: E +
  Karl. **Trigger: with the E3.3 type decision**, since they are the same
  shape of question. **E3.4's disposition (2026-08-22), which does NOT
  close this:** the engine takes a REQUIRED `claim_design` (the caller's
  declaration, recorded in the manifest), evaluates the guard for EVERY
  design, records all of them as data (`claim.verdicts`), and hands the
  writer the declared design's verdict for every surface — the run-level
  reading in practice, with the writer's per-surface signature left as
  built. The arity question this entry was tied to is closed (below).
  **DECIDED at the E3.4 approval (Karl, 2026-08-22): THE GUARD IS RIGHT;
  NARROW THE WRITER'S SIGNATURE.** The argument is the session's own from
  E3.1+2, recorded in those terms: eligibility as E2.5 defines it is a
  property of the EVIDENCE BEHIND A RUN, and none of its six preconditions
  becomes true for kriging and false for RF; what genuinely differs per
  estimator is the WATERMARK, already computed per surface. A per-surface
  verdict parameter invites a distinction the guard cannot produce.
  **The task:** `write_surface` takes the RUN's verdict (one per run, not
  one per surface) — and the narrowing MUST PRESERVE the engine's property
  that it never picks: `ProspectivityEngine` keeps `claim_design` as a
  REQUIRED argument and hands the writer `verdicts[claim_design]`; a
  narrowing that defaulted the design or let the writer choose would
  quietly return the choice to the caller, which is the thing the argument
  refuses (`tests/test_engine_run.py::…declared_claim_designs_verdict…` is
  the separating test and must stay green). Owner: E. **Trigger: the next
  edit to `surfaces/writer.py`, or with the shape-tolerant hash task — the
  same commit series.** Not built at the approval (docs-only).
  Detail: [E3.1-2.md](walkthroughs/E3.1-2.md) §3;
  `engine/prospectivity/surfaces/writer.py` module docstring.

- [x] **`compare_to_ts6`'s type is UNDECIDED, and the two candidate answers
  pull apart** (E3.1+2 commit 1, 2026-08-21 — **reported rather than picked,
  per the task's own instruction**). **CLOSED at E3.4 commit 1 (2026-08-22,
  `31dc10b`): `RunManifest.ts6_agreement` IS the mapping** — one
  self-identifying agreement per estimator, `None` meaning "the comparison
  step did not run" (what the E2.4 CV-only artifact records). Built under the
  2B protocol (before/after in `results.py`'s docstring; sweep: `engine.py`,
  the template-method stub, `reference.py`'s Phase-0 `compare_to_ts6` stub
  RETIRED at commit 2). Detail: [E3.4.md](walkthroughs/E3.4.md) §1.
  The prompt offered two reconciliations: `PredictionSurface` gains a
  constructor from the per-estimator `(mu, sd)` dict, or `_compare_to_ts6`'s
  signature changes to take what `run()` holds. The constraint it named is
  that shipping a type which cannot express "all of them" would force E3.3's
  "which estimator" answer by accident. **A THIRD constraint decides it and
  was not named: the MANIFEST'S ARITY.** `RunManifest.ts6_agreement` is
  singular (`TS6Agreement | None`), and `TS6Agreement` is `extra="forbid"`
  with **no estimator field** — it cannot even self-identify which surface it
  describes. So a mapping cannot be recorded without a Phase-0 shape change
  (the 2B revision protocol), and a single agreement forces the choice.
  **What E3.1+2 did instead:** left `compare_to_ts6` untouched (still
  `NotImplementedError`) and had the builder return a MAPPING, which expresses
  "all of them" without deciding which.
  **E3.3's HALF IS DONE (2026-08-22, `1febedc`):** `compare_all_to_ts6`
  returns one agreement PER ESTIMATOR, each self-identifying via the new
  `TS6Agreement.estimator_name` — so both manifest answers stay expressible —
  and `reference.py`'s stub now names THIS entry instead of claiming E3.3
  would implement the wiring.
  **THE ARITY IS DECIDED — Karl, E3.3 approval (2026-08-22):
  `ts6_agreement` BECOMES A MAPPING** (one agreement per estimator, keyed by
  name). The reasoning, recorded against the tempting alternative: collapsing
  to a single agreement would force a "which estimator IS the comparison"
  answer nobody has argued for, and the three genuinely differ — kriging's
  surface is near-constant, RF's is blocky and ceiling-bound, the baseline's
  is flat by construction; one number would silently privilege one of them.
  **E3.4 BUILDS IT under the 2B Phase-0 revision protocol** — before/after
  shapes and the stale-reference sweep, the CVScore precedent. Owner: E.
  **Trigger: E3.4's manifest extension.** Detail: [E3.3.md](walkthroughs/E3.3.md);
  [E3.1-2.md](walkthroughs/E3.1-2.md) §4.

- [x] **E3.3 CARRIES THE DIGITIZATION ERROR — Track E's half DONE at E3.3
  commit 2 (2026-08-22, `1febedc`).** The comparison reads the value through a
  three-state accessor, REFUSES the real (non-SYNTHETIC) path by name when it
  is missing — which is the OBSERVER for the requirement — reports "not
  applicable — synthetic fixture" on the fixture path rather than assuming
  zero, and carries the value into `benchmark_uncertainty(_note)` when
  supplied. **The residue is not E's:** the value is Track G's (G3.1), and the
  SLOT does not exist in Contract 6 yet — see the new §2 entry below, because
  a premise check found ABSENT where the prompt said null. *(original
  entry)*
  E3.3 compares our surface to a raster **we produced by eye from a printed
  map**. A comparison that treats the benchmark as EXACT overstates its own
  precision — and it would do so in the same breath as reporting an r whose
  N_eff is ~2 (the other E3.3 decision). The digitization error is a value the
  comparison should carry, not a caveat in prose.
  **This is not buildable today** and that is the point of recording it now:
  the raster does not exist (`data/ts6/` holds only the contract), and the
  error is a property of the digitization Track G has not yet performed.
  **What E3.3 must do:** read the error where Track G records it, propagate it
  into the agreement report, and — if it is absent — say so rather than
  assuming zero. Owner: E (the propagation) + G (the value). **Trigger: E3.3
  commit 2**, with the correlation posture. Detail: Contract 6's
  `raster_data_origin` comment; [E3.1-2.md](walkthroughs/E3.1-2.md).

- [x] **ADD Contract 6's `digitization_uncertainty` SLOT — a structural
  contract change, Karl's call** — **DONE at the E3.3 approval (2026-08-22,
  `4834e31`, `reference_version` 3 → 4, `digitization_uncertainty: null`,
  `[GEOLOGY — ISAAC]`, additive). Checked off at E3.4 (2026-08-22): the
  commit that closed it did not tick this box — the first repo-vs-repo
  disagreement the E3.4 premise check found, and the deferral rule's
  "closing = checking it off in the commit that closed it" applied one
  commit late. The VALUE is still G3.1's.** *(original entry)* (found at E3.3
  commit 2, 2026-08-22, by a premise check: the task prompt said the field "is null today" and it does
  not EXIST — absent, not null, and this project treats those as different
  states with different remedies).
  **The consumer already exists** (`ts6.comparison.ts6_digitization_uncertainty`,
  the C8.1 loader posture: absent raises naming the STRUCTURAL gap, null
  raises naming the unfilled VALUE, present returns), so P2.A's
  "a field with no consumer is a field nobody has tested the meaning of"
  condition is met — the same sequence as `acceptance_thresholds`:
  E2.5 built the consumer, C8.1 added the slot.
  **Shape when added:** `digitization_uncertainty: null` (kg/m²; no value
  until something is digitized), `[GEOLOGY — ISAAC]`, `reference_version`
  3 → 4 with the contracts-README note; additive, so Track G's re-sync is a
  read. Owner: E + Karl (the bump). **Trigger: with E3.4, or before Track G
  digitizes — whichever comes first.** Detail:
  [E3.3.md](walkthroughs/E3.3.md) §2.

- [ ] **`digitization_method` is now DERIVED's EVIDENCE, and a one-word answer
  will not satisfy it** (TAX.1 approval, 2026-08-22 — committed `9a7ecac`).
  DERIVED's evidence requirement is a derivation formula or the artifact
  recording it. For the TS-6 raster that is `digitization_method`, whose
  current state is **null** with a three-option comment
  ("georeferenced raster scan" | "table interpolation" | "contour
  vectorization"). **Those are a vocabulary, not an answer.** To evidence a
  DERIVED claim the field must be specific enough to RE-RUN: which figure,
  which edition, what georeferencing, what value-extraction procedure, what
  contour or colour mapping was assumed.
  **The parallel is exact and worth stating**: TAX.1 refused a bare
  "deterministic" as a SYNTHETIC determinism basis for the same reason — a
  field that names the CATEGORY rather than the MECHANISM evidences nothing.
  **PARTIALLY ANSWERED at E3.3 commit 2:** the COMPARISON now enforces the
  floor at run time (`MIN_DIGITIZATION_METHOD_CHARS = 40`, refusing Contract
  6's own three vocabulary options as category words). Whether the AUDIT
  should also enforce it — so an unspecific method fails the suite, not just
  the run — is the half still open. Owner: G (the value)
  + E + Karl (whether to enforce). **Trigger: when Track G delivers the
  raster** — which is Checkpoint 3. Detail: `data/ts6/ts6_reference.yaml`.

- [x] **LITERATURE's evidence requirement has NO OBSERVER — CLOSED at OBS.1
  (2026-08-26), AND IT CLOSED OVERDUE.** The fix was one negation fixture
  (`test_audit_reports_literature_declarations_missing_their_citation`),
  needing no data, no decision and no delivery — so it was buildable from the
  day it was found, 2026-08-20. Re-running the measurement that scored it:
  deleting the branch now fails **1 of 704**, was **0 of 703**. The fixture
  separates three neighbours (no citation key / whitespace citation /
  document+table+page), and the well-formed row is the discriminating one.
  **RECORDED BECAUSE AN ENTRY THAT CLOSES WITHOUT SAYING IT WAS LATE TEACHES
  NOTHING:** this entry's deadline ("before Track G supplies any cited value")
  LAPSED at G.3 on 2026-08-24 when the two GEBCO PDFs landed declared
  LITERATURE with citations, was missed at that approval, and was missed again
  during G.2 the next day — which shipped two MORE cited LITERATURE values
  against an unobserved check. It was found only at the G.2 approval, by
  re-measuring rather than by the trigger doing its job. **The cause is now a
  named defect class** (CLAUDE.md, *trigger mismatch*): the trigger watched an
  external Track-G delivery the remedy never needed, so the alarm was wired to
  the wrong door. **REPORTED, NOT FIXED:** the resolver does not distinguish an
  EMPTY citation from a MISSING one — both collapse into one finding text —
  now pinned as behaviour so changing it is deliberate. Detail:
  [OBS.1.md](walkthroughs/OBS.1.md). *(original entry)* — the one evidence
  check of five that nothing tests** (found at P2.CLOSE commit 4, 2026-08-20,
  by the sole-observer measurement; **not fixed there — that commit is
  docstrings-only by instruction**).
  **The measurement:** deleting the `LITERATURE without a citation` branch
  from the audit resolver (`tests/test_data_origin_audit.py:329–332`) fails
  **ZERO of 471 tests**. Its siblings each have exactly one observer —
  SYNTHETIC-without-generator 1, SYNTHETIC-without-seed 1,
  DERIVED-without-formula 1 — measured in the same run, so this is a gap in
  coverage and not an artifact of how the mutation was applied.

  **Why it matters more than a missing test usually would.** CLAUDE.md's
  data-origin section states that "all five evidence requirements are
  ENFORCED, which is checkable", and names the audit resolver as LITERATURE's
  enforcer. The check EXISTS and would fire — no tracked file currently
  declares LITERATURE without a citation, which is exactly why nothing
  noticed. **This is coverage-that-isn't at the level of the taxonomy's own
  enforcement**, and LITERATURE is the class Track G's contributions arrive
  as (Isaac's citation is the AUTHORED→LITERATURE promotion), so the check
  starts mattering the moment Track G delivers.

  **The consequence, stated because the fact alone understates it:**
  `CLAUDE.md`'s data-origin section tells every reader that all five evidence
  requirements are ENFORCED *and checkable*, and names this resolver as
  LITERATURE's enforcer. **The first real citation Isaac supplies would land
  against an unexercised check** — and the AUTHORED→LITERATURE promotion is
  exactly how Track G's work is designed to arrive (Contract 8's
  `target_definition`, `acceptance_thresholds`, and the `[18]` TS-6 values
  all promote this way). Nothing is currently wrong in the repo; the check
  would fire today. What is missing is any evidence that it still will after
  the next edit to the resolver.

  **QUALIFIED AT THE E3.0 APPROVAL (2026-08-21): NEITHER PHASE-3 DELIVERABLE'S
  ORIGIN CLASS IS SETTLED BY THE REPO**, so "both arrive as LITERATURE" is a
  premise this entry must not rest on.

  * **The AOI polygon** could be MEASURED (hashed DeepData polygons —
    `docs/contracts/README.md`'s Contract 2 row already contemplates them),
    DERIVED (computed from the corpus, which is the "sampled areas only"
    option), or LITERATURE (a cited published boundary). The class follows
    the option chosen, and the option is §1's open AOI decision.
  * **The TS-6 raster**: Contract 6 gives it fields matching ALL THREE
    evidence shapes at once and decides none — `content_hash: null "filled at
    ingestion"` (MEASURED's evidence), `digitization_method` (DERIVED's), and
    values that come from a publication (LITERATURE's).
    **DECIDING TS-6's CLASS IS A PREREQUISITE FOR E3.3, NOT A DISCOVERY
    DURING IT** — the comparison writes an origin into the manifest, and a
    class chosen while the number is being computed is chosen to suit it.

  **THE URGENCY SURVIVES THE QUALIFICATION, which is the point:** whichever
  way each lands, at least one Phase-3 arrival falls in LITERATURE — the ONLY
  class with no observer. DERIVED, the likeliest alternative for TS-6, HAS
  one (1 of 471). So the gap is not hypothetical for Phase 3; it is on the
  path.

  **RE-QUALIFIED AT E3.4 (2026-08-22): TS-6's class is now SETTLED — DERIVED
  (Contract 6 v3, TAX.1 approval, `9a7ecac`), the class WITH an observer. So
  "two Phase-3 arrivals riding on LITERATURE" (the E3.4 spec's closing list;
  the handoff) is STALE: ONE Phase-3 arrival — the AOI — can still land in
  LITERATURE, and it is not settled either way (§1). Isaac's target citation
  (Contract 8, AUTHORED→LITERATURE) remains the certain arrival. Trigger
  unchanged; the count is corrected rather than inflated.

  **The fix is one negation fixture**, in the shape the other two already
  use: a `data_origin: LITERATURE` node with no citation must appear in
  `findings.invalid`, and one with a locating citation must not. Owner: E.
  **Trigger: BEFORE TRACK G SUPPLIES ANY CITED VALUE** — which is sooner than
  Phase 3, since the AOI decision and Isaac's target citation both arrive as
  LITERATURE (confirmed at the P2.CLOSE approval, 2026-08-20; the earlier
  wording, "with the next Track G delivery", made the trigger contingent on a
  delivery rather than preceding it).

  **THE DEADLINE HAS EXPIRED, AND IT EXPIRED AT G.3 — one day before the
  arrival this entry predicted** (found at the G.2 approval, 2026-08-25, by
  measuring rather than assuming). The trigger says BEFORE, so it did not
  "fire at" a delivery: it lapsed the instant `eb3ef3b` (G.3, 2026-08-24)
  committed `data/bathymetry/data_origin.yaml` with the two GEBCO PDFs
  declared LITERATURE with locating citations — Track G's first cited values.
  G.2 then added two more (`data/aoi/study_area.geojson` and the preserved raw
  download), so the AOI arrived exactly as this entry foresaw. **It was missed
  at the G.3 approval and again during G.2.**

  **THE GAP ITSELF IS UNCHANGED, RE-MEASURED at the G.2 approval:** deleting
  the `LITERATURE without a citation` branch from
  `tests/test_data_origin_audit.py` still fails **ZERO of 703** tests (the
  P2.CLOSE measurement was 0 of 471). The reason is exactly why nothing
  noticed then and nothing notices now: **the branch fires only on a MISSING
  citation, and all five LITERATURE subjects in the repo HAVE one** —
  `normalization.yaml#screening` (since P2.0c, 2026-08-08, so LITERATURE did
  NOT get its first real member at G.2), the two GEBCO PDFs, and G.2's two.
  Adding well-formed members can never close this; only the negation fixture
  can. **And there is no G.1 task in this repo — the observer was not built
  there.** G.2 DID demonstrate the branch is live (stripping the AOI's
  citation made `..._carry_their_resolver_side_evidence` fail by name), but a
  probe run by hand is not an observer in the suite. Owner: E. **Trigger:
  OVERDUE — it lapsed 2026-08-24 and every further Track-G citation widens the
  gap.** Detail: [P2-closeout.md](walkthroughs/P2-closeout.md) commit 4;
  [G.2.md](walkthroughs/G.2.md).
- [x] **THE HASH SCHEME BECOMES SHAPE-TOLERANT** (DECIDED by Karl at the E3.4
  approval, 2026-08-22; **not built there — docs-only commit**). **BUILT at
  HASH.1 commit 1 (2026-08-22):** present fields + `schema_version` inside
  the substance for versioned artifacts; a LEGACY mode over a per-class
  FROZEN field set for artifacts that arrive with a `content_hash` and no
  `schema_version` — needed because a plain present-fields rule was
  MEASURED to move the E2.4 run manifest's hash (its re-stamp hashed five
  nulls) and `exclude_defaults` the corpus manifest's too. Both committed
  hashes unchanged and pinned by literal; new fields must default to None,
  refused at class definition otherwise. The historical set is 2, as
  counted here. Detail: [HASH.1.md](walkthroughs/HASH.1.md) §1;
  `provenance/artifact.py` module docstring. *(original entry)*
  **The question:** `ProvenanceArtifact.substance()` is `model_dump()` minus
  the excluded names, defaults included, so any new field re-hashes every
  committed instance of that artifact class. Re-stamp history on every
  addition, or make the hash shape-tolerant?
  **DECISION: shape-tolerant.** Hash over PRESENT fields (a field at its
  default is absent from the substance); record the schema version
  alongside, explicitly; leave historical manifests with their original
  hashes.
  **The reasoning, with the losing argument because it is real:**
  * Re-stamping means committed provenance CHANGES AFTER THE FACT — directly
    against what the chain exists to do — and it scales badly: every future
    field touches every historical artifact. E3.4 paid that cost once
    (`31dc10b`, six lines); the path-hash fix would charge it again.
  * The counterargument — two manifests with different SHAPES could hash
    identically, so the hash stops identifying the schema — is real but
    weaker: the shape is already recorded elsewhere in the artifact, and
    this hash's job is identifying SUBSTANCE, not schema. Recording the
    schema version alongside restores what is lost, explicitly rather than
    as a side effect of the hash.
  **What the decision does NOT fix, bounded and counted** (`git ls-files
  data`, verified at the approval rather than restated): artifacts written
  before a schema version exists cannot be distinguished from a
  differently-shaped one by hash alone. That set is **2 committed
  artifacts** — `data/runs/e2.4/run_manifest.json` and
  `data/corpus/manifest.json` — because `substance()` lives on the shared
  base, so the decision reaches all four artifact types, not only
  `RunManifest`. No feature-stack or training-matrix manifest is committed.
  **The E3.4 re-stamp of `data/runs/e2.4/run_manifest.json` STAYS as it is:**
  retroactively un-stamping would be the same after-the-fact edit this
  decision exists to stop.
  **What changes when it lands:** `tests/test_provenance_artifact.py`'s
  hash tests gain the "a defaulted field does not enter the substance" case
  and the "two shapes, same substance, same hash, DIFFERENT schema version"
  case; the E2.4 artifact test keeps its self-hash assertion (the file is
  unchanged; only future emissions differ). Owner: E. **Trigger: BEFORE the
  path-hash fix (§3 below), so that choice is not forced under time pressure
  by a fix that would otherwise re-stamp everything again.**
  Detail: [E3.4.md](walkthroughs/E3.4.md) §1 and §A; `domain/results.py`
  docstring ("the hash covers the shape").
- [ ] **`claim.py`'s runner-vs-record disagreement branch raises `NameError`,
  not `ClaimRefused`** (found at E3.4 while reading the guard before wiring
  it, 2026-08-22; **deferred, not fixed: E2.5's module, its own test**).
  `_check_spatially_blocked`'s SECOND refusal — "declares
  spatially_blocked=True but is absent from the manifest's
  claim_eligible_designs" — formats `manifest.claim_eligible_designs!r`
  (`validation/claim.py:195`) where only `inputs.manifest` is in scope
  (line 191 reads it correctly). The branch is reachable only when the
  runner and its own record disagree, which no run today produces, so it
  has NO OBSERVER and would surface as a `NameError` traceback instead of
  the named refusal it was written to give. **Fix:** `inputs.manifest`,
  plus a constructed manifest whose design declares `spatially_blocked=True`
  while `claim_eligible_designs` omits it (the `_eligible_run()` fixture
  with one field broken — the file's own convention). Owner: E. **Trigger:
  the next edit to `claim.py`, or before Checkpoint 3**, whichever first.
  Detail: [E3.4.md](walkthroughs/E3.4.md) §4.
- [ ] **A PASSING pre-registration gate will put a timestamp INSIDE the
  content hash** (found at E3.4 commit 1 while recording the verdict as
  data, 2026-08-22; latent — no gate passes today).
  `claim.verdicts.*.preconditions[].detail` is inside the substance hash.
  Five of the six checkers' success details are constants or run facts; the
  sixth — `_check_pre_registered_threshold` — renders
  `scores_first_visible.isoformat()` into its SUCCESS detail, and
  `scores_first_visible` is deliberately OUTSIDE the hash (the
  pre-registration clock). So the day Contract 8's `acceptance_thresholds`
  is filled and the gate passes, two emissions of one run with different
  clocks will hash differently — the property the exclusion exists to
  protect, lost through a string. Today every verdict FAILS that
  precondition with a clock-free message, which is why the reproduction
  tests are green. **Fix:** the detail names the comparison's OUTCOME, not
  the clock's value (the clock is already recorded beside it), or the
  emitter records `{precondition, passed}` and keeps `detail` out of the
  substance. Owner: E. **Trigger: with Contract 8's `acceptance_thresholds`
  VALUE (Track G / Karl) — before the first passing verdict is emitted.**
  Detail: [E3.4.md](walkthroughs/E3.4.md) §2.
- [ ] **The THEOREM test's numeric tolerances are seed-calibrated too — the
  same defect as the leakage pins, in the test next to them** (found at
  P2.CLOSE commit 1, 2026-08-20, by a premise check that swept the file's
  OTHER test; **not fixed there — outside that item's stated scope**, which
  named the leakage test's magnitude pins).
  `tests/test_cv_known_answer.py::test_across_the_synthetic_clusters_kriging_reverts_to_the_training_mean_the_theorem_on_the_fixture`
  asserts kriging ≈ baseline across the 50 km gap with three tolerances
  (per-fold RMSE within 5%, bias within 0.2, pooled within 2%). **Swept over
  seeds 1–8: all three hold fully at 2 of 8** (seeds 8 and 13); the
  structural assertion `range_km < 30.0` holds **8 of 8**.
  Worked example at seed 3, fold 0: kriging RMSE 3.5409 vs baseline 3.2365
  — **9.41%**, against a 5% tolerance, with a fitted range of 13.89 km.

  **The claim is sound; the TOLERANCE is what is calibrated to seed 13.** The
  theorem is asymptotic, not exact: with a fitted range R and a 50 km gap the
  far-field weights carry a residual ~exp(−50/R), which at R = 13.89 km is
  ~2.7% and not zero — so how tightly kriging matches the baseline depends on
  the seed's fitted range, and the current numbers were read off one draw.
  **CHECKED AND CLEARED, recorded so the next reader does not re-investigate
  it (P2.CLOSE, 2026-08-20):** the fitted range **22.07 km** recurs across
  seeds 1, 3, 4 and 13, in different folds — which looks exactly like a
  hardcoded fallback. It is not. It is the DECLARED
  `range_at_candidate_ceiling`, and the flag reads `True` at precisely those
  folds and `False` elsewhere (verified by printing both together). The
  estimator already says, in a field designed for it, that the range is
  unconstrained from above because it exceeds what the supported lags can
  resolve. Honest behaviour, correctly labelled — **do not spend a session on
  it again.**
  **Candidate fix, same shape as commit 1's:** assert what is structural
  (`range_km < 30`, 8/8; kriging strictly closer to the baseline than to a
  no-skill predictor) and report the tolerances. Owner: E.
  **Trigger: before the theorem is cited outside the walkthrough, or the next
  time this file is edited.** Detail:
  [P2-closeout.md](walkthroughs/P2-closeout.md) commit 1.
- [x] **The provenance chain's identity is NOT portable: the feature-stack
  manifest hashes the caller-supplied PATH STRING, so no downstream artifact
  hash can be verified anywhere but the machine that wrote it** — **FIXED at
  HASH.1 commit 2 (2026-08-22).** `DemGrid.provenance()` no longer carries
  the path (it was a location, never an identity — `content_hash` is the
  identity); `FeatureStackManifest.dem_path` records the string the caller
  passed, OUTSIDE the hash (schema_version 2). MEASURED after the fix: the
  same DEM bytes in another directory give the same stack hash, the same
  raster bytes, the same run `content_hash`, and **0 moving hash values
  (was 11)**; relative vs absolute in the same directory pinned too; two
  different DEMs still differ. The determinism test was REBUILT to vary the
  DEM PATH (the audit's row M(b) coverage-that-isn't is closed by the same
  change). The emitter ASSERTS the stack substance is path-free and refuses
  by name otherwise, records `path_dependent_hashes.count = 0` with
  `was: 11`, and names what REMAINS: native byte order in `matrix_sha256`
  (same-endianness hosts), raster bytes across GDAL versions unmeasured,
  and `inputs.environment` inside the run hash BY DESIGN. The two E3.4
  tests that were pinned to go red did, and were UPDATED (not deleted) to
  pin the measured zero. One thing the first draft got wrong and the
  measurement caught: echoing the stack's `dem_path` inside the run's
  chain block put the path back into the run hash one artifact
  downstream. Detail: [HASH.1.md](walkthroughs/HASH.1.md) §2.
  *(original entry)* (found at
  E2.4 §3 by the run manifest's own chain assertion; **SCOPED at the E2.4
  audit, row M, 2026-08-19** — this entry is the audit's version, not the
  original assumption, which said "absolute paths" and "a different machine"
  and understated both).

  **What is machine-dependent, exactly.** `FeatureStackManifest`'s substance
  carries the DEM's path string **nine times** — once at `dem.path` and once
  inside each of the eight `layers[i].dem.path`. Nothing else
  environment-derived enters any substance (no hostname, username, locale or
  timestamp; the two wall-clock fields are already excluded). The trigger is
  **wider than a different machine**: the manifest records whatever string the
  caller passed, so the SAME file in the SAME directory, passed relatively vs
  absolutely, yields two different `content_hash` values while
  `dem.content_hash` is identical and the rasters are byte-identical.

  **The test that claims the property cannot observe it.**
  `tests/test_covariate_stack.py::test_two_independent_builds_produce_identical_rasters_and_substance`
  builds both stacks from ONE `dem_path`, varying only the OUTPUT directory —
  i.e. it varies the axis the manifest does NOT record and holds fixed the one
  it DOES. Measured: same dem path + different output dir → hashes equal;
  different dem path → hashes differ. Its assertion is true and its docstring's
  claim ("two independent builds must produce the SAME hash") is broader than
  the fixture can see. **This is coverage-that-isn't sitting under
  PROVENANCE.md's most-cited invariant**, and it has passed since E1.4.

  **The blast radius, measured.** `FeatureStackManifest` →
  `TrainingMatrixManifest.upstream_hashes` → `RunManifest.upstream_hashes` and
  `content_hash`. Of the run manifest's three upstream hashes, only **`corpus`**
  is verifiable off-machine (`data/corpus/manifest.json` is committed and its
  hash matches); `feature_stack` and `training_matrix` are **not** — no stack or
  matrix artifact is committed to compare against, and recomputing gives
  different values. `matrix_sha256` (over the arrays) IS stable and reproduces;
  a latent second-order caveat is that `ndarray.tobytes()` uses NATIVE byte
  order, so `matrix_sha256` and `coords_fingerprint` are portable only across
  same-endianness hosts while `training_matrix.py`'s docstring says
  "Deterministic across machines" unqualified.

  **State it plainly: PROVENANCE.md claims a property the implementation does
  not deliver.** Its CONTENT HASH SCHEME says "same inputs and same decisions
  produce the same hash **on any machine, at any time**". Until this is fixed,
  an `upstream_hashes` reference proves origin **only on the machine that wrote
  it** — the chaining rule is locally checkable, not portably checkable.
  Measured consequence, already visible: the committed
  `data/runs/e2.4/run_manifest.json` reproduces byte-identically in all 15 of
  its SUBSTANCE fields from a different directory, and in neither of its
  identity fields.

  **THE BLAST RADIUS, RE-MEASURED AT E3.4 (2026-08-22): IT NOW REACHES 9 OF
  THE 10 OUTPUT FILES** — every raster (tags) and every provenance sidecar
  (`grid.identity()`); NOT `data_origin.yaml`, which quotes no hash. (The
  first statement of this, "every output file", was wrong by one and was
  corrected by MEASURING the two-directory diff: **11 distinct hash values
  move** — the stack hash, the matrix hash, nine files — and the manifest's
  `provenance_chain.path_dependent_hashes.count` now carries that number,
  computed at emission by testing each file's bytes for the stack hash.)
  Each written raster's tags and each provenance sidecar carry the stack
  hash (`grid_stack_content_hash`; `grid.identity()`), so the same
  SurfaceResult written against a stack built from the same DEM bytes at a
  different path is a DIFFERENT FILE (values identical — measured with
  `np.array_equal`; bytes not). At whole-run scale: the same DEM bytes in a
  different directory reproduce the scores, the fold record, every verdict,
  every agreement and every surface summary byte-for-byte, and differ in
  EXACTLY `upstream_hashes`, `prediction_grid`, `provenance_chain`,
  `output_hashes`, `surfaces` (the file hashes) and `content_hash` — pinned
  as an equality on the differing SET in
  `tests/test_engine_run.py::test_the_same_bytes_in_a_different_tree_…` and
  in `tests/test_run_manifest_extension.py::test_the_chain_limit_…`. Both
  tests pin the defect's PRESENCE deliberately: when the fix lands they go
  red and the manifest's `provenance_chain` claim (which today says only the
  corpus is verifiable off-machine) must change in the same commit. The
  limit is STATED IN THE EMITTER'S OUTPUT (`provenance/emitter.py:
  CHAIN_LIMIT_NOTE`), not only here.

  **Fix** (small in code, wide in consequence — it changes an E1.4 artifact's
  substance and every pinned hash, which is why E2.4 listed it rather than
  making it): record paths as basenames or repo-relative, or exclude them from
  the substance as `generated_at` is; then re-pin. The determinism test must be
  rebuilt to vary the DEM PATH, or it will keep passing either way. **Note the
  re-stamp precedent (E3.4): fixing this re-hashes the committed E2.4 artifact
  AGAIN (its `upstream_hashes` quote the stack), and the §2 entry on
  shape-rehashing decides how.**

  Owner: E. **Trigger: BEFORE CHECKPOINT 1** — real GEBCO arrives at a new path
  and every stack hash changes for a reason that has nothing to do with the
  terrain. **Separating "the DEM changed" from "the path changed" at that
  moment is the expensive version of this fix**, and it lands exactly when the
  hashes are supposed to be proving that the terrain is what changed. Detail:
  [2026-08-19-e2.4-implementation-audit.md](audits/2026-08-19-e2.4-implementation-audit.md)
  row M (a, b, c); [E2.4.md](walkthroughs/E2.4.md) §3 "what does and does not
  reproduce"; `features/stack.py` manifest assembly;
  [PROVENANCE.md](contracts/PROVENANCE.md) "CONTENT HASH SCHEME".
- [ ] **AUTHORED's EVIDENCE RULE CANNOT BE HONESTLY SATISFIED BY AN ARTIFACT
  DERIVED FROM AN AUTHORED VALUE — `author_inherited_from` is refused by
  the audit** (found at the E4.2 approval, 2026-08-22, by probing the
  resolver both directions on the writer's actual sidecar; **the taxonomy
  is NOT widened here — Karl's call, the TAX.1 precedent**).
  E4.2's economics rasters carry the COMPUTED origin AUTHORED
  (`combine_origins(SYNTHETIC surface, AUTHORED cutoff)`) and no author of
  their own: the model derived a footprint from a value someone else
  authored. The sidecar therefore records `author_inherited_from:
  data/economics/scenarios.yaml (author: unrecorded)` and no `author:`.
  **Measured against `tests/test_data_origin_audit.py` on a staged copy:**
  as written → invalid, `"AUTHORED with author None"` on every raster (the
  resolver never reads `author_inherited_from`); `author: unrecorded` →
  `audit()` accepts but the frozen-set test flags a new file (P2.0: not
  available to new work); `author: model` → accepted and FALSE. So the form
  passes today only because run outputs are OUTSIDE the walk, and the
  first economics raster committed under `data/` meets a rule it cannot
  honestly satisfy — TAX.1's shape (SYNTHETIC's seed rule was unsatisfiable
  for a synthetic-by-inheritance surface and was WIDENED to admit a
  determinism basis rather than left as an unenforceable strictness).
  **Options, for Karl:** (a) widen AUTHORED's evidence to admit
  `author_inherited_from: <path>` where the cited path's OWN declaration
  resolves (checkable: the audit follows the reference); (b) a derived-
  from-AUTHORED artifact records the derivation as DERIVED's evidence does
  and the lattice keeps saying AUTHORED — i.e. AUTHORED-by-inheritance
  carries DERIVED's evidence, mirroring SYNTHETIC-by-inheritance; (c) leave
  it and never commit an economics raster. Not (c) silently. This is the
  first artifact to inherit authorship; the next will find a rule here
  rather than re-derive one. Owner: E + Karl. **Trigger: before the first
  economics raster is committed under `data/` — and no later than the
  E3.1+2 entry above ("the first commit that writes a surface into
  `data/`"), which fires at the same moment.** Detail:
  [E4.2.md](walkthroughs/E4.2.md) closing; `economics/writer.py:
  _origin_entry`; the approval ledger row.
- [ ] **THE SLOPE FILTER IS PHYSICALLY MEANINGLESS AT 0.1° AND IS APPLIED
  ANYWAY — resolve at Checkpoint 1** (E4.1 commit 2, 2026-08-22).
  Contract 4's `spatial_filters.max_slope_degrees: 6` is a COLLECTOR limit;
  the stack's `slope` is Horn's 3x3 gradient on ~11 km cells, a regional
  gradient whose maximum on this grid is **0.87°** (median 0.31°) — the
  filter removes zero cells and could not remove any. `CutoffEconomicModel`
  applies it as specified (not skipped, not pretended to mean something)
  and records `SLOPE_RESOLUTION_NOTE` beside the count. At Checkpoint 1
  with ~460 m GEBCO cells the gradient becomes local enough that a
  collector limit begins to mean something — and Isaac's `[GEOLOGY —
  ISAAC]` confirmation of the threshold is still owed. Owner: E (the
  resolution note becomes a measurement) + G (the value). **Trigger:
  Checkpoint 1.** Detail: `economics/cutoff.py`; [E4.1.md](walkthroughs/E4.1.md) §2.
- [ ] **OTHER ENTRIES TRIGGERED "BEFORE CHECKPOINT 1", reported at HASH.1 so
  none expires the way the sole-observer pass did** (2026-08-22; none of
  them is HASH.1's to do). Three remain live with that trigger: (i) §1/§2
  the bathymetry source's `data_origin: null` in `source_queue.yaml` — Karl
  (+ G), "at download / before Checkpoint 1"; (ii) §2 GEBCO TID
  classification and whether the matrix needs a TID mask — Karl + G,
  "before Checkpoint 1"; (iii) §3 `DemGrid.load` accepting rotated /
  south-up geotransforms it cannot handle — **E-only**, "before Checkpoint
  1 (the next new DEM entering the system)", a one-line assertion and the
  natural companion to this task that was NOT pulled in because the prompt
  scoped two commits. Owner: E. Trigger: before Checkpoint 1, unchanged.
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
- [x] **`DemGrid.load` accepts rotated and south-up geotransforms — CLOSED
  at G.3 commit 3 (2026-08-24), before any real DEM is loaded:** both
  refusals in `load()` (rotation/shear naming b and d; south-up naming the
  orientation), two constructed refusal tests plus a self-activating check
  that the real GEBCO subset's transform satisfies the predicate;
  mutation-verified (both refusals deleted → exactly the two named tests
  fail). *(original entry)* (found by the E2.0-2 adversarial review's
  probes; pre-existing
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
- [x] **PHASE-2 CLOSEOUT BATCH — DONE 2026-08-20 (P2.CLOSE, four commits,
  one per sub-item).** All four sub-items closed; suite 470 → 471 passed / 2
  skipped. Three findings were turned up by the premise checks and BACKLOGGED
  rather than fixed inside the closeout (§3: the theorem test's seed-calibrated
  tolerances; LITERATURE's missing evidence observer) — and two of Karl's own
  premises did not survive verification (the README's actual text; the
  SESSION_STATE path plus two markdown links that would have dangled).
  Walkthrough: [P2-closeout.md](walkthroughs/P2-closeout.md).
  *(original entry, for the record)* **four items that were each due "at
  Phase-2 closeout" and would each have expired there separately** (consolidated at
  the E2.5 approval, 2026-08-19, by Karl's instruction: "so they stop
  expiring individually"). E2.5 IS the last Track-E task in Phase 2, so all
  four triggers have now FIRED; this entry is what they fired into.
  **Owner: E. Trigger: before Phase 3, or before the repo is shown to anyone,
  whichever comes first** — the wording P2.C already carried, with "Phase-2
  closeout" replaced now that the closeout is the present moment.

  **Two sub-items are not purely E's**, and the batch's single owner line must
  not quietly reassign them: (a) P2.C carries one `[KARL — DECIDE]` point —
  the `SESSION_STATE.md` fate — and was owned "Karl + E" as an entry; and
  (b) F-6's three options are a Karl-and-E choice about whether markdown
  drift is pytest's problem at all. E can do everything else in the batch
  unblocked. (Counted, not remembered: one `[KARL — DECIDE]` tag inside the
  P2.C body. An earlier draft of this very sentence said "two" — the
  correction-drift shape CLAUDE.md rule 5 names, caught by grepping the
  block instead of re-reading the sentence.)

  **Nothing below is a summary** — each sub-item is its original entry, moved
  whole with its citations. The per-item trigger sentences are left in place
  as the record of what each was originally due against; **the batch trigger
  above supersedes them all.**

  - **(a) DONE 2026-08-20 (P2.CLOSE commit 3).** All nine items dispositioned;
    three needed no edit and are recorded as such (the fixtures README was
    already done at P2.0d-3; the "blocked on" framing had no live instance
    left outside the deliberate section title; obligation 6's `sd_ddof` keeps
    its verbatim text by its own disposition). Two premises did not survive
    checking and are corrected in the walkthrough: the root README read
    "Phase 1, Track E complete through E1.4", not "Phase 0 (scaffold)"; and
    `SESSION_STATE.md` lives at `docs/`, with TWO inbound markdown links in
    the origin audit that would have dangled — flattened, not left broken.
    Two further mismatches were found by the in-file scan item 1 asked for:
    §1's `[06]` entry cited `corpus_builder.py:168` (now a column mapping;
    the guard is at :234) and named `_require_production_path()` where
    callers actually hit `_require_proven_measured()`. Detail:
    [P2-closeout.md](walkthroughs/P2-closeout.md) commit 3.
    *(original entry, for the record)* **P2.C — doc-consistency fixes (the deferral LANDED, E2.4 §1,
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

  - **(b) DONE 2026-08-20 (commit 2).** Finding re-verified first — the
    column was deleted and the suite stayed green at 470. Shape (a), a
    doc-lint, chosen because (c)'s premise fails: THERE IS NO RENDERER to
    assert on. Trade-off and what it does not catch are recorded at the test.
    *(original)* **Nothing observes the walkthrough's own comparison tables** (E2.4 audit
    F-6 residue, recorded 2026-08-19 when the column half was fixed and this
    half was not). Obligation 7's uncertainty-semantics column is now a real
    column in both §3 tables that print sd-derived numbers, and the MANIFEST
    side is tested end to end — but `test_every_sd_shaped_number_in_the_artifact_carries_its_semantics`
    reads the artifact, not the markdown, so the column can be deleted from
    `docs/walkthroughs/E2.4.md` with a green suite. There is no report renderer
    in `engine/` to test: the tables are hand-written. Options: (a) accept —
    markdown drift is caught by review, not by pytest; (b) generate the §3
    tables from the manifest so the column cannot be dropped without the
    generator changing; (c) a doc-lint test that asserts the semantics column
    exists in any table printing `cov ±1σ` or `z-RMS`. Owner: Karl + E.
    Trigger: at Phase-2 closeout, or the first time a table is edited by hand.
    Detail: [2026-08-19-e2.4-implementation-audit.md](audits/2026-08-19-e2.4-implementation-audit.md)
    F-6.

  - **(c) DONE 2026-08-20 (commit 1).** The 8-seed measurement reproduced
    exactly; a 40-seed sweep then showed the AUDIT'S OWN REMEDY would have
    left the suite red (base − RF ≥ 0.15 fails seed 4) and that the baseline
    floor it never flagged holds at only 29/40. Only the DIRECTION survives
    (40/40) and is asserted, at five fields rather than one.
    *(original)* **The known-answer leakage test's MAGNITUDE pins are not seed-robust —
    the test is green at ONE of eight sampled seeds** (E2.4 audit row L,
    2026-08-19; entry written when Karl approved the deferral, the finding
    itself having been recorded in the audit at `dc0290a`).
    `tests/test_cv_known_answer.py` pins six things on the planted two-cluster
    field. **Measured by sweeping the FIELD seed over 11–18** (the k-fold,
    runner and RF seeds are held at 0 and were NOT swept):

    | assertion | holds at |
    |---|---|
    | floor `0.75 ≤ ratio_baseline ≤ 1.0` | **8 of 8** |
    | `ratio_baseline − ratio_RF ≥ 0.15` | **8 of 8** |
    | `ratio_baseline − ratio_kriging ≥ 0.15` | 6 of 8 (fails 11, 17) |
    | `ratio_kriging ≤ 0.65` | 4 of 8 (fails 11, 14, 15, 16) |
    | `ratio_RF ≤ 0.60` | 5 of 8 (fails 11, 12, 18) |
    | the three ± 0.02 point pins | seed 13 only, by construction |

    **The whole test would be RED at 7 of 8 seeds**, and the ratio CEILINGS are
    more fragile than the gap.

    **THE CANDIDATE FIX — pin what survives seed variation, report what does
    not.** ASSERT: (i) the DIRECTION — each spatial model's ratio strictly below
    the baseline's, which held 8/8 and is what §3's conclusion actually rests on;
    and (ii) `ratio_baseline − ratio_RF ≥ 0.15`, which also held 8/8. DEMOTE to
    reported-not-asserted: (iii) the absolute gap `ratio_baseline −
    ratio_kriging ≥ 0.15` (fails 11, 17); (iv) `ratio_kriging ≤ 0.65` (fails 11,
    14, 15, 16); (v) `ratio_RF ≤ 0.60` (fails 11, 12, 18); (vi) the three ± 0.02
    point pins (seed 13 only, by construction). The alternative is to raise the
    fixture size until the magnitudes ARE properties of the method rather than of
    seed 13 — which is the better science and the larger change. **A remedy
    naming only the `≥ 0.15` gap leaves the test red at 6 of 8**, which is the
    correction-drift shape CLAUDE.md rule 5 now names. Either way it is a CODE
    change, which is why the audit listed it rather than fixing it.
    Owner: E. **Trigger: before Phase-2 closeout** (and in any case before the
    leakage number is cited outside the walkthrough, or the fixture is resized at
    Checkpoint 1). Detail:
    [E2.4.md](walkthroughs/E2.4.md) §3 (the seed-robustness paragraph and its
    table);
    [2026-08-19-e2.4-implementation-audit.md](audits/2026-08-19-e2.4-implementation-audit.md)
    row L / F-7 (the eight-seed ratio table).

  - **(d) DONE 2026-08-20 (commit 4).** List re-derived by measurement, not
    from the survey: three confirmed sole observers (1 of 471 each) now carry
    their warnings; the two ambiguous P2.0c candidates DISSOLVED (6 and 8
    observers) and are recorded so the next pass does not re-investigate them.
    *(original)* **Sole-observer hygiene pass** (recorded at E2.0-2; convention
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

- [x] **THE FULL-DATA VARIOGRAM PARAMETERS LIVED ONLY IN PROSE — CLOSED at
  E5.5 commit 2 (2026-08-22), the entry written at the moment of closing
  because E5.0 (read-only by instruction) found it and could not land it.**
  E5.4's requirement 4 — mark the no-information region — needs the fitted
  range the surface was predicted under, and no artifact carried it: the
  run manifest's twenty `range_km` values were all PER-FOLD CV fits in
  `cross_validation` (0.36 km, "range below first supported lag", etc.),
  while the full-data fit (21.611 km, AT the candidate ceiling) existed
  only in [E3.1-2.md](walkthroughs/E3.1-2.md) §2. The mechanism was already
  there and dropped: `build_surfaces` records each estimator's `provenance()`
  at the full-matrix fit in `SurfaceResult.provenance` (E3.1+2) and the
  emitter's surfaces block took `summary()` only. Now `surfaces[est].full_data_fit`
  carries it for every estimator (kriging's `KrigingReport` dict with the
  ceiling and floor flags, `residual_dof`, the bin table and its exclusions,
  the spherical alternative; RF's read-back hyperparameters; the baseline's
  moments), verified by a FRESH refit in the test and separated from every
  per-fold value. Detail: [E5.5.md](walkthroughs/E5.5.md) §2;
  `provenance/emitter.py` (the surfaces block).
- [x] **HONESTY-SURFACE INPUTS STILL PROSE-ONLY AFTER E5.5's THREE ADDITIONS
  — CLOSED at E5.4 (2026-08-23), each decided:** (i) the 0.5 kg/m² fraction is
  NOT displayed by decision — the no-information count (2,846 of 2,880
  predictable cells) is the viewer's statement of the same fact; (ii) the
  34-cell count is DERIVED in the presentation model (shape-not-value) from
  the stations and the fitted range, never recomputed in the page; (iii) the
  cluster geometry is visible as drawn points, the stripes clearing only
  around the two clusters; (iv) the registry dependence is shown via the
  layer's `fit_facts` (n_estimators 500, read back). Detail:
  [E5.4.md](walkthroughs/E5.4.md) §2. *(original entry)* **E5.4 decides
  derive-vs-record for each** (E5.5 commit 2, 2026-08-22;
  the closing check the E5.5 prompt asked for). Checked against E5.0 §4's
  inventory after `full_data_fit`, `sd_min/sd_max` and `training_stations`
  landed: (i) **the 99.62 %-within-0.5-kg/m² fraction** (E3.1-2 §2) — not
  recorded; derivable in the browser from the exported surface and
  `full_data_fit.training_mean` (baseline) — a derivation downstream, which
  E5.0 §3 flagged as a second source of truth; (ii) **the 34-cells-within-
  one-range count** — derivable from `training_stations` + `full_data_fit.range_km`
  + `prediction_grid`, the same way; (iii) **the two-cluster / 991-km
  geometry** — carried as data (`cross_validation.designs[].assignment`,
  the LOCO fold labels and `measured_min_separation_km`) but only as a
  sentence in `purpose` — *at E5.3 the 35 stations are DRAWN from
  `training_stations`, so the clustering is visible without the number;
  the number stays derive-vs-record for E5.4*; (iv) **the RF-registry dependence** (40 vs 500
  trees changes the surface) — now verifiable from `full_data_fit.n_estimators`
  but stated nowhere a reader meets. None blocks E5.4; each is a choice
  between recording a number at the emitter (schema 5, under HASH.1's rule)
  and deriving it in the viewer with the derivation named. Owner: E.
  **Trigger: E5.4's specification pass.** Detail: [E5.5.md](walkthroughs/E5.5.md)
  closing; E5.0 report §4 (chat, 2026-08-22 — the report itself is not in
  the repo; its substance is in E5.5.md §0).

- [ ] **A RUN DIRECTORY CANNOT BE COMMITTED UNDER `data/` AS IT STANDS —
  three refusals, measured by probing, one of them new** (E5.5 commit 3,
  2026-08-22; staged at `data/runs/e5.5-probe/` in a `git archive` copy,
  `git add`ed, `audit()` called directly). Not intended to be committed —
  the viewer and the API read a directory the harness or E5.6's CI job
  produces — but the first run directory that IS lands on: (a) UNCLASSIFIED
  ×10 — `economics/economics.footprints.json` carries no top-level
  `data_origin`, and the nine `features/stack/` files have no sidecar (the
  stack's `provenance.json` is not one of the three marker forms); (b)
  INVALID ×18 — every economics raster `AUTHORED with author None`, the
  `author_inherited_from` entry above CONFIRMED on a real run directory;
  (c) **NEW — `run_manifest.json` is flagged as "newly carrying
  `author: unrecorded`"** because it QUOTES Contract 4's cutoff declaration
  (`economic_results[].cutoff.author`, four occurrences): the deep scan
  (`_contains_unrecorded_author`, any depth) cannot tell a file that
  DECLARES an unrecorded author from one that RECORDS another file's
  declaration, and a manifest must be able to quote what it resolved. The
  other direction holds: stripping one sidecar entry makes exactly that
  raster unclassified and nothing else moves. Remedies, each small: a
  `data_origin` block on the association record; a `data_origin.yaml` in
  `features/stack/` (TAX.1's form, SYNTHETIC-by-inheritance with the stack's
  determinism basis); and a quoted-declaration rule in the scan (e.g. a
  `files:`/`cutoff`-shaped node whose `data_origin` sits beside its
  `author` is a QUOTATION, not a declaration — to be decided against the
  scan's own evidence). Owner: E (a, c) + Karl (b, the existing entry).
  **Trigger: before any run output is committed under `data/` — the same
  moment as the E3.1+2 entry and the `author_inherited_from` entry above.**
  Detail: [E5.5.md](walkthroughs/E5.5.md) §3; `harness.py` `RUN_LAYOUT`.
  *Confirmed at E5.1 (2026-08-22): SERVING a run directory over HTTP is not
  committing it — the audit walks `git ls-files -- data tests/fixtures`, the
  API's runs root is wherever the operator points it, and nothing served
  enters git; an E5.7 deployment that copies a run INTO `data/` would trip
  this entry, one that serves from outside does not.*
  *E5.2 (2026-08-22): the flat-array exports join the run directory
  (`export/`, 22 files) with their own `data_origin.yaml` in TAX.1's form and
  an in-file `data_origin` block each; if a run is ever copied under `data/`
  they classify, and the economics exports meet the same
  `author_inherited_from` refusal as the rasters — no new cost, the same one.*

- [ ] **THE CONTEXT-LAYER DATA TASK — download, hash, classify the real
  layers; two decisions ride on it that are Karl's** (E5.3 commit 2,
  2026-08-23 — the capability shipped with a FIXTURE, a rectangle that says
  it is one; the data is deliberately not acquired there). The layers: the
  CCZ management area (Marine Regions MRGID 64222, layer
  `MarineRegions:isa_ccz_managementarea`, CC-BY 4.0) and the ISA shapefiles —
  exploration areas, reserved areas, APEIs (ISA copyright; ISBA/17/LTC/7,
  ISBA/18/C/22, ISBA/26/C/58, ISBA/26/C/43). Each arrives as a file under
  `data/context/` (INSIDE the audit's walk: a `.geojson` must declare
  `data_origin` in-file), its sha256 in `services/api/context.py`'s
  registry, its citation in `attribution_text` where a user sees it, and its
  class under the taxonomy DECIDED, not assumed. **Riding decisions (Karl):
  (i) whether the CCZ polygon resolves the AOI** (§1, Checkpoint 1) — and
  note the classification question that comes with it: a downloaded, hashed
  shapefile from an authoritative publisher may be MEASURED (the relation
  the corpus has to PANGAEA) rather than the LITERATURE the AOI entry
  assumes, which would take the AOI off the zero-observer class; reasoning
  recorded, not decided here — **DECIDED at G.2 (2026-08-25): LITERATURE, and
  the MEASURED reading above was considered and rejected. The artifact is a
  boundary DECREED in ISBA instruments and digitised from them; nothing in its
  lineage was measured (GEBCO's DERIVED rests on measured soundings — there is
  no analogue), and its sha256 proves only WHICH COPY we hold. So the AOI does
  NOT come off the zero-observer class; see that entry, whose deadline has now
  EXPIRED**; **(ii) whether the APEIs populate Contract 2's
  `exclusions.geojson`** (AUTHORED, `features: []`, asserted EMPTY by E4.1 so
  the day it is not is visible — the first polygon is a visible refusal in
  `CutoffEconomicModel` until rasterisation is built) — **STILL OPEN; this is
  the whole of what remains here.**

  **HALF THIS ENTRY IS DONE (G.2, 2026-08-25).** The CCZ management area is
  downloaded, hashed, classified and WIRED: it is `data/aoi/study_area.geojson`
  itself (Contract 2's file, not a copy under `apps/web/`), the registry points
  at it, and the CC-BY attribution reaches the footer. **The FIXTURE rectangle
  is deleted** — `apps/web/context/ccz_management_area_FIXTURE.geojson` no
  longer exists, so the trigger below ("before E5.7 ships a public URL with the
  fixture rectangle still drawn") can no longer fire as written. What remains
  is the ISA shapefiles and decision (ii).

  ~~Also measured at E5.3: the CCZ box is ~13.86 M km² against a ~0.41 M km²
  prediction extent (33.8×; 2.96 %)~~ — **SUPERSEDED at G.2 and struck rather
  than edited, because the comparison itself was wrong, not just the numbers:
  it put the CCZ's BOUNDING BOX against the prediction EXTENT box, and the
  polygon is only 83 % of its box while the extent counts cells the covariates
  do not define. Like against like, the AOI POLYGON (11,399,939 km²) against
  the run's PREDICTABLE domain (346,927 km²) is 32.9×, i.e. 3.04 % of the zone.
  This copy stood for a day after `services/api/context.py` and the test were
  corrected — the correction-scoped-to-the-claim-not-the-entry shape, this time
  across FILES; correction-drift instance (q).** Drawing the real boundary
  shows how small the study area is, which is honest and is not to be hidden by
  adjusting the view.
  Owner: Karl (acquire + decide) + E (wire). **Trigger: whenever the ISA
  shapefiles are downloaded.** *(The public-URL half of this trigger is spent:
  reported FIRED at E5.7 (2026-08-23) with the rectangle still drawn, and
  RESOLVED at G.2 by deleting it.)* Detail:
  [G.2.md](walkthroughs/G.2.md); [E5.3.md](walkthroughs/E5.3.md) §3;
  `services/api/context.py`.

- [ ] **THE VIEWER IS CATALOG-DRIVEN; THE CATALOG IS NOT YET DATA-DRIVEN**
  (E5.3 §0.4, 2026-08-23; Karl: "worth a BACKLOG entry for when a second
  dataset actually arrives, rather than generalizing the catalog
  speculatively"). The viewer renders whatever the catalog advertises — one
  control per declared axis, labels and values from `grid.axes` /
  `axis_labels` / `value_labels`, states from the cells, ramp and format from
  per-entry hints — and `tests/test_viewer_model.py` proves it on a foreign
  catalog (three axes, layer types and names this project does not have) with
  no code change. The generality stops one layer lower: `services/api/catalog.py`'s
  `KINDS`, `APPLICABLE_AXES`, `RAMP_BY_KIND`, `FORMAT_BY_KIND` and the label
  tables are THIS project's constants, so a five-axis dataset — a second study
  area, a lunar volatile surface, an estimator nobody has written — needs an
  E5.1 change, not a viewer change. That is the honest boundary of the
  flexibility requirement: real, and one layer below where the requirement
  implies. The generalization (axes declared by the MANIFEST or a contract,
  the catalog reading them) is not made speculatively. Owner: E.
  **Trigger: the first second dataset.** Detail: [E5.3.md](walkthroughs/E5.3.md)
  §1; `catalog.py` header.

- [ ] **CP5b: THE PAGE'S STANDING STATUS MUST CHANGE WITH THE FACTS** (E5.7,
  2026-08-23). A shared link renders a preview card from `<title>` and the
  `description` / `og:` tags with no JavaScript, so the verdict banner cannot
  survive into it; `apps/web/index.html` therefore carries the STANDING status
  in plain text — "non-scientific until Checkpoints 1/3/4 … the claim guard
  refuses … the verdict is on the page" — asserted by
  `deploy/verify_deployment.py`. That text is true today and becomes false
  the day the facts change. Owner: E. **Trigger: CP1, CP3 or CP4 landing —
  any checkpoint that lifts a reason — and CP5b before the launch URL is
  shared.** Detail: [E5.6-7.md](walkthroughs/E5.6-7.md) §2; `deploy/README.md`.

- [ ] **CONFIGS THE SUITE NEVER EXERCISES** (entered at the G.3 approval,
  2026-08-24; the class is in CLAUDE.md's defect table at ×3 — ci.yml until
  E5.6, the gitignore tif rules until G.3, `.claude/launch.json` still).
  A config file is code that nothing executes in CI: a rule that silently
  matches nothing is indistinguishable from one that works. The remedy with
  a record of working is making the SUITE exercise the config the way its
  consumer does (`test_ci_job.py` parses the workflow). The residue, found
  by the approval's scan and deliberately NOT fixed in that commit:
  * **.gitignore's load-bearing rules have no suite observer** — G.3's fix
    was proven by a ONE-TIME manual `check-ignore`, not by a test; a suite
    test asserting `git check-ignore` on representative paths
    (`data/bathymetry/x.tif`, `data/ts6/x.tif`, `outputs/x`, `deploy/run/x`)
    would make the next trailing-comment regression visible.
  * **`.claude/launch.json` carries absolute session-scratchpad paths**
    (committed at `58b6b8e`) that exist on no other machine — the dev
    servers refuse on a fresh boot (correctly, by the not-a-run refusal).
    Fix when next touched: point at `outputs/demo/runs` (which
    `demo_alpha.py` produces) or regenerate. *This open item previously
    lived ONLY in the Phase-5 handoff — an open item outside this file,
    against its own rule; landed here at the G.3 approval.*
  * **The Dockerfile build is untested** — not built in CI, daemon absent
    at E5.7 (recorded honestly there); first exercised whenever Karl builds
    the image for CP5a. If CP5a closes without CI ever building it, decide
    whether a build-only job is worth its minutes.
  * **ci.yml's action pins** (`actions/checkout@v4`, `setup-python@v5`)
    resolve only on GitHub's runners; `test_ci_job.py` parses structure,
    not pin validity. Residual, low: a bad pin fails loudly on the next
    push. Owner: E (+ Karl for launch.json's intended paths). Trigger: the
    next touch of each config; the gitignore test any time, cheap.
  Not exercised-in-CI but NOT in the class: `pyproject.toml` (pip and
  pytest consume it in CI on every run — the consumer executes it where
  the suite lives); the data contracts (parse tests exist). No
  `.gitattributes` exists.

- [ ] **CONTRACT 2 CANNOT DECLARE A CHANGE CLASS — it was frozen without a
  version field** (entered at G.2, 2026-08-25; deliberately NOT solved there).
  `contract_versions.py` identifies `study_area.geojson` by `area_id` + a
  content hash, because Contract 2 has no `*_version`. So the AOI is the one
  contract where the §2 `change_class` proposal (metadata vs semantic) cannot
  be applied AT ALL: there is no version to class, and re-sync travels through
  a hash that moves on ANY edit — a reformatted comment and a new polygon are
  indistinguishable to a consumer. G.2 replaced the geometry and added an
  in-file origin declaration in one commit, and the ONLY signal either change
  produced was `study_area_content_hash` moving, which is exactly the noise
  the freeze existed to prevent. This is the sharpest instance of the §2
  entry, not a separate problem: fixing it means either giving Contract 2 a
  version field (a structural change to a frozen contract) or accepting that
  its hash is its only version and saying so in the contracts README. Owner:
  Karl + E. Trigger: with the §2 `change_class` decision, or the next edit to
  `study_area.geojson`. Detail: [G.2.md](walkthroughs/G.2.md) section 4;
  `engine/prospectivity/provenance/contract_versions.py:5`.

- [ ] **SHOULD THE AOI BOUND THE PREDICTION GRID? The README line that said
  it did is STRUCK, and the question it implied is real** (entered at G.2,
  2026-08-25). G.2-PRE found `docs/contracts/README.md` claiming Track E
  does "clip/align grid" for Contract 2 — zero code, zero tests, the same
  shape as the tripwire clause C8.1 struck, in the contracts' own summary
  table. G.2 STRUCK it rather than implementing it, because implementing it
  is a decision and not a fix; the row now says what is true (the AOI is read
  as the coverage denominator; nothing clips or aligns on it).
  **The decision, with the asymmetry that makes it non-obvious** (G.2-PRE
  section 2e): the covariates' NaN-union mask can only ever SHRINK the
  domain, so an AOI LARGER than the feature stack is silently inert — which
  is today's case and why nothing has broken — while an AOI SMALLER than the
  stack would be the first thing in this repo capable of DISCARDING cells the
  covariates support. That is a real behaviour change and needs stated
  intersection semantics before any code reads the polygon geometrically.
  Note it is not urgent: at Checkpoint 1 a global GEBCO DEM stops bounding
  anything by accident, which is when the answer starts mattering. Owner:
  Karl + E. Trigger: Checkpoint 1, or any task that makes something read the
  AOI's geometry for filtering. Detail: [G.2.md](walkthroughs/G.2.md)
  section 4; `services/api/context.py`; `engine/prospectivity/surfaces/grid.py`.

- [ ] **THE COMMITTED CORPUS MANIFEST NOW DIVERGES FROM EVERY FRESH BUILD**
  (found at G.2 by measuring, 2026-08-25; deliberately not fixed there).
  `data/corpus/manifest.json` is LEGACY (no `schema_version`) and records
  `study_area_id: ccz_alpha_aoi`, `fraction_outside: 1.0` and the
  placeholder's hash. Every run rebuilds it (`upstream_hashes.corpus`), and a
  fresh build now differs in FOUR fields at once —
  `contract_versions`, `study_area_containment`, `generated_at`, and
  `schema_version` (null becomes 1, i.e. the artifact would leave HASH.1's
  legacy class). Regenerating therefore bundles a legacy-status transition
  into whatever commit does it, and moves a hash three test modules pin,
  which is why G.2 left it: only ONE of those four reasons is about the AOI.
  Nothing downstream propagates the stale numbers (runs use their own fresh
  build), so this is a staleness-of-record problem, not a correctness one —
  but a reader opening that file today reads "108 of 108 rows outside the
  AOI", which is now false and alarming. Decide: regenerate (and re-pin the
  three literals in one deliberate commit), or declare the committed copy a
  dated archive and say so in it. Owner: Karl + E. Trigger: the next corpus
  change, or any time. Detail: [G.2.md](walkthroughs/G.2.md) section 4.

- [ ] **SEVEN LIVE SITES STILL DESCRIBE THE AOI AS A PLACEHOLDER OR THE
  CONTEXT LAYER AS A FIXTURE — all outside the G.2-approval commit's
  docs-only fence** (entered at the G.2 approval, 2026-08-25, found by a
  completeness sweep over G.2's own output; the E3.1+2 precedent — "the two
  engine-side date labels that commit's docs-only fence could not reach" —
  is why they land here rather than being fixed in that commit).
  **Every one is a FALSE STATEMENT IN LIVE CODE, not stale prose in a dated
  record**, and two of them reach an emitted artifact or a served page:
  * `engine/prospectivity/provenance/geometry.py:250-252` —
    `count_outside_study_area`'s FUNCTION docstring still says "the AOI itself
    is an open decision (docs/BACKLOG.md §1), so this module states the
    mismatch and stops". **G.2 rewrote this file's MODULE docstring and its
    emitted `note` and missed the function three lines below** — the
    correction-scoped-to-the-claim-not-the-entry shape inside the very commit
    that was fixing that string. There is no mismatch now: 0 of 108.
  * `engine/prospectivity/harness.py:169-170` — `load_study_area`'s docstring:
    "Contract 2's AOI feature — the committed placeholder until the AOI
    decision (BACKLOG §1)". Both halves false; G.2 never touched this file.
  * `engine/prospectivity/terrain/tid_accounting.py:80` and `:134` — "the AOI
    decision replaces it at CP1", the second inside an **EMITTED artifact
    field** (`bounds_source`), so a G.3 TID artifact now ships a sentence
    about a decision that has been made.
  * `services/api/context.py:51-57` — "WHERE THEY LIVE: `apps/web/context/`
    (the fixture)". G.2 DELETED that directory; the docstring contradicts the
    registry seven lines above it in the same file.
  * `tests/test_context_layers.py:97` and `:129` — "by the same closed form
    the coverage block uses". FALSE and it is G.2's own: the numerator is
    `polygon_area_km2`'s closed-form spherical excess, the denominator is
    `grid_predictable_area_km2`'s cos(lat)-weighted per-cell SUM. The 32.9×
    ratio is sound and like-against-like in QUANTITY; only the METHOD claim is
    wrong (correction-drift instance (p)).
  * `apps/web/README.md:11,17` — "Not built yet", predating G.2: the page has
    shipped and been deployed to a rehearsal URL.
  Owner: E. Trigger: any time — each is a one-line edit, and they are grouped
  so the sweep happens ONCE rather than one file per task. Detail:
  [G.2.md](walkthroughs/G.2.md) §8.

- [ ] **SWOT VERTICAL GRAVITY GRADIENT AS A COVARIATE IN ITS OWN RIGHT —
  a real scientific idea, deliberately OUT OF SCOPE** (entered at TID.2,
  2026-08-26). TID.2 established that 54.9% of the study extent is bathymetry
  PREDICTED from SWOT gravity by a machine-learning model. The idea that
  follows: if gravity is already determining the terrain under half the
  domain, use the **vertical gravity gradient directly** as a covariate rather
  than only its bathymetric inversion. The scientific case is genuine —
  gravity reveals BASEMENT structure beneath sediment, and nodule abundance is
  thought to relate to sediment thickness and basement topography, which is
  exactly the signal a smoothed depth surface loses.
  **WHY IT IS OUT OF SCOPE, stated so the idea is not silently dropped:** it
  is a NEW DATA SOURCE (a SWOT/altimetry gravity grid this repo does not
  hold), a NEW CONTRACT SLOT (Contract 3 registers terrain recipes over one
  DEM; a gravity grid is a second raster with its own resolution, CRS and
  provenance), a NEW LICENCE to read and record, and — the real bar — a
  covariate whose relationship to abundance needs its OWN justification
  rather than inheriting terrain's. Adding it would also make the training
  matrix depend on a field the 35 stations were never chosen against.
  **TRIGGER, written per the OBS.1 rule** (a trigger naming an event unrelated
  to its remedy expires unnoticed): **when the covariate set is actually
  reopened** — i.e. when someone proposes changing Contract 3's registry, or
  when a CP1 result makes the terrain covariates look insufficient. NOT a
  date, and NOT "when convenient". *And the honest half of that rule applies
  too: this could NOT be done today — it needs data the repo does not have —
  so it is a genuine trigger and not a priority wearing one.* Owner: Karl
  (scope + the science) + E (the wiring, if ever). Detail:
  [TID.2.md](walkthroughs/TID.2.md);
  `data/bathymetry/tid_accounting.json` → `predicted_class_provenance`.

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

- **THE VIEWER STACK — MapLibre GL JS + deck.gl from a CDN; Next.js DECLINED
  (Karl, 2026-08-22; recorded at E5.1 commit 0).** The Phase-0 lane's E5.2
  "thin Next.js viewer" is replaced by ONE static HTML page: MapLibre GL JS +
  deck.gl loaded from a CDN with pinned versions and SRI hashes, no npm, no
  node, no build step. BOTH HALVES: Next.js is declined because Global Fishing
  Watch needs React for a product team and a component library, while this
  needs one page — and MapLibre + deck.gl is the same rendering engine GFW
  uses, with no second toolchain in a solo project; 4wings is declined because
  its tile format packs a time series per cell and this data has no time axis
  (the switching axis is layer × estimator × z × scenario). Measured at E5.0 §5
  (2026-08-22): MapLibre GL JS 6.5.0 BSD-3-Clause, ESM-only from the CDN
  (5.24.0 is the last UMD build); deck.gl 9.3.10 MIT, UMD `dist.min.js`
  1,648,135 B; a library is a TOOL the origin taxonomy does not classify
  (the quantile-forest precedent, E2.3); `apps/web/*.html` is outside the
  audit's walk. A build step, if one ever becomes unavoidable, is a stack
  decision to STOP on, not an implementation detail. **Still open inside this
  decision — CLOSED at E5.3 (Karl, 2026-08-23): NO TILE BASEMAP.** Zero Natural
  Earth coastline features intersect the study extent (nearest coast 10.4°
  away), so a tile service would render ocean and buy an uptime dependency, a
  licence and a runtime fetch for nothing; the page draws a dark background, a
  graticule and the VENDORED public-domain Natural Earth 110m coastline
  (`apps/web/ne_110m_coastline.geojson`, sha256 in `services/api/web.py`).
  *(was: the basemap tile source — a third external dependency with its
  own licence, attribution and uptime.)* Where the decision
  lives: the alpha proposal's Phase-5 lane (revised 2026-08-22, tracked at
  E5.1 commit 0), CLAUDE.md's stack list and status line, `apps/web/README.md`.
  Detail: E5.0's §5 report (chat, 2026-08-22; substance in
  [E5.1.md](walkthroughs/E5.1.md) §0).
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
