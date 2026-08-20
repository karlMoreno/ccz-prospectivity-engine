# P2.CLOSE — the Phase-2 closeout batch

Specification: the P2.CLOSE task prompt (2026-08-20), closing
`docs/BACKLOG.md` §3's **PHASE-2 CLOSEOUT BATCH** and its four sub-items.
Four commits, one per item, code first while the tree was quiet.

| commit | item | suite after |
|---|---|---|
| `ef0db97` | 1 — the seed-robustness pins (code) | 470 passed, 2 skipped |
| `c1a7e1a` | 2 — F-6 residue: an observer for the tables (code) | **471** passed, 2 skipped |
| `2b477de` | 3 — the P2.C doc batch (docs) | 471 passed, 2 skipped |
| `93855c0` | 4 — the sole-observer hygiene pass (docstrings) | 471 passed, 2 skipped |

**Net: 470 → 471 passed, 2 skipped.** One test added (commit 2); commit 1
rewrote a test without changing the count; commits 3 and 4 changed no logic.

---

## The premise checks came first, and three of them changed the work

The prompt warned that several premises were asserted from a transcript. Three
did not survive, and each changed what got built:

| premise as stated | what the repo says |
|---|---|
| assert the direction **and RF's gap** — "both 8/8" | RF's gap is 8/8 on seeds 11–18 but **39/40** on a wider sweep, failing seed 4. Asserting it would have left the suite red at a seed in the test's own list. |
| the root README reads **"Phase 0 (scaffold)"** | It reads **"Phase 1, Track E complete through E1.4."** The BACKLOG's own sub-item had this right; the prompt's paraphrase had drifted. |
| `SESSION_STATE.md`, delete it — "grep for references and report any" | It is at **`docs/`**, and two of its inbound references are **markdown LINKS** in the 2026-08-08 origin audit, not mentions. Deleting without repairing them trades a stale file for two broken links. |

A fourth check confirmed a premise that looked wrong and was not: the corpus
has 36 MASS rows but **35** training-eligible, because eligibility also
excludes quality-flagged rows (`samples/corpus_csv.py:21`). The docs were
right; the quick query was incomplete.

---

## Commit 1 — the leakage test asserts the direction, reports the magnitudes

**The audit's measurement reproduced exactly** (field seed swept 11–18;
k-fold, runner and RF seeds held at 0): whole test green at 1 of 8, floor 8/8,
`base − RF` 8/8, `base − krig` 6/8, `krig ≤ 0.65` 4/8, `RF ≤ 0.60` 5/8, point
pins 1/8.

Because the surviving assertions were about to become load-bearing, the sweep
was widened to 40 seeds:

| claim | holds at | fails at |
|---|---|---|
| **DIRECTION: kriging ratio < baseline** | **40/40** | — |
| **DIRECTION: RF ratio < baseline** | **40/40** | — |
| `base − RF >= 0.15` | 39/40 | seed 4, by 0.0085 |
| `base − krig >= 0.15` | 34/40 | 1, 11, 17, 28, 33, 36 |
| floor `0.75 <= base <= 1.0` | 29/40 | 11 seeds — **9 of them by exceeding 1.0** |
| `RF <= 0.60` | 21/40 | 19 seeds |
| `krig <= 0.65` | 13/40 | 27 seeds |
| the three ±0.02 point pins | **1/40** | everything but seed 13 |

Minimum margins over 40 seeds: `base − krig` **0.0808**, `base − RF`
**0.1415**; no negatives in either.

**So the test asserts the direction at five independently drawn fields and
computes-and-reports the rest.** Five, not one, because the docstring claims
to separate *"random splitting inflates scores on autocorrelated data"* from
*"this seed happened to inflate"* — and no single-seed test can make that
separation however its docstring is worded. Seed 4 is kept in the list
deliberately: it is where the audit's proposed pin fails.

The published seed-13 numbers (0.814 / 0.568 / 0.468) stay published — they
are a measurement at a stated seed — and are now pinned only widely, as
fixture identity rather than effect size.

**Mutations: 4 of 4 caught, but only after two restructurings.**

| # | mutation | first attempt | after fix |
|---|---|---|---|
| M1 | direction reversed | caught | caught |
| M2 | leakage removed (LOCO vs itself) | caught | caught |
| M3 | collecting condition → `if False` | **SURVIVED** | caught |
| M4 | seed list shrunk to one | **SURVIVED** | caught |

M3 is the one worth keeping: collecting *violations* and asserting the list is
empty stays green when the collecting condition breaks. Replaced with a
positive full-state comparison — the pairs that inverted against every pair
examined. M4 added an explicit guard on the seed count, because `expected` is
derived from the same list, so both sides shrank together.

---

## Commit 2 — obligation 7's report-side observer

**Finding re-verified by doing it:** the uncertainty-semantics column was
deleted from §3's fold table and the full suite stayed **green at 470**.

**The choice is (a), and (c)'s premise does not hold.** Karl leaned (c) —
assert on the renderer — but there is no renderer: no markdown emitter exists
in `engine/`, the §3 tables are hand-written, and the audit's own
table-verification script was never committed. (c) would mean building a
renderer and regenerating a frozen historical walkthrough, against the
convention C8.1 re-affirmed one commit earlier.

| | |
|---|---|
| **catches** | an sd-derived table losing the column that says what its sd means |
| **does NOT catch** | a *wrong* semantics sentence; drift in any document not named in the list; and it is brittle, because parsing prose is brittle |

Scope fence honoured: one obligation, one observer, one document list.

**Mutations: 4 run, 3 caught, 1 a genuine no-op — and the no-op was the
finding.** M3 (`if False`) survived the first draft, exactly as in commit 1,
and got the same positive-comparison fix. M4 removed the header/separator
parsing and survived — because **exact CELL equality**, not the separator
check, is what keeps the lint off the prose row that mentions "z-RMS 0" in a
sentence. My docstring had named the wrong mechanism; it now names the
measured one, and records that removing the separator check changes nothing
on today's file.

---

## Commit 3 — the P2.C doc batch, nine items

| # | item | disposition |
|---|---|---|
| 1 | BACKLOG AOI denominator | **fixed** — "108 of 114" → all **108 of 108**, `fraction_outside` 1.0 |
| 2 | `covariates.yaml` title vs version | **fixed** — "(v2)" → "(v4)"; the drift was two versions. Comment-only |
| 3 | root README status | **rewritten** — premise corrected first (see above) |
| 4 | handoff Task A–D closeout | **added** — the four tasks named, incl. the test-name audit's 17 findings and the still-open datetime item |
| 5 | "blocked on" → contract-slot framing | **no edit needed** — last live instance fixed at E2.4 §1; only BACKLOG §1's section title remains, kept deliberately as a grouping label. The `[KARL — DECIDE]` on extending it to CLAUDE.md is **moot**: CLAUDE.md has no occurrence |
| 6 | docs prose vs the origin taxonomy | **fixed** — `PATTERNS.md`'s "recorded in the layer's name" → the declared `data_origin`; the contracts README's pre-vocabulary `SYNTHETIC → REAL` shorthand → declarations; BACKLOG §1's gate name corrected |
| 7 | `tests/fixtures/samples/README.md` | **confirmed done** at P2.0d-3, skipped |
| 8 | CI comment | **fixed** — rewritten to what actually runs, and **CLAUDE.md's reproducibility line corrected with it**, since that sentence is the one `ci.yml` quoted |
| 9 | `SESSION_STATE.md` | **deleted** (Karl's answer), with both dangling links repaired |

**Two further mismatches found by the in-file scan item 1 asked for**, both in
§1's `[06]` entry: it cited `corpus_builder.py:168`, which is now a column
mapping (the guard is at `:234`), and named `_require_production_path()` where
callers actually hit `_require_proven_measured()`. Both functions are live —
the latter calls the former — so the entry was *incomplete*, not wrong.

**A tenth item the prompt's list omitted:** the BACKLOG's own P2.C block also
carries "obligation 6 names a field that cannot exist" (`sd_ddof`, superseded
by `hyperparameters.sd_mapping`). Its disposition is to keep the verbatim text
and record the supersession on the closure line — already done at E2.4 §2 —
so it needs no action, and is noted here so its absence from the prompt does
not read as an oversight.

---

## Commit 4 — the sole-observer list, re-derived

Seven mutations, each run against the **full** suite.

| candidate | result |
|---|---|
| SYNTHETIC without a generator | **SOLE OBSERVER** — 1 of 471 |
| SYNTHETIC without a seed | **SOLE OBSERVER** — 1 of 471 (same test) |
| DERIVED without a derivation | **SOLE OBSERVER** — 1 of 471 |
| the render bypasses the watermark helper | **SOLE OBSERVER** — 1 of 471 |
| P2.0c #9 — layer-origin copy | **NOT a sole observer — 6 tests** |
| P2.0c #10 — hardcoded composition | **NOT a sole observer — 8 tests** |
| LITERATURE without a citation | **ZERO tests — see below** |

The three confirmed tests now carry the E2.0-1b warning in their own
docstrings with this evidence. **The two ambiguous P2.0c candidates dissolved
on measurement** — the origin-composition path turns out to be among the
best-observed things in the repo — and that is recorded so the next hygiene
pass does not re-investigate them. C8.1's two already carry their warnings.

Docstrings only, verified two ways: `git diff`, and an AST comparison with
docstrings stripped (identical for both files).

---

## What the premise checks turned up, and where it went

Three findings, none fixed inside the closeout, each with a BACKLOG entry
written at the moment of deferral:

1. **The theorem test's tolerances are seed-calibrated too** — its three
   numeric tolerances hold fully at 2 of 8 seeds while its structural
   assertion (`range_km < 30`) holds 8/8. Worked example at seed 3: kriging
   RMSE 3.5409 vs baseline 3.2365, **9.41%** against a 5% tolerance. The
   theorem is asymptotic, not exact — the far-field residual is ~exp(−50/R),
   which at R = 13.89 km is ~2.7% and not zero.
2. **LITERATURE's evidence requirement has no observer** — deleting the check
   fails **zero of 471** tests, while its three siblings have one each. The
   check exists and would fire; nothing exercises it. This is
   coverage-that-isn't at the level of the taxonomy's own enforcement, in the
   class Track G's contributions arrive as.
3. Not a defect, checked and cleared: kriging's recurring **22.07 km** fitted
   range across seeds is the declared `range_at_candidate_ceiling` (the flag
   is `True` exactly there) — honest behaviour, not a fallback.

**PATTERNS.md needs no change** — no pattern was added or retired. Recorded
here rather than by editing that file to note a non-event.

## What the next task adds

**Phase 3 planning**, which needs the **AOI decision** — the point where
Track G becomes load-bearing again. That decision is `docs/BACKLOG.md` §1's
"Study area / AOI scope" item, whose denominator this batch corrected: all
108 of 108 corpus rows fall outside the Phase-0 placeholder, so the AOI is
not a detail to inherit.
