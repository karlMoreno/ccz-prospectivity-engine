"""build_covariate_stack — E1.4's deliverable orchestration.

Loads the DEM once, runs every enabled Contract 3 recipe through the
CovariateRegistry, and writes one GeoTIFF per covariate plus a single
provenance.json sidecar (sorted keys, no timestamps — byte-identical across
runs, same determinism bar as E1.3's corpus CSV).

Not a new pattern: this is glue over the registry, the way corpus_builder.py
is glue over IngestionPipeline. ProspectivityEngine's `feature_builder`
callable seam (engine.py) will wrap registry.build_all in Phase 2; this
module exists so E1.4's rasters/provenance can be produced and reviewed now.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from engine.prospectivity.features._contract import load_covariates_yaml
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry


def build_covariate_stack(dem_path: Path, output_dir: Path) -> dict[str, Path]:
    """Compute all enabled covariates from `dem_path`; write rasters +
    provenance.json under `output_dir`. Returns {layer_name: written_path,
    ..., "provenance": provenance_path}."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    grid = DemGrid.load(Path(dem_path))
    registry = build_default_registry()
    results = registry.build_all(grid)

    written: dict[str, Path] = {}
    for result in results:
        layer_path = output_dir / f"{result.name}.tif"
        with rasterio.open(
            layer_path,
            "w",
            driver="GTiff",
            height=result.values.shape[0],
            width=result.values.shape[1],
            count=1,
            dtype="float32",
            crs=grid.crs,
            transform=grid.transform,
            nodata=np.nan,
        ) as dataset:
            dataset.write(result.values.astype(np.float32), 1)
        written[result.name] = layer_path

    provenance = {
        "contract": "docs/contracts/covariates.yaml",
        "registry_version": load_covariates_yaml()["registry_version"],
        "dem": grid.provenance(),
        "layers": [result.provenance for result in results],
    }
    provenance_path = output_dir / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    written["provenance"] = provenance_path
    return written
