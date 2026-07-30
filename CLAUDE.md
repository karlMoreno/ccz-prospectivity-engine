# CLAUDE.md — CCZ Prospectivity Engine

This file is read automatically by Claude Code at the start of every session.
It encodes how this project must be built. Follow it unless I explicitly override
a point in the conversation.

---

## What this project is (one paragraph)

An open, reproducible modernization of **ISA Technical Study No. 6 (2010)**: for one
Clarion-Clipperton Zone (CCZ) study area, predict polymetallic-nodule abundance
(kg/m²) from an openly-sourced sample corpus + terrain covariates, with honest
uncertainty, an economic minability layer, a provenance manifest, and a benchmark
comparison against the TS-6 2010 surface. Two people build it: **Track E** (engineer,
the code) and **Track G** (geologist, the data + science). They are decoupled by a set
of frozen **contracts**. The authoritative specs are:

- `Proposals and contract V3/CCZ-Prospectivity-Engine-Alpha-Proposal-v3.md` — the build
  plan (phases, scope, requirements).
- The seven contracts (frozen data/interface shapes) — **treat these as ground truth**:
  - **Canonical (what the code reads):** `docs/contracts/` (schema, `covariates.yaml`,
    contracts README) + `data/` (`config/normalization.yaml`, `sources/source_queue.yaml`,
    `aoi/study_area.geojson`, `ts6/ts6_reference.yaml`, `economics/scenarios.yaml`).
  - **Authoring copies (Karl's source documents, not read by any code path):**
    `Proposals and contract V3/Contracts_v3/`.
  - Path corrected 2026-07-29 (P3): this file previously pointed at
    `phase0-contracts-v3/`, which has never existed in the repo.

If anything I ask conflicts with those documents, say so and ask before proceeding.

---

## The single most important rule: STOP AT PHASE BOUNDARIES

Build **one phase at a time** (Phase 0 → 1 → 2 …, per the alpha proposal §10). At the
end of each phase:

1. Summarize what you built and how it maps to the phase's exit criteria.
2. Run the tests / CI and show me they pass.
3. **STOP and wait for my review. Do not start the next phase until I say go.**

I am the engineer of record and must understand every part of this codebase (I have to
defend it to grant reviewers). Never accumulate code I haven't reviewed. Prefer many
small, reviewable steps over one large leap.


- At the end of each phase (and each significant task), also write or update
  `docs/walkthroughs/<phase>.md`: reading order, ASCII architecture diagram,
  per-file explanation, a test inventory table (what each test asserts in plain
  English + which contract rule it enforces), how to hand-check it manually,
  what's deliberately missing, and what the next task will add.

---

## Design-pattern discipline (my standing preference)

- Use explicit, named **design patterns** for the architectural seams, and **explain in a
  comment which pattern is used, for what, and why** — right where it's implemented.
- The patterns this project expects (from the proposal):
  - **Strategy** — swappable implementations behind an interface: `TerrainSource`,
    `SampleSource`, `ProxySource`, `Estimator`, `EconomicModel`, `TS6Reference`,
    and (ingestion) `SourceAdapter`, `AbundanceNormalizer`.
  - **Template Method** — fixed sequences: `IngestionPipeline.run()`
    (fetch→adapt→normalize→dedup→validate→append) and `ProspectivityEngine.run()`
    (ingest→features→CV→predict→uncertainty→economics→compare_to_ts6→manifest).
  - **Adapter** — one `SourceAdapter` per source-family → the master-observation schema.
  - **Specification** — dedup + quality rules as small composable predicates.
- "Program to an interface, not an implementation." Adding a data source, a model, a
  covariate, or a whole new body (the future lunar port) should mean **adding a class,
  not rewriting the pipeline.** If a change forces a pipeline rewrite, stop and flag it.

## Documentation & explanation style

- When you explain architecture or flow (in comments, docstrings, `docs/`, or chat),
  include a small **ASCII UML / box diagram** so I can visualize it. This is a hard
  preference, not optional.
- Keep prose explanations tight. Diagrams + short paragraphs over walls of text.

---

## Scientific-integrity rules (these protect the model — do not violate)

These come from the contracts (`master_observations.schema.json`, `normalization.yaml`)
and are the whole point of the project. Encode them in code + tests, not just docs.

- **Evidence classes are sacred.** Every observation is tagged exactly one of
  `MASS | COUNT | COVER | GRID | GRADE`. Never untagged.
- **Train on `MASS` only.** `SampleSource` selects rows where
  `evidence_class == MASS AND abundance_kg_m2 is present AND is_open == true`. Nothing else.
- **`COVER` is NEVER converted to kg/m².** Percent cover is a covariate, never a bare
  abundance value. If you ever find yourself writing cover→mass into `abundance_kg_m2`,
  that is a bug — stop.
- **`GRID` is a prior/benchmark, never a training station** (TS-6, Washburn). It must be
  flagged `observation_or_prediction != observed`.
- **`COUNT` → kg/m² only via a recorded `mean_nodule_mass_g`**, with the assumption and its
  uncertainty written into `derivation_formula` / `quality_grade`.
- **Provenance is mandatory.** Every derived value records its `derivation_formula`; every
  row traces to a `source_id` in `source_queue.yaml`. Only `is_open == true` sources may
  enter a "published" run.
- **Spatial cross-validation is mandatory** for any model claim. Never report a plain
  random-split score. Always run the mean baseline alongside. A run cannot be marked
  VALIDATED if spatial CV did not run.
- **Uncertainty is always paired** with any prediction surface. Never emit a prediction
  without its uncertainty.
- **Honesty over impressiveness.** If the data is thin or a result is weak, say so plainly.
  Never fabricate values; use clearly-labeled placeholders ("illustrative only") and tell me.

---

## Dependency & scope discipline (keep it small)

- **Minimal dependencies.** This runs on a laptop in minutes. Approved stack only:
  Python 3.11+, `rasterio`, `numpy`, `pandas`, `geopandas`/`shapely`, `scikit-learn`,
  `scikit-gstat`/`pykrige`, `richdem`/`xarray-spatial`, `pydantic`, `pytest`,
  `pangaeapy` (ingestion), `fastapi` (read-only API later). Ask before adding anything else.
- **No** Kubernetes, task queues, Redis, clusters, or an upload-and-compute web backend.
- **Do not bulk-install agent/skill harnesses or plugins.** Add tooling deliberately, one
  piece at a time, only when a concrete need appears.
- Stay inside the current phase's scope. If something feels like Phase B/C, Option-B
  proxies, multiple study areas, or the lunar port — it's out of the alpha. Flag it, don't build it.

---

## Reproducibility rules

- Hash-pin dependencies (lockfile). Content-hash every ingested input; record it.
- Every model run emits a **provenance manifest** (inputs + hashes, params, seeds, CV
  strategy + scores, baseline scores, TS-6 agreement, output hashes).
- Set and record random seeds. Same inputs + seed → same outputs.
- CI runs the full pipeline end-to-end on **synthetic fixtures** every push. The fixtures
  are the concurrency safety net — keep them working.

---

## Workflow conventions

- **Research/read before writing.** Before implementing against a contract, read that
  contract file and restate its shape back to me in one or two lines.
- Write the **test alongside the code** (pytest). For the integrity rules above, the test
  is the enforcement (e.g. a test that fails if a `COVER` row ever gets `abundance_kg_m2`).
- Small commits with clear messages. One logical change per commit.
- When you finish a unit of work, show: what changed, why, the test result, and the
  ASCII diagram if the structure changed.
- If you're unsure about a geology decision (sampled area, wet/dry basis, mean nodule
  mass, which covariates matter), **mark it `[GEOLOGY — ISAAC]` and leave a safe default +
  a TODO** rather than guessing silently.

---

## Repository layout (target — from the alpha proposal §12)

```
ccz-prospectivity-engine/
├── engine/prospectivity/
│   ├── domain/          # Observation/EvidenceClass, StudyArea, results
│   ├── ingestion/       # SourceAdapter + AbundanceNormalizer + dedup (Specification)
│   ├── terrain/ · samples/ · features/
│   ├── estimators/      # kriging, random_forest, mean_baseline
│   ├── validation/ · uncertainty/
│   ├── ts6/             # TS6Reference + compare_to_ts6()
│   ├── economics/       # EconomicModel + scenarios
│   ├── provenance/      # manifest emitter (run + corpus)
│   └── engine.py        # Template Method run()
├── services/api/        # read-only FastAPI (later phase)
├── apps/web/            # thin viewer (later phase)
├── database/            # migrations, fixtures
├── data/                # contracts live here (corpus/, sources/, config/, aoi/, ts6/, economics/, fixtures/)
├── docs/contracts/      # the seven contracts + README
└── docker-compose.yml · Makefile · README.md · CLAUDE.md
```

---

## Current status

- Phase: **0 (scaffold) — not yet started.** Start here.
- The seven contracts live in `docs/contracts/` + `data/` (canonical — see the paths above);
  `Proposals and contract V3/Contracts_v3/` holds the authoring copies. Treat them as frozen;
  if one needs a structural change, bump its `*_version`, tell me, and note it in the
  contracts README.
- Do **not** jump ahead to Phase 1 (real source adapters) until Phase 0's scaffold +
  synthetic fixtures + green CI exist and I've reviewed them.



