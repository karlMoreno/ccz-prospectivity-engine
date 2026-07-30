# Phase 1 — Claude Code Prompts (v2)

Revision of the Phase 1 task prompts. **E1.2 is the substantive rewrite** (registry
selection, `mean_nodule_mass_g` guard, flag destination, two new required tests).
E1.3 and E1.5 got one-line consistency additions so they line up with the E1.2
changes. E1.1 and E1.4 are unchanged.

Changes from v1 are marked **[NEW]** so you can diff at a glance.

---

## E1.1 — Real SourceAdapters (Adapter pattern) — *unchanged*

> Start Phase 1, task E1.1 only. Read `source_queue.yaml` and
> `master_observations.schema.json` first and restate the master schema back to me.
> Then implement real `SourceAdapter` subclasses in `engine/prospectivity/ingestion/`
> for the three Phase-A source families: a `PangaeaAdapter` (via pangaeapy), a
> `TabularFileAdapter` (Dryad/Mendeley xlsx/csv via pandas), and a
> `RegionalGridAdapter` ([18]/[19]). Each maps its native columns → the
> master-observation schema and sets `source_id`, `evidence_class`, and provenance
> fields per that source's `source_queue.yaml` entry. Keep the Adapter-pattern
> comment explaining what each does and why. Do NOT normalize or dedup yet —
> adapters only produce raw typed rows. Write one test per adapter against a small
> saved sample of each format. Stop when the three adapters pass their tests so I
> can review.

**Watch for:** adapter boundary stays clean — no kg/m² math (E1.2), no dedup (E1.3).
One source row can legitimately spawn multiple evidence rows (e.g. [01] → MASS +
COUNT + COVER).

---

## E1.2 — AbundanceNormalizer per class (Strategy + Registry) — *revised*

> Task E1.2 only. Read `normalization.yaml` and `master_observations.schema.json`
> first, and restate the five per-class rules AND the screening bounds back to me
> before writing code. **[NEW]** If the screening bounds or any per-class rule is
> missing or ambiguous in `normalization.yaml`, STOP and tell me — do not improvise
> a scientific rule.
>
> Implement `AbundanceNormalizer` strategies in `engine/prospectivity/ingestion/`:
>
> - `MassNormalizer` — already-kg/m² passthrough; else
>   `nodule_mass_kg / sampled_area_m2`, recording `derivation_formula`.
> - `CountNormalizer` — kg/m² only if `mean_nodule_mass_g` is present **on the row
>   or in that source's `source_queue.yaml` entry** **[NEW — confirm which]**;
>   otherwise leave `abundance_kg_m2` blank and keep the row as a covariate. Do NOT
>   substitute a literature default mean nodule mass. **[NEW]**
> - `CoverNormalizer` — NEVER writes `abundance_kg_m2` — hard rule.
> - `GridNormalizer` — keeps the value but forces `observation_or_prediction` to
>   `compiled/interpolated`.
> - `GradeNormalizer` — no kg/m²; just carries the metal fields.
>
> **[NEW]** Select strategies via a `NormalizerRegistry` mapping
> `evidence_class → normalizer instance` — no if/elif chains in the pipeline.
> Comment the Strategy pattern (each class encapsulates one interchangeable
> normalization policy) and the Registry (decouples selection from the pipeline;
> adding a future evidence class is one registration line).
>
> Apply the screening bounds after normalization, flagging out-of-range rows rather
> than dropping them. **[NEW]** Flag by writing the schema's QC/flag field — restate
> that field's name from the schema before using it; if no such field exists in the
> frozen schema, STOP and tell me instead of adding one.
>
> Add tests asserting each rule, and specifically:
> 1. The COVER test — fails if a COVER row ever gets a non-null `abundance_kg_m2`.
> 2. **[NEW]** Registry completeness — every `evidence_class` in the schema has
>    exactly one registered normalizer (fails loudly if a class would pass through
>    unnormalized).
> 3. **[NEW]** CountNormalizer without `mean_nodule_mass_g` yields a blank
>    `abundance_kg_m2` — never a substituted value.
>
> Stop for review.

**Watch for:** the COVER test is still the most important test in the project. The
two STOP conditions are deliberate — a missing bound or missing flag field is a
*contract* question for you, not an engineering call for Claude Code.

**Before running this prompt, verify yourself:**
- [ ] `normalization.yaml` actually contains all five rules AND the screening bounds.
- [ ] You know where `mean_nodule_mass_g` lives (per-row column vs per-source entry
      in `source_queue.yaml`) — edit the bracketed line to say which.
- [ ] The frozen schema has a QC/flag field (find its exact name), or you've decided
      how flagging works before Claude Code has to.

### Target architecture

```
                 +--------------------------+
                 |  AbundanceNormalizer     |  <<Strategy interface>>
                 |  + normalize(obs) -> obs |
                 +------------^-------------+
                              |
      +----------+-----------+-----------+------------+
      |          |           |           |            |
 MassNorm.  CountNorm.  CoverNorm.  GridNorm.   GradeNorm.
                              ^
                              |
                 +------------+-------------+
                 |  NormalizerRegistry      |  <<Registry / Factory>>
                 |  evidence_class -> impl  |
                 +--------------------------+
                              ^
                              | registry[row.evidence_class].normalize(row)
                 +------------+-------------+
                 |  IngestionPipeline (E1.3)|
                 +--------------------------+
```

---

## E1.3 — Dedup + validation → build the corpus (Specification + Template Method)

> Task E1.3 only. Implement the Specification dedup rules from
> `normalization.yaml`'s deduplication section as composable predicates: DOMES
> families deduped by cruise+station+coords+date (not DOI); individual nodules [05]
> nested within box-core EVENTS [01] (the event is the sample); grids [18][19]
> never merged with observed stations; cover never merged with mass. Wire
> `IngestionPipeline.run()` (fetch→adapt→normalize→validate→dedup→append)
> end-to-end so the three real adapters produce one master corpus written to
> `data/corpus/master_observations.csv`. **[NEW]** The normalize step must go
> through the E1.2 `NormalizerRegistry` — no direct strategy instantiation or
> branching in the pipeline. Add tests for each dedup rule. Stop for review.

**Watch for:** the "event is the spatial sample, not the nodule" rule ([05]'s
~9,000 nodules nested in [01]'s box cores) is the subtle one. Have Claude Code
explain its aggregation in a comment and eyeball it.

---

## E1.4 — Terrain features + plot the corpus over the DEM — *unchanged*

> Task E1.4 only. Implement the enabled Option-A recipes in `covariates.yaml`
> (depth, slope, aspect, roughness, profile/plan curvature, TPI, BPI) as
> deterministic, versioned functions in `engine/prospectivity/features/`, each
> recording its `recipe_version`. Run them against the synthetic DEM for now.
> Produce a plot: the covariate stack, plus the corpus [MASS] points overlaid on
> the DEM, saved to `docs/` or an outputs folder. Add tests asserting each recipe
> is deterministic (same input → same output). Stop for review.

**Watch for:** still runs on the synthetic DEM; the real GEBCO tif swaps in at
Checkpoint 1. Fully doable before Isaac finishes G1.1.

---

## E1.5 — Unit tests (the safety net) — *one addition*

> Task E1.5. Audit our Phase 1 tests and fill gaps so we explicitly cover:
> (1) evidence-class tagging — every ingested row gets exactly one correct class;
> (2) normalization correctness per class — including the hard rules that COVER
> never yields kg/m² and GRID is never observed, **[NEW]** plus registry
> completeness (every schema evidence class → exactly one normalizer);
> (3) dedup rules — DOMES families, nodules-nested-in-events, grids-never-merged.
> Show me the final test count and what each guards. Confirm CI is green. This
> completes Phase 1 Track E — stop for my review before Checkpoint 1.

---

## Pattern summary for Phase 1 (grant-defense cheat sheet)

> **Moved.** The authoritative version is **[`docs/PATTERNS.md`](../PATTERNS.md)**
> (E1.5, 2026-07-29). It supersedes the table that used to sit here: it is
> written from the code with `file:line` citations, covers the patterns added
> after this planning note was written (Observer, Layer Supertype, Null Object,
> the feature-recipe Strategy and Registry), names the test that depends on each
> structure, and adds a **reverse audit** of indirection that is *not* earning
> its keep. Keeping a second copy here would guarantee they drift.
>
> One correction worth carrying over, since this note's wording was wrong:
> Specification was justified above as "composable, named predicates." The
> *named predicate* half held; the **composable half did not** — the shipped
> dedup logic has one production Specification and zero composition sites, and
> `PATTERNS.md` §3.1 recommends deleting the unused combinators. Defending
> "composable" to a reviewer would not survive a look at the code.
