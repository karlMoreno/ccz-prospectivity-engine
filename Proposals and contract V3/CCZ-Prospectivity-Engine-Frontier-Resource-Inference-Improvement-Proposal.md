# CCZ Prospectivity Engine
## Frontier Resource Inference Improvement Proposal

**Status:** Post-alpha strategic improvement proposal  
**Purpose:** Define the strongest research and product direction for the CCZ Prospectivity Engine after completion of the current alpha and Path C corpus integration.  
**Relationship to existing documents:** This proposal is **additive**. It does not replace the current *CCZ Prospectivity Engine Proposal v3* or *CCZ Prospectivity Engine Alpha Proposal v3*. The alpha should be completed as designed. This proposal defines what should happen **after the alpha is scientifically real**.  
**Strategic objective:** Extract the maximum research, engineering, and career value from the CCZ project before transitioning the same inference architecture to lunar south-pole resource prospectivity.

---

# 1. Executive Summary

The CCZ Prospectivity Engine is already becoming a strong engineering artifact:

- evidence-typed ingestion,
- strict source provenance,
- MASS / COUNT / COVER / GRID / GRADE separation,
- ordinary kriging,
- quantile random forest,
- mandatory baseline comparison,
- spatial cross-validation,
- paired uncertainty,
- TS-6 comparison,
- economic overlays,
- reproducible manifests,
- read-only API,
- interactive map viewer,
- and a claim guard that can refuse weak scientific results.

Once the remaining real Path C datasets, real terrain, real TS-6 reference, and real economic assumptions are incorporated, the alpha will answer:

> **Given the currently available open physical observations, where are polymetallic nodules likely to be abundant, and how uncertain is that prediction?**

That is a good project and potentially a good paper.

It is not yet the strongest version of the project.

The recommended post-alpha breakthrough is to stop treating the five evidence classes merely as ingestion categories and instead make them the **central scientific problem**.

The project should become:

> # A Frontier Resource Inference Engine
>
> A system for inferring a hidden resource field from multiple imperfect observation modalities, each with its own fidelity, bias, support scale, provenance, and uncertainty — and validating the resulting model by replaying history and predicting measurements that were not yet available at training time.

The CCZ becomes the first benchmark domain.

The lunar south pole becomes the second.

The long-term thesis is therefore no longer:

```text
CCZ MODEL
    +
MOON MODEL
```

It becomes:

```text
             FRONTIER RESOURCE INFERENCE ENGINE
                           |
             +-------------+-------------+
             |                           |
             v                           v
      CCZ BENCHMARK                LUNAR BENCHMARK
 polymetallic nodules            south-pole volatiles
             |                           |
             +-------------+-------------+
                           |
                           v
             DOES THE INFERENCE METHOD
          TRANSFER ACROSS FRONTIER DOMAINS?
```

That is a substantially stronger engineering and research story.

---

# 2. Why the Previous Commercial Roadmap Should Not Be the Immediate Priority

The earlier commercial-improvement direction proposed:

```text
Prospectivity
    ↓
Value of Information
    ↓
Expedition Optimization
    ↓
Mine Planning
    ↓
Knowledge Graph
    ↓
Investor Intelligence
```

The problem is not that these ideas are bad.

The problem is that most of them require information the project does not currently possess:

- true vessel day costs,
- sampling costs,
- AUV deployment constraints,
- operator budget constraints,
- campaign objectives,
- proprietary box-core observations,
- private resource-block geometry,
- actual collector throughput,
- internal recovery assumptions,
- real processing economics,
- customer risk tolerances.

Without these inputs, a campaign optimizer risks optimizing assumptions invented by the project itself.

Likewise, a detailed NPV engine risks producing false precision if geological uncertainty is overwhelmed by guessed commercial parameters.

The strongest near-term improvement should therefore satisfy four rules:

```text
1. Uses data the project can actually obtain.
2. Produces a scientific claim that can be tested.
3. Extends the current architecture instead of replacing it.
4. Transfers naturally to the lunar south pole.
```

Multi-fidelity inference + historical replay satisfies all four.

---

# 3. The Existing Project Contains the Seed of the Breakthrough

The existing data architecture already separates five fundamentally different types of evidence:

```text
[MASS]   physical recovered nodule mass / concentration
[COUNT]  nodule count / density
[COVER]  visible nodule cover from imagery
[GRID]   compiled or interpolated regional resource surfaces
[GRADE]  nodule chemistry / metal composition
```

The current integrity rules deliberately prevent these classes from being silently conflated.

Examples:

```text
COVER -> never silently becomes kg/m²

GRID -> never becomes an independent ground-truth station

COUNT -> can become mass only through an explicitly recorded
         mean-nodule-mass assumption

GRADE -> chemistry only; joins to abundance evidence
```

This was originally designed as an ingestion-safety rule.

It should become the next model.

Instead of asking only:

\[
P(A(x)\mid \text{MASS observations})
\]

where \(A(x)\) is true nodule abundance, the engine should ask:

\[
P(A(x)\mid
MASS,\,
COUNT,\,
COVER,\,
terrain,\,
remote\ sensing,\,
regional\ priors)
\]

while preserving the distinction between the observation processes.

---

# 4. Improvement 1 — Multi-Fidelity Resource Inference

## 4.1 Central Idea

Treat the true abundance field as **latent**:

\[
A(x)
\]

where:

\[
A(x) = \text{true nodule abundance at location }x
\]

The system never observes \(A(x)\) perfectly.

Instead, different measurement systems observe different manifestations of it.

```text
                         HIDDEN RESOURCE FIELD
                              A(x) kg/m²
                                  |
               +------------------+------------------+
               |                  |                  |
               v                  v                  v
            [MASS]             [COUNT]             [COVER]
          box cores          nodules/m²            imagery
               |                  |                  |
       direct observation    measurement model   measurement model
               |                  |                  |
               +------------------+------------------+
                                  |
                                  v
                          POSTERIOR RESOURCE
                              μ(x), σ(x)
                                  |
                      +-----------+-----------+
                      |                       |
                      v                       v
                   [GRID]                  [GRADE]
              prior / benchmark        correlated field
```

The evidence classes remain separate.

The fusion model learns how they relate.

---

# 5. Measurement Models

## 5.1 MASS

MASS remains the highest-fidelity target.

A simple observation model is:

\[
y_i^{(M)}
=
A(x_i)
+
b_{m_i}
+
\epsilon_i
\]

where:

- \(y_i^{(M)}\) = observed abundance,
- \(A(x_i)\) = latent abundance,
- \(b_{m_i}\) = sampling-method bias,
- \(\epsilon_i\) = measurement noise.

This permits the engine to model known differences between:

```text
box core
grab sampler
free-fall grab
dredge
experimental chamber
```

rather than pretending every sample method measures the same thing equally well.

---

## 5.2 COUNT

COUNT should not be converted into deterministic MASS.

Instead:

\[
N_i
\sim
\operatorname{Poisson}
\left(
a_i \lambda(x_i)
\right)
\]

where:

- \(N_i\) = observed nodule count,
- \(a_i\) = sampled area,
- \(\lambda(x_i)\) = latent nodule density.

Mass is related through the nodule-mass distribution:

\[
A(x)
\approx
\lambda(x)\,E[M_n(x)]
\]

where:

\[
M_n = \text{mass of one nodule}
\]

The important difference from a direct COUNT→MASS conversion is:

\[
E[M_n]
\]

has uncertainty.

That uncertainty propagates into the final abundance field.

---

## 5.3 COVER

COVER must remain an indirect observation.

Do not use:

\[
\text{cover percentage}
\Rightarrow
\text{kg/m²}
\]

Instead model:

\[
P(C_i \mid A(x_i), S_i, B_i, R_i)
\]

where:

- \(C_i\) = visible nodule cover,
- \(S_i\) = size distribution,
- \(B_i\) = burial / visibility effect,
- \(R_i\) = regional or survey-specific calibration state.

The system can then learn:

```text
high visible cover
        +
typical nodule size
        +
known burial behavior
        ↓
probability distribution over abundance
```

rather than a single fabricated conversion factor.

---

## 5.4 GRID

GRID should remain:

```text
benchmark
regional prior
historic estimate
```

not ground truth.

The fusion layer may optionally use a GRID surface as a prior:

\[
A(x) \sim P_{\text{prior}}(A(x))
\]

but the system must retain the ability to run:

```text
WITH GRID PRIOR
vs
WITHOUT GRID PRIOR
```

so the benchmark cannot silently leak into the prediction target.

---

## 5.5 GRADE

GRADE should initially remain a correlated field:

\[
G_m(x)
\]

for metal \(m\), such as:

```text
Ni
Cu
Co
Mn
```

Later:

\[
P(A(x), G(x))
\]

can support resource-value inference.

This should not be the first multi-fidelity milestone.

---

# 6. Improvement 2 — Historical Replay Engine

## 6.1 Why This Matters

Spatial cross-validation is necessary.

It is not the strongest test available.

The CCZ contains decades of observations collected at different times.

The engine should exploit chronology.

For cutoff time \(t\):

\[
D_{\text{train}}(t)
=
\{
d_i :
available\_date_i \le t
\}
\]

and:

\[
D_{\text{future}}(t)
=
\{
d_i :
available\_date_i > t
\}
\]

The engine trains using only the first set.

The second set remains completely hidden.

Then the engine predicts the hidden observations.

This answers:

> **Could this model have predicted measurements that had not yet been collected?**

That is a much harder and more intuitive claim than:

> "The model achieved a certain CV RMSE."

---

# 7. Historical Replay Architecture

```text
Observation Corpus
      |
      v
+--------------------+
| temporal metadata  |
+----------+---------+
           |
           v
     ReplaySnapshot(t)
           |
     +-----+------+
     |            |
     v            v
 TRAINING       FUTURE
 evidence       evidence
     |            |
     v            |
 Model fit        |
     |            |
     v            |
Prediction        |
     |            |
     +------+-----+
            |
            v
       REVEAL FUTURE
            |
            v
      EvaluationReport
```

---

# 8. New Validation Regime

The engine should eventually report at least three independent validation classes.

## 8.1 Spatial Holdout

Existing concept:

\[
\text{Train spatially separated from test}
\]

Purpose:

```text
Can the model interpolate / transfer spatially?
```

---

## 8.2 Leave-One-Program-Out

Example:

```text
Train:
DOMES
SO268
BGR

Hold out:
IOM
```

Then rotate.

Purpose:

```text
Can the model generalize across
sampling programs,
contract areas,
campaigns,
and methodologies?
```

This is particularly important because the current corpus risks learning campaign-specific structure.

---

## 8.3 Temporal Replay

Example:

```text
knowledge cutoff:
2010

train:
all information available by 2010

hide:
later observations

predict:
later stations

reveal:
actual later measurements
```

Purpose:

```text
Could the system predict genuinely future evidence?
```

---

# 9. Improvement 3 — Dataset Value / Evidence Ablation

Once the Path C corpus is substantially complete, the system should determine what each dataset actually contributes.

For source \(S_j\):

\[
\Delta_j
=
Skill(D)
-
Skill(D \setminus S_j)
\]

For an entire evidence class:

\[
\Delta_{\text{MASS}}
\]

\[
\Delta_{\text{COUNT}}
\]

\[
\Delta_{\text{COVER}}
\]

\[
\Delta_{\text{terrain}}
\]

\[
\Delta_{\text{imagery}}
\]

\[
\Delta_{\text{GRID}}
\]

---

# 10. Example Evidence Contribution Report

Illustrative format only:

| Evidence Configuration | Replay RMSE | 90% Interval Coverage | Unsupported Area | Program Transfer Score |
|---|---:|---:|---:|---:|
| MASS only | — | — | — | — |
| MASS + terrain | — | — | — | — |
| + COUNT | — | — | — | — |
| + COVER | — | — | — | — |
| + imagery-derived size | — | — | — | — |
| + GRID prior | — | — | — | — |

The values are generated by the engine.

No desired result should be assumed.

---

# 11. Why Ablation Is Strategically Important

The 60+ Path C entries are not 60 independent MASS datasets.

They include:

```text
MASS
COUNT
COVER
GRADE
GRID
duplicate publication families
historic compilations
discovery hubs
contact targets
image datasets
```

This means the interesting question is not simply:

> "How much does sample count increase?"

The stronger question is:

> **Which types of evidence actually improve unseen-resource inference?**

That is a publishable scientific question by itself.

It also generalizes beyond the CCZ.

---

# 12. Improvement 4 — Computer Vision as an Evidence Factory

Computer vision should be used.

It should **not** become the identity of the project.

The goal is not:

> "Build a better segmentation network."

The goal is:

> "Convert large optical survey archives into typed, uncertainty-bearing resource evidence."

The image system should emit:

```text
ImageEvidence
├── image_id
├── source_id
├── longitude
├── latitude
├── observed_area_m2
├── nodule_count
├── nodule_density_m2
├── visible_cover_percent
├── estimated_size_distribution
├── estimated_exposed_area
├── burial_visibility_model
├── segmentation_uncertainty
├── model_version
└── provenance
```

That output feeds the same evidence-fusion architecture.

---

# 13. Computer-Vision Architecture

```text
Raw CCZ imagery
      |
      v
+---------------------+
| Image SourceAdapter |
+----------+----------+
           |
           v
+---------------------+
| Nodule Segmenter    |
+----------+----------+
           |
           v
+---------------------+
| Geometry / Scale    |
| Calibration         |
+----------+----------+
           |
           v
+---------------------+
| ImageEvidence       |
| COUNT / COVER / SIZE|
+----------+----------+
           |
           v
 Multi-Fidelity Model
```

The CV model is therefore a **sensor adapter**, not the resource model itself.

---

# 14. Improvement 5 — Resource Support / Confidence Layer

A user should be able to distinguish:

```text
high predicted abundance
```

from:

```text
high confidence in predicted abundance
```

The project already exposes uncertainty.

The next step is a more explicit resource-support classification.

Possible factors:

\[
Support(x)
=
f(
station\ density,
distance\ to\ observations,
variogram\ support,
source\ fidelity,
model\ disagreement,
prediction\ interval,
cross\ program\ transfer,
replay\ performance
)
\]

Possible research labels:

```text
HIGH SUPPORT
MODERATE SUPPORT
LOW SUPPORT
UNSUPPORTED
```

These labels must not be presented as formal CRIRSCO / SEC / JORC resource categories unless reviewed and signed off by the appropriate qualified professional.

---

# 15. Resource Support Viewer

Example:

```text
CELL: 11.82°N, 128.14°W

Predicted abundance:
18.9 kg/m²

Prediction interval:
12.1 – 24.7 kg/m²

RESOURCE SUPPORT:
MODERATE

WHY:
+ 3 nearby MASS observations
+ COVER support
+ terrain inside training envelope
- nearest direct MASS station 43 km away
- model disagreement elevated
- temporal replay performance weak in this region
```

This turns uncertainty from a number into an interpretable evidence structure.

---

# 16. Improvement 6 — Licensing-Aware Model Runs

The corpus mixes licenses.

The architecture should explicitly distinguish research use from potential commercial use.

Introduce:

```text
RunPurpose
├── RESEARCH
└── COMMERCIAL_COMPATIBLE
```

and:

```text
LicensePolicy
├── permits_ingestion
├── permits_derived_use
├── permits_commercial_use
├── permits_redistribution
├── attribution_requirements
└── notes
```

Then the system can build:

```text
ALL-AVAILABLE RESEARCH MODEL
              vs
COMMERCIAL-COMPATIBLE MODEL
```

---

# 17. License Sensitivity as an Experiment

Define:

\[
\Delta_{\text{license}}
=
Skill_{\text{research}}
-
Skill_{\text{commercial-compatible}}
\]

This answers:

> **How much predictive capability depends on data that cannot safely support a commercial product?**

That is strategically important before any commercialization effort begins.

A future commercial launch would still require actual legal review.

This feature merely ensures licensing cannot be ignored by the architecture.

---

# 18. Improvement 7 — Dataset Contribution Leaderboard

The viewer should show what information the model relies on.

Example:

```text
EVIDENCE CONTRIBUTION

SO268 MASS                    +++++
DOMES MASS                    ++++
Terrain                       +++
SO268 COVER                   ++
Image size distribution       ++
TS-6 prior                    +
Dataset X                     0
Dataset Y                     -
```

A negative contribution is scientifically valuable.

It may indicate:

```text
measurement incompatibility
sampling bias
regional domain shift
bad normalization
historical methodology mismatch
```

The system should not automatically discard negative contributors.

They should become investigation targets.

---

# 19. Improvement 8 — Model Disagreement Surface

The engine already contains multiple estimators.

Instead of using model comparison only in tables, create:

\[
D(x)
=
Var(
\hat A_1(x),
\hat A_2(x),
\ldots,
\hat A_k(x)
)
\]

where each estimator produces a prediction.

This becomes:

```text
MODEL CONSENSUS MAP
```

Regions where:

```text
kriging
random forest
multi-fidelity model
```

strongly disagree deserve explicit attention.

High model disagreement should not be hidden inside a single uncertainty layer.

---

# 20. Improvement 9 — Counterfactual Evidence Explorer

The viewer should allow:

```text
remove MASS dataset X
remove all COVER
remove GRID prior
remove terrain
remove imagery
use only pre-2010 evidence
```

Then the prediction surface updates.

This exposes the model's dependency structure.

Example:

```text
WITH COVER:
rich zone extends 80 km east

WITHOUT COVER:
zone disappears

Interpretation:
the extension is supported primarily by image-derived evidence,
not direct MASS samples.
```

This is significantly more informative than a static heat map.

---

# 21. The New Viewer Concept

The future viewer should become an **interactive scientific replay environment**.

```text
+--------------------------------------------------------------+
|                CCZ RESOURCE REPLAY                           |
+--------------------------------------------------------------+
| TIME                                                         |
| [1970 -------- 1990 -------- 2010 -------- 2020 ------ 2026] |
|                                                              |
| EVIDENCE                                                     |
| [x] MASS                                                     |
| [x] COUNT                                                    |
| [x] COVER                                                    |
| [x] TERRAIN                                                  |
| [ ] GRID PRIOR                                               |
|                                                              |
| HOLDOUT                                                      |
| Program: SO268                                               |
| Status: HIDDEN                                               |
|                                                              |
| MODEL                                                        |
| Multi-Fidelity Resource Model                                |
|                                                              |
|             +---------------------------+                    |
|             |                           |                    |
|             |          CCZ MAP          |                    |
|             |                           |                    |
|             +---------------------------+                    |
|                                                              |
| REPLAY METRICS                                               |
| RMSE                       ...                               |
| interval coverage          ...                               |
| high-resource capture      ...                               |
|                                                              |
| [ REVEAL FUTURE OBSERVATIONS ]                               |
+--------------------------------------------------------------+
```

---

# 22. Replay Interactions

The viewer should support experiments such as:

```text
Use only data available before 1980.

Use only data available before TS-6.

Hide SO268.

Hide IOM.

Hide all imagery.

Hide all historic GRID products.

Train eastern CCZ -> predict western CCZ.

Train contractor areas -> predict APEI.

Train old programs -> predict modern programs.

Reveal future observations.
```

The viewer becomes a research instrument rather than simply a presentation layer.

---

# 23. New Scientific Questions the Project Can Answer

The post-alpha project should be designed around questions rather than features.

## Q1

\[
\boxed{
Can sparse MASS observations support useful CCZ abundance prediction?
}
\]

---

## Q2

\[
\boxed{
Do COUNT observations improve predictions beyond MASS alone?
}
\]

---

## Q3

\[
\boxed{
Does imagery-derived COVER improve out-of-program prediction?
}
\]

---

## Q4

\[
\boxed{
How much uncertainty reduction comes from terrain covariates?
}
\]

---

## Q5

\[
\boxed{
Does TS-6 act as a useful prior or merely leak historic assumptions?
}
\]

---

## Q6

\[
\boxed{
Can models trained on historic programs predict modern observations?
}
\]

---

## Q7

\[
\boxed{
Which evidence sources actually transfer across CCZ regions?
}
\]

---

## Q8

\[
\boxed{
How much resource-model skill is lost under commercial-license restrictions?
}
\]

---

# 24. Success Does Not Require the Model to Win

The project's existing honesty philosophy should remain.

All of the following are valid outcomes.

### Outcome A

Multi-fidelity inference strongly improves future-data prediction.

Result:

```text
SUCCESS
```

---

### Outcome B

COVER improves interpolation but fails program transfer.

Result:

```text
IMPORTANT DOMAIN-SHIFT FINDING
```

---

### Outcome C

COUNT adds little information beyond MASS.

Result:

```text
USEFUL NEGATIVE RESULT
```

---

### Outcome D

Random forest performs well under ordinary CV but fails temporal replay.

Result:

```text
VALIDATION WARNING
```

---

### Outcome E

The mean baseline survives every hard validation regime.

Result:

```text
CURRENT OPEN DATA ARE INSUFFICIENT
```

This would still be a scientifically meaningful outcome.

---

# 25. Improvement 10 — Generalize the Architecture Before Moving to the Moon

The transition to the lunar south pole should not begin as a duplicate repository.

Before the Moon implementation, extract the generic inference abstractions.

Target conceptual structure:

```text
                 FrontierResourceEngine
                          |
        +-----------------+------------------+
        |                 |                  |
        v                 v                  v
 ResourceEvidence   ObservationModel   LatentFieldModel
        |                 |                  |
        v                 v                  v
   adapters          measurement        inference
                        physics
```

---

# 26. Proposed Generic Interfaces

```text
ResourceEvidence
├── location
├── observed_quantity
├── support_geometry
├── evidence_type
├── fidelity
├── uncertainty
├── source
└── provenance
```

```text
ObservationModel
├── evidence_type
├── forward_model(latent_state)
├── likelihood(observation, latent_state)
└── provenance()
```

```text
LatentFieldModel
├── fit(evidence)
├── predict(location)
├── uncertainty(location)
└── provenance()
```

```text
ReplayExperiment
├── cutoff
├── included_sources
├── hidden_sources
├── validation_design
└── result
```

---

# 27. CCZ Implementation

```text
CCZ ResourceEvidence
├── MASS
├── COUNT
├── COVER
├── GRID
└── GRADE
```

Terrain:

```text
bathymetry
slope
roughness
curvature
TPI
BPI
```

Target:

```text
polymetallic-nodule abundance
```

---

# 28. Lunar Implementation

The lunar south-pole port can use the same architecture with different adapters and observation models.

Potential evidence:

```text
direct / near-direct:
lander measurements
drill measurements
sample measurements

remote:
neutron spectroscopy
radar
thermal observations
spectroscopy

terrain:
LOLA elevation
slope
curvature
illumination
permanent-shadow geometry

priors:
published volatile / ice models
```

Target:

```text
water / ice prospectivity
or
volatile concentration
```

The scientific question becomes:

> **Can the same inference architecture remain useful when the observation modalities, spatial scales, physical measurement processes, and ground-truth density change completely?**

---

# 29. Why the Moon Port Becomes More Valuable Under This Strategy

Without the generalized inference architecture:

```text
CCZ ML project
+
Moon ML project
```

can look like two unrelated portfolio pieces.

With this architecture:

```text
Frontier Resource Inference
        |
        +--> CCZ validation domain
        |
        +--> lunar validation domain
```

becomes one coherent research program.

The contribution shifts from:

> "I made two maps."

to:

> "I developed and tested a reusable inference framework for frontier-resource environments where direct ground truth is sparse and heterogeneous remote observations dominate."

---

# 30. Proposed Repository Evolution

Do not restructure the alpha before it is complete.

Post-alpha, evolve carefully.

```text
engine/
└── prospectivity/
    ├── domain/
    ├── ingestion/
    ├── provenance/
    ├── estimators/
    ├── validation/
    │   ├── spatial/
    │   ├── program_holdout/
    │   └── temporal_replay/
    │
    ├── evidence/
    │   ├── base.py
    │   ├── mass.py
    │   ├── count.py
    │   ├── cover.py
    │   ├── grid.py
    │   └── grade.py
    │
    ├── observation_models/
    │   ├── base.py
    │   ├── mass_model.py
    │   ├── count_model.py
    │   └── cover_model.py
    │
    ├── fusion/
    │   ├── latent_field.py
    │   └── multi_fidelity.py
    │
    ├── replay/
    │   ├── snapshot.py
    │   ├── experiment.py
    │   ├── ablation.py
    │   └── evaluation.py
    │
    ├── support/
    │   ├── resource_support.py
    │   ├── model_disagreement.py
    │   └── license_policy.py
    │
    └── reporting/
        ├── replay_report.py
        ├── evidence_contribution.py
        └── support_report.py
```

---

# 31. Architectural Rule — Do Not Break the Existing Estimator Contract

The current estimator architecture is useful:

```text
Estimator
├── fit()
├── predict() -> mean + uncertainty
└── provenance()
```

Keep it.

Do not force multi-fidelity evidence fusion into the existing estimator interface if the abstraction becomes unnatural.

Instead:

```text
                 <<interface>>
               ObservationModel
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
   MassModel     CountModel     CoverModel
       |             |             |
       +-------------+-------------+
                     |
                     v
              LatentFieldModel
                     |
                     v
                  μ(x), σ(x)
```

The existing estimator registry remains available as:

```text
single-target model baselines
```

against which the multi-fidelity model must compete.

---

# 32. Required Baselines

The new system should never be evaluated in isolation.

At minimum compare against:

```text
Mean baseline
Ordinary kriging
Quantile random forest
MASS-only latent model
Multi-fidelity latent model
```

This allows the project to answer:

```text
Did the sophisticated evidence model actually add value?
```

rather than assuming it did.

---

# 33. Required Experiments

## Experiment 1 — MASS Only

```text
Input:
MASS

Goal:
baseline spatial resource inference
```

---

## Experiment 2 — MASS + Terrain

```text
Input:
MASS
terrain covariates
```

---

## Experiment 3 — MASS + COUNT

```text
Input:
MASS
COUNT
```

---

## Experiment 4 — MASS + COVER

```text
Input:
MASS
COVER
```

---

## Experiment 5 — MASS + COUNT + COVER

```text
Input:
all observation classes
```

---

## Experiment 6 — Add GRID Prior

```text
Input:
all above
+
historic regional model
```

---

## Experiment 7 — Leave-One-Program-Out

Example:

```text
hide SO268
train everything else
predict SO268
```

---

## Experiment 8 — Temporal Replay

Example:

```text
cutoff = 2010
hide post-2010 data
predict future observations
```

---

## Experiment 9 — Licensing Constraint

```text
research corpus
vs
commercial-compatible corpus
```

---

# 34. Metrics

The project should move beyond a single RMSE.

## Prediction Accuracy

\[
RMSE
\]

\[
MAE
\]

---

## Calibration

For nominal interval level \(p\):

\[
Coverage(p)
=
\frac{
\#\{y_i \in PI_i(p)\}
}{
n
}
\]

---

## High-Resource Capture

Example:

\[
Recall_{top\ decile}
\]

Measure how often truly high-resource observations fall inside the predicted high-resource region.

---

## Spatial Transfer

```text
leave-region-out performance
```

---

## Program Transfer

```text
leave-program-out performance
```

---

## Temporal Transfer

```text
future-observation replay performance
```

---

## Evidence Gain

\[
\Delta Skill
\]

when an evidence class or dataset is added.

---

# 35. Proposed Post-Alpha Roadmap

| Phase | Build | Purpose |
|---|---|---|
| **CCZ-A** | Finish Path C corpus | Maximize real evidence base |
| **CCZ-B** | Temporal metadata + replay engine | Turn history into validation |
| **CCZ-C** | Leave-one-program / leave-one-area validation | Test transferability |
| **CCZ-D** | Multi-fidelity MASS + COUNT model | First evidence-fusion experiment |
| **CCZ-E** | Add COVER measurement model | Use imagery without corrupting MASS |
| **CCZ-F** | Image evidence pipeline | Scale indirect observations |
| **CCZ-G** | Ablation / dataset-value engine | Quantify what information matters |
| **CCZ-H** | Resource-support + disagreement layers | Make uncertainty interpretable |
| **CCZ-I** | Licensing-aware runs | Separate research and commercial paths |
| **CCZ-J** | Hosted replay / counterfactual viewer | Publish the full scientific artifact |
| **FREEZE CCZ v1** | Paper + benchmark + dataset + viewer | Complete first frontier-resource case study |
| **MOON-A** | Extract generic evidence interfaces | Prepare portability |
| **MOON-B** | Lunar adapters + terrain | Run second domain |
| **MOON-C** | Lunar replay / sparse-truth experiments | Test cross-domain transfer |

---

# 36. Recommended Immediate Order

Do not start multi-fidelity modeling before the corpus is ready.

Recommended sequence:

```text
FINISH ALPHA
    |
    v
INGEST PATH C
    |
    v
CLEAN TEMPORAL METADATA
    |
    v
BUILD HISTORICAL REPLAY
    |
    v
BUILD PROGRAM HOLDOUTS
    |
    v
MEASURE MASS-ONLY PERFORMANCE
    |
    v
ADD COUNT
    |
    v
ADD COVER
    |
    v
RUN EVIDENCE ABLATIONS
    |
    v
ONLY THEN BUILD IMAGE SCALE-UP
```

This order prevents a complicated fusion model from hiding a basic data problem.

---

# 37. What Should Be Explicitly Deferred

## Defer More Estimator Collecting

Do not add models merely because they exist.

Examples:

```text
XGBoost
LightGBM
multiple neural nets
extra kriging variants
```

Only add a model if it tests a real scientific hypothesis.

---

## Defer Expedition Optimization

Until real operator constraints exist.

---

## Defer Full NPV Modeling

Until economic parameters can be defended.

---

## Defer Collector Digital Twin

That is a different problem and depends heavily on proprietary operational telemetry.

---

## Defer Investor Terminal

Company / regulatory intelligence can remain a separate project.

Do not let it consume the resource-inference research program.

---

## Defer Full Lunar Clone

Do not reproduce the CCZ code manually.

Extract the general inference abstractions first.

---

# 38. What Should Be Accelerated

```text
1. Path C corpus completion
2. acquisition / observation dates
3. program identifiers
4. sample-method metadata
5. geographic holdout metadata
6. historical replay
7. multi-fidelity inference
8. imagery-derived evidence
9. evidence ablation
10. cross-domain portability
```

---

# 39. New Contracts Needed

The existing frozen contracts should remain intact.

Post-alpha contracts can be additive.

---

## Contract 8 — Evidence Model

Defines:

```text
evidence_type
support_geometry
measurement_unit
fidelity
uncertainty
bias_model
observation_model
source_id
```

---

## Contract 9 — Replay Snapshot

Defines:

```text
snapshot_id
knowledge_cutoff
allowed_sources
hidden_sources
hidden_programs
hidden_regions
model_config
seed
```

---

## Contract 10 — Evidence Contribution

Defines:

```text
experiment_id
baseline_configuration
added_or_removed_evidence
metric_before
metric_after
delta
confidence
```

---

## Contract 11 — Resource Support

Defines:

```text
cell_id
support_class
direct_sample_support
remote_support
distance_to_mass
prediction_interval
model_disagreement
program_transfer_score
temporal_replay_score
reasons
```

---

## Contract 12 — License Policy

Defines:

```text
run_purpose
source_id
license
commercial_use_allowed
redistribution_allowed
derived_use_allowed
required_attribution
decision
```

---

# 40. Proposed Research Paper Direction

A stronger paper title than simply:

> "Machine Learning Prediction of Polymetallic Nodules in the CCZ"

would be something closer to:

> **Multi-Fidelity Resource Inference in the Clarion-Clipperton Zone: Integrating Physical Samples, Image Evidence, Terrain, and Historical Resource Models Under Sparse Ground Truth**

or:

> **Can Public Heterogeneous Evidence Predict Future Polymetallic-Nodule Observations? A Historical Replay Benchmark for the Clarion-Clipperton Zone**

or eventually:

> **Frontier Resource Inference Under Sparse Ground Truth: From the Deep Seafloor to the Lunar South Pole**

The third title becomes possible only after the lunar port exists.

---

# 41. Strongest Demonstration

The strongest public demo is not:

```text
Here is our current best heatmap.
```

It is:

```text
STEP 1
Set knowledge cutoff to 2010.

STEP 2
Hide all later observations.

STEP 3
Run the model.

STEP 4
Show predicted abundance and uncertainty.

STEP 5
Reveal the later observations.

STEP 6
Measure where the model succeeded and failed.
```

That is immediately understandable.

It makes scientific failure visible.

And it is extremely difficult to fake.

---

# 42. Desired End State of the CCZ Project

Before moving full-time to the Moon, the CCZ project should ideally contain:

```text
[ ] complete usable Path C corpus
[ ] source / observation chronology
[ ] program metadata
[ ] real GEBCO-class terrain
[ ] real TS-6 benchmark
[ ] real spatial validation
[ ] leave-one-program-out validation
[ ] temporal replay validation
[ ] MASS-only benchmark
[ ] COUNT measurement model
[ ] COVER measurement model
[ ] multi-fidelity inference
[ ] imagery evidence pipeline
[ ] dataset ablation
[ ] evidence contribution report
[ ] resource-support surface
[ ] model disagreement map
[ ] licensing-aware run mode
[ ] interactive replay viewer
[ ] public benchmark release
[ ] paper / technical report
```

At that point, continuing to add CCZ features probably has diminishing return.

That is the correct moment to freeze CCZ v1 and move the inference architecture to the Moon.

---

# 43. Strategic Story After Completion

Current story:

> "I built an ML pipeline for predicting polymetallic-nodule abundance from open CCZ data."

Improved story:

> **I built a reproducible resource-inference system for environments where direct ground truth is extremely sparse. The system fuses multiple observation modalities with different fidelities, explicitly models measurement bias and uncertainty, tracks the provenance of every value, and validates predictions by replaying history and predicting observations that were unavailable at training time. I first validated it on decades of Clarion-Clipperton Zone exploration evidence, then ported the same inference architecture to lunar south-pole resource prospectivity.**

That is the target.

---

# 44. Primary Recommendation

Do not spend the post-alpha period making the CCZ engine broader.

Make it **deeper**.

The recommended final CCZ evolution is:

\[
\boxed{
\text{Prospectivity}
\rightarrow
\text{Multi-Fidelity Inference}
\rightarrow
\text{Historical Replay}
\rightarrow
\text{Evidence Attribution}
\rightarrow
\text{Frontier Resource Engine}
}
\]

The most important two improvements are:

\[
\boxed{
\text{Historical Replay}
}
\]

and:

\[
\boxed{
\text{Multi-Fidelity Evidence Fusion}
}
\]

These should become the final major CCZ research chapters before the lunar transition.

---

# 45. Questions for Claude Code / Technical Review

Please review this proposal against the current CCZ Prospectivity Engine architecture.

Specifically answer:

## Architecture

1. Can the proposed `ObservationModel` / `LatentFieldModel` architecture coexist cleanly with the existing `Estimator` interface?
2. Which existing modules should remain untouched?
3. Should multi-fidelity inference live inside `engine/prospectivity/` or become a higher-level generic package?
4. What is the minimum refactor necessary before the lunar port?
5. Which abstractions should remain CCZ-specific until a second domain proves they generalize?

## Replay

6. What exact metadata is required to make historical replay scientifically defensible?
7. Should replay use source publication date, sample date, acquisition date, or multiple temporal fields?
8. How should the engine prevent information leakage from later compilations such as TS-6?
9. How should a historical snapshot be hashed and reproduced?
10. What is the strongest temporal benchmark possible from the current Path C corpus?

## Multi-Fidelity Modeling

11. What is the simplest credible first model combining MASS + COUNT?
12. Should the first implementation be:
    - hierarchical Bayesian,
    - Gaussian process,
    - multi-output Gaussian process,
    - generalized additive model,
    - another approach?
13. How should sample-method bias be represented?
14. How should observation support area be represented?
15. How should COUNT / COVER uncertainty propagate into abundance?

## Validation

16. Which leave-one-program-out designs are scientifically meaningful?
17. How should spatial and temporal validation interact?
18. Which metrics should be mandatory?
19. What baseline should the multi-fidelity model have to beat?
20. Which experiment would most quickly falsify the project thesis?

## Computer Vision

21. What is the minimum image pipeline necessary to produce useful COVER / COUNT evidence?
22. Should segmentation be built internally or initially consume an existing detector?
23. How should segmentation uncertainty enter the observation model?
24. How should buried nodules / visibility bias be represented?

## Portability

25. Which parts of the current domain model are truly CCZ-specific?
26. What interfaces should be extracted before implementing a lunar source?
27. What should deliberately remain duplicated until two implementations prove the abstraction?
28. Would a `FrontierResourceEngine` package be justified before the lunar implementation, or only afterward?

## Final Review Requested

Return:

```text
1. Major strengths
2. Major weaknesses
3. Scientific risks
4. Architectural risks
5. Features to cut
6. Features to accelerate
7. Recommended contracts
8. Recommended first 3 post-alpha phases
9. Specific codebase refactors
10. Simplest credible multi-fidelity model
11. Strongest historical replay experiment
12. Overall verdict
```

Challenge the proposal aggressively.

Do not assume multi-fidelity inference will improve prediction.

The architecture and experiments must make it easy to prove that it does **not** work if the evidence does not support it.

---

# 46. Final Recommendation

Finish the existing alpha and complete Path C.

Then make the CCZ project answer a harder question:

> **Can heterogeneous public evidence gathered over decades actually predict resource observations that were not yet available?**

Use the existing evidence-class discipline to build a proper multi-fidelity observation model.

Use the history of the CCZ to build a temporal replay benchmark.

Measure exactly which datasets and observation types improve prediction.

Expose where the system lacks support.

Freeze the CCZ version when those experiments are complete.

Then move the same inference architecture to the lunar south pole.

That produces a coherent research program:

```text
                  FRONTIER RESOURCE INFERENCE

        sparse direct samples
                 +
        heterogeneous sensors
                 +
        imperfect historic priors
                 +
        explicit measurement models
                 +
        quantified uncertainty
                 +
        temporal replay
                 |
                 v
         RESOURCE PREDICTION
            THAT CAN FAIL
           HONESTLY IN PUBLIC
                 |
        +--------+--------+
        |                 |
        v                 v
       CCZ               MOON
```

That is the recommended path for extracting the maximum value from the CCZ Prospectivity Engine before transitioning to lunar resource prospectivity.
