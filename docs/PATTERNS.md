# Design patterns in this codebase — what's earning its keep, and what isn't

Authoritative version of the Phase-1 pattern table (the copy in
`docs/prompts/phase1_prompts_v2.md` now points here). Written from reading the
code, not from the plan: §2 lists patterns that are implemented and justified,
**§3 is the reverse audit** — indirection that is *not* currently paying for
itself. §3 is the more useful half.

The standard applied throughout: a pattern earns its keep when there is a
**real variation point** — something that varies today, or is arriving on a
known schedule — and the indirection makes that variation cheap or makes a
guarantee testable. Indirection without a variation point costs more than it
buys.

---

## 1. Summary table

| Pattern | Where | Variation point (what varies / what's fixed) | Earning it? |
|---|---|---|---|
| Adapter | [`source_adapter.py:31`](../engine/prospectivity/ingestion/source_adapter.py#L31) + 4 concrete | source file formats vary / master schema fixed | **Yes** — 4 impls |
| Strategy | [`normalizer.py:29`](../engine/prospectivity/ingestion/normalizer.py#L29) + 5 concrete | per-evidence-class kg/m² policy varies / call site fixed | **Yes** — 5 impls |
| Strategy | [`recipe.py:69`](../engine/prospectivity/features/recipe.py#L69) + 8 concrete | terrain math varies / build sequence fixed | **Yes** — 8 impls |
| Registry | [`normalizer_registry.py:74`](../engine/prospectivity/ingestion/normalizer_registry.py#L74) | which normalizer for a tag / no branching | **Yes** — 5 entries + completeness |
| Registry | [`registry.py:61`](../engine/prospectivity/features/registry.py#L61) | which recipe for a covariate name | **Yes** — 8 entries + completeness |
| Specification | [`dedup_rules.py:156`](../engine/prospectivity/ingestion/dedup_rules.py#L156) | dedup predicate varies / pipeline filter fixed | **Partly** — 1 production impl (§3.1) |
| Specification *combinators* | [`specification.py:44-70`](../engine/prospectivity/ingestion/specification.py#L44) | — | **No** — unused (§3.1) |
| Template Method | [`pipeline.py:69`](../engine/prospectivity/ingestion/pipeline.py#L69) | steps vary / order fixed | **Yes** |
| Template Method | [`recipe.py:84`](../engine/prospectivity/features/recipe.py#L84) | compute varies / resolve→compute→provenance fixed | **Yes** |
| Template Method | [`engine.py:94`](../engine/prospectivity/engine.py#L94) | strategies vary / run order fixed | **Not yet** (§3.2) |
| Observer | [`recorder.py:47`](../engine/prospectivity/provenance/recorder.py#L47) | recording varies / pipeline decisions fixed | **Yes** — 2 impls |
| Null Object | [`recorder.py:66`](../engine/prospectivity/provenance/recorder.py#L66) | absence of an observer / no conditionals | **Yes** |
| Layer Supertype | [`artifact.py:61`](../engine/prospectivity/provenance/artifact.py#L61) | per-stage fields vary / chaining fields fixed | **Yes** — 3 subclasses |
| Constructor injection seam | `dataset_loader` in each file adapter | data source varies (disk / injected text) | **Yes** — every adapter test |

---

## 2. Patterns that are earning their keep

### 2.1 Adapter — the source families

```
   PANGAEA .tab      Dryad .csv/.xlsx      regional grid .csv
        │                   │                      │
   ┌────▼──────┐    ┌───────▼────────┐    ┌────────▼─────────┐
   │Pangaea    │    │TabularFile     │    │RegionalGrid      │
   │Adapter    │    │Adapter         │    │Adapter           │
   │ ▲ Boxcore │    └───────┬────────┘    └────────┬─────────┘
   │ ▲ Nodule  │            │                      │
   └────┬──────┘            │                      │
        └───────────────────┴──────────────────────┘
                            ▼
                 SourceAdapter (ABC): fetch() -> adapt()
                            ▼
                 one master-observation RawRecord shape
```

**Varies:** every source's native format — PANGAEA's `/* … */` metadata block,
three columns all named "Nodules", Dryad's spreadsheet, a grid CSV.
**Fixed:** the master schema, and `IngestionPipeline`, which knows none of it.

**Without it:** the pipeline grows a format branch per source, and adding
source #7 edits the pipeline instead of adding a class (AR-D01).

**Tests that depend on the structure:** every `test_*_adapter.py` calls
`adapter.fetch()`/`adapt()` directly and validates output against the master
schema — possible only because the boundary is a real seam
([`test_boxcore_summary_adapter.py:73`](../tests/test_boxcore_summary_adapter.py#L73),
[`test_nodule_aggregate_adapter.py:241`](../tests/test_nodule_aggregate_adapter.py#L241)).
`BoxcoreSummaryAdapter` subclassing `PangaeaAdapter` is the payoff made
concrete: a new PANGAEA source is a subclass, not a parser.

### 2.2 Strategy — normalizers and feature recipes

```
  AbundanceNormalizer (ABC)            CovariateRecipe (ABC)
   ├─ MassNormalizer                    ├─ DepthRecipe
   ├─ CountNormalizer                   ├─ HornSlopeRecipe / HornAspectRecipe
   ├─ CoverNormalizer  ← NEVER kg/m²    ├─ RoughnessRecipe
   ├─ GridNormalizer   ← forces         ├─ Profile/PlanCurvatureRecipe
   └─ GradeNormalizer     "compiled"    └─ TpiRecipe / BpiRecipe
```

**Varies:** the scientific rule per evidence class; the math per covariate.
**Fixed:** the one-line call site (`registry.normalize(record)`,
`recipe.build(grid)`).

**Without it:** the COVER rule — the single most important guard in the project
— becomes an `if` inside a large function, and cannot be mutation-tested in
isolation. It is precisely because `CoverNormalizer` is one small class that
[`test_normalizers.py:102`](../tests/test_normalizers.py#L102) could be
verified by mutation (E1.2 review) in seconds.

### 2.3 Registry — completeness as a testable property

This is the pattern doing the most *scientific* work, and the reason is
counter-intuitive: its value is not lookup, it's the **completeness
guarantee**. `assert_complete()`
([`normalizer_registry.py:92`](../engine/prospectivity/ingestion/normalizer_registry.py#L92))
turns "did we forget an evidence class?" into a test that fails loudly, and
`build_default_registry()`
([`registry.py:87`](../engine/prospectivity/features/registry.py#L87)) does the
same for covariates *plus* cross-checks each `recipe_version` against the
contract.

**Without it:** selection becomes `if/elif` on `evidence_class`, and a
forgotten class silently passes through unnormalized — the failure mode with no
symptom. Guarded by
[`test_normalizers.py:151`](../tests/test_normalizers.py#L151),
[`test_covariate_registry.py:20`](../tests/test_covariate_registry.py#L20), and
now the three-way agreement test
([`test_corpus_invariants.py:109`](../tests/test_corpus_invariants.py#L109)).

### 2.4 Template Method — fixed sequences

```
  IngestionPipeline.run()                CovariateRecipe.build()
    fetch ──► adapt ──► normalize          _resolve_windows()  ← hook
      ──► validate ──► dedup ──► append      ──► _compute()    ← hook
    (order is the contract)                  ──► + provenance  (never skippable)
```

**Varies:** the injected collaborators. **Fixed:** the order.

**Without it:** `build()`'s provenance step becomes something each of 8 recipes
must remember, and the one that forgets produces an unlabelled raster. Guarded
structurally by
[`test_covariate_recipes.py:191`](../tests/test_covariate_recipes.py#L191) (every
recipe declares its border policy) and
[`test_engine_template_method.py:34`](../tests/test_engine_template_method.py#L34).

### 2.5 Observer + Null Object — provenance recording

```
   IngestionPipeline ──emits──► PipelineObserver (ABC)
   (never reads back)                ├─ NullObserver     ← DEFAULT, no-op
                                     └─ ProvenanceRecorder
```

**Varies:** whether and how a build is recorded. **Fixed:** the pipeline's
decisions — the invariant, proved by
[`test_corpus_manifest.py:172`](../tests/test_corpus_manifest.py#L172): recorded
and unrecorded builds produce a byte-identical corpus.

**Without it:** the pipeline grows reporting state, and every pipeline test has
to care about it. Null Object specifically buys the absence of
`if self._observer is not None` at four call sites.

### 2.6 Layer Supertype — the provenance artifacts

Three artifacts, one base, identical chaining field names — see
[`contracts/PROVENANCE.md`](contracts/PROVENANCE.md). **Without it:** walking
`upstream_hashes` from a prediction back to a corpus needs a per-artifact special
case. Guarded by
[`test_provenance_artifact.py:21`](../tests/test_provenance_artifact.py#L21).

---

## 3. Reverse audit — indirection NOT earning its keep

### 3.1 Specification combinators are dead ceremony — recommend deleting

[`specification.py:44-73`](../engine/prospectivity/ingestion/specification.py#L44)
defines `_AndSpecification`, `_OrSpecification`, `_NotSpecification` plus the
`&`/`|`/`~` operators. **Production composition sites: zero.** The only callers
are the 3 tests in
[`test_specification_combinators.py`](../tests/test_specification_combinators.py).

The premise was that dedup rules would compose. E1.3 discovered they don't:
rules 4 and 5 collapsed into a single guard (`_comparable_evidence`), rule 3
moved into an adapter entirely, and rules 1–2 turned out to be the *same*
mechanical rule. What shipped is **one** production `Specification`
(`DuplicateStationSpecification`), and it is stateful — it mutates the corpus on
match — which is exactly the kind of predicate that must *not* be composed with
`&`/`|`, since evaluation order would become load-bearing and invisible.

**Recommendation: delete the three combinator classes, the operators, and their
test file** (~45 lines + 3 tests). Keep the `Specification` ABC: the pipeline
depends on that interface, `dedup_specification` is optional and swappable, and
tests inject alternatives. If a genuinely composable rule appears later,
reintroducing `&` is a 10-line change — cheaper than the standing invitation to
compose a stateful predicate incorrectly.

### 3.2 Five ABCs have zero production implementations

| ABC | Production impls | Status |
|---|---|---|
| [`TerrainSource:26`](../engine/prospectivity/terrain/source.py#L26) | **0** | **Actively bypassed** — see below |
| [`SampleSource:33`](../engine/prospectivity/samples/source.py#L33) | **0** | Consumer arriving Phase 2 |
| [`Estimator:28`](../engine/prospectivity/estimators/base.py#L28) | 0 | Phase 2 |
| [`EconomicModel:30`](../engine/prospectivity/economics/model.py#L30) | 0 | Phase 4 |
| [`TS6Reference:29`](../engine/prospectivity/ts6/reference.py#L29) | 0 | Phase 3 |

All five are Phase-0 pre-declared seams with test-only subclasses. Pre-declaring
an interface for work that lands in two phases' time is a bet, and it should be
called what it is. Two need naming individually:

**`TerrainSource` is the real problem — not merely unearned, divergent.** E1.4
built [`DemGrid.load(path)`](../engine/prospectivity/features/dem_grid.py#L79),
which reads the DEM directly and *bypasses `TerrainSource` entirely*. So the
codebase has an interface for "where does the bathymetry come from" whose only
real consumer doesn't use it, and a `FixtureTerrainSource` whose
`content_hash="sha256:synthetic-fixture"` placeholder is exactly the kind of
fake the provenance work exists to eliminate. **Recommendation:** at Checkpoint
1, either put `DemGrid` behind `TerrainSource` (the honest fix — real GEBCO vs
synthetic *is* a genuine variation point, arriving now) or delete the ABC. Do not
leave both.

**`SampleSource` is a near-miss, not ceremony.** Its concrete
`get_training_samples()` carries the MASS-only rule, and the rule itself *is*
in production (`Observation.is_training_eligible()`, called by the corpus
manifest). What's missing is the `CorpusCsvSampleSource` the Phase-0 walkthrough
promised; production currently reads the corpus directly. Phase 2's training
matrix is its natural consumer. **Recommendation:** implement it in Phase 2, or
fold the ABC away — but the variation point (CSV now, database later) is real
and near, so implementing is the better call.

**`Estimator` / `EconomicModel` / `TS6Reference`:** leave them. Phase 2 fills
`Estimator` immediately with three implementations (§4), which is the strongest
possible justification. Revisit `EconomicModel` and `TS6Reference` if Phase 3–4
slips.

### 3.3 Not a finding, checked anyway

- **Single-entry registries:** none. `NormalizerRegistry` has 5, `CovariateRegistry` 8.
- **Abstractions with one impl that is genuinely alone:** `ProvenanceRecorder`'s
  `PipelineObserver` has 2 (Null + real), which is the minimum that earns an
  interface. `SourceAdapter`, `AbundanceNormalizer`, `CovariateRecipe` all have 4+.
- **`geometry.py` clustering** is one hardcoded algorithm (single-linkage). The
  linkage *distance* is parameterized; the algorithm is not. That's correct —
  there is no second clustering algorithm in view, and adding a Strategy for one
  would be precisely the ceremony this section objects to.

### 3.4 Absent patterns where a variation point is real *today*

**None in Phase 1.** Every real variation point currently in the code has a seam.
The genuine gaps are all Phase 2, listed in §4 — and one Phase-1-adjacent item:
`TerrainSource` (§3.2), where the variation (synthetic → real GEBCO) arrives at
Checkpoint 1 and the seam exists but is unused rather than missing.

---

## 4. Where the next patterns belong (Phase 2 — report only, nothing built)

### 4.1 Estimators — Strategy + Registry, mirroring `NormalizerRegistry` exactly

**Variation point:** ordinary kriging (TS-6 parity), random forest, and the mean
baseline are three interchangeable answers to "fit and predict with paired
uncertainty." The `Estimator` ABC already exists
([`estimators/base.py:28`](../engine/prospectivity/estimators/base.py#L28)).

The registry shape is justified by a **project rule, not by taste**: CLAUDE.md
requires the mean baseline to run *alongside* any model claim. A registry makes
"every run includes the baseline" a completeness test — the same trick
`assert_complete()` plays for evidence classes — instead of a convention someone
has to remember at each call site. That argument is the strongest case for a
registry anywhere in the codebase, stronger than the normalizer one.

Also: uncertainty is always paired (CLAUDE.md), so `predict()` returning
`(mean, std)` should stay the ABC's signature — the interface makes an unpaired
prediction unrepresentable, which is worth more than a test.

### 4.2 Cross-validation splitters — Strategy

**Variation point:** spatial CV (mandatory) versus random k-fold, the latter kept
*only* as the demonstrably-wrong comparison. Two implementations, both real, both
needed simultaneously — a textbook Strategy. `engine.py` already takes
`cross_validator` as an injected callable, so this may not even need an ABC;
promote to one only if the splitters need shared state.

**Note the honest constraint from the corpus manifest:** with two clusters,
spatial CV reduces to leave-one-cluster-out at n=2 folds
(`spatial_summary_training_eligible`: 2 clusters, 974 km support gap). The
Strategy seam is what lets a fold structure be swapped when more sources land —
but no pattern fixes n=2. That's BACKLOG §4.

### 4.3 Economic scenarios — Strategy, probably thin

**Variation point:** market versus strategic cutoffs from `scenarios.yaml`.
`EconomicModel` exists and `scenario_configs` is already a list passed to
`apply()`. **Candid assessment: this may be over-engineering.** The two
"scenarios" differ by a cutoff *number* read from a contract file, not by
algorithm. Unless Phase 4 reveals genuinely different economic *math*, one
`EconomicModel` parameterized by the scenario dict is the right size, and a
class per scenario would be ceremony of exactly the §3.1 kind. Recommend
deciding at Phase 4 against the real `scenarios.yaml`, not now.

### 4.4 Suggested by the code, not on the original list

- **`CorpusCsvSampleSource`** (§3.2) — the missing production `SampleSource`.
  Phase 2's training matrix needs it; it closes a real gap rather than adding a
  pattern.
- **Training-matrix assembly** needs the DEM-resolution guard from BACKLOG §3
  (features from different DEM resolutions must never mix). That's a validation
  function, **not** a pattern — flagging it here so it isn't mistaken for one.
