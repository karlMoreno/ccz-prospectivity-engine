# Phase 2 diagnostic — seven numbers

Read-only pass. Sources: `data/runs/e2.4/run_manifest.json` (the committed
E2.4 run, `run_id` `e2.4-report`, seed 0), the corpus, and one throwaway
script `scratch/phase2_diag.py` (Q3/Q4/Q5 only), output
`scratch/phase2_diag.json` + `scratch/phase2_diag.png`. Nothing committed,
nothing in the repo changed.

Two caveats that apply to every number below, stated once:

- **The covariates are computed on a SYNTHETIC DEM.** Every RF number is a
  noise-score. Kriging and the mean baseline are unaffected — kriging
  declares `input_kind = "coordinates"` and the baseline ignores feature
  values — so their numbers are real measurements on real coordinates and
  real abundance.
- **No acceptance threshold was pre-registered.** Any threshold set now is
  post-hoc for this dataset, permanently.

---

## Q1. Spatial CV result

**Blocking schemes — four designs, reported separately because they answer
different questions.** Two are claim-eligible (declared `spatially_blocked`),
two are not.

| design | blocking | folds | fold sizes (n held out) | measured min train–test separation | claim-eligible |
|---|---|---|---|---|---|
| `leave_one_site_out` | single-linkage blocks, **2.0 km** linkage | **5** | 7, 7, 7, 8, 6 | **4.614 km** | yes — **the headline within-cluster gate** |
| `leave_one_cluster_out` | single-linkage blocks, **100 km** linkage | **2** | 21, 14 | **986.036 km** | yes — across-cluster |
| `leave_one_station_out` | none (LOO) | 35 | 1 each | 0.054 km | **no** |
| `random_k_fold` | none, k=5 | 5 | 7 each | 0.054 km | **no** |

### A. WITHIN-CLUSTER — `leave_one_site_out` (5 folds, 4.6–10 km separation)

Pooled over folds:

| estimator | RMSE | MAE | R² (pooled) | folds scored | bias |
|---|---|---|---|---|---|
| mean_baseline | **4.1860** | 3.4403 | **−0.1975** | 5/5 | −0.005 |
| ordinary_kriging | **4.5095** | 3.8247 | **−0.2189** | **4/5** (fold 3 REFUSED at fit) | +0.418 |
| random_forest | **4.1406** | 3.3933 | **−0.1716** | 5/5 | +0.705 |

Like-for-like on shared folds only (`baseline_on_same_folds`):

- **ordinary_kriging 4.5095 vs baseline 4.5092** → **−0.0003 RMSE, i.e. kriging is very slightly WORSE.**
- **random_forest 4.1406 vs baseline 4.1860** → **+0.0454 RMSE better.**

Per fold (baseline RMSE − estimator RMSE; positive = estimator better):

| fold | n | baseline RMSE | kriging Δ | RF Δ |
|---|---|---|---|---|
| 0 | 7 | 3.980 | −0.052 | +0.012 |
| 1 | 7 | 3.830 | 0.000 | +0.034 |
| 2 | 7 | 6.012 | −0.000 | −0.022 |
| 3 | 8 | 2.835 | *(refused)* | +0.231 |
| 4 | 6 | 3.706 | +0.065 | +0.058 |

**Fold-to-fold spread of the baseline's own RMSE: sd = 1.172, range = 3.178
(2.835 → 6.012).**

- kriging mean margin **+0.0032** → **0.003 ×** the fold-to-fold spread.
- RF mean margin **+0.0626** → **0.053 ×** the fold-to-fold spread.

### B. ACROSS-CLUSTER — `leave_one_cluster_out` (2 folds, 986 km separation)

| estimator | RMSE | MAE | R² (pooled) | folds scored |
|---|---|---|---|---|
| mean_baseline | **4.1636** | 3.4269 | **−0.1847** | 2/2 |
| ordinary_kriging | **4.5821** | 3.9102 | **−0.2039** | **1/2** (fold 0 REFUSED at fit, n_train = 14) |
| random_forest | **4.9226** | 4.2026 | **−0.6560** | 2/2 |

On the one fold kriging could fit, its RMSE, MAE and bias equal the
baseline's **to 12 decimal places** (4.5821 / 3.9102 / +1.8857). That is not
a tie to be tallied — it is the geometry: the fitted range is ~22 km against
a 986 km gap, so kriging reverts to the training cluster's mean, which is
what the baseline predicts. **This design cannot rank estimators.** Its one
real measurement is that the two clusters' means differ by ±1.886 kg/m².

RF on the same folds: **4.9226 vs 4.1636 → 0.759 WORSE**, which is **1.25 ×
the fold-to-fold spread** — the only margin in this table larger than the
noise, and it points the wrong way.

### Plainly

- **Does ordinary kriging beat the mean baseline out of fold? NO.** Within
  cluster it is 0.0003 RMSE *worse* pooled (+0.0032 mean per-fold margin,
  0.003 × the fold spread). Across clusters it ties exactly, by construction.
- **Does RF? Not meaningfully.** +0.0454 RMSE within cluster — **0.053 × the
  fold-to-fold spread** — and 0.759 *worse* across clusters. Its covariates
  are synthetic noise, so even the small positive number is not evidence.
- **Every pooled R² is negative** (−0.17 to −0.66): on these folds all three
  estimators, the baseline included, do worse than predicting the global mean
  of the held-out data.
- **No margin here exceeds the fold-to-fold spread except RF's across-cluster
  deficit.** Per-fold aggregation gives RF +0.0626 rather than +0.0454; the
  difference between those two aggregations (0.017) is itself larger than
  kriging's entire margin.

---

## Q2. Variogram parameters

Refitted on all **35** training stations with the project's own fitter
(`OrdinaryKrigingEstimator.fit` → `report()`); the E2.4 run's per-fold fits
use 27–29 stations and differ slightly.

| quantity | value |
|---|---|
| model family used | **exponential**, γ(h) = c₀ + c₁(1 − exp(−3h/a)) |
| nugget **c₀** | **7.8797** (kg/m²)² |
| partial sill **c₁** | **13.5143** |
| sill c₀+c₁ | **21.3940** |
| range **a** | **21.611 km** (practical range convention) |
| **c₀/(c₀+c₁)** | **0.3683** |
| alternative family fitted | spherical, range 21.611 km |
| **weighted SSE — exponential (used)** | **5269.79** |
| **weighted SSE — spherical (not used)** | **4006.64** |
| residual dof | **1** (4 fitted bins − 3 parameters) |

**Lag binning:** edges **[0, 2, 4, 6, 8, 10, 13, 986, 997] km** — 8 bins,
non-uniform. **min pairs per bin = 30. Max fit lag = 13 km.**

| bin (km) | pairs | mean lag | γ̂ | used in fit? |
|---|---|---|---|---|
| 0–2 | **102** | 0.727 | 10.688 | yes |
| 2–4 | 4 | 2.141 | 15.880 | no — 4 < 30 pairs |
| 4–6 | 48 | 5.271 | 9.963 | yes |
| 6–8 | 50 | 7.251 | 10.278 | yes |
| 8–10 | 19 | 9.169 | 12.568 | no — 19 < 30 pairs |
| 10–13 | 78 | 10.805 | **23.395** | yes |
| **13–986** | **0** | — | — | **no — zero pairs** |
| 986–997 | **294** | 991.102 | 16.168 | no — beyond the 13 km fit lag |

**Fitting method: weighted least squares, weights = pair counts**, best
candidate range by weighted SSE over a candidate grid (first-wins tie-break).

**Two things worth flagging.**

1. **The spherical alternative fits BETTER by the objective actually used**
   (SSE 4006.64 vs 5269.79, 24% lower) and is nonetheless not the model used.
   That is a recorded decision, not an accident — but the used model is not
   the best-fitting one.
2. **The fitted sill (21.394) exceeds the sample variance of y (15.063) by
   42%.** A variogram whose sill is well above the data's own variance is
   being driven by the last supported bin (10–13 km, γ̂ = 23.4, itself above
   the sample variance), not by an asymptote the data reached.

**On the "~68% nugget" figure cited in E2.2 and the walkthroughs:** that is a
*different quantity* from c₀/(c₀+c₁). It is γ̂(0–1 km) ≈ 10.2 divided by the
**sample variance** 15.06 ≈ 0.68. The fitted model's nugget ratio is
**0.368**. Both are defensible measurements; they are not interchangeable,
and the gap between them exists only because the fitted sill overshoots the
sample variance. If the strategic decision leans on "68% of variance is
unstructured", the supporting number is the raw short-lag semivariance ratio,
not the fitted nugget fraction.

---

## Q3. Variogram identifiability ← **the answer you need**

**The lag distribution is bimodal with an empty region between the modes, and
the fitted range falls inside the empty region.**

Across all 35 stations: **595 pairs**, of which **301 within-cluster** and
**294 between-cluster**.

| quantity | value |
|---|---|
| **largest within-cluster lag** | **12.022 km** |
| **smallest between-cluster lag** | **986.036 km** |
| largest between-cluster lag | 995.997 km |
| **width of the empty region** | **974.014 km** |
| **pairs with lag strictly between 12.022 and 986.036 km** | **0** |
| **fitted range a** | **21.611 km** |

Pairs per fitting bin are in Q2's table. In summary: **278 pairs across the
four bins the fit actually used** (102 + 48 + 50 + 78), all at lags **≤ 13
km**; 23 pairs in two bins excluded for insufficient support (4 and 19,
against a 30-pair minimum); 294 pairs at ~991 km, excluded as beyond the fit
lag; and **zero pairs anywhere between 13 km and 986 km**.

### Is the fitted range constrained by data?

**No. It is extrapolated, and the estimator itself says so.**

- The fitted range **21.611 km is 1.8× the largest lag at which any pair
  exists (12.022 km)**. There is no empirical semivariance at 21.6 km, or
  anywhere within 974 km of it.
- The fit reports **`range_at_candidate_ceiling = True`** — the project's own
  flag meaning *"the range sat at the top of the candidate grid: unconstrained
  from above, it exceeds what the supported lags can resolve."* The same flag
  is `True` in the E2.4 run's per-fold fits.
- **Residual dof = 1.** Four bins, three parameters. The fit is one
  observation away from being an interpolation of its own summary statistics.
- The last supported bin (10–13 km) has **γ̂ = 23.4, above the fitted sill of
  21.4 and above the sample variance of 15.1** — the empirical variogram is
  **still rising where the data stops**. A variogram still rising at the edge
  of support has no identified range; the fitter returns the ceiling of
  whatever candidate grid it was given.

**Stated as plainly as you asked: the range is not a measurement. It is the
upper end of the search grid, reported because the fitter must return
something. Any use of the number 21.6 km — or the ~13 km figure quoted in
earlier walkthroughs — as a physical correlation length is unsupported by
this data.** What the data does constrain is the shape of γ below ~13 km,
where 278 pairs exist.

---

## Q4. Kriging variance vs sample density

Script: `scratch/phase2_diag.py`; plot `scratch/phase2_diag.png`. Value-
independent — uses only the fitted variogram (Q2) and station geometry.

**Window:** the eastern cluster's bounding box, **57.3 km²**, 21 stations,
**366.8 stations / 1000 km²**, evaluated on a 45×45 grid (2025 targets).
(The western cluster or a full-CCZ window would be dominated by
extrapolation far from any datum and would say nothing about density.)

| × current | n samples | samples / 1000 km² | mean σ²_OK | mean σ_OK | % reduction |
|---|---|---|---|---|---|
| 1 | 21 | 366.8 | **14.886** | **3.858** | 0.00% |
| 1.5 | 37 | 646.3 | 12.724 | 3.567 | 14.52% |
| 2 | 46 | 803.5 | 12.382 | 3.519 | 16.82% |
| 3 | 70 | 1222.7 | 11.929 | 3.454 | 19.86% |
| 4 | 85 | 1484.7 | 11.780 | 3.432 | 20.87% |
| **5** | 121 | **2113.5** | 11.540 | 3.397 | 22.48% |
| 6 | 141 | 2462.9 | 11.448 | 3.383 | 23.10% |
| 8 | 189 | 3301.3 | 11.298 | 3.361 | 24.10% |
| 10 | 216 | 3772.9 | **11.238** | **3.352** | **24.51%** |

Marginal σ² reduction per added sample: 0.1351 (×1→1.5), 0.0381, 0.0189,
0.0100, 0.0067, 0.0046, 0.0031, 0.0022.

- **(a) KNEE: ×5 current density ≈ 2114 samples / 1000 km².** The marginal
  rate there (0.00665) first falls below 5% of the initial rate (0.00676).
- **(b) ASYMPTOTE: σ² → the nugget, 7.880** (σ ≈ 2.807). At ×10 the sweep
  reaches 11.238 — still **3.36 above the floor**, and approaching it slowly.
- **Current density relative to the knee: 366.8 / 2113.5 = 0.17×.** Current
  sampling sits at about **one fifth of the knee density**.

**The number that matters more than the knee:** mean σ_OK at current density
is **3.858 kg/m²**, against a field standard deviation of **3.881 kg/m²**.
**Kriging's predictive uncertainty at current density is 99.4% of simply
quoting the field's own spread.** A 10× increase in sampling takes it to
3.352 — still **86% of the field sd**. Density is not the binding
constraint; the nugget is.

---

## Q5. Station geometry

| cluster | n | NN min | NN median | NN max | max within-cluster lag | bbox area | stations / 1000 km² |
|---|---|---|---|---|---|---|---|
| Eastern | **21** | **0.054 km** | **0.349 km** | **0.716 km** | 11.168 km | **57.3 km²** | **366.8** |
| Western | **14** | **0.156 km** | **0.532 km** | **0.857 km** | 12.022 km | **79.7 km²** | **175.6** |

At the 2 km single-linkage used by the within-cluster gate, the 35 stations
form **5 sites of 8, 7, 7, 7, 6** (eastern = 3 sites, western = 2).

Bounding areas are lat/lon bounding boxes converted at the cluster's mean
latitude — an over-estimate of the sampled area, so the densities above are
if anything conservative.

---

## Q6. QRF zero-width sd

**Fraction of predictions with sd = 0: 0 of 97 scored predictions = 0.00%**,
in the committed E2.4 run. Every RF fold across all four designs reports
`zero_width_training_predictions = 0` (47 fold-level records).

**Cause — none of the three offered, and the reason matters:**

- **Not insufficient trees.** `n_estimators = 500`.
- **Not the covariate-cell structure collapsing quantiles.** The 4-cell
  structure is what *prevents* zero width here: each cell holds **6 to 11
  distinct y values** (cells 0–2: 7 stations, 6 distinct; cell 3: 14
  stations, 11 distinct), so no leaf population is single-valued. *(Note:
  `docs/walkthroughs/E2.3.md` states "every cell has ≥ 7 distinct y" — the
  measured minimum is **6**. The substantive claim, that no cell is
  single-valued, holds.)*
- **Degenerate leaf membership is the mechanism that WOULD cause it**, and it
  is guarded rather than assumed: a constructed 14-station constant-y cell
  yields exactly 14 zero-width predictions with sd 0.0, and the count is
  pinned in the suite so a corpus change producing a single-valued cell shows
  up as a finding rather than a silent 0.

**A real sd-collapse did occur in E2.3 and was fixed.** With
`aggregate_leaves_first = False`, per-tree quantile functions were averaged
and collapsed to sd 0 on distinct X. The fix pools all retained leaf
populations across trees (Meinshausen) before taking quantiles;
`aggregate_leaves_first = True` is recorded in the run's hyperparameters with
that reason attached.

**Defect or structural? Neither, today.** Zero-width sd is a structural
possibility of QRF that this corpus does not trigger, and the one instance
that *was* a defect (per-tree averaging) is fixed and observed.

---

## Q7. Covariate cell structure

**Distinct covariate value combinations across the 35 training stations: 4.**
(`distinct_cell_count = 4`, `shared_cell_count = 35` — every station shares
its cell with at least one other.)

| cell | stations | distinct y | mean y | sd y | within-cell SS |
|---|---|---|---|---|---|
| 0 | **7** | 6 | 21.657 | 2.979 | 53.26 |
| 1 | **7** | 6 | 15.143 | 2.658 | 42.38 |
| 2 | **7** | 6 | 20.229 | 4.194 | 105.55 |
| 3 | **14** | 11 | 20.314 | 3.193 | 132.54 |

**The 0.348 ceiling, recomputed here from the manifest's `cell_groups` and
the corpus y:**

```
within-cell SS = 333.7      total SS = 512.2
R²_max = 1 − 333.7 / 512.2 = 0.3484
```

**Derivation:** stations sharing a cell have **identical X and different y**.
No function of X can distinguish them, so within-cell variance is irreducible
error. The ceiling is one minus its share of total variance.

**Scope: it binds ANY covariate-driven model, not RF alone.** With 4 distinct
rows the design matrix has rank ≤ 4 against 8 covariates. **Ordinary kriging
is NOT bound by it** — kriging predicts from coordinates, which remain
distinct for all 35 stations. Consequence for reading any comparison table:
if RF underperforms kriging on this fixture, the honest explanation is that
RF is fighting a 0.348 ceiling kriging never sees, not that kriging is the
better method.

---

## WHAT THESE NUMBERS RULE OUT

**1. That this dataset supports a fitted spatial correlation range.** The
range (21.6 km) sits 1.8× beyond the largest lag with any data, inside a
974 km window containing zero pairs, flagged by the fitter's own
`range_at_candidate_ceiling = True`, with 1 residual degree of freedom and an
empirical variogram still rising where support ends. **Any statement of the
form "nodule abundance is spatially correlated out to X km" is not
defensible from this corpus.** What is defensible is the shape of γ below
13 km.

**2. That either model has demonstrated skill.** Every pooled R² is negative
on both blocked designs. Kriging does not beat the mean baseline at the
honest within-cluster gate (−0.0003 RMSE pooled; margin 0.003× the
fold-to-fold spread) and ties it exactly across clusters by construction. RF's
+0.045 RMSE is 0.053× the fold spread and is computed on synthetic
covariates. **"The model beats the baseline" is not available in any form.**

**3. That the across-cluster comparison says anything about model quality.**
With a ~22 km range against a 986 km gap, kriging reverts to the training
cluster's mean and reproduces the baseline to 12 decimal places. That design
measures the difference between two cluster means (±1.886 kg/m²) and cannot
rank estimators. **Reporting the 2-fold result as a generalization test would
be wrong.** It also only scored 1 of 2 folds — kriging refused the 14-station
fit.

**4. That more sampling at these locations fixes it.** Ten times the current
density reduces mean kriging variance by 24.5%, from σ = 3.86 to 3.35 against
a field sd of 3.88. At current density kriging's predictive uncertainty is
**99.4% of the field's own spread** — it is, in variance terms, barely
distinguishable from quoting the mean. The floor is the nugget (σ ≈ 2.81),
reachable only asymptotically. **Densification inside the existing footprint
is not the lever;** the unstructured short-range component is.

**5. That covariates can be rescued by a better model.** Four distinct
covariate rows for 35 stations cap *any* covariate-driven model at R² =
0.348, before considering that the covariates are synthetic. Changing the
algorithm cannot move that ceiling — only a DEM whose cells re-separate the
stations can.

**6. That the "~68% nugget" and the fitted nugget fraction are the same
claim.** They are 0.68 and 0.368 respectively, and the gap exists because the
fitted sill overshoots the sample variance by 42%. If that figure is load-
bearing for a decision, cite the short-lag semivariance ratio and say so.

### What survives

Two measurements are real, DEM-independent, and unaffected by all of the
above: **the short-lag semivariance structure below 13 km** (278 pairs, real
coordinates, real y, no covariates), and **the station geometry** (2 clusters,
5 sites, the density and nearest-neighbour figures in Q5). The engine itself
is also demonstrably working — the refusals, the exact baseline ties, and the
negative R² values are the machinery reporting honestly rather than failing
quietly.
