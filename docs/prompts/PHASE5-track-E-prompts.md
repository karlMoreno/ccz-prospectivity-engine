PHASE 5 — TRACK E PROMPTS (E5.0 through E5.7)

Run one at a time. Adversarial review on E5.1, E5.3 and E5.4 — the API is the
seam everything reads, the viewer is the first artifact a human meets, and the
honesty surface is what makes the second defensible.

FOUR NOTES BEFORE THE FIRST PASTE:

  (i)   THE PHASE-3 AND PHASE-4 PROMPT FILES ARE UNTRACKED. Two phases have
        run against on-disk prompts outside the INSTRUCTIONS channel, and both
        times a session called one "tracked" after checking with `ls` rather
        than `git`. Check this file's tracking state before deferring to any
        on-disk copy.
  (ii)  THIS PHASE ADDS THE FIRST NON-PYTHON CODE to the repo. That is a
        stack decision Karl has made — MapLibre GL JS + deck.gl from CDN, no
        npm, no build step. If any task finds a build step unavoidable, STOP:
        that is a stack decision, not an implementation detail.
  (iii) THE TRIPWIRE PATTERN HOLDS. E2.5, E3.4 and E4.3 were each scoped as
        assembly and were. E5.6 is partly built already. Inventory before
        building; if the new part exceeds the stated shape, STOP and say what
        leaked.
  (iv)  E2.5's GUARD REFUSES TODAY, for three independent reasons. No Phase-5
        task adds a precondition or lifts one. Any task touching the manifest
        asserts the failing AND passing sets unchanged.

════════════════════════════════════════════════════════════════════════════
E5.0 — PREFLIGHT (read-only; ends in a report and two decisions)
════════════════════════════════════════════════════════════════════════════

Read-only. No code, no commit, no file edits. Report and stop.

Read CLAUDE.md, docs/BACKLOG.md, docs/PATTERNS.md, and the E3.1-2, E4.2, E4.3
and HASH.1 walkthroughs. Run the suite IN THE FOREGROUND and report the count
— a background run produced an empty output file with exit 0 once, which is
indistinguishable from a run with nothing to say.

§1 — THE CONTROL-AXIS INVENTORY. Enumerate what the viewer can switch
between, FROM THE ARTIFACTS THAT EXIST ON DISK, not from the lane list's
description. Report the true cross-product of layer type × estimator ×
z-level × scenario, and name every combination that does NOT have an
artifact. A control offering a state with no artifact is a broken promise in
the UI, and the disabled-vs-absent decision in E5.3 depends on this count.

§2 — THE SERVING DECISION [KARL — DECIDE]. Measure, do not estimate: the byte
size of one prediction surface exported as GeoJSON at 3,400 cells, and the
projected size for all layers together. Then project the Checkpoint-1 case —
real GEBCO at ~460 m over the same region. Report where the client-side
threshold plausibly sits, what the tile path would cost, and whether TiTiler
is compatible with the pinned FastAPI/GDAL versions. Recommend; Karl decides.

§3 — WHAT THE API MUST EXPOSE. E5.1's catalog is what the viewer reads.
Report what the manifest ALREADY carries that the viewer needs — E4.2's
association record, the surfaces' identity, the claim verdict, the watermark
reasons, the legend statistics — and what would have to be DERIVED. Anything
derived is a second source of truth; flag each one.

§4 — THE HONESTY INVENTORY. List every claim the viewer would implicitly make
by displaying something, and where its caveat currently lives. At minimum:
the surface is within 0.5 kg/m² of the training mean over 99.62% of its
domain; the covariates are synthetic; the economics are placeholders; the
TS-6 comparison is against a fixture; the claim verdict REFUSES. For each,
report whether a user would MEET it or have to go LOOKING for it. This
inventory is E5.4's specification.

§5 — THE STACK, VERIFIED. Confirm MapLibre GL JS and deck.gl are usable from
a CDN with no build step; name the versions and their licenses. Confirm no
npm/node dependency would enter the repo. Report how the origin taxonomy
treats a vendored or CDN-referenced JS library — it is a TOOL, not data, the
same as quantile-forest (C8.1 precedent) — and whether the audit's walk would
see any new file the viewer adds.

Report all five and STOP.

════════════════════════════════════════════════════════════════════════════
E5.1 — READ-ONLY API + LAYER CATALOG (two commits; adversarial review on 2)
════════════════════════════════════════════════════════════════════════════

── COMMIT 1: THE READ-ONLY API ──

FastAPI. Endpoints: runs, a run's manifest, CV scores, TS-6 agreement, the
economics block.

READ-ONLY MUST BE STRUCTURAL, NOT A CONVENTION. No POST/PUT/PATCH/DELETE
route may exist, and a test must assert that over the app's actual route
table — not over a list the author maintains. This is the same rule as
never-cherry-pick and the same test shape: enumerate from the framework, not
from a declaration.

The API SERVES what the manifest RECORDS. It computes nothing, derives
nothing, and re-hashes nothing. If a value the viewer needs is not in the
manifest, that is an E5.1 finding and a manifest question — report it rather
than computing it at the API layer, which would put a second source of truth
behind a URL.

── COMMIT 2: THE LAYER CATALOG (adversarial review) ──

An endpoint the viewer reads to discover what layers exist for a run. Per
entry: identity (hash, path), control-axis coordinates (layer type,
estimator, z, scenario), computed origin, both watermark reasons with their
expiry conditions, the claim verdict, and the statistics the legend needs
(min, max, the binning).

THE CATALOG RESOLVES FROM THE MANIFEST. Never from a directory listing, never
by parsing a filename. E4.2 built the association record for exactly this,
and TAX.1 refused name-inference once already.

TESTS, both directions — one alone lets a layer vanish or a phantom appear:
  · every catalog entry corresponds to an artifact that exists on disk;
  · every artifact that exists appears in the catalog;
  · no write route exists (over the real route table);
  · the claim verdict's failing AND passing sets match a direct guard run;
  · both watermark reasons are present, per reason, on every layer carrying
    them — and a fixture where ONE is lifted produces one lifted and one
    unlifted (the discrimination property; without it "two reasons" is
    decoration);
  · the legend statistics match the raster, computed independently.

Beware the single-source tamper (CLAUDE.md, ×2): a test that forges ONE
witness proves only that the catalog does not read that witness. Forge every
derived witness consistently and leave only the ground truth dissenting.

════════════════════════════════════════════════════════════════════════════
E5.2 — LAYER EXPORT (one commit)
════════════════════════════════════════════════════════════════════════════

Rasters → the web-renderable form E5.0 §2 chose.

THE EXPORT IS A DERIVED ARTIFACT and carries the origin machinery: computed
origin (never declared), both watermark reasons, and a hash chaining to the
raster it came from. MUTATION-VERIFY THE LAUNDERING DIRECTION — an export
that loses its provenance on the way to the browser is exactly the failure
the watermark family exists to prevent, and it is easiest to introduce here
because the target format has no metadata tags.

THE MASK SURVIVES THE EXPORT. Masked cells (no covariates — undefined) must
remain distinguishable from cells with a value. A format where undefined
becomes zero, or simply vanishes, makes the map claim knowledge it does not
have — the same defect E4.2 refused at the raster level, and the browser is
where it would be invisible.

Report the export's total size against §2's measurement, and state the
Checkpoint-1 path explicitly: what changes, what does not, and whether the
catalog's shape survives the swap. That is the contract-slot discipline
applied to a serving format.

Tests: round-trip (values, coordinates, mask); the mask's cell set matches the
raster's exactly; origin and both reasons present; the chaining hash matches
the source raster by recomputation; determinism.

════════════════════════════════════════════════════════════════════════════
E5.3 — THE VIEWER (two commits; adversarial review on 2)
════════════════════════════════════════════════════════════════════════════

ONE STATIC HTML PAGE. MapLibre GL JS + deck.gl from CDN. No npm, no node, no
build step, no framework. If that turns out impossible, STOP — it is a stack
decision.

── COMMIT 1: THE MAP AND THE CONTROLS ──

  · dark basemap, gridded heatmap over it;
  · LEFT CONTROL PANEL: layer type, estimator, z-level, scenario — from
    E5.0 §1's inventory. Combinations with no artifact are DISABLED AND
    LABELLED WHY, not absent. An absent control is indistinguishable from a
    control that was never built;
  · BINNED COLOUR LEGEND with values and units, updating with the layer;
  · HOVER READOUT: cell value, its PAIRED UNCERTAINTY, and coordinates.
    Prediction and uncertainty always together — the pairing rule has been
    structural in the code since E2.1 and must not be breakable in the UI;
  · zoom, pan, scale bar. Measure and screenshot optional.

NO TIMELINE. There is no time axis. GFW's scrubber drives a temporal
aggregation; this data has none, and a scrubber with one frame is a control
that lies about what varies.

── COMMIT 2: THE STATIONS, AND WHAT THE MAP ARGUES (adversarial review) ──

DRAW THE 35 STATIONS over the surface. Their clustering — two groups ~991 km
apart, zero pairs between 13 km and 986 km — is the single most important fact
about this dataset. A viewer that renders a smooth surface without showing
where the data actually sits conceals the finding, and a reviewer who notices
that omission will discount everything else on the map.

Tests: the viewer loads every layer the catalog advertises; a catalog entry
whose artifact is missing fails VISIBLY rather than rendering nothing; the
control state maps to exactly one layer; the hover readout matches the
underlying value spot-checked AGAINST THE RASTER, not against the export —
checking the export against itself proves only that the export is
self-consistent.

Whatever test mechanism you choose for the JS (a headless browser, a
DOM-free unit harness, or asserting on the data layer only), state its LIMIT:
what it cannot observe. A viewer test that cannot fail on a visual defect
should say so rather than implying coverage it does not have.

════════════════════════════════════════════════════════════════════════════
E5.4 — THE HONESTY SURFACE (one commit; adversarial review)
════════════════════════════════════════════════════════════════════════════

This task decides whether the viewer is defensible. Its specification is
E5.0 §4's inventory.

A GFW-styled map is an AUTHORITY ARTIFACT: the aesthetic says measured,
operational, real. This surface is within 0.5 kg/m² of the training mean over
99.62% of its domain, on synthetic terrain, with placeholder economics, and
E2.5's guard REFUSES to call any of it a claim. Every other honesty mechanism
here lives where a MACHINE reads it. The viewer is the first artifact where a
HUMAN meets the output, and the one most capable of overriding all of them.

REQUIREMENTS, each with a test:

  1. THE CLAIM VERDICT IS VISIBLE WITHOUT INTERACTION — not a link, not a
     modal, not a footer. Where the map is, with the FAILING PRECONDITIONS
     NAMED. This is E2.5's discrimination property made visual: a viewer
     saying "not validated" without saying WHICH conditions failed is the
     blanket refusal the guard was designed not to be.
  2. BOTH WATERMARK REASONS, SEPARATELY, with their expiry conditions —
     terrain lifts at Checkpoint 1, economics at Checkpoint 4, and fixing one
     leaves the other. A single "illustrative" badge collapses them.
  3. THE UNCERTAINTY IS NOT OPTIONAL [KARL — DECIDE, propose first]. Options:
     side-by-side panels, a required overlay, or uncertainty in the readout
     with no way to hide it. The pairing rule is structural in the code; a UI
     that lets a user turn the uncertainty off breaks in the viewer what the
     ABC enforces everywhere else. Propose one with its cost; if it stays a
     toggle, say why and what protects the pairing instead.
  4. THE 99% FACT IS ON THE MAP [KARL — DECIDE, propose first]. Almost all of
     this surface carries no information, and rendering it as a smooth field
     states the opposite. Options: draw the one-fitted-range contour around
     the data, hatch or fade the no-information region, or default to the
     uncertainty layer rather than the prediction. Propose one, state what it
     costs and what it does not fix.

MUTATION-VERIFY EACH: remove the verdict; collapse the two reasons to one;
hide the uncertainty; remove the no-information marking. Each must fail a
test BY NAME. An honesty surface with no observer is decoration, and this
project has refused decoration four times.

════════════════════════════════════════════════════════════════════════════
E5.5 — RUN HARNESS · E5.6 — CI · E5.7 — DEPLOY
════════════════════════════════════════════════════════════════════════════

E5.5 — one command that runs the full pipeline and produces every artifact
the viewer reads. TRIPWIRE: the engine's composition already sequences most
of this. Inventory first; report assembly vs new.

E5.6 — PARTLY BUILT. ci.yml runs the whole suite and test_engine_run.py runs
the real composition inside it. What is missing is a named,
artifact-producing job. Verify that before scoping, and report what the job
adds beyond what already runs.

E5.7 — static viewer + a small API host. THE CLAIM VERDICT TRAVELS WITH THE
DEPLOYMENT: a public URL is the strongest claim this project will make, and
it must carry its own refusal. Confirm the deployed viewer shows the verdict
and both watermark reasons before any URL is shared.
Sentry is optional — a hosted service dependency for one static page and a
small API. If added, say what it is for beyond "errors."

════════════════════════════════════════════════════════════════════════════
CLOSING PHASE 5 TRACK E
════════════════════════════════════════════════════════════════════════════

  · Walkthrough per task; a phase walkthrough at the end.
  · CP5a's criteria, verified: the viewer shows every layer that exists,
    correctly, with the verdict and both reasons visible without
    interaction.
  · State plainly what CP5b still needs — CP1, CP3, CP4 — and that the
    verdict will change because the FACTS changed, not because the viewer
    did.
  · A derived statement of what Track E can still do without Track G. Derive
    it from the lane list and the open items; do not assert it from memory of
    the plan. That claim has been wrong twice.
  · BACKLOG: anything a premise check surfaced; any trigger that fired.
  · Suite trajectory and final count.

Stop for review before CP5a.
