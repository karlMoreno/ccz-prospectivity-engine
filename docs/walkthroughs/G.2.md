# G.2 — The CCZ boundary as the AOI, and the coverage metric

**2026-08-25 · three commits · suite 688 → 694 → 703 → 703**

Karl's decision (G.2-PRE §4): **option (b), two concepts kept apart.** This
walkthrough records what that cost, what it did not cost, and the four things
measured along the way that no one predicted.

```
   BEFORE (Phase 0 → G.2)                AFTER (G.2)
   ─────────────────────                 ───────────
   study_area.geojson                    study_area.geojson
     a 2° box, PLACEHOLDER: true           the CCZ management area
     AUTHORED, declared in a README        LITERATURE, declared IN THE FILE
     108 of 108 corpus rows OUTSIDE        0 of 108 outside
     read by: a hash, a count              read by: a hash, a count,
                                             the coverage block, the viewer
              ↓                                       ↓
   "where may the model predict?"        UNCHANGED — still the feature
     answered by accident: whatever        stack's extent, recorded per run
     DEM the run was handed                in manifest.prediction_grid
                                                      ↓
                                          aoi_coverage (schema 5)
                                            stable  : the AOI + its area
                                            per_run : range → supported → fraction
```

## 1. Why (b), and why (a) and (c) lost

Two questions were tangled: *what region is this project about* and *where may
the model emit values*. (b) separates them. The second question was **already
answered by the code** — `PredictionGrid.from_stack()` inherits the feature
stack's extent and `manifest.prediction_grid` has recorded extent, transform,
dimensions and `n_predictable` since E3.1+2 — so (b) is not a new
architecture. G.2-PRE's words: *one block of arithmetic, not an architecture.*

**(a) — one slot, prediction stays implicit.** Lost because the manifest would
have kept saying what the extent WAS without ever saying anyone CHOSE it, while
a real AOI sat in the repo implying otherwise.

**(c) — one slot, regenerated as the corpus grows.** Lost **on a measurement,
not a preference**, and this is the one worth keeping: `study_area_content_hash`
lives in `contract_versions`, which is in `LEGACY_HASHED_FIELDS` and *not* in
`HASH_EXCLUDED_FIELDS`. A polygon regenerated at each ingestion therefore moves
**every future run's `content_hash`**, and the denominator every coverage figure
is quoted against moves with it. Cross-run comparison weakens by construction.
This is the option the planning conversation had been arguing for.

G.2-PRE §5 sealed it: the DOMES coordinates are **not in the source index** (they
live in the datasets) and `source_queue.yaml` has no spatial field at all, so the
corridor's future extent is *unknowable from planning documents*. Fixing the
denominator externally and MEASURING coverage against it is the only option that
does not require predicting where the corpus lands.

## 2. Commit 1 — the polygon, declared

**Two structural corrections to the plan, both forced by the repo:**

1. **The contract file cannot be the publisher's bytes.** `contract_versions.py`
   reads `features[0].properties.area_id`; `StudyArea.from_geojson_feature` needs
   `area_id` and `name`; the WFS response carries `{"dummy": 0, "mrgid": 64222}`.
   So the committed file is *necessarily* an edit. The raw download is preserved
   at `data/aoi/sources/ccz_management_area_mrgid64222.geojson` (44,498 B, the
   publisher's sha256) and `test_the_contract_geometry_is_the_publishers_verbatim`
   asserts the two geometries are equal — which is what turns "only the properties
   were rewritten" into a measurement instead of a promise.
2. **The Marine Regions row is not `src_deepdata_public_context`.** That row is
   ISA DeepData (`data.isa.org.jm`, APEI/contract polygons) — the exclusions half,
   a different publisher and a different licence. A new row
   `src_ccz_boundary_marineregions` was added; merging them would have left the
   APEI source with no row at all.

**Geometry, re-verified** (every figure reproduced): MultiPolygon, 2 parts,
EPSG:4326, 44,498 B; main polygon **11,399,937 km²** / 1,629 closed-ring coords;
sliver **1.41 km²** / 4 coords; both parts **11,399,939 km²**; polygon is 83.0 %
of its own bounding box.

**The sliver decision: KEEP, and the reason changed once its topology was
measured.** It is not a detached island — it touches the main polygon at
**exactly one point**, `(-159.08957834, 7.79794191)`, which is the main ring's
*own closure vertex*. It is a digitisation spur at the seam. Keeping it means the
geometry still verifies against the source; dropping it would have made the AOI
partly *ours*, which is precisely what (b) exists to avoid. Its share is
**0.0000123 %**, pinned as a value rather than an inequality, and the test asserts
the *topology* (`touches`, `intersection` is a Point) so a library that "cleans"
it fails rather than silently redefining the AOI.

**Origin: LITERATURE.** Not MEASURED — the artifact is a boundary *decreed* in
ISBA instruments, and its sha256 proves only which COPY this repo holds. Not
DERIVED — that requires MEASURED inputs, and unlike GEBCO (whose DERIVED rests on
measured soundings at the bottom of its chain) there is no measurement anywhere
here. LITERATURE's evidence rule — a citation that LOCATES the value — is the one
that is satisfiable, and ISBA/17/LTC/7 et seq. satisfies it. *Karl to confirm;
this decides the `src_deepdata_public_context` entry's other half only for the
management area, not for the APEIs.*

**The file vouches for nothing about itself** — properties are `{"dummy": 0,
"mrgid": 64222}`: no name, no citation, no date, no licence. Every piece of
provenance therefore lives in the declaration and the ledger, with nothing
embedded to cross-check against. That is stated in the file, because a reader
would reasonably expect otherwise after GEBCO, whose own documentation supplied
its evidence.

**The audit exemption is gone, and the moment mattered.** `study_area.geojson`
was the one classified file none of the three resolvers could reach; its
EXCLUSIONS reason read *"an in-file marker would move the recorded hash"* — true,
and it stopped being a cost at the one moment the file was replaced outright,
which moved the hash anyway. The file now carries a top-level `data_origin`
(a GeoJSON foreign member, RFC 7946 §6.1, precedented by `exclusions.geojson`
beside it), `_in_file_declaration` reaches it like any other `.geojson`, and the
EXCLUSIONS entry had to go or the module's own never-shadow-a-classification
hygiene test would have caught it. The README-pin test was rewritten from
*restating* the origin to **asserting the README and the file agree**, reading the
origin out of the file — hardcoding `"LITERATURE"` on both sides would pass if
both were wrong together.

**`fraction_outside`, measured rather than assumed: 108/108 → 0/108**, and 0/35
for the training set asserted separately (an aggregate over 108 can hide one
station). The placeholder's miss was **latitude**, not ocean: it reached lon
−125.0 but stopped at lat 13.0, and the west cluster sits at 14.07 N.

**Probes, both directions:** as committed → pass; declaration stripped → 4 named
failures; citation stripped → LITERATURE's evidence branch fires; geometry
truncated to one part → the derivation observer fires.

## 3. Commit 2 — the coverage block

**`no_information()` could not be reused, and the reason is not style.** It loops
prediction-grid cells; the AOI is ~33× larger than the grid, so a grid-cell loop
has nothing to say about the CCZ's other 97 %. What the two share is the
**predicate**, and that is what moved into `provenance/coverage.py`, imported by
both. `test_one_predicate_serves_both_consumers_on_one_earth` asserts the viewer
calls it **by identity**, so a copied body would not satisfy it.

**One earth.** `viewer_model` had its own `6371.0` while `geometry.py` and
`ts6/comparison.py` both used the IUGG mean `6371.0088` — one predicate, two
earths, nothing observing that they agreed. Unified. The claim that this moves
nothing is **measured**: 2,846 no-information cells under both radii, E5.4's
recorded number unchanged.

**The ordering problem is resolved in the OUTPUT, not in a doc.** The range comes
from a fit which comes from a run, so the block names its two halves:

| | contents | quotable |
|---|---|---|
| `stable` | AOI id, hash, area; station count; the predictable domain's share | alone |
| `per_run` | range, supported area, fraction, quadrature step | only with its run |

and `statement` emits the honest sentence directly, so a reader who quotes one
sentence quotes a true one:

> 0.036 % of the 11,399,939 km² AOI (ccz_management_area) lies within one fitted
> variogram range (21.611 km, from ordinary_kriging **itself AT ITS CANDIDATE
> CEILING, so the supported area is a LOWER BOUND**) of any of the 35 training
> stations — 4,125 km². The denominator is fixed; the numerator is this run's.

No range fitted yields `per_run: None`, never `0.0`: no support MEASURED and no
support COMPUTABLE are different facts and a zero would read as the first.

**The method is pinned because it is part of the claim** — and the convergence was
**re-measured with the shipped integrator** rather than inherited. G.2-PRE
reported 4,120 ± 3 km²; this integrator (which clips to the AOI and pads its bbox
differently) measures **4,143.8 / 4,134.3 / 4,124.6 / 4,124.6 / 4,122.1 km²** at
steps 0.04 / 0.02 / 0.01 / 0.005 / 0.0025 — i.e. **4,124 ± 12** at 0.02 and finer,
with the *fraction* stable at 0.0362 % from 0.01 down. G.2-PRE's ± 3 is
deliberately **not** quoted: a spread measured on one instrument does not describe
another, and quoting it would have been correction drift in the very note that
exists to make the number comparable. Step 0.01 ships (same answer to four
significant figures, 4× faster than 0.005).

**The convergence test runs on the real 35 stations**, through
`get_training_samples()` rather than a reimplemented gate, because convergence is
a property of the shipped configuration. The two-station fixture used elsewhere in
that module is the *worst* case for this quadrature (isolated discs are almost all
edge) and converges more slowly — asserting the shipped tolerance there would have
measured the fixture, not the method.

**Also corrected here, and it was live rather than stale prose:** `geometry.py`'s
containment note said the AOI was a Phase-0 placeholder and an open decision.
That string is **emitted into every corpus manifest**, so it was a falsehood being
written into new artifacts, not a comment nobody reads.

**Mutations — six, and one survived.** M1 (bounding box instead of the disc
union), M2 (extent area instead of predictable), M3 (drop the sliver), M5 (store
the fraction), M6 (zero instead of not-computable) each failed by name. **M4 —
swapping `EARTH_RADIUS_KM` back to `6371.0` — PASSED all nine tests.** Read rather
than assumed: the unification test asserts function *identity*, and 1.4 ppm sits
below every other tolerance, so the **de-duplication was guarded and the constant
was not**. Closed with a one-degree pin to six decimals (111.195080 vs 111.194927);
M4 re-applied and caught by name. *Two precisions added at the approval, both
measured: (1) re-run with the new pin DESELECTED, M4 gives 8 passed / 1 deselected —
so "the other tests cannot see it" is confirmed rather than inferred, and it holds
because `haversine_km` is the only site M4 touches while the AREA functions read
`EARTH_RADIUS_KM` directly. A mutation of the CONSTANT ITSELF is a different, broader
mutation, and the area pins DO catch that one. (2) Of the two asserts the fix added,
only the literal pin is load-bearing against that broader mutation — the first
compares against `EARTH_RADIUS_KM` on both sides and moves with it. Keep both: they
catch different mutations.* This is the check-itself-is-in-scope corollary
arriving in a mutation batch: a guard that covers the *shape* of a fix can leave
its *value* unobserved.

## 4. Commit 3 — the viewer, and three things reported not fixed

**The fixture rectangle is gone**, and the registry points at **Contract 2's own
file** rather than a copy under `apps/web/` — so the map draws the polygon the run
was given (E5.3's stations-from-the-manifest rule, one layer over) and the repo
holds two copies of these coordinates instead of three. The CC-BY attribution
reaches the footer where a viewer sees it.

**The scale ratio, re-measured on the polygon.** The old note compared the CCZ's
**bounding box** (~13.86 M km²) with the prediction **extent** (~0.41 M) and got
33.8×. Both sides were generous: the box overstates the zone by 20 %, and the
extent counts cells the covariates do not define. Polygon against **predictable
domain**: 11,399,939 / 346,927 = **32.9×**, i.e. the domain this project can speak
about is **3.04 %** of the zone. *Corrected at the approval: the ratio is
like-against-like in QUANTITY (two areas of a region, both latitude-aware) but NOT
"by the same closed form", as this section and the test docstring both said — the
numerator is `polygon_area_km2`'s closed-form spherical excess, the denominator is
`grid_predictable_area_km2`'s cos(lat)-weighted per-cell SUM. The remedy overstated
its own rigour while correcting a real defect; correction-drift instance (p), and the
test docstring's copy is BACKLOG §3's fence residue.*

**The README defect: STRUCK, not implemented.** `docs/contracts/README.md:132`
claimed Track E
does "clip/align grid" for Contract 2 — zero code, zero tests. Implementing it is
a *decision*, not a fix, so the row now says what is true and the question is a
BACKLOG entry with the asymmetry that makes it non-obvious: the covariates' mask
can only ever SHRINK the domain, so an AOI **larger** than the stack is silently
inert (today's case), while a **smaller** one would be the first thing in this repo
capable of discarding cells the covariates support.

**The fresh-run look** (required every time a task touches the page; report
"nothing" explicitly when nothing is found). A fresh production run, served, looked
at. **Nothing was found in the change.** Two things that looked like findings were
**my own instruments**: a downscaled screenshot that cut off the footer, and a JS
check run before the context fetch completed — both said the attribution was
missing while `#attrib` in fact read *"Coastline: Natural Earth (public domain) ·
CCZ management area: Marine Regions MRGID 64222 (CC-BY 4.0), from ISA limits
ISBA/17/LTC/7 et seq."* Verified positively in the end: the boundary draws as a
white outline whose eastern edge is **curved** (the fixture's was straight),
`/context/ccz_management_area` serves the 2-part geometry with 4 and 1,629
vertices, and both context layers report "shown". One pre-existing warning
reproduced only at a small pane size (`fitBounds` padding exceeding the canvas);
it reads the prediction grid's extent, which this task did not touch.

**Reported, not closed:** the APEIs into `exclusions.geojson` (different
publisher, ISA copyright rather than CC-BY, and **two** Track-E steps because
E4.1 asserts the exclusion set is empty); Contract 2's inability to declare a
change class; and the committed corpus manifest, which now diverges from every
fresh build in four fields at once — only one of which is about the AOI, which is
why regenerating it was left as its own decision rather than bundled here.

## 5. Test inventory

| Test | Asserts, in plain English | Rule it enforces |
|---|---|---|
| `..._geometry_is_the_publishers_verbatim` | the contract file's geometry equals the raw download's; the properties differ | the derivation is a measurement, not a promise |
| `..._ledger_hash_matches_the_preserved_publisher_bytes` | recomputed sha256 = the ledger's; 44,498 B; LITERATURE with an ISBA citation | the ledger is the hash observer, not the audit |
| `..._published_two_part_multipolygon` | 2 parts, 4 + 1,629 coords, sliver *touches* the main ring at its closure vertex | a cleaned sliver is a silent AOI change |
| `..._loads_as_a_study_area_and_identifies_the_contract` | `StudyArea` + `contract_versions` read it through the real paths | the two property consumers still work |
| `..._every_corpus_row_falls_inside_the_management_area` | 0 of 108 and 0 of 35 outside | measured, not assumed; a row outside would be a finding |
| `..._in_file_declaration_is_reachable_and_carries_its_locator` | the AUDIT'S resolver reaches it; LITERATURE + ISBA locator | the exemption is really gone |
| `..._readme_row_declaration_for_study_area_matches_the_file` | README and file AGREE (origin read from the file) | two answers, no way to tell which is used |
| `..._aoi_area_is_the_published_polygons_by_closed_form` | 11,399,937 / 1.41 / 11,399,939; sliver share 0.0000123 % | the keep-it decision's premise |
| `..._union_of_discs_not_their_bounding_box` | ~2 disc areas, not the 350,000 km² cluster bbox | the fixture separates union from bbox |
| `..._quadrature_has_converged_at_the_shipped_step` | halving the step does not move the fraction, on the real 35 | the method is part of the claim |
| `..._fraction_is_derived_from_the_range_and_not_stored` | 5× range → ~25× area; the denominator does not move | derived, not stored |
| `..._no_range_is_reported_as_not_computable_rather_than_zero` | `per_run` None; "not the same as zero" | absent ≠ zero |
| `..._statement_carries_the_dated_numerator_and_the_ceiling_caveat` | LOWER BOUND appears at ceiling and NOT otherwise | the caveat discriminates |
| `..._one_predicate_serves_both_consumers_on_one_earth` | viewer calls the shared function *by identity*; one degree = 111.195080 km | no second implementation; M4's survivor closed |
| `..._earth_radius_unification_moves_no_recorded_count` | equal cell counts under both radii | "negligible" measured, not asserted |
| `..._predictable_area_excludes_masked_cells` | masked half → half the area | the extent box is the wrong number |
| `..._boundary_is_the_aoi_itself_and_the_scale_ratio_is_measured_on_it` | the registry path IS the AOI file; 32.9× and 3.04 % | a copy would pass every other check |

## 6. How to hand-check this

```bash
# the geometry is the publisher's, and the ledger's hash is the publisher's
shasum -a 256 data/aoi/sources/ccz_management_area_mrgid64222.geojson
grep -A2 "src_ccz_boundary_marineregions" data/sources/source_queue.yaml | head

# the coverage block on a fresh run
python -m engine.prospectivity.harness --dem <dem> --dem-data-origin SYNTHETIC \
  --ts6 <ts6> --ts6-data-origin SYNTHETIC --out /tmp/run --run-id look
python -c "import json;print(json.load(open('/tmp/run/run_manifest.json'))['aoi_coverage']['statement'])"
```

## 7. What is deliberately missing

* **Nothing clips on the AOI.** By design today; the decision is a BACKLOG entry.
* **`exclusions.geojson` is still empty.** The APEIs are their own acquisition.
* **The coverage block has one consumer.** It is recorded in the manifest and not
  yet rendered by the viewer — E5.4's honesty surface is where it would go, and
  wiring it is a separate task with its own fresh-run look.
* **`data/corpus/manifest.json` was not regenerated.** Four fields move at once;
  only one is about the AOI.

## 8. What the approval's verification pass found (2026-08-25)

G.2 was approved, and a verification pass over its OWN output found **four
false claims, three of them G.2's own** — recorded here because the pass is
the point, not the score. All four are correction-drift instances (p)–(s):

| # | Claim | Why it was false |
|---|---|---|
| (p) | "by the same closed form" (§4 above and `test_context_layers.py:97,129`) | numerator is closed-form spherical excess; denominator is a cos(lat)-weighted **cell sum**. The 32.9× is sound; the *method* claim is not |
| (q) | `BACKLOG`'s copy of 33.8× / 2.96% | corrected in `context.py` and the test at G.2, left standing in an OPEN entry for a day — the correction-scoped-to-the-claim shape, across **files** |
| (r) | CLAUDE.md's "found something **both times** anyone looked" | already false at E5.6-7, whose look found nothing. A rule about looking whose own tally nobody looked at |
| (s) | `README.md:132` in §4 | the ROOT README has no such line; the file is `docs/contracts/README.md` |

**Two of Karl's approval figures did not survive either, and are recorded as
NOT counted rather than silently dropped:** the "±3 km²" convergence is a
NEAR-MISS, not an instance — 4,120 lies *inside* the shipped instrument's own
4,124 ± 12, it was correctly attributed to G.2-PRE throughout, and it was
never asserted of the shipped integrator (quoting it would have been drift
inside the note whose purpose is comparability, which is why the note says so
explicitly). The **two earth radii** are a duplication defect, not a claim
unsupported by a source, so they belong to the M4 corollary and not to this
class. `geometry.py`'s containment note is likewise not counted: G.2 made it
false in commit 1 and fixed it in commit 2, so it never outlived its source
across tasks — though its FUNCTION docstring three lines below **was** missed
and is now BACKLOG §3 residue.

**The M4 survivor got a corollary, not an inventory row** ("a guard on the
wrapper is not a guard on the value"), after checking it against both
candidate classes: it is not the unreachable-check sub-pattern (nothing
refused first) and not fixture degeneracy (no fixture, no coinciding
statistics). One instance; every row in that table opened with at least two.

**The LITERATURE-observer deadline had already expired** — at G.3
(2026-08-24), one day *before* the AOI arrival the entry itself predicted, and
missed at that approval. Re-measured here: deleting the branch still fails
**0 of 703**, because the branch fires only on a MISSING citation and all five
LITERATURE subjects have one. Adding well-formed members can never close it.
