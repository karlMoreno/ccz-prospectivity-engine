<!-- Tracked UNEDITED at E2.4 §1 (2026-08-18) per E2.4 sequencing prompt item 1E(c) and the
     P2.PRE instruction-provenance rule. This is the handoff Karl pasted at the start of the
     E2.4 session (written from a planning conversation). It is a SUMMARY, not a source of
     truth — the repo files it names win. The first-actions cross-check that answered it is
     recorded in docs/walkthroughs/E2.4.md §0. -->

HANDOFF — Claude Code, start of E2.4
Paste at the start of a fresh session. This is a summary, not a source of truth. `CLAUDE.md`, `docs/BACKLOG.md`, `docs/PATTERNS.md`, `docs/walkthroughs/`, `docs/audits/`, and the contract files win over anything here. This document was written from a planning conversation; the repo has moved since it was last checked.
First actions

1. Read `CLAUDE.md` — note two conventions added since Phase 1: the fixture-degeneracy rule (a hand-computed fixture must separate the claimed statistic from its neighbors) and the deferral rule (a finding whose disposition is deferred gets its BACKLOG entry at the moment of deferral).
2. Read `docs/prompts/phase2_prompts.md` §E2.4 as revised 2026-08-14 (the dated revision line at the top of the section). That section IS the E2.4 specification: the geometry theorem, the eight runner obligations verbatim, and the score-dating design. The prompt Karl pastes sequences it; it adds nothing to it.
3. Read `docs/BACKLOG.md` — specifically the runner-obligations entry, the pre-registration-clock entry (§2), and the E2.5 tripwire appended to it.
4. Read `docs/walkthroughs/E2.2.md` §2 and `E2.3.md` §2 for what each estimator's `report()` exposes — the runner carries those fields into run provenance.
5. Run the suite; report the count. Last confirmed: 374 passed, 2 expected skips.
6. Cross-check the docs against each other, not only against this file — confirming this handoff against the repo cannot surface two repo files that disagree.
7. Report anything in this handoff the repo contradicts.

State
Phase 2 estimators are complete through E2.3, and the E2.0–E2.3 review chain is audited and closed (`docs/audits/` disposition ledger, verdict block dated 2026-08-14, Phase-3 residue: zero — no Section 0 carry-overs ride into E2.4).

```
  P2.0–P2.A  ✓  preflight: origin taxonomy, Contract 8, [05] investigation
  E2.0       ✓  TrainingMatrix + 4th ProvenanceArtifact (35×8, ceiling 0.348)
  E2.1       ✓  Estimator ABC (Template Method, __init_subclass__ guard),
                MeanBaseline, EstimatorRegistry, known-answer fixture
  E2.2       ✓  OrdinaryKriging — fit 0–13 km only, range at candidate
                ceiling (unconstrained from above), nugget ~68% of variance
  E2.3       ✓  RandomForest + QRF uncertainty (quantile-forest dep),
                sd = (q84−q16)/2, zero-width count 0 on real matrix, pinned
  ─────────────────────────────────────────────────────────────────────
  E2.4       ←  THIS TASK: spatial CV + comparison report
  E2.5          refuse-to-validate (expected small — see tripwire)

  Deferred, not blocking: P2.C doc fixes (needs Karl's SESSION_STATE.md
  call), P2.D datetime dedup.

```

The facts that shape E2.4 — verify each in the repo, then honor them
The geometry theorem (BACKLOG runner obligation 8; §E2.4 revised text). Two clusters (21 E / 14 W, ~991 km apart), fitted kriging range ≤ 13 km, so across clusters kriging reverts to the training cluster's local mean — kriging ≈ baseline BY CONSTRUCTION. The across-cluster fold measures how much the clusters differ; it structurally cannot rank estimators. The WITHIN-cluster gate is the only live model comparison. If across-cluster numbers deviate from the theorem, that is a bug until proven otherwise — STOP and investigate before writing any report.
The ceiling binds RF, not kriging. 35 stations occupy 4 distinct covariate cells → max covariate-model R² = 0.348, recomputable from the matrix manifest's cell_groups. Kriging predicts from coordinates and is exempt. Every table that shows both must carry this asymmetry.
Three estimators, three kinds of "sd" (obligation 6). Baseline: sample moment (SD, ddof=1). Kriging: model moment (√kriging variance; exceeds the sill far-field by the Lagrange term). RF: quantile half-width ((q84−q16)/2, distribution-free). The uncertainty-semantics column appears in every table that prints an sd-shaped number.
sd=0 policy decided at design time (obligation 3, marked LIVE). Count is 0 today on the real matrix and pinned — this is insurance whose trigger is visible. Any metric that divides by uncertainty states its sd=0 policy before the runner runs; a metric that silently drops sd=0 points excludes exactly the points where a model is most wrong about itself.
The pre-registration clock. E2.4's run manifest carries `scores_first_visible` OUTSIDE the substance hash (the `generated_at` parallel). The timestamp is mutable metadata — honest by convention; the COMMIT introducing the scores is the authoritative witness, and the field's description says so. Kriging nuance: RF's synthetic-era scores are noise-scores, but kriging fits real coordinates against real y, so its scores are real measurements today and any later threshold is post-hoc in the full sense. No acceptance gate exists; E2.5's recorded verdict ("no pre-registered gate existed when these scores were computed") is the honest output, not a gap.
The E2.2 atomicity precedent. A refused refit must never leave an estimator predicting with a stale system matrix — E2.4 refits the ONE shared registry instance per fold, which is exactly the shape that finding protected. The review probes this.
Task shape (Karl's prompt sequences it)
Three commits. Section 1 (fold assignment + metric policy) ends at a STOP: propose within-cluster blocking — leave-one-station-out (max data, but ~2 km neighbors leak at the 13 km fitted range: quantify) vs block-by-cell (honest for RF's cell-constant X, but 3–4 blocks) vs both side-by-side — with measured pair-distance consequences on the real clusters. Karl picks. Do not proceed until answered. Section 2 is the runner (adversarial review; probes: cherry-picking via a dummy fourth estimator, stale refit, provenance completeness failing BY NAME). Section 3 is the comparison report, framed per the theorem, expected outcomes stated in advance so deviation is the news.
Conventions (unchanged, plus the two new ones)
One task per prompt; restate the contract before code; STOP on ambiguity; mutation-verify every guard and report each mutation with its failure message; full-state comparisons (`dataclasses.fields`, not selected fields); fixture docstrings state which neighboring claims they separate; reviews run against committed state or a copy — a mutating reviewer takes a `cp` backup before its first write and restores by `cp`, never `git checkout`; deferred findings get their BACKLOG entry at the moment of deferral; walkthrough + BACKLOG updates in the same commit; PATTERNS.md only if a pattern was genuinely added; suite trajectory reported per commit.
Open, owned by Karl — none blocks E2.4

* Within-cluster blocking choice — the one STOP in this task.
* `src_bathymetry_primary` / GEBCO TID classification (before Checkpoint 1).
* ~~`SESSION_STATE.md` fate (gates P2.C item 9 only).~~ **ANSWERED at P2.CLOSE, 2026-08-20: DELETE. Done.**
* Contract `change_class: metadata|semantic` (before the next metadata-shaped contract addition).
