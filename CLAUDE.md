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

## Data origin: every value is classified

Every value in this repo declares HOW IT CAME TO EXIST HERE, using the five-member
vocabulary in `engine/prospectivity/provenance/origin.py` (P2.0). This section is the
durable home of the standing decisions; the reasoning lives in
`docs/audits/2026-08-08-origin-vocabulary-audit.md` and `docs/walkthroughs/P2.0.md`.
All five evidence requirements are ENFORCED, which is checkable:

- **MEASURED** — a measurement dataset this repo holds. Evidence: the file present with
  its recorded SHA-256 matching the bytes → **production guard** (`_require_proven_measured`).
- **DERIVED** — computed from MEASURED inputs. Evidence: the derivation formula or the
  artifact recording it → **audit resolver** (`tests/test_data_origin_audit.py`).
- **LITERATURE** — a value from a publication, no file in hand. Evidence: a citation that
  LOCATES the number (document + table/section/page; "TS-6" alone is insufficient) →
  **audit resolver**.
- **SYNTHETIC** — generated by a deterministic recipe. Evidence: the generator's import
  path AND seed(s) — the only thing separating a seeded generator from hand-typed values
  under a `synthetic_*` filename → **audit resolver**. Nothing is renamed: the
  `synthetic_*`/`src_synthetic_*` misnomers are recorded in docstrings, and no code may
  infer origin from a name, title, or path — declaration or nothing.
- **AUTHORED** — someone typed it. Evidence: `author:` from the `ALLOWED_AUTHORS`
  allow-list → **audit resolver**. `author: unrecorded` is NOT available to new work; it
  names the frozen set of pre-P2.0 files in `tests/test_data_origin_audit.py`, which can
  only shrink.

**Propagation:** `combine_origins` returns the LEAST-real input — a real corpus does not
launder a synthetic terrain — and file-level and run-level origins are COMPUTED with it
(entries → file, artifacts → run), never hand-written.

**The authoring rule (operative in every session):** when you create a file containing
values — a fixture, a contract default, an example row, a stand-in parameter — you
declare its origin IN THE SAME EDIT, never afterwards. A value whose origin is added
later is a value someone reconstructed from memory. If you cannot determine the origin
of a value you are about to write, that is the STOP-on-ambiguity condition, not an
invitation to pick the most plausible label.

**The prohibition:** nothing reachable from a production build path may be other than a
MEASURED declaration with COMPLETE evidence, and production corpus inputs live under
`data/sources/`. The guard checks the proof — a hash over real bytes — never the claim.
Watermarks derive from declarations, default-ON: absence of proof produces a watermark,
never a clean render.

Why each rule exists (evidence, not assertion): `[06]` and `[18]` reached
`REAL_ADAPTER_BUILDERS` as fabricated fixtures and were caught by a person reading a
file, not by a test; `data/fixtures/native/`'s fabricated CSVs sat on the real-data side
of both path guards until the 2026-08-08 audit; and a MEASURED label on an undownloaded
source is indistinguishable from a fabricated one without its hash — which is why the
guard checks the proof and not the claim.

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

## Testing conventions (a test that guards nothing is worse than no test)

Three separate audits have now found the same class of defect in this repo: a test
that **counts as coverage while guarding nothing**. It is worse than a missing test,
because a missing test is visible. These rules exist because each one was learned the
hard way — the evidence is cited, not asserted.

1. **A test's name must describe what its assertions verify** — not what the author
   intended to verify, and not the rule the test sits near.
   *Evidence:* the test-name audit (2026-07-30) found **17** names claiming more, less,
   or other than their bodies checked. Two could have caused a wrong action rather than
   mere confusion: `test_mass_rows_are_training_eligible` stated a rule that is FALSE
   since P1 (a flagged MASS row is not eligible) and contradicted
   `test_sample_source.py`'s opposite assertion; and
   `..._reconciles_exactly_for_at_least_31_of_36_events` invited a maintainer to
   "fix" a failure by loosening toward 31, quietly erasing the documented D8 residual
   the body exists to pin.

2. **A test asserting a rule must not load its data through the class that enforces
   that rule.** It can never observe a violation — the loader raises first, so the
   assertion is decorative and the failure it reports names the wrong thing.
   *Evidence:* E1.5 found `test_observation_schema.py`'s COVER/GRID assertions read the
   corpus via `Observation(**row)`, whose validator forbids exactly those violations.
   Fix: assert against the raw artifact (see `tests/test_corpus_invariants.py`, which
   reads the corpus CSV as strings with no Pydantic in the path).

3. **An assertion that something is "unchanged" must compare full state**, not selected
   fields. Same for "identical", "adds nothing", "survives untouched".
   *Evidence:* E1.5's `..._adds_nothing` compared row count and IDs only, and passed
   while every merged row's `notes` tripled on re-runs — one of them recording the row
   as a duplicate of ITSELF.

4. **A hand-computed fixture must separate the claimed statistic or rule from its
   neighbors.** A fixture whose SYMMETRY makes distinct claims coincide verifies the
   value while being unable to distinguish the statistic — a different defect than
   coverage-that-isn't, because the assertion is real and the fixture is blind.
   *Evidence:* on `[2, 4, 6]`, SD, MAD, and half-range are all exactly 2.0, and a
   spread-statistic swap survived every hand-computed test (E2.1 MB9; fixed by
   `[13, 11, 8, 9, 9]`, where SD, SE, MAD, half-range, and ddof=0 all separate).
   The same idea in different clothes: E2.0-2's `shared_cell_count == len(stations)`
   is numerically true on the real corpus, so only a constructed mixed-occupancy
   fixture could catch the hardcode. When building a fixture, state in its docstring
   which neighboring claims it separates.

Corollaries worth keeping in mind:

- **A fixture must be able to distinguish the claim from its negation.** If every
  fixture row shares a value, a test asserting that value is read "per row" cannot fail
  when the code hardcodes it.
- **Aggregate assertions do not prove per-item claims.** A total and a set of classes
  are satisfied by a skewed distribution; group and assert per item.
- **Prefer a mutation check to a green run.** Break the thing on purpose, watch the test
  fail, restore it. This project's established practice, and it is how every guard above
  was verified.

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

- Phase: **1, Track E — complete through E1.4** (as of 2026-07-29). Phase 0's scaffold +
  seven contracts, real ingestion (E1.1 source adapters, E1.2 normalizers, E1.3 dedup +
  corpus build, plus the P1/P1b/P2/P3 review batches), and terrain feature recipes (E1.4:
  Contract 3 v3 metre-based windows, the 8 Option-A covariates, the plot deliverable) are
  all built and reviewed.
- **Corpus state:** `data/corpus/master_observations.csv` holds **108 rows** (36 SO268
  box-core events × MASS/COUNT/COVER), of which **35 are training-eligible**. It is
  **single-source** (`[01]`+`[05]` merged under `src_so268_boxcore`) until Track G delivers
  real Dryad `[06]` data or the TS-6 `[18]` digitization — both are deliberately unwired
  because their placeholders were fabricated. `data/corpus/manifest.json` is the build
  record; see `docs/contracts/PROVENANCE.md`.
- **Next task:** the provenance manifest work is done for ingestion + features; Phase 2
  (estimators + spatial CV) is next, and needs a decision on the training target first
  (buried vs surface abundance — `docs/BACKLOG.md` §1).
- **Open items live in `docs/BACKLOG.md`** — the single source of truth, grouped by who is
  blocked. Read it before proposing work; add an entry whenever something is deliberately
  deferred.
- Per-task walkthroughs are in `docs/walkthroughs/` (`phase-0-and-E1.1.md`, `E1.2.md`,
  `E1.3.md`, `E1.4.md`). Read the relevant one before changing that area.
- The seven contracts live in `docs/contracts/` + `data/` (canonical — see the paths above);
  `Proposals and contract V3/Contracts_v3/` holds the authoring copies. Treat them as frozen;
  if one needs a structural change, bump its `*_version`, tell me, and note it in the
  contracts README.
- Do **not** jump ahead to Phase 2 (estimators, spatial CV) without my go-ahead — the
  phase-boundary rule above still governs.



