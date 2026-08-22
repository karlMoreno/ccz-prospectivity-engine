PHASE 3 — TRACK E PROMPTS (E3.0 preflight, E3.1+2, E3.3, E3.4)

Track G is not delivering soon. Per the two-track architecture, that changes
nothing about sequencing: every Track-G value is a contract slot with a
declared default, and Track E builds against the shape. Where a Phase-3 task
appears to need a Track-G value, the prompt below says which slot holds it
and what the default is.

FOUR STRUCTURAL NOTES, all verifiable and all worth knowing before the first
paste:

  (i)  E3.1 and E3.2 ARE ONE OPERATION. The Estimator ABC's predict()
       returns (mu, sd) as a structurally inseparable pair —
       __init_subclass__ refuses an override, and the Template Method
       validates the pairing. A task that produces a prediction surface
       without its uncertainty surface would have to fight the interface to
       do it. They are merged below.
  (ii) E3.4 IS MOSTLY ALREADY BUILT. E2.4 emitted a RunManifest carrying
       fold assignment, per-fold per-estimator scores, both estimators'
       reportable state, and the chained upstream hashes. The lane list was
       written before that existed. E3.4 is therefore an EXTENSION, and its
       size is a tripwire.
  (iii) THE AOI DOES NOT BLOCK PHASE 3 — see E3.0 §2.
  (iv) THE TS-6 AGREEMENT NUMBER IS MEANINGLESS TODAY and the machinery is
       still worth building — same posture as E2.4's synthetic-covariate
       scores. Stated in advance so §3 cannot report it as a finding.

### E3.0 RUN AND APPROVED — TWO DECISIONS, TWO CORRECTIONS (Karl, 2026-08-20)

E3.0 was executed read-only against `4e77d2f` (suite 471 passed / 2 skipped)
and approved. What it settled, recorded here because a later reader meets this
spec before it meets the report:

  DECISION 1 — COG. Write with the GDAL COG driver (present: GDAL 3.9.2,
    rasterio 1.4.1 — NO dependency needed). Assert only what rasterio can
    observe: driver, tiled, block_shapes, overviews, CRS, transform, dtype,
    nodata. DO NOT claim COG-ness in the manifest or the tags. Measured
    reason: at the 100x34 grid the payload is 13.3 KiB — smaller than ONE
    512x512 float32 block (1 MiB) — the driver generates NO overviews at that
    size (probed: [] vs [2, 4] at 2048x2048), and nothing installed can
    validate the IFD/byte-layout property that actually makes a GeoTIFF
    cloud-optimized (rio_cogeo, osgeo.gdal, validate_cloud_optimized_geotiff
    all unimportable). A native test would verify STRUCTURE without verifying
    the PROPERTY, so claiming COG-ness would be a claim with a partial
    observer. Revisit at Checkpoint 1 (BACKLOG §3).

  DECISION 2 — E3.3's correlation. Report descriptive r with N_eff printed
    BESIDE it, and NO p-value. At N_eff ~ 2 no significance test is
    meaningful, and a corrected test (Clifford-Richardson / Dutilleul) would
    turn p < 0.001 into p ~ 0.6 — more honest inference over the same
    emptiness. THE LIMIT, stated in the entry and required in the output: a
    correction adjusts DEGREES OF FREEDOM; it cannot manufacture information.
    The real problem is that one surface is constant over 99% of its domain.

  CORRECTION 1 — THE CHANNEL COUNT IS FOUR, NOT FIVE. Fixed in §4(a) below.
    `E2.3.md`'s "saturation finding" table names THREE channels — predictions
    (the 0.348 ceiling), importances (rank-4), uncertainties (the zero-width
    mechanism). No fourth exists anywhere in the record. The surface is the
    FOURTH channel. The zero-width mechanism IS the uncertainties channel, not
    a separate one.

  CORRECTION 2 — THE EXTENT IS A FIXTURE'S, NOT A CONFIGURED DOMAIN'S. Fixed
    in §2 and in E3.1+2 COMMIT 1 below. The domain-of-definition argument
    HOLDS; what does not hold is any implication that a production extent is
    configured somewhere. THERE IS NO PRODUCTION EXTENT CONFIGURATION IN THE
    REPO. The extent is a property of whatever DEM is handed to the run, and
    today the only DEM is `tests/fixtures/rasters.py`.

  ALSO CORRECTED, and it was Track E's error rather than Karl's: the E3.0
    report called this file "the tracked spec". IT WAS UNTRACKED — present on
    one disk, absent from the repo, and therefore outside the INSTRUCTIONS
    provenance channel (P2.PRE: "tracked prompts and handoffs — the
    instruction record lives in the repo"). It is committed as of this
    revision, which is what makes the corrections above a record rather than
    a local edit.

════════════════════════════════════════════════════════════════════════════
E3.0 — PHASE-3 PREFLIGHT (read-only; ends in a report and two decisions)
════════════════════════════════════════════════════════════════════════════

Read-only. No code, no commit, no file edits. Report and stop.

Read CLAUDE.md, docs/BACKLOG.md, docs/PATTERNS.md, the E2.4/E2.5/C8.1
walkthroughs, and Contract 6 (data/ts6/ts6_reference.yaml) first. Run the
suite and report the count.

§1 — THE E3.4 TRIPWIRE. Inventory what the RunManifest already carries
against what E3.4 must add (a TS-6 agreement block, and whatever the
surfaces need). Report: what is assembly, what is genuinely new. If the new
part exceeds an agreement block and its tests, STOP and say what leaked —
the SIZE of E3.4 is a diagnostic, exactly as E2.5's was.

§2 — THE AOI, WHICH IS NOT A BLOCKER TODAY. [REVISED 2026-08-20 after E3.0
verified it: the conclusion HOLDS and one premise was overstated. There is NO
PRODUCTION EXTENT CONFIGURATION anywhere in the repo. "The feature stack,
whose extent E1.4's preflight set to the corpus bbox + 0.5°" describes a TEST
FIXTURE (`tests/fixtures/rasters.py`: WEST -126.5, NORTH 14.7, 0.1 deg, 100 x
34 -> lon [-126.5, -116.5], lat [11.3, 14.7], 3,400 cells, ~1,085 x 376 km).
The extent is a property of whatever DEM is handed to the run. E3.0 also
confirmed (c) more strongly than stated: `FixtureTerrainSource.load()` ACCEPTS
the study_area argument and DISCARDS it — nothing clips on the AOI at all.]
Verify this argument against the
repo rather than accepting it:

  A prediction surface can only exist where its inputs exist. RF needs all
  eight covariates at every predicted cell; those live in the feature stack,
  whose extent E1.4's preflight set to the corpus bbox + 0.5°. Outside that
  extent the covariates are not extrapolated — they are UNDEFINED. So the
  alpha's prediction domain is the stack's extent, and that is a
  domain-of-definition fact, not a geology decision.

  Confirm: (a) the stack's extent and cell size; (b) that the Phase-0
  placeholder AOI excludes 100% of the corpus and therefore cannot be the
  prediction domain; (c) that nothing currently filters on the AOI. Then
  state the consequence: the AOI becomes a REAL decision at Checkpoint 1,
  when real GEBCO is global and the stack stops bounding anything. Report
  whether the BACKLOG's AOI entry carries that trigger; if it says "blocks
  prediction surfaces," that is now wrong and needs the contract-slot
  framing.

§3 — THE COG QUESTION. Determine what the installed GDAL/rasterio can write
natively — GDAL ≥ 3.1 exposes a COG driver, in which case no dependency is
needed. Report the version, what the driver produces, and how COG-ness would
be VALIDATED (a written file that is not actually a valid COG is a claim
without an observer). If validation needs a dependency, report it as a
dependency decision with the same evidence the QRF decision got: maintenance
state, transitive deps, license, lockfile delta. Do not add anything.

§4 — TWO PREDICTIONS TO PUT ON RECORD BEFORE ANY SURFACE EXISTS, so §3 of
E3.1+2 cannot report them as findings. Verify each is entailed rather than
guessed, and state the reasoning:

  (a) RF'S SURFACE WILL BE BLOCKY. It was trained on FOUR distinct X rows
      (E2.0-3). A forest partitions on the splits those rows admit, so its
      predicted surface over the full grid takes a small number of distinct
      values. Predict roughly how many and why. This is the saturation
      finding's FOURTH channel — after the 0.348 ceiling (predictions),
      rank-4 importance (importances), and the zero-width mechanism
      (uncertainties). [CORRECTED 2026-08-20: this read "FIFTH". E2.3's
      table names THREE channels and the zero-width mechanism is the
      uncertainties channel, not a fourth one.]
  (b) KRIGING'S SURFACE WILL BE MOSTLY THE MEAN. Fitted range ~22 km at the
      candidate ceiling; the stack extent spans ~1,000 km. So beyond a few
      tens of km from the two clusters, predictions revert to the training
      mean with variance ≈ sill + the Lagrange term. Estimate what FRACTION
      of the domain is effectively "no information" — that number is the
      honest headline of the whole phase, and it should be computed from
      the geometry, not eyeballed off a map.

§5 — THE SPATIAL-CORRELATION TRAP (E3.3's central statistical problem).
Report, do not solve:

  A correlation between two spatially autocorrelated surfaces is INFLATED,
  because the effective number of independent observations is far smaller
  than the number of cells. This is the same phenomenon this project already
  measured in another costume — random k-fold's inflation over spatial CV —
  and it will be much larger here, since both surfaces are smooth by
  construction.

  Report: how many cells the common grid would have; what the effective
  sample size might plausibly be given the fitted range; what corrections
  exist (Clifford–Richardson / Dutilleul modified tests are the standard
  references — VERIFY what is actually available in the installed stack
  rather than assuming) and what each would cost. Recommend an approach for
  E3.3 and say what it does not fix.

§6 — TWO LITERATURE-CLASS ARRIVALS. Both the AOI polygon and the digitized
TS-6 raster arrive as LITERATURE-class values (a citation, no file we
hashed). The BACKLOG records that LITERATURE's evidence check has ZERO
observers — deleting it fails 0 of 471. Confirm that is still true, and
state plainly that Phase 3's two Track-G deliverables are both in the class
whose check nothing exercises. This raises its trigger's urgency; report
it, do not fix it.

Report all six sections and STOP. Two decisions will be Karl's: the COG
approach if a dependency is implicated, and the E3.3 correlation approach.

════════════════════════════════════════════════════════════════════════════
E3.1+2 — PREDICTION AND UNCERTAINTY SURFACES (merged; three commits)
════════════════════════════════════════════════════════════════════════════

The lane list splits these; the interface does not. predict() returns
(mu, sd) as an inseparable pair, so one call produces both surfaces and
splitting the task would invite emitting one without the other. Merged, with
the merge recorded in the walkthrough.

Adversarial review on COMMIT 2 — the surface builder is where every
downstream number comes from.

── COMMIT 1: THE GRID AND THE DOMAIN ──

**THREE STRUCTURAL FACTS E3.0 §1 SURFACED. THEY BELONG TO THIS COMMIT, NOT TO
E3.4** (E3.4 is assembly: `ts6_agreement` and `output_hashes` are existing
`RunManifest` fields, `TS6Agreement` already matches Contract 6's three
metrics + role_note, and `finalize()` is idempotent so re-stamping folds the
block into the content hash):

  1. THERE IS NO GRID CONSTRUCTION ANYWHERE IN `engine/`. `_fit_predict`
     (`engine.py:145-154`) predicts at the 35 TRAINING locations via
     `route(estimator, matrix)` — not on a grid. This commit introduces the
     first grid the engine has ever had.
  2. `_compare_to_ts6` PASSES A TYPE MISMATCH that is currently masked by
     `NotImplementedError`: it hands `dict[str, tuple[mu, sd]]` to
     `compare_to_ts6(prediction: PredictionSurface, ...)`. Something must
     reconcile the two before E3.3 can run; deciding it here is cheaper than
     discovering it there.
  3. NOTHING WRITES A RASTER. `PredictionSurface.raster_path` has no producer.

**THE EXTENT IS A FIXTURE'S** (E3.0 §2, corrected 2026-08-20). There is no
production extent configuration; the grid inherits whatever DEM the run is
given. Say so in the code comment rather than implying a configured domain —
today that DEM is `tests/fixtures/rasters.py`, 100 x 34 @ 0.1 deg.

**THE COG DECISION APPLIES TO THIS COMMIT'S WRITER** (Karl, 2026-08-20): GDAL
COG driver, no dependency; assert driver / tiled / block_shapes / overviews /
CRS / transform / dtype / nodata; claim NO COG-ness anywhere in the manifest
or the tags. At 3,400 cells the driver emits no overviews and the payload is
13.3 KiB.

**THE TWO HEADLINE NUMBERS, ENTAILED BEFORE ANY SURFACE EXISTS** — E3.1+2
MEASURES these, it does not discover them, and §3 of its walkthrough must
report them as confirmations:

  (a) KRIGING IS THE TRAINING MEAN OVER 99% OF ITS OWN DOMAIN. Computed from
      geometry over the 3,400 grid-cell centres against the 35 stations:
      distance to the nearest station is min 0.59 km, MEDIAN 277.2 km, max
      524.6 km. **99.00% of cells (3,366/3,400) lie beyond one fitted range
      (21.6 km); 99.62% lie beyond 13 km, the largest lag with ANY empirical
      support; only 34 cells lie within one range of any datum.** The fitted
      range is itself unidentified — `range_at_candidate_ceiling=True`, 1.8x
      beyond the largest observed lag, inside a 974 km window containing zero
      pairs.
  (b) RF'S SURFACE IS BOUNDED BY ARITHMETIC. Four distinct training X rows
      with cell means 21.657 / 15.143 / 20.229 / 20.314; every tree has at
      most 4 leaves and every forest prediction is a weighted average of those
      four. **Every value on the RF surface lies in [15.143, 21.657]; dynamic
      range <= 6.514 kg/m^2, regardless of what the covariates do.** THREE OF
      THE FOUR MEANS ARE WITHIN 1.5 kg/m^2 OF EACH OTHER, so expect a
      near-flat surface at ~20-21 with one low region at ~15, in a small
      number of plateaus (order 10^0-10^1) with axis-parallel boundaries.

Define the prediction grid as the feature stack's own grid — same extent,
same cell size, same transform. Rationale in the code: predicting on the
covariates' native grid means NO RESAMPLING of covariates, so the surface
inherits the stack's provenance exactly and no interpolation is introduced
between the recorded values and the predicted ones. Record the grid's
identity (extent, cell size, CRS, the stack's DEM hash) as data.

Then a domain mask: cells where ANY covariate is NaN (the nan_border, per
E2.0-2) are NOT predicted. They are masked as undefined and COUNTED, not
zero-filled and not imputed — the same flag-never-drop rule the matrix
refuses on. Report the masked-cell count.

Tests: grid identity matches the stack's; the mask matches the stack's NaN
union exactly; determinism.

── COMMIT 2: THE SURFACE BUILDER (adversarial review) ──

For each estimator in the registry — ITERATE names(), never cherry-pick,
the E2.4 obligation still binds — fit on the full training matrix and
predict over every unmasked grid cell, producing a (mu, sd) pair per cell.

INPUT ROUTING IS A DECLARATION: read input_kind from the estimator (C8.1's
mechanism), route coordinates to kriging and covariates to RF, and never
match on name. A registered estimator lacking the declaration fails BY NAME.

MEMORY AND SCALE: the grid may be large. Report the cell count before
building. If a whole-grid predict is impractical, chunk it — and prove the
chunking is a no-op by asserting a chunked build is byte-identical to an
unchunked build on a small fixture. A chunk boundary that changes a
prediction is a defect this test exists to catch.

THE PREDICTIONS FROM E3.0 §4 ARE NOW MEASURABLE. Report:
  · the number of DISTINCT values in RF's surface (§4a's blockiness,
    measured);
  · the fraction of the domain where kriging's |prediction − training mean|
    is below a stated epsilon, and where its variance is within a stated
    epsilon of sill + Lagrange (§4b's "no information" fraction, measured).
If either deviates from E3.0's reasoning, STOP and investigate — a
prediction derived from geometry that the surface contradicts is a bug until
proven otherwise.

Every surface value carries its paired uncertainty by construction; assert
that no (mu, sd) pair is ever emitted with sd absent, non-finite, or
negative. The zero-width mechanism from E2.3 applies here too: COUNT sd == 0
cells and report them; do not floor them.

── COMMIT 3: THE COG WRITER AND THE WATERMARK ──

Write each surface as a COG per E3.0 §3's decision, with a validation test
that the written file IS a valid COG — not merely that a file was written.

THE WATERMARK PROBLEM, which is new here: a GeoTIFF cannot carry a visible
stamp the way plot_stack's PNG does. So the non-scientific status must live
where a consumer will actually meet it. Implement ALL of:
  · the computed origin (SYNTHETIC today, derived via combine_origins —
    never declared by hand) written into the GeoTIFF's metadata tags,
    alongside the watermark string;
  · a provenance sidecar beside the file, per the established pattern;
  · and — the load-bearing one — E2.5's guard CONSULTED at write time. If
    the claim is not eligible, the surface is still written (building on
    fixtures is legitimate) but written as NON-PUBLISHABLE, with the
    refusal's failing preconditions recorded in the tags. Publishing from
    fixtures is what the guard exists to prevent, and wiring it here is what
    makes it load-bearing rather than a thing that only runs in tests.

Today the guard REFUSES. That is the expected output; do not reach for
anything to make it pass.

Tests: the written COG validates; the origin tag is COMPUTED not declared
(mutation: declare it MEASURED in a fixture, confirm the watermark
disappears and the test catches the laundering); an ineligible claim
produces a marked non-publishable file rather than an unmarked one or an
exception; round-trip — reading the COG back gives the same values,
georeferencing, and mask.

Mutation-verify each of the three watermark carriers separately: removing
any one must fail a test BY NAME. A watermark with one carrier is one
deletion from silence.

Walkthrough, mutation table, suite trajectory per commit. Stop for review.

════════════════════════════════════════════════════════════════════════════
E3.3 — compare_to_ts6() (two commits)
════════════════════════════════════════════════════════════════════════════

STATE FIRST, in the walkthrough, before any number: the TS-6 raster is a
SYNTHETIC FIXTURE. [18] was removed as fabricated and the production guard
refuses it; the real digitized surface is Track G's G3.1 and arrives at
Checkpoint 3. Therefore today's agreement number MEASURES NOTHING about
TS-6 — it exercises the comparison machinery. Same posture as E2.4's
synthetic-covariate scores, and stated in advance so it cannot be reported
as a finding.

**KARL'S DECISION ON THE CORRELATION (2026-08-20, from E3.0 §5): DESCRIPTIVE
r WITH N_eff PRINTED BESIDE IT, AND NO p-VALUE.** The reasoning belongs in the
entry AND in the emitted output, not only here:

  * A correlation over the common grid would carry df ~ 3,398 on 3,400 cells.
    That df is fiction — both surfaces are smooth by construction, so the
    effective number of independent observations is far smaller.
  * A geometric bound gives N_eff ~ 278 IF the surface varied everywhere. It
    does not: kriging is constant over 99% of the domain, the ~34 cells
    carrying any signal fall in TWO clusters, so **N_eff ~ 2**. For RF, N_eff
    is bounded by the handful of plateaus.
  * At N_eff ~ 2 no significance test is meaningful. A corrected test
    (Clifford-Richardson 1989 / Dutilleul 1993 — both hand-implementable over
    numpy; scipy 1.17.1 is present but is a TRANSITIVE dep via scikit-learn,
    not a declared one; statsmodels / esda / libpysal are NOT installed) would
    turn p < 0.001 into p ~ 0.6: more honest inference over the same
    emptiness.
  * **THE LIMIT, required in the output next to the number: a correction
    adjusts DEGREES OF FREEDOM; it cannot manufacture information. The real
    problem is that one surface is constant over 99% of its domain, and no
    test corrects for that.**

This is the same phenomenon the project already measured in another costume —
random k-fold's inflation over spatial CV, where the DIRECTION held 40/40 —
and it is larger here because both surfaces are smooth rather than merely
autocorrelated.

**BEFORE E3.3 RUNS, NOT DURING IT: decide TS-6's ORIGIN CLASS** (BACKLOG §1).
Contract 6 currently offers fields matching all three evidence shapes at once
and decides none of them.

── COMMIT 1: RESAMPLING TO A COMMON GRID ──

Both surfaces must reach one grid. Decide and record: which grid (ours,
TS-6's, or a third), which resampling method, and why. The constraint that
should drive it: resampling OUR surface introduces interpolation into
values we just took care not to interpolate — so resampling TS-6 onto our
grid is the honest default. State it, and state what it costs (TS-6 is a
compiled coarse product; upsampling it invents detail it does not have —
record that in the comparison's provenance rather than hiding it).

GRID is a benchmark class, never a training station (Contract 1's evidence
discipline). Assert that the comparison path cannot feed the corpus — a
test, not a comment.

── COMMIT 2: AGREEMENT, WITH ITS INFLATION DECLARED ──

Compute agreement as the lane list specifies: spatial correlation + mean
difference. AND — per E3.0 §5, per Karl's decision — report the effective
sample size or the correction alongside the naive correlation. A naive
correlation between two smooth surfaces over N cells is inflated by exactly
the phenomenon this project measured as random-k-fold leakage; reporting it
bare would be the same error in a new costume.

Report at minimum: the naive correlation, the cell count, the effective
sample size under the chosen method, and the correlation's interpretation
under that effective n. If the effective n is small enough that the
correlation is not distinguishable from zero, SAY SO — that is the honest
output and it is the likely one, given that kriging's surface is mostly
constant.

Also report the mean difference and its sign, which is interpretable
regardless of the correlation problem.

role_note (Contract 6): benchmark_only vs reproduction_check is the
CIRCULARITY marker — whether our covariates derive from the same proxies
TS-6 used. Today Option-A terrain-only covariates make benchmark_only the
defensible default; record it as the declared default with its [GEOLOGY —
ISAAC] tag, and make the comparison REFUSE to run under a null role_note
rather than assuming. Track G's G3.2 fills the acceptable-agreement
question; that slot stays null and the comparison reports rather than
judges.

Tests: known-answer — two identical surfaces correlate 1.0 with zero mean
difference; a surface and its negation correlate −1.0; a constant surface
against anything produces the degenerate case handled by name (kriging's
surface is nearly constant, so this is not hypothetical). Fixture docstrings
state which neighboring claim each separates, per the degeneracy rule.

Walkthrough, mutations, stop for review.

════════════════════════════════════════════════════════════════════════════
E3.4 — THE MANIFEST EMITTER (extension; one or two commits)
════════════════════════════════════════════════════════════════════════════

Scoped by E3.0 §1's tripwire inventory. E2.4 already emits a RunManifest
with fold assignment, per-fold per-estimator scores, both estimators'
reportable state, and the chained upstream hashes. This task EXTENDS it.

What it adds: the surface artifacts' identity (each COG's hash, its grid,
its masked-cell count, its origin), the TS-6 agreement block (with the
effective-n and the role_note), and E2.5's claim verdict — the failing
preconditions, named, as data rather than prose.

THE CHAIN MUST BE ASSERTED, not recorded: corpus hash → feature stack →
training matrix → run → surfaces, each verified against the actual artifact
by recomputation, not by reading a literal. Note the known limit from the
audit — of three upstream hashes only the corpus is verifiable off-machine,
because the stack manifest embeds a caller-supplied path (BACKLOG, trigger
before Checkpoint 1). State that limit in the emitter's own output rather
than only in a doc; a chain that claims more than it delivers is the defect
that entry exists to fix.

Tests: the manifest reproduces byte-identically across two runs apart from
the excluded timestamp fields; every recorded hash matches its artifact by
recomputation; a missing surface fails BY NAME; the claim verdict's failing
set matches E2.5's guard run directly.

CLOSING PHASE 3 TRACK E:
  · A phase walkthrough with the measured versions of E3.0 §4's two
    predictions — RF's distinct-value count and kriging's no-information
    fraction — as the phase's headline findings.
  · Confirm what Checkpoint 3 can and cannot review, given that TS-6 is
    still a fixture and no acceptance threshold exists.
  · BACKLOG: the AOI's trigger moved to Checkpoint 1; the LITERATURE
    observer gap now has two Phase-3 arrivals riding on it; anything a
    premise check surfaced, entered at the moment of deferral.
  · Suite trajectory and the final count.

Stop for review before Checkpoint 3.
