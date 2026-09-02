# POS.1 — What [04] would need to become ingestible, and what would collide if it did

**2026-09-01 · one commit · suite unchanged (no code touched)**

Derivation only. **[04] was not ingested, no corpus row was created, and no
contract field was changed.** The task was to measure whether the position option
is even available and at what quality — not to take it. The decision it bears on
stays Karl's and is BACKLOGged undecided.

The headline is that the option is available, from a **better table than the one
anyone was looking at**, and that the collision it would create is with **[02]**,
not [03].

```
  [04] Table 1        weighed mass / 0.25 m2, 21 cores      NO COORDINATES
        │
        ▼  station + box core (the WET.2 key, never box core alone)
  [03] TABLE 10       Station-Box Core | Lat | Long | Depth   21 of 21 COVERED
        │                                                     incl. 9-14, 19-25
        │                                                     which Table 8 lacks
        ▼
  0.1 arcmin  ->  ~129 m worst case  ->  6.5% of the narrowest 2 km lag bin
        │
        ▼
  [04] alone: 190 pairs, 1.27-26.68 km, EVERY bin to 13 km populated
        │
        └─ but [02] shares 19 of the same 21 PHYSICAL box cores
```

## 1. Step 1 — the coordinate table, and the search that found it

**It is Table 10, not Table 8.** [03]'s Table 10 (printed p. 464), *"Bulk
compositions of nodules from DOMES Sites A, B, and C"*, carries four left-hand
columns before its chemistry: **`Station-Box Core` | `Lat. (North)` | `Long.
(West)` | `Depth (Meters)`**.

**How the negative was established first**, because this nearly went the other way:
an exhaustive search over all 37 pages returns **zero** occurrences of "Latitude"
and **zero** of "Longitude"; zero degree-minute `N`/`W` patterns; and Table 8 — the
table already transcribed — has no coordinate column. Figure 6 is the only other
per-core spatial record and is a **map**, so reading positions off it would be
inference, which the STOP conditions forbid. Table 10's columns were found only
because the degree glyph OCRs inconsistently (`15°07 9'`, `i5008:3'`, and five Site
C rows printing the degree symbol not at all), so pattern searches missed them and
a token search for a bare `Lat` did not.

**Transcribed** at 650–700 dpi from page images to
`~/CCZ/downloads/domes/Piper1979_Table10_COORDS_TRANSCRIPTION.txt`, outside the
repo beside the existing transcriptions. **0 cells unreadable.** OCR errors the
transcription corrects are listed in its header.

### Verification, including the one that could not be run

| check | result |
|---|---|
| printed data rows | **47** — Site A 17, Site B 4, Site C 26 |
| unique station-box core keys | **41** |
| duplicated keys | 6 (`46-3`, `46-7`, `47-12`, `47-13`, `50-29`, `50-30`) — two nodules analysed from each |
| duplicates carry identical lat/lon/depth | **yes, all six** |
| printed summary statistics over these columns | **none exist** |

**The recompute check could not be run, and that is a finding rather than a pass.**
Table 10 prints `Average (Site A)`, `Average (Site B)`, `Average (Site C)` rows —
but they are **blank in the Lat/Long/Depth columns**; the averages are over the
chemistry columns only. So there is no printed summary over the transcribed columns
to recompute against. Earlier work found dropped rows in Table 8 of this same
source by exactly this method; **that instrument is unavailable here**, and the
coordinates therefore rest on the image reads and on the internal checks of §4.
The first STOP condition cannot fire from this direction — not because the
summaries recomputed, but because there are none.

## 2. Step 2 — coverage is total, and better than Table 8's

Joined on **station + box core**, the WET.2 key. Box-core number alone is refused:
Site C mixes two station series and Table 10's `15-50`, `16-49` collide numerically
with the RP-8 series' `15-21`, `16-22`.

| | count |
|---|--:|
| [04] box cores carrying data (derived at WET.2) | **21** |
| of those, present in Table 10 | **21** |
| without coordinates | **0** |

**Coverage 21/21 = 100%.** The key resolves uniquely — each station-box core
appears once in Site C.

**And it covers more than Table 8 does.** Table 10 includes **`9-14` and `19-25`**
— [04]'s two *"Recovery probably incomplete"* cores, which Table 8 omits entirely
(WET.1 §3). The coordinate table reaches two cores the abundance table does not.

## 3. Step 3 — coordinate quality against the repo's own lag bins

Printed precision is **degrees + decimal minutes to 0.1′**, both columns.

| | value |
|---|---|
| 1′ latitude | 1852 m → **0.1′ = 185.2 m** |
| 1′ longitude at 15.2 °N | 1787.2 m → **0.1′ = 178.7 m** |
| half-ulp (rounding to nearest 0.1′) | **±92.6 m** lat, **±89.4 m** lon |
| worst-case planar offset | **129 m** |

Against the repo's `DEFAULT_BIN_EDGES_KM = (0, 2, 4, 6, 8, 10, 13, 986, 997)`, the
**narrowest bin is 2.0 km**. Positional uncertainty is **0.129 / 2.0 ≈ 6.5% of a
bin**.

> **The positional uncertainty is SMALL relative to the bins these stations would
> populate — not comparable to them.** Even the shortest observed separation
> (1.27 km) exceeds the worst-case offset by a factor of ~10, so no pair is at risk
> of being binned wrongly by coordinate rounding.

## 4. Step 4 — spatial sanity, and one real source defect

Each site was tested against **its own spread** (median distance to the site
centroid, MAD as the scale), then cross-checked against the depth column.

**FLAGGED AND CONFIRMED AS A SOURCE DEFECT — core `3-8`, an [04] core:**

| | |
|---|---|
| printed | `15°15.4'` N, **`126°59.3'` W**, depth 4363 m |
| distance to Site C centroid | **104.1 km** (MAD-z **26.1**) |
| depth | **4363 m — inside** the site range 4359–4641, consistent with neighbours |
| nearest neighbours as printed | 95.5–100.3 km away |
| read as `125°59.3'` (one digit) | falls **3.2 km** from `1-6`; neighbours at 3.2–6.7 km |
| **displacement between the two readings** | **107.3 km** |

Position and depth disagree: the depth says this core belongs in the cluster, the
longitude puts it 104 km outside. **Re-read at 1400 dpi before reporting: the page
prints `126°59.3'`.** This is a **defect in [03]**, not a transcription error. It is
left as printed in the transcription and flagged on both source rows.

**FLAGGED AND DISPOSED OF AS NOT DEFECTS:** Site C's `16-49` (67.4 km) and `58-61`
(63.7 km) are RP-6-OC-75 stations from the wider 1975 survey — internally coherent
with their own pair partners (`15-50`/`16-49` 19 km apart; `58-60`/`58-61` 6 km
apart) and consistent in depth. Site B's `51-34` sits 162.8 km from a 4-core
centroid because Site B is two station groups, not one cluster. **None of these is
an [04] core**, so none touches the measurement.

## 5. Step 5 — the three-way overlap, and where the collision actually is

Over the RP-8-OC-76 Leg 9 cores. [02]'s cores read from its PANGAEA `.tab` on disk;
[03] as the union of its two per-core tables (Table 8's 19, Table 10's 21).

| set | n | members |
|---|--:|---|
| in **all three** | **19** | |
| [02] & [03] only | 0 | — |
| [02] & [04] only | 0 | — |
| **[03] & [04] only** | **2** | `9-14`, `19-25` |
| unique to [02] | 0 | — |
| unique to [03] | 0 | — |
| unique to [04] | 0 | — |

**Is [04] a subset of [03]? YES.**
**Does [04] add any station [03] does not have? NO — none.**
[04] adds two stations **[02]** does not have: `9-14` and `19-25` — the same two
incomplete-recovery cores again.

> **The double-count exposure is [02]×[04], and it is 19 of 21 cores.** [02] is not
> yet ingestible and may later enter as MASS. [04] is a weighed mass over a stated
> area. If both enter without a rule, **19 physical box cores are counted twice** —
> the same seafloor, weighed once, admitted as two independent stations. Established
> now, while nothing is ingested, which is the point of measuring it here.

## 6. Step 6 — what [04] alone would contribute, measured

Derived from the Table 10 coordinates by great-circle distance, binned with the
repo's own `DEFAULT_BIN_EDGES_KM`. **No pair count was taken from any handoff.**

| lag band (km) | pairs, all 21 cores | pairs, 20 cores (excluding the defective `3-8`) |
|---|--:|--:|
| 0 – 2 | 4 | **4** |
| 2 – 4 | 11 | **11** |
| 4 – 6 | 17 | **17** |
| 6 – 8 | 29 | **29** |
| 8 – 10 | 22 | **22** |
| 10 – 13 | 44 | **44** |
| 13 – 986 | 83 | **63** |
| 986 – 997 | 0 | **0** |
| **total** | **210** | **190** |

Separations run **1.27 – 26.68 km** (median 10.65) with `3-8` excluded; including it
the maximum jumps to 120.3 km and the widest bin gains 20 spurious pairs — the
defect's only effect on this measurement, and a reason to exclude it.

> **[04] alone populates every bin from 0 to 13 km, and the bottom of the 13–986 km
> window at 13–26.7 km. It populates nothing at 986–997 km.**

The 13–986 km bin is the repo's recorded zero-pair window (TRACK-G: two ~12 km
clusters ~991 km apart, nothing between). [04] alone does **not** close that window
— it puts 63 pairs into its lowest ~1.4%, extending support from 13 km out to about
27 km. That is new lag space, and it is the specific thing [04] would buy.

## 7. What this measured, and what it deliberately did not

**Measured:** the position source exists, covers 21/21, at ~129 m worst case, which
is 6.5% of the narrowest lag bin; one source defect that must be excluded or
corrected; a 19-core collision with [02]; and 190 pairs extending lag support to
~27 km.

**Not decided, and not decidable here:** whether [04] may take position from [03].
That is Karl's, and it carries a provenance question this task did not answer — a
row whose abundance is MEASURED from [04] and whose position is MEASURED from a
*different publication* has two origins in one row, and the corpus has no
per-field provenance today. BACKLOGged undecided.

## 8. Limits of POS.1

- **The recompute check was unavailable**, not passed (§1). The coordinates rest on
  image reads plus the internal consistency of §4, not on a printed summary.
- **Only four columns of Table 10 were transcribed.** The chemistry columns were
  not, so the table's printed `Average` rows remain unchecked by this task.
- **`3-8` is left as printed.** No corrected value was written anywhere; the
  reading `125°59.3'` is stated as the hypothesis that explains the depth, not
  adopted. Correcting a printed source value is a decision, not a transcription.
- **[02]'s cores were read from its PANGAEA `.tab`**, not from the USBM report,
  which is still not on disk (RETRIEVAL-LOG §2). The overlap therefore rests on
  PANGAEA's event list for [02], and would want re-checking against the report if
  it is ever obtained.
- **No code changed; no contract field changed; [04] was not ingested.**
