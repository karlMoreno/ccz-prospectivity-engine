"""The LAYER EXPORT (E5.2) — every raster the viewer reads, as FLAT ARRAYS.

    <out>/*_prediction.tif + *_uncertainty.tif  ──► export/<estimator>.surface.json   (mu[] AND sd[] — one file, the pair)
    <out>/economics/<raster>.tif                ──► export/<raster stem>.json          (values[] — the codes)
    <out>/export/data_origin.yaml                    the audit's sidecar for every export (TAX.1's form)

KARL'S DECISION (E5.0 §2): FLAT ARRAYS, NOT GeoJSON. The comparison was
MEASURED on one paired surface (kriging mu + sd, 3,400 cells), not estimated:

    form                                            bytes      gzip
    GeoJSON polygons, full precision               756,255    37,680
    GeoJSON polygons, 3 dp                         687,209    31,855
    GeoJSON points (cell centres), 3 dp            407,609    10,996
    GeoJSON polygons, 3 dp, MASKED CELLS DROPPED   584,609    27,091   <- the failure
    flat arrays (transform + mu[] + sd[], 3 dp)     42,643       957

Flat arrays are 16x smaller than points and 700x smaller than polygons,
because the geometry is ONE affine transform the manifest already carries
(`prediction_grid.transform`): a GeoJSON polygon per cell repeats that
transform 3,400 times per layer and, over 21 layers, 14.4 MB of the same
grid written over and over. The cell at flat index i sits at row i // width,
column i % width, and its centre is transform * (col + 0.5, row + 0.5) — the
same georeferencing the raster carries, which is what the round-trip test
compares against (never the transform this file quotes).

THE FOURTH ROW IS THE ONE TO READ. Dropping the 520 masked cells saves
~100 KB on the polygon form, which is why someone will do it, and it is the
exact failure this module refuses: a masked cell is UNDEFINED (no
covariates — E4.2's mask, kept apart from the footprint) and must stay
distinguishable from a cell with a value. Here it is `null`, at its own
index, never 0, never absent. `json.dumps` would otherwise emit the
non-standard token `NaN` for a numpy NaN — Python reads it back, a browser's
`JSON.parse` rejects it — so every array is converted explicitly and
serialized with `allow_nan=False`, which raises rather than lets one through.

A DERIVED ARTIFACT, CARRYING THE ORIGIN MACHINERY DELIBERATELY. Every other
artifact in this project carries its origin where the format provides
(GeoTIFF tags, a sidecar, a manifest field); JSON provides nothing, so the
export carries it in its own body: `data_origin` COMPUTED by combine_origins
over its inputs (never declared — the export of a SYNTHETIC raster is
SYNTHETIC; of an AUTHORED footprint, AUTHORED); the watermark IN THE FORM
THE SOURCE CARRIES IT — a surface's one reason as a string, an economics
raster's TWO reasons per reason (E5.1 §2: the asymmetry is by design; an
export that normalised them is how a reader would come to believe surfaces
have an economics caveat); the failing preconditions by name; and a
chaining `source` hash recomputed from the raster's bytes, so the emitter
can verify which bytes this file renders. An export is verified against the
PIXELS by the emitter before the manifest records it (`_verify_exports`),
and hashed into `output_hashes` under `export/<basename>`.

THE PAIR IS ONE FILE. A surface export holds `mu` AND `sd`: the pairing rule
has been structural since E2.1 (`Estimator.predict`), and a browser that can
fetch a prediction without its uncertainty would be the first place the
rule could be broken. Two economics rasters that belong to no pair are one
file each.

WHERE IT LIVES: inside the run directory (`<out>/export/`), part of E5.5's
RUN_LAYOUT and the manifest's full listing. Outside `data/`, so outside the
origin audit's walk — stated, not relied on: the sidecar written beside the
exports is the declaration the audit would read if a run were ever committed
under `data/` (the same cost E5.5's BACKLOG entry records for the rest of the
run directory).

CHECKPOINT 1 (stated, not built): ~1.96 M cells is ~24 MB raw as flat arrays
and not a page load; tiles arrive via TiTiler inside the API, and the catalog
entry gains a `tiles_url` beside `data_url` — a sibling key in a dict, no
schema change (E5.1's catalog is dict content; verified in the walkthrough).
Not added here: a field with no consumer is a field nobody has tested.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import rasterio
import yaml

from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import SIDECAR_NAME

FORMAT = "ccz-flat-array/1"
EXPORT_DIR = "export"
DECIMALS = 3
GENERATOR = "engine.prospectivity.export.flat.export_layers"
DETERMINISM_BASIS = (
    "a pure function of the source raster's pixels (rounded to 3 dp, NaN -> null), its "
    "sidecar or association-record entry, and the prediction grid's identity; no sampling, "
    "no RNG, keys sorted, compact separators — the same bytes from the same inputs anywhere"
)
LAYOUT_NOTE = (
    "row-major, north-up: the value at flat index i is row i // width, column i % width; "
    "cell centre = transform * (col + 0.5, row + 0.5) in EPSG:4326 (lon, lat)"
)
MASK_ENCODING = (
    "null = UNDEFINED (no covariates at this cell — the mask, not a value): never 0, never "
    "absent, never NaN (allow_nan=False refuses one); the null set equals the raster's NaN set"
)
WHY_NOT_GEOJSON = {
    "measured_on": "kriging mu + sd, 3,400 cells (E5.0 §2, 2026-08-22)",
    "bytes": {
        "geojson_polygons_full_precision": 756255,
        "geojson_polygons_3dp": 687209,
        "geojson_points_3dp": 407609,
        "geojson_polygons_3dp_masked_cells_DROPPED": 584609,
        "flat_arrays_3dp": 42643,
    },
    "gzip": {
        "geojson_polygons_full_precision": 37680,
        "geojson_polygons_3dp": 31855,
        "geojson_points_3dp": 10996,
        "geojson_polygons_3dp_masked_cells_DROPPED": 27091,
        "flat_arrays_3dp": 957,
    },
    "note": "the geometry is one transform the manifest carries; the fourth row is the failure this format refuses",
}


def flatten(values: np.ndarray) -> list[float | None]:
    """Row-major list, rounded to DECIMALS, NaN -> None at its own index —
    the mask survives as null, never as 0 and never by omission."""
    rounded = np.round(np.asarray(values, dtype=np.float64), DECIMALS)
    return [None if not np.isfinite(v) else float(v) for v in rounded.ravel().tolist()]


def dumps(payload: dict) -> bytes:
    """Deterministic, compact, and NaN-refusing: a numpy NaN that escaped
    `flatten` raises here rather than becoming the token `NaN`."""
    return (json.dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def _grid_block(grid: PredictionGrid) -> dict:
    identity = grid.identity()
    return {
        "crs": identity["crs"], "width": identity["width"], "height": identity["height"],
        "transform": list(identity["transform"]), "extent": list(identity["extent"]),
        "n_cells": identity["n_cells"], "layout": LAYOUT_NOTE,
    }


def _read(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        return dataset.read(1), dataset.tags()


def export_surface(estimator: str, written: Mapping[str, Path], grid: PredictionGrid, out_dir: Path) -> Path:
    """One estimator's PAIRED surfaces -> one export file. The origin, the
    watermark (a string: one reason), `publishable` and the failing
    preconditions come from the sidecar the writer produced (carrier 2)."""
    prediction, uncertainty = Path(written["prediction"]), Path(written["uncertainty"])
    sidecar = json.loads(Path(written["provenance"]).read_text())
    mu, _ = _read(prediction)
    sd, _ = _read(uncertainty)
    origin = combine_origins([sidecar["data_origin"], sidecar["data_origin"]])  # both rasters: the pair's inputs
    payload = {
        "format": FORMAT,
        "kind": "surface_pair",
        "estimator": estimator,
        "fields": {"mu": "predicted abundance, kg/m² (prediction)", "sd": "paired uncertainty (uncertainty)"},
        "pairing_note": "mu and sd are ONE file on purpose: the pairing rule (E2.1) must not be breakable in a browser",
        "source": {
            "prediction": {"key": prediction.name, "sha256": file_sha256(prediction)},
            "uncertainty": {"key": uncertainty.name, "sha256": file_sha256(uncertainty)},
            "sidecar": {"key": Path(written["provenance"]).name, "sha256": file_sha256(Path(written["provenance"]))},
        },
        "grid": _grid_block(grid),
        "decimals": DECIMALS,
        "mu": flatten(mu),
        "sd": flatten(sd),
        "n_values": int(np.isfinite(mu).sum()),
        "n_masked": int((~np.isfinite(mu)).sum()),
        "mask_encoding": MASK_ENCODING,
        "data_origin": origin.value,
        "data_origin_note": "COMPUTED by combine_origins over the two source rasters' computed origin — never declared here",
        "watermark_form": "surface: one reason (terrain), a string — as the source carries it (E5.1 §2: not normalised)",
        "watermark": sidecar["watermark"],
        "watermark_reasons": None,
        "publishable": sidecar["publishable"],
        "claim_failing_preconditions": sidecar["claim_failing_preconditions"],
        "claim_eligible": sidecar["claim_eligible"],
        "uncertainty_method": sidecar["surface"]["uncertainty_method"],
        "uncertainty_semantics": sidecar["surface"]["uncertainty_semantics"],
        "legend": {k: sidecar["surface"].get(k) for k in ("mu_min", "mu_max", "sd_min", "sd_max", "n_distinct_values")},
        "generator": GENERATOR,
        "determinism_basis": DETERMINISM_BASIS,
        "why_not_geojson": WHY_NOT_GEOJSON,
    }
    path = out_dir / f"{estimator}.surface.json"
    path.write_bytes(dumps(payload))
    return path


def export_economics_raster(file: str, entry: dict, economics_dir: Path, grid: PredictionGrid, out_dir: Path) -> Path:
    """One economics raster -> one export file. The two reasons and the
    computed origin come from E4.2's association record entry; the failing
    preconditions and `publishable` from the raster's own tags."""
    raster = economics_dir / file
    values, tags = _read(raster)
    origin = combine_origins([entry["data_origin"]])
    kind = entry["kind"]
    payload = {
        "format": FORMAT,
        "kind": kind,
        "estimator": entry["estimator"],
        "z": entry["z"],
        "scenario": entry.get("scenario") if kind == "footprint" else None,
        "pair": [entry["scenario_a"], entry["scenario_b"]] if kind == "difference" else None,
        "source": {"key": f"economics/{file}", "sha256": file_sha256(raster), "record": "economics/economics.footprints.json"},
        "grid": _grid_block(grid),
        "decimals": DECIMALS,
        "values": flatten(values),
        "n_values": int(np.isfinite(values).sum()),
        "n_masked": int((~np.isfinite(values)).sum()),
        "mask_encoding": MASK_ENCODING,
        "encoding": tags.get("encoding"),
        "meaning": tags.get("meaning"),
        # the record keeps a footprint's counts at the entry's top level and a
        # difference's under `counts` (E4.2); mirrored as the emitter records them
        "counts": (
            {k: entry[k] for k in ("n_minable", "n_predictable", "fraction_of_predictable", "area_m2") if k in entry}
            if kind == "footprint"
            else {**(entry.get("counts") or {}), "difference_fraction_of_predictable": entry.get("difference_fraction_of_predictable"), "area_m2": entry.get("area_m2")}
        ),
        "cutoff_kg_m2": tags.get("cutoff_kg_m2"),
        "data_origin": origin.value,
        "data_origin_note": "COMPUTED by combine_origins over the source raster's computed origin (the record's) — never declared here",
        "watermark_form": "economics: two independent reasons, per reason — as the source carries them (E5.1 §2: not collapsed)",
        "watermark": None,
        "watermark_reasons": entry["watermark"]["reasons"],
        "publishable": tags.get("publishable") == "true",
        "claim_failing_preconditions": sorted(p for p in (tags.get("claim_failing_preconditions") or "").split(",") if p),
        "generator": GENERATOR,
        "determinism_basis": DETERMINISM_BASIS,
    }
    path = out_dir / f"{Path(file).stem}.json"
    path.write_bytes(dumps(payload))
    return path


def _origin_sidecar(exports: Mapping[str, tuple[Path, dict]], out_dir: Path) -> Path:
    """The audit's marker for every export, in TAX.1's form: SYNTHETIC-by-
    inheritance exports carry the generator and the determinism basis;
    AUTHORED-by-inheritance exports (the economics) carry the derivation and
    the authorship they inherit — the same form E4.2 wrote and the same open
    question (BACKLOG §3, `author_inherited_from`)."""
    files = {}
    for path, payload in exports.values():
        entry = {"data_origin": payload["data_origin"], "generator": GENERATOR, "determinism_basis": DETERMINISM_BASIS,
                 "derivation": f"flat-array export of {json.dumps(payload['source'], sort_keys=True)} — {LAYOUT_NOTE}"}
        if payload["data_origin"] == DataOrigin.AUTHORED.value:
            entry["author_inherited_from"] = "data/economics/scenarios.yaml (author: unrecorded) via economics/data_origin.yaml"
        files[path.name] = entry
    sidecar = out_dir / SIDECAR_NAME
    sidecar.write_text(
        "# ORIGIN DECLARATIONS for the flat-array exports in this directory (E5.2),\n"
        "# in the audit's sidecar form. Every origin is COMPUTED by combine_origins\n"
        "# over the source raster's origin; nothing here is declared by hand.\n"
        + yaml.safe_dump({"files": files}, sort_keys=True)
    )
    return sidecar


def export_layers(
    out_dir: Path | str,
    *,
    surfaces_written: Mapping[str, Mapping[str, Path]],
    economics_dir: Path | str,
    grid: PredictionGrid,
) -> dict[str, Path]:
    """Every surface pair and every economics raster named by the association
    record -> `<out_dir>/export/`. Iterates what was WRITTEN, never a
    directory listing; resolves economics rasters from the record, never a
    name. Returns {export key: path} with keys `export/<basename>`."""
    out = Path(out_dir) / EXPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    economics_dir = Path(economics_dir)
    exports: dict[str, tuple[Path, dict]] = {}
    for estimator in sorted(surfaces_written):
        path = export_surface(estimator, surfaces_written[estimator], grid, out)
        exports[f"{EXPORT_DIR}/{path.name}"] = (path, json.loads(path.read_bytes()))
    record = json.loads((economics_dir / "economics.footprints.json").read_text())
    for file in sorted(record["files"]):
        path = export_economics_raster(file, record["files"][file], economics_dir, grid, out)
        exports[f"{EXPORT_DIR}/{path.name}"] = (path, json.loads(path.read_bytes()))
    sidecar = _origin_sidecar(exports, out)
    written = {key: path for key, (path, _) in exports.items()}
    written[f"{EXPORT_DIR}/{sidecar.name}"] = sidecar
    return written
