# OBS.1 — The LITERATURE observer, and why its trigger guaranteed it would expire

**2026-08-26 · two commits · suite 703 → 704 → 704**

The fixture is five minutes of work. The second commit is the reason the task
existed: the entry was **buildable from the day it was found** and its trigger
was watching something else entirely.

```
  THE ENTRY                        WHAT IT NEEDED        WHAT IT WATCHED
  ─────────────────────────────────────────────────────────────────────
  LITERATURE has no observer   →   one negation      vs   "before Track G
  (found 2026-08-20)               fixture                 supplies any
                                   (no data,               cited value"
                                    no decision,                 │
                                    no delivery)                 │
                                        │                        ▼
                                        │              lapsed at G.3
                                   possible on          2026-08-24,
                                   DAY ONE              missed twice
```

## 1. Commit 1 — the negation fixture

**The measurement, re-run:** deleting LITERATURE's evidence branch failed
**0 of 703** at the G.2 approval; it now fails **1 of 704**, naming
`test_audit_reports_literature_declarations_missing_their_citation`. Its
siblings score 1 each; LITERATURE now matches them.

**Why real data could never have closed it.** The branch fires only on a
MISSING citation, and all five LITERATURE subjects in the repo carry one
(`normalization.yaml#screening` since P2.0c, the two GEBCO PDFs from G.3,
G.2's two). Adding well-formed members — which is what "Track G supplies a
cited value" produces — moves the count not at all. Only a deliberately
malformed declaration exercises the branch, which is exactly what the DERIVED
and SYNTHETIC negation tests do and why they scored 1.

**What the fixture separates** (the degeneracy rule): a declaration with no
`citation` key; one whose citation is whitespace; and one carrying
document + table + page. The third is the discriminating row — a check that
flagged *every* LITERATURE declaration would satisfy the first two asserts and
be worthless. The reported set is asserted in full, not via
`assert not violations` (convention 7).

**Reported, not fixed:** the resolver does **not** distinguish an EMPTY
citation from a MISSING one — `not (citation and str(citation).strip())`
collapses both, and both surface under one finding text. Defensible (neither
locates a number) but a real limit: a reviewer cannot tell whether the author
forgot the field or typed nothing into it. Pinned as behaviour so a change is
deliberate.

**Two record corrections came back "already correct".** No tracked file claims
LITERATURE's first member arrived at G.2. The only `G.1` references are
`G.3.md` correctly disambiguating the G.3 prompt's own misnomer, and the
G.2-approval note that none exists; `G1.1` in the closed GEBCO entry is an
unrelated legacy label from the original proposal, not a task name.

## 2. Commit 2 — the trigger-mismatch class

**Where it belongs, and why not the conventions section:** the defect
inventory **already houses a record-keeping class** — *deferral without a
landing spot* (×4). This is its sibling. That one is a disposition with no
home; this one is a home whose alarm is wired to the wrong door.

**Count DERIVED, not taken (the prompt supplied none): ×2 demonstrated.**
(a) LITERATURE's, above. (b) The AOI entry, whose trigger read "before Phase-2
prediction surfaces" — **Phase 2 ended producing none**, so the condition could
never become true, while defining the AOI never depended on surfaces existing.
Adjacent evidence, deliberately *not* counted because those triggers did fire:
the E2.X disposition audit found **4 expired** triggers in a single pass.

## 3. The sweep — all 62 open entries

Measured, not sampled: every open entry judged against the repo, then
every "doable today" claim sent to an independent refuter. **23 of 26
were refuted** — which is the point of running the second pass at all.

| List | Count | Meaning |
|---|---|---|
| **A — trigger mismatch** | **30 of 62** | the trigger names something adjacent to, not required by, the work |
| **B — already true** | **24 of 62** | the condition is satisfied today; the entry is live and unnoticed |
| **C — doable today** | **3** | survived refutation: a priority wearing a trigger's clothes |
| **overlap (all three)** | **1** | `#43` — the entry that motivated this task, found independently by the sweep |

The overlap is the self-check: the method, run blind over all 62 entries,
surfaced the LITERATURE entry as live + possible + unnoticed without being
told it was the subject.

### A
* #2 — G.0-1 CCZ geometry + APEIs/exclusions — the trigger watches E5.7's public-URL deployment, while both ISA sources are public downloads available from day one.
* #4 — G.0-3 digitized TS-6 → Checkpoint 3 — chains to G.0-step0's thresholds, but digitization needs the figure and 6–12 h of labor, not a pre-registered number.
* #5 — G.0-4 the Phase-A open corpus — watches the pre-registration clock while the real enabler, Karl's verdict on the [05]-vs-[01] burial contradiction, has been available since 2026-08-09.
* #9 — Real TS-6 [18] digitization (Contract 6) — the trigger is backwards: Checkpoint 3 is the review this work PRODUCES, not a condition that enables it.
* #12 — covariates.yaml geology questions (window scale, depth vs relief) — watches a phase boundary while the entry's own owner line names G.0-2 as the moment the answers change covariates.
* #14 — Contract 4 real economics — inverted: Checkpoint 4 is the review this work makes possible, and the entry's own ask puts it before any published run.
* #15 — the wet/dry basis is recorded nowhere — both trigger halves watch downstream consequences (a published run, CP4) rather than the cruise report that would answer it.
* #23 — Pipeline-level row quarantine — waits on a Track-G download while the seam it needs has been in the repo since E1.3 (its D6 half is gated by a contract change instead).
* #24 — Deterministic tie-break to replace first-encountered — waits on [02][03][04]/NOAA while the ranks are optional; the real gate is a Contract 5 change plus Karl's fallback choice.
* #27 — Washburn dual-class fan-out untested — waits on a [19] download for what the entry itself calls a hand-built fixture; the real gate is undecided per-class observation_or_prediction.
* #29 — Datetime format mismatch silently blocks dedup — names where the bug first BITES, not what enables the fix (which is a frozen-contract tolerance nobody can calibrate yet).
* #30 — Intra-batch duplicate detection — names the DOMES downloads while the defect is in pipeline code committed at E1.3; the true blocker is undecided survivorship.
* #31 — source_id foreign-key enforcement — names the next real adapter while the check needs only the committed corpus, which is exactly why it would be degenerate.
* #32 — Lockfile is macOS-arm64 only — 'pre-publication' is a deadline, not an enabling condition; the real gate is an unchosen hash-pinning resolver.
* #35 — demo.py's swallowed TypeError — an external presentation event that enables nothing, while the actual blocker is which DEM the fixed call may point at.
* #36 — CI hygiene (MPLBACKEND, bare pip) — piggybacks on 'the next CI edit', which the two-line fix never needed.
* #37 — the origin audit's coverage boundary — 'before Phase-2 closeout' is a deadline that enables nothing, and it expired two phases ago.
* #38 — Two C8.1 date labels in model_config.yaml — piggybacks on an unrelated future commit to a file nothing has touched since the deferral.
* #40 — Two E3.1+2 date labels in surfaces/ — piggybacks on 'the next commit that touches either file', which is unrelated to knowing which date to write.
* #41 — Narrow write_surface's signature — piggybacks on the hash task and the next writer edit; the real blocker is that the recorded rationale is measurably false.
* #43 — LITERATURE's evidence requirement has NO OBSERVER — watched an external Track-G delivery while the fix is one negation fixture needing no data at all.
* #44 — claim.py's disagreement branch raises NameError — both limbs (next claim.py edit, Checkpoint 3) are piggybacks on the fix itself.
* #45 — a PASSING gate puts a timestamp INSIDE the content hash — names Contract 8's threshold VALUE, which the suite's existing passing fixture makes unnecessary.
* #46 — the THEOREM test's seed-calibrated tolerances — clause 1 fired before the entry was written and clause 2 is a piggyback on editing the file.
* #47 — AUTHORED evidence for an inheritance-derived artifact — names a commit event, while the gate is Karl's three-way taxonomy decision.
* #49 — index of entries triggered 'before Checkpoint 1' — the checkpoint has not fired, yet all three referenced items resolved without it.
* #51 — a run directory cannot be committed under data/ — names the commit that cannot happen, while the gate is entry 47's undecided taxonomy call.
* #60 — Option-B covariates — no trigger line at all, only the phase label 'Phase 6', which enables nothing.
* #61 — Postgres/PostGIS parked until Phase 5 — the condition is a phase label, and it arrived without the entry moving.
* #62 — Phase B/C source tiers — no trigger line; 'out of the alpha entirely' is a scope exclusion that can never become true.

### B
* #1 — G.0-step0 pre-register the thresholds — 'NOW' is honest: both slots are still null and the hard-before-G.0-2 deadline is now the closest thing on the board.
* #2 — G.0-1 CCZ geometry + APEIs/exclusions — the fixture-rectangle trigger discharged at G.2, and the exclusions half it never described is still open.
* #7 — Training target awaiting Track G — 'any time' is accurate; the P2.B measurement is done and only Karl's geology ruling is missing.
* #10 — Geographic spread over row count — 'next source-queue pass' has fired twice (G.3, G.2) without discharging.
* #11 — normalization.yaml geology parameters — the :67/:123 half is gated by nothing today; only the :103 GRADE-join half is correctly unfired.
* #12 — covariates.yaml geology questions — the 'before Phase-2 modeling hardens' deadline expired three phases ago with the entry still open.
* #13 — source_queue download hygiene — 'each download' has fired twice and been honoured both times; the remaining nulls await undownloaded bytes.
* #16 — LITERATURE citations failing the locate-the-number bar — the 211-page TS-6 PDF is on disk, so the condition is met even though closing it is not.
* #19 — Contract change_class — 'before the next metadata-shaped addition' has fired at least three times (model_config 1→2, ts6_reference 2→3 and 3→4).
* #20 — THE PRE-REGISTRATION CLOCK — all three halves have fired; Track G engaged on thresholds at G.0 and both G.3 and G.2 ran before step 0.
* #21 — uncited literature-shaped numbers in the contracts README — 'any time before a published run' is satisfied and no published run exists.
* #22 — verified copy before any tree-mutating process — fired at least three times since the 2026-08-19 widening without the rule reaching any prompt.
* #25 — Smoothed synthetic DEM — 'any time; cheap' is satisfied, though the fixture is now a CI/production input and the scale is unmeasurable today.
* #33 — corpus CSV bytes not hash-pinned — the named 'natural fit' came and went at E3.4, taking only the run-level half.
* #36 — CI hygiene (minor) — 'next CI edit' fired twice (2b477de, 96e3d93) and neither touched it.
* #37 — the origin audit's coverage boundary — the deadline expired at Phase-2 closeout and the gap is now wider, with demo.py and three siblings tracked but outside the walk.
* #40 — Two E3.1+2 date labels in surfaces/ — the trigger fired twice (TAX.1 c6938a0, E4.2 4d1ddcb) and the labels are untouched.
* #41 — Narrow write_surface's signature — both limbs fired (HASH.1 landed, writer.py edited at E4.2) and nothing was narrowed.
* #43 — LITERATURE's evidence requirement has NO OBSERVER — the trigger lapsed at G.3 and G.2, which shipped cited LITERATURE values with zero observers.
* #46 — the THEOREM test's tolerances — clause 1 was already false when written: the theorem is cited in five places outside the walkthrough, including to a user.
* #55 — configs the suite never exercises — the gitignore observer's 'any time, cheap' condition holds and no check-ignore test exists anywhere.
* #58 — the committed corpus manifest diverges from every fresh build — the divergence is live today across four fields, including the superseded AOI.
* #59 — live sites still calling the AOI a placeholder or the context layer a fixture — every cited site survives after G.2 made them false.
* #61 — Postgres/PostGIS parked until Phase 5 — Phase 5 arrived and is effectively complete on Track E; the parking condition expired unnoticed.

### C
* #43 — LITERATURE's evidence requirement has NO OBSERVER — refutation failed: the negation fixture landed at eb0cbd4 and was mutation-verified independently, leaving one docs-scoped closing commit.
* #44 — claim.py's runner-vs-record branch raises NameError — refutation failed: the bug reproduces live through the public API and the remedy is one identifier plus the fixture base already at tests/test_claim_guard.py:85.
* #45 — a PASSING pre-registration gate puts a timestamp INSIDE the content hash — refutation failed: both red and green halves were measured with the suite's existing PRE_REGISTERED_CONTRACT, no Track-G value required (scope: two render sites, not one).

### OVERLAP
* #43 — LITERATURE's evidence requirement has NO OBSERVER — live (its trigger lapsed at G.3/G.2), possible (one fixture, no data), and unnoticed (the box at docs/BACKLOG.md:1623 still reads '- [ ]' after the fix landed).

Of 62 swept entries, 30 have a trigger that names something adjacent to rather than required by the work (A), 24 have a trigger whose condition is already satisfied today (B), 3 survived refutation as genuinely doable now (C), and exactly 1 — #43, the LITERATURE evidence observer — appears in all three lists.

**Two defects the sweep REPRODUCED LIVE while refuting** — reported, not
fixed, per the task's instruction:

* **`claim.py`'s runner-vs-record disagreement branch** raises
  `NameError: name 'manifest' is not defined` through the public API — built
  from the entry's own prescribed fixture and called. A guard that crashes
  instead of refusing.
* **The pre-registration timestamp**: two `RunManifest`s differing ONLY in
  `scores_first_visible` (2026-08-19 vs 2026-08-20) both come back eligible
  with 6/6 preconditions, using the suite's existing `PRE_REGISTERED_CONTRACT`
  — no Track-G value needed to demonstrate it.

## 4. The closing-check proposal, with its cost measured

The task asked whether every approval should list EVERY entry whose trigger is
now true, computed from the entries. **Measured before deciding** (convention
6): this sweep cost **33 agents, ~3.5 M tokens, 998 tool calls, ~40 minutes**
of wall clock — because judging "is this trigger true?" means reading the
entry, the files it cites and `git log`, and because the refutation pass was
load-bearing (23 of 26 claims died there).

**Not adopted at that price per approval.** An approval that skipped it under
time pressure would be indistinguishable from one that ran it clean — the same
failure shape as the trigger it is meant to catch.

**Adopted instead, ascending cost:** (1) the **writing rule** — ask what would
make the WORK possible, and if the answer is "nothing", write a PRIORITY not a
trigger; free, and it prevents the class at source. (2) **Say "any time" out
loud** — 9 of 62 entries already do, and they need no sweep to find. (3) A
sweep at **phase boundaries, not per approval** — ~40 minutes is affordable a
few times per phase and absurd per task; the E2.X disposition audit is the
precedent.

**Reported rather than hidden: a mechanical check will not work here.** Only
**24 of 62** triggers name an event a script could evaluate; **35 are
judgement** and **3 have no trigger line at all**. A test over the 24 would
leave the majority unwatched while reading as coverage — coverage-that-isn't,
applied to the BACKLOG itself.

## 5. Test inventory

| Test | Asserts | Rule it enforces |
|---|---|---|
| `test_audit_reports_literature_declarations_missing_their_citation` | a citation-less and a whitespace-citation LITERATURE declaration are both reported BY NAME; a located one is not; the reported set is exactly those two | LITERATURE's evidence bar — the branch's only observer |

## 6. What is deliberately missing

* **Empty vs missing citation stays collapsed.** Reported above, pinned, not fixed.
* **The sweep fixed nothing.** Lists A, B and C are reports; no entry was
  re-triggered, closed or edited on their account.
* **The 30 mismatched triggers are not rewritten.** Rewriting them is a
  separate pass, and doing it inside the task that named the class would have
  meant changing a rule and its subjects in one commit — the same objection
  TAX.1 recorded when it declined to fold LITERATURE's observer into a rule change.
