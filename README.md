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

**Phase 1, Track E complete through E1.4.** Phase 0's scaffold + seven
contracts, real ingestion (E1.1–E1.3: source adapters, per-evidence-class
normalizers, dedup Specifications, corpus build), and terrain feature
recipes (E1.4: Contract 3 v3 metre-based windows, the 8 Option-A covariates,
plot deliverable on the labelled synthetic DEM) are built and reviewed. The
corpus ([`data/corpus/master_observations.csv`](data/corpus/master_observations.csv))
holds **108 rows** (36 SO268 box-core events × MASS/COUNT/COVER), **35
training-eligible MASS rows**, and is **single-source** until Track G
delivers real Dryad data and the TS-6 digitization. Per-task reviews live in
[`docs/walkthroughs/`](docs/walkthroughs/).

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
