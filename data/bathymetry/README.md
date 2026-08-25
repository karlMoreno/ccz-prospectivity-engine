# data/bathymetry/

**FILLED at G.3 (2026-08-24): GEBCO_2026 bathymetry + TID companion, CCZ
subset N25/S0/W-160/E-110.** The `src_bathymetry_primary` row in
`data/sources/source_queue.yaml` is the complete record — origin (DERIVED,
by GEBCO's own "information product" wording), DOI, subset bbox, licence,
accessed date, and **both sha256 hashes**.

What lives here and its tracking state, deliberately split:

| file | tracked? | why |
|---|---|---|
| `gebco_2026_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif` (144 MB) | **no** (`.gitignore data/bathymetry/*.tif`, Phase 0) | see "durability" below |
| `gebco_2026_tid_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif` (72 MB) | **no** (same rule) | same |
| `GEBCO_Grid_terms_of_use.pdf` | yes (gitignore exception) | the DERIVED classification's evidence quote |
| `GEBCO_Grid_documentation.pdf` | yes (exception) | the TID code table (§3.0) + dataset reference (§6.0) |
| `data_origin.yaml` | yes | declares the two PDFs; carries the rasters' would-be entries as comments (a tracked sidecar entry naming an untracked file is refused as dangling — correctly) |
| `tid_accounting.json` | yes | the TID accounting artifact (G.3 commit 2) |

**Durability (the standing state, pending Karl's confirmation):** the
rasters are FETCH-AT-BUILD, not committed. The repo's own `.gitignore` has
excluded `data/bathymetry/*.tif` since Phase 0, and plain committing is
foreclosed anyway — the 144 MB file exceeds GitHub's 100 MiB hard push
limit, so committing it would break every future `git push`. The files are
not precious; the RECORD is: GEBCO_2026 is a fixed release at a DOI, and
the ledger row records the exact subset bbox, so re-obtaining is one
download through https://download.gebco.net/ (Grid Subsetting App) with the
row's bbox, then verifying:

```bash
python -m pytest tests/test_bathymetry_ledger.py -q
```

(the hash assertions self-activate whenever the rasters are present; on a
clone without them they skip, by name). What the clone-and-reproduce promise
becomes under fetch-at-build: *anyone who clones gets these numbers after
one recorded, hash-verified download* — conditional on GEBCO continuing to
serve the release. Git-LFS remains the upgrade path if Karl wants
bytes-with-clone; the gitignore's own comment has said "track with DVC
later" since Phase 0.

**A clean origin audit is NOT hash-verification** (TRACK-G.md §0.5, probed):
the audit checks declarations, not bytes. The hashes live in the ledger row
and are asserted by `tests/test_bathymetry_ledger.py`.

The synthetic fixture (`tests/fixtures/rasters.py`) remains the CI DEM until
Checkpoint 1; the harness takes these files explicitly:
`--dem data/bathymetry/gebco_2026_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif
--dem-data-origin DERIVED`. **Do not run that before Contract 8's
`acceptance_thresholds` is filled** — the pre-registration clock
(TRACK-G.md §4; `docs/walkthroughs/G.3.md` §3).
