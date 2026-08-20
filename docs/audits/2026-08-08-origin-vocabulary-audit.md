# Origin-vocabulary audit — 2026-08-08

- **Performed against:** commit `34c86f440e31e0fea291d12fd3eeab434aec7fa7`
  (`git rev-parse HEAD` at audit time; the working tree was clean apart from
  untracked docs).
- **Status:** point-in-time report. It records what was found on 2026-08-08;
  where this document and the code disagree, the code wins.
- **data_origin:** AUTHORED · **author:** model
- Note on links: inline file links are repo-root-relative (written for the
  session UI); resolve them from the repository root, not from this file's
  directory.

The report below is reproduced verbatim from the audit session's final
message. Disagreements, if any arise later, are to be added as dated notes
under the finding they dispute — the report itself is not edited.

---

Audit complete. Read-only throughout; nothing was edited. The headline before the six sections: I found **not four but roughly two dozen distinct mechanisms**, including two machine-readable origin fields you didn't list (`placeholder: true` in the AOI file, and the `src_synthetic_*` source-id convention), one latent hole (`data/fixtures/native/` fabricated CSVs sit on the **"real_data"** side of both path-heuristic guards), and four contradictions beyond the one you predicted — including one where the samples-directory README claims the opposite of what one of its files' own header says.

---

## 1. INVENTORY

The repo's word "synthetic" is doing double duty throughout: it covers both taxonomy-SYNTHETIC (seeded generators) and taxonomy-AUTHORED (hand-typed values). Rows grouped by layer.

**Machine-readable fields**

| Where | Mechanism | Value domain | What it actually means |
|---|---|---|---|
| [corpus_manifest.py:87](engine/prospectivity/provenance/corpus_manifest.py:87), computed at [:275–282](engine/prospectivity/provenance/corpus_manifest.py:275), recorded at [manifest.json:50](data/corpus/manifest.json:50),:77 | `backed_by` per source | `"real_data" \| "fixture" \| "unknown"` | Path-shape inference: "fixture" iff the input path contains **both** `tests` and `fixtures`; `None` path → "unknown"; everything else → "real_data". Only the "real_data" branch is ever test-asserted ([test_corpus_manifest.py:214](tests/test_corpus_manifest.py:214)) |
| [scenarios.yaml:56](data/economics/scenarios.yaml:56),:71; typed at [results.py:68](engine/prospectivity/domain/results.py:68) | `illustrative_only` | boolean | "These numbers are authored placeholders; while true the engine must watermark and may not present output as real" ([scenarios.yaml:7–11](data/economics/scenarios.yaml:7)). Propagation is an interface obligation ([model.py:39–42](engine/prospectivity/economics/model.py:39)); a test pins **all** scenarios true ([test_contracts_parse.py:31–34](tests/test_contracts_parse.py:31)) |
| [study_area.geojson:13–14](data/aoi/study_area.geojson:13) | `"placeholder": true` + `"(PLACEHOLDER)"` in `name` | boolean + naming | The AOI self-marks as an authored illustrative box. Consumed descriptively only ([geometry.py:199](engine/prospectivity/provenance/geometry.py:199), [manifest.json:163](data/corpus/manifest.json:163)). This is the repo's **second** machine-readable origin field, and it uses a different vocabulary than `backed_by` |
| [schema:287–293](docs/contracts/master_observations.schema.json:287); [observation.py:88](engine/prospectivity/domain/observation.py:88); live in every corpus row | `derivation_formula` | free text, required-when-computed (AR-D04) | Per-row DERIVED mechanism: the formula by which a computed value was produced |
| [schema:296–308](docs/contracts/master_observations.schema.json:296); [evidence.py:31–37](engine/prospectivity/domain/evidence.py:31) | `observation_or_prediction` | `observed \| compiled \| interpolated \| modelled` | Epistemic status of the datum **in the world** (physical sample vs someone's compiled/model product). Guard: GRID may never be `observed` ([observation.py:124–127](engine/prospectivity/domain/observation.py:124)) |
| [schema:319–330](docs/contracts/master_observations.schema.json:319); defaults per class in [normalization.yaml](data/config/normalization.yaml) (A/B/C at :39, :53, :65, :76, :88) | `quality_grade` | `A \| B \| C` | Confidence — but the per-class defaults encode origin-adjacent facts (B = "derived via an assumption", C = compiled) |
| CSV columns `abundance_value_original` / `abundance_unit_original` / `abundance_basis` ([master_observations.csv:1](data/corpus/master_observations.csv:1)) | original-vs-derived value pairing | free | Preserves the reported value beside the computed one — DERIVED's audit trail |
| [ts6_reference.yaml:65–70](data/ts6/ts6_reference.yaml:65); [results.py](engine/prospectivity/domain/results.py) `TS6Agreement.role_note` | `role_note` | `benchmark_only \| reproduction_check` (null today) | Whether the TS-6 comparison is independent or circular — an origin-of-validation marker |
| [source_queue.yaml](data/sources/source_queue.yaml) `primary_use` (:37 etc.) | role vocabulary | `TRAIN \| TRAIN_AGGREGATE \| COVARIATE \| BENCHMARK \| PRIOR \| CONTEXT` | Modeling role; BENCHMARK/PRIOR correlate with compiled products but it is not an origin field |

**Guards and code constants**

| Where | Mechanism | Value domain | What it actually means |
|---|---|---|---|
| [corpus_builder.py:79–101](engine/prospectivity/ingestion/corpus_builder.py:79) | `_require_production_path()` + `_FIXTURES_PATH_PARTS` | raises / passes | Refuses paths containing both `tests` and `fixtures` at adapter construction on the production path — same predicate as `_backed_by` |
| [corpus_builder.py:239](engine/prospectivity/ingestion/corpus_builder.py:239); unwired builders at :177–221 | `REAL_ADAPTER_BUILDERS` (the name is the claim) | list membership | Membership = "this source reads real data"; `[06]`/`[18]` excluded with docstrings recording why |
| [contract_versions.py:23–29](engine/prospectivity/provenance/contract_versions.py:23) | `file_sha256()` "no placeholders" doctrine | `sha256:<hex>` | Every recorded hash must be computed from real bytes; `DemGrid.from_terrain_layer` verifies a layer's reported hash against bytes read (E1.5, mutation-verified) |
| [plot_stack.py:64–66](engine/prospectivity/features/plot_stack.py:64), docstring :12 | `SYNTHETIC` watermark | hardcoded suptitle string | Stamps the plot "SYNTHETIC DEM (seeded noise; illustrative only…)". **Unconditional** — not driven by any recorded origin fact (see §5) |
| [test_corpus_invariants.py:154](tests/test_corpus_invariants.py:154) | `DELIBERATELY_UNREACHABLE` | set of evidence classes | "Registered but no wired adapter produces it" — code reachability, adjacent to origin but about the pipeline, not values |
| [test_corpus_manifest.py:207](tests/test_corpus_manifest.py:207) | placeholder-hash rejection test | pass/fail | Pins that every recorded input hash is computed, not the `"sha256:synthetic-fixture"` class of fake |

**Naming and file conventions**

| Where | Mechanism | What it actually means |
|---|---|---|
| [data/fixtures/native/](data/fixtures/native) `synthetic_*_native.csv`; [adapters.py:31](tests/fixtures/adapters.py:31),:92,:124 `src_synthetic_*`; [conftest.py:47–56](tests/conftest.py:47) | filename + source-id convention | "These values are made up" (cruise `SYN01`). Hand-typed — **no generator, no seed**, so taxonomy-AUTHORED despite the name |
| [rasters.py:66–77](tests/fixtures/rasters.py:66) `write_synthetic_bathymetry` / `write_synthetic_ts6_raster` | generator functions, seeds 0 and 1 | The only artifacts meeting the strict SYNTHETIC definition (deterministic recipe + recorded seed + import path) |
| [rasters.py:80–124](tests/fixtures/rasters.py:80) `FixtureTerrainSource` / `FixtureTS6Reference`; TS6 title "Synthetic TS-6 benchmark (fixture)" :119 | origin in the layer's `name`/`title`, real computed hash | E1.5's rule: being synthetic is recorded in the name, never by faking a hash |
| [so268_nodules_sample.csv:1–6](tests/fixtures/samples/so268_nodules_sample.csv:1) | in-file `TEST FIXTURE NOTE` header | "VERBATIM excerpt (not synthetic) of the real PANGAEA.904962… CC BY-NC 4.0" — the repo's **only** per-file origin header, and its best existing pattern |
| [normalizers.py:11](tests/fixtures/normalizers.py:11) | `SYNTHETIC_MEAN_NODULE_MASS_G = 12.5` | "[GEOLOGY — ISAAC placeholder]; fixture-only" — a hand-picked constant (AUTHORED), "synthetic" in name only |

**Tag and prose conventions**

| Where | Mechanism | What it actually means |
|---|---|---|
| 29 sites across the seven contract-side files (normalization 3, ts6 5, scenarios 8, source_queue 7, exclusions 1, study_area 2, covariates 3) | `[GEOLOGY — ISAAC]` tag | "This value is an authored engineering stand-in awaiting domain confirmation" — origin marker **and** task-ownership marker in one |
| [scenarios.yaml:38](data/economics/scenarios.yaml:38),:46,:57–58,:72–73 | `<<< PLACEHOLDER >>>` inline markers | Comment-level authored-value flags, human-readable only |
| [source_queue.yaml](data/sources/source_queue.yaml) `license/accessed_date/content_hash/sampled_area_m2: null` passim; header :9–10 | null-until-download convention | "Not yet fetched/verified here"; `is_open==true` gates published runs |
| [Contracts_v3/master_observations.schema.json:2](Proposals and contract V3/Contracts_v3/master_observations.schema.json:2) | `$HISTORICAL_ARTIFACT` header | Document-status marker: frozen authoring copy, not authoritative — not a value-origin claim |
| Doc-claims layer: [ci.yml:3–6](.github/workflows/ci.yml:3) ("synthetic sources in data/fixtures/native/"), SESSION_STATE.md:24 *(file DELETED at P2.CLOSE, 2026-08-20; it survives at `58aced6`)*, [bathymetry README](data/bathymetry/README.md), CLAUDE.md corpus paragraph, module docstrings ([source_adapter.py:8](engine/prospectivity/ingestion/source_adapter.py:8), [dem_grid.py:4](engine/prospectivity/features/dem_grid.py:4), [ts6/reference.py:4](engine/prospectivity/ts6/reference.py:4), [terrain/source.py:4](engine/prospectivity/terrain/source.py:4)) | prose origin claims | Where origin currently *lives* for anything without a field — searchable, unverifiable, and duplicated |

---

## 2. OVERLAP ANALYSIS

**`backed_by` — REPLACES.** It is the closest existing thing: already the per-source origin slot in the manifest, already consumed by a test, already positioned exactly where a taxonomy label belongs. But its three values are inferred from path shape, and the inference is wrong for `data/fixtures/native/` (contains `fixtures` but not `tests` → books as `"real_data"`). Keeping `backed_by` beside a new origin field would give two vocabularies that disagree precisely where it matters. The taxonomy should take over this field's slot: `real_data`→MEASURED, `fixture`→AUTHORED or SYNTHETIC, `unknown`→an explicit unclassified state — declared by the source entry and *verified* rather than inferred. (Changing it changes the manifest's `content_hash` on rebuild — that is a deliberate, versioned contract change, not breakage; see §6.)

| Mechanism | Verdict | Why |
|---|---|---|
| `illustrative_only` | **SUBSUMES** the origin half, leaves the policy half | The flag conflates "these values are AUTHORED" (origin — taxonomy's job) with "output must be watermarked and unpublishable" (consequence — stays). The flip-to-false at Checkpoint 4 *is* an origin transition (AUTHORED → LITERATURE/MEASURED) wearing a policy costume |
| `SYNTHETIC` plot watermark | **SUBSUMES** | A rendering consequence of SYNTHETIC origin. Today it's a hardcoded constant (§5); under the taxonomy it becomes derived from the DEM layer's recorded origin — which fixes it |
| `_require_production_path()` | **LEAVES ALONE** as a guard, subsumes its predicate | The refusal role stays; the *criterion* (path shape) is what the taxonomy replaces — "refuse anything on the production path not declared MEASURED" is checkable, path-independent, and closes the `data/fixtures/native/` hole |
| `REAL_ADAPTER_BUILDERS` membership | **LEAVES ALONE** | Wiring control. Membership stops being the origin *claim* once sources declare origin, but the list itself remains the build roster |
| `derivation_formula` (+ `*_original` columns) | **SUBSUMES** | It is DERIVED's required evidence, verbatim. The taxonomy adopts it; nothing new needed at row level |
| `observation_or_prediction` | **LEAVES ALONE** | Different axis: how the value came to exist *in the world* (sample vs compiled product), not how it entered *this repo*. A real TS-6 GRID row would be LITERATURE + `compiled`; a station row is MEASURED + `observed`. Orthogonal, with a documentable mapping |
| `quality_grade` | **LEAVES ALONE** | Confidence disposition. The origin-ish content of its class defaults (B ≈ assumption-derived) migrates to DERIVED; the grade stays a quality judgment |
| `qa_status` | **LEAVES ALONE** | Quality disposition (your pre-classification holds) |
| `is_open` | **LEAVES ALONE** | License fact (your pre-classification holds) |
| `placeholder: true` (AOI) | **SUBSUMES** | The repo's other machine-readable origin boolean, in a third vocabulary. Becomes AUTHORED + author + reason; the boolean can stay as a courtesy but stops being load-bearing |
| `[GEOLOGY — ISAAC]` tags | **SUBSUMES** the origin half, leaves the workflow half | "This is an authored stand-in" → AUTHORED with an owner. "Isaac must fill this" is task routing and stays |
| `<<< PLACEHOLDER >>>` markers | **SUBSUMES** | Comment-level AUTHORED flags, absorbed by the same declaration |
| null-until-download convention | **SUBSUMES** partially | Nulls currently *imply* "nothing measured here yet"; the taxonomy states it. The license/access fields themselves are untouched |
| `primary_use` | **LEAVES ALONE** | Modeling role, not origin |
| `role_note` (benchmark/circularity) | **LEAVES ALONE** | Validation-independence, its own axis |
| `file_sha256` / hash-verification discipline | **LEAVES ALONE** | Identity/integrity layer the taxonomy *chains to* — MEASURED's evidence requirement, not its replacement |
| `synthetic_*` / `src_synthetic_*` / `(PLACEHOLDER)` naming | **REPLACES** as signal | Naming stays as human courtesy; the checked thing becomes the declared field. Note the terminology collision the taxonomy resolves: repo-"synthetic" = "made up", taxonomy-SYNTHETIC = "seeded generator" — today's usage is mostly taxonomy-AUTHORED |
| `$HISTORICAL_ARTIFACT` | **LEAVES ALONE** | Document authority status, not value origin |
| `DELIBERATELY_UNREACHABLE` | **LEAVES ALONE** | Code reachability |
| Prose/docstring origin claims (CI header, READMEs, CLAUDE.md) | **REPLACES** as evidence source | Docs stop being where origin is *established*; they describe what the fields declare |

---

## 3. CLASSIFICATION

**`data/`**

| File | Origin | Evidence |
|---|---|---|
| [SO268-bc-nodules-summary-PANGAEA-904967.tab](data/sources/SO268-bc-nodules-summary-PANGAEA-904967.tab) | **MEASURED** | Published PANGAEA dataset; in-file citation block (Schoening & Gazis 2019, DOI 10.1594/PANGAEA.904967); SHA-256 recorded in the manifest |
| [SO268-bc-nodules-PANGAEA-904962.tab](data/sources/SO268-bc-nodules-PANGAEA-904962.tab) | **MEASURED** | Same authors, DOI 10.1594/PANGAEA.904962; SHA-256 recorded |
| [source_queue.yaml](data/sources/source_queue.yaml) | **MIXED: AUTHORED registry carrying LITERATURE facts** | Structure, `primary_use`, notes, and the 0.25 default generalization are authored; DOIs/titles/licenses are facts about publications. `sampled_area_m2: 0.25` for `[01]`/`[05]` is traceable to the source itself — the 904967 abstract states the 50×50 cm box and "multiply this value by 4" |
| [master_observations.csv](data/corpus/master_observations.csv) | **MIXED: MEASURED + DERIVED** (file-level: DERIVED from MEASURED inputs) | Coordinates/masses/counts/cover are measured values from `[01]`/`[05]`; `abundance_kg_m2`, `mean_nodule_mass_g`, `nodule_density_m2` are computed, each with a per-row `derivation_formula`; `notes`/QA text is authored by the pipeline. Generated by `build_corpus()` — never hand-written |
| [manifest.json](data/corpus/manifest.json) | **DERIVED** | Generated by `CorpusManifest`/`ProvenanceRecorder` from the build; content-hash chained per [PROVENANCE.md](docs/contracts/PROVENANCE.md) |
| [normalization.yaml](data/config/normalization.yaml) | **MIXED: LITERATURE + AUTHORED** | Screening block :17–24 cited "from TS-6 Table 2" (LITERATURE); rules prose, dedup key, `coordinate_tolerance_deg: 0.001` are authored policy; two geology parameters declared null |
| [scenarios.yaml](data/economics/scenarios.yaml) | **AUTHORED** (with LITERATURE anchors) | Self-declares "ALL VALUES ARE ILLUSTRATIVE PLACEHOLDERS"; cutoffs 10.0/5.5 authored, anchored to TS-6's real distribution stated in comments; `weight_fraction`s transcribe TS-6 baseline grades (LITERATURE-derived), prices are 0 |
| [study_area.geojson](data/aoi/study_area.geojson) | **AUTHORED** | Self-marked `placeholder: true`; `$comment` calls the box "ILLUSTRATIVE"; excludes 100% of the corpus |
| [exclusions.geojson](data/aoi/exclusions.geojson) | **AUTHORED** | "Starts EMPTY on purpose"; zero features — structure only |
| [ts6_reference.yaml](data/ts6/ts6_reference.yaml) | **MIXED: LITERATURE + AUTHORED + declared-null** | TS-6 title/URL/caveats citing TS-6 sections (LITERATURE); comparison defaults authored; the five digitization fields null awaiting Track G; `raster:` points at a file that does not yet exist |
| [bathymetry/README.md](data/bathymetry/README.md) | **AUTHORED** (prose, no data values) | Documents the reserved directory and the synthetic stand-in arrangement |
| [fixtures/native/synthetic_{boxcore,cover,grid}_native.csv](data/fixtures/native) | **AUTHORED** — *not* SYNTHETIC despite the names | Hand-typed fabricated values (cruise `SYN01`, round coordinates); no generator and no seed exist in the repo, so they fail the taxonomy's SYNTHETIC requirements |
| `data/.DS_Store` | Not value-bearing (Finder metadata) — excluded | — |

**`docs/contracts/`**

| File | Origin | Evidence |
|---|---|---|
| [master_observations.schema.json](docs/contracts/master_observations.schema.json) | **AUTHORED** | Contract document; bounds are authored plausibility limits, the 100 kg/m² ceiling's physics rationale recorded in the README |
| [covariates.yaml](docs/contracts/covariates.yaml) | **MIXED: AUTHORED + LITERATURE** | Structure, windows (1400/460/2300 m), enabled flags authored; `ts6_finding` strings and the 4,100–4,200 m `geology_note` cite TS-6 findings (LITERATURE, no table/page refs) |
| [README.md](docs/contracts/README.md) | **AUTHORED** | Contract-status document; contains two uncited literature-shaped claims (§4) |
| [PROVENANCE.md](docs/contracts/PROVENANCE.md) | **AUTHORED** | Architecture decision record |

**`tests/fixtures/`**

| File | Origin | Evidence |
|---|---|---|
| [rasters.py](tests/fixtures/rasters.py) | **SYNTHETIC generator** — the only artifact family meeting the strict definition | Deterministic recipes, `np.random.default_rng(seed=0)` and `seed=1`, import path `tests.fixtures.rasters`; extent comment says "seeded, reproducible… never to be mistaken for real bathymetry" |
| [adapters.py](tests/fixtures/adapters.py), [normalizers.py](tests/fixtures/normalizers.py), [sample_source.py](tests/fixtures/sample_source.py) | **AUTHORED** test doubles | Hand-written; constants like `SYNTHETIC_MEAN_NODULE_MASS_G = 12.5` are authored picks, "synthetic" in name only |
| [samples/README.md](tests/fixtures/samples/README.md) | **AUTHORED** | And contradicted by the fourth file it doesn't list — §5 |
| [samples/pangaea_boxcore_sample.csv](tests/fixtures/samples/pangaea_boxcore_sample.csv), [dryad_chamber_sample.csv](tests/fixtures/samples/dryad_chamber_sample.csv), [regional_grid_sample.csv](tests/fixtures/samples/regional_grid_sample.csv) | **AUTHORED** | README: "hand-built… Not real downloaded data (no real coordinates/values)" |
| [samples/so268_nodules_sample.csv](tests/fixtures/samples/so268_nodules_sample.csv) | **MEASURED (verbatim excerpt)** | Its own header: rows "taken as-is" from four named events of the real PANGAEA.904962 file, CC BY-NC 4.0. The *selection* is authored; the values are measured |

---

## 4. CANNOT CLASSIFY

No whole file in scope has an undeterminable origin — every one resolves from in-repo evidence. Two evidence gaps fall short of the taxonomy's *requirements* without changing the labels, stated rather than guessed:

1. **Author identity for every AUTHORED artifact.** The taxonomy requires `author: model or a named person`. The repo records committers (git: karlMoreno), but nowhere records whether a person or a model drafted any given value — not for the native CSVs, the sample CSVs, the AOI box coordinates, the scenario cutoffs, or the contract bounds. The AUTHORED label is determinable; its required evidence field is reconstructible from nothing currently in the repo.
2. **Uncited literature-shaped numbers inside classifiable files:** the contracts README's "published CCZ abundances run ~1.5–30 kg/m²" and "~2 g/cm³ wet bulk density" (:29–31, no citation); the per-class `quality_grade_default`s in normalization.yaml (authored policy, rationale unrecorded). These are value-level, not file-level, gaps — LITERATURE-if-cited, AUTHORED-as-written.

---

## 5. CONTRADICTIONS

Your predicted one is confirmed, and it is not the only one. Ordered by how much they matter:

1. **[covariates.yaml](docs/contracts/covariates.yaml) window defaults — confirmed.** `default_window_m: 1400` (:57) and the per-recipe `params` (:89, :107, :113) read as settled, versioned physical parameters. Their actual origin chain: 1400 m "preserves what v2's cell counts meant on real GEBCO 15-arc-sec" (:33–35) — and v2's 3-cell choice has no recorded origin at all. The `[GEOLOGY — ISAAC]` tag at :54–56 admits the real scale question is open, but it sits in a comment; the machine-readable params block carries no marker distinguishing geology-confirmed from engineering-stand-in. The contradiction is between the file's two halves.

2. **[tests/fixtures/samples/README.md](tests/fixtures/samples/README.md) vs [so268_nodules_sample.csv](tests/fixtures/samples/so268_nodules_sample.csv).** The README claims, for the whole directory, "Not real downloaded data (no real coordinates/values)" and lists only three of the four files. The fourth file's own header states it is a verbatim excerpt of the real, CC BY-NC-licensed PANGAEA.904962 data — real coordinates, real values. The README's blanket claim is false, and a licensed real-data excerpt sits in a directory documented as containing none.

3. **[plot_stack.py:64–66](engine/prospectivity/features/plot_stack.py:64) — the watermark is a constant, not a classification.** The suptitle asserts "SYNTHETIC DEM (seeded noise…)" unconditionally; nothing consults the DEM's origin. Correct for every caller today; at Checkpoint 1 the same function run on real GEBCO stamps real output SYNTHETIC — the mirror image of the error the watermark exists to prevent. A mechanism that claims to express origin but expresses a string.

4. **`_backed_by()` / `_require_production_path()` vs [data/fixtures/native/](data/fixtures/native).** Both guards define "fixture" as a path containing both `tests` and `fixtures` ([corpus_builder.py:95](engine/prospectivity/ingestion/corpus_builder.py:95), [corpus_manifest.py:282](engine/prospectivity/provenance/corpus_manifest.py:282)). The three fabricated CSVs under `data/fixtures/native/` contain `fixtures` but not `tests`: they would **pass** the production-path guard and book as `backed_by: "real_data"`. Latent, not live — nothing wires them into `REAL_ADAPTER_BUILDERS`, and conftest uses them without manifests — but it is exactly the `[06]` failure shape, and `_backed_by`'s docstring promise ("a reader can verify… rather than trust") does not hold for this directory. The "fixture" branch also has zero test assertions anywhere.

5. **Minor:** [ci.yml:3–6](.github/workflows/ci.yml:3) describes CI as running "on the synthetic sources in data/fixtures/native/"; the suite has since also built the real corpus from `data/sources/*.tab` on every push. The comment self-qualifies ("later phases… grow this workflow") but understates what CI now exercises. SESSION_STATE.md is stale (44 tests, Phase-0-era) but self-dates, so it misleads only a reader who skips its second line. *(RESOLVED at P2.CLOSE, 2026-08-20: Karl's answer was DELETE. The file is gone — `git show 58aced6` for archaeology — so this row's link is flattened to plain text rather than left dangling. The link was one of only two inbound references in the repo, which is what made deletion the cheap option.)*

---

## 6. HASH IMPACT

Files whose SHA-256 is recorded in [data/corpus/manifest.json](data/corpus/manifest.json) — these **must not** be edited to carry a marker:

| File | Recorded where | Alternative location for an origin marker |
|---|---|---|
| [SO268-bc-nodules-summary-PANGAEA-904967.tab](data/sources/SO268-bc-nodules-summary-PANGAEA-904967.tab) | `sources[0].input_content_hash` ([manifest.json:55](data/corpus/manifest.json:55)) | Its entry in [source_queue.yaml](data/sources/source_queue.yaml) (already the metadata home: license, accessed_date, the null `content_hash` slot), and/or the manifest's per-source block via the recorder — which is where `backed_by` already lives. Doubly forbidden regardless of hashes: it is verbatim published data, and editing it falsifies the MEASURED evidence itself |
| [SO268-bc-nodules-PANGAEA-904962.tab](data/sources/SO268-bc-nodules-PANGAEA-904962.tab) | `sources[1].input_content_hash` (:82) | Same as above |
| [study_area.geojson](data/aoi/study_area.geojson) | `contract_versions.study_area_content_hash` (:20) | It already self-marks (`placeholder: true` — the hash *covers* that marker). Further origin metadata belongs in the recorder-written `study_area_containment.note` or the contracts README row. If the AOI is ever deliberately replaced, the hash changing is the mechanism working — the rule is no marker-only edits |
| [manifest.json](data/corpus/manifest.json) itself | self-hash `content_hash` (:15), excluding itself + `generated_at` | Never hand-edited under any circumstances — it is generated. New origin fields enter through `CorpusManifest`/`ProvenanceRecorder` code and a rebuild, as a deliberate, versioned change to the manifest shape |

Two adjacent facts worth having before designing the taxonomy's placement:

- **[master_observations.csv](data/corpus/master_observations.csv) is *not* hash-pinned by the manifest.** The manifest records `corpus_path`, counts, and its own substance-hash — no field hashes the CSV's bytes. A hand-edit to the CSV would break no recorded hash today (only a rebuild's full-state idempotency comparison would surface drift). It must not be hand-edited anyway — it is a generated artifact, so any per-row origin marker arrives as a schema column (schema-version bump) through the pipeline — but note that the hash chain does not currently anchor the corpus bytes themselves.
- Downstream, the feature stack records `upstream_hashes: {"dem": …}` and `DemGrid` verifies reported DEM hashes against bytes read, so a marker inside any raster changes its identity. That is already solved correctly: origin belongs in `TerrainLayer.name`/provenance, "never by faking a hash" — the E1.5 rule, and the pattern the taxonomy generalizes.

Report ends here. Nothing was implemented, no field added, no file touched.
