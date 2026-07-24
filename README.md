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

**Phase 0 (scaffold).** See `docs/contracts/README.md` for the Phase 0
done-checklist.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
# --only-binary avoids a source build of rasterio, which needs a local GDAL
# toolchain (gdal-config) you likely don't have installed.
pip install -e ".[dev]" --only-binary=:all:
pytest -v
```
