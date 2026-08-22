# Provenance architecture — four artifacts, chained

The alpha's stated deliverables are a CSV corpus, GeoTIFF rasters, and a JSON
provenance manifest. "The manifest" is in fact **four** artifacts, one per
pipeline stage. This file defines the boundary between them and the one rule
that connects them.

**Decision (2026-07-29; extended to four 2026-08-14, E2.0-3):** keep them
separate; do not merge. They have different lifetimes — a corpus outlives
many feature stacks, a feature stack outlives many training matrices, and a
matrix is 1:1 with a run only by convention (nothing enforces it; two runs
may share a matrix). One merged manifest would mean rebuilding everything to
record anything, and re-hashing a corpus every time a model run changed a
seed.

## The four artifacts

```
   ┌─────────────────────────┐
   │  raw downloads           │  data/sources/*.tab      (hashed per source)
   │  synthetic / real DEM    │  outputs/.../*.tif        (hashed as "dem")
   └───────────┬─────────────┘
               │
     ┌─────────▼──────────────┐         ┌──────────────────────────┐
     │  1. CorpusManifest       │         │  2. FeatureStackManifest   │
     │  data/corpus/            │         │  <stack dir>/              │
     │      manifest.json       │         │      provenance.json       │
     │  STAGE: ingestion        │         │  STAGE: features (E1.4)    │
     └───────────┬──────────────┘         └────────────┬──────────────┘
                 │  content_hash                        │  content_hash
                 │                                      │
                 └──────────────┬───────────────────────┘
                                │  both quoted in upstream_hashes
                     ┌──────────▼─────────────────┐
                     │  3. TrainingMatrixManifest   │
                     │  STAGE: matrix assembly      │
                     │  (E2.0-3; in-memory,         │
                     │   hash quoted downstream)    │
                     └──────────┬─────────────────┘
                                │  content_hash
                     ┌──────────▼───────────┐
                     │  4. RunManifest        │
                     │  STAGE: model run      │
                     │  (E2.4: CV run emitted;│
                     │   E3.4: EXTENDED with  │
                     │   surfaces · TS-6 map  │
                     │   · claim · chain;     │
                     │   Phase 4 adds econ)   │
                     └──────────────────────┘
```

| # | Artifact | Stage | Written to | Records |
|---|---|---|---|---|
| 1 | `CorpusManifest` | ingestion | `data/corpus/manifest.json` | per-source dispositions + real input SHA-256s + licenses; corpus totals by evidence class and `qa_status`; `training_eligible_count`; contributing sources **including fully-absorbed ones**; corpus geometry (bounding boxes, AOI containment, cluster + pairwise-distance structure) |
| 2 | `FeatureStackManifest` | features | `<stack dir>/provenance.json` | per-covariate recipe + `recipe_version`, requested metres **and** resolved cell window (with the clamp flag), border policy, CRS strategy, DEM identity |
| 3 | `TrainingMatrixManifest` | matrix assembly | in-memory (E2.1+ decides persistence; its hash is what downstream quotes) | Contract 8 target **value + declared origin** (the one decision upstream hashes are invariant to); `sampling_method`; `shared_cell_count` **and** `cell_groups` (the grouping is what makes the covariate-model R² ceiling recomputable next to any score); `matrix_sha256` over the matrix's canonical bytes; computed `data_origin` (combine over corpus + stack origins, never hand-declared); n/covariate names in column order |
| 4 | `RunManifest` | model run | emitted by `engine/prospectivity/validation/runner.py: emit_run_manifest` (E2.4 §2); the real-data CV run's manifest is committed at E2.4 §3 (location recorded there) | `run_id`, seed, the flat CV score table (`CVScore`: one row per design/fold/estimator/metric, the baseline's value beside every row, `uncertainty_method` per row, refusals named by status), `cross_validation` (every design's fold assignment with required + measured separations and its `purpose`; every (design, fold, estimator) result with status / refusal / metrics / uplift / the estimator's per-fold `provenance()`; pooled metrics on comparable folds), `estimator_declarations` (input_kind, uncertainty_method, uncertainty_semantics, class — read from the declarations), `claim_eligible_designs`, computed `data_origin` (the matrix's; watermark derives, default-on), `scores_first_visible` (OUTSIDE the content hash — the pre-registration clock; its description names the COMMIT as the authoritative witness); **E3.4 (`provenance/emitter.py: extend_run_manifest`):** `ts6_agreement` — a MAPPING, one self-identifying agreement per estimator (`None` = the comparison step did not run); `output_hashes` — `{basename: sha256}` of every written file, recomputed from the bytes; `prediction_grid` (the stack's grid identity); `surfaces` (per estimator: summary, computed origin, watermark, the two rasters' and the sidecar's hashes); `claim` (E2.5's verdict for EVERY design, each precondition pass/fail by name, plus the DECLARED claim design); `provenance_chain` (every link recomputed at emission, with its off-machine verifiability stated — see the chaining rule below); **E4.1 (schema_version 2):** `economic_results` — one `EconomicScenarioResult` per Contract 4 scenario: the cutoff WITH its origin, the confidence levels (z is a stated reading; each estimator's `uncertainty_semantics` travels), one footprint summary per estimator per level, the COMPUTED origin and the per-reason WATERMARK VERDICT (terrain ↔ Checkpoint 1; economic parameters ↔ Checkpoint 4 — derived from declared facts, never a copied flag); `economic_differences` — Contract 4's difference pairs, `None` when the economics step did not run; **E4.3 (schema_version 3):** `economics` — the block resolved from E4.2's association record and VERIFIED by recomputation (every raster's sha256 from its bytes, its tags against the record and the results, counts from the pixels, the origin by `combine_origins`, the terrain reason from the stack's declared DEM origin); the record itself hashed into `output_hashes` under `economics/…`; the scenarios with their cutoffs in the DeclaredField shape; the difference fractions; the two watermark reasons per artifact |

**Why the matrix gets its own artifact:** the corpus hash and the stack hash
are both INVARIANT to the target definition, so two matrices built on
different y would present identical `upstream_hashes` — without a
matrix-level record, the one decision that defines what the model predicts
has no identity in the provenance chain. Folding it into `RunManifest` was
considered and declined: matrix↔run is 1:1 only by convention, and artifacts
here are separated by LIFETIME.

## The chaining rule

> **Every downstream artifact records the `content_hash` of the upstream
> artifacts it consumed, in `upstream_hashes`.**

So a prediction traces to **exactly one** corpus and **exactly one** feature
stack, by mechanical lookup rather than by convention or filename.

- `CorpusManifest.upstream_hashes` is `{}` — ingestion is the first stage.
  Its raw inputs are not artifacts, so each source's file hash is recorded in
  that source's own entry instead.
- `FeatureStackManifest.upstream_hashes` carries `{"dem": "sha256:…"}`. The
  DEM is a raw input rather than an artifact; hashing it here is what lets a
  run prove which terrain its features came from. Option-A covariates come
  from the DEM alone, so the corpus is **not** upstream of the feature stack.
- `TrainingMatrixManifest.upstream_hashes` carries both `{"corpus": …,
  "feature_stack": …}` — the matrix is the first artifact where the two
  lineages meet, and its assembler verifies the stack manifest it is handed
  actually describes the DEM being sampled before quoting it.
- `RunManifest.upstream_hashes` = `{"training_matrix": <TrainingMatrixManifest
  content_hash>, "corpus": …, "feature_stack": …}` — the matrix artifact's
  identity PLUS the two it chains to, quoted from the matrix manifest's own
  upstream record so one lookup reaches all three (E2.5 condition 5). The
  emitter RE-DERIVES the matrix's `matrix_sha256` from the arrays it is
  handed and refuses a manifest that does not describe them (E2.4 §2D: the
  chain is asserted, never copied). Fixed at E2.4 §2 (2026-08-19).
- **E3.4 extends the rule to the run's OUTPUTS and states its limit in the
  artifact.** `extend_run_manifest` RECOMPUTES every link — the corpus
  manifest's substance, the stack manifest's substance, the matrix arrays,
  the benchmark raster's bytes, every written raster (values re-read and
  compared to the in-memory surface) and sidecar — and refuses by name when
  any two records of one fact disagree. `provenance_chain` then says, per
  link, what was recomputed and whether it is verifiable OFF the machine that
  wrote it: **only the corpus is** (the path-hash limit below), and at E3.4
  that limit measurably reaches every output file, because raster tags and
  sidecars quote the stack hash. A chain that claimed more than that would be
  the defect the BACKLOG entry exists to prevent.

## The shared base

All four extend `ProvenanceArtifact`
([`engine/prospectivity/provenance/artifact.py`](../../engine/prospectivity/provenance/artifact.py)) —
**Layer Supertype** (Fowler, PoEAA): one common superclass for every type in
the provenance layer, so the four chaining fields are declared once with
identical names:

| Field | Meaning |
|---|---|
| `generated_at` | when the artifact was produced |
| `content_hash` | the artifact's own identity hash |
| `contract_versions` | which frozen contracts were in effect |
| `upstream_hashes` | `content_hash` of each artifact consumed |

Identical *names* are the point — `tests/test_provenance_artifact.py` asserts
it over all four — because walking the chain must not require per-artifact
special cases.

### The content-hash scheme (HASH.1, 2026-08-22: shape-tolerant)

`content_hash` is computed over the artifact's canonical JSON with **two
fields excluded** — `content_hash` itself (self-reference is impossible) and
`generated_at` (a wall-clock timestamp would make two otherwise identical
builds hash differently) — and, since HASH.1, over **present fields only,
with the schema version inside the substance**:

| artifact | detected by | substance |
|---|---|---|
| **versioned** (every artifact emitted since HASH.1) | `schema_version` set at construction to the class's `SCHEMA_VERSION` | every field whose value is not `None`, `schema_version` among them |
| **legacy** (stamped before HASH.1) | arrives with a `content_hash` and **no** `schema_version` — only `finalize()` ever sets `content_hash`, so this separates reloaded history from a fresh build | the class's **frozen** `LEGACY_HASHED_FIELDS`, defaults included — byte-for-byte the pre-HASH.1 payload, so the hash never moves |

**Why** (Karl's decision, E3.4 approval): under the old rule `substance()`
dumped every field, defaults included, so adding ANY field re-hashed every
committed artifact of that type — E3.4 paid that once (six lines on
`data/runs/e2.4/run_manifest.json`), and every future field would have
charged it again. Re-stamping means committed provenance CHANGES AFTER THE
FACT, against what the chain exists to do. **The losing argument, because it
is real:** two manifests with different shapes can now hash identically when
their present fields agree, so the hash no longer identifies the schema. It
loses because the shape is recorded elsewhere in the artifact and the hash's
job is SUBSTANCE; `schema_version` inside the substance restores what is
given up explicitly (v1 and v2 with identical present fields hash apart —
tested), not as a side effect of dumping defaults.

**Why a legacy mode rather than a plain present-fields rule — measured
before building:** the E2.4 run manifest was re-stamped at E3.4 with five
`null` fields IN its substance, so `exclude_none` alone moves its hash
(`e3ac1561…` → `b649fd96…`), and `exclude_defaults` moves the corpus
manifest's too (`upstream_hashes: {}`). "Leave historical artifacts with
their original hashes" therefore requires the old rule for them, over a
field set frozen at HASH.1 per class.

**What the decision does NOT fix, bounded:** artifacts stamped before HASH.1
carry no schema version, so by hash alone they cannot be told from a
differently-shaped artifact. That set is **two committed files** —
`data/corpus/manifest.json` and `data/runs/e2.4/run_manifest.json`; stack
and matrix manifests are generated fresh per run and are unaffected. **The
E3.4 re-stamp stays as it is**: un-stamping it would be the after-the-fact
edit the decision exists to prevent. Both legacy hashes are pinned by
literal in `tests/test_provenance_artifact.py`.

**The rule for new fields, enforced at class definition:** a field a
subclass introduces outside its frozen legacy set must default to `None`
(`__pydantic_init_subclass__` refuses otherwise, by name) and
`SCHEMA_VERSION` is bumped — a non-None default would enter every
artifact's present-field substance and re-hash history by a side door.

So `content_hash` is a hash of **substance**: same inputs and same decisions
produce the same hash at any time. **"On any machine" — how much of it the
implementation delivers, measured (HASH.1 commit 2, 2026-08-22):** the
feature stack's substance embeds no path any more (`DemGrid.provenance()`
lost `path`; the location is recorded as `FeatureStackManifest.dem_path`,
OUTSIDE the hash — the `generated_at` precedent), so the same DEM bytes
built from any directory, by a relative or an absolute path, give the same
stack hash, the same matrix hash, the same surface bytes and the same run
`content_hash` — **0 directory-dependent hash values, down from the 11
E3.4 measured**. What "any machine" still does NOT cover, stated in every
run manifest's `provenance_chain.path_dependent_hashes.remaining_limits`:
`matrix_sha256` and the coordinate fingerprints hash native byte order
(same-endianness hosts); raster bytes across GDAL versions are not
measured; and the run manifest's `inputs.environment` is inside its hash
BY DESIGN, so two machines with different installed versions hash
differently — which is right. Manifests are byte-identical across builds
**apart from `generated_at`** (and, for the stack, `dem_path`), and their
`content_hash` matches outright — asserted in the tests, now with the DEM
PATH varied, which the pre-HASH.1 determinism test never did.

**Corollary — order invariance.** `CorpusManifest` sorts its source lists by
`source_id` rather than leaving them in adapter-run order, because the corpus
itself is order-independent (P2 proved the CSV is byte-identical with
`REAL_ADAPTER_BUILDERS` reversed). An identical corpus must produce an
identical manifest hash, or a downstream `upstream_hashes` reference could
flip because someone reordered a build list.

## How the corpus manifest is populated: OBSERVER

`IngestionPipeline` emits lifecycle events (`on_fetched`, `on_adapted`,
`on_normalized`, `on_absorbed`, `on_admitted`, `on_rejected`) to a
`PipelineObserver`; `ProvenanceRecorder` accumulates them. The pipeline stays
a Template Method with no reporting responsibility, and the **default
observer is `NullObserver`** (Null Object), so an un-observed pipeline behaves
exactly as it did before observers existed.

**The invariant:** recording never changes a pipeline decision. The pipeline
never reads observer state and never branches on it;
`test_corpus_manifest.py::test_recording_does_not_change_the_corpus` proves a
recorded and an unrecorded build produce a byte-identical corpus.

### Process counts vs. outcome counts

A distinction worth knowing, because getting it wrong produced a real defect
(found by the reversed-order test, 2026-07-29):

- **Process** counts come from observed events: `fetched_rows`,
  `adapted_records`, `normalized_records`, `rejected_rows`.
- **Outcome** counts are recomputed from the **finished corpus**:
  `admitted_rows`, `absorbed_rows`, `flagged_admitted_rows`.

They differ because the dedup merge overwrites a corpus slot **in place** with
a higher-quality row from a later source (D1/D4) rather than appending it. So
"rows this source's pipeline appended" flips with adapter order while the
finished corpus does not. Only the corpus-derived attribution is published.

### The reconciliation identity

```
adapted_records == admitted_rows + absorbed_rows + rejected_rows
```

Anchored on **adapted**, not fetched, because the row→record relationship is
not 1:1 in either direction: `[01]` fans one raw row out into one record per
evidence class (36 → 108), and `[05]` aggregates individual nodules up to
events (1,658 → 72). `fetched_rows` is recorded alongside so that expansion or
reduction is visible instead of looking like rows went missing.

`flagged_admitted_rows` is a **subset of admitted** — a quality mark on rows
that *are* in the corpus — not a fourth disposition. A flagged row is
recorded, kept, and excluded from training; it is never dropped
(`normalization.yaml`: flag, never drop).

## What each artifact deliberately does not record

- **CorpusManifest**: no dependency versions or `requirements.lock` hash —
  assigned to the Phase-3 manifest work in [`../BACKLOG.md`](../BACKLOG.md) §3,
  and they describe a *run environment* rather than a corpus.
- **FeatureStackManifest**: keeps `registry_version` at top level even though
  `contract_versions` now carries it too. Preserving exactly what the E1.4
  sidecar already recorded took precedence over de-duplicating the field.
- **TrainingMatrixManifest**: no watermark flag (the watermark DERIVES from
  the computed `data_origin` at render time — `training_matrix.py`'s
  `matrix_watermark`, default-ON per P2.0d-3) and no stored R² ceiling (it
  is recomputable from `cell_groups` + y, and a stored copy could go stale
  against them). No persisted file location yet — the matrix is rebuilt per
  run and its hash is what downstream quotes; E2.1+ decides persistence.
- **RunManifest**: emitted since E2.4 §2 (the CV run). The ONE deliberate
  exception to "no wall-clock in the substance": `scores_first_visible` is
  recorded IN the artifact and kept OUT of `content_hash` (per-class
  `HASH_EXCLUDED_FIELDS`, which a subclass can only extend), because the
  DATE is the fact being recorded — and being outside the hash it is
  mutable metadata whose authoritative witness is the commit that
  introduced the scores (BACKLOG §2, the pre-registration clock). No
  watermark flag here either: the watermark derives from the computed
  `data_origin` (`run_watermark`, the matrix's rule reused). Since E3.4 it
  records the surfaces, the TS-6 agreement mapping, the claim verdicts and
  the recomputed chain; what it still does NOT record: the run ENVIRONMENT
  (dependency versions, the `requirements.lock` hash — BACKLOG §3
  "Dependency versions into the provenance manifest", which E3.4 did not
  reach), a persisted training-matrix file (the matrix's hash is what is
  quoted), and any raster PATH (basenames only — a path in the substance is
  the stack's defect one artifact over). Economics arrives in Phase 4.
