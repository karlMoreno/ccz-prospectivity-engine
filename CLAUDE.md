# CLAUDE.md — CCZ Prospectivity Engine

This file is read automatically by Claude Code at the start of every session.
It encodes how this project must be built. Follow it unless I explicitly override
a point in the conversation.

---

## What this project is (one paragraph)

An open, reproducible modernization of **ISA Technical Study No. 6 (2010)**: for one
Clarion-Clipperton Zone (CCZ) study area, predict polymetallic-nodule abundance
(kg/m²) from an openly-sourced sample corpus + terrain covariates, with honest
uncertainty, an economic minability layer, a provenance manifest, and a benchmark
comparison against the TS-6 2010 surface. Two people build it: **Track E** (engineer,
the code) and **Track G** (geologist, the data + science). They are decoupled by a set
of frozen **contracts**. The authoritative specs are:

- `Proposals and contract V3/CCZ-Prospectivity-Engine-Alpha-Proposal-v3.md` — the build
  plan (phases, scope, requirements).
- The seven contracts (frozen data/interface shapes) — **treat these as ground truth**:
  - **Canonical (what the code reads):** `docs/contracts/` (schema, `covariates.yaml`,
    contracts README) + `data/` (`config/normalization.yaml`, `sources/source_queue.yaml`,
    `aoi/study_area.geojson`, `ts6/ts6_reference.yaml`, `economics/scenarios.yaml`).
  - **Authoring copies (Karl's source documents, not read by any code path):**
    `Proposals and contract V3/Contracts_v3/`.
  - Path corrected 2026-07-29 (P3): this file previously pointed at
    `phase0-contracts-v3/`, which has never existed in the repo.

If anything I ask conflicts with those documents, say so and ask before proceeding.

---

## The single most important rule: STOP AT PHASE BOUNDARIES

Build **one phase at a time** (Phase 0 → 1 → 2 …, per the alpha proposal §10). At the
end of each phase:

1. Summarize what you built and how it maps to the phase's exit criteria.
2. Run the tests / CI and show me they pass.
3. **STOP and wait for my review. Do not start the next phase until I say go.**

I am the engineer of record and must understand every part of this codebase (I have to
defend it to grant reviewers). Never accumulate code I haven't reviewed. Prefer many
small, reviewable steps over one large leap.


- At the end of each phase (and each significant task), also write or update
  `docs/walkthroughs/<phase>.md`: reading order, ASCII architecture diagram,
  per-file explanation, a test inventory table (what each test asserts in plain
  English + which contract rule it enforces), how to hand-check it manually,
  what's deliberately missing, and what the next task will add.

---

## Design-pattern discipline (my standing preference)

- Use explicit, named **design patterns** for the architectural seams, and **explain in a
  comment which pattern is used, for what, and why** — right where it's implemented.
- The patterns this project expects (from the proposal):
  - **Strategy** — swappable implementations behind an interface: `TerrainSource`,
    `SampleSource`, `ProxySource`, `Estimator`, `EconomicModel`, `TS6Reference`,
    and (ingestion) `SourceAdapter`, `AbundanceNormalizer`.
  - **Template Method** — fixed sequences: `IngestionPipeline.run()`
    (fetch→adapt→normalize→dedup→validate→append) and `ProspectivityEngine.run()`
    (ingest→features→CV→predict→uncertainty→economics→compare_to_ts6→manifest).
  - **Adapter** — one `SourceAdapter` per source-family → the master-observation schema.
  - **Specification** — dedup + quality rules as small composable predicates.
- "Program to an interface, not an implementation." Adding a data source, a model, a
  covariate, or a whole new body (the future lunar port) should mean **adding a class,
  not rewriting the pipeline.** If a change forces a pipeline rewrite, stop and flag it.

## Documentation & explanation style

- When you explain architecture or flow (in comments, docstrings, `docs/`, or chat),
  include a small **ASCII UML / box diagram** so I can visualize it. This is a hard
  preference, not optional.
- Keep prose explanations tight. Diagrams + short paragraphs over walls of text.

---

## Scientific-integrity rules (these protect the model — do not violate)

These come from the contracts (`master_observations.schema.json`, `normalization.yaml`)
and are the whole point of the project. Encode them in code + tests, not just docs.

- **Evidence classes are sacred.** Every observation is tagged exactly one of
  `MASS | COUNT | COVER | GRID | GRADE`. Never untagged.
- **Train on `MASS` only.** `SampleSource` selects rows where
  `evidence_class == MASS AND abundance_kg_m2 is present AND is_open == true`. Nothing else.
- **`COVER` is NEVER converted to kg/m².** Percent cover is a covariate, never a bare
  abundance value. If you ever find yourself writing cover→mass into `abundance_kg_m2`,
  that is a bug — stop.
- **`GRID` is a prior/benchmark, never a training station** (TS-6, Washburn). It must be
  flagged `observation_or_prediction != observed`.
- **`COUNT` → kg/m² only via a recorded `mean_nodule_mass_g`**, with the assumption and its
  uncertainty written into `derivation_formula` / `quality_grade`.
- **Provenance is mandatory.** Every derived value records its `derivation_formula`; every
  row traces to a `source_id` in `source_queue.yaml`. Only `is_open == true` sources may
  enter a "published" run.
- **Spatial cross-validation is mandatory** for any model claim. Never report a plain
  random-split score. Always run the mean baseline alongside. A run cannot be marked
  VALIDATED if spatial CV did not run.
- **Uncertainty is always paired** with any prediction surface. Never emit a prediction
  without its uncertainty.
- **Honesty over impressiveness.** If the data is thin or a result is weak, say so plainly.
  Never fabricate values; use clearly-labeled placeholders ("illustrative only") and tell me.

---

## Data origin: every value is classified

Every value in this repo declares HOW IT CAME TO EXIST HERE, using the five-member
vocabulary in `engine/prospectivity/provenance/origin.py` (P2.0). This section is the
durable home of the standing decisions; the reasoning lives in
`docs/audits/2026-08-08-origin-vocabulary-audit.md` and `docs/walkthroughs/P2.0.md`.
All five evidence requirements are ENFORCED, which is checkable:

- **MEASURED** — a measurement dataset this repo holds. Evidence: the file present with
  its recorded SHA-256 matching the bytes → **production guard** (`_require_proven_measured`).
- **DERIVED** — computed from MEASURED inputs. Evidence: the derivation formula or the
  artifact recording it → **audit resolver** (`tests/test_data_origin_audit.py`).
- **LITERATURE** — a value from a publication, no file in hand. Evidence: a citation that
  LOCATES the number (document + table/section/page; "TS-6" alone is insufficient) →
  **audit resolver**.
- **SYNTHETIC** — generated by a deterministic recipe. Evidence: the generator's import
  path **AND (a seed OR a recorded determinism basis)** — the only thing separating a
  generated value from hand-typed values under a `synthetic_*` filename → **audit
  resolver** (`tests/test_data_origin_audit.py`: the generator check, the
  seed-or-basis check, and `MIN_DETERMINISM_BASIS_CHARS` against a bare basis).
  *Widened at TAX.1 (2026-08-21) and NOT a loosening: the old rule required a seed, which
  a SYNTHETIC-BY-INHERITANCE artifact cannot have when its generator is genuinely seedless
  — E3.1+2's kriging surface is synthetic because its DEM is, and ordinary kriging records
  no seed. That artifact was declared honestly and could not pass, while a FABRICATED seed
  would have. A seed and a determinism basis are two answers to one question — what makes
  this reproducible — and the old rule admitted only one. The basis must NAME WHAT MAKES IT
  DETERMINISTIC; a bare "deterministic" is refused by name.* Nothing is renamed: the
  `synthetic_*`/`src_synthetic_*` misnomers are recorded in docstrings, and no code may
  infer origin from a name, title, or path — declaration or nothing.
- **AUTHORED** — someone typed it. Evidence: `author:` from the `ALLOWED_AUTHORS`
  allow-list → **audit resolver**. `author: unrecorded` is NOT available to new work; it
  names the frozen set of pre-P2.0 files in `tests/test_data_origin_audit.py`, which can
  only shrink.

**Propagation:** `combine_origins` returns the LEAST-real input — a real corpus does not
launder a synthetic terrain — and file-level and run-level origins are COMPUTED with it
(entries → file, artifacts → run), never hand-written.

**The authoring rule (operative in every session):** when you create a file containing
values — a fixture, a contract default, an example row, a stand-in parameter — you
declare its origin IN THE SAME EDIT, never afterwards. A value whose origin is added
later is a value someone reconstructed from memory. If you cannot determine the origin
of a value you are about to write, that is the STOP-on-ambiguity condition, not an
invitation to pick the most plausible label.

**The prohibition:** nothing reachable from a production build path may be other than a
MEASURED declaration with COMPLETE evidence, and production corpus inputs live under
`data/sources/`. The guard checks the proof — a hash over real bytes — never the claim.
Watermarks derive from declarations, default-ON: absence of proof produces a watermark,
never a clean render.

Why each rule exists (evidence, not assertion): `[06]` and `[18]` reached
`REAL_ADAPTER_BUILDERS` as fabricated fixtures and were caught by a person reading a
file, not by a test; `data/fixtures/native/`'s fabricated CSVs sat on the real-data side
of both path guards until the 2026-08-08 audit; and a MEASURED label on an undownloaded
source is indistinguishable from a fabricated one without its hash — which is why the
guard checks the proof and not the claim.

---

## Dependency & scope discipline (keep it small)

- **Minimal dependencies.** This runs on a laptop in minutes. Approved stack only:
  Python 3.11+, `rasterio`, `numpy`, `pandas`, `geopandas`/`shapely`, `scikit-learn`,
  `scikit-gstat`/`pykrige`, `richdem`/`xarray-spatial`, `pydantic`, `pytest`,
  `pangaeapy` (ingestion), `fastapi` (read-only API, E5.1). **The viewer (E5.3) is ONE
  static HTML page on MapLibre GL JS + deck.gl, loaded from a CDN with pinned versions
  and SRI hashes — no npm, no node, no build step (decided 2026-08-22; BACKLOG §7).**
  Ask before adding anything else.
- **No** Kubernetes, task queues, Redis, clusters, or an upload-and-compute web backend.
- **Do not bulk-install agent/skill harnesses or plugins.** Add tooling deliberately, one
  piece at a time, only when a concrete need appears.
- Stay inside the current phase's scope. If something feels like Phase B/C, Option-B
  proxies, multiple study areas, or the lunar port — it's out of the alpha. Flag it, don't build it.

---

## Reproducibility rules

- Hash-pin dependencies (lockfile). Content-hash every ingested input; record it.
- Every model run emits a **provenance manifest** (inputs + hashes, params, seeds, CV
  strategy + scores, baseline scores, TS-6 agreement, output hashes).
- Set and record random seeds. Same inputs + seed → same outputs.
- CI runs the full suite every push. It exercises the REAL ingestion path (the two
  hash-verified PANGAEA `.tab` files in `data/sources/`), the real 108-row corpus and
  35-station matrix over a **synthetic DEM**, the estimators, spatial CV, and the claim
  guard. The **synthetic fixtures** are the concurrency safety net — keep them working.
  (Corrected at P2.CLOSE, 2026-08-20: this line said CI runs "on synthetic fixtures",
  which understated it by two phases and was the sentence `ci.yml`'s stale comment quoted.)

---

## Testing conventions (a test that guards nothing is worse than no test)

Three separate audits have now found the same class of defect in this repo: a test
that **counts as coverage while guarding nothing**. It is worse than a missing test,
because a missing test is visible. These rules exist because each one was learned the
hard way — the evidence is cited, not asserted.

1. **A test's name must describe what its assertions verify** — not what the author
   intended to verify, and not the rule the test sits near.
   *Evidence:* the test-name audit (2026-07-30) found **17** names claiming more, less,
   or other than their bodies checked. Two could have caused a wrong action rather than
   mere confusion: `test_mass_rows_are_training_eligible` stated a rule that is FALSE
   since P1 (a flagged MASS row is not eligible) and contradicted
   `test_sample_source.py`'s opposite assertion; and
   `..._reconciles_exactly_for_at_least_31_of_36_events` invited a maintainer to
   "fix" a failure by loosening toward 31, quietly erasing the documented D8 residual
   the body exists to pin.

2. **A test asserting a rule must not load its data through the class that enforces
   that rule.** It can never observe a violation — the loader raises first, so the
   assertion is decorative and the failure it reports names the wrong thing.
   *Evidence:* E1.5 found `test_observation_schema.py`'s COVER/GRID assertions read the
   corpus via `Observation(**row)`, whose validator forbids exactly those violations.
   Fix: assert against the raw artifact (see `tests/test_corpus_invariants.py`, which
   reads the corpus CSV as strings with no Pydantic in the path).

3. **An assertion that something is "unchanged" must compare full state**, not selected
   fields. Same for "identical", "adds nothing", "survives untouched".
   *Evidence:* E1.5's `..._adds_nothing` compared row count and IDs only, and passed
   while every merged row's `notes` tripled on re-runs — one of them recording the row
   as a duplicate of ITSELF.

4. **A hand-computed fixture must separate the claimed statistic or rule from its
   neighbors.** A fixture whose SYMMETRY makes distinct claims coincide verifies the
   value while being unable to distinguish the statistic — a different defect than
   coverage-that-isn't, because the assertion is real and the fixture is blind.
   *Evidence:* on `[2, 4, 6]`, SD, MAD, and half-range are all exactly 2.0, and a
   spread-statistic swap survived every hand-computed test (E2.1 MB9; fixed by
   `[13, 11, 8, 9, 9]`, where SD, SE, MAD, half-range, and ddof=0 all separate).
   The same idea in different clothes: E2.0-2's `shared_cell_count == len(stations)`
   is numerically true on the real corpus, so only a constructed mixed-occupancy
   fixture could catch the hardcode. When building a fixture, state in its docstring
   which neighboring claims it separates.

5. **A correction is verified against the PRIMARY SOURCE, not against the
   finding that prompted it — and a remedy is written from the full
   measurement, not the part the finding named.**
   *Evidence:* the E2.4 doc fixes introduced FOUR false claims while correcting
   true findings, none caught by re-reading the findings and all caught by a
   verification pass over the CORRECTIONS. Two show the two halves of the rule:
   a correction cited `ff2d0c6` as the mutation-restore baseline when the guards
   those mutations target exist only in `64679a9` (checkable in one command:
   `refusal_phase` is ABSENT from `ff2d0c6`'s runner and present throughout
   `64679a9`'s — 7 occurrences on 6 lines, a count worth stating precisely in a
   rule about stating things precisely); and a remedy naming only the gap pins would have left the test
   red at 6 of 8 seeds, because the ratio ceilings — which the finding had not
   named — are the more fragile assertion.

   **A CORRECTION PASS IS SCOPED TO THE CLAIM, NOT THE ENTRY** (added at the
   C8.1 approval, 2026-08-20). Correcting one sentence in a document does not
   inspect its neighbours, and a reviewer who has just fixed an entry feels
   like that entry has been checked.
   *Evidence:* the E2.5-approval pass corrected `BACKLOG.md` §2's
   admissible-set conflation — a sentence in that entry's opening paragraph —
   and left standing, in the FOURTH AND LAST BULLET OF THE SAME ENTRY, the
   tripwire clause asserting a loader refusal that did not exist — the clause the E2.5 prompt had inherited its false premise from.
   The fix landed in the right entry, on the wrong sentence.

   **AND: BEING IN THE REPO IS NOT EVIDENCE — IT IS ONLY PERSISTENCE.** That
   false premise was not misremembered when a prompt was written; it was
   WRITTEN INTO the repo by an approval (`009835e`, 2026-08-18) and read back
   as corroboration one day later. All three provenance channels this project
   built — VALUES (the origin taxonomy), INSTRUCTIONS (tracked prompts and
   handoffs), VERDICTS (the ledger) — are repo-resident, and **none of them
   distinguishes a claim that was VERIFIED from one that was merely
   RECORDED.** What made this one refutable was the ATTRIBUTION convention:
   the bullet self-attributed "(Karl, E2.X approval, 2026-08-14)", so it
   traced to a person and a date instead of reading as ambient repo fact.
   That convention is carrying more weight than anyone assigned it — with one
   measured limit: its date is when the claim was STATED, not when it entered
   the repo (four days apart here), so it buys traceability, not chronology.

6. **When a finding becomes a fix, re-run its measurement at the FIX's
   stakes, not the finding's.** A measurement adequate to DETECT a problem may
   be inadequate to GROUND the remedy — and it will reproduce perfectly while
   being too small, which is what makes it convincing.
   *Evidence:* P2.CLOSE commit 1. The E2.4 audit's 8-seed sweep reproduced
   EXACTLY, down to which seeds fail which pin, and it supported a remedy —
   "assert the direction and `base − RF >= 0.15`, both 8/8" — that a 40-seed
   sweep showed would have **shipped RED**: `base − RF >= 0.15` fails at seed
   4, which is in the test's own seed list. The same sweep showed the baseline
   floor holds at only **29/40**, a fragility the 8-seed finding never
   surfaced because the floor passed 8 of 8 there. Only the DIRECTION survived
   40/40, and it is what the test now asserts.

   **This is ADJACENT to convention 5, not a special case of it — neither
   absorbs the other.** Convention 5 asks whether a claim is TRUE against its
   primary source; the 8-seed measurement was true, reproducible, and
   correctly reported. This asks whether the evidence is SUFFICIENT for the
   weight about to be placed on it. A finding needs only enough resolution to
   show something is wrong; a fix needs enough to show what is right, and the
   second bar is higher precisely where the first was cleared convincingly.

7. **`violations = [... if cond]; assert not violations` is GREEN when `cond`
   breaks** — an empty list passes. Prefer a POSITIVE FULL-STATE COMPARISON
   (what satisfied the rule vs everything examined), and where the
   collection's SIZE carries the claim — a multi-seed property, an every-fold
   property — assert the size too, because shrinking the input shrinks both
   sides of a comparison silently.
   *Evidence:* P2.CLOSE commits 1 and 2, mutations M3 and M4 — see the
   inventory row below for the three citable instances. Two independent
   drafts in ONE batch had it, which is why it is written as an idiom to
   avoid rather than an incident.

Corollaries worth keeping in mind:

- **A fixture must be able to distinguish the claim from its negation.** If every
  fixture row shares a value, a test asserting that value is read "per row" cannot fail
  when the code hardcodes it.
- **Aggregate assertions do not prove per-item claims.** A total and a set of classes
  are satisfied by a skewed distribution; group and assert per item.
- **Prefer a mutation check to a green run.** Break the thing on purpose, watch the test
  fail, restore it. This project's established practice, and it is how every guard above
  was verified.
- **The check itself is in scope.** A probe, a fixture or a harness can carry the
  same defect as the code it examines — E2.4's audit proved its strongest claim on
  a fold order where the failure it was testing for could not occur, and its
  mutation harness silently made no backups. Run the rule against the instrument.
  *Harness findings are now ×5 (E2.2's reviewer restore; E2.4's session harness
  with no backups; HASH.1's H-M2, an import error the harness's line filter
  counted as 0 failed; E4.1's B-M5, reported caught by the wrong test and by
  three including its own when re-applied by hand; the E4.2-approval
  background suite run whose output file was EMPTY with exit 0) — every one
  the harness, none the code. A mutation that "passes" for an unexamined
  reason is a survivor until the reason is read; a mutation that FAILS for an
  unexamined reason is too; and a background run with an empty output file is
  indistinguishable from a run with nothing to say — confirm in the
  foreground. FIXTURE findings are a separate column (the single-source
  tamper row): do not conflate them.*
- **A check scoped by what is actually there observes what nobody predicted.**
  The counterpart to coverage-that-isn't: `output_hashes` is recomputed over
  the DIRECTORY LISTING and the emitter refuses two files under one key, so
  two output-location mistakes in two tasks were caught instantly — E4.2's
  rasters written beside the surfaces (the listing), E4.3's economics
  `data_origin.yaml` colliding by basename (the key refusal). A check against
  a list the writer declares would have passed both times.
- **Assert a property END TO END, not at the site where its cause was removed.**
  Removing a defect's cause and verifying there cannot see the same defect
  reintroduced downstream by the removal itself. *Evidence:* HASH.1 commit 2
  removed the DEM path from the stack substance and its first draft echoed
  `dem_path` into the run's chain block — inside the run substance — so the run
  hash still moved with the directory; the two-tree measurement showed
  `provenance_chain` as the single differing field. One exact instance; the
  adjacent prior is E3.4's "every output file" (a claim at the emitter, refuted
  by the downstream count). The same reason E3.4's chain assertion recomputes
  every link rather than trusting the site that produced it.

### The defect classes this project keeps finding, with their counts

Created at the E2.4 doc-fix approval (2026-08-19) because the four rules above
cite their evidence individually and nothing carried the TALLY — and a class
that recurs is a different fact from a rule that exists. Counts are derived
below, not asserted; each instance is citable.

| Class | Count | Instances |
|---|---|---|
| **Coverage-that-isn't** — a test that counts as coverage while guarding nothing | **×6** | the test-name audit's 17 misnamed tests (rule 1); `test_observation_schema.py` reading the corpus through the validator that forbids the violation (rule 2); `..._adds_nothing` comparing row count and IDs while every merged row's `notes` tripled (rule 3); `test_covariate_stack.py`'s determinism test, which varies the output dir (not in the substance) and holds the DEM path fixed (in it) — passing since E1.4 under PROVENANCE.md's most-cited invariant (E2.4 audit row M(b)); **and a SUB-PATTERN with two instances of its own — THE UNREACHABLE CHECK BELOW A STRUCTURAL GUARANTEE**: (5) C8.1 deleted an `if declared.data_origin == "AUTHORED"` branch from the claim guard once the LOADER refused AUTHORED outright, and (6) E3.1+2's surface builder re-checked non-pairs, non-finite sd and negative sd that `Estimator.predict()` — a FINAL Template Method — already refuses. **The shared cause is worth more than either instance: defense-in-depth added BELOW a structural guarantee is not redundancy, it is unreachable code that LOOKS like a guard**, and a reader counts it as protection that is not there. Both were caught the same way — by trying to TEST the branch and finding the guarantee fired first — which is why the rule is "test the refusal, and see which layer answers". E3.1+2 kept only the check the ABC cannot make: one entry per cell REQUESTED, since only the caller knows how many it asked for |
| **Fixture degeneracy** — the fixture cannot separate the claim from its neighbours or its negation | **×5** | `[2, 4, 6]`, where SD = MAD = half-range = 2.0 (E2.1 MB9); `shared_cell_count == len(stations)`, true on the real corpus (E2.0-2); the rank-4 RF fixture, blind to `aggregate_leaves_first` (E2.3 review); the metrics fixture where mean\|e\| = median\|e\| = 2.0, blind to a mean→median swap in MAE (E2.4 §1 review); **K3-A** — the audit's own stale-refit probe, run on a fold order where no stale state could exist (E2.4 audit) |
| **Deferral without a landing spot** — a disposition that survives only in a transcript | **×4** (the prompt proposing this table said ×3; the fourth is named here) | three of 22 review findings at the E2.X disposition audit; **and P2.C + the `SESSION_STATE.md` question at E2.4 §0 finding C**, which existed only in a planning transcript AFTER the deferral rule was written — the rule's first post-adoption instance |
| **Correction drift** — a fix, a remedy, or a PREMISE asserts something the primary source does not support | **×14** (of the first 6, 3 caught PRE-COMMIT; of the five E3.4 instances, 4 refuted at the premise check and 1 — the session's own — caught post-commit by a measurement; the two HASH.1 instances both refuted at the premise check, one of them deciding a design; E4.1's one is the session's own, caught post-commit by `git status`) | (a) the four false claims in the E2.4 doc fixes (rule 5 above), caught pre-commit by a verification pass over the corrections; (b) **the E2.5 prompt's tripwire inventory** asserted that Contract 8's loader "already refuses an AUTHORED acceptance threshold" — there is no `acceptance_thresholds` slot at all, and the loader has no origin-based refusal. The deferral was DESIGNED in P2.A ("`acceptance_thresholds` arrives with E2.5 … a field with no consumer is a field nobody has tested the meaning of") and recorded in the contract header, then asserted two tasks later as already built. **The site is new: a task PROMPT's premises, not a correction's text** — and it was caught only because the session applied rule 5 to the prompt rather than only to its own edits; (c) **this very commit** — the sentence recording (b) claimed P2.C carries "two `[KARL — DECIDE]` points"; the block carries ONE. Caught by grepping the block rather than re-reading the sentence. Karl's approval specified ×2; the third is counted here because the row's counts are DERIVED and a tally that omits the drift produced while writing the tally is the defect it names; (d) **C8.1's walkthrough** claimed the false premise "was written into the BACKLOG five days earlier", conflating the day the tripwire was STATED (2026-08-14) with the day it was COMMITTED (2026-08-18, `009835e`) — caught pre-commit by `git log -S`, inside the table that is itself about mis-dated premises; **(e) the TAX.1 prompt's §2** said the origin audit's walk "may sit outside" the outputs directory — it does not, and **E3.1+2 had already measured that**. The cause is the sharpest yet: **a qualifier TRUE IN ONE CONTEXT** (the coverage-boundary entry, where the boundary genuinely was uncertain) **was reused in another without re-checking**, while the measurement refuting it sat in the repo. It is the laundering shape one scale down — a recorded claim read back as corroboration — and it made the task look harder than it was; **(f) the E3.3 prompt** said Contract 6's digitization-uncertainty field "is null today" — NO SUCH FIELD EXISTS, and absent vs null is this project's own distinction with different remedies. With (b), this makes a RECURRENCE with two instances: **a deferral designed in one task, remembered as built (or existing) in a later one by the same author** — `acceptance_thresholds` (P2.A design → E2.5 premise), `digitization_uncertainty` (TAX.1-approval decision → E3.3 premise). The remedy that keeps working is verifying the field's state before writing against it, which is why both consumers are THREE-STATE accessors instead of null checks; **(g)–(k), all at E3.4 (2026-08-22), count DERIVED from the record:** (g) the spec's closing list said the LITERATURE observer gap "now has two Phase-3 arrivals riding on it" — TRUE WHEN WRITTEN (E3.0 approval), stale by use: TAX.1 had settled TS-6 as DERIVED, so one arrival remains; (h) the same list said "the AOI's trigger moved to Checkpoint 1" as work to do — the E3.0 approval that produced the list had already done it; (i) the E3.4 prompt named PROVENANCE.md's "shape fixed when the emitter is built" line as a sweep target — **E2.4's own sweep had already rewritten it**, and the sentence was reused verbatim from E2.4's sequencing prompt: instance (e)'s shape again, a qualifier true in one context carried into another; (j) the prompt asked the manifest to carry a "refusal state" for a null `digitization_uncertainty` — **no such state can exist downstream of E3.3's refusal**, which RAISES there: a requested output the primary source forbids; (k) **the session's own:** commit 1's chain block said the path-hash limit reaches "every output file" — measuring it gave 11 values, not 12, because `data_origin.yaml` quotes no hash; a remedy's SCOPE stated beyond its measurement, caught post-commit by the count the prompt's §4 suggested. Of the five, four were prompt premises refuted at the premise check before any code acted on them; (k) reached a commit (`31dc10b`) and was corrected at `e257542`; **(l) the HASH.1 prompt** assumed a plain present-fields rule would leave both committed hashes alone and made that a STOP condition — measured false (the E3.4 re-stamp hashed five nulls; `exclude_defaults` moves the corpus too), and it DECIDED the design (the legacy mode); **(m) the HASH.1 approval** named E3.1+2's mask-union check as the first instance of "asserted at the cause site, not end to end" — the test recomputes the union from the rasters on disk, and its note was a fixture degeneracy; the nearest prior is E3.4's "every output file". Both refuted at the premise check; **(n) the E4.1 walkthrough's own §0** recorded the Phase-4 prompts file as "tracked, committed with E4.0's report" — it exists on disk and is UNTRACKED; the session verified EXISTENCE (`ls`) and not TRACKING (`git ls-files`), the E3.0 situation recurring one phase later, caught by the commit's own `git status` and corrected the same day |
| **Single-source tamper** — a recomputation guard whose fixtures forge ONE witness: it proves the emitter does not read THAT witness, and a multi-source copier passes it. **The rule: a recomputation guard is only as strong as the most CONSISTENT forgery its fixtures produce. Forge every derived witness consistently, and leave only the ground truth dissenting.** NOT coverage-that-isn't (the tests could observe a violation) and NOT fixture degeneracy (no symmetry makes claims coincide): three agreeing witnesses and one dissenting ground truth, and the ground truth the only thing nobody checked against | **×2** (1 caught by reading pre-commit, 1 by mutation) | **(a) E3.4 commit 1**: every refusal test made two RECORDS disagree — which a copying emitter also catches — found by reading and closed pre-commit with the separating fixtures (a tampered substance whose quoted hash still agrees everywhere; a forged benchmark hash quoted consistently); **(b) E4.3 E-M6**: `n_minable` read from the raster TAG instead of the pixels survived the first mutation run because the only count-tamper test forged the record alone; the separating fixture forges tag, record, result AND the record's sha256 to agree while the pixels dissent. **Its second layer:** that fixture's first draft ERRORED on the real code (`IGNORE_COG_LAYOUT_BREAK`), so its "catch" was not one until it passed there — a fixture that fails for the wrong reason is not an observer |
| **Vacuous collection** — an idiom whose failure mode is SILENT EMPTINESS: the check is capable of observing the violation, but the collection it reports through can be emptied or shrunk without the assertion noticing | **×3** (all caught by mutation, none escaped) | **(a)** P2.CLOSE commit 1, M3 — `violations = [... if not r[name] < r[BASE]]` with `assert not violations`; breaking the CONDITION to `if False` left the direction assertion unable to fail, on the test whose whole purpose was that direction; **(b)** P2.CLOSE commit 2, M3 — the same shape in the F-6 doc-lint (`missing = [...]`), written independently an hour later, which is why this is an idiom and not an incident; **(c)** P2.CLOSE commit 1, M4 — the SILENT-SHRINKAGE variant: with the fix in place, cutting `LEAKAGE_SEEDS` to one seed still passed, because `expected` derives from the same list and both sides shrank together. **Distinct from its neighbours:** not coverage-that-isn't (the check CAN observe the violation — it is the reporting channel that empties), and not fixture degeneracy (no symmetry, no coinciding statistics; the fixture is fine) |

The counts are the point: **coverage-that-isn't and fixture degeneracy are not
historical, they are recurring**, and the two most recent instances of each were
found in the CHECKING apparatus (a determinism test; an audit probe), not in the
work under test. Correction drift's second instance moves the class one level
further out again — into the PREMISES a task is scoped on — which is why rule 5
says "the primary source" rather than "the finding": a premise has no finding to
re-read, only a repo to check. Its third arrived inside the commit that wrote
its second down — which is the most economical demonstration the file has that
the class is not a story about past carelessness.

**The newest class is the only one whose instances are all from a single
batch, and that is the point about it:** two independent drafts reached for
`assert not violations` within an hour of each other, so it is a REFLEX
rather than a lapse — the reason convention 7 states an idiom to avoid
instead of citing an incident. It is also the only class so far with a 100%
mutation-catch rate and zero escapes, which is what a defect class looks like
when the instrument that finds it is run as a matter of course.

**The ratio is the argument for the verification step: 3 of the 4 were caught
PRE-COMMIT, and the one that was not — (b) — is the one that reached a task
prompt and cost two tasks to unwind.** So an escapes-only tally would read
ONE, and a tally that counted only what escaped would trend toward zero
precisely BECAUSE the check works, then be cited as grounds for dropping it.
This row counts OCCURRENCE, deliberately: the number is a measure of how
often the class is produced, not of how often it survives.

---

## Workflow conventions

- **Research/read before writing.** Before implementing against a contract, read that
  contract file and restate its shape back to me in one or two lines.
- Write the **test alongside the code** (pytest). For the integrity rules above, the test
  is the enforcement (e.g. a test that fails if a `COVER` row ever gets `abundance_kg_m2`).
- Small commits with clear messages. One logical change per commit.
- When you finish a unit of work, show: what changed, why, the test result, and the
  ASCII diagram if the structure changed.
- If you're unsure about a geology decision (sampled area, wet/dry basis, mean nodule
  mass, which covariates matter), **mark it `[GEOLOGY — ISAAC]` and leave a safe default +
  a TODO** rather than guessing silently.
- **A phase-boundary status claim is DERIVED from the lane list and the open
  items, never asserted from memory of the plan.** *Evidence, ×2:* at the
  Phase-3 and Phase-4 boundaries the approval asserted "nothing substantial
  remains for Track E without Track G" and the repo refuted it both times —
  Phase 4's whole E-lane is placeholder-based by the proposal's own words,
  and Phase 5's E5.1/E5.3/E5.4 need no G input. The answer changed what
  happened next both times.
- **A review finding whose disposition is deferred gets its BACKLOG entry AT THE MOMENT
  OF DEFERRAL, written by whoever defers it — and review disposition rows append to
  `docs/audits/` at review time, not reconstructed at a phase boundary.**
  *Evidence:* the E2.X disposition audit (2026-08-14,
  `docs/audits/2026-08-14-e2-review-disposition.md`) found 3 of 22 review findings had
  survived only in a planning transcript; all three were deferrals without a landing spot
  ("note for whenever you next present"; "when the BACKLOG item gets done, both layers go
  in"; a trigger reading "after E2.0" that silently expired). The nineteen that landed all
  had an immediate home — a Section 0, a closeout item, a BACKLOG entry named in the same
  prompt that produced the finding. The rule's cleanest demonstration is its own adoption:
  the approval message that added it first proposed deferring it to P2.C — the exact
  pattern it forbids — and corrected itself in the same message.

---

## Repository layout (target — from the alpha proposal §12)

```
ccz-prospectivity-engine/
├── engine/prospectivity/
│   ├── domain/          # Observation/EvidenceClass, StudyArea, results
│   ├── ingestion/       # SourceAdapter + AbundanceNormalizer + dedup (Specification)
│   ├── terrain/ · samples/ · features/
│   ├── estimators/      # kriging, random_forest, mean_baseline
│   ├── validation/ · uncertainty/
│   ├── ts6/             # TS6Reference + compare_to_ts6()
│   ├── economics/       # EconomicModel + scenarios
│   ├── provenance/      # manifest emitter (run + corpus)
│   └── engine.py        # Template Method run()
├── services/api/        # read-only FastAPI (later phase)
├── apps/web/            # thin viewer (later phase)
├── database/            # migrations, fixtures
├── data/                # contracts live here (corpus/, sources/, config/, aoi/, ts6/, economics/, fixtures/)
├── docs/contracts/      # the seven contracts + README
└── docker-compose.yml · Makefile · README.md · CLAUDE.md
```

---

## Current status

- Phase: **5, Track E — IN PROGRESS. E5.0 (preflight, read-only) reported
  2026-08-22; E5.5 (the run harness) LANDED 2026-08-22 and RESEQUENCED
  FIRST — E5.0 found no viewer layer existed on disk (every surface was a
  pytest tmp artifact), so the lane order is now E5.5 → E5.1 → E5.2 → E5.3
  → E5.4 → E5.6 → E5.7. One command produces a run directory
  (`python -m engine.prospectivity.harness`, `docs/walkthroughs/E5.5.md`
  §3 for the layout); the manifest is at schema 4 with the full-data fit,
  the sd ranges and the training stations; suite 611 → 624. **The E5.2/E5.3
  stack decision is SETTLED (Karl, 2026-08-22): MapLibre GL JS + deck.gl from a
  CDN, one static page; Next.js DECLINED — GFW needs React for a product team
  and a component library, this needs one page (BACKLOG §7). Lane order
  E5.5 → E5.1 → E5.2 → E5.3 → E5.4 → E5.6 → E5.7.** E5.1 LANDED 2026-08-22:
  the read-only FastAPI (`services/api/`, `python -m services.api.app <runs_root>`)
  and the layer catalog (`/runs/{id}/layers`: 24 layers, the 72-cell grid with
  three states, the watermark forms kept apart, the verdict once). E5.2 LANDED
  2026-08-22: every layer exported as FLAT ARRAYS (Karl's decision, E5.0 §2 —
  700x smaller than polygons), the mask as null, the origin and the source's
  watermark form carried in the file and verified by the emitter against the
  pixels; the catalog's `data_url` per entry; a run directory is now 62 files
  / 2.75 MB. E5.3 LANDED 2026-08-23: the viewer — ONE static page
  (`apps/web/index.html`, MapLibre 5.24.0 + deck.gl 9.3.10 from a CDN with SRI
  hashes recorded in `services/api/web.py`), driven by a SERVED PRESENTATION
  MODEL (`GET /runs/{id}/viewer`, the named exception to 'the API computes
  nothing': bins, labels and states are rendering decisions); no tile basemap
  (a vendored public-domain coastline); context layers as a second class with
  their own origin and a FIXTURE rectangle; the 35 stations from the manifest.
  The page names no layer, model, axis or unit of this project (grepped); the
  DOM, rendering and interaction are UNTESTED and the walkthrough says so. First
  non-Python files in the repo, outside the audit's walk (confirmed). Suite 665.
  Next: E5.4, the honesty surface — awaiting Karl's review of E5.3.**
  Previous: **4, Track E — COMPLETE and APPROVED (E4.3 approved 2026-08-22;
  E4.0 → E4.1 → E4.2 → E4.3; suite 566 → 611 across the phase)**; Phase 3 Track E complete and
  approved (E3.4, 2026-08-22); Phase 2 (E2.5, 2026-08-19). (Minimal update;
  the full status refresh is the P2.C item in `docs/BACKLOG.md` §2.)
  **Phase 4's design contribution:** an economic artifact carries TWO
  watermark reasons as separate claims with separate expiry — terrain lifts
  at Checkpoint 1, economic parameters at Checkpoint 4 — because the origin
  lattice's single AUTHORED answer is correct and lossy. **What Checkpoint 4
  can review:** the machinery end to end and the fact that both scenarios
  cover the whole predictable domain (2,880/2,880; 347,707 km²) with an
  empty difference. **What it cannot:** an economic claim — no real Contract
  4 value, no GRADE, no recovery fraction, no recorded wet/dry basis; the
  claim verdict refuses on every design and the economics block says why a
  second time. **Track E is complete to the Phase-4 boundary, and what
  remains without Track G is DERIVED, not assumed:** G-FREE — E5.1 (the
  read-only API), E5.3 (the one-command run harness), E5.4 (CI end-to-end on
  fixtures — already mostly true: `ci.yml` runs the whole suite and
  `test_engine_run.py` runs the real composition inside it; a named
  artifact-producing job is what is missing); KARL'S DECISION — E5.2's
  Next.js viewer is outside the approved stack; KARL'S — E5.5 deploy;
  WAITING ON G — Checkpoints 1, 3, 4 and the AOI. Phase 5 planning opens
  with the E5.2 stack decision.
  **E4.2 (2026-08-22) is done:** the 12 footprint
  rasters and the 6 difference maps, on the surfaces' grid through the one
  COG writer, the two-reason verdict per reason on every file, the mask kept
  apart from the footprint, the difference's meaning ("a sensitivity map,
  not a resource map") in its tags — uniformly true and uniformly empty on
  today's surfaces, as stated in advance. **E4.1 (2026-08-22) is done:** Contract 4's loader,
  the per-reason watermark verdict (terrain ↔ Checkpoint 1; parameters ↔
  Checkpoint 4), and `CutoffEconomicModel` on confidence-level footprints —
  the measured output on today's surfaces is the whole domain under both
  scenarios and an empty difference, stated in advance, a property of the
  placeholder cutoffs, not the seafloor. **HASH.1 (2026-08-22) is done:** the hash scheme
  is shape-tolerant (present fields + `schema_version`; two legacy
  artifacts keep their hashes) and the path-hash defect is fixed (0
  directory-dependent hash values, was 11) — Checkpoint 1 is unblocked on
  Track E's side whenever Karl wants it. Starting E4.1 is Karl's call under
  the phase rule. **What Checkpoint 3 can review:** the
  machinery end to end (`ProspectivityEngine.run()` composes ingestion,
  features, CV, the guard, paired surfaces, the writer, the TS-6 comparison
  and the extended manifest on the real corpus over a synthetic DEM) and two
  real measurements (kriging within 0.5 kg/m² of the mean over 99.62% of its
  domain; RF's ~1,842-value surface inside [11.6, 26.8]). **What it cannot
  review:** a model claim — there is no publishable one, and the guard says
  so structurally (`docs/walkthroughs/E3.4.md` §5). Phase 0's scaffold +
  seven contracts, Phase 1's real ingestion (E1.1–E1.3 + the P1/P1b/P2/P3 review batches),
  terrain feature recipes (E1.4), and E1.5 are built and reviewed; Phase 2's preflight
  (P2.0 origin taxonomy, Contract 8, P2.B/P2.A), the training matrix (E2.0), the Estimator
  ABC + mean baseline + registry (E2.1), ordinary kriging (E2.2), and the quantile random
  forest (E2.3) are built and reviewed; the E2.0–E2.3 review chain is audited and closed
  (`docs/audits/2026-08-14-e2-review-disposition.md`).
- **Corpus state:** `data/corpus/master_observations.csv` holds **108 rows** (36 SO268
  box-core events × MASS/COUNT/COVER), of which **35 are training-eligible**. It is
  **single-source** (`[01]`+`[05]` merged under `src_so268_boxcore`) until Track G delivers
  real Dryad `[06]` data or the TS-6 `[18]` digitization — both are deliberately unwired
  because their placeholders were fabricated. `data/corpus/manifest.json` is the build
  record; see `docs/contracts/PROVENANCE.md`.
- **Next task:** **E5.4** — the honesty surface, whose specification is E5.0 §4's
  thirteen-row inventory (every row LOOKING today): the claim verdict visible without
  interaction with its failing preconditions named, both watermark reasons with their
  expiry, the uncertainty not optional, the 99 %-no-information region marked. The
  Phase-2/3/4 closeout facts this bullet used to carry live in their walkthroughs
  and `docs/BACKLOG.md` (corrected 2026-08-22, E5.1 commit 0: it had said
  "Phase 3 planning" two phases late — found by E5.0).
- **Open items live in `docs/BACKLOG.md`** — the single source of truth, grouped by who is
  blocked. Read it before proposing work; add an entry whenever something is deliberately
  deferred.
- Per-task walkthroughs are in `docs/walkthroughs/` (`phase-0-and-E1.1.md`, `E1.2.md`
  … `E1.5.md`, `P2.0.md`, `P2.B-and-P2.A.md`, `E2.0.md` … `E2.5.md`, whose second
  half is the PHASE-2 TRACK-E CLOSEOUT, `C8.1.md`, `P2-closeout.md`,
  `E3.1-2.md`, `TAX.1.md`, `E3.3.md`, and `E3.4.md`, whose second half is
  the PHASE-3 TRACK-E CLOSEOUT). Read the relevant
  one before changing that area.
- The seven contracts live in `docs/contracts/` + `data/` (canonical — see the paths above);
  `Proposals and contract V3/Contracts_v3/` holds the authoring copies. Treat them as frozen;
  if one needs a structural change, bump its `*_version`, tell me, and note it in the
  contracts README.
- The phase-boundary rule above still governs: one task per prompt, STOP at each
  boundary for review. (The former "do not jump ahead to Phase 2" line was removed at
  E2.4 §1 — it was an active instruction contradicting the current work.)



