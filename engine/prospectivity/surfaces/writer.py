"""write_surface — the COG writer and the THREE watermark carriers (E3.1+2 §3).

    SurfaceResult ──► <name>_prediction.tif   ┐
                 ──► <name>_uncertainty.tif   ├─ GeoTIFF TAGS  (carrier 1)
                 ──► <name>.provenance.json  ─┴─ SIDECAR       (carrier 2)
                          ▲
                          └── ClaimVerdict (E2.5's guard)      (carrier 3)

THE WATERMARK PROBLEM IS NEW HERE. `plot_stack` can stamp a PNG where a human
sees it; a GeoTIFF has no such surface, and a consumer meets one through GDAL,
QGIS or a script — never through a caption. So the non-scientific status is
carried THREE ways, and every carrier is separately mutation-tested: a
watermark with one carrier is one deletion from silence.

THE ORIGIN IS COMPUTED, NEVER DECLARED. `data_origin` is derived by
`combine_origins` from the inputs that actually produced the surface (the
stack's layer origin and the training matrix's), so a surface built on a
SYNTHETIC DEM cannot launder itself into DERIVED by being written to a new
file. The watermark then derives from THAT, default-on: absence of proof
produces a watermark, never a clean render.

PUBLISHABILITY IS THE GUARD'S ANSWER, NOT THIS MODULE'S. E2.5's
`ClaimVerdict` is a REQUIRED argument: an ineligible claim still WRITES —
building on fixtures is legitimate — but writes as NON-PUBLISHABLE with the
failing preconditions named in the tags. Publishing from fixtures is what the
guard exists to prevent, and consulting it here is what makes it load-bearing
rather than a thing that only runs in tests.

    A MEASURED LIMIT ON "PER SURFACE" (E3.1+2 §3, 2026-08-20): the task asked
    for a verdict PER SURFACE rather than per run. `evaluate_claim` is keyed
    on (RunManifest, design) and FOUR of its six preconditions
    (paired-uncertainty, single-DEM, provenance-chain, pre-registered
    threshold) are properties of the RUN; the other two are properties of a
    DESIGN. None is a property of an ESTIMATOR, so today's guard cannot yield
    a verdict that differs between kriging's surface and RF's. This signature
    takes ONE VERDICT PER SURFACE so the shape is expressible the day the
    guard gains that granularity — but a caller passing the same verdict to
    every surface is reporting the truth as the guard currently computes it,
    not cutting a corner.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.validation.claim import ClaimVerdict

# The GDAL COG driver is present at GDAL >= 3.1 (measured here: 3.9.2 via
# rasterio 1.4.1), so no dependency is needed to WRITE one.
#
# WE DO NOT CLAIM COG-NESS, and E3.0 §3 is why: at this grid the payload is
# ~13 KiB — smaller than ONE 512x512 float32 block — the driver emits NO
# overviews at that size, and nothing installed (rio_cogeo, osgeo.gdal,
# validate_cloud_optimized_geotiff) can check the IFD/byte-layout property
# that actually makes a GeoTIFF cloud-optimized. Asserting the observable
# fields while calling the result "a COG" would be a claim with a partial
# observer, so the tags record what was OBSERVED and never the label.
COG_DRIVER = "COG"

WATERMARK_TAG = "watermark"
ORIGIN_TAG = "data_origin"
PUBLISHABLE_TAG = "publishable"
REFUSED_TAG = "claim_failing_preconditions"
NO_WATERMARK = "none (proven MEASURED lineage — no watermark required)"
NO_REFUSALS = "none (every precondition passed)"


def surface_watermark(data_origin: DataOrigin | str | None) -> str | None:
    """The watermark text for a surface's COMPUTED origin, or None for a
    proven-MEASURED lineage.

    `watermark UNLESS proven`, never `watermark IF synthetic` — the positive
    rule P2.0d-3 established. An unknown or absent origin produces a
    watermark; only MEASURED renders clean, because a missing declaration is
    exactly the case a negative rule would let through.
    """
    if data_origin is None:
        return (
            "NON-SCIENTIFIC — this surface's data origin is UNRECORDED, which is "
            "not the same as clean; it is unproven"
        )
    origin = DataOrigin(data_origin)
    if origin is DataOrigin.MEASURED:
        return None
    return (
        f"NON-SCIENTIFIC — computed from {origin.value} inputs. This surface is "
        "not a scientific claim: the covariates are computed on a synthetic DEM "
        "until Checkpoint 1 delivers real bathymetry."
    )


def _tags(
    result, data_origin: DataOrigin, verdict: ClaimVerdict, kind: str, grid: PredictionGrid
) -> dict[str, str]:
    watermark = surface_watermark(data_origin)
    failing = sorted(item.precondition.value for item in verdict.failures)
    # NEVER AN EMPTY STRING: GDAL DROPS empty tags, so a clean surface would
    # come back with the tag ABSENT — indistinguishable from a file written
    # before the tag existed. An explicit "none (...)" says which it is.
    return {
        ORIGIN_TAG: data_origin.value,
        WATERMARK_TAG: watermark or NO_WATERMARK,
        PUBLISHABLE_TAG: "false" if (failing or watermark) else "true",
        REFUSED_TAG: ",".join(failing) if failing else NO_REFUSALS,
        "estimator_name": result.estimator_name,
        "surface_kind": kind,
        "uncertainty_method": result.uncertainty_method,
        "uncertainty_semantics": result.uncertainty_semantics,
        "n_predicted": str(result.n_predicted),
        "n_masked": str(result.n_masked),
        "n_sd_zero": str(result.n_sd_zero),
        "grid_stack_content_hash": grid.stack_content_hash,
        "grid_dem_content_hash": grid.dem_content_hash,
    }


def _write_raster(path: Path, values: np.ndarray, grid: PredictionGrid, tags: dict) -> None:
    with rasterio.open(
        path,
        "w",
        driver=COG_DRIVER,
        height=grid.height,
        width=grid.width,
        count=1,
        dtype="float32",
        crs=grid.crs,
        transform=rasterio.Affine(*grid.transform),
        nodata=np.nan,
    ) as dataset:
        dataset.write(values.astype(np.float32), 1)
        dataset.update_tags(**tags)


def write_surface(
    result,
    grid: PredictionGrid,
    output_dir: Path | str,
    *,
    data_origin: DataOrigin | str,
    verdict: ClaimVerdict,
) -> dict[str, Path]:
    """Write one estimator's paired surfaces plus their provenance sidecar.

    `data_origin` is the COMPUTED origin of this surface — the caller derives
    it with `combine_origins` over the inputs; this function never infers one.
    `verdict` is E2.5's answer for this surface and is REQUIRED: there is no
    code path that writes an unmarked file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    origin = DataOrigin(data_origin)
    name = result.estimator_name

    written: dict[str, Path] = {}
    for kind, values in (("prediction", result.mu), ("uncertainty", result.sd)):
        path = output_dir / f"{name}_{kind}.tif"
        _write_raster(path, values, grid, _tags(result, origin, verdict, kind, grid))
        written[kind] = path

    # CARRIER 2 — the sidecar. A NEW VALUE-BEARING FILE, so it declares its
    # own origin in the same edit that creates it (the authoring rule), and
    # the declaration is the COMPUTED one, not a hand-typed label.
    sidecar = output_dir / f"{name}.provenance.json"
    sidecar.write_text(
        json.dumps(
            {
                "data_origin": origin.value,
                # SYNTHETIC'S EVIDENCE, required by the origin taxonomy and
                # supplied here because the audit refuses a bare SYNTHETIC
                # label: "the generator's import path AND seed(s)". Found by
                # probing test_data_origin_audit.py against a staged sidecar
                # — the first draft declared SYNTHETIC with neither and was
                # refused BY NAME on both counts.
                "generator": "engine.prospectivity.surfaces.builder.build_surfaces",
                "seed": _seed_of(result),
                "data_origin_note": (
                    "COMPUTED by combine_origins from the feature stack's layer "
                    "origin and the training matrix's origin — never declared by "
                    "hand. The watermark below derives from this value."
                ),
                "watermark": surface_watermark(origin),
                "publishable": not (verdict.failures or surface_watermark(origin)),
                "claim_failing_preconditions": sorted(
                    item.precondition.value for item in verdict.failures
                ),
                "claim_eligible": verdict.eligible,
                "claim_is_scientific": verdict.is_scientific,
                "surface": result.summary(),
                "grid": grid.identity(),
                "rasters": {kind: path.name for kind, path in written.items()},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    written["provenance"] = sidecar
    return written


def _seed_of(result) -> int | None:
    """The estimator's recorded seed, or None where it has none.

    Kriging is deterministic given its inputs and records no seed; the forest
    records one. Reporting None is the honest answer for the former — a
    fabricated 0 would satisfy the audit while naming a seed nothing used.
    """
    seed = result.provenance.get("seed")
    return int(seed) if seed is not None else None


def compute_surface_origin(layer_origin: str, matrix_origin: str) -> DataOrigin:
    """The surface's origin: the LEAST-REAL of what produced it.

    A surface is no more real than the terrain its covariates came from or the
    corpus its target came from, and `combine_origins` is the one function
    that rule lives in (one rule, every scale — entries to file, artifacts to
    run, and now inputs to surface).
    """
    return combine_origins([layer_origin, matrix_origin])
