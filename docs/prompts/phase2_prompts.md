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
  treatment `scenarios.yaml` already gets with `illustrative_only`.
- The user's Checkpoint 2 wording ("run on the REAL Phase-A corpus") is half-satisfied
  today. Checkpoint 2's *scientific* review requires Checkpoint 1 to have happened
  first; before that it is a mechanics review only.

### Blocked on Isaac before E2.0

**The training target is undecided.** Buried versus surface abundance (BACKLOG §1) —
`[01]`'s published mass includes buried nodules, which surface collectors cannot recover.
This is the definition of `y`. Don't start E2.0 without it, or the matrix gets rebuilt.

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
- **Record provenance into `RunManifest`**, chaining upstream `content_hash` values
  (corpus manifest → feature stack → training matrix → run). Do not invent a fourth
  provenance format; extend `ProvenanceArtifact`.
- **Write a walkthrough** (`docs/walkthroughs/E2.x.md`) and update `PATTERNS.md` and
  `BACKLOG.md` in the same commit.
- **Never fabricate a value.** Clearly-labelled placeholders only.
- Commit after each task.

---

## E2.0 — Training matrix assembly (prerequisite; not in the original lane list)

> **Task E2.0 only. Do not implement any estimator.**
>
> Restate first: `SampleSource`'s interface, `Observation.is_training_eligible()`'s
> rule, and what the feature-stack provenance sidecar records about DEM resolution and
> border policy. Report the training-eligible row count from the real corpus (expect
> 35) before writing code.
>
> Implement:
> 1. **`CorpusCsvSampleSource`** — the missing `SampleSource` implementation flagged in
>    E1.5's reverse audit. Reads `master_observations.csv`, returns training-eligible
>    MASS rows only. The `qa_status` gate must hold: flagged and failed rows are
>    excluded.
> 2. **Covariate extraction at station locations** — produce the training matrix
>    (35 rows × 8 covariates + target + coordinates + `source_record_id`).
> 3. **The DEM-resolution guard** (BACKLOG §3). Contract 3 v3 states features from
>    different DEM resolutions must never be mixed in one training matrix. Enforce it
>    at assembly: compare each layer's recorded `dem.resolution_deg` and raise on
>    mismatch. Add a test that a mixed-resolution stack raises.
> 4. **The synthetic-DEM watermark.** While the feature stack's provenance says the DEM
>    is synthetic, the training matrix and everything derived from it must carry a
>    flag marking it non-scientific. Mirror how `scenarios.yaml` watermarks
>    illustrative economics.
>
> **STOP and ask me — two extraction decisions:**
> - **Sampling method.** Nearest cell, or bilinear interpolation from surrounding
>   cells? Report the trade-off given the DEM's cell size relative to station spacing
>   (stations within a cluster are ~1–12 km apart; the synthetic DEM is ~11 km/cell and
>   real GEBCO ~450 m/cell — the answer may differ before and after Checkpoint 1, which
>   is itself worth reporting).
> - **Border cells.** Recipes leave a NaN rim per the declared border policy. What
>   happens to a station whose cell is NaN for some covariates? Options: drop the
>   station (loses real data), impute (fabricates), or carry NaN into the matrix and let
>   each estimator declare how it handles missing features. Report which stations are
>   actually affected today before I decide.
>
> Tests: exactly 35 rows and no station silently dropped (assert the count against the
> corpus, so a dropped station fails rather than shrinking the matrix); the qa_status
> gate excludes the flagged station by name; resolution mismatch raises; the matrix is
> deterministic across two assemblies; the watermark is present while the DEM is
> synthetic.
>
> Report the matrix shape, which stations (if any) hit NaN covariates, and stop.

**Watch for:** the "no station silently dropped" test is the important one. With n=35,
losing two stations to a border rim is a 6% data loss that would never show up as an
error — the same silent-shrinkage class as the dedup bugs from Phase 1.

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

**Also carry forward, still open from Phase 1:** the buried-versus-surface target
decision (blocks E2.0), the AOI scope (blocks prediction surfaces), and the
geographic-spread download priority.

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
