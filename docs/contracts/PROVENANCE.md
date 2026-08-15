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
                     │  (Phase 2-4)           │
                     └──────────────────────┘
```

| # | Artifact | Stage | Written to | Records |
|---|---|---|---|---|
| 1 | `CorpusManifest` | ingestion | `data/corpus/manifest.json` | per-source dispositions + real input SHA-256s + licenses; corpus totals by evidence class and `qa_status`; `training_eligible_count`; contributing sources **including fully-absorbed ones**; corpus geometry (bounding boxes, AOI containment, cluster + pairwise-distance structure) |
| 2 | `FeatureStackManifest` | features | `<stack dir>/provenance.json` | per-covariate recipe + `recipe_version`, requested metres **and** resolved cell window (with the clamp flag), border policy, CRS strategy, DEM identity |
| 3 | `TrainingMatrixManifest` | matrix assembly | in-memory (E2.1+ decides persistence; its hash is what downstream quotes) | Contract 8 target **value + declared origin** (the one decision upstream hashes are invariant to); `sampling_method`; `shared_cell_count` **and** `cell_groups` (the grouping is what makes the covariate-model R² ceiling recomputable next to any score); `matrix_sha256` over the matrix's canonical bytes; computed `data_origin` (combine over corpus + stack origins, never hand-declared); n/covariate names in column order |
| 4 | `RunManifest` | model run | (emitter is Phase 2–4) | `run_id`, seed, CV scores, TS-6 agreement, economic results, output hashes |

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
- `RunManifest.upstream_hashes` will quote the training-matrix hash (which
  itself chains to corpus + stack); the exact set is fixed when the emitter
  is built (Phase 2).

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

### The content-hash scheme

`content_hash` is computed over the artifact's canonical JSON with **two
fields excluded**:

- `content_hash` itself — self-reference is impossible.
- `generated_at` — a wall-clock timestamp would make two otherwise identical
  builds hash differently, destroying the one property the hash exists to
  provide.

So `content_hash` is a hash of **substance**: same inputs and same decisions
produce the same hash on any machine at any time (CLAUDE.md: "same inputs +
seed → same outputs"). This is what makes it usable both as an upstream
reference and as a reproducibility check. Manifests are therefore
byte-identical across builds **apart from `generated_at`**, and their
`content_hash` matches outright — both asserted in the tests.

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
- **RunManifest**: still a shape, not yet an emitter. Phase 2–4 fills it.
