# Session State

Last updated: end of the session that built Phase 0 + Phase 1 E1.1.
Full detail on everything below: [`docs/walkthroughs/phase-0-and-E1.1.md`](walkthroughs/phase-0-and-E1.1.md).

## Git state (as of this update)

- Branch: `main` (up to date with `origin/main` at the time of writing)
- Last commit: `4160546` — "Phase 0 scaffold + E1.1 source adapters"
- That single commit contains everything listed as "Complete" below, including
  `docs/walkthroughs/phase-0-and-E1.1.md` itself.
- **This file is committed separately, immediately after being written.**

## Complete

### Phase 0 (E0.1–E0.5) — scaffold

- Repo layout, `pyproject.toml`, `docker-compose.yml` (Postgres/PostGIS + MinIO, unwired)
- Domain types: `engine/prospectivity/domain/{evidence,observation,study_area,terrain,ts6,results}.py`
- Empty-but-frozen interfaces: `terrain/source.py`, `samples/source.py`, `estimators/base.py`,
  `economics/model.py`, `ts6/reference.py`, `ingestion/{source_adapter,normalizer,specification,pipeline}.py`,
  `engine.py` (`ProspectivityEngine`, Template Method)
- Seven contracts copied into canonical locations: `docs/contracts/` + `data/{corpus,aoi,economics,sources,ts6,config}/`
- Synthetic fixtures: `data/fixtures/native/*.csv`, `tests/fixtures/{adapters,normalizers,sample_source,rasters}.py`
- CI: `.github/workflows/ci.yml` (runs `pytest -v` on every push)

### Phase 1, E1.1 — real SourceAdapters

- `engine/prospectivity/ingestion/_column_mapping.py` — shared fan-out helper (`EvidenceClassMapping`, `build_records()`)
- `engine/prospectivity/ingestion/pangaea_adapter.py` — `PangaeaAdapter` (PANGAEA DOIs `[01]`–`[05]`, `[12]`)
- `engine/prospectivity/ingestion/tabular_file_adapter.py` — `TabularFileAdapter` (Dryad/Mendeley xlsx/csv `[06]`, `[14]`)
- `engine/prospectivity/ingestion/regional_grid_adapter.py` — `RegionalGridAdapter` (GRID grids `[18]`, `[19]`)
- Tests: `tests/test_{pangaea,tabular_file,regional_grid}_adapter.py` + saved samples in `tests/fixtures/samples/`
- Deps added: `pangaeapy`, `openpyxl`

### Verified test count

```
$ pytest -v
============================== 44 passed in 0.93s ==============================
```
Re-run and confirmed passing at the time this file was written — not carried over from memory.

## In progress

Nothing. E1.1 is done and reviewed (walkthrough doc written, all 44 tests re-verified
green). Session is paused at a clean checkpoint before E1.2 starts.

## Next: E1.2 — real `AbundanceNormalizer` per evidence class

Paste this to start next session:

> Start Phase 1, task E1.2 only. Read `data/config/normalization.yaml` and
> `engine/prospectivity/ingestion/normalizer.py` first, and restate the per-evidence-class
> rules back to me. Then implement real `AbundanceNormalizer` subclasses in
> `engine/prospectivity/ingestion/` for all five evidence classes: `MassNormalizer`,
> `CountNormalizer`, `CoverNormalizer`, `GridNormalizer`, `GradeNormalizer`. Each must
> implement exactly the rule `normalization.yaml` specifies for its class (MASS:
> `kg_m2 = nodule_mass_kg / sampled_area_m2`, or pass through if already reported as
> kg/m2; COUNT: `kg_m2 = nodule_density_m2 * mean_nodule_mass_g / 1000` ONLY if
> `mean_nodule_mass_g` is present, else leave `abundance_kg_m2` untouched; COVER: never
> produce `abundance_kg_m2`; GRID: keep the compiled value as `abundance_kg_m2` but
> always flagged `observation_or_prediction` compiled/interpolated, never training-eligible;
> GRADE: never produce `abundance_kg_m2`, only join `mn/ni/cu/co_pct`). Keep the
> Strategy-pattern comment explaining what each class does and why, matching the style in
> `normalizer.py` and the three E1.1 adapters. Do NOT touch dedup (`Specification`) or the
> `SourceAdapter` classes — normalizers only. Write one test per normalizer proving its
> formula against a hand-built `RawRecord`, plus a regression test proving the
> COVER/GRADE normalizers never set `abundance_kg_m2` even when handed a record that
> already has `abundance_value_original` set. Stop when all five normalizer tests pass so
> I can review.

## Decisions and gotchas from this session

1. **Contract path mismatch.** `CLAUDE.md` points to `phase0-contracts-v3/`; the real
   files were under `Proposals and contract V3/Contracts_v3/`. Copied into canonical
   locations (`docs/contracts/` + `data/*`); `CLAUDE.md`'s own path reference is still
   stale.
2. **CSV quoting bug, fixed.** Two example rows in `master_observations.csv` (both the
   copy in this repo and the original under `Proposals and contract V3/`) had an
   unescaped comma in `notes`, breaking `pandas.read_csv`. Fixed by quoting the field in
   both files.
3. **`validate`-before-`dedup` ordering, disclosed not fixed.** `IngestionPipeline.run()`
   runs `validate` before `dedup`; the alpha proposal's shorthand states the reverse.
   Documented in `pipeline.py`'s module docstring — dedup rules need typed `Observation`
   fields, so this is intentional, but it's a real deviation from the proposal's literal
   wording.
4. **No hash-pinned lockfile yet.** `pyproject.toml` uses version ranges, not exact hash
   pins. Installing requires `--only-binary=:all:` (no local GDAL toolchain for a
   `rasterio` source build). Revisit with `uv`/`pip-tools` before a published run.
5. **No `source_id` FK enforcement.** `master_observations.schema.json` declares a
   `foreignKeys` constraint back to `source_queue.yaml`, but nothing in code checks a
   real `source_id` actually exists there. Intentional for now (E1.1's tests use
   synthetic `source_id`s that don't appear in the real queue) but worth closing before
   a real corpus is built.
6. **E1.1 coverage gap:** no test exercises a source with both GRID and GRADE evidence
   (that's `src_washburn2021_grid [19]`) — only the GRID-only case (`src_ts6_grid [18]`)
   is tested. The fan-out mechanism should support it; it's just unverified.
7. **E1.1 coverage gap:** no adapter has been run through a live `IngestionPipeline` with
   a real `AbundanceNormalizer` yet — every E1.1 test calls `adapter.fetch()`/`.adapt()`
   directly. That integration starts in E1.2/E1.3. There is no corpus-builder entry point
   yet.
8. `data/bathymetry/` was missing from the repo layout after the initial Phase 0 pass
   (caught by you, not by me) — added as an empty directory with a README explaining
   what belongs there and when (Phase 1 G1.1, Integration Checkpoint 1).
