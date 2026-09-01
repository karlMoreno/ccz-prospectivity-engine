# AREA.1 — Closing [14]'s area basis: one half closed by recomputation, one half stopped

**2026-09-01 · one commit · suite 709 → 709 (no code touched)**

The task was to close [14]'s area basis. Half of it closed cleanly and the other
half hit the contract's own STOP condition: **the R script does not determine which
denominator `area_percent` was computed against, and neither does the arithmetic.**
Two other things came out of the same reading — the dataset is not what the index
said it was, and the disturbed/undisturbed filter is now a one-line rule.

```
  THE THREE AREA COLUMNS                     WHAT SETTLED, AND HOW
  ─────────────────────────────────────────────────────────────────────
  image_area_m2   raw frame     mean 4.447 ─┐
  Export_Area     analysed      mean 2.513 ─┤  densities: Export_Area
  area_percent    nodule cover  mean 13.75 ─┘  239/239 exact, 1.8e-15
                                                        │
                       area_percent's denominator ──────┴──> STOP
                       script silent · workbook has 0 formulas ·
                       numerator unpublished · the two candidates
                       differ by a CONSTANT 0.5650, so no internal
                       check can ever separate them
```

## 0. Scope

[14] was **not ingested**. Nothing was written to the corpus. The three deposited
files were read where they sit:

```
~/CCZ/downloads/cover-count/Data supporting Asymmetric recovery of benthic meg/
    Megafauna_density_and_nodule_coverage_[14].xlsx
    Metadata_[14].docx
    Statistical_Analysis_and_Plotting_Scripts_[14].R
```

## 1. Step 1 — the R script does not determine it. STOP.

The contract said: *"If the script does not determine it, STOP and report rather
than inferring."* It does not, and the evidence is negative rather than partial:

- **`area_percent` is never assigned anywhere in the 990-line script.**
  `grep -E "area_percent *(<-|=[^=])"` returns **nothing**. All 13 occurrences are
  reads — a plot aesthetic, `max()`, `cor.test()`, `lm()`, `mean()`,
  `complete.cases()`. Line 714's `Area_percent = mean(area_percent, ...)` is an
  aggregation of the finished column, not its definition.
- **The script never mentions either candidate.** `Export_Area` and
  `image_area_m2` appear **zero times** in it.
- **The only line that touches the column's origin is the read** (line 46):

  > `image_data <- read_excel("C:/Users/nicol/OneDrive/Bureau/Publications/DSM_Laurenz_AWI/Mendeley/Megafauna_density_and_nodule_coverage.xlsx")`

  There is no computing line to quote, because there is none.
- **The workbook holds no formula either.** All 45 columns × 279 rows are hard
  values; a scan for cells beginning `=` returns **0**.
- **And the deposit says so itself.** `Metadata.docx`, final line:

  > "The deposited dataset corresponds to the final processed dataset used in the
  > study; intermediate data-processing steps performed prior to creation of this
  > dataset are not included in this repository."

**The STOP fired. No denominator was inferred.**

## 2. Step 2 — the arithmetic cannot settle it either, and could not in principle

The contract asked for an independent recomputation from each candidate. It cannot
be run, for a reason worth stating precisely rather than as "we couldn't":

**(a) The numerator is not published.** `area_percent` is a nodule-area fraction,
and no column is that nodule area. Exhaustively: of the 45 columns, **none**
satisfies `c / image_area_m2 × 100 == area_percent`, and **none** satisfies
`c / Export_Area × 100 == area_percent`, at 1e-6. The implied nodule area (e.g.
1.1205 m² under `image_area_m2`, 0.6331 m² under `Export_Area` for row 1) appears
nowhere in the deposit.

**(b) The two candidates are not separable even in principle here.**

```
  Export_Area / image_area_m2  =  0.5650  on ALL 279 rows  (constant: TRUE)
```

The ratio is a single constant, so the two denominators produce `area_percent`
values differing by exactly **×1.7699** everywhere. Any internal-consistency check
would have to anchor the absolute scale — and the only thing that could anchor it,
the nodule area, is the unpublished numerator from (a). **A test with no power was
not manufactured into an answer.**

**So both legs the contract required are absent.** The area basis for
`area_percent` is recorded **OPEN**, not inferred.

**What was suggestive, and why it still decides nothing.** `Metadata.docx`
describes the workbook as containing *"image area used for density and nodule
coverage calculations"* — singular, one area serving both. Since §3 shows the
densities used `Export_Area`, that reading would make `area_percent` per
`Export_Area` too. But the phrase has a second literal reading — the column
actually named `image_area_m2` — and §3 **refutes** that one for density. A
sentence that supports two readings, one of which is already known false, is not
evidence for the other. Recorded as ambiguous; not used to close.

## 3. What DID close — the density columns are per `Export_Area`

Derived by recomputation, not read off a label:

| denominator tested | exact matches | mismatches | max abs diff |
|---|--:|--:|---|
| **`Export_Area`** | **239 / 239** | 0 | **1.8 × 10⁻¹⁵** |
| `image_area_m2` | 0 / 239 | 239 | 2.6 |

(`total_abundance ÷ total_abundance_per_m2`, over the 239 rows with non-zero
abundance.) Every per-m² column in the file — total, mobile, sessile, and all
twelve taxa — is on the `Export_Area` basis.

That fixes the meaning of the two area columns: **`image_area_m2` is the raw frame
footprint** (mean 4.447 m², range 3.259–6.041) and **`Export_Area` is the analysed
sub-area actually annotated** (mean 2.513 m², range 1.841–3.413), a fixed 56.50% of
the frame. Half of the task's question is therefore answered, and it is the half
with a downstream consumer.

## 4. Step 3 — `Zone`, `Distance_from_start`, and the filter rule

**`Zone`** takes exactly three values. Counts derived by counting:

| `Zone` | meaning (the script's own terminology note) | rows | `Distance_from_start` span |
|---|---|--:|---|
| `Outside1` | Zone A — undisturbed, north of the site | **121** | 0.00 – 614.28 m |
| `Inside` | **the Mining Test Site — disturbed** | **69** | 617.98 – 953.72 m |
| `Outside2` | Zone B — undisturbed, south of the site | **89** | 957.93 – 1646.76 m |
| | | **279** | closes against the row count |

The mapping is not inferred from the names; the script states it:

> "In the manuscript, the transect is divided into Zone A, the Mining Test Site,
> and Zone B. For consistency with earlier versions of the analysis, the original
> code labels are retained: Outside1 = Zone A, Inside = Mining Test Site, and
> Outside2 = Zone B."

**`Distance_from_start`** is a geodesic distance in metres from the transect
origin (14.1191226 N, −125.8697643 W, given in the script): **279 distinct values,
0.000 → 1646.757 m, monotone non-decreasing with row order.** The three zones are
contiguous, non-overlapping spans of it, which is why a `Zone` filter and a
distance filter are interchangeable.

> ### The hard filter rule
> **Disturbed seafloor: `Zone == "Inside"` → 69 rows.**
> **Undisturbed seafloor: `Zone != "Inside"` → 210 rows survive.**
> 69 + 210 = 279.

## 5. Step 4 — reconciling the index. One claim wrong, one never made

**The description was wrong, in three places.** Both hunt-index copies and the
`[14]` queue row said the work was to *"separate pre-impact, impact, and
post-impact records."*

**The dataset has no temporal design at all.** Derived from the `Filename` column:

```
  distinct dive prefixes : {'SO295_136': 279}
  distinct capture dates : ['20221203']
```

**All 279 images are one dive, on one day.** There is no pre-impact record, no
post-impact record, and nothing to separate temporally. The separation the dataset
actually supports is **spatial** — the `Zone` column of §4, along a 1.65 km
transect. The paper's finding is *asymmetric* recovery between Zone A and Zone B,
which is a spatial contrast by construction.

**The row count was never claimed, so there was nothing to correct.** No row count
for [14] exists anywhere — not in either index copy, not in the queue row, not in
any walkthrough or plan. **279 is recorded here for the first time**, derived by
counting non-empty rows. Reporting "no discrepancy" is the honest outcome; the
alternative would have been inventing one to match the task's framing.

**Two smaller corrections made at the same time**, both from the deposited files:

- [14] is **not a cover-only table**. It is a **megafauna density** dataset (45
  columns; twelve taxa, mobile/sessile splits, depth, coordinates) that *also*
  carries nodule coverage. The index's `What:` line was thin rather than wrong;
  it now says so.
- The study is now named in the index: **Philbert, Purser, Böhringer & Thomsen,
  "Asymmetric recovery of benthic megafauna after a polymetallic nodule mining
  trial in the Clarion-Clipperton Fracture Zone"**, GSR MiningImpact test site.

**A judgment call, flagged for Karl.** The correction was applied to **both** index
copies, including `Proposals and contract V3/Contracts_v3/CCZ_DATA_SOURCES.md`,
which sits in the directory CLAUDE.md says to treat as frozen. That rule is written
about **the seven contracts** ("bump its `*_version`"); `CCZ_DATA_SOURCES.md` is
neither one of the seven nor versioned — it is a duplicate of the hunt index.
Correcting one copy and leaving a known-false sentence standing in the other is the
drift table's (q) shape exactly, so both were fixed. **Revert the second if you
read the freeze rule more broadly than I did.**

## 6. Is [14] fully characterized? No — and here is the one thing left

**Closed:** what the dataset is; its row count (279); its structure (one row per
image); its spatial zones and their counts; the disturbed/undisturbed filter rule;
the density area basis (`Export_Area`, verified 239/239); the meaning of both area
columns; and the index's description.

**Open — one item:** which denominator `area_percent` was computed against. It has
a BACKLOG entry filed at the moment of deferral.

**How much it costs today: nothing.** [14] is `COVER` / `COVARIATE` and is never
converted to kg/m², so no current consumer touches `area_percent`'s scale. The open
half becomes live the moment `area_percent` is compared against another source's
cover fraction — [11] Amon or [12] APEI-6 — because the two readings differ by
**1.77×**, which is larger than most of the between-site differences such a
comparison would be looking for.

## 7. Limits of AREA.1

- **The STOP was honored where it bound and not beyond it.** No denominator was
  inferred for `area_percent`. Steps 3 and 4 were completed because they are
  independent of step 1's outcome, and step 4 is a correction of records already
  known to be suspect.
- **The `Export_Area` density finding rests on 239 of 279 rows** — the 40 rows with
  zero total abundance carry `0 ÷ 0` and cannot discriminate. That is a property of
  the data, not a sampling choice, and 239 exact matches at 1.8 × 10⁻¹⁵ against 0
  is not a marginal result.
- **`Sediment.coverage` was checked and is not an area column** — it is a
  categorical string ("Faint coverage"), so it is not a candidate denominator and
  not a numerator.
- **Nothing was hashed.** [14] was not ingested, so `content_hash` and
  `accessed_date` stay null and the `[GEOLOGY — ISAAC]` licence question on that
  row is untouched.
- **AREA.1's labels were first written 2026-08-31 and are 2026-09-01.** The
  session banner said the 31st; `git log` and the system clock both said the 1st
  when the commit landed, and the convention takes the date from `git log`.
  Caught by comparing the commit stamp against the labels, and corrected in all
  six places, including both index copies. **This is the second consecutive
  session with this slip** (WET.3 had it too) — the cause is the same each time:
  labels get written early in the session from the banner, and the commit lands
  after local midnight. The cheap fix is to stamp labels from `git log` at commit
  time rather than at writing time.
- **No code changed; the suite is unchanged at 709 passed, 2 skipped.**
