# HANDOFF — CCZ Prospectivity Engine (planning/strategy thread, Phase 2)

Paste into a new chat to bring it up to speed. This is the **planning/strategy**
companion to the coding work, which happens separately in Claude Code on my machine.
Supersedes `handoff_to_phase_1.md`.

---

## Who I am / what this is

I'm the **software engineer** on a two-person student project. My teammate **Isaac** is a
**geology undergrad**. We're building the **CCZ Prospectivity Engine**: an open,
reproducible modernization of **ISA Technical Study No. 6 (2010)** that predicts
polymetallic-nodule **abundance (kg/m²)** across a Clarion-Clipperton Zone study area
from an openly-sourced sample corpus plus terrain covariates — with honest uncertainty,
an economic minability layer, a provenance manifest, and a benchmark against the TS-6
2010 surface. It's for portfolio and grant/consulting credibility, not a SaaS. Long-term
it's designed to port to the lunar south pole by swapping the DEM and the samples.

I'm **new to ML.** Explain ML concepts when they come up. I own the engineering and the
domain framing; I'm learning the data-science vocabulary as I go.

## My standing preferences

- Use **design patterns** and explain in comments **which pattern does what and why**.
- Use **ASCII UML / box diagrams** when explaining architecture or flow.
- **Stop at task boundaries for my review.** I have to defend this to grant reviewers, so
  I want to understand every piece. Prefer small reviewable steps.
- **Never fabricate values.** Clearly-labelled placeholders only.
- When something is a *scientific* decision rather than an engineering one, surface it as
  a decision for me — don't pick for me.

---

## Where the build actually is

**Phase 1 Track E is COMPLETE.** As of my last confirmed report: **202 tests (200 pass,
2 deliberate skips)**. The repo is authoritative if these numbers have drifted.

```
Corpus:  108 rows = 36 box-core events × 3 evidence classes (36 MASS / 36 COUNT / 36 COVER)
         35 training-eligible  (1 excluded: SO268/1_12-2, a failed box core, flagged)
         2 contributing sources, both real, both CC BY-NC 4.0
         0 fabricated values
Contracts: schema v4 · covariates registry v3 · normalization policy v1
```

**The two sources:**
- `[01]` **PANGAEA.904967** — SO268 box-core summary. Authoritative for mass and count.
  Abundance 11.6–26.8 kg/m², mean ~19.4 (consistent with published BGR/GSR figures).
- `[05]` **PANGAEA.904962** — 1,658 individual nodules aggregated to the same 36 events.
  **Fully absorbed** by dedup: it contributes `mean_nodule_mass_g` and provenance but
  appears under no `source_id` of its own in the corpus.

They cross-validate against each other: counts match exactly on 31 of 36 events, masses
agree within 0.285 kg. The 5 residuals are documented, not smoothed over.

**Deliberately unwired:** `[06]` Dryad chamber and `[18]` TS-6 grid were removed because
their fixtures were fabricated; a path guard blocks re-wiring until real files exist.
`[19]` Washburn never wired. So the corpus is single-source until Track G delivers.

---

## The single most important fact about our data

**35 stations in two clusters ~12 km across, ~991 km apart.** Of 595 station pairs:
301 are under 13 km, 294 are near 991 km, and **zero fall between ~13 km and ~986 km.**

This is not a footnote — it constrains the method:

- A **variogram** can only be estimated where pairs exist, so there is no empirical
  support across exactly the range we'd want to predict over. Any curve through that gap
  is an assumption.
- **Honest spatial CV** reduces to leave-one-cluster-out: two folds, each predicting
  ~991 km away. That's extrapolation, not interpolation.
- The likely honest finding is that kriging and RF **do not beat a mean baseline** on
  this geometry. If so, that's a finding about the data and it's publishable — not
  something to tune away.
- Practical consequence for Track G: **geographic spread beats row count.** Twenty
  stations *between* the clusters are worth more than a hundred inside them.

Also: **all 108 rows fall outside** the Phase-0 placeholder study area. The AOI is an
open decision.

---

## Core design ideas (don't relitigate unless I ask)

**Two-track concurrent build, decoupled by seven frozen contracts.** Track E (me) builds
the whole pipeline against synthetic fixtures; Track G (Isaac) produces real data and
science parameters. We meet only at integration checkpoints where a fixture is swapped
for a real file. Neither waits on the other.

**Five evidence classes, never conflated.** Every observation carries exactly one:
- **MASS** (kg/m²) — the **only** class the model trains on
- **COUNT** (nodules/m²) — → kg/m² only via a recorded mean nodule mass
- **COVER** (% from imagery) — **NEVER** becomes kg/m²; hard rule, mutation-tested guard
- **GRID** (compiled/interpolated) — prior or benchmark, never a training station
- **GRADE** (Mn/Ni/Cu/Co %) — joins to stations, feeds economics, never abundance

Out-of-range values are **flagged, never dropped**, and `qa_status` now genuinely gates
training eligibility (it didn't until we caught that in an audit).

**Other settled decisions:** DeepData's abundance/grade layer is confidential, so the
corpus comes entirely from open published sources. Bathymetry is public GEBCO-class.
Ordinary kriging is the TS-6-parity method; random forest is the ML baseline; a mean
baseline runs alongside every claim. Random k-fold is disqualified — it leaks on
spatially autocorrelated data. Postgres/PostGIS stays parked until Phase 5; the alpha
runs on files.

---

## Where Phase 2 is going

Lane: `E2.0` training matrix → `E2.1` estimator interface + mean baseline → `E2.2`
ordinary kriging → `E2.3` random forest → `E2.4` spatially-blocked CV → `E2.5`
refuse-to-validate guard. Prompts are written (`phase2_prompts.md`).

**Two structural caveats I already know about:**

1. **E2.0 isn't in the original lane list.** Covariate extraction at station locations was
   deferred out of E1.4 into "Phase 2's training matrix," so it has to come first. It
   also absorbs two backlog items (the missing `CorpusCsvSampleSource`, and enforcing the
   DEM-resolution rule).
2. **Phase 2 can be built but not believed yet.** The corpus is real; the covariates
   aren't — every terrain feature is computed on a **synthetic DEM**, so a model trained
   today learns real abundance against noise. Fine for building machinery, but every
   Phase-2 output must be watermarked non-scientific until real GEBCO lands at
   Checkpoint 1.

---

## Blocked on Isaac

- **Buried vs surface abundance as the training target** — blocks E2.0. `[01]`'s
  published mass *includes* buried nodules (mean ~12% of an event's count, max ~73%),
  which surface collectors can't recover. This is the definition of `y`.
- **AOI scope** — blocks prediction surfaces.
- **Real GEBCO bathymetry** — Checkpoint 1; blocks any scientific claim from Phase 2.
- **G2.1 validation metrics + acceptance thresholds** — specifically *what counts as
  credible uplift over a mean baseline*. Without that number, Checkpoint 2 has no gate.
- **G2.2 plausible spatial range** (advisory prior — the only information available about
  the medium range, given our support gap).
- **G2.3 real economic parameters** — `scenarios.yaml` is entirely `illustrative_only`.

---

## Working practices that have earned their place

These came out of Phase 1 the hard way; they're worth preserving:

- **Restate the contract before coding**, and **STOP on ambiguity** rather than improvise.
  This caught the `qa_status` field question, a schema bound conflict, and the COUNT
  mean-mass ambiguity before any code was written.
- **Mutation-verify guards.** Break it, watch the test go red, revert. A guard that has
  never been seen to fail is not known to work.
- **Registry + completeness tests** so adding a class can't be silently forgotten.
- **Watch for "coverage that isn't."** Three separate audits found tests that counted as
  coverage while guarding nothing — a test asserting a rule while loading data through the
  class that *enforces* that rule can never observe a violation; an "unchanged" assertion
  comparing two fields out of thirty misses the other twenty-eight.
- **Property tests beat value tests.** The order-independence test caught two distinct
  bugs; the cross-dataset reconciliation against independently published data is external
  validation no fixture can provide.
- **Silent failure is the dangerous class.** Prefer a loud raise over a quiet no-op.
- **Commit after every task** (we once had 25 files of reviewed work uncommitted).

---

## What I might ask next

Phase 2 task guidance and review; ML concepts as they arise (variograms, spatial CV,
uncertainty calibration); drafting messages to Isaac; the Phase 3 prediction-surface
plan; or a Phase 5 Postgres/PostGIS setup guide when I get there.

---

*Authoritative sources in the repo, which win over this summary: `CLAUDE.md`,
`docs/BACKLOG.md`, `docs/PATTERNS.md`, `docs/walkthroughs/`, `data/corpus/manifest.json`,
and the contracts under `docs/contracts/` + `data/`.*
