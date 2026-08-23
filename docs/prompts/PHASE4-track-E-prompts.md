PHASE 4 — TRACK E PROMPTS (E4.0 preflight, E4.1, E4.2, E4.3)

Track G delivers nothing here. Per the two-track architecture that changes
the sequencing not at all: Contract 4's values are slots with declared
defaults and an existing watermark marker, and Track E builds against the
shape.

FOUR NOTES BEFORE THE FIRST PASTE, all verifiable:

  (i)   PHASE 4 CARRIES **TWO** WATERMARKS, NOT ONE. Phases 2–3 were
        non-scientific because the DEM is synthetic. Phase 4 adds a second,
        independent reason: the economic parameters are placeholders
        (Contract 4's illustrative_only). These are different claims with
        different expiry conditions — Checkpoint 1 lifts the first,
        Checkpoint 4 the second — and a single "non-scientific" flag would
        collapse them. This is the phase's central design problem.
  (ii)  E4.3 IS ALMOST CERTAINLY ASSEMBLY. E3.4 built the emitter, the chain
        assertion, the surface identity block, and the claim verdict.
        RunManifest already has an economic field per the Phase-0 shape —
        verify. Its size is a tripwire, as E2.5's and E3.4's were.
  (iii) EVERY PHASE-4 OUTPUT IS DOWNSTREAM OF A SURFACE THAT IS THE TRAINING
        MEAN OVER 99% OF ITS DOMAIN. A minable-footprint map derived from it
        is a map of where a nearly-constant surface crosses a placeholder
        cutoff. That is not a defect to fix; it is the honest output, and it
        must be stated in advance so §E4.2 cannot report it as a finding.
  (iv)  E2.5's GUARD ALREADY REFUSES. Adding an economics layer does not
        change that and must not be allowed to look like it does.

════════════════════════════════════════════════════════════════════════════
E4.0 — PHASE-4 PREFLIGHT (read-only; ends in a report and two decisions)
════════════════════════════════════════════════════════════════════════════

Read-only. No code, no commit, no file edits. Report and stop.

Read CLAUDE.md, docs/BACKLOG.md, docs/PATTERNS.md, the E3.4 and HASH.1
walkthroughs, and Contract 4 (data/economics/scenarios.yaml) in full. Run the
suite and report the count.

§1 — CONTRACT 4 AS IT ACTUALLY IS. Report its structure field by field: what
scenarios exist, which values are placeholders, where illustrative_only sits
and what reads it today, and what the [GEOLOGY — ISAAC] tags ask for. Do NOT
work from the lane list's summary ("grade units, metal weights, market
cutoff, strategic cutoff, exclusions, caveats") — verify what the file
contains, and report any of those the contract does NOT have a slot for.
Each missing slot is a contract decision for Karl, not something to invent.

§2 — THE PHASE-0 SEAMS. EconomicModel is a Phase-0 ABC with zero
implementations, the same shape SampleSource and Estimator were. Report its
signature, whether engine.py already sequences it, what RunManifest's
economic field looks like, and whether any of it can express what E4.1–E4.3
need. If a Phase-0 revision is required, that is the 2B protocol again —
report it now rather than discovering it in E4.1.

§3 — THE TWO-WATERMARK PROBLEM. This is the decision Karl must make, so
report the options with their costs rather than choosing:

  The origin machinery derives non-scientific status from the computed
  origin. Contract 4's placeholders are AUTHORED. So an economic artifact's
  computed origin is AUTHORED regardless of the DEM — which is CORRECT but
  LOSSY: it says "not scientific" without saying that there are two
  independent reasons, that they lift at different checkpoints, and that
  fixing one leaves the other.

  Report at least: (a) whether the origin lattice can express this already
  (does combine_origins over {SYNTHETIC, AUTHORED} lose information a reader
  needs?); (b) what a separate per-reason record would cost, and whether it
  duplicates the origin or complements it; (c) how E2.5's verdict already
  handles multiple independent refusal reasons — it names each failing
  precondition rather than emitting one boolean, which may be the precedent
  to follow rather than a new mechanism.

§4 — WHAT A MINABLE FOOTPRINT IS, MECHANICALLY. Before E4.2 exists: state
what the computation actually is (a threshold on the prediction surface?
abundance × grade × recovery against a cutoff? something Contract 4
specifies?), and what it needs that does not exist. Specifically: is there
any GRADE data in the corpus to combine with abundance? The evidence-class
discipline says GRADE joins to stations and feeds economics — report whether
any GRADE rows exist today (my reading is zero, since [19] was never wired),
and if so what E4.2 can compute without them. A footprint computed from
abundance alone under an abundance cutoff is a different thing from one
computed from contained metal value; say which Contract 4 asks for.

§5 — THE UNCERTAINTY QUESTION, which the lane list does not mention. Every
prediction carries a paired uncertainty. A minable-footprint map that
thresholds only the mean discards it, and produces a hard boundary on a
surface whose uncertainty is at its far-field ceiling over 99% of the
domain. Report the options — a footprint at the mean, a probability-of-
exceeding-cutoff surface, or footprints at stated confidence levels — with
what each costs and what each would claim. Recommend one; Karl decides.

§6 — TRIPWIRE. Inventory what E4.3 must add against what the manifest
already carries. Report assembly vs new. If the new part exceeds an
economics block and its tests, STOP and say what leaked.

Report all six and STOP. Two decisions will be Karl's: the two-watermark
representation (§3) and the uncertainty treatment (§5).

════════════════════════════════════════════════════════════════════════════
E4.1 — EconomicModel READING CONTRACT 4 (two commits)
════════════════════════════════════════════════════════════════════════════

Adversarial review on COMMIT 2.

── COMMIT 1: THE LOADER AND THE MARKER ──

Implement the EXISTING EconomicModel ABC — do not define a parallel
interface; the seam exists, fill it. If §2 found it cannot express what is
needed, apply the 2B revision protocol: before/after shapes, stale-reference
sweep, recorded in the walkthrough.

Read Contract 4 through a loader beside the Contract 8 one, reusing the same
repo-root finder. THE THREE-STATE ACCESSOR POSTURE APPLIES (C8.1, and E3.3's
digitization_uncertainty): a field that is ABSENT, a field that is NULL, and
a field that is POPULATED are three different states with three different
remedies. Absent raises naming the structural gap; null raises naming the
unfilled value; populated returns the value AND its declared origin
together, so a consumer asks "what is the cutoff, and is it a finding or a
stand-in?" in one call.

illustrative_only is the marker Contract 4 already has. Do NOT build a
second one. Report what reads it today and wire the model to it — but note
that under the origin machinery the watermark should DERIVE from the
computed origin (P2.0d-3), so illustrative_only may be redundant with
data_origin: AUTHORED. Report which is authoritative and whether one should
subsume the other; if they can disagree, that is two sources of truth for
one fact and the answer is not "keep both."

TWO SCENARIOS (market + strategic) as the lane list specifies, both on
placeholder values. Their DIFFERENCE is the point of having two — state in
the code what the two are meant to bracket.

── COMMIT 2: THE COMPUTATION (adversarial review) ──

Per §4's finding. Whatever the computation is, it is a function of the
prediction surface, Contract 4's parameters, and — if GRADE exists — grade.
If GRADE does not exist, the model computes what abundance alone supports
and REFUSES BY NAME what it cannot, rather than assuming a grade.

Per §5's decision: the uncertainty treatment Karl chose, implemented as
chosen, with the alternatives recorded in the code as considered-and-
declined.

MANDATORY, stated in advance so it cannot be reported as a finding: the
economic output over 99% of the domain is a function of a nearly-constant
prediction surface against a placeholder cutoff. Report what fraction of the
domain the footprint covers, and note that the number is a property of the
cutoff's relation to the training mean, not of the seafloor. If the
footprint is all-or-nothing over the domain, that is the expected result.

Tests: known-answer on hand-computed parameters (not "output is not null");
the three accessor states, each by name; a refusal when a required parameter
is null; scenarios differ where Contract 4 says they should; determinism;
the computed origin is AUTHORED and derived, never declared.

════════════════════════════════════════════════════════════════════════════
E4.2 — MINABLE-FOOTPRINT RASTERS + SCENARIO DIFFERENCE MAP (two commits)
════════════════════════════════════════════════════════════════════════════

── COMMIT 1: THE FOOTPRINT RASTERS ──

Write per-scenario footprint rasters on the SAME grid as the prediction
surfaces — same extent, cell size, transform, mask. No resampling; a
footprint on a different grid than the surface it thresholds would need
interpolation, and E3.1+2 took care not to introduce any.

Reuse E3.1+2's COG writer and its watermark carriers. Do NOT build a second
writer. The E3.0 §3 decision still holds: GDAL COG driver, assert what
rasterio can observe, claim NO COG-ness.

THE WATERMARK NOW CARRIES TWO REASONS (§3's decision). Whatever
representation Karl chose, each footprint raster must carry BOTH — the
synthetic-DEM reason and the placeholder-economics reason — in a form where
lifting one does not silently lift the other. Mutation-verify: satisfy one
reason in a fixture, confirm the other survives and a test catches a
collapse to a single flag.

── COMMIT 2: THE SCENARIO DIFFERENCE MAP ──

The market-vs-strategic difference, on the same grid. State what the map
MEANS: it is the area whose minability depends on which placeholder cutoff
is assumed, which is a sensitivity map, not a resource map. That distinction
belongs in the raster's tags and the walkthrough, not only in prose.

Report its area as a fraction of the domain. If the two scenarios produce
identical footprints, say so plainly — that would mean the placeholder
cutoffs do not bracket anything, which is a finding about Contract 4's
placeholders and worth a BACKLOG entry for G4.1.

Tests: both footprints and the difference share the surface's grid identity
exactly; the difference is the set difference of the two, verified
independently; the two-reason watermark on every written file; round-trip.

════════════════════════════════════════════════════════════════════════════
E4.3 — MANIFEST INTEGRATION (one commit; assembly per §6)
════════════════════════════════════════════════════════════════════════════

Extend the manifest with the economics block: the scenarios used, their
parameter values AND declared origins, the footprint rasters' identity
(hash, grid, area fraction), the difference map's identity and area, and the
two-reason watermark state.

THE CHAIN EXTENDS: corpus → stack → matrix → run → surfaces → footprints,
every link verified by RECOMPUTATION. HASH.1 made this path-independent —
verify that the new artifacts inherit that property, and report the
path-dependent count (it should still be zero; if the economics block
reintroduces a path, that is the E3.4 lesson recurring and it must be caught
by measuring in two trees, not by reading).

E2.5's verdict is unchanged by this phase and must be seen to be: adding
economics does not add a precondition and does not lift one. Assert the
verdict's failing set is identical before and after the economics block
exists. If it moves, STOP.

Confirm the shape-tolerant hashing from HASH.1 means this addition does NOT
re-stamp history — that is the property it was built for, and this is its
first real use. Report the committed artifacts' hashes before and after.

Tests: the manifest reproduces in a second tree; the chain recomputes; a
missing footprint fails BY NAME; the economics block's origins are computed;
the claim verdict is unchanged.

CLOSING PHASE 4 TRACK E:
  · Walkthrough with the footprint fractions, the scenario-difference area,
    and both watermark reasons stated as separate claims with separate
    expiry conditions.
  · What Checkpoint 4 can and cannot review.
  · BACKLOG: anything a premise check surfaced; any trigger that FIRED with
    this phase; and G4.1's ask sharpened by what E4.1 found missing in
    Contract 4.
  · Suite trajectory and final count.

Stop for review before Checkpoint 4.
