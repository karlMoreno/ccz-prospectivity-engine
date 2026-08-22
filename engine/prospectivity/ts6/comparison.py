"""The TS-6 comparison (E3.3): one grid, computed origin, declared inflation.

    TS6Surface (Contract 6)          PredictionGrid + SurfaceResult (E3.1+2)
          │                                     │
          ▼                                     │
    resample_ts6_to_grid  ── nearest ──►  ONE GRID: OURS
          │                                     │
          └────────────┬────────────────────────┘
                       ▼
            compare_surface_to_ts6  ──►  TS6Agreement
            (commit 2: r · N_eff · mean difference · refusals)

WHICH GRID, AND WHY (commit 1's decision, recorded here rather than implied):
the comparison happens on OUR grid — the feature stack's native grid that
E3.1+2 inherited without resampling. Resampling OUR surface would introduce
interpolation into values the surface builder just took care NOT to
interpolate; the TS-6 raster is the input that moves. WHAT THAT COSTS, stated
rather than hidden: TS-6 is a compiled coarse product (0.1° native per
Contract 6's grid_note), and upsampling it to a finer grid cannot add
information it does not have. NEAREST NEIGHBOUR is used for exactly that
reason — it repeats the compiled values into blocks instead of inventing
smooth detail between them (bilinear would manufacture gradients TS-6 never
published). The resampling's provenance travels with the comparison.

THE COMPARISON'S ORIGIN IS COMPUTED, NEVER DECLARED. `combine_origins` over
the two inputs — our surface's computed origin and the TS-6 input's DECLARED
origin (`TS6Surface.data_origin`, mirroring Contract 6 v3's
`raster_data_origin`). Least-real wins: a MEASURED TS-6 cannot launder a
synthetic-DEM surface, and a real surface cannot launder a fixture benchmark.
Today both inputs are SYNTHETIC and the comparison is SYNTHETIC — which is
the honest label for a number that exercises machinery and measures nothing
about TS-6.

GRID IS A BENCHMARK CLASS, NEVER A TRAINING STATION (Contract 1's evidence
discipline). This module imports nothing from `ingestion/`, `samples/` or the
corpus path, and the suite asserts that structurally — the comparison CANNOT
feed the corpus, as a test rather than a comment.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.surfaces.grid import PredictionGrid


@dataclass(frozen=True)
class ResampledTS6:
    """The TS-6 values on OUR grid, with the resampling recorded as data."""

    values: np.ndarray  # (H, W) float64, NaN where TS-6 has no data
    provenance: dict


def comparison_origin(
    surface_data_origin: DataOrigin | str, ts6_data_origin: DataOrigin | str | None
) -> DataOrigin:
    """The comparison artifact's origin: the LEAST-REAL of its two inputs.

    A TS-6 input with NO declared origin is refused rather than defaulted —
    "declaration or nothing" (P2.0d-3): a silent default here would let an
    undeclared benchmark pass as whatever flatters the comparison.
    """
    if ts6_data_origin is None:
        raise ValueError(
            "the TS-6 input carries no declared data_origin — the comparison's "
            "origin is COMPUTED from its inputs and cannot be computed from an "
            "undeclared one. Declare it on the TS6Surface (the fixture declares "
            "SYNTHETIC; the real digitized raster is DERIVED per Contract 6 v3 "
            "raster_data_origin)."
        )
    return combine_origins([surface_data_origin, ts6_data_origin])


def resample_ts6_to_grid(ts6: TS6Surface, grid: PredictionGrid) -> ResampledTS6:
    """TS-6's raster on OUR grid, by nearest neighbour.

    Nearest, not bilinear, deliberately: when the TS-6 grid is coarser than
    ours, nearest REPEATS each compiled value into a block — visibly coarse,
    honestly coarse — where bilinear would invent smooth gradients between
    values TS-6 never published. When the grids already coincide (today's
    fixture) the operation is an identity, and the provenance records that
    too rather than leaving a reader to infer it.
    """
    with rasterio.open(ts6.raster_path) as dataset:
        source = dataset.read(1).astype(np.float64)
        source_transform = dataset.transform
        source_crs = dataset.crs
        source_nodata = dataset.nodata
        source_res = (dataset.transform.a, -dataset.transform.e)

    if source_nodata is not None and not np.isnan(source_nodata):
        source = np.where(source == source_nodata, np.nan, source)

    destination = np.full((grid.height, grid.width), np.nan)
    reproject(
        source=source,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=rasterio.Affine(*grid.transform),
        dst_crs=grid.crs,
        resampling=Resampling.nearest,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )
    destination.flags.writeable = False

    same_grid = (
        tuple(source_transform)[:6] == grid.transform
        and source.shape == (grid.height, grid.width)
    )
    upsampled = source_res[0] > grid.res_x_deg or source_res[1] > grid.res_y_deg
    return ResampledTS6(
        values=destination,
        provenance={
            "target_grid": "ours (the feature stack's native grid) — resampling "
            "our surface would interpolate values the builder took care not to",
            "method": "nearest",
            "method_reason": "repeats compiled values into blocks rather than "
            "inventing smooth detail between them",
            "source_resolution_deg": [float(source_res[0]), float(source_res[1])],
            "target_resolution_deg": [grid.res_x_deg, grid.res_y_deg],
            "identity": bool(same_grid),
            "upsampling_note": (
                "TS-6 is coarser than the target grid: the resampled values "
                "REPEAT in blocks and carry no detail below the source "
                "resolution — the comparison inherits that, it does not hide it"
                if upsampled
                else "no upsampling: source resolution is at or below the target's"
            ),
            "ts6_source_id": ts6.source_id,
            "ts6_content_hash": ts6.content_hash,
        },
    )
