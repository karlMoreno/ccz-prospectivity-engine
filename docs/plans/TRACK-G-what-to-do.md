# TRACK G — WHAT YOU ACTUALLY DO

Track G is three kinds of work and nothing else:

- **Downloading** — files from public portals. Mechanical. Evenings.
- **Recording** — what each file is: units, area sampled, wet or dry, licence,
  where you got it, when. Mechanical, but only you can do it because it comes
  off the source documents.
- **Deciding** — the geology calls. A handful, but they're the ones that
  matter, and nobody else can make them.

Everything else — the taxonomy, the audit, the hashing, the guards — is
Track E's, and Track E is finished. When you hand a file over, the pipeline
knows what to do with it.

---

## Already done

- **[01] SO268** — downloaded, parsed, 108 rows in the corpus. This is your
  template for what "done" looks like for a source.
- **SO268's sampled area** (0.25 m² box core → ×4 to reach kg/m²) recorded
  in `normalization.yaml`.
- Synthetic stand-ins for everything else, so the pipeline runs today.

## Not done — the honest list

This is the Phase 0 Track G lane, unchanged, with what's missing:

| | Task | State |
|---|---|---|
| G0.1 | Read TS-6 → `docs/geology/` | not started |
| G0.2 | Download the queue: [02]–[06], [11], [12], [14], [18], [19] | only [01] done |
| G0.3 | Record sampled area + wet/dry basis per source | SO268's area only; **wet/dry empty everywhere** |
| G0.4 | Pick the study area, draft `study_area.geojson` | placeholder only — all 108 rows fall *outside* it |
| G0.5 | Pull the boundary polygons; pick the GEBCO grid | not started |
| G0.6 | QA rules → `docs/geology/qa_rules.md` | not started |

---

## The order, and what "done" means for each

### 1. Download the map data (an evening)

**GEBCO bathymetry.** Get the 15-arc-second global grid, or a regional
subset covering the whole CCZ box (roughly 0°–23.5°N, 160°–111°W). **Grab
the TID grid in the same session** — it's a separate download that tells you
which cells are real soundings and which are altimetry guesses. You will
want them matched, and going back for it later is annoying.

Don't cut it to a small extent yet. That comes after step 2.

**The CCZ boundary.** Marine Regions, entry MRGID 64222, layer
`MarineRegions:isa_ccz_managementarea`. CC-BY 4.0, downloadable as shapefile
or GeoJSON.

**Contract areas and APEIs.** ISA's shapefiles at
`isa.org.jm/exploration-contracts/maps/`. Note: these carry ISA copyright,
not CC-BY — read the terms before planning to commit them to a public repo.

> **Done when:** the files are on disk with a note beside each one saying the
> URL, the date you downloaded it, and the licence.

### 2. Pick the study area (an hour, and it's a real decision)

You know where your data is: two clusters about 991 km apart. The question
is what area the model is allowed to predict over.

The tension, already measured: 99% of your current domain sits beyond one
variogram range of any station. **A study area much larger than your data is
a choice to publish mostly-mean cells** — a big map that says almost nothing
almost everywhere.

Three options: the sampled areas only (small, honest, unimpressive); the
full CCZ (impressive, mostly empty); or something between that includes the
gap you'd like to sample next.

> **Done when:** `study_area.geojson` holds a real polygon and you can say in
> one sentence why that boundary and not a different one.

Then cut your GEBCO subset to it.

### 3. Download the source queue (a few evenings)

The remaining Phase-A sources: **[02][03]** DOMES, **[04][05]** derived,
**[06]** Dryad, **[11][12][14]** cover/count, **[18]** TS-6, **[19]**
Washburn.

For each one, as you download it, write down four things — they're trivial
now and painful to reconstruct later:

- the URL and the date
- the licence (this decides whether the file can live in a public repo)
- **what one row means** — a station? an event? an individual nodule?
- **the area sampled** — this is what turns a mass into kg/m²

> **Done when:** each file is on disk with those four facts written next to it.

### 4. Read TS-6 (a day)

The 2010 ISA Technical Study No. 6. You're pulling out four things into
`docs/geology/`:

- which covariates it treats as proven predictors of nodule abundance
- what data it was built from
- what thresholds it uses (abundance cutoffs, viability)
- what biases it carries — where its coverage is thin, what it assumed

This is the document your project claims to modernize, so knowing it well is
worth a day. It also tells you what the digitized surface (step 6) actually
depicts.

### 5. Record units and basis per source (follows from step 3)

For each source, into `normalization.yaml`:

- **sampled area in m²** — how the raw number becomes kg/m²
- **wet or dry** — and this one matters more than it looks

Wet/dry is currently empty on all 108 existing rows. Nodules hold a lot of
water; wet and dry masses differ substantially. If you mix bases you get a
number that means nothing, and the config file already says "record it, do
not silently mix." **`unknown` is an honest answer** when a source doesn't
say. A guess is not.

### 6. Digitize the TS-6 abundance surface (the labor item)

Take the printed abundance map from TS-6 and turn it into a raster.

Write down, as you go, enough that someone else could redo it: which figure,
which edition, how you georeferenced it, how you read values off it (contour
tracing? colour matching?). And **digitize a sample of cells twice** — the
spread between your two passes *is* your digitization uncertainty, and the
pipeline requires that number before it will treat the comparison as real.

### 7. Write the QA rules (an afternoon, after steps 3–5)

`docs/geology/qa_rules.md` — what makes a row untrustworthy. You'll know by
then: implausible values, positions too imprecise to place, samplers that
don't compare, sources that don't state a basis.

### 8. Real economic numbers (later)

Two scenarios with real cutoffs and real metal prices, each with a citation
and a date. One constraint worth knowing now: the two current placeholder
cutoffs both sit below your training mean, so every cell is "minable" under
both and the two scenarios are identical maps. Real cutoffs should be able to
*disagree* somewhere — and if honest ones still don't, that's a finding about
CCZ grade worth stating plainly.

---

## The geology decisions, collected

These are the only ones that need you specifically:

1. **The study area** (step 2) — how big, and why.
2. **Do the DOMES rows train the model, or only inform it?** 1970s free-fall
   grabs recover nodules differently than box cores. If they're not
   comparable, "context only" is an honest answer.
3. **The burial question.** Six SO268 leg-2 events disagree with the
   published buried counts — five under-record, two record zero sediment
   depth for every nodule, all fifteen leg-1 events reconcile exactly. Looks
   like a per-leg recording difference. It decides whether "abundance" means
   surface nodules or all nodules, and at the worst event that's an 11×
   difference in mass.
4. **Wet or dry, per source** (step 5).
5. **How close is close enough** for a grade sample to describe a station
   (step 3's [19]).
6. **Real economic cutoffs** (step 8).

---

## The one rule not to break

**Write down what would count as success before you run the model on real
data.** One or two sentences — "the model earns a claim if it beats the mean
baseline by X on the within-site test" — committed before the first real run.

It takes five minutes and it's the one thing you can't fix afterwards: once
you've seen the scores, any threshold you set is a threshold you chose
knowing the answer, and that's worth much less. Everything else on this list
can be redone in any order.
