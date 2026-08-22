"""write_footprints / write_difference — the economic rasters (E4.2).

    ScenarioFootprints ──► footprint__<scenario>__<estimator>__z<z>.tif      × (estimators × levels)
    FootprintDifference ─► difference__<a>__<b>__<estimator>__z<z>.tif        × (estimators × levels)
                                  │
                                  ├── GeoTIFF tags   (carrier 1: the two-reason verdict, PER REASON)
                                  ├── economics.footprints.json  (carrier 2 + THE ASSOCIATION)
                                  └── data_origin.yaml           (the audit's marker, merged)

ONE WRITER. `surfaces/writer.py: write_cog` — E3.1+2's — writes every
raster here; there is no second COG writer and the E3.0 §3 decision
(GDAL COG driver; assert what rasterio observes; claim NO COG-ness) is
inherited rather than restated. The origin is never re-derived: it is the
footprints' COMPUTED origin, carried.

THE GRID IS THE SURFACE'S. Same extent, cell size, transform, MASK — a
footprint on another grid than the surface it thresholds would need
interpolation. Asserted against the footprints' RECORDED grid identity
(captured at computation) and against the surface's mask exactly, never
against a literal.

THE MASK AND THE FOOTPRINT ARE DIFFERENT THINGS. A masked cell (no
covariates — UNDEFINED) is nodata (NaN); a not-minable cell (covariates
present, below the cutoff or filtered) is 0.0; minable is 1.0. A raster
where "undefined" and "false" were the same value would claim knowledge it
does not have — the flag-never-drop discipline, one artifact further down.

THE TWO-REASON WATERMARK, PER REASON, ON EVERY FILE. The verdict's reasons
are written as SEPARATE tags (`watermark_reason_terrain`,
`watermark_reason_economic_parameters`), each saying lifted or unlifted with
its cause and checkpoint, beside the combined `watermark` text. Lifting one
cannot silently lift the other because each tag is derived from its own
reason, not from the combined state — and a collapse to a single flag is
observable (the per-reason tags are what a test reads).

THE ASSOCIATION IS MACHINE-RESOLVABLE. The filename is readable, but no
consumer infers from it: every written file is entered in
`economics.footprints.json` with its (kind, scenario(s), estimator, z) and
sha256, and the same facts sit in its tags. That is the sidecar-resolution
posture TAX.1 established for `data_origin.yaml` — an association the RECORD
resolves, never one a human infers from adjacent names.

THE DIFFERENCE MAP (commit 2) is a SENSITIVITY map, not a resource map —
the area whose minability depends on WHICH PLACEHOLDER CUTOFF IS ASSUMED —
and its tags say so. Its encoding keeps apart what a naive raster would
collapse: 0 = not minable under either; 1 = minable under both; 2 =
minable under b only (the difference); 3 = minable under a only; NaN =
undefined. On today's surfaces every unmasked cell is 1 — stated in
advance (E4.1), not a finding.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import numpy as np

from engine.prospectivity.economics.model import ScenarioFootprints
from engine.prospectivity.economics.watermark import WatermarkVerdict
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.surfaces.builder import SurfaceResult
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import (
    NO_REFUSALS,
    SIDECAR_NAME,
    merge_origin_sidecar,
    write_cog,
)
from engine.prospectivity.validation.claim import ClaimVerdict

ASSOCIATION_NAME = "economics.footprints.json"
FOOTPRINT_ENCODING = (
    "1.0 = minable; 0.0 = NOT minable (covariates present: below the cutoff at this z, "
    "or filtered); nodata (NaN) = UNDEFINED (no covariates) — the mask, not a verdict"
)


def footprint_name(scenario: str, estimator: str, z: float) -> str:
    return f"footprint__{scenario}__{estimator}__z{z:g}.tif"


def _reason_tags(verdict: WatermarkVerdict) -> dict[str, str]:
    """One tag PER REASON, each from its own reason's state — never from the
    combined verdict, so lifting one cannot lift the other through a tag."""
    tags = {}
    for reason in verdict.reasons:
        state = "lifted" if reason.lifted else "UNLIFTED"
        tags[f"watermark_reason_{reason.reason}"] = f"{state}: {reason.cause}; lifts at {reason.lifted_by}"
    tags["watermark_reasons_unlifted"] = str(len(verdict.unlifted))
    tags["watermark"] = verdict.text() or "none (every independent reason lifted)"
    return tags


def _require_same_grid(recorded: dict, grid: PredictionGrid, what: str) -> None:
    if recorded != grid.identity():
        differing = sorted(k for k in set(recorded) | set(grid.identity()) if recorded.get(k) != grid.identity().get(k))
        raise ValueError(
            f"{what} were computed on a grid whose identity differs from the grid handed "
            f"to the writer in {differing} — a footprint must be written on the surface's "
            "own grid (no resampling); refusing"
        )


def _require_mask(minable: np.ndarray, surface: SurfaceResult, estimator: str, what: str) -> np.ndarray:
    """The masked set must be EXACTLY the surface's mask. Returns the mask."""
    surface_mask = ~np.isfinite(surface.mu)
    if minable.shape != surface_mask.shape:
        raise ValueError(f"{what} for {estimator!r} has shape {minable.shape}, the surface {surface_mask.shape}")
    if minable[surface_mask].any():
        raise ValueError(
            f"{what} for {estimator!r} marks {int(minable[surface_mask].sum())} masked cell(s) minable — "
            "a cell with no covariates cannot be a verdict"
        )
    return surface_mask


def _write_one(path: Path, values: np.ndarray, mask: np.ndarray, grid: PredictionGrid, tags: dict) -> str:
    out = values.astype(np.float32).copy()
    out[mask] = np.nan
    write_cog(path, out, grid, tags)
    return file_sha256(path)


def _merge_association(path: Path, entries: dict) -> None:
    existing = {}
    if path.is_file():
        existing = json.loads(path.read_text()).get("files") or {}
    existing.update(entries)
    path.write_text(
        json.dumps(
            {
                "note": (
                    "THE ASSOCIATION of every economics raster with its (kind, scenario(s), "
                    "estimator, z) — resolved from this record and from each file's tags, never "
                    "inferred from a filename"
                ),
                "footprint_encoding": FOOTPRINT_ENCODING,
                "files": dict(sorted(existing.items())),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _origin_entry(footprints_origin: str, footprints: ScenarioFootprints) -> dict:
    """The `data_origin.yaml` entry for an economics raster: the COMPUTED
    origin with its derivation and the authorship it INHERITS from Contract 4
    — never a new `author:` (P2.0: `unrecorded` is not available to new
    work; this cites the contract's own declaration rather than making one)."""
    return {
        "data_origin": footprints_origin,
        "generator": footprints.provenance.get("generator"),
        "derivation": (
            f"combine_origins(surface {footprints.provenance.get('surface_data_origin')}, "
            f"Contract 4 cutoff {footprints.scenario.cutoff.data_origin}) over "
            f"{footprints.provenance.get('rule')}"
        ),
        "author_inherited_from": f"data/economics/scenarios.yaml (author: {footprints.scenario.cutoff.author})",
    }


def write_footprints(
    footprints: ScenarioFootprints,
    grid: PredictionGrid,
    surfaces: Mapping[str, SurfaceResult],
    output_dir: Path | str,
    *,
    claim_verdict: ClaimVerdict,
) -> dict[tuple[str, float], Path]:
    """One scenario's footprints: a raster per (estimator, z), the association
    sidecar, the origin sidecar. Returns (estimator, z) -> path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _require_same_grid(footprints.grid_identity, grid, f"{footprints.scenario.name}'s footprints")
    if set(footprints.levels) != set(surfaces):
        raise ValueError(
            f"{footprints.scenario.name}'s footprints cover {sorted(footprints.levels)} but the "
            f"surfaces cover {sorted(surfaces)} — every estimator, never a subset"
        )
    failing = sorted(item.precondition.value for item in claim_verdict.failures)
    reason_tags = _reason_tags(footprints.watermark)
    written: dict[tuple[str, float], Path] = {}
    association: dict[str, dict] = {}
    origin_entries: dict[str, dict] = {}
    for estimator in sorted(footprints.levels):
        for z, level in footprints.levels[estimator].items():
            mask = _require_mask(level.minable, surfaces[estimator], estimator, f"{footprints.scenario.name} z={z:g}")
            path = output_dir / footprint_name(footprints.scenario.name, estimator, z)
            tags = {
                "kind": "footprint",
                "scenario": footprints.scenario.name,
                "estimator": estimator,
                "z": f"{z:g}",
                "metric": "mu - z*sd",
                "cutoff_kg_m2": f"{footprints.scenario.cutoff_value:g}",
                "cutoff_data_origin": str(footprints.scenario.cutoff.data_origin),
                "encoding": FOOTPRINT_ENCODING,
                "data_origin": footprints.data_origin,
                **reason_tags,
                "publishable": "false" if (failing or footprints.watermark.watermarked) else "true",
                "claim_failing_preconditions": ",".join(failing) if failing else NO_REFUSALS,
                "uncertainty_method": surfaces[estimator].uncertainty_method,
                "uncertainty_semantics": footprints.uncertainty_semantics[estimator],
                "n_minable": str(level.n_minable),
                "n_predictable": str(level.n_predictable),
                "area_m2": f"{level.area_m2:.1f}",
                "slope_filter_note": footprints.filters["max_slope_degrees"]["note"],
                "grid_stack_content_hash": grid.stack_content_hash,
                "grid_dem_content_hash": grid.dem_content_hash,
            }
            digest = _write_one(path, level.minable.astype(np.float32), mask, grid, tags)
            written[(estimator, z)] = path
            association[path.name] = {
                "kind": "footprint",
                "scenario": footprints.scenario.name,
                "estimator": estimator,
                "z": z,
                "sha256": digest,
                "n_minable": level.n_minable,
                "n_predictable": level.n_predictable,
                "fraction_of_predictable": level.fraction_of_predictable,
                "area_m2": level.area_m2,
                "data_origin": footprints.data_origin,
                "watermark": footprints.watermark.to_record(),
            }
            origin_entries[path.name] = _origin_entry(footprints.data_origin, footprints)
    _merge_association(output_dir / ASSOCIATION_NAME, association)
    merge_origin_sidecar(output_dir / SIDECAR_NAME, origin_entries)
    return written
