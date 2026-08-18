# E2 review-disposition audit — 2026-08-14

- **Performed against:** commit `562d9a7` (E2.4-PRE; `git rev-parse HEAD` at
  audit start; working tree clean apart from the untracked `demo.py`).
  Phase-2 fixes landed as `612805f`; this ledger is the commit after.
- **Status:** point-in-time ledger. Where this document and the code
  disagree, the code wins.
- **data_origin:** AUTHORED · **author:** model
- **Provenance of the checklist:** the 22-item checklist this ledger
  verifies was AUTHORED (author: model) by the reviewer FROM THE PLANNING
  TRANSCRIPT — the repo cannot reconstruct it. Each item was verified
  against the repo on 2026-08-14 by direct probe (grep, `git show`,
  `git log`, a per-commit test-count reconstruction); the checklist's own
  claims of "done" and "gap" were trusted no more than each other. This is
  the same instruction-provenance gap the project closed at P2.0a′ (the
  origin audit committed from a transcript) and P2.PRE — the review
  findings and their dispositions now exist in the repo, not in a chat.

**Why this audit exists.** Each E2 task ended with an adversarial review
whose findings were dispositioned by carrying them into the NEXT task's
prompt (Section-0 carry-overs, closeout items, BACKLOG entries). That chain
worked, but nothing had verified it END TO END: if a carry-over was dropped
between a review and the prompt meant to carry it, nothing would have
caught it. Result: **nothing was dropped.** Two predicted gaps and one
stale table were confirmed; two BACKLOG triggers had silently expired; two
§4 risks had been answered but never re-dispositioned. All fixed in docs.

---

## PHASE 1 — THE LEDGER (read-only)

Dispositions: **LANDED** (as specified — file/commit cited) ·
**LANDED-MODIFIED** (landed with a correction; delta stated) ·
**NOT-LANDED** (what is missing) · **DELIBERATELY-DROPPED** (only with a
recorded decision — none found).

### E2.0-1 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 1 | Sole-observer docstring on the `is_open` test — mutation evidence 1-of-272 and the license framing (CC BY-NC; a closed row in a published run is a licensing problem) | **LANDED** | `tests/test_corpus_csv_sample_source.py:185` "SOLE OBSERVER — do not delete or weaken"; "271 of 272 tests stayed green"; "the corpus is CC BY-NC 4.0 … a LICENSE condition" — commit `7bbd9b7` |
| 2 | Known-answer BACKLOG entry carries the correlate-the-DEM prohibition (closed at E2.1 — verify the CLOSED entry retains it and the fixture docstring carries it) | **LANDED** | BACKLOG closed entry :358 "the synthetic DEM is NEVER made to correlate with real abundance" with the original text retained (:377); `tests/fixtures/known_answer.py:18` "THE PROHIBITION, WHICH IS THE PART THAT MUST SURVIVE" |
| 3 | `phase2_prompts.md` rewrite: four corrections + dated revision line | **LANDED** | `7bbd9b7` (+331 lines); `phase2_prompts.md:83` "Revised 2026-08-13 … superseded on four points" naming all four |
| 4 | `regenerate_default_stack_plot` AND its test deleted; demo.py untracked/unmodified; count 272 → 271 | **LANDED** | 0 references in `plot_stack.py` / `test_plot_stack.py`; `?? demo.py`; `git log -- demo.py` empty (never tracked); reconstructed count 271 at `48aab20` |
| 5 | demo.py's swallowed TypeError (step 6 calls `plot_covariate_stack()` with no args, excepts, globs a stale PNG) recorded anywhere | **NOT-LANDED** (as predicted) | no hit in BACKLOG or E2.0.md → **fixed Phase 2** (BACKLOG §3 entry) |

### E2.0-2 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 6 | Audit coverage-boundary entry, in the CORRECTED form (the checklist author's `SYNTHETIC_MEAN_NODULE_MASS_G` claim was wrong — it is inside the walk and already declared) | **LANDED** | BACKLOG :542–545 "Correction to the E2.0-2 prompt's expectation, verified 2026-08-14: … lives in `tests/fixtures/normalizers.py:19`, INSIDE the walk and already declared AUTHORED" |
| 7 | Sole-observer hygiene pass — five candidates, owner E, trigger "after E2.0" | **LANDED, TRIGGER EXPIRED** | entry present, all five candidates named; "Trigger: after E2.0" with E2.0 long past and no action → **fixed Phase 2** (trigger → before Phase-2 closeout) |
| 8 | `cell_groups` + ceiling recomputable from the manifest; kriging exemption in the E2.0 walkthrough | **LANDED** | `training_matrix.py:124`; `test_cell_groups_match_the_extraction_and_the_ceiling_recomputes_to_0348`; E2.0.md:554 "Ordinary kriging is NOT bound: it predicts from COORDINATES" |

### E2.0-3 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 9 | Cross-helper watermark-divergence test, named for the divergence, mutation-verified BOTH directions | **LANDED** | `test_the_two_watermark_thresholds_deliberately_differ_on_derived` (`8280e14`); E2.1.md rows W-A / W-B — "the only test failing in BOTH directions" |
| 10 | ABC revision's STALE-REFERENCE sweep recorded in the E2.1 walkthrough WITH results (not just the revision) | **LANDED** | E2.1.md:57–63 "References to the old shape, checked": `engine.py:118` needed no change; `test_engine_template_method.py` stub renamed to `_predict`; PATTERNS.md §4.1 corrected. Independent re-sweep at audit: the only `def predict(self` outside `base.py` is the deliberate rogue-override test |

### E2.1 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 11 | Fixture-degeneracy rule in CLAUDE.md's testing conventions, citing [2,4,6]/MB9 | **LANDED** | CLAUDE.md rule 4 (`954e4e0`), both citations present |
| 12 | Every E2.2/E2.3 fixture carries the degeneracy statement (≥3 per task spot-checked, incl. the RF cross-column correlation check) | **LANDED** | module-docstring hits: `test_variogram.py` 2, `test_kriging.py` 5, `test_random_forest.py` 6, `test_random_forest_known_answer.py` 5; `_max_chance_correlation` guard + negation test present |
| 13 | Sill-vs-SD caveat in the kriging docstring + the Lagrange far-field pin test | **LANDED** | `kriging.py:33–40` (both effects); `test_far_field_variance_strictly_exceeds_the_fitted_sill` |

### E2.2 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 14 | Review incident recorded AS an incident in E2.2.md; BACKLOG entry: reviews run against committed state or a copy | **LANDED** | E2.2.md:241 "### Review incident — RECORDED AS AN INCIDENT" (three questions answered from the workflow logs; sha256 `ed6c9ee7…` cross-copy match); BACKLOG :260 |
| 15 | The SECOND layer of the review-workflow rule — (b) a mutating reviewer takes a copy before its first write and restores by `cp`, never `git checkout` — recorded in the ENTRY, not only in prose | **NOT-LANDED** (as predicted) | entry had (a) only; layer (b) existed in E2.2.md's incident prose but not in the actionable BACKLOG entry → **fixed Phase 2** (both layers now in the entry, citing the math reviewer's one-command-late log and the fixtures reviewer's cp/cmp discipline) |
| 16 | `range_at_candidate_ceiling` in kriging's `report()` and in the runner obligations; the ~68% nugget line addressed to Track G in E2.2's real-data section | **LANDED** | `kriging.py:93,296`; BACKLOG obligation 5; E2.2.md:227 "For the eventual Track G notes … ~68% of the total variance is unstructured below station spacing" |

### E2.3 review carry-overs

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 17 | All six QRF additions (mapping + semantics string; quantile sanity test; zero-width diagnostic reported-not-floored; hybrid dismissed on the record; obligation #6 semantics column; dependency hygiene with the taxonomy note) | **LANDED** | `f646942`: `qrf_half_width_q16_q84`; `test_reported_quantiles_are_monotone_and_the_sd_is_exactly_their_half_width`; `zero_width_training_predictions` (4 refs); E2.3.md "The hybrid, dismissed on the record"; BACKLOG "UNCERTAINTY-SEMANTICS COLUMN"; `quantile-forest==1.4.2` pinned + "TOOLS, not data" |
| 18 | Closeout items: saturation finding cross-referenced three ways with expiry; obligation #3 live with count-0-today framing; pre-registration clock; geometry theorem as obligation 8 | **LANDED** | `094132c` (BACKLOG +95, E2.0.md +8, E2.3.md +54); all four grep-confirmed |
| 19 | E2.4-PRE: section rewritten, eight obligations verbatim-verified, commit-date-is-authoritative in BACKLOG §2 | **LANDED** | `562d9a7`; the verbatim copy verified line-for-line (91 lines) at write time; the commit-date line present in both files |

### Cross-cutting

| # | Item | Disposition | Evidence |
|---|---|---|---|
| 20 | Every E2 walkthrough has ONE consolidated mutation table | **LANDED-MODIFIED (E2.3)** | E2.0 (14 rows), E2.1 (11), E2.2 (6) each consolidated. **E2.3's were scattered across three tables** (RF1–RF8 §2, KA1–KA2 §3, RF9–RF12 §2-DECISION) and its closeout's "every mutation, one table" line predated E2.3-4's RF9–RF12 → **fixed Phase 2** (one fifteen-row table in the E2.3 closeout) |
| 21 | Every promised BACKLOG entry exists with owner + a trigger that has not silently expired | **LANDED, 4 EXPIRED** | All promised entries present. Past triggers with no action: coverage boundary + sole-observer hygiene ("after E2.0"); §4 "Variogram support gap" + "Spatial CV fold structure" ("Phase-2 kickoff (E2.2)") — the latter two were CONFRONTED/ANSWERED by E2.2 (Karl's three decisions; recorded exclusions + unsupported range) and the E2.3 closeout (the geometry theorem) but never re-dispositioned → **fixed Phase 2** (two triggers refreshed; two §4 items closed with pointers to what answered them). "Before the next adversarial review" (review-workflow entry) is live, not expired |
| 22 | Suite trajectory 261 → 374 reconstructed per commit; unexplained changes flagged | **LANDED — none unexplained** | Test-count reconstruction from `git show` at all 17 commits (defs + parametrize expansion): deltas +10 (E2.0-1) / 0 (1b) / +18 (E2.0-2) / +17 (E2.0-3) / +1 (E2.1-0) / +13 (E2.1-2) / +6 (E2.1-3) / 0 (E2.2-0) / +6 (E2.2-1) / +20 (E2.2-2) / 0 (E2.3-1) / +12 (E2.3-2) / +7 (E2.3-3, 6 defs + one ×2 parametrize) / +3 (E2.3-4) / 0 / 0 — every delta matches the walkthroughs' per-commit reports; endpoint 376 collected = 374 passed + 2 expected skips (real pytest). The handoff's pre-E2.0 "261" and the E2.0-1 "271" reconcile through the deleted-then-restored `test_regenerate_default_stack_plot` (272 locally at E2.0-1 with the untracked wrapper test; 271 committed after E2.0-2 §0 discarded it) |

**Totals:** 17 LANDED · 1 LANDED-MODIFIED · 2 NOT-LANDED (both predicted by
the checklist) · 2 trigger-expired · 0 DELIBERATELY-DROPPED.

---

## PHASE 2 — WHAT WAS FIXED (commit `612805f`, docs/BACKLOG only)

| Ledger row | Fix |
|---|---|
| 5 | BACKLOG §3: demo.py's swallowed TypeError recorded as a hazard (owner Karl, trigger before it is next presented) |
| 7, 21 | BACKLOG: "after E2.0" triggers on the sole-observer hygiene pass and the coverage-boundary entry refreshed to "before Phase-2 closeout (Checkpoint 2)" |
| 15 | BACKLOG: the review-workflow entry now records BOTH layers — (a) commit/stash/worktree before a review; (b) mutating reviewers `cp`-copy before first write, restore by `cp`/`cmp`, never `git checkout` — citing the math reviewer's one-command-late log and the fixtures reviewer's correct discipline |
| 21 | BACKLOG §4: "Variogram support gap" and "Spatial CV fold structure" closed as CONFRONTED/ANSWERED, each pointing at what answered it (E2.2 §1–§2; runner obligation 8 / E2.4-PRE) |
| 20 | E2.3.md closeout: one consolidated fifteen-row mutation table (RF1–RF12, RF9b, KA1–KA2), replacing the stale three-table pointer |

## PHASE 3 — ITEMS REQUIRING engine/ OR tests/ (NOT fixed here)

**None.** No ledger row is NOT-LANDED in a way that needs a code or test
change. Volume: zero — within the expected zero-to-two.

`git diff --stat` for both Phase-2 commits: `docs/` only. Suite: **374
passed, 2 skipped** — unchanged by this audit.
