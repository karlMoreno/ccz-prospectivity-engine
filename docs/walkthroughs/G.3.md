# G.3 — GEBCO_2026 bathymetry + TID ingested, declared, accounted (2026-08-24)

Three commits: the files declared with their ledger row (`eb3ef3b`), the TID
accounting as a machine-readable artifact (`8a69eb1`), the DemGrid
orientation assertion + this closeout (commit 3). **The harness was NOT run
— deliberately.** §3 says why, and what state CP1 is left in.

```
 ~/CCZ/downloads/gebco/                data/bathymetry/
 ┌─────────────────────┐   cp    ┌──────────────────────────────┐
 │ bathy.tif   144 MB  │ ──────▶ │ *.tif      UNTRACKED (rule   │
 │ tid.tif      72 MB  │         │            fixed at G.3)     │
 │ terms.pdf           │         │ *.pdf      TRACKED (scoped   │
 │ documentation.pdf   │         │            exceptions)       │
 └─────────────────────┘         │ data_origin.yaml  TRACKED    │
                                 │ tid_accounting.json TRACKED  │
        the COMMITTED record ──▶ │ README.md  (the map)         │
                                 └──────────────────────────────┘
   src_bathymetry_primary (Contract 5): DERIVED · doi · subset_bbox
   · licence · accessed_date · sha256 × 2   ← the hash observer
```

## §0 — Verification against the prompt's numbers, and what disagreed

Everything in the prompt's §0 reproduced with the repo's venv (sizes, 12000
× 6000, 15 arc-sec, bounds, depth −7417/+4163 median −4641, land 171,547 =
0.238%, the TID histogram to the cell, direct 26.616% / predicted 73.146%,
study extent 1,958,400 cells at 45.131% / 54.869%, study depth −4975/−528
median −4395, per-row 31.8–72.8% sd 10.4 pp, every row and column with a
direct cell) — **except three, reported per the instruction:**

1. **The TID dtype is `int8`, not `uint8`** (rasterio band dtype). Codes
   0–72 fit either; recorded so the acceptance criterion is exact.
2. **The station count with the prompt's implied filter is 36, not 35.**
   MASS ∧ abundance ∧ is_open misses the qa-flag condition; the production
   gate (`Observation.is_training_eligible()`) gives 35. The artifact uses
   the production gate, not a reimplementation — two implementations of one
   rule is how they drift.
3. **The per-cluster confound (item 4's motivating worry) is REFUTED:** all
   35 training stations — both clusters — sit on **TID 11 (multibeam)**.
   West 14/14 direct, east 21/21 direct. Station positions correlate with
   survey effort by sitting ON the survey boxes. Per the prompt's own rule,
   no asymmetry BACKLOG entry is opened, because the asymmetry does not
   exist. What remains true: the PREDICTION domain is 54.9% predicted, so
   the caveat lives with the surfaces (the accounting artifact is the
   honesty surface's future input), not with the training matrix — which
   also answers the §2 entry's TID-mask question: **no training-matrix mask
   is needed for the current corpus** (nothing to mask; every station is on
   direct measurement).

**Found while probing, not in the prompt: the Phase-0 gitignore rules for
`data/bathymetry/*.tif` and `data/ts6/*.tif` had never matched anything.**
A trailing comment is part of a gitignore pattern, so both rules were
no-ops since Phase 0 — proven by `git status` showing the copied tifs and
`git check-ignore` exiting 1; fixed in commit 1 (comments moved off the
pattern lines, matching then verified). Nothing was ever silently ignored
that shouldn't have been — the failure mode ran the other way (files that
were BELIEVED ignored would have shown up as untracked noise, and the first
person to `git add -A` would have staged 216 MB).

## §1 — Commit 1: DERIVED by the publisher's own words; the ledger as the record

**The class.** DERIVED, decided by the source's own words (both quotes
verified in the shipped `GEBCO_Grid_terms_of_use.pdf`): the grid is
"created by interpolating, applying algorithms and mathematical techniques
to bathymetric data" and "GEBCO considers the GEBCO Grid to be an
information product"; GEBCO "does not provide the underlying source
bathymetric data"; resolution "may be significantly different" from the
measured data's. ~~One licence-summary phrase in the prompt did NOT verify:
"must not mislead" — the actual terms say *must not suggest official status
or IHO/IOC/GEBCO endorsement*; the ledger row records the verified wording.~~
**CORRECTED AT THE G.3 APPROVAL (2026-08-24): the struck sentence is FALSE —
a correction that OVERSHOT.** The terms' "Users must" list has THREE
obligations, and the third is "Not mislead others or misrepresent The GEBCO
Grid or its source" — verbatim in the terms PDF AND §7.2 of the
documentation, both checked at the approval with a full-text extraction.
G.3's extractor (a regex over Tj/TJ operators) silently dropped that span,
and the check concluded the obligation was ABSENT when a paraphrase was
merely INEXACT — the instrument was the defect (the check itself is in
scope). The ledger row now carries all three; until this correction it
carried an INCOMPLETE LICENCE RECORD — the class of defect this project
exists to refuse, and the clause that went missing is the one about not
misrepresenting the source. A licence obligation recorded nowhere cannot be
honored by anyone reading the record. Correction-drift instance (o) in
CLAUDE.md's table: a verification that finds a paraphrase inexact and
infers the underlying fact is absent.
The 73.146%-predicted TID composition corroborates the class independently.

**The evidence rule fits without strain.** DERIVED's evidence is "a
derivation formula or the artifact recording it" — nothing in the rule or
the resolver requires the derivation to be OURS. The artifact recording
this one is GEBCO's own documentation, tracked in the same commit; the
ledger row's `derivation` summarizes it and says whose it is. No taxonomy
change needed; probed rather than assumed (below). This differs from
TAX.1's TS-6 case only in WHO performed the derivation, and the rule never
asked.

**The TID grid is its own artifact** — provenance metadata ABOUT the
bathymetry (the same kind of thing this project's taxonomy is), classified
explicitly DERIVED with its own derivation text, never by adjacency.

**Where the declarations live, and why (the dangling constraint).** The
rasters are untracked (the Phase-0 rule, now actually working), and the
audit refuses — correctly — a tracked sidecar entry naming an untracked
file. So: the PDFs have sidecar entries (LITERATURE, locating citations);
the rasters' committed declaration is the LEDGER ROW (DERIVED, both
hashes, subset bbox, licence, DOI); their would-be sidecar entries ride as
comments for the day the storage decision changes.

**The audit, probed both directions** (scratch tree, the real resolver, the
exact entry text):

| state | result |
|---|---|
| rasters staged-as-tracked, full sidecar entries | **passes clean** |
| `derivation` stripped from both | **fails by name** ×2: "DERIVED without a derivation formula…" |
| sidecar entries removed | **unclassified by name** ×2 |
| the real committed shape (PDFs declared, tifs untracked) | clean; `dangling = []` |
| counter-probe: tif entries committed while tifs untracked | **dangling** ×2, by name |

Of E5.5's three run-directory refusals, only **(a) unclassified** applies
to this shape (demonstrated above); (b) AUTHORED-with-author-None cannot
arise (DERIVED carries no author) and (c) the quoted-declaration false
positive has no `author: unrecorded` to quote.

**A clean audit is NOT hash-verification** — the resolver has no
MEASURED/DERIVED hash branch (TRACK-G.md §0.5). The hash observer is
`tests/test_bathymetry_ledger.py`: recorded sha256 vs the actual bytes,
self-activating whenever the rasters are present (the
`test_grid_rows_are_never_flagged_observed` pattern), plus a cross-record
test that the accounting artifact and the ledger row name the same bytes —
which runs everywhere, rasters or not.

**[KARL — DECIDE] durability, reported with the measured numbers:**

- **Plain COMMIT is foreclosed twice over:** the 144 MB tif exceeds
  GitHub's 100 MiB hard push limit (committing it would break every future
  `git push` — including the pending CP5a push), and it would put 216 MB
  into history permanently (`.git` today: **14 MB**; a later re-cut adds
  another 216 MB, forever).
- **GIT-LFS:** viable (both files under LFS limits), adds a dependency and
  a hosting quota; a cloner without LFS gets pointer files that look like
  data. The gitignore's own Phase-0 comment ("track with DVC later")
  anticipated this family.
- **FETCH-AT-BUILD (implemented as the standing state):** the release is
  fixed at a DOI and the row records the exact subset bbox, so a lost file
  costs one re-download through the Grid Subsetting App plus
  `pytest tests/test_bathymetry_ledger.py` to hash-verify. **Recommended.**
  The files are not precious; the record is — unlike the SO268 corpus,
  whose value is the parsing, these bytes are re-obtainable from the
  publisher by construction.
- **What the promise becomes, stated honestly:** "anyone who clones gets
  these numbers" becomes "anyone who clones gets these numbers after one
  recorded, hash-verified download" — conditional on GEBCO continuing to
  serve the 2026 release. If that conditionality is unacceptable for the
  alpha's reproducibility claim, LFS is the upgrade path; nothing in this
  commit forecloses it.

**Recorded at the approval (2026-08-24): this decision was FORECLOSED, not
judged.** The prompt posed commit-vs-LFS-vs-fetch as a trade-off; GitHub's
100 MiB hard push limit forecloses COMMIT outright (the 144 MB raster would
break every future push, including the pending CP5a push), and the repo's
Phase-0 rule forecloses it a second time. A decision posed as a trade-off
had an external hard constraint the planning side had not checked — the
premise-failure shape, one level up: a question framed without verifying
the environment it lands in. **The LFS-upgrade trigger, so it is not
re-derived later:** a failed or hash-mismatched re-download of the 2026
release (GEBCO no longer serving it byte-identically), or a reproducibility
reviewer requiring bytes-with-clone. Either fires the upgrade; nothing else
does.

## §2 — Commit 2: the TID accounting (`data/bathymetry/tid_accounting.json`)

**Design decision (the prompt asked for a proposal):** a JSON data artifact
beside the rasters — not a companion raster (72 MB again, and untracked by
the same rule, so invisible to a cloner) and not a manifest block (no run
exists yet; the manifest quotes it later when CP1 runs). In-file DERIVED
declaration (the audit reads `.json` top-level keys), derivation = the
generator's import path (`engine.prospectivity.terrain.tid_accounting`, a
pure function, floats explicitly rounded — the determinism basis), inputs =
the three sha256s. E5.4's honesty surface gets a machine-readable input
when CP1 arrives.

The four accountings (numbers in the artifact; highlights):

1. **The mapping, from the documentation §3.0 Table 2, not memory:** direct
   10–17, indirect/predicted 40–48, unknown 70–72, land 0 — with the full
   per-code name table.
2. **Study extent:** 1,958,400 cells, 45.131% direct / 54.869% predicted,
   depth −4975 to **−528** m (a SEAMOUNT, stated in advance — roughness,
   TPI, BPI will spike there; not a finding when it happens).
3. **The distribution a mean hides:** per-row direct fraction 31.8–72.8%
   (sd 10.4 pp), all 816 rows shipped. Every row and column has a direct
   cell — TRUE BUT MISLEADING alone (recorded in the artifact's own
   caveat): the coverage is survey blocks and transit tracks over a
   strongly bimodal field. **3b:** 45,461 direct/predicted adjacencies
   (1.16% of cell adjacencies) — covariates computed ACROSS a swath edge
   measure the transition between two data sources; an EXPECTED finding.
4. **Stations (the number that decides):** §0.3 above — 35/35 multibeam,
   both clusters; the confound refuted; no matrix mask needed.

## §3 — Commit 3: the assertion, the clock, what is armed

**DemGrid refuses what it cannot handle** (BACKLOG §3 entry, open since
E2.0-2): rotation/shear refused naming b and d; south-up (e ≥ 0) refused
naming the orientation instead of dying later blaming "window_m and
cell_size_m must be positive". Today's GEBCO subset is north-up and
shear-free (verified — the assertion passes today and is the observer for
tomorrow's file; a self-activating test checks the real file's transform
whenever present).

**The harness was NOT run, and cannot honestly be:** Contract 8's
`acceptance_thresholds` is **`value: null`** (checked this session). The
pre-registration clock (TRACK-G.md §0.3/§4) is per-run and nothing
downstream can restore a pre-registration that did not happen — so **CP1 is
BLOCKED on G.0-step0** (the thresholds task; the G.3 prompt's "G.1"), and
that is the correct state, not a failure. The first real-data harness run
happens AFTER a threshold with an admissible origin lands.

**What this arms (the CP1 task measures, not discovers):** the 0.348 R²
ceiling dissolves on its stated expiry (15-arc-sec cells separate the 35
stations' covariates); the terrain watermark reason lifts and the economics
reason does NOT; Contract 3 v3's metre windows resolve unclamped;
the 6° slope filter becomes meaningful at ~460 m cells; covariates.yaml's
geology questions come due; `EXPECTED_VERDICT_SETS` moves BY DESIGN in the
same change as the data; TiTiler fires (~1.96 M cells).

**What does not change, because it is the paper's point:** the sampling
geometry. Two clusters ~991 km apart, zero pairs between 13 and 986 km,
the range unidentified at its ceiling. Real terrain fixes the covariate
problem, not the support problem. If the models still fail to beat the
mean baseline at the honest gate, that is the result.

## Test inventory

| test | asserts (plain English) | rule it enforces |
|---|---|---|
| `test_bathymetry_ledger.py::…row_is_filled_derived_open…` | the ledger row carries DERIVED, is_open, bbox, DOI, date, licence, two distinct sha256s | Contract 5's fill-on-download header; provenance-is-mandatory |
| `…recorded_hashes_match_the_bytes_whenever…` | per file, sha256(bytes) == the recorded value; skips by name when absent | the ledger is the hash observer (audit cannot be) |
| `…citation_backing_pdfs_are_tracked…` | both GEBCO PDFs are in the git index | the DERIVED evidence's backing ships; gitignore regression visible |
| `test_tid_accounting.py::…declares_derived_with_a_derivation…` | in-file DERIVED + generator import path | the authoring rule (declared in the same edit) |
| `…quotes_the_same_raster_hashes_as_the_ledger_row` | accounting inputs == ledger hashes, no rasters needed | cross-record consistency; runs on CI |
| `…class_boundaries_match_the_documented_tid_table` | direct 10–17 / indirect 40–48 / unknown 70–72 / land 0; majority-predicted separates a swap | take the table from the document, not memory |
| `…internally_consistent_counts_and_recomputed_row_stats` | class cells sum to totals; row stats recomputed from the shipped array | convention 7 (positive full-state; no vacuous collection) |
| `…station_block_uses_the_production_gate_count…` | n = 35 = rows; clusters sum; direct+predicted = n per cluster | one gate, never reimplemented |
| `…regenerating…reproduces_the_committed_artifact_exactly` | full dict equality, fresh build vs committed; skips by name | convention 3 (full state, not selected fields) |
| `test_dem_grid.py::…rotated_transform_is_refused…` | shear terms named in the refusal | the E2.0-2 gap, closed |
| `…south_up_transform_is_refused_naming_orientation…` | south-up refused at load, right name | same |
| `…real_gebco_subset_passes_the_orientation_assertion…` | the real file's transform satisfies the predicate; skips by name | today's pass is tomorrow's observer |

## Mutation record

Backups verified before each batch, restores by `cp`, `cmp`-verified after
(the widened harness rule; no incidents). **M5's first application was a
NO-OP** — the sed assumed a one-line array that `indent=1` splits across
lines — caught by the verify-the-mutation step and re-applied via a JSON
edit: the sixth harness finding's shape avoided by the rule written for it.

| mutation | caught by (read, not assumed) |
|---|---|
| M1 ledger bathy hash ±1 hex | the byte observer AND the cross-record test (CI catches it too) |
| M3 artifact tid hash ±1 hex | the cross-record test + regeneration |
| M4 per-row sd 0.1043→0.1042 | the recomputed-stats test + regeneration |
| M5 class table [10,17]→[10,18] | the class-table test + regeneration |
| M6 station n 35→34 | the station test + regeneration |
| M7 both DemGrid refusals deleted | exactly the two named refusal tests (the real-file test correctly does NOT fail — it observes the file, not the code) |

Regeneration is the second observer only where the rasters exist; on CI the
committed-state tests are the observers — the reason both layers exist.

## Closeout

- BACKLOG: §1 GEBCO and §2 GEBCO-TID closed on their original boxes (the
  TID-mask question answered in-close: no training mask needed, surfaces
  caveat rides the artifact); §3 DemGrid closed; count 61 → 58. The
  covariates.yaml geology questions and the AOI entry are REPORTED, not
  closed — both come due at the CP1 run, which is blocked on G.0-step0.
  The G.0-2 sequence box stays OPEN with its acquisition half noted done.
- Suite: 676 → 679 (commit 1) → 685 (commit 2) → 688 (commit 3), 2
  skipped throughout; confirming run in the foreground at each commit.
