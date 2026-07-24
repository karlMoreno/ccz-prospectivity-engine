# data/bathymetry/

Reserved for the real public GEBCO-class bathymetry grid for the study area
(the `src_bathymetry_primary` entry in `data/sources/source_queue.yaml` —
currently `title`/`is_open`/`license` all `null`, marked `[GEOLOGY — ISAAC]`).

Not the DeepData confidential processed bathymetry — public GEBCO only.

- **Who fills this in:** Track G (alpha proposal §10, G1.1).
- **When:** Phase 1, swapped in at Integration Checkpoint 1 ("swap synthetic
  DEM -> real bathymetry.tif").
- **Until then:** Track E builds/tests `TerrainSource` against a synthetic
  raster generated on the fly by `tests/fixtures/rasters.py`
  (`write_synthetic_bathymetry`) — no file needs to exist here for Phase 0
  or Phase 1's CI to pass.
