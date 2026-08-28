# WET.1 — Do [03] and [04] report abundance on the same wet/dry basis? AMBIGUOUS, and why the test had no power

**2026-08-28 · one commit · suite 709 → 709 (no code touched)**

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

1. **A full transcription of [03]'s Table 9 box-core sub-table** (printed p. 458,
   columns 6–8), then re-running §4 against the **Weight kg/m²** column instead of
   Table 8's mixed one. If the weight-only ratio tightens onto 0.80, the basis
   reading survives; if the spread persists, it does not. This is possible today —
   the PDF is on disk — and it is the cheapest decisive step.
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
