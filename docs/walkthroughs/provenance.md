# Provenance artifacts — shared base + corpus manifest (2026-07-29)

**Audience:** you, the engineer of record. Architecture and the chaining rule
live in [`../contracts/PROVENANCE.md`](../contracts/PROVENANCE.md) — read that
first; this covers reading order, per-file detail, and the test inventory.

**Test count: 179** (157 before + 22 new; 178 pass, 1 is E1.3-P1b's known GRID
skip).

## Reading order

```
1. docs/contracts/PROVENANCE.md          the boundary + chaining rule (start here)
2. provenance/artifact.py                the shared base (Layer Supertype)
3. provenance/recorder.py                the Observer + why NullObserver is default
4. ingestion/pipeline.py                 the 4 emit points (diff is small)
5. provenance/corpus_manifest.py         what the corpus manifest records
6. provenance/geometry.py                cluster + pairwise-distance summary
7. data/corpus/manifest.json             the actual output
```

## Structure

```
   IngestionPipeline (TEMPLATE METHOD, unchanged sequence)
     fetch ──► adapt ──► normalize ──► validate ──► dedup ──► append
       │         │           │                        │         │
       └─────────┴───────────┴────────────────────────┴─────────┘
                              │ emits (OBSERVER)
                              ▼
              PipelineObserver ◄── NullObserver (DEFAULT, no-op)
                              ◄── ProvenanceRecorder (accumulates)
                                       │
              corpus (finished) ───────┤ outcome counts read from HERE,
                                       │ not from append order
                                       ▼
                            build_corpus_manifest()
                                       │
                     CorpusManifest ───┴──► data/corpus/manifest.json
                            │
                            └─ extends ProvenanceArtifact (LAYER SUPERTYPE)
                                          ▲            ▲
                          FeatureStackManifest      RunManifest
```

## Per-file

| File | What it is |
|---|---|
| `provenance/artifact.py` | New. `ProvenanceArtifact` — Layer Supertype declaring `generated_at`, `content_hash`, `contract_versions`, `upstream_hashes` once. `finalize()` stamps the hash; the hash excludes itself **and** `generated_at` (substance, not moment). |
| `provenance/recorder.py` | New. `PipelineObserver` (concrete no-op methods, so a new event never breaks an existing observer), `NullObserver` (Null Object — keeps `if observer is not None` out of the Template Method), `ProvenanceRecorder`, `SourceRecord`. |
| `provenance/corpus_manifest.py` | New. `CorpusManifest` + `SourceProvenance` + `build_corpus_manifest()`. Outcome counts (`admitted`/`absorbed`/`flagged`) recomputed from the finished corpus; process counts from events. |
| `provenance/geometry.py` | New. Haversine, single-linkage clustering, pairwise-distance distribution, AOI containment. Descriptive only — nothing here judges or filters. scipy not required. |
| `provenance/contract_versions.py` | New. Contract versions read from the contracts themselves; `file_sha256()` — the one real hash function, no placeholders. |
| `ingestion/pipeline.py` | 4 emit points + an `observer` parameter defaulting to `NullObserver`. `_dedup` became a loop to emit per absorbed row — **same number of `is_satisfied_by` calls in the same order**, which matters because the Specification mutates the corpus as it goes. |
| `ingestion/corpus_builder.py` | New `build_corpus_with_manifest()` (constructs adapters once, so the manifest hashes the files the build actually read); `build_corpus(observer=...)`; `main()` writes both artifacts. |
| `features/stack.py` | `FeatureStackManifest` replaces the hand-built dict. Same four keys, plus the shared fields; `registry_version` kept top-level deliberately. |
| `domain/results.py` | `RunManifest` extends the base. Only change to what it records: `created_at` → `generated_at`. |
| adapters (`boxcore_summary`, `nodule_aggregate`, `tabular_file`) | One line each: public `input_path` so the manifest can hash the real input without adapters growing a reporting method. |

## Test inventory (22 new)

| File | Tests | Enforces |
|---|---|---|
| `test_provenance_artifact.py` | 7 | All three artifacts subclass the base and expose the 4 shared fields with identical **names and types**; hash excludes `generated_at` (same substance → same hash) and is not self-referential; hash changes when substance changes; `RunManifest` kept every pre-refactor field. |
| `test_corpus_manifest.py` | 15 | **(1)** `[05]` in `contributing_sources` though absent from every corpus row, and its `mean_nodule_mass_g` really is present. **(2)** `adapted == admitted + absorbed + rejected` for every source; flagged ⊆ admitted. **(3)** `training_eligible_count` (35) ≠ admitted (108), excludes flagged/failed and specifically `SO268/1_12-2`. **(4)** identical across two builds apart from the timestamp; hashes match. **(5)** identical (whole manifest **and** content_hash) with adapter order reversed. **(6)** recorded and unrecorded builds produce a byte-identical corpus; `NullObserver` is the default. Plus: per-source licenses + corpus-level non-commercial flag; real 64-hex SHA-256 per input, never "synthetic"; the AOI mismatch and the variogram support gap. |

`test_covariate_stack.py`'s byte-identical test was **strengthened**, not
relaxed: rasters still compared byte-for-byte, and provenance.json now
compared field-for-field minus `generated_at` **plus** an assertion that
`content_hash` matches — a sharper determinism check than the byte compare it
replaces, because the hash is computed over substance.

## Hand-check

```bash
python -m engine.prospectivity.ingestion.corpus_builder   # writes CSV + manifest
```

Then in `data/corpus/manifest.json`: `contributing_sources` lists **two**
sources; `sources_absorbed_entirely` is `["src_so268_nodules"]`;
`training_eligible_count` is 35 against `corpus_row_count` 108 with
`rows_by_qa_status` explaining the gap (3 flagged); `study_area_containment`
reports 108 of 108 outside; and
`spatial_summary_training_eligible.pairwise_distance_km` shows **595 pairs**
(C(35,2) — the stations that can actually train) with `largest_gap_km` ≈ 974
between ≈12 km and ≈986 km. `spatial_summary_all_rows` records the same
structure over all 36 event locations (630 pairs) so the effect of excluding
the flagged box core is visible; the conclusion is identical either way.
Confirm `git diff` on `master_observations.csv` is empty — the manifest work
must not change the corpus.

## Deliberately not recorded

- **Dependency versions / `requirements.lock` hash** — BACKLOG §3, Phase 3;
  they describe a run environment, not a corpus.
- **The D8 `[01]`↔`[05]` reconciliation summary** (offered as an optional
  extension): declined. It compares *pre-dedup* adapter output, so the emitter
  would have to re-run both adapters and re-implement the comparison that
  `test_reconciliation.py` already owns — well past the ten-line bar, and it
  would duplicate test logic in production code.
- **Anything judgmental.** `geometry.py` states the cluster structure and the
  support gap; whether kriging is defensible on that support is a Phase-2
  decision (BACKLOG §4), not a warning this module emits.
