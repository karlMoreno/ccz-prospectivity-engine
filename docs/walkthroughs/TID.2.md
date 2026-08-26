# TID.2 — What the predicted cells actually are

**2026-08-26 · one commit · suite 704 → 709 · nothing downloaded**

G.3 recorded **where** the predicted cells are. This records **what they are**,
and measures the consequence instead of asserting it.

```
  G.3                                TID.2
  ───                                ─────
  54.9% of the study extent          ...is SRTM15+ V2.8, whose predictions
  is TID 40-48, "predicted"          come from SWOT satellite gravity put
  from satellite gravity             through a machine-learning model
        │                                        │
        │                            ┌───────────┴───────────┐
        ▼                            ▼                       ▼
  "the interpolation's        WHOSE gravity,           MEASURED: how much
   smoothness" (prose)        which method,            short-wavelength
                              which papers             structure is missing
```

## 1. §0 verified verbatim — all of it held

The tracked `GEBCO_Grid_documentation.pdf` **§2.1** says, and the artifact now
carries the sentence rather than a paraphrase:

> This release of the SRTM15+ data set uses a new highly-accurate gravity field
> data set from the Surface Water and Ocean Topography (SWOT) satellite (Yu et
> al., 2024) and machine learning methods to produce a bathymetric model
> (Sandwell et al., 2025).

Both references are in the PDF's own bibliography, confirmed with DOIs
(`10.1126/science.ads4472`; `10.22541/essoar.176339961.11752151/v1`). The
paraphrase is avoided deliberately: the G.3 approval's correction-drift
instance **(o)** was a licence clause paraphrased into losing an obligation.

**The release distinction — the load-bearing claim — HOLDS, and by reading
rather than inferring.** The documentation carries a parallel section per
release. §2.1 (GEBCO_2026) names **Version 2.8** and the SWOT sentence; §2.2
(GEBCO_2025) names **Version 2.7** and mentions neither SWOT nor machine
learning. So GEBCO_2026 is the first release whose predicted cells rest on
SWOT, and this provenance is specific to the file this repo holds. That was
checked against both sections — *not* inferred from the word "new".

## 2. §1's resolution figure — NOT verified, and recorded as uncited

The ~8 km figure comes from NASA/JPL press material this repo does not hold.
**The tracked documentation states no resolution for the gravity field at
all:** `8 km`, `wavelength` and `km resolution` return **zero** hits, and every
`resolution` mention refers to the 15-arc-second **grid spacing**.

So `gravity_field_km` is **null**, with a status field explaining why, and a
test fails if anyone later fills in `8.0` without a source. Yu et al. 2024 is
cited as where such a number would live — this repo has not read it, and this
project's own LITERATURE bar is a citation that LOCATES the number.

**The consequence for the "17×" ratio: it is uncited too, so it is not
recorded.** Instead the measurement below was designed **not to depend on the
number** — which turned out to be the stronger route anyway.

**What IS verifiable, and is recorded:** the grid cell is 15 arc-seconds ≈
**463.3 m N–S / 451.4 m E–W at 13°N**, computed from the geotransform. And a
sharper fact than the ratio: **every one of Contract 3's windowed scales —
roughness and TPI at 1400 m, BPI at 460–2300 m — lies entirely below any
plausible gravity resolution.** The recipes operate wholly inside the
unresolved band, which does not require knowing whether that band starts at
8 km or 6 or 12.

## 3. The measurement, and the confound it had to survive

**The confound:** multibeam surveys *target* interesting terrain — seamounts,
contractor blocks. Predicted cells could be smoother simply by sitting on
flatter seafloor. Absolute roughness cannot tell the two apart.

**The control:** a per-cell **short/long roughness ratio**, which is scale-free,
so a cell on flat abyssal plain and a cell on a rough flank are compared on the
same footing. Short = 3 cells (~1.4 km, Contract 3's own roughness window);
long = 19 cells (~8.8 km, at or above where the gravity field is credited).

| scale | direct | predicted | direct/predicted |
|---|---|---|---|
| 1400 m (roughness/TPI window) | 11.19 m | 4.50 m | **2.49×** |
| 2300 m (BPI outer radius) | 18.18 m | 7.76 m | **2.34×** |
| 8.8 km (at/above the gravity scale) | 44.14 m | 25.54 m | **1.73×** |
| **per-cell short/long ratio** | **0.2575** | **0.1737** | **1.48×** |

**Two independent signatures, and they agree.** The gap *narrows* as the window
grows (2.49 → 2.34 → 1.73) — that is what suppression of short wavelengths
looks like, and the opposite of what a simple amplitude difference would do.
And after normalising every cell by its **own** long-wavelength roughness,
predicted cells still carry about **a third less** short-wavelength structure.

**The alternative hypothesis the task named is REFUTED for this extent.** If
the ML step were *injecting* structure the gravity field cannot support, the
deficit would run the other way at short scales. It does not, at any scale
measured — which is the better outcome, since injected structure would be a
worse problem than smoothing.

## 4. Which covariates are affected — the effect scales with derivative order

| layer | direct | predicted | ratio | order |
|---|---|---|---|---|
| **depth** | −4302 m | −4456 m | **0.97** | 0 — a VALUE |
| **slope / aspect** | 1.485° | 0.672° | **2.21×** | 1st derivative |
| **curvature** (profile, plan) | 6.215e-05 | 9.562e-06 | **6.50×** | 2nd derivative |

Each derivative amplifies the missing short-wavelength content, and the
measurement follows that axis exactly. **Depth is the exception** — the medians
agree within ~4%, so a gravity inversion gets depth broadly right. That is what
makes the other two mean something: this is not a uniform offset.

**Seven of Contract 3's eight layers are load-bearing on short-wavelength
structure** (slope, aspect, profile curvature, plan curvature, roughness, TPI,
BPI); depth is the one that is not.

## 5. What this arms — a named train/predict shift for CP1

G.3 measured that **all 35 training stations sit on TID 11 (multibeam)** —
both clusters. Combined with this task's measurement:

> **Training covariates are computed on measured terrain. Prediction
> covariates are ~55% an inversion whose short-wavelength content is measurably
> suppressed — most in curvature, then slope, least in depth.**

That is a **train/predict domain shift with a named mechanism**, and it should
be stated before a model runs rather than discovered in a residual plot.

**It does not block CP1 and it is not a defect.** It is a property of the only
terrain data that exists at this scale; the alternative is no terrain at all.
The honest form is that the model will be extrapolating from measured terrain
onto inferred terrain, and the covariates most affected are exactly the
derivative ones a nodule-abundance model would lean on.

## 6. The asymmetry, read the right way

The DIRECT cells are attributed to a method (multibeam) and nothing else. The
PREDICTED cells are now attributed to a mission, a gravity field, a model and
two papers. **That is not because prediction is better documented, or better.**
It is because prediction NEEDS more documentation to be interpretable: a
multibeam sounding means one thing, while an inversion means whatever its
gravity field and its model make it mean. The artifact says so where a reader
meets the asymmetry.

## 7. Test inventory

| Test | Asserts | Rule |
|---|---|---|
| `..._quotes_the_tracked_pdf_and_both_references` | the verbatim §2.1 sentence; both DOIs | provenance traces to the tracked source, not a paraphrase |
| `..._release_distinction_is_recorded_as_verified_from_both_sections` | §2.1 vs §2.2 named; "Version 2.7"; "NO mention" | verified by reading, not inferred from "new" |
| `..._gravity_resolution_is_recorded_as_UNCITED_rather_than_asserted` | field is null; status says NOT STATED; measurement independent of it | a news figure must not launder into the record |
| `..._short_wavelength_deficit_is_measured_and_survives_the_confound` | gap narrows with scale AND the scale-free ratio still separates | the terrain-selection confound is controlled |
| `..._effect_scales_with_derivative_order_and_depth_is_the_exception` | depth ≈1, slope >1.5, curvature > slope | not a uniform offset |

Four mutations, each caught by name: filling in 8.0 as fact; swapping the
short/long windows; asserting the release distinction unverified; and dropping
the confound control.

## 8. What is deliberately missing

* **No acquisition.** Nothing downloaded; the rasters and the PDF were already tracked.
* **G.3's numbers are untouched** — verified: rebuilding changed **no**
  pre-existing key, and the determinism guard still passes.
* **No covariate added.** SWOT's vertical gravity gradient as a covariate in
  its own right is a real idea and is BACKLOGged with its scope reasoning and a
  trigger tied to the covariate question actually being reopened.
* **The gravity field's resolution stays unknown here.** Closing it means
  reading Yu et al. 2024, which is an acquisition.
