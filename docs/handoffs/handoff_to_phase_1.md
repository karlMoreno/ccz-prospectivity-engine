# HANDOFF — CCZ Prospectivity Engine (planning/strategy thread)

Paste this into a new chat to bring it up to speed. This is the **planning/strategy**
companion to the coding work (which happens separately in Claude Code on my machine).

---

## Who I am / what this is

I'm the **software engineer** on a two-person student project. My teammate **Isaac** is
a **geology undergrad**. We're building the **CCZ Prospectivity Engine**: an open,
reproducible modernization of **ISA Technical Study No. 6 (2010)** that predicts
polymetallic-nodule **abundance (kg/m²)** across a Clarion-Clipperton Zone (CCZ) study
area from an openly-sourced sample corpus + terrain covariates — with honest
uncertainty, an economic minability layer, a provenance manifest, and a benchmark
comparison against the TS-6 2010 surface. It's for portfolio + grant/consulting
credibility, not a SaaS. Long-term it's designed to port to the lunar south pole (swap
the DEM + samples).

I'm **new to ML.** Explain ML concepts when they come up. I own the engineering and the
domain framing; I'm learning the data-science vocabulary as I go.

## My standing preferences (please follow)

- Use **design patterns** and explain in comments **which pattern does what and why**.
- Use **ASCII UML / box diagrams** when explaining architecture or flow.
- Stop at phase boundaries for my review; I want to understand every piece (I have to
  defend this to grant reviewers). Prefer small reviewable steps.
- Never fabricate values; use clearly-labeled placeholders.

## The core design idea (why the project is shaped the way it is)

**Two-track concurrent build, decoupled by seven frozen "contracts":**
- **Track E** (me, engineer) builds the whole pipeline against SYNTHETIC fixtures.
- **Track G** (Isaac, geologist) produces the real data + science parameters.
- They only meet at **integration checkpoints** where a fixture is swapped for a real
  file. Neither waits on the other. The contracts are the frozen "shape of the handoff."

**The seven contracts** (in `phase0-contracts-v3/`, now in the repo):
1. `master_observations` (schema + CSV) — the evidence-typed data corpus
2. `study_area.geojson` (+ exclusions) — the AOI geometry
3. `covariates.yaml` — terrain features (Option A now; TS-6-proven proxies = Option B later)
4. `scenarios.yaml` — economic cutoffs (market vs strategic)
5. `source_queue.yaml` — the Path C **Phase A** download queue (the ~10 open sources)
6. `ts6_reference.yaml` — the digitized TS-6 2010 surface (benchmark)
7. `normalization.yaml` — per-evidence-class → kg/m² policy

## The single most important scientific idea: evidence classes

Open "nodule data" is not one thing. Every observation is tagged exactly one of:
- **MASS** (kg/m²) — the **only** class the model trains on
- **COUNT** (nodules/m²) — covariate; → kg/m² only via a recorded mean nodule mass
- **COVER** (% from seafloor images) — covariate; **NEVER** silently converted to kg/m²
- **GRID** (compiled/interpolated, e.g. TS-6) — prior/benchmark, **never** a training station
- **GRADE** (Mn/Ni/Cu/Co %) — joins to abundance stations; feeds economics

Conflating these poisons the model. The "COVER never becomes kg/m²" rule is the one that
matters most and is enforced in code (a Pydantic model rejects it).

## Key decisions already made (don't relitigate unless I ask)

- **DeepData's abundance/grade layer is CONFIDENTIAL** and has no public API. So it is
  NOT the sample source — it's only good for public context layers (APEI/contract
  polygons). Confirmed the "TMC decade of data" was *environmental*, not resource data.
- **Path C** = assemble abundance from open published sources (PANGAEA, DOMES, NOAA,
  contractor papers). Scoped to **Phase A** (the one-day numeric/derivable download queue)
  for the alpha. Phase B (PDF extraction) and Phase C (targeted requests) come later.
- **Spatial cross-validation is mandatory** — random k-fold leaks on spatially
  autocorrelated data and gives fake-good scores. This is the project's most defensible
  point. Always run a mean baseline alongside. Uncertainty is always paired with predictions.
- **Bathymetry = public GEBCO-class**, never DeepData's confidential processed bathy.
- **Ordinary kriging** is the TS-6-parity method; random forest is the ML baseline.
- **Postgres/PostGIS is deliberately parked** until Phase 5 (the read-only API/viewer).
  The alpha runs on files: CSV corpus + GeoTIFF rasters + JSON manifest. This is
  intentional for reproducibility.
- **v-next direction:** lead with ML + calibrated uncertainty + "where should you sample
  next" (active sampling) — framed as *decision-grade prediction*, NOT "replace surveys."
  The accuracy ceiling is the DATA (sparse, ~hundreds of points), not the model.

## Tools / people context

- Coding happens in **Claude Code** on my machine (separate session). This chat is for
  planning/strategy/learning.
- A friend (**Aymane**, Cogentic — local-first AutoML for tabular data) is a potential
  ML advisor. Verdict: don't integrate his tool into the engine (it does random k-fold by
  default = wrong for spatial data; closed tool breaks reproducibility), but great as an
  independent benchmark and for ML advice.
- Considered "ECC / Everything Claude Code" bulk agent harness — decided AGAINST (solves
  a problem I don't have; adds surface area to a project whose whole virtue is minimalism).

## Where the build actually is right now

- **Phase 0 (scaffold): DONE** — package layout, the 7 interfaces as abstract base classes,
  Pydantic `Observation` model mirroring the schema, synthetic fixtures, CI green.
- **Phase 1, task E1.1: DONE** — real `SourceAdapter`s for the three Phase-A source
  families (PangaeaAdapter via pangaeapy, TabularFileAdapter for Dryad/Mendeley xlsx/csv,
  RegionalGridAdapter for the TS-6/Washburn grids). 44 tests passing.
- **Next up:** E1.2 (AbundanceNormalizer per class), E1.3 (dedup Specification rules +
  build the corpus), E1.4 (terrain feature recipes + plot MASS points over the DEM),
  E1.5 (unit tests). Then **Integration Checkpoint 1**: swap synthetic DEM → Isaac's real
  GEBCO bathymetry.tif; corpus MASS rows become trainable.
- Repo is on GitHub (private for now; goes public at alpha launch). Contracts + code +
  markdown are versioned; big binaries (.tif, .dmg, PDFs) are gitignored.

## What I might ask next

Phase 1 wrap-up guidance, learning ML concepts as they arise, drafting messages to Isaac
or Aymane, the Phase-2 modeling plan (kriging + spatial CV + baseline), or a Phase-5
Postgres/PostGIS setup guide when I get there.

---

*The authoritative specs are in the repo: `CCZ-Prospectivity-Engine-Alpha-Proposal-v3.md`,
`CCZ-Prospectivity-Engine-Proposal-v3.md`, and `phase0-contracts-v3/`. When in doubt,
those + `CLAUDE.md` win over this summary.*
