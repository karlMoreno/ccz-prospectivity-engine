# HANDOFF — Claude Code session, start of Phase 2

Paste at the start of a fresh Claude Code session. **This is a summary, not a source of
truth.** `CLAUDE.md`, `docs/BACKLOG.md`, `docs/PATTERNS.md`, `docs/walkthroughs/`, and the
contract files win over anything here. Read them before acting on this.

---

## First actions in a new session

Do these before writing any code:

```
1. Read CLAUDE.md, docs/BACKLOG.md, docs/PATTERNS.md
2. Read docs/walkthroughs/E1.5.md and E1.4.md (most recent state)
3. Read data/corpus/manifest.json (authoritative corpus numbers)
4. Run the suite; report the count and confirm it matches CLAUDE.md
5. Report anything in this handoff that the repo contradicts
```

That last step matters — this document was written from review notes, and the repo has
moved since.

---

## State as of last confirmed report

Phase 1 Track E complete. **202 tests (200 pass, 2 deliberate skips.)** The two skips are
expected: the corpus-level GRID assertion self-deactivates while `[18]` is unwired, and
re-activates when it's wired back.

```
Corpus     data/corpus/master_observations.csv — 108 rows
           36 events × {MASS, COUNT, COVER}; 35 training-eligible
           1 excluded: SO268/1_12-2 (failed box core, qa_status=flagged)
Manifest   data/corpus/manifest.json — content_hash sha256:372be3bb…
Sources    src_so268_boxcore  [01] PANGAEA.904967  (real, CC BY-NC 4.0)
           src_so268_nodules  [05] PANGAEA.904962  (real, fully absorbed by dedup)
Unwired    [06] Dryad, [18] TS-6 — fabricated fixtures removed in P1/P1b;
           _require_production_path() blocks re-wiring until real files exist
           [19] Washburn — never wired
Contracts  schema v4 · covariates registry v3 · normalization policy v1
Env        Python 3.11 pinned · requirements.lock · pangaeapy in the [fetch] extra
           always `python -m pip`, never bare `pip`
```

---

## Architecture in place

```
  SourceAdapter (ADAPTER)                          4 implementations
      │                                            Pangaea / Tabular / RegionalGrid /
      ▼                                            NoduleAggregate + BoxcoreSummary
  IngestionPipeline.run()  (TEMPLATE METHOD)
      fetch → adapt → normalize → validate → dedup → append
                          │           │        │
                          │           │        └─ DuplicateResolutionPolicy.resolve()
                          │           │           → Resolution (pure); pipeline applies
                          │           │             via an EXHAUSTIVE match
                          │           └─ Observation (Pydantic, schema v4)
                          └─ NormalizerRegistry (STRATEGY + REGISTRY)
                             5 normalizers, completeness-tested
      │
      ▼  ProvenanceRecorder (OBSERVER) books dispositions as decided
  CorpusManifest ─┐
  FeatureStackManifest ─┤ all extend ProvenanceArtifact (LAYER SUPERTYPE)
  RunManifest ─┘        chained by content_hash; hash excludes itself + generated_at

  DemGrid ← TerrainSource (seam wired; CRS strategy A = per-row longitude scaling)
      ▼
  CovariateRegistry (STRATEGY + REGISTRY) — 8 Option-A recipes, metre-based windows
```

**Retired patterns, deliberately:** `Specification` and its combinators were deleted —
the real dedup rules turned out neither composable nor pure. `PATTERNS.md` records the
reverse audit; don't reintroduce them.

---

## Invariants Phase 2 must not break

- **MASS is the only training class.** COVER never yields `abundance_kg_m2`. GRID is never
  a training station. GRADE never becomes abundance.
- **`qa_status` gates `is_training_eligible()`** — flagged and failed rows never train.
  `fail` is terminal; on a merge, the **most severe** status wins.
- **Every prediction pairs with an uncertainty.** A bare point estimate is not a
  deliverable.
- **A mean baseline runs alongside every model claim** (`CLAUDE.md` requirement).
- **Random k-fold is disqualified** for validation — spatial leakage on autocorrelated
  data. It may exist only as the labelled wrong-comparison.
- **Features from different DEM resolutions must never mix** in one training matrix
  (Contract 3 v3). Not yet enforced in code — that's an E2.0 task.
- **No fabricated values** anywhere in the production corpus or its derivatives.

---

## Conventions to follow (all established, all in CLAUDE.md)

- **Name the design pattern in comments, with the variation point it exists for** — not
  just the pattern name.
- **Restate the relevant contract before writing code.** If a needed parameter is missing
  or ambiguous, **STOP and ask** — do not improvise a scientific rule. This has caught
  several real contract defects.
- **Mutation-verify every new guard.** Break it, confirm the test fails, revert, confirm
  green, and report which mutations you ran.
- **Testing conventions** (in `CLAUDE.md`, added after three audits found the same defect
  class):
  - A test's name must describe what its **assertions** verify, not the author's intent.
  - A test asserting a rule must **not** load its data through the class that enforces
    that rule — it can never observe a violation.
  - An "unchanged" assertion must compare **full state**, not selected fields.
  - A fixture must be able to distinguish the claim from its negation.
  - Aggregate assertions don't prove per-item claims.
- **Registry completeness tests** and **exhaustive dispatch with an explicit raise** —
  prefer a loud failure over a silent no-op.
- **Per task:** a walkthrough in `docs/walkthroughs/`, updates to `PATTERNS.md` and
  `docs/BACKLOG.md` in the same commit, and a commit at the end. Don't leave reviewed work
  uncommitted.
- **Provenance:** extend `ProvenanceArtifact`; chain upstream `content_hash` values. Don't
  create a fourth provenance format.

---

## Phase 2 plan

Full prompts live in `phase2_prompts.md` (run them one at a time, in order).

```
E2.0  Training matrix           ← NOT in the original lane list; must come first
E2.1  Estimator interface + mean baseline
E2.2  Ordinary kriging (variogram + kriging variance)
E2.3  Random forest + uncertainty
E2.4  Spatially-blocked CV vs baseline
E2.5  Refuse-to-validate guard
```

**E2.0 exists because** covariate extraction at station locations was explicitly deferred
out of E1.4. It also closes two BACKLOG items: the missing `CorpusCsvSampleSource`
(`SampleSource` has no production implementation) and enforcing the DEM-resolution rule.

**The `Estimator` ABC already exists from Phase 0 with zero implementations.** Implement
it; don't define a parallel interface. Same for `EconomicModel` and `TS6Reference` later.

---

## The data constraint that shapes Phase 2

**35 training stations in two clusters ~12 km across, ~991 km apart.** Of 595 pairs: 301
under 13 km, 294 near 991 km, **zero between ~13 and ~986 km**.

Consequences you must design around rather than around-the-houses:

- The **empirical variogram has no support** across the range we'd predict over. E2.2 must
  report lag bins **with pair counts**, refuse to fit unsupported bins, and record the
  unsupported range in provenance. Do **not** force a long range to make a prediction map
  look smooth — a short range correctly reverts toward the mean far from data with
  variance approaching the sill, and that is the honest output.
- **Directional/anisotropic variograms are declined** — 35 points in two clusters would
  give directional bins of 2–3 pairs. Document the refusal.
- **Spatial CV needs two designs:** leave-one-cluster-out (2 folds, measures
  extrapolation at ~991 km) *and* within-cluster blocking (measures interpolation at
  1–13 km). They answer different questions; reporting one number hides that.
- **n=35 with 8 covariates, all derived from one DEM** → collinear and overfit-prone.
  Report the correlation matrix. RF **OOB score must not be reported as validation** —
  it's random resampling, i.e. spatial leakage.
- **If the models don't beat the baseline, report that.** Do not tune toward beating it.
  "The ceiling is the data, not the model" is the project's own position.

---

## Also true, and easy to forget

**The covariates are synthetic.** Every terrain feature is computed on a synthetic DEM
until real GEBCO arrives at Checkpoint 1. So Phase 2 builds and tests correctly, but
learns real abundance against noise. Every Phase-2 output must be **watermarked
non-scientific** while that's true — mirror `scenarios.yaml`'s `illustrative_only`
treatment, and verify the watermark actually fires end-to-end rather than merely existing
in code.

**The AOI placeholder excludes 100% of the corpus.** All 108 rows fall outside
`study_area.geojson`. Nothing filters on it today; it's recorded descriptively in the
manifest. Don't "fix" it — defining the real AOI is an open decision for the engineer of
record and Track G.

---

## Ready-now BACKLOG items, if you have spare capacity

Check `docs/BACKLOG.md` for the current list and exact citations. Ready without any Track G
input:

- **Pipeline-level row quarantine** — one malformed row currently aborts the whole batch,
  which contradicts flag-never-drop. Needed before `[02][03][04]` are wired.
- **Deterministic tie-break** replacing first-encountered — the DOMES families and
  NOAA/PANGAEA mirrors collide by design with no quality-grade asymmetry. Proposal is
  written up in E1.3.md §14.
- **Naive vs timezone-aware datetime comparison** in the dedup key — same instant compares
  unequal, so dedup silently misses. Failure mode is silent: no exception, just duplicate
  stations that look like independent samples and inflate the apparent sample count.
- **Smoothed synthetic DEM** — the current fixture is uncorrelated noise, so derivative
  covariates are noise-of-noise and a stencil-axis bug has places to hide. Cheap;
  diagnostic value only.

---

*Read the repo before trusting this file. If it contradicts `CLAUDE.md`, the walkthroughs,
or the manifest, say so — and the repo wins.*
