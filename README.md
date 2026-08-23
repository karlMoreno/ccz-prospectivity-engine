# CCZ Prospectivity Engine

An open, reproducible modernization of ISA Technical Study No. 6 (2010): for
one Clarion-Clipperton Zone (CCZ) study area, predict polymetallic-nodule
abundance (kg/m²) from an openly-sourced sample corpus + terrain covariates,
with honest uncertainty, an economic minability layer, a provenance manifest,
and a benchmark comparison against the TS-6 2010 surface.

See [`CLAUDE.md`](CLAUDE.md) for how this project is built, and
[`Proposals and contract V3/CCZ-Prospectivity-Engine-Alpha-Proposal-v3.md`](<Proposals and contract V3/CCZ-Prospectivity-Engine-Alpha-Proposal-v3.md>)
for the full build plan. The seven frozen contracts live in
[`docs/contracts/`](docs/contracts/README.md) and [`data/`](data/).

## Status

**Phases 0–4, Track E complete; Phase 5 in progress** (status corrected
2026-08-22 — this said "Phase 2" two phases late). Phase 0's scaffold + eight
contracts, real ingestion (E1.1–E1.3: source adapters, per-evidence-class
normalizers, `DuplicateResolutionPolicy` dedup, corpus build), terrain feature
recipes (E1.4), the training matrix, three estimators behind one `Estimator`
ABC (mean baseline, ordinary kriging, quantile random forest), spatially-blocked
cross-validation, the refuse-to-validate claim guard (Phase 2), paired
prediction/uncertainty surfaces, the TS-6 comparison and the extended run
manifest (Phase 3), the economic footprints and difference maps (Phase 4), and
the one-command run harness (E5.5) are built and reviewed. Every output is
watermarked SYNTHETIC / ILLUSTRATIVE until Checkpoints 1, 3 and 4, and the claim
guard refuses every run — by design. The suite is **624 passed, 2 skipped**.
The viewer (E5.3) is one static page on MapLibre GL JS + deck.gl from a CDN.

**Demo:** `python demo_alpha.py` walks every phase with its input and output and
ends with the viewer served locally; the copy-paste version is
[docs/DEMO.md](docs/DEMO.md). `python demo.py` is the Phase-1 ingestion deep dive.

The corpus ([`data/corpus/master_observations.csv`](data/corpus/master_observations.csv))
holds **108 rows** (36 SO268 box-core events × MASS/COUNT/COVER), of which
**35 are training-eligible**. It draws on **2 real open sources**, both
**CC BY-NC 4.0**, and contains **no fabricated values** — the placeholders
that once stood in for a third and fourth source were removed rather than
left in place.

Every value in the repo declares HOW IT CAME TO EXIST — `MEASURED`,
`DERIVED`, `LITERATURE`, `SYNTHETIC` or `AUTHORED` — and the declarations are
enforced, not documented: a production build path admits only a `MEASURED`
declaration whose recorded SHA-256 re-hashes to the bytes on disk, and an
audit test resolves the evidence for every other class. See
[the data-origin section of `CLAUDE.md`](CLAUDE.md) and
[`engine/prospectivity/provenance/origin.py`](engine/prospectivity/provenance/origin.py).

**No output here is a scientific claim yet.** The terrain covariates are
computed on a **SYNTHETIC DEM** until Checkpoint 1 delivers real bathymetry,
so every run is watermarked non-scientific by that same taxonomy — the
watermark is DERIVED from the computed origin and defaults ON. Accordingly,
the claim guard's verdict on the real run is a **REFUSAL**, for three
independent reasons: no acceptance threshold was pre-registered before the
scores existed, the covariates are synthetic, and at the honest
within-cluster gate neither model beats the mean baseline. That refusal is
the machinery working, and it is recorded rather than described:
[`docs/walkthroughs/E2.5.md`](docs/walkthroughs/E2.5.md).

Per-task reviews live in [`docs/walkthroughs/`](docs/walkthroughs/); open
items in [`docs/BACKLOG.md`](docs/BACKLOG.md).

## Development

**Python 3.11 required** (`requires-python = ">=3.11,<3.12"` — the pinned
binary-wheel set is resolved and verified for cp311; see
[`requirements.lock`](requirements.lock) for the known-good versions,
notably `rasterio==1.4.1` on macOS arm64).

```bash
python3.11 -m venv .venv
source .venv/bin/activate
# --only-binary avoids a source build of rasterio, which needs a local GDAL
# toolchain (gdal-config) you likely don't have installed.
python -m pip install -e ".[dev]" --only-binary=:all:
pytest -v
```

`.[dev]` is the standard path: it covers the whole pipeline, the test suite,
and the plot deliverables (matplotlib is dev-only; engine runtime never
imports it).

### Optional: live PANGAEA fetching (`.[fetch]`)

Only needed to download datasets by DOI over the network. The pipeline and
tests never require it — the wired sources read local `.tab` files from
`data/sources/`. It is a separate extra because pangaeapy pins
`netcdf4>1.6.5`, and `netcdf4==1.6.5` is the newest release with a
cp311/macOS-arm64 binary wheel — anything newer builds from source and needs
HDF5 headers first:

```bash
brew install hdf5 netcdf   # macOS arm64 only, before the extra
python -m pip install -e ".[fetch]"
```
