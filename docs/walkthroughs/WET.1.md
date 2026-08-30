# WET.1 — Do [03] and [04] report abundance on the same wet/dry basis? AMBIGUOUS, and why the test had no power

**2026-08-28 · two commits · suite 709 → 709 → 709 (no code touched)**

> **AMENDED 2026-08-28, same day, commit 2.** The verdict is **unchanged and
> ACCEPTED: AMBIGUOUS**. Commit 2 does not revisit it — it *strengthens the
> reason for it*. §9 derives that Table 8's Concentration column is a closed-form
> function of the two columns printed beside it, so the confound §5 identified
> from two dashes is not partial: **Table 8 contains no mass measurement
> anywhere**, and a wet/dry question is **not well-posed against it**. §10 records
> a second, independent defect of the same source: Table 8 has **dropped rows**.
> §5 and §7 are amended in place with pointers; nothing already recorded is
> withdrawn.

The hypothesis was clean and the arithmetic came out where it was supposed to:
the median ratio of [04]-derived to [03]-reported abundance over the 19 shared
box cores is **0.800**, exactly the factor Piper's own Table 9 caption implies.
The verdict is still **AMBIGUOUS**, because the same 0.80 is produced by a
confound this task found inside [03] itself, and the two cannot be separated
from these two documents.

```
  THE PREDICTION                     WHAT THE 19 CORES ACTUALLY DID
  ────────────────────────────────────────────────────────────────────
  [03] Table 9 caption:              median 0.800   <- lands on it
  "lowered by 20% to give a          geomean 0.810
   nodule concentration on a         BUT: min 0.593, max 1.220
   dry-weight and salt-free basis"        spread 2.06x
        │                                      │
        ▼                                      ▼
  dry = 0.80 x wet                   a CONSTANT factor cannot
  so [04]/[03] -> 0.80               produce a 2x spread
        │                                      │
        └──────────────┬───────────────────────┘
                       ▼
        [03]'s Table 9 prints "-" for the box-core WEIGHT of
        cores 11 and 23, yet Table 8 prints values for both.
        Table 8's "Concentration" column is NOT uniformly a
        weighed box-core mass -> a method offset of the same
        size as the effect, riding in the same direction.
```

## 0. Scope, and what this task deliberately did not do

Neither source was ingested; `master_observations` is untouched; no adapter was
written. The two PDFs already on disk
(`~/CCZ/downloads/domes/Sorem_methods.pdf`, `Piper_1979_chapter.pdf`) were read,
two tables were transcribed to plain text **outside the repo** so they stay
inspectable and re-checkable, and the arithmetic ran over those files:

- `~/CCZ/downloads/domes/Sorem1989_Table1_TRANSCRIPTION.txt`
- `~/CCZ/downloads/domes/Piper1979_Table8_TRANSCRIPTION.txt`

Both carry the provenance header, the printed column structure, and an explicit
unreadable-cell count. **Cells that could not be read: 0.** One cell is flagged
LOW CONFIDENCE (the station number `D. 58` on printed p. 455, second digit broken
in the scan); it belongs to the block the join excludes, so no digit was inferred
for any figure that enters the arithmetic.

**Neither PDF's OCR text layer was trusted.** Both tables were read from renders
of the page images (Sorem at 400 dpi, Piper at 600 dpi). For Piper's Table 8 this
was not optional: the text layer drops the Station column entirely for the Site C
block that matters and mis-reads digits throughout — `I.S` for 1.8, `lO'.S` for
10.8, `D. 248` for `D. 24B`, `D. IS` for `D. 18`. None of those strings were used.

## 1. The two contract facts, verified before any arithmetic

**[04]'s sampled area — VERIFIED, unambiguous.** Sorem, printed p. 193
(`Sorem_methods.pdf` page index 8), in prose: *"…it is realized that the area of
seabed represented by each box core is only 0.25 m2."* Corroborated independently
on printed p. 191: the sampler is *"a stainless steel sample box 50 cm square"* —
0.5 m × 0.5 m = 0.25 m². Two statements, same number, no ambiguity. The STOP
condition did not fire, and `source_queue.yaml`'s `[04]` row has been filled from
this (it read `null` with a `[GEOLOGY — ISAAC] confirm` tag).

**[03]'s Table 9 percentage — VERIFIED.** Piper, printed p. 458, Table 9 caption:
*"The average value listed in column 9 was lowered by 20% to give a nodule
concentration on a dry-weight and salt-free basis."*

**The factor, derived here rather than taken from the prompt.** "Lowered by 20%"
means the dry, salt-free value is 80% of the value before the adjustment:

```
    dry_saltfree = (1 - 20/100) x wet_salted = 0.80 x wet_salted
```

So under the hypothesis ([04] dry+salt-free, [03] Table 8 wet+salted) the ratio
**[04]/[03] should sit at 0.80**, and [03]/[04] at 1.25.

## 2. Transcription, and the check that did NOT come back clean

**[04] Table 1 — reconciles almost perfectly, and the paper's own prose confirms
the row set.**

| check | result |
|---|---|
| rows printed | 22 (box cores 6–28; **no row for 26** — the table jumps 25 → 27) |
| box cores carrying data | **21** |
| box cores carrying none | **1** — core 17, printed *"(Core reserved by NOAA-DOMES for biological research)"* |
| footnote-2 *"Recovery probably incomplete"* | cores **14** and **25** |
| size-class **grams** sum to printed Total weight | 20 / 21 rows exactly |
| size-class **counts** sum to printed Total number | 20 / 21 rows exactly |

The two misses are **printed** off-by-ones, confirmed against the page image, not
transcription slips: core 16's classes sum to 3326 against a printed total of
3327; core 21's counts sum to 260 against a printed 261.

The decisive check is external to the table: summing the Total-number column over
the 21 data-bearing cores gives **4113**, and Sorem's prose on p. 193 reads *"The
total number of nodules used from 21 box cores was 4,113."* Row set and count
column, confirmed by the paper against itself.

**[03] Table 8 — rows complete, printed averages do NOT recompute.** Row counts
were confirmed twice: once by reading the images, once mechanically by clustering
the PDF's own word y-positions. Site A 27 rows (14 left block + 13 right),
Site B 34 (17 + 17), Site C 50 (26 + 24). Both methods agree exactly, so no row
was missed.

The printed `Average:` rows are another matter, and this is **reported, not
smoothed over**:

| site | column | printed | recomputed | n |
|---|---|---:|---:|---:|
| A | coverage % | 21 | 21.815 | 27 |
| A | diameter cm | 3.0 | 3.152 | 25 |
| A | conc kg/m² | 4.3 | **4.411** | 27 |
| B | coverage % | 10 | 9.357 | 21 |
| B | diameter cm | 5.2 | **5.194** ✓ | 16 |
| B | conc kg/m² | 5.5 | **5.494** ✓ | 34 |
| C | coverage % | 43 | 44.462 | 39 |
| C | diameter cm | 2.6 | 2.753 | 38 |
| C | conc kg/m² | 9.2 | **9.944** | 50 |

Site B's concentration and diameter recompute exactly. Site A's concentration
would need **n = 28** against 27 printed rows; Site C's would need **n = 54**
against 50. That pattern — every recomputed mean too *high*, each needing a few
more rows — is consistent with the authors having averaged over a larger working
set than they printed, but the documents do not say so and this walkthrough does
not assert it. The printed 9.2 is not a typo: Piper's text on p. 457 repeats it
(*"The average abundance of nodules at Site C is 9.2 kg/m2 (Table 8)"*).

**What this costs the task: nothing.** The join uses per-row values, not the
printed averages, and the per-row values are the ones the row-count check and the
image reads confirm.

## 3. The join key — established BEFORE joining, because the hazard is real

Piper's Table 8 Site C is two station series printed as one block, and the
box-core numbers collide across them. Measured, not assumed: **10** box-core
numbers in the other Site C series also occur in Sorem's Table 1 (6, 7, 8, 9, 10,
11, 12, 19, 21, 27). A join on box-core number alone would double-match all ten —
box core 27, for instance, is both `D. 20` (7.4 kg/m²) and `D. 21` (16.3 kg/m²).

**Which subset is Sorem's cruise and leg. Four independent lines, all from the
two documents:**

1. **The photograph's own shipboard label.** Sorem's Figure 6 (p. 192) is a deck
   photograph of a box core whose label board reads, legibly in the scan:
   `RP-8-OC-76   LEG 9` / `STATION 12   BC 18`. That is documentary evidence
   *in the image*, not just the caption — and Piper's Table 8 has exactly one row
   pairing station 12 with box core 18.
2. **Piper names the cruise.** Printed p. 453: *"At Site C, a 225-km2 area (Fig. 6)
   was surveyed in detail on R/V OCEANOGRAPHER cruise RP-8-0C-76."* Figure 6's own
   caption: *"…box core and camera flight locations for NOAA cruise RP-8-0C-76,
   Site C."* And of the other series, p. 456: *"One box core … taken just to the
   north of this area **on an earlier cruise**"* — Piper himself separates them.
3. **Piper uses the station–boxcore composite ID in his own prose.** *"Box core
   7-12, located in the central part of this channel"* (p. 456); Fig. 5's caption
   names *"box cores 11-16 and 18-24 from Site C"*. Each resolves to a Table 8 row
   in the candidate block and to a Sorem box core.
4. **The mapping is one-to-one, monotone, and its single irregularity is the core
   Sorem says was withdrawn.** Station = BC − 5 for box cores 6…16, and BC − 6 for
   18…28. Exactly one box core sits in the sequence without advancing the station
   count: **17** — the core Sorem's Table 1 records as reserved by NOAA-DOMES for
   biological research.

**And then the set identity, which is the strongest single fact:**

```
  Sorem data-bearing cores (21) : 6 7 8 9 10 11 12 13 14 15 16 18 19 20 21 22 23 24 25 27 28
  Piper candidate block    (19) : 6 7 8 9 10 11 12 13    15 16 18 19 20 21 22 23 24    27 28
  Sorem \ Piper = {14, 25}      = EXACTLY Sorem's two footnote-2 cores
  Piper \ Sorem = {}            (empty)
```

The two box-core sets are **identical** once the two cores Sorem footnotes as
*"Recovery probably incomplete"* are removed. That is not a coincidence a wrong
block could produce.

**Consequence for step 1's flag:** both incomplete-recovery cores are absent from
[03] entirely, so neither ever reaches the join. There is no
with-flagged / without-flagged split to report — the exclusion was made by Piper,
not by this analysis.

## 4. Overlap and the full ratio distribution

**Overlap: 19 box cores** (derived — `|Sorem_data ∩ Piper_block|`).
[04] kg/m² = (Total weight g / 1000) / 0.25 m².

| BC | stn | [04] g | [04] kg/m² | [03] kg/m² | ratio [04]/[03] |
|---:|:----|-------:|-----------:|-----------:|------:|
| 6 | D.1 | 1180 | 4.72 | 5.1 | **0.925** |
| 7 | D.2 | 2059 | 8.24 | 13.9 | **0.593** |
| 8 | D.3 | 431 | 1.72 | 1.8 | **0.958** |
| 9 | D.4 | 1568 | 6.27 | 9.4 | **0.667** |
| 10 | D.5 | 2151 | 8.60 | 11.0 | **0.782** |
| 11 | D.6 | 2976 | 11.90 | 9.6 | **1.240** |
| 12 | D.7 | 2316 | 9.26 | 9.0 | **1.029** |
| 13 | D.8 | 2044 | 8.18 | 6.7 | **1.220** |
| 15 | D.10 | 1563 | 6.25 | 7.5 | **0.834** |
| 16 | D.11 | 3327 | 13.31 | 17.5 | **0.760** |
| 18 | D.12 | 2755 | 11.02 | 10.8 | **1.020** |
| 19 | D.13 | 2460 | 9.84 | 12.3 | **0.800** |
| 20 | D.14 | 3668 | 14.67 | 20.4 | **0.719** |
| 21 | D.15 | 2052 | 8.21 | 13.0 | **0.631** |
| 22 | D.16 | 2226 | 8.90 | 12.8 | **0.696** |
| 23 | D.17 | 3922 | 15.69 | 6.5 | **2.414** |
| 24 | D.18 | 2480 | 9.92 | 11.5 | **0.863** |
| 27 | D.21 | 3870 | 15.48 | 16.3 | **0.950** |
| 28 | D.22 | 2828 | 11.31 | 18.7 | **0.605** |

| set | n | median | geomean | min | max | spread | 95% CI on median |
|---|--:|---:|---:|---:|---:|---:|---|
| all shared cores | 19 | 0.834 | 0.877 | 0.593 (BC 7) | 2.414 (BC 23) | 4.07× | 0.719 – 0.958 |
| minus BC 11, 23 (see §5) | 17 | **0.800** | 0.810 | 0.593 | 1.220 | 2.06× | 0.696 – 0.950 |

14 of 19 ratios fall below 1.0. Both bootstrap intervals **exclude 1.00** and both
**contain 0.80**.

## 5. The verdict — AMBIGUOUS

**What supports the hypothesis.** The central tendency is where the caption says
it should be: median 0.800 on the trimmed set, 0.834 on the full one, geometric
mean 0.810–0.877, and a 95% interval that excludes "same basis" in both cases.
The direction is right too — [04] is the *lower* of the pair, as a dry, salt-free
figure should be.

**What refuses to let that resolve it.** A basis conversion is a *constant*. If
the only difference between the two tables were moisture and salt, every core
would land on 0.80 up to one-decimal rounding. Instead the trimmed set spans
0.593 to 1.220 — a **2.06× spread** around a predicted constant, with **three**
cores above 1.0 (12, 13, 18 — where a dry [04] should be impossible against a wet
[03]); on the full 19 it is five, adding 11 and 23. The dispersion is roughly ten
times the effect being measured.

**And the confound found inside [03] itself, which is the reason this is
AMBIGUOUS rather than FAILS.** Piper's Table 9 breaks Site C concentrations into
a box-core **Weight kg/m²** column and a **Photo kg/m²** column. For box cores
**11 and 23 that Weight column is a printed dash** — [03] records *no*
weight-derived concentration for them — yet Table 8 prints 9.6 and 6.5 for both.
So **Table 8's "Concentration" column is not uniformly a weighed box-core mass.**
Box core 23 is the distribution's maximum outlier (2.414), and it is one of the
two. Across the shared cores, where Table 9's two columns disagree, Table 8's
value tracks the **Photo** column more often than the Weight one (BC 6, 9, 12, 22,
27, 28), though a few (8, 13, 19) match neither — a pattern this task reports as
a lead, not as a settled reading.

That is fatal to the test's power, not to the hypothesis. A photographic estimate
running ~25% above a weighed mass would produce a median of 0.80 with exactly this
kind of scatter, and so would a 20% wet→dry conversion with noise. **The two
explanations are the same size, point the same way, and cannot be told apart from
these two documents.** Reporting RESOLVES here would be reading a confound as a
confirmation.

> **AMENDED — §9 replaces "not uniformly" with "not anywhere".** The two dashes
> were the visible corner of a whole-table property. Table 8's Concentration
> column reproduces from the Coverage and Diameter columns printed beside it by
> a single constant, and Piper's Techniques section says in plain words that the
> abundances "were estimated from photographs of box cores". The confound is not
> a contaminant in the column — it **is** the column. See §9.

**Not FAILS, either.** The evidence leans the hypothesis's way — the median sits
on the predicted value and the interval excludes parity. Calling it FAILS would
throw away a real signal.

**AMBIGUOUS: the spread is too wide, and a confound of equal magnitude is
present. The Contract 1 wet/dry gap stays OPEN** and gets its BACKLOG entry in
this commit.

## 6. [03] and [04] are NOT independent sources — recorded regardless of the verdict

**The footnote, verified in the PDF.** Sorem's Table 1 carries superscript 1 on
its title, and the footnote below the rule reads: **"¹From Sorem et al. 1979a."**
Sorem's own reference list (p. 200) resolves it:

> Sorem, R. K., R. H. Fewkes, and W. D. McFarland. 1979a. Occurrence and character
> of manganese nodules in DOMES Sites A, B, and C, east equatorial Pacific Ocean.
> In Bischoff, J., and D. Piper, eds., *Marine geology and oceanography of the
> Pacific nodule province.* New York: Plenum, **475–527**.

[03] is pp. **437–474** of that same Plenum volume, one of whose editors is Piper
himself. [04] Table 1 is therefore a 1989 re-publication of numbers from the
chapter immediately following [03] in the same book. Piper's chapter cites it
directly — *"(Sorem et al., this volume)"* (p. 456) — and credits Sorem for the
box-core photographs Table 8's coverage column rests on (Fig. 4 caption, p. 453:
*"Photographs were provided by R. Sorem."*).

**And this task proved the sharper form of it:** §3 showed the two tables describe
**the same 19 physical box cores** from the same cruise and leg. They are not two
observations of the seafloor; they are two reports of one sampling programme.
Ingesting both as independent MASS stations would duplicate 19 stations.

**Recorded through the mechanism already in use for [18]/[19]** — the
`derivation:` and `notes:` prose on the source's own row in
`data/sources/source_queue.yaml`, where `[19]` carries *"largely derived from
TS-6 + Morgan"* and *"NOT independent stations"*. No second mechanism was
invented. Both `[03]` and `[04]` rows now carry the relationship and name each
other.

## 7. What would close the wet/dry gap (the BACKLOG entry's content)

The gap is not blocked on data acquisition — it is blocked on **separating the
method offset from the basis offset**, and the evidence that would do it is
named, in order of decreasing reach:

1. ~~**A full transcription of [03]'s Table 9 box-core sub-table** (printed
   p. 458, columns 6–8), then re-running §4 against the **Weight kg/m²** column
   instead of Table 8's mixed one — the cheapest decisive step.~~
   **AMENDED — this step is UNDER-POWERED, not pending. See §11.** It is still the
   right instrument in kind, and it does remove the method confound §9 identifies.
   What it cannot do is *establish* a basis: it weighs [04]'s unstated basis
   against [03]'s unstated basis — two unknowns, one equation.
2. **Sorem et al. 1979a itself** (pp. 475–527, the source [04]'s Table 1 is drawn
   from), which should state how the nodules were dried and weighed. Not on disk;
   same volume as [03].
3. **A statement of basis for TS-6's own distribution**, which Contract 4's
   cutoffs are anchored to — still unstated, and the other half of the same gap.

Until then `abundance_basis` stays **unrecorded rather than guessed**: a basis
picked from a median that a confound can produce would be an AUTHORED value
wearing a citation, which is the failure mode this project's LITERATURE bar exists
to catch.

## 8. Corrections and limits of this task

- **The prompt's "reciprocal of that factor" was not adopted verbatim.** The
  factor was derived here (§1) and the prediction stated explicitly as
  **[04]/[03] → 0.80**, since "the factor" is ambiguous between 0.80 and 1.25.
- **Sorem's Figure 6 caption disagrees with his own Table 1 on a count** — it says
  the pictured core *"contained 170 nodules at the surface"* while Table 1 gives
  321 for box core 18. Most likely a surface count against a fully-excavated
  total, and it does not touch the station↔box-core pairing, which the
  photograph's label board carries independently of the caption. Flagged, not
  resolved.
- **The Table 9 Weight-vs-Photo pattern in §5 is a lead, not a finding.** The two
  dash cells (BC 11, 23) were read directly from the page image and are solid; the
  broader column-tracking claim rests on a partial read and is exactly what item 1
  of §7 exists to settle.
- **This walkthrough's own count was wrong on first writing, and the
  verification pass over it caught that**: §5 said the trimmed set had *five*
  cores above 1.0 — five is the FULL set's count (11, 12, 13, 18, 23); the
  trimmed set has three, because trimming removes two of them. A figure true of
  one set carried into the sentence about the other — the drift table's
  qualifier-true-in-one-context shape (e), reproduced inside the paragraph that
  exists to argue the trimmed set matters. Corrected before the commit landed.
- **No code changed; the suite is unchanged at 709 passed, 2 skipped.**

---

# Commit 2 — 2026-08-28. The verdict recorded, and the confound derived to its floor

The verdict as accepted: **AMBIGUOUS.** The distribution was shown, the reasoning
held, and declining to read a confound as a confirmation was the right call. What
follows does not reopen it. §9 shows the confound is total rather than partial,
which makes AMBIGUOUS *more* firmly the right verdict, not less — and changes what
"open" means for the Contract 1 gap.

## 9. AMENDMENT — Table 8 contains no mass measurement anywhere

§5 recorded that Table 8's Concentration column is *"not uniformly a weighed
box-core mass"*, on the evidence of two dashes in Table 9. That was true and it
understated the case.

**The derivation.** Table 8 prints, beside every Concentration, a **Coverage (P,
%)** and an **Average Diameter (D, cm)**. Testing whether one constant `k`
reproduces `Concentration = k · P · D` to the printed decimal, across the whole
table:

| block | rows with P and D printed | reproduced by ONE constant | admissible interval for k |
|---|--:|--:|---|
| Site C, second station series (**the 19 join rows**) | 19 / 19 | **16 / 19** | [0.07994, 0.08013] |
| Site C, first series + M.W. rows | 19 / 31 | 18 / 19 | [0.07978, 0.08008] |
| Site A | 25 / 27 | **25 / 25** | [0.07982, 0.08007] |
| Site B | 16 / 34 | **16 / 16** | [0.07995, 0.08024] |
| **all of Table 8** | **79 / 111** | **75 / 79** | **[0.07995, 0.08007]** |

Every interval contains **k = 0.08000 exactly**, and the whole-table interval is
0.0800 ± 0.00006. Sites A and B reproduce with *no* exceptions. This is not a
correlation — it is the column being recomputed.

**The four rows that do not reproduce**, all in Site C, all re-read from the page
images at 900 dpi and all confirmed transcribed correctly, so the residuals belong
to the source:

| row | P | D | printed | 0.08·P·D | residual |
|---|--:|--:|--:|--:|--:|
| C `D.14` BC 38 | 57 | 1.4 | 6.3 | 6.38 | −0.08 |
| C `D.1` BC 6 | 20 | 3.1 | 5.1 | 4.96 | +0.14 |
| C `D.11` BC 16 | 30 | 7.2 | 17.5 | 17.28 | +0.22 |
| C `D.16` BC 22 | 70 | 2.1 | 12.8 | 11.76 | **+1.04** |

Three are small enough to be the authors' own rounding or arithmetic; BC 22's
+1.04 has the shape of a single-digit typesetting slip (11.8 set as 12.8).

**Against the constant printed in the Techniques section.** Piper, printed p. 439,
verified against the page image rather than the OCR layer:

> "Nodule abundances (A, in kg/m2) **were estimated from photographs of box
> cores** by determining nodule coverage (P) and average maximum nodule diameter
> (D), and using the following equation: **A = 19.5 DP/100** (This equation assumes
> that the vertical nodule axis is 0.57 times D). In the case of 15 box cores,
> these estimates have been compared to actual nodule weights. With the exception
> of two box cores, agreement of the two techniques was within 25%."

The printed coefficient is **0.195**. The fitted one is **0.0800**. They differ by
a factor of **2.4375**, and the printed coefficient reproduces **not one row** of
the table it describes. As a sanity check the fitted constant is the physical one:
`A = (P/100)·(0.57 D)·10·ρ` gives k = 0.0800 at ρ ≈ 1.40 g/cm³, a plausible wet
bulk density for nodules; the printed 0.195 implies ρ ≈ 3.4 g/cm³, which no
manganese nodule has. **The equation as printed is wrong; the table was computed
with 0.08.**

**The finding, restated as the derivation supports it.** Whichever coefficient was
intended, the sentence that matters needs no fitting at all: Piper says the
abundances **were estimated from photographs**. The arithmetic confirms he means
it literally — the column is a closed form over the two columns beside it.

> **[03] Table 8 contains no mass measurement anywhere.** Its Concentration
> column is a geometric estimate: covered area × an assumed vertical axis × an
> assumed bulk density. Nothing in it was ever on a balance.

**Therefore a wet/dry basis question is not well-posed against Table 8.** A basis
describes what was *and was not* driven off a sample that was weighed. Table 8
weighs nothing; its moisture content is not unstated, it is *undefined*. Asking
whether Table 8 is wet or dry is a category error, and `abundance_basis` cannot be
filled for it with any value — including `"unknown"`, which asserts that an answer
exists and is not known.

**What this does and does not do to the verdict.** It does not rescue the
hypothesis and it does not refute it. It removes the ratio's standing as evidence
about basis at all: §4's 0.800 median compares a balance reading against a
photograph, so its agreement with 0.80 is not a measurement of drying loss. The
verdict stays **AMBIGUOUS** — and §5's reason for it is now derived rather than
inferred.

**This extends §5 rather than contradicting it** (the STOP condition this task
carried, checked before writing): §5 said the column is not uniformly a weighed
mass; §9 says it is nowhere one. Same direction, strictly stronger. §5's subsidiary
observation — that Table 8's values track Table 9's *Photo* column more often than
its *Weight* column — is now explained rather than merely noted, since Table 8 and
Table 9's Photo column are the same computation.

## 10. NEW FINDING — [03] Table 8 has dropped rows

Independent of the basis question, and a defect of the source rather than of the
transcription: **Table 8's printed `Average:` rows cannot be reproduced from the
rows Table 8 prints.** Row counts were confirmed twice (image reads and clustering
of the PDF's own word positions), so nothing was missed on this side.

For each site and column: the recomputation at the printed row count, and every
integer denominator whose mean rounds to the printed value.

| site | column | rows available | sum | recomputed | printed | verdict | implied n |
|---|---|--:|--:|--:|--:|---|---|
| A | Coverage % | 27 | 589.0 | 21.815 | 21 | **FAILS** | **28** |
| A | Avg Diameter cm | 25 | 78.8 | 3.152 | 3.0 | **FAILS** | **26** |
| A | Concentration kg/m² | 27 | 119.1 | 4.411 | 4.3 | **FAILS** | **28** |
| B | Coverage % | 21 | 196.5 | 9.357 | 10 | **FAILS** | **19–20** |
| B | Avg Diameter cm | 16 | 83.1 | 5.194 | 5.2 | recomputes | 16 |
| B | Concentration kg/m² | 34 | 186.8 | 5.494 | 5.5 | recomputes | 34 |
| C | Coverage % | 39 | 1734.0 | 44.462 | 43 | **FAILS** | **40** |
| C | Avg Diameter cm | 38 | 104.6 | 2.753 | 2.6 | **FAILS** | **40–41** |
| C | Concentration kg/m² | 50 | 497.2 | 9.944 | 9.2 | **FAILS** | **54** |

**Sites A and C fail on all three columns; Site B fails on Coverage only.**

**Why "dropped rows" rather than "bad arithmetic".** Site A settles it. All three
of its columns imply **exactly one more row** than is printed — 28 against 27, 26
against 25, 28 against 27 — and the bounds that missing row must satisfy are
mutually consistent and physically sensible: coverage ≤ 13%, diameter ≤ 0.5 cm,
concentration ≤ 2.7 kg/m². They are also consistent with **§9's own formula**:
0.08 × 13 × 0.5 = 0.52 kg/m², comfortably inside the ≤ 2.7 the concentration bound
allows independently. One near-barren box core, present when the averages were
computed and absent when the table was set. Three independent columns agreeing on
"+1 row, and here is what it looked like" is not three arithmetic slips.

Site C is the same shape, larger: +1 coverage, +2–3 diameter, +4 concentration —
**at least four rows** dropped, of which fewer carried coverage and diameter than
carried concentration, which is the printed pattern of the `M.W.` (R/V *Moana
Wave*) rows. Summing the concentration column's implied denominators, Table 8's
working set held **at least 116 rows against the 111 it prints**.

**Site B's Coverage is the one that runs the other way** — 19–20 implied against 21
printed, the only column anywhere implying *fewer* rows. A dropped row cannot
produce that; it is either an excluded subset or a mis-computed average. Recorded,
not explained.

**Does this touch the join?** **Yes — the 19 join rows sit entirely inside Site C**,
the worst-affected site. It does not corrupt the join, which uses per-row values
and never the printed averages, and §9's fit is per-row too. What it does is bound
how much this source can be trusted to have printed what it computed: an average
whose denominator disagrees with its own table is a source that did not check
itself.

## 11. AMENDMENT — the closing remedy is under-powered, and the gap may be inapplicable

§7 named "transcribe Table 9's Weight column and re-run the ratio" as the closing
step. Before leaving it there, its resolution was derived.

**Printed precision of [03] Table 9, column 7 (`Weight kg/m²`).** Every printed
value is an integer — the column carries **1 kg/m² resolution**, so a half-ulp
rounding uncertainty of **±0.5 kg/m²**. As read at WET.1, 17 of the join's 19 cores
carry a numeric weight (cores 11 and 23 print a dash, and core 17 — the reserved
one — is listed but blank). The column runs
`3, 7, 7, 7, 8, 9, 10, 11, 11, 11, 13, 14, 14, 15, 17, 19, 20`.

| | value | ±0.5 as % of value | against the 20% effect |
|---|--:|--:|---|
| minimum | 3 | **±16.7%** | **comparable** — effect is only 1.2× the noise |
| median | 11 | ±4.5% | smaller — effect is 4.4× the noise |
| maximum | 20 | ±2.5% | smaller — effect is 8.0× the noise |

**The honest reading of that table: resolution alone does not sink the remedy.** At
the median the quantization is about a quarter of the effect, and over 17 cores the
noise on a median ratio would be roughly 1%. Only at the column's low end does the
rounding become comparable to the thing being measured. Recording it as "resolution
kills it" would be as wrong as recording it as decisive.

**What does sink it is structural.** Even a perfectly transcribed, perfectly
resolved Weight column would compare **[04]'s unstated basis against [03]'s
unstated basis**. Neither document says how its nodules were dried or drained
before weighing — [04] Table 1 gives grams with no protocol, and [03] gives Table 9
column 7 with none either (the 110 °C drying on p. 439 governs the samples selected
for *chemical analysis*, not the abundance weighings). A ratio of 0.80 between two
unknowns has two unknowns and one equation; it cannot say which side is dry. **The
remedy is therefore UNDER-POWERED rather than pending** — worth doing to remove
§9's method confound, not capable of closing the gap.

**What the gap actually is, per source, after §9:**

| | is a basis question well-posed? | state |
|---|---|---|
| **[03] Table 8** (the column a corpus would ingest) | **No** — no mass exists in it (§9) | **INAPPLICABLE**, not open |
| [03] Table 9 col 7 (box-core weights) | Yes | **OPEN** — protocol unstated in [03] |
| [03] Table 9 col 9 (area averages) | Yes | **ANSWERED** — dry, salt-free, by its own caption |
| [04] Table 1 (grams) | Yes | **OPEN** — protocol unstated in Sorem 1989 |

**What would actually close it:** a document that states a drying/weighing protocol
for at least one side — **Sorem et al. 1979a** (pp. 475–527, the chapter [04]
Table 1 is drawn from) is the first candidate and is not on disk. Failing that, the
gap stays open for [04] and for [03]'s Table 9, and is **closed as inapplicable**
for [03]'s Table 8.

## 12. Consequences recorded but NOT acted on (they are Karl's call)

§9 has two implications for `source_queue.yaml`'s `[03]` row that this task
deliberately did not execute, because both change contract-bearing fields:

- **`evidence_classes: [MASS, COVER]`.** The PANGAEA dataset catalogued as `[03]`
  *is* Table 8 (its own citation line reads "(Table 8, pages 454-455)"). After §9,
  its Concentration column is not a MASS observation — it is COVER and size run
  through a formula. Carrying it as MASS would put 79 computed rows into a training
  target as if they were weighings.
- **`data_origin: MEASURED`.** Under TAX.1's rule — what the artifact IS decides
  its class — a column computed by closed form from two measured inputs is
  **DERIVED**. The Coverage and Diameter columns remain MEASURED.

Both are flagged in the `[03]` row's comment block and carry a BACKLOG entry. No
field value was changed.

## 13. Corrections and limits of commit 2

- **Nothing in commit 1 was withdrawn.** §5's confound finding was amended to a
  stronger form, §7's step 1 was struck and replaced, and the verdict is unchanged.
- **All four non-reproducing rows were re-verified before being called source
  defects**, at 900 dpi: `D.1`/BC 6 (20, 3.1), `D.11`/BC 16 (30, 7.2),
  `D.16`/BC 22 (70, 2.1) and `D.14`/BC 38 (57, 1.4, 6.3) all read exactly as
  transcribed at commit 1. The fit is therefore also an independent audit of the
  transcription, and it passed. **The claim was over-broad when first written**
  and the verification pass caught it: the sentence said "four" while naming
  three — `D.14`/BC 38, the one row outside the join series, had not been
  re-read. It was then re-read rather than the claim narrowed, which is why the
  sentence now says four and means it. This is the drift table's *remedy
  overstating its own rigour* shape (p), appearing inside a bullet whose whole
  job is to state what was verified.
- **The Table 9 Weight column in §11 was read, not exhaustively re-verified.** The
  precision claim (integers, ±0.5) is robust to that and so is the minimum (3) and
  the median (11 under either reading of the one ambiguous glyph, at box core 12,
  which the OCR renders 3 and the 600-dpi image renders 8).
- **§9's density check is a plausibility argument, not a claim about the authors'
  intent.** It says 0.08 corresponds to a believable nodule density and 0.195 does
  not; it does not establish how the printed 19.5 arose.
- **No code changed; the suite is unchanged at 709 passed, 2 skipped.**

---

# WET.2 — 2026-08-30. Per-row provenance for [03] Table 8, and the claim that was too broad

Commit 2 recorded that `abundance_basis` **cannot be filled for Table 8 with any
value**. That sentence was broader than the evidence under it. The constant fit
covers the rows that print Coverage *and* Average Diameter; it is **silent** on the
rows that do not, and Table 8 has 32 of those (8 + 24). This task partitions the table,
states what the fit does and does not reach in each part, and narrows the record
accordingly.

**Nothing here re-runs the fit** — the constant, its interval and its four
exceptions are taken as recorded. **`evidence_classes` and `data_origin` are
untouched and their flags stand** (§12); correcting them needs paired Track-E
re-wiring and is its own task.

## 14. The partition — derived from the shapes Table 8 actually prints

Rather than assume classes, the table was asked which shapes occur. Exactly four
do, over the three binary facts available per row (is Coverage printed, is Diameter
printed, is Concentration non-zero):

| class | Coverage | Diameter | Concentration | n | A / B / C |
|---|---|---|---|--:|---|
| **P1-BOTH-INPUTS** | printed | printed | > 0 | **78** | 25 / 15 / 38 |
| **P2-BOTH-INPUTS-ZERO** | printed | printed | = 0 | **1** | 0 / 1 / 0 |
| **P3-COVERAGE-ONLY** | printed | **dashed** | = 0 (all) | **8** | 2 / 5 / 1 |
| **P4-NO-INPUTS** | **dashed** | **dashed** | > 0 (all) | **24** | 0 / 13 / 11 |
| | | | **sum** | **111** | |

**The partition closes: 111 = 27 + 34 + 50, the printed row count of Table 8.**
Exclusivity is by construction — a single predicate chain, first match wins — and
every row was asserted to receive exactly one class. Two corners are empty and were
checked rather than assumed: **no row prints a Diameter without a Coverage** (0
rows), and **no row prints neither input while carrying a zero** (0 rows). The
STOP conditions did not fire.

Two shapes are worth naming for what they are. **P3 is the barren class**: all 8
rows print Coverage 0 or 1 with a dashed Diameter — there were no nodules to
measure a diameter on, so the input is missing for a physical reason, and the
Concentration is 0. **P2 is a single row**, Site B `D.53` box core 44, printing
Coverage `.5` and Diameter `.7` — the smallest non-empty core in the table.

## 15. What the fit reaches, class by class

| class | does the recorded constant fit apply? | what it establishes | what it does not |
|---|---|---|---|
| **P1** (78) | **Yes — this is the fit's entire domain.** 74 reproduce at k ∈ [0.07995, 0.08007]; 4 do not | these rows are **computed**, not weighed: covered area × assumed vertical axis × assumed bulk density | nothing about the 4 exceptions individually |
| **P2** (1) | Formally yes, **evidentially no** | 0.08 × 0.5 × 0.7 = 0.028 → prints 0.0 — consistent, but **a zero is produced by every method**, so this row carries no discriminating information | that the row was computed rather than weighed |
| **P3** (8) | **No — the fit cannot be evaluated**, there is no Diameter to multiply | nothing about method | anything; but the Concentration is **0.0**, and a barren core weighs zero on any basis, so no basis question arises |
| **P4** (24) | **No — the fit is entirely silent.** Neither input is printed | nothing whatsoever | everything: origin, method, basis |

**The correction this makes to the record.** Commit 2's finding — *"Table 8
contains no mass measurement anywhere"* — is established for **74 rows** and
strongly indicated for the 4 P1 exceptions (three residuals of 0.08–0.22 are
consistent with the same computation plus a rounding or arithmetic slip; BC 22's
+1.04 has the shape of a single-digit typesetting error). It is **vacuously true**
for the 9 zero-valued rows of P2 and P3, which contain no mass on any reading. It
is **not established at all** for the 24 rows of P4. The honest scope of the
finding is **87 of 111 rows**, not 111.

## 16. The Moana Wave series coincides exactly with P4

Table 8's caption: *"The M.W. Series of samples were collected by the R/V MOANA
WAVE."* Tested as a set identity rather than eyeballed:

```
  rows whose Station is an M.W. label : 24
  rows in class P4                    : 24
  M.W. \ P4 = 0        P4 \ M.W. = 0        M.W. == P4 : TRUE
```

The correspondence is **exact**: the four sub-series `M.W.16` (10 rows, Site B),
`M.W.8` (3, Site B), `M.W.13A` (3, Site C) and `M.W.13B` (8, Site C) are precisely
the rows that print neither input, and no D. row is among them.

**This is the strongest single fact in the task.** The class the fit cannot reach
is not a scatter of incomplete rows — it is one coherent block, collected by a
different vessel, and every D. (DOMES/*Oceanographer*) row in the table prints at
least a Coverage. Whatever produced the M.W. numbers, it was a different pipeline,
which is exactly why the fit is silent on them and exactly why the silence is not
an accident of typesetting.

**A hazard that follows, recorded because it would bite a later join.** The
`M.W.13A`/`13B` box-core numbers run 2–12, and **7 of those 11 (6, 7, 8, 9, 10, 11,
12) collide numerically with Table 9's RP-8-OC-76 box-core numbers.** A lookup of
"Site C box core N" against Table 9 would return an *Oceanographer* weight for a
*Moana Wave* row. This is WET.1 §3's recurrence hazard one level down, and it is
the trap any attempt to find weights for P4 walks into first.

## 17. Discriminator search on P4 — bounded, and its outcome

Question: can **any** test available from the two documents on disk distinguish a
weighed mass from a photo estimate with unprinted inputs, for the 24 P4 rows?

**Test A — are the printed values reachable by the fitted equation under plausible
unprinted inputs?** Table 8's own printed inputs span Coverage 0–70% and Diameter
0.7–9.0 cm. For each P4 value, all integer Coverage and 0.1-cm Diameter pairs in
those ranges were enumerated:

- **24 of 24 P4 values are reachable.** Zero rows are unreachable, so no row
  falsifies the formula.
- The map is heavily many-to-one: **median 30 distinct (P, D) pairs** per printed
  value (min 5, max 62). Even the hardest row — `M.W.13B` box core 11 at
  **30.0 kg/m²**, the table's maximum — needs only P·D = 375, e.g. 70% × 5.4 cm or
  50% × 7.5 cm, both inside the observed ranges.
- **Result: cannot exclude the formula, and cannot confirm it.** A test that every
  value passes has no discriminating power. **FAILED.**

**Test B — does the last-decimal-digit distribution of P4 differ from P1's, where
the formula is known to have been used?**

| last digit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| P1 (n=78) | 11 | 3 | 6 | 7 | 14 | 10 | 6 | 7 | 9 | 5 |
| P4 (n=24) | 6 | 4 | 2 | 0 | 1 | 2 | 4 | 2 | 0 | 3 |

P4 ends in `.0` more often (6/24 = 0.250 vs 11/78 = 0.141), which is the visible
oddity — `20.0`, `15.0`, `15.0`, `30.0` all appear in `M.W.13B`. Exact one-sided
binomial: **P(X ≥ 6 | rate 0.141, n = 24) = 0.112**, not significant at 0.05.
**FAILED — and its power ceiling is worse than the p-value suggests:** a weighed
mass printed to one decimal and a computed mass printed to one decimal have the
*same support*. Digit frequency can detect a different **rounding habit**; it
cannot detect a different **measurement method**. Its power against the actual
question is zero at any sample size, so it is reported and discarded rather than
pursued.

**Test C — does any other table in [03] carry weights for the same cores?**
`MOANA` and `M.W.` occur on **exactly two pages of the chapter — 454 and 455**,
which are Table 8 itself. Checked individually:

- **Table 9** (p. 458, the only table with a box-core `Weight kg/m²` column) is
  *"Nodule abundance in five areas within Site C"*, keyed to Fig. 6 — *"box core
  and camera flight locations for NOAA cruise RP-8-0C-76"*. It is the
  *Oceanographer* series. It contains no M.W. row, and the numeric collision above
  is a trap, not a match. It also covers Site C only, so the 13 Site B M.W. rows
  have no candidate table at all.
- **Table 10** (pp. 464–465, bulk nodule compositions) is keyed by station-boxcore
  labels — `1-6`, `2-7`, … `22-28`, plus Site A/B and RP-6-OC-75 labels. **No M.W.
  label appears.** It also carries chemistry, not abundance.
- **Table 6** (pp. 450–451) is sediment leachate chemistry, labelled `46-1-1`,
  `47-10-9` … under cruise `RP-8-0C-75`. No M.W., and no abundance column.
- **[04]** cannot help either: Sorem 1989 Table 1 is RP8-OC-76 Leg 9 box cores
  only, so it shares not one core with the M.W. series.

**FAILED — no other table on disk carries the M.W. cores in any column.**

**Test D — does the prose state a method for the M.W. samples?** The caption says
only that they were *collected* by the R/V *Moana Wave*; collection is not
measurement. The chapter mentions the series nowhere else. Worse, the Techniques
section offers a **third** candidate origin rather than narrowing to two: besides
box-core photographs it describes *bottom* photographs used *"to estimate nodule
size and abundance"* from about 200 usable frames. So P4 could be weighed, or a
box-core photo estimate with unprinted inputs, or a bottom-photograph estimate —
and nothing on disk chooses. **FAILED.**

> ### **OUTCOME: NO DISCRIMINATOR AVAILABLE.**
> Four tests were tried. A and B have statable power and both return nothing —
> A because every P4 value is reachable, B because it is underpowered at n = 24
> *and* structurally blind to the distinction. C and D fail on availability: no
> other table on disk carries these cores, and no prose describes their method.
> No further test was manufactured, because none was found whose power could be
> stated.

## 18. The narrowed `abundance_basis` record for [03]

Commit 2's blanket claim is replaced by a per-class disposition, written onto the
transcription itself as a per-row column (§19) and onto the `[03]` queue row:

| class | n | `abundance_basis` disposition | why |
|---|--:|---|---|
| **P1**, the 74 the fit reproduces | 74 | **INAPPLICABLE** | no mass exists in the value; it is a geometric computation. A basis is a category error here |
| **P1**, the 4 exceptions | 4 | **INAPPLICABLE (presumed)** | same class and same shape; the fit misses them by 0.08–1.04, consistent with a slip, but not individually established |
| **P2 + P3** | 9 | **VACUOUS** | the Concentration is 0.0. A barren core weighs zero wet and zero dry; the question is well-formed and its answer is method-independent |
| **P4** | 24 | **UNRESOLVED** | non-zero values; the fit is silent, and §17 found no discriminator on disk |

**UNRESOLVED is deliberately distinct from the two dispositions already in the
record.** *INAPPLICABLE* asserts there is no mass to have a basis (P1). *OPEN*
asserts a mass exists, has a basis, and the basis is not stated — which is where
[04] Table 1 and [03] Table 9 col 7 sit. **UNRESOLVED asserts less than either: we
do not know whether these 24 values are masses at all.** Filling `abundance_basis`
for them with `"unknown"` would over-claim, because `"unknown"` presupposes a
mass; leaving them INAPPLICABLE would over-claim in the other direction.

## 19. Recorded

- **Per-row provenance column on the transcription**
  (`~/CCZ/downloads/domes/Piper1979_Table8_TRANSCRIPTION.txt`) — one value per row
  for all 111 rows, not a summary. Two mechanical format changes are documented in
  the file's own amended header: the texture field is now always present (a printed
  blank writes `.`), and `provenance` is the new final field. **Round-trip
  verified**: re-parsed after the rewrite, all 111 rows present and every original
  field byte-identical to before.
- **`[03]`'s queue row** carries the narrowed four-way disposition, replacing the
  blanket "cannot be filled with any value".
- **A BACKLOG entry filed at the moment of deferral** for P4's unresolvability.
- **`evidence_classes` and `data_origin` untouched**, flags standing, per scope.

## 20. Can [03] enter as MASS at source level? Still no — and what would have to change

**No.** 87 of 111 rows are either a geometric computation (P1) or a
method-independent zero (P2, P3); none of them is a mass observation, and no
evidence could make them one, because the arithmetic that produced them is
recorded in the table itself.

**The only class whose reclassification could change anything is P4** — and even
then the answer at *source* level stays no:

1. P4 would first need a discriminator showing its 24 values are weighings. §17
   says none exists on disk, so this needs a document not yet held.
2. If that succeeded, [03] would become a **partial** MASS source: 24 of 111 rows,
   admissible only under a row-level filter on the provenance column. A source-level
   MASS classification would still be wrong, because it would admit the other 87.
3. And those 24 would then land in `abundance_basis` **OPEN**, not resolved — a
   weighing whose drying protocol [03] never states. They would arrive needing the
   same answer the Contract 1 gap is already waiting on.
4. **None of the 24 is in the WET.1 join.** P4 is disjoint from the 19 RP-8-OC-76
   cores, so nothing here revisits the AMBIGUOUS verdict.

## 21. Corrections and limits of WET.2

- **A recorded claim was narrowed, not withdrawn.** Commit 2's *"`abundance_basis`
  cannot be filled for Table 8 with any value"* was true of the class it was
  reasoning about and over-stated for the table as a whole. Its scope is now
  87 of 111 rows, with the remaining 24 explicitly UNRESOLVED. The verdict, the
  constant, and the non-independence record are unaffected.
- **The four P1 exceptions are carried as "presumed", not proven.** They sit in the
  fit's class and are almost certainly the same process with slips, but this task
  did not re-run the fit and does not claim them individually.
- **Test B is reported despite being worthless**, because "we looked and it told us
  nothing" is a different record from "we did not look" — and because its power
  ceiling, not its p-value, is the reason it was abandoned.
- **This section's own complement count was wrong on first writing.** The intro
  said Table 8 has "33" rows not printing both inputs; it has **32** (P3's 8 plus
  P4's 24 — the complement of P1+P2 = 79). Caught by re-deriving the complement
  from the partition table rather than re-reading the sentence, and corrected in
  all three places it had been copied to before the commit was finalised. The
  partition itself, which is what the STOP condition guards, always summed to 111.
- **The P4 disposition depends on the transcription being complete for those rows.**
  The M.W. rows print only a Concentration, so there is little to mis-read; the
  row count was confirmed mechanically at WET.1 and is unchanged here.
- **No code changed; the suite is unchanged at 709 passed, 2 skipped.**
