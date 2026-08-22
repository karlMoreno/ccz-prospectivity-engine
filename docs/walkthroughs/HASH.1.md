# HASH.1 — shape-tolerant hashing, then the path-hash fix

**Landed 2026-08-22.** Specification: the HASH.1 prompt (Karl), itself built
on two BACKLOG §3 entries whose triggers order the commits — the
shape-tolerant decision's trigger is "before the path-hash fix", the
path-hash entry's is "before Checkpoint 1". Reading order:
`engine/prospectivity/provenance/artifact.py` (the scheme) → the four
`LEGACY_HASHED_FIELDS` declarations → `features/dem_grid.py` + `stack.py`
(commit 2) → `provenance/emitter.py`'s chain block → the tests.

| commit | what | suite |
|---|---|---|
| 1 | shape-tolerant hashing: present fields + `schema_version` in the substance; a LEGACY mode over frozen field sets; the new-field rule | 556 → **563** |
| 2 | the path-hash fix: the DEM path leaves the stack substance; the chain block updated to what is now true | see §2 |

**Both E-only. Neither needs Track G.**

## §0 — Premises verified before code

| claim | verified |
|---|---|
| the two BACKLOG entries say what the prompt says | yes — read at lines 1408 (shape-tolerant, decided, trigger "BEFORE the path-hash fix") and 1518 (path-hash, "nine times", trigger "BEFORE CHECKPOINT 1") |
| the committed historical set is TWO artifacts | `git ls-files data` → `data/corpus/manifest.json`, `data/runs/e2.4/run_manifest.json`; stack and matrix manifests are generated fresh per run and are unaffected |
| a plain "present fields" rule leaves both hashes alone | **NO — measured, and it decided the design.** `exclude_none` moves the E2.4 manifest (`e3ac1561…` → `b649fd96…`: its E3.4 re-stamp hashed five nulls IN the substance); `exclude_defaults` moves the corpus manifest too (`upstream_hashes: {}` is at its default). The prompt's STOP condition — "if it moves, STOP" — was therefore reachable under the naive scheme, which is why the scheme has a legacy mode |
| the DEM path enters the substance nine times | `DemGrid.provenance()["path"]`, quoted once at `dem` and once in each of 8 `layers[i].dem` (recipe.py:97, stack.py:102) — nine |
| nothing reads the path back | no consumer of `dem["path"]` in `engine/`; two E3.4 tests read it to locate the DEM file (updated in commit 2) |

## §1 — Commit 1: the scheme

```text
  fresh artifact ──construction──► schema_version = SCHEMA_VERSION (content_hash is None)
                                    substance = present (non-None) fields + schema_version
  reloaded with content_hash, no schema_version ──► LEGACY
                                    substance = LEGACY_HASHED_FIELDS (frozen), defaults included
                                              = byte-for-byte the pre-HASH.1 payload
```

**The decision, with the losing argument in the code** (`artifact.py`'s
module docstring): hash over PRESENT fields, schema version alongside —
INSIDE the substance, because outside it the mitigation would be
decorative — historical artifacts untouched. The counterargument (two
shapes can hash identically) is real and loses because the shape is
recorded elsewhere and the hash's job is substance.

**Why a legacy mode.** "Leave historical artifacts with their original
hashes" is not satisfiable by `exclude_none` alone (§0's measurement), so
artifacts that arrive with a `content_hash` and no `schema_version` — the
one discriminator that separates reloaded history from a fresh build, since
only `finalize()` sets `content_hash` — are hashed under the old rule over
a field set FROZEN per class as a literal. A snapshot, never computed from
the live fields: computed, it would track the additions it exists to keep
out (mutation H-M2′ below is exactly that regression).

**What it does not fix, bounded:** the two legacy artifacts carry no schema
version and cannot be told from a differently-shaped artifact by hash
alone. Both hashes are pinned by literal (`test_provenance_artifact.py`,
`COMMITTED`) so a scheme change that moved either fails by name. **The
E3.4 re-stamp stays** — said in the code where someone would be tempted.

**The new-field rule, structural:** a field a subclass INTRODUCES outside
its frozen set must default to `None`, refused at class definition
otherwise. The first draft refused too much — `test_cv_runner`'s `_Sneaky`
narrows the exclusion set, which made inherited `run_id` look new — so
"new" is defined as "not on any base class", and the exclusion test keeps
its own job.

### Tests (+7, `test_provenance_artifact.py`)

| test | asserts | separates |
|---|---|---|
| `…adding_a_field…does_not_change_an_existing_artifacts_hash` | a constructed one-field-later subclass: a fresh v1 reloaded hashes the same (versioned regime); the committed E2.4 artifact reloaded hashes to its stored value (legacy regime) — two assertions, two rules | the property the commit exists for, per regime |
| `…same_present_fields…different_schema_versions_are_distinguishable` | identical substance minus the version; different hashes | the counterargument's mitigation |
| `…schema_version_is_inside_the_hashed_substance_not_beside_it` | present in a fresh substance; absent from a legacy one (its frozen set predates the field) | "inside" from "alongside" |
| `…two_committed_artifacts_are_legacy_and_their_hashes_are_unchanged` | both load legacy; both equal their literal pins; the set has two members | the prompt's STOP condition, as a test |
| `…legacy_is_detected_by_a_content_hash_without_a_schema_version` | fresh → 1; with hash and version → kept; with hash, no version → legacy; `model_copy` preserves | the discriminator |
| `…every_real_artifact_declares_a_frozen_legacy_set…` | declared in each class's own `__dict__`; ⊆ live fields; equal today, with the inequality message saying "bump SCHEMA_VERSION" | a snapshot from an inherited or computed set |
| `…new_field_with_a_non_none_default_is_refused_at_class_definition` | `list` default refused by name; `None` default accepted | the rule from "no new field exists" |

### Mutations 4/4 (one re-run in its realistic form)

| # | mutation | caught by |
|---|---|---|
| H-M1 | versioned substance covers absent fields again (the old rule) | the versioned case of the adding-a-field test, by name |
| H-M2 | legacy set turned into a `property` | **not a survivor: an IMPORT error** (`TypeError: argument of type 'property' is not iterable` in `__pydantic_init_subclass__`) — loud, but the harness's line filter counted it as 0 failed. Recorded because a mutation that "passes" for an unexamined reason is the instrument defect CLAUDE.md names |
| H-M2′ | legacy substance reads the LIVE fields at the point of use | the legacy case of the adding-a-field test: "the frozen set did not hold" |
| H-M3 | `schema_version` excluded from the substance | the distinguishability test and the inside-not-beside test |
| H-M4 | the new-field refusal removed | the positive control: DID NOT RAISE |
