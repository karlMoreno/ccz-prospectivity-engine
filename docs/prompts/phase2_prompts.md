# Phase 2 — Modeling + Spatial Validation (Claude Code Prompts)

Companion to `phase1_prompts_v2.md`. Same conventions: one task per prompt, stop at
every boundary, STOP conditions for anything that is a scientific decision rather than
an engineering one.

**Two structural notes before any of this runs — read both.**

### 1. Phase 2 adds a task the lane list omits

Covariate extraction at station locations was explicitly deferred out of E1.4 as
"Phase 2's training matrix." Nothing can be estimated before that exists, so it is
**E2.0** below and it comes first.

```
  E2.0  Training matrix  ──► E2.1  Estimator interface + mean baseline
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
              E2.2  Ordinary kriging        E2.3  Random forest
                        └─────────────┬─────────────┘
                                      ▼
                        E2.4  Spatially-blocked CV vs baseline
                                      ▼
                        E2.5  Refuse-to-validate guard
```

### 2. Phase 2 can be *built* now but not *believed* until Checkpoint 1

The corpus is real. The covariates are not — every terrain feature is currently computed
on a synthetic DEM, so a model trained today learns the relationship between real
abundance and **noise**. That is fine for building and testing the machinery (it is the
two-track discipline working as designed), but it means:

- No scientific claim from Phase 2 is valid until real GEBCO bathymetry lands.
- Every Phase-2 output must be **watermarked** while the DEM is synthetic — the same
  treatment `scenarios.yaml` already gets with `illustrative_only`. (Automatic since
  P2.0d-3: the watermark derives from the computed data origin — nothing to build,
  only to verify it fires.)
- The user's Checkpoint 2 wording ("run on the REAL Phase-A corpus") is half-satisfied
  today. Checkpoint 2's *scientific* review requires Checkpoint 1 to have happened
  first; before that it is a mechanics review only.

### Blocked on Isaac before E2.0 — SETTLED (P2.B/P2.A, 2026-08-09)

The training target no longer blocks E2.0. P2.B settled it from the data:
`[05]`'s per-nodule burial column contradicts `[01]`'s published buried counts
on 6 of 36 events (all SO268/2; worst `2_182-1`, 0 recorded vs 24 published),
so surface-only mass is **not derivable** and `target_definition:
total_as_published` is the one admissible value — held in Contract 8
(`data/config/model_config.yaml`), declared `AUTHORED · author: model`, which
IS its provisional marker. Isaac's value-with-citation arrives as the
AUTHORED→LITERATURE promotion; the live Track G question is the six-event
burial contradiction (BACKLOG §1).

---

## Cross-cutting requirements (state once, apply to every prompt below)

Every Phase-2 task must:

- **Restate the relevant contract before writing code**, and STOP rather than improvise
  if a needed parameter is missing or ambiguous.
- **Mutation-verify every new guard** — this project's established practice. Report which
  mutations were run and what failed.
- **Pair every prediction with an uncertainty.** A point estimate with no interval is not
  a deliverable in this project.
- **Run the mean baseline alongside any model claim.** `CLAUDE.md` requires it.
- **Record provenance into the `ProvenanceArtifact` chain**, chaining upstream
  `content_hash` values (corpus manifest → feature stack → training matrix → run).
  Do not invent a fourth provenance **format** — extending the Layer Supertype with
  a new `ProvenanceArtifact` subclass is the sanctioned way to add an *artifact*
  (E2.0-3 does exactly that; `docs/contracts/PROVENANCE.md` defines the boundary).
- **Write a walkthrough** (`docs/walkthroughs/E2.x.md`) and update `PATTERNS.md` and
  `BACKLOG.md` in the same commit.
- **Never fabricate a value.** Clearly-labelled placeholders only.
- Commit after each task.

---

## E2.0 — The training matrix (three commits)

> **Revised 2026-08-13**, after the Phase-2 preflight (P2.0 origin taxonomy,
> P2.B target investigation, P2.A Contract 8) and the E2.0-1 commit
> (`87a2f64`). The original E2.0 section predated the preflight and was
> superseded on four points: the training target is no longer blocked on
> Track G (P2.B settled it from the data; Contract 8 holds it); the
> synthetic-DEM watermark is no longer a build task (P2.0d-3 derives it from
> computed origin — E2.0-3 only verifies it fires); "do not invent a fourth
> provenance format" was being read as forbidding a fourth ARTIFACT, and
> E2.0-3 adds exactly that — a fourth `ProvenanceArtifact` subclass, the
> sanctioned Layer Supertype extension; and the two STOP questions (sampling
> method, border cells) are decided below with the alternatives recorded.
> The original section is preserved in git history (pre-`87a2f64`).


Three commits. Adversarial review on E2.0-2 only — that's where the eligibility
gate and the DEM-resolution guard live. E2.0-1 is a loader over an audited
corpus; E2.0-3 is assembly plus a provenance subclass over machinery P2.0 built.

Two design decisions are **made**, with the alternative recorded in each prompt
so a later reader sees a choice rather than an accident.

---

### E2.0-1 — `CorpusCsvSampleSource`

```
Read CLAUDE.md, docs/BACKLOG.md, docs/PATTERNS.md, and the P2.B/P2.A walkthrough
first. Run the suite and report the count. Restate the contract before writing
code. STOP on ambiguity rather than improvising.

SCOPE FENCE: this task is the SampleSource only. No covariate extraction, no
matrix, no provenance artifact — those are E2.0-2 and E2.0-3.

WHAT THIS CLOSES

SampleSource is a Phase-0 Strategy with no production implementation; every
caller today uses a fixture. BACKLOG §3 has carried the gap since E1.3. The
engine has been reading real data through test doubles, which is the sort of
thing that is fine until it isn't.

BUILD CorpusCsvSampleSource, implementing the EXISTING SampleSource ABC. Do not
define a parallel interface — the seam exists, fill it.

THE ELIGIBILITY GATE, stated as the contract states it

A row is training-eligible iff ALL of:

  evidence_class == MASS        the only class the model trains on
  abundance_kg_m2 is present     0.0 is VALID (barren), not missing —
                                 no truthiness checks anywhere near this
  is_open is true                license gate on published runs
  qa_status is training-eligible flagged and failed never train; fail is
                                 terminal

Expected result: 35 rows from 108. If you get a different number, STOP and
report rather than adjusting the gate to reach 35 — the manifest's
training_eligible_count is the check, not the target.

Reuse the existing is_training_eligible() logic rather than reimplementing the
predicate. Two implementations of one rule is how they drift.

TESTS

  - 35 of 108, and the excluded 73 are excluded for the RIGHT reason — assert
    per-reason counts, not just the total. An aggregate assertion does not
    prove a per-item claim (CLAUDE.md testing conventions).
  - SO268/1_12-2 (the failed box core) is excluded BY NAME.
  - A barren station (abundance_kg_m2 == 0.0) IS eligible. This is the falsy-
    zero bug E1.2 already found once in MassNormalizer; it would bias the model
    toward higher abundance and it is silent.
  - COVER and COUNT rows never appear, even though COUNT rows carry
    abundance_kg_m2.
  - The source must NOT load its data through the class that enforces the rule
    it is asserting — construct rows directly so a violation is observable.

MUTATION-VERIFY the qa_status gate and the is_open gate separately. A single
mutation tripping both proves only that a gate runs.

Walkthrough section, BACKLOG update closing the CorpusCsvSampleSource item, one
commit.
```

---

### E2.0-2 — Covariate extraction and the single-DEM guard

```
ADVERSARIAL REVIEW REQUIRED before commit — this adds a guard and a sampling
rule that every downstream number depends on.

SCOPE FENCE: extraction and the guard. No TrainingMatrix assembly, no
provenance artifact — that is E2.0-3.

1. THE SINGLE-DEM GUARD (Contract 3 v3, never enforced in code)

Contract 3 v3 states: covariates computed from DEMs of different resolutions
must NEVER be mixed in one training matrix. Slope, aspect, and both curvatures
are native-resolution 3×3 operators, so their physical scale IS the DEM
resolution; roughness/TPI/BPI resolve metres to cells from that same
resolution.

The feature stack's provenance.json records the DEM hash and resolution per
layer. Read them and REFUSE if any layer disagrees with any other on either.
Refuse by name, stating which layers disagree and on what.

This is a validation function, not a pattern (PATTERNS.md §4.4). Do not build a
seam for it.

Mutation-verify: hand-edit a copy of a stack provenance so one layer reports a
different DEM hash, confirm the refusal names that layer, revert.

2. POINT SAMPLING — DECISION MADE: NEAREST-CELL

Sample each covariate raster at the 35 station coordinates by nearest cell
centre. Record sampling_method: "nearest_cell" in the output.

Why, and the alternative, both recorded in the code comment:

  Bilinear interpolation was considered and declined for the alpha. It
  propagates the nan_border inward by a cell, and it invents values between
  cells — on a DEM whose derivative covariates are computed with a stated
  border policy, interpolating those derivatives compounds two approximations
  and makes the recorded provenance less exactly true of the number.

  The known consequence of nearest-cell, which must be RECORDED not hidden: on
  the 0.1° synthetic DEM a cell is ~11 km, so several stations within one
  ~12 km cluster resolve to the SAME cell and receive IDENTICAL covariate
  values. On real GEBCO (~460 m at 13N) they separate. So the alpha's matrix
  has near-duplicate rows by construction, and any apparent within-cluster
  signal before Checkpoint 1 is an artifact of the fixture.

  Report how many of the 35 stations share a cell with another station, and
  record that count in the output. It is a one-line diagnostic that tells a
  reviewer how much independent information the matrix actually carries.

  One function with a recorded sampling_method — NOT a PointSampler Strategy.
  There is one method; building the seam for a second that nobody has asked for
  is the ceremony PATTERNS.md §3 objects to. It gets promoted to a Strategy the
  day bilinear is actually wanted, and the recorded field is what makes that
  swap auditable.

3. BORDER AND MISSING VALUES

A station landing on a NaN border cell is NOT silently dropped and NOT
zero-filled. Flag-never-drop is the corpus's own rule; the same applies here.
Report any such station by name and carry the NaN through to E2.0-3, which
decides what a matrix with holes does.

Test that a station on a border cell produces a flagged NaN rather than a
number. Mutation-verify it — a zero-fill would be invisible in aggregate.

TESTS

  - Known-value: a station at a known coordinate on a synthetic DEM returns the
    value at the expected cell, computed independently.
  - All 35 stations sample all 8 covariates; shape is exactly 35×8.
  - Determinism: two independent extractions are identical.
  - The shared-cell count is reported and matches an independent computation.
  - The guard refuses a mixed-resolution stack.

Walkthrough section, one commit.
```

---

### E2.0-3 — `TrainingMatrix` and its provenance

```
SCOPE FENCE: assembly and provenance. E2.0-1 and E2.0-2 are already committed.

1. TrainingMatrix

Assemble X (35×8), y (35), coords (35×2), and station ids, from the
SampleSource and the extractor. Order must be deterministic and stated — sort
by a stable key, not by whatever the CSV happened to give.

If any covariate value is NaN from E2.0-2's border policy, the matrix does not
silently carry it into a model. Either the station is excluded with the
exclusion recorded, or the matrix refuses. Decide and state which; do NOT
impute. Report which stations are affected — on the current synthetic DEM the
answer should be none, and if it isn't, that is a finding about the fixture
extent.

2. PROVENANCE — DECISION MADE: A FOURTH ProvenanceArtifact SUBCLASS

TrainingMatrixManifest extends ProvenanceArtifact, alongside CorpusManifest,
FeatureStackManifest, and RunManifest. It records:

  upstream_hashes    {corpus: sha256:…, feature_stack: sha256:…}
  target_definition  the VALUE and its DECLARED ORIGIN from Contract 8 —
                     both, in one record. The value alone loses the caveat,
                     which is the entire reason Contract 8's loader returns
                     DeclaredField.
  sampling_method    "nearest_cell"
  shared_cell_count  from E2.0-2
  n_stations, n_covariates, and the covariate names in matrix column order
  data_origin        COMPUTED by combine_origins over the corpus and stack
                     origins — never declared by hand

Why a fourth artifact rather than folding into RunManifest, recorded in the
class docstring:

  The corpus hash and the feature-stack hash are both INVARIANT to the target
  definition. Two matrices built on different y would therefore present
  identical upstream_hashes. Contract 8 does not close this on its own — the
  contract file is not hashed into either upstream artifact — so without a
  matrix-level record, the one decision that defines what the model predicts
  has no identity in the provenance chain.

  The alternative considered: fold these fields into RunManifest, on the
  grounds that a matrix is cheap to rebuild and 1:1 with a run. Declined
  because it is 1:1 only by convention — nothing enforces it, and the moment
  two runs share a matrix or one matrix feeds a re-run with a different seed,
  the record is in the wrong place. PROVENANCE.md's stated principle is that
  artifacts are separated by LIFETIME.

  This makes four artifacts where PROVENANCE.md documents three. Update that
  file's diagram and table in this commit — a provenance document that omits an
  artifact is the defect class the 2026-08-08 audit was about.

3. THE WATERMARK FOLLOWS AUTOMATICALLY

The computed origin will be SYNTHETIC, because the feature stack is. Do not add
a watermark flag — P2.0d-3's rule derives it. VERIFY it fires end to end rather
than trusting that it exists: a test that the assembled matrix's manifest
reports SYNTHETIC and that the watermark is present. Mutation-verify by
declaring the stack MEASURED in a fixture and confirming the watermark
disappears — that is the Checkpoint-1 direction, and it is the one P2.0c's
tests could not observe.

TESTS

  - Two independent builds produce identical matrices and identical
    content_hash (the E1.3 corpus-CSV determinism bar).
  - upstream_hashes match the actual corpus and stack manifests, not literals.
  - Changing target_definition changes the matrix content_hash — this is the
    property the fourth artifact exists for, so it must be asserted directly.
  - The manifest names covariates in matrix column order, and a reordered
    registry produces a matrix whose columns match its own manifest.
  - Origin is SYNTHETIC and computed, not declared.

CLOSING

  - PROVENANCE.md updated to four artifacts.
  - Walkthrough for E2.0 across all three commits, with every mutation in one
    table.
  - PATTERNS.md: TrainingMatrixManifest is Layer Supertype reuse, not a new
    pattern. Add a row only if something genuinely new appeared; if not, say so
    in the walkthrough.
  - BACKLOG: close CorpusCsvSampleSource and the DEM-resolution rule; record
    the shared-cell finding as a Checkpoint-1 item.
  - One commit.
```
---

## E2.1 — Estimator interface + mean baseline

> **Task E2.1 only.**
>
> The `Estimator` ABC already exists from Phase 0 with zero implementations — implement
> it rather than defining a new interface. Restate its signature first, and report
> whether it can express paired uncertainty; if it cannot, that is a Phase-0 interface
> question — STOP and report rather than working around it.
>
> Implement a **Strategy + Registry** exactly mirroring E1.2's `NormalizerRegistry`:
> - `EstimatorRegistry` mapping an estimator name to an instance, with an
>   `assert_complete()`-style guarantee and a completeness test.
> - `MeanBaselineEstimator` — predicts the training mean everywhere; uncertainty is the
>   training standard deviation (state whether you use SD or standard error and why).
>
> Comment the patterns, and comment the *reason* the registry is justified here
> specifically: `CLAUDE.md` requires a mean baseline alongside every model claim, so a
> registry turns "the baseline always ran" into a structural guarantee with a
> completeness test, rather than a convention every call site must remember. That is a
> stronger justification than the normalizer registry had — say so.
>
> Every estimator must return prediction **and** uncertainty. Add a test that an
> estimator returning `None` uncertainty fails loudly, so the pairing rule is
> structural rather than documentary.
>
> Tests: hand-computed baseline value on a small fixture (not "output is not null");
> uncertainty is the SD of the same fixture, hand-computed; registry completeness;
> unpaired-uncertainty rejection, mutation-verified.
>
> Stop for review.

### Target architecture

```
                 +----------------------------+
                 |  Estimator (Phase-0 ABC)   |  <<Strategy>>
                 |  + fit(X, y)               |
                 |  + predict(X) -> (mu, sd)  |   paired, always
                 +-------------^--------------+
                               |
         +---------------------+---------------------+
         |                     |                     |
  MeanBaseline          OrdinaryKriging        RandomForest
   (E2.1)                  (E2.2)                 (E2.3)
                               ^
                               |
                 +-------------+--------------+
                 |  EstimatorRegistry         |  <<Registry>>
                 |  name -> instance          |  completeness-tested;
                 +----------------------------+  baseline cannot be omitted
```

---

## E2.2 — Ordinary kriging (TS-6 parity) — the hard one

> **Task E2.2 only. Report the variogram support analysis before fitting anything.**
>
> **The constraint you must confront first.** The 35 training stations form two clusters
> ~12 km across, ~991 km apart. Every station pair is either under 13 km or near 991 km
> — there are **zero pairs between roughly 13 km and 986 km**. A variogram is estimated
> from how semivariance grows with lag distance, so across that entire range there is no
> empirical support. Any curve drawn through it is an assumption, not an estimate.
>
> **Step 1 — report, don't fit.** Compute the empirical variogram and report, per lag
> bin: the bin's distance range, the **number of pairs**, and the semivariance. Name
> explicitly which bins have zero pairs. Then stop and show me this before fitting a
> model.
>
> **STOP and ask me — three decisions:**
> - **Minimum pairs per lag bin** before a bin may inform the fit. A bin with 2 pairs is
>   noise. Propose a threshold and say what it excludes.
> - **Which lags the fit is allowed to see.** Within-cluster lags only (0–13 km, honest
>   about what it measures: local structure), or including the ~991 km bin (which would
>   pull the range far beyond anything supported)?
> - **Variogram model family** (spherical, exponential, Gaussian, Matérn) and whether
>   the nugget is fitted or fixed.
>
> **Step 2 — implement, with these requirements:**
> - Ordinary kriging returning prediction **and kriging variance**, paired.
> - **Do not force a long range to make the prediction map look smooth.** With a range
>   shorter than the inter-cluster distance, kriging correctly reverts toward the local
>   mean far from data, with variance approaching the sill. That behaviour is the honest
>   output, not a defect to tune away — comment it as such.
> - **Record the unsupported lag range in the run provenance**, so any consumer of a
>   prediction surface can see that the model was extrapolating between clusters.
> - **Decline directional/anisotropic variograms explicitly.** With 35 points in two
>   clusters, directional binning would produce bins of 2–3 pairs. Note this as a
>   documented refusal in the walkthrough, not an oversight.
>
> Tests: kriging at an exact data location returns that observation with near-zero
> variance (the standard exactness check, hand-verified); kriging variance increases
> monotonically with distance from the nearest datum along a transect; the fit refuses
> to use bins below the agreed minimum pair count, mutation-verified; determinism across
> two runs.
>
> Report the variogram table, the fitted parameters, and stop.

**Watch for:** the temptation is a smooth, plausible-looking prediction map across the
whole area. That map would be almost entirely extrapolation, and the kriging variance is
the thing that tells the truth. If the variance surface looks alarming between clusters,
it is working.

---

## E2.3 — Random forest + uncertainty

> **Task E2.3 only.**
>
> Report these two facts before writing code, because they shape what the model can
> honestly claim:
> - **n = 35, features = 8.** That ratio invites overfitting.
> - **All 8 covariates derive from one DEM**, so they are strongly collinear (slope,
>   roughness, TPI, and BPI are all functions of the same local elevation
>   neighbourhood). Report the actual correlation matrix from the training matrix.
>
> Implement `RandomForestEstimator` behind the same `Estimator` interface, registered in
> `EstimatorRegistry`. Uncertainty via quantile regression forest or ensemble spread —
> state which and why.
>
> **Hard requirement: OOB score must not be reported as validation.** Out-of-bag
> resampling is random, which means spatial leakage on autocorrelated data — exactly the
> failure mode this project's methodology exists to avoid. Compute it if useful for
> diagnostics, but label it clearly as **not** a validation metric, and make sure nothing
> downstream can pick it up as one. Spatial CV (E2.4) is the only honest number.
>
> Report variable importance, and report it with the caveat that at n=35 with collinear
> features importances are unstable — demonstrate this by reporting importance across
> several seeds rather than asserting it.
>
> Tests: determinism under a fixed seed; uncertainty always paired and never `None`;
> a test asserting OOB is not present in whatever structure feeds validation reporting,
> mutation-verified.
>
> Stop for review.

---

## E2.4 — Spatially-blocked cross-validation

> **Task E2.4 only. This is the project's most defensible methodological claim — build
> it carefully.**
>
> **Two CV designs, because they answer two different questions.** Implement both as
> Strategy implementations behind one splitter interface:
>
> 1. **Leave-one-cluster-out** — train on one cluster, predict the other, ~991 km away.
>    Two folds. This measures **extrapolation** to unsampled regions, which is what the
>    project's actual use case requires.
> 2. **Within-cluster spatial blocking** — spatially blocked folds inside each cluster.
>    This measures **local interpolation** at 1–13 km, a genuinely different and much
>    easier question.
>
> Report both. Collapsing them into one number would hide that the model may interpolate
> well locally and be useless at range — which given the geometry is the likely truth.
>
> 3. **Random k-fold** — implement it too, **labelled as the demonstrably-wrong
>    comparison**. Its purpose is to be reported alongside the spatial results to
>    demonstrate the inflation that random splitting produces on autocorrelated data.
>    Guard it so it cannot be selected as the validation method for a published claim.
>
> Requirements:
> - **The mean baseline runs in every fold, always**, for every design. Report uplift
>   over baseline per fold, not only averaged.
> - **Report per-fold results**, not just means. With two folds, a mean hides everything.
> - Fold assignment must be deterministic and recorded in provenance.
> - **A spatial-leakage assertion**: for every fold, assert train and test sets are
>   disjoint and separated by a stated minimum distance. This is the test that makes the
>   methodological claim real rather than asserted.
>
> **State the expected result honestly in the walkthrough.** With two folds and ~991 km
> extrapolation, kriging and RF may not beat the mean baseline. If they don't, that is a
> finding about the *data*, not a failure of the code — and it is publishable. Do not
> tune toward beating the baseline.
>
> Tests: spatial disjointness per fold with a buffer, mutation-verified; determinism of
> fold assignment; baseline present in every fold's results (a completeness-style test);
> random k-fold cannot be selected for a published claim.
>
> Stop for review.

---

## E2.5 — Refuse-to-validate guard

> **Task E2.5 only. Structural refusal, not a convention.**
>
> Mirror the `_require_production_path()` guard from P1: make the invalid state
> unreachable rather than merely documented.
>
> No model result may be emitted as a validated claim unless **all** of the following
> hold. Each is a separate raise with a message naming the specific failure:
> 1. Spatially-blocked cross-validation ran (random k-fold does not satisfy this).
> 2. The mean baseline ran alongside, in every fold.
> 3. Every prediction carries a paired uncertainty.
> 4. All feature layers share one DEM resolution (E2.0's guard, re-asserted at
>    claim time).
> 5. The run's provenance records the upstream corpus, feature-stack, and
>    training-matrix hashes.
>
> Additionally: if the feature stack's DEM is synthetic, the output must be
> **watermarked non-scientific** rather than refused — building on fixtures is
> legitimate, publishing from them is not. Mirror `scenarios.yaml`'s
> `illustrative_only` treatment.
>
> Tests: one per condition, each attempting to emit a claim with that condition unmet
> and asserting the specific raise. Mutation-verify by removing each guard in turn.
> Plus an exhaustiveness test in the spirit of the `Resolution` dispatch check: if a new
> validation precondition is added to the contract without a corresponding guard, a test
> fails.
>
> Report the final test count and stop. **This completes Phase 2 Track E — stop for my
> review before Checkpoint 2.**

---

## Track G — the brief for Isaac

Not Claude Code prompts. These are what to ask for, and what each unblocks.

**G2.1 — Validation metrics and acceptance thresholds** → `docs/geology/metrics.md`

Ask for: which metrics carry weight in resource estimation (RMSE, MAE, bias, R²,
interval coverage), and **what counts as credible uplift over a mean baseline** for a
sparse nodule dataset. The threshold matters more than the metric list: without it,
"the model beat the baseline by 8%" has no interpretation. Also ask what interval
coverage he would expect from an honest uncertainty surface — that is the number that
makes "calibrated uncertainty" checkable rather than rhetorical.

**G2.2 — Plausible spatial range (advisory)**

Ask for: over what distance he would expect nodule abundance to remain correlated in
the CCZ — hundreds of metres, kilometres, tens of kilometres? This is advisory, not a
fitted parameter, and it serves as a plausibility check on whatever the variogram
produces. Given our support gap, his prior is the *only* information available about
the medium range, so it should be recorded as a prior rather than smuggled into a fit.

**G2.3 — Real economic parameters**

Ask for: metals of interest, grade units, cutoff logic, and price sources for
market-versus-strategic scenarios. `scenarios.yaml` is entirely `illustrative_only`
today and the engine watermarks output until that flips. Not blocking for Phase 2, but
it is the long-lead item for Phase 4.

**Also carry forward, still open from Phase 1:** the buried-versus-surface question
(no longer blocks E2.0 — Contract 8 holds the provisional target; the live question
is the six-event `[05]`-vs-`[01]` burial contradiction, BACKLOG §1), the AOI scope
(blocks prediction surfaces), and the geographic-spread download priority.

---

## Integration Checkpoint 2

```
  Prerequisite:  Checkpoint 1 done  (real GEBCO bathymetry in)
                        │
                        ▼
  Run kriging + RF + baseline on the real corpus with real covariates,
  under both spatial CV designs, with the E2.5 guard active.
                        │
                        ▼
  Track G reviews:  credible uplift over baseline?   (against G2.1's threshold)
                    plausible variogram range?       (against G2.2's prior)
                    honest interval coverage?
                        │
                        ▼
  Feedback becomes a spec update — not a tuning pass.
```

**The distinction that matters at this checkpoint:** if the models do not beat the
baseline, the correct response is to report that and ask what data would change it —
not to adjust the model until the number improves. Given 35 stations in two clusters,
"the ceiling is the data, not the model" is the project's own stated position, and
Checkpoint 2 is where that either holds up or gets revised on evidence.

**Before the checkpoint, verify the watermark actually fires.** Run the full pipeline on
the synthetic DEM and confirm every output is marked non-scientific. A watermark that
only exists in code is not a safeguard — this is the same lesson as `qa_status` having
no downstream effect until P1 made it gate training eligibility.

---

## What Phase 2 deliberately does not include

- **Prediction and uncertainty surfaces as raster products** (COGs over the full AOI) —
  these need the AOI decision and belong to the next phase. Phase 2 predicts at
  held-out stations for validation, not across a grid.
- **TS-6 benchmark comparison** — needs the real digitisation (Checkpoint 3).
- **Economic overlay** — needs real `scenarios.yaml` (Checkpoint 4).
- **Option-B covariates** (sediment, chlorophyll, CCD) — Phase 6.
- **Active sampling / "where to sample next"** — the natural follow-on from a
  calibrated uncertainty surface, and a strong v-next feature, but out of the alpha.
