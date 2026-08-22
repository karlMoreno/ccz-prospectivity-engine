"""PredictionGrid — the domain a surface is defined on (E3.1+2 commit 1).

THE GRID IS THE FEATURE STACK'S OWN GRID: same extent, same cell size, same
transform, same CRS. It is not chosen and not configured — it is INHERITED,
and that is the point. Predicting on the covariates' native grid means NO
RESAMPLING of covariates, so the surface inherits the stack's provenance
exactly and no interpolation is introduced between the values E1.4 recorded
and the values a model predicts from.

    ┌──────────────────────────┐        ┌────────────────────────────┐
    │  feature stack (E1.4)    │        │  PredictionGrid            │
    │  <dir>/provenance.json   │───────►│  transform · crs · H×W     │
    │  <dir>/{depth,slope,…}   │  reads │  covariates (L,H,W)        │
    │  .tif  (8 layers)        │        │  predictable mask (H,W)    │
    └──────────────────────────┘        └────────────────────────────┘
                                                    │
                                    cell_centres()  │  covariate_rows()
                                   (coordinates)    ▼   (covariates)
                                        the two things `input_kind` routes to

THERE IS NO PRODUCTION EXTENT CONFIGURATION IN THIS REPO, and this docstring
says so rather than letting a reader infer one (E3.0 §2, corrected
2026-08-20). The extent is a property of whatever DEM the run is handed.
Today the only DEM is the synthetic fixture in `tests/fixtures/rasters.py`
(100 × 34 @ 0.1°, lon [−126.5, −116.5], lat [11.3, 14.7] — an extent E1.4's
preflight set to the corpus bbox + 0.5° so that all 35 stations land on it).
"corpus bbox + 0.5°" describes THAT FIXTURE. At Checkpoint 1 a global GEBCO
DEM stops bounding anything, which is when the AOI becomes a real decision
(`docs/BACKLOG.md` §1).

THE DOMAIN MASK IS FLAG-NEVER-DROP. A cell where ANY covariate is NaN — the
nan_border every windowed recipe leaves (E2.0-2) — is NOT predicted. It is
marked undefined and COUNTED, never zero-filled and never imputed, the same
rule the training matrix refuses on. A surface that quietly imputed its
border would be reporting model output where it has no input.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio


@dataclass(frozen=True)
class PredictionGrid:
    """The stack's grid, its covariate cube, and the mask of predictable cells.

    Arrays are read-only (`flags.writeable = False`), the convention
    TrainingMatrix established: a consumer that mutates a grid in place would
    silently change every surface built from it afterwards.
    """

    transform: tuple[float, ...]  # the affine's 6 coefficients, as data
    crs: str
    width: int
    height: int
    res_x_deg: float
    res_y_deg: float
    layer_names: tuple[str, ...]
    covariates: np.ndarray  # (L, H, W) float64
    predictable: np.ndarray  # (H, W) bool — True where every layer is finite
    dem_content_hash: str
    stack_content_hash: str
    stack_dir: str

    # ------------------------------------------------------------------ build
    @classmethod
    def from_stack(cls, stack_dir: Path | str) -> "PredictionGrid":
        """Read a feature stack directory (E1.4's `build_covariate_stack`
        output) into a grid.

        THE LAYER ORDER IS THE MANIFEST'S, not the directory listing's: a
        glob would order by filename and silently permute the covariate
        columns relative to the training matrix, which is the class of defect
        E2.0's "reordered-layers column consistency" test exists to catch.
        """
        stack_dir = Path(stack_dir)
        manifest = json.loads((stack_dir / "provenance.json").read_text())
        layer_names = tuple(layer["name"] for layer in manifest["layers"])
        if not layer_names:
            raise ValueError(f"{stack_dir}/provenance.json records no layers")

        planes = []
        identity: tuple | None = None
        for name in layer_names:
            path = stack_dir / f"{name}.tif"
            with rasterio.open(path) as dataset:
                here = (
                    tuple(dataset.transform)[:6],
                    dataset.crs.to_string() if dataset.crs else None,
                    dataset.width,
                    dataset.height,
                )
                if identity is None:
                    identity = here
                elif here != identity:
                    # One grid, or no grid. Layers that disagree on geometry
                    # cannot be stacked into a cube whose (row, col) means one
                    # place — the same one-DEM rule E2.0-2 enforces upstream.
                    raise ValueError(
                        f"layer {name!r} has grid {here!r}, which differs from "
                        f"{identity!r} — every layer must share one grid"
                    )
                planes.append(dataset.read(1).astype(np.float64))

        assert identity is not None
        transform, crs, width, height = identity
        covariates = np.stack(planes)
        # THE MASK: any NaN in any layer makes the cell undefined.
        predictable = ~np.isnan(covariates).any(axis=0)
        for array in (covariates, predictable):
            array.flags.writeable = False

        return cls(
            transform=transform,
            crs=crs,
            width=width,
            height=height,
            res_x_deg=transform[0],
            res_y_deg=-transform[4],
            layer_names=layer_names,
            covariates=covariates,
            predictable=predictable,
            dem_content_hash=manifest["upstream_hashes"]["dem"],
            stack_content_hash=manifest["content_hash"],
            stack_dir=str(stack_dir),
        )

    # ------------------------------------------------------- the two routings
    def cell_centres(self) -> np.ndarray:
        """(H*W, 2) lon/lat of every cell CENTRE, row-major.

        Centres, not corners: a coordinate-consuming estimator asked to
        predict "at a cell" must be asked about the middle of it, and a
        half-cell offset here would shift every kriging surface by ~5.5 km at
        0.1° without changing any test that only checks shapes.
        """
        a, b, c, d, e, f = self.transform
        cols = np.arange(self.width) + 0.5
        rows = np.arange(self.height) + 0.5
        col_grid, row_grid = np.meshgrid(cols, rows)
        lon = a * col_grid + b * row_grid + c
        lat = d * col_grid + e * row_grid + f
        return np.column_stack([lon.ravel(), lat.ravel()])

    def covariate_rows(self) -> np.ndarray:
        """(H*W, L) covariate values, row-major, columns in manifest order —
        the design matrix a covariate-consuming estimator predicts from."""
        return self.covariates.reshape(len(self.layer_names), -1).T

    # ---------------------------------------------------------------- reports
    @property
    def n_cells(self) -> int:
        return self.width * self.height

    @property
    def n_predictable(self) -> int:
        return int(self.predictable.sum())

    @property
    def n_masked(self) -> int:
        return self.n_cells - self.n_predictable

    def identity(self) -> dict:
        """The grid's identity AS DATA — what a downstream artifact records to
        prove which domain a surface was built on."""
        return {
            "crs": self.crs,
            "width": self.width,
            "height": self.height,
            "transform": list(self.transform),
            "resolution_deg": [self.res_x_deg, self.res_y_deg],
            "extent": self.extent(),
            "layer_names": list(self.layer_names),
            "dem_content_hash": self.dem_content_hash,
            "stack_content_hash": self.stack_content_hash,
            "n_cells": self.n_cells,
            "n_predictable": self.n_predictable,
            "n_masked": self.n_masked,
        }

    def extent(self) -> list[float]:
        """[west, south, east, north] in degrees."""
        a, _, c, _, e, f = self.transform
        return [c, f + e * self.height, c + a * self.width, f]
