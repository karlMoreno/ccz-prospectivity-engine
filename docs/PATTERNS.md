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
| Strategy | [`terrain/source.py:26`](../engine/prospectivity/terrain/source.py#L26) | synthetic DEM vs real GEBCO / recipes unchanged | **Yes, as of 2026-07-29** — now bridged (§3.2) |
| Strategy | [`normalizer.py:29`](../engine/prospectivity/ingestion/normalizer.py#L29) + 5 concrete | per-evidence-class kg/m² policy varies / call site fixed | **Yes** — 5 impls |
| Strategy | [`recipe.py:69`](../engine/prospectivity/features/recipe.py#L69) + 8 concrete | terrain math varies / build sequence fixed | **Yes** — 8 impls |
| Strategy | [`samples/source.py:33`](../engine/prospectivity/samples/source.py#L33) + [`corpus_csv.py`](../engine/prospectivity/samples/corpus_csv.py) | corpus location varies (CSV now, DB Phase 5) / MASS-only gate frozen on the ABC | **Yes, as of 2026-08-13** — implemented (§3.2) |
| Registry | [`normalizer_registry.py:74`](../engine/prospectivity/ingestion/normalizer_registry.py#L74) | which normalizer for a tag / no branching | **Yes** — 5 entries + completeness |
| Registry | [`registry.py:61`](../engine/prospectivity/features/registry.py#L61) | which recipe for a covariate name | **Yes** — 8 entries + completeness |
| Registry | [`estimators/registry.py`](../engine/prospectivity/estimators/registry.py) | which estimator for a name / the CLAUDE.md baseline mandate | **Yes, as of 2026-08-14 (E2.1)** — completeness IS the baseline guarantee (§4.1's prediction, realized) |
| ~~Specification~~ → **policy object** | [`dedup_rules.py`](../engine/prospectivity/ingestion/dedup_rules.py) + [`resolution.py`](../engine/prospectivity/ingestion/resolution.py) | dedup decision varies / pipeline applies it | **Retired 2026-07-30** — pattern didn't fit; shipped an honest policy (§3.0) |
| Template Method | [`pipeline.py:69`](../engine/prospectivity/ingestion/pipeline.py#L69) | steps vary / order fixed | **Yes** |
| Template Method | [`recipe.py:84`](../engine/prospectivity/features/recipe.py#L84) | compute varies / resolve→compute→provenance fixed | **Yes** |
| Template Method | [`engine.py:94`](../engine/prospectivity/engine.py#L94) | strategies vary / run order fixed | **Not yet** (§3.2) |
| Template Method | [`estimators/base.py`](../engine/prospectivity/estimators/base.py) `predict` | estimator math varies / pairing validation fixed, final via `__init_subclass__` | **Yes, as of 2026-08-14 (E2.1)** |
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

**Added at E2.4 §2 (2026-08-19) —
[`CrossValidationRunner.run()`](../engine/prospectivity/validation/runner.py):**

```
  for each FoldSplitter (design):
    split ──► assert_spatially_separated(required_separation_km) ──► claim gate
      ──► for each fold: for EVERY (name, estimator) in registry.items():
            route by estimator.input_kind ──► fit (refusal RECORDED; predict
            structurally unreachable after it) ──► predict ──► score ──► provenance()
      ──► join every row to the baseline's row for the same fold ──► pool
  ──► emit_run_manifest (the chain re-derived, never copied)
```

The eight BACKLOG §3 runner obligations are properties of this one object:
iterating `items()` makes "the baseline RAN" follow from "the baseline is
REGISTERED" (the structural half E2.1 could not supply), and the try/else
shape makes a stale-state predict after a refused refit impossible rather
than forbidden. `engine.py`'s old `cross_validator` callable seam (one
estimator, no coordinates) is RETIRED for this — §4.2 below, realized.

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

### 3.0 Specification: retired — **neither half of the justification held** ✅

The Phase-1 cheat sheet justified this pattern as *"composable, named
predicates."* Both halves have now failed, and it is worth stating together
because the pair is the finding — a pattern adopted for two reasons, neither of
which survived contact with the real dedup rules.

| Claimed | Actual |
|---|---|
| **Composable** (`&`/`|`/`~`) | Zero production composition sites. Combinators deleted, §3.1. |
| **Predicate** — pure, side-effect free, safe to evaluate any number of times | **A mutating admission policy.** `is_satisfied_by()` reads the corpus and, on a match, replaces a row in place, merges fields into the survivor, appends a provenance note, escalates `qa_status` — then returns `False` to *commit* that, meaning "don't also append", not "no". |

**This is not academic — it produced a bug directly.** Two calls to something
named `is_satisfied_by` were assumed to be free, because that is what the name
and the pattern both promise. E1.5 found the consequence: the provenance note
was re-appended on the second call, and on a `build_corpus()` re-run a row
recorded itself as *its own duplicate*. Row counts stayed correct the whole
time, so the length-only idempotency test never saw it. The advertised contract
and the actual contract diverged, and the gap was where the defect lived.

**The guards made it safe; they did not make it legible.** Two idempotency
guards were added (the merge wouldn't re-append a known link; the resolver
short-circuited a same-record re-offer), both mutation-verified, so repeated
evaluation became harmless. But a reader still met a method named
`is_satisfied_by` returning a `bool`, with no signal at the call site that
calling it *rewrote the corpus* — the safety lived in two guards and three
docstrings rather than in the shape of the code. Documentation recorded the
divergence; it did not remove the trap. **That is what the C2 refactor below
fixed.**

Where this is written down, so it survives without this file:
[`specification.py`](../engine/prospectivity/ingestion/specification.py)'s ABC
docstring (no future implementer may assume purity; a mutating implementation
needs a paired idempotency test) and
[`dedup_rules.py`](../engine/prospectivity/ingestion/dedup_rules.py)'s class
docstring (what it may remove, merge, append, and escalate — stated first).

**RESOLVED 2026-07-30 (Option C2).** The pattern is retired here and the ABC is
deleted. `DuplicateStationSpecification` became
**`DuplicateResolutionPolicy`**, exposing a **pure** `resolve(candidate) ->
Resolution`; `IngestionPipeline._dedup` applies the decision. `Resolution` is a
closed set of value objects — `Admit`, `AlreadyPresent`, `AbsorbInto`,
`Replace` — each naming what should happen, with the five previously-hidden
effects now explicit fields: which row is affected (`existing`), what the slot
must hold (`merged`), what was gap-filled (`donated_fields`), the provenance
link (`note`), and the sticky QA verdict (`escalated_status`).

What that bought, beyond honesty:

- **Idempotency became structural.** The same-record re-offer is the
  `AlreadyPresent` variant, and the guard is that `_dedup` has no branch
  writing anything for it — where it used to be an early `return False` that
  read like "not a duplicate". The note guard is now a property of a pure
  computation, so `merged` is already correct before any write.
- **The recorder stopped inferring.** ~20 lines in `corpus_manifest.py`
  recomputed `admitted`/`absorbed` by counting the finished corpus and
  subtracting, because the event stream couldn't be trusted — that inference
  is where the attribution bug lived. `Replace` now books both sides as it is
  decided, so the tallies match the corpus with no subtraction anywhere.
- **The policy is testable without a mutable corpus.** Its tests assert on
  decisions; only the few that care about corpus *effect* apply one.

The `Specification` ABC is **deleted**: zero implementations after this, and it
had already lost its combinators (§3.1). A genuinely pure future rule
(AOI/exclusion-zone against `exclusions.geojson`, or an `is_open` publication
gate) should get a fresh base class whose docstring can promise purity without
caveats — not inherit one whose documentation had become a warning about the
class that left.

> **Assessment for a reviewer:** adopting Specification in Phase 0 was a
> reasonable bet on rules that turned out to be neither composable nor pure.
> Recognising that from the shipped code and replacing it with a policy object
> that says what it does is the outcome that demonstrates pattern *judgment*
> rather than pattern *application*.

**A note on the dated walkthroughs.** `docs/walkthroughs/E1.2.md`, `E1.3.md`,
`E1.5.md`, `phase-0-and-E1.1.md` and `provenance.md` describe the
**pre-refactor** state — `Specification`, `is_satisfied_by`,
`DuplicateStationSpecification`. They are deliberately left as historical
records of what was true when each task shipped; this file and the code are
authoritative for what is true now.

### 3.1 Specification combinators — DELETED 2026-07-29 ✅

`_AndSpecification`, `_OrSpecification`, `_NotSpecification` and the `&`/`|`/`~`
operators are gone, along with `test_specification_combinators.py`. The
`Specification` ABC stays: the pipeline depends on that interface,
`dedup_specification` is optional and swappable, and tests inject alternatives.
Rationale, now recorded in
[`specification.py`](../engine/prospectivity/ingestion/specification.py)'s own
docstring so it survives without this file:

1. **Nothing composed them.** Phase 0 froze the operators assuming the dedup
   rules would compose. They didn't: Contract 7's rules 4 and 5 collapsed into a
   single guard (`_comparable_evidence`), rule 3 moved into an adapter because a
   many-to-one aggregation isn't a boolean predicate at all, and rules 1–2
   turned out to be the same mechanical key-match. **Zero production composition
   sites**; three tests that tested only themselves.
2. **The shipped Specification is stateful, so composition is unsafe.**
   `DuplicateStationSpecification.is_satisfied_by()` merges the candidate into
   the corpus row and returns False (D1/D4). Under `a & b`, short-circuiting
   would silently decide whether `b`'s merge ran; under `~a`, a False meaning
   "already merged, don't append" would invert into "append this". Evaluation
   order would be load-bearing and invisible at the call site — a corpus
   corruption bug with no symptom.

**This was not theoretical.** Writing the idempotency test that §3.1 motivated
(item 2 of the same follow-up) found the stateful merge was **not** idempotent:
a second `is_satisfied_by()` on the same pair re-appended the provenance link,
and on a `build_corpus()` re-run a row recorded itself as "duplicate of \<its own
source_record_id\>". Row counts stayed correct throughout, so the length-only
idempotency test never saw it. Both causes are fixed and guarded
([`test_dedup_rules.py`](../tests/test_dedup_rules.py) idempotency test,
[`test_corpus_builder.py:189`](../tests/test_corpus_builder.py#L189) strengthened
to compare every field). The fragility the combinators would have amplified was
real and present.

### 3.2 Five ABCs have zero production implementations

| ABC | Production impls | Status |
|---|---|---|
| [`TerrainSource:26`](../engine/prospectivity/terrain/source.py#L26) | 0 | **WIRED 2026-07-29** — no longer bypassed; see below |
| [`SampleSource:33`](../engine/prospectivity/samples/source.py#L33) | 1 | **IMPLEMENTED 2026-08-13** (E2.0-1) — `CorpusCsvSampleSource`; see below |
| [`Estimator`](../engine/prospectivity/estimators/base.py) | 1 | **FILLED 2026-08-14** (E2.1) — `MeanBaselineEstimator`; `predict` became the ABC's Template Method enforcing the (mean, std) pairing, final via `__init_subclass__`; kriging/RF arrive E2.2/E2.3 |
| [`EconomicModel:30`](../engine/prospectivity/economics/model.py#L30) | 0 | Phase 4 |
| [`TS6Reference:29`](../engine/prospectivity/ts6/reference.py#L29) | 0 | Phase 3 |

All five are Phase-0 pre-declared seams with test-only subclasses. Pre-declaring
an interface for work that lands in two phases' time is a bet, and it should be
called what it is. Two need naming individually:

**`TerrainSource` — WIRED, not deleted (resolved 2026-07-29).** The finding was
that E1.4's `DemGrid.load(path)` read the DEM directly, leaving an interface for
"where does bathymetry come from" whose only real consumer ignored it.

The precise diagnosis matters: **the seam was never absent.**
`ProspectivityEngine._ingest` already called `terrain_source.load(study_area)`
and handed the resulting `TerrainLayer` to `feature_builder`. What was missing
was any way for `features/` to *consume* a layer — so E1.4 went around it. Fixed
by adding the bridge:

```
   TerrainSource (STRATEGY)          ┌─ FixtureTerrainSource   (synthetic, today)
     .load(study_area)  ◄────────────┤
        │                            └─ GEBCOTerrainSource     (Checkpoint 1)
        ▼
   TerrainLayer  ──► DemGrid.from_terrain_layer(layer)  ──► recipes (unchanged)
                       │  verifies layer.content_hash against the bytes read
                       └─ from_terrain_source(source, area) = load + bridge
```

`from_terrain_layer` is the primary form because it matches what the engine
already produces; `from_terrain_source` is the convenience. Swapping synthetic →
real GEBCO is now a substitution **at the seam**: change the injected
`TerrainSource`, change nothing in `DemGrid` and nothing in any recipe.

Two things the bridge also fixed:

- **It verifies the reported hash** against the SHA-256 of the bytes it actually
  read, so a source that reports a hash it didn't compute fails loudly instead
  of seeding provenance with a fiction (mutation-verified).
- **`FixtureTerrainSource`'s `content_hash="sha256:synthetic-fixture"` placeholder
  is gone**, replaced by a real computed hash — as is the identical placeholder
  in `FixtureTS6Reference`, fixed in the same pass since leaving one of two
  identical fakes would just reintroduce the problem at Checkpoint 3. Being
  synthetic is recorded in the layer's name, never by faking a hash.

`DemGrid.load(path)` remains for direct use (the plot CLI, tests) — it is the
low-level reader the bridge delegates to, not a competing way in.

**`SampleSource` is a near-miss, not ceremony.** Its concrete
`get_training_samples()` carries the MASS-only rule, and the rule itself *is*
in production (`Observation.is_training_eligible()`, called by the corpus
manifest). What's missing is the `CorpusCsvSampleSource` the Phase-0 walkthrough
promised; production currently reads the corpus directly. Phase 2's training
matrix is its natural consumer. **Recommendation:** implement it in Phase 2, or
fold the ABC away — but the variation point (CSV now, database later) is real
and near, so implementing is the better call.

**RESOLVED 2026-08-13 (E2.0-1).** `CorpusCsvSampleSource`
([`samples/corpus_csv.py`](../engine/prospectivity/samples/corpus_csv.py))
implements the hook: CSV → NaN-to-None → `Observation(**row)`, so the
production read path validates every row against Contract 1 at load. The
gate stays on the ABC, un-reimplemented. The mutation pass surfaced the fact
that justifies the constructed-row tests: with every real corpus row
`is_open=True`, dropping the `is_open` condition left **271 of 272 tests
green** — the one failure was the new constructed closed-row test, the sole
observer of that gate in the whole suite
([`test_corpus_csv_sample_source.py`](../tests/test_corpus_csv_sample_source.py)).

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

**None in Phase 1.** Every real variation point currently in the code has a seam,
and as of 2026-07-29 the one that had a seam it wasn't using (`TerrainSource`,
§3.2) is wired. The genuine gaps are all Phase 2, listed in §4.

---

## 4. Where the next patterns belong (written pre-Phase-2 as report-only;
##    §4.1's estimator half SHIPPED in E2.1 — see its "Realized" note)

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

**Realized in E2.1 (2026-08-14), with one correction to the paragraph
above:** the tuple signature EXPRESSED pairing but did not make an unpaired
prediction unrepresentable — `(mean, None)` and a bare `(2, n)` array (which
unpacks positionally) both sailed through. `predict()` is now the ABC's
TEMPLATE METHOD validating the pair from a `_predict` hook (the
`build()/_compute()` split), and the registry + `assert_complete()` landed
exactly as this section argued, with the baseline as the one REQUIRED entry.

### 4.2 Cross-validation splitters — Strategy

**Variation point:** spatial CV (mandatory) versus random k-fold, the latter kept
*only* as the demonstrably-wrong comparison. Two implementations, both real, both
needed simultaneously — a textbook Strategy. (Written pre-E2.4: "`engine.py`
already takes `cross_validator` as an injected callable, so this may not even
need an ABC" — it did need one, see the Realized note below; the callable seam
was retired at E2.4 §2.)

**Note the honest constraint from the corpus manifest:** with two clusters,
spatial CV reduces to leave-one-cluster-out at n=2 folds
(`spatial_summary_training_eligible`: 2 clusters, 974 km support gap). The
Strategy seam is what lets a fold structure be swapped when more sources land —
but no pattern fixes n=2. WHY n=2 cannot rank the estimators (not only that it
is small) is the two-fold geometry theorem — BACKLOG §3 "E2.4 runner
obligations" (8): with the fitted range ≤ 13 km of support, kriging across the
~991 km gap reverts to the training cluster's mean, so across clusters kriging ≈
baseline BY CONSTRUCTION and the fold is a measurement of how much the clusters
differ, not a model comparison. (The former "That's BACKLOG §4" pointer went to
an item that is now closed by that theorem.)

**Realized in E2.4 §1 (2026-08-18):** `FoldSplitter` ABC in
`engine/prospectivity/validation/splitter.py` — Strategy, with a
`spatially_blocked: ClassVar[bool]` DECLARATION enforced by `__init_subclass__`
(the E2.1 predict-is-final precedent): a splitter that does not say whether its
folds may back a claim cannot be declared, so E2.5's guard reads a declaration
and never infers from a name. `split()` returns a `FoldAssignment` (labels,
folds, rule, parameters, and the tie-break STABILITY INTERVAL of thresholds that
reproduce the partition) — the assignment as data for the run manifest. First
implementation: `SingleLinkageBlockSplitter` (connected components of the
within-`linkage_km` graph — the corpus manifest's own clustering, ONE
implementation shared via `geometry.single_linkage_labels`), which at 100 km IS
leave-one-cluster-out. It did need an ABC after all: the declaration is
class-level state a bare callable cannot carry. **§2 (2026-08-19, Karl's §1B
pick):** the same class at 2 km is `leave_one_site_out` (the headline
within-cluster gate), plus `LeaveOneStationOutSplitter` (declared
`spatially_blocked = False`: unbuffered, within-site, never a generalization
result) and `RandomKFoldSplitter` (declared `False`: the demonstrably-wrong
comparison) — four Strategies behind one runner, and `assert_claim_eligible`
reads the RECORDED declaration to decide which may back a claim.

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
  pattern. **Done, E2.0-1 (2026-08-13)** — see §3.2's resolution note.
- **Training-matrix assembly** needs the DEM-resolution guard from BACKLOG §3
  (features from different DEM resolutions must never mix). That's a validation
  function, **not** a pattern — flagging it here so it isn't mistaken for one.
