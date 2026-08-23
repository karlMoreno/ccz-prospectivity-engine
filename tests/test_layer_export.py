"""E5.2 — the flat-array layer export: the round trip, the mask, the origin
machinery carried deliberately, the chaining hash, determinism, the size pin.

STATED FIRST: every export here renders a SYNTHETIC surface or an AUTHORED
placeholder footprint; every one carries a watermark and a refused verdict,
and the pixels it renders measure nothing about the seafloor. What is under
test is that the export is a FAITHFUL rendering — values, mask and geometry
— and that the provenance a JSON file cannot carry in metadata is carried in
its body and verified before the manifest records it.

The ground truth throughout is OUTSIDE the record: the raster's own pixels
and georeferencing read with rasterio, never the transform the export quotes.
"""

from __future__ import annotations

import gzip
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.export.flat import (
    DECIMALS,
    EXPORT_DIR,
    FORMAT,
    WHY_NOT_GEOJSON,
    dumps,
    export_economics_raster,
    export_layers,
    flatten,
)
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.surfaces.grid import PredictionGrid

ESTIMATORS = ("mean_baseline", "ordinary_kriging", "random_forest")


def _strict(path: Path) -> dict:
    """Parse as a BROWSER would: any NaN/Infinity token is an error."""
    def refuse(token):
        raise ValueError(f"non-standard JSON token {token!r}")
    return json.loads(path.read_bytes(), parse_constant=refuse)


@pytest.fixture(scope="module")
def exports(production_run: dict) -> dict:
    out = production_run["out"]
    return {**production_run, "dir": out / EXPORT_DIR, "raw": json.loads((out / "run_manifest.json").read_text())}


def test_values_coordinates_and_mask_survive_the_round_trip_against_the_rasters_own_georeferencing(exports: dict) -> None:
    """For every surface pair and every economics raster: each exported value
    equals the pixel to the stated rounding (codes exactly); the cell centre
    reconstructed from the export's LAYOUT (index -> row, col) using the
    RASTER's transform equals the raster's own `xy()` — never the transform
    the export carries, which would be checking the export against itself;
    and the raster's transform is what the export quotes."""
    out, d = exports["out"], exports["dir"]
    for est in ESTIMATORS:
        payload = _strict(d / f"{est}.surface.json")
        assert payload["format"] == FORMAT and payload["decimals"] == DECIMALS and payload["kind"] == "surface_pair"
        for field, kind in (("mu", "prediction"), ("sd", "uncertainty")):
            with rasterio.open(out / f"{est}_{kind}.tif") as ds:
                pixels, transform, (h, w) = ds.read(1), ds.transform, ds.shape
                sample = [(0, 0), (h - 1, w - 1), (17, 50), (3, 99)]
                centres = {rc: ds.xy(*rc) for rc in sample}
            values = payload[field]
            assert len(values) == h * w == payload["grid"]["n_cells"] == 3400
            for i, v in enumerate(values):
                p = pixels[i // w, i % w]
                if v is None:
                    assert not np.isfinite(p), (field, i)
                else:
                    assert abs(v - float(p)) <= 0.5 * 10 ** -DECIMALS + 1e-9, (field, i)
            for (row, col), (x, y) in centres.items():
                i = row * w + col
                assert (i // payload["grid"]["width"], i % payload["grid"]["width"]) == (row, col)
                assert transform * (col + 0.5, row + 0.5) == pytest.approx((x, y))
            assert tuple(payload["grid"]["transform"]) == tuple(transform)[:6] and payload["grid"]["width"] == w
    for name in ("footprint__MARKET_STANDARD__random_forest__z1", "difference__MARKET_STANDARD__STRATEGIC_SUBSIDIZED__ordinary_kriging__z0"):
        payload = _strict(d / f"{name}.json")
        with rasterio.open(out / "economics" / f"{name}.tif") as ds:
            pixels = ds.read(1)
        codes = [None if not np.isfinite(p) else float(p) for p in pixels.ravel()]
        assert payload["values"] == codes  # codes are exact, rounding changes nothing


def test_the_mask_is_the_rasters_nan_set_exactly_and_a_moved_mask_of_the_same_size_is_not(exports: dict) -> None:
    """SET EQUALITY over cell indices, not a count: E4.2's 520 NaN cells are
    the ground truth, and the null set must be THOSE cells. The separating
    construction: a mask shifted by one cell has the same count (520) and a
    different set — a count-only assertion would pass it."""
    out, d = exports["out"], exports["dir"]
    for est in ESTIMATORS:
        payload = _strict(d / f"{est}.surface.json")
        with rasterio.open(out / f"{est}_prediction.tif") as ds:
            pixels = ds.read(1)
        nans = {int(i) for i in np.flatnonzero(~np.isfinite(pixels.ravel()))}
        nulls_mu = {i for i, v in enumerate(payload["mu"]) if v is None}
        nulls_sd = {i for i, v in enumerate(payload["sd"]) if v is None}
        assert nulls_mu == nulls_sd == nans and len(nans) == 520 == payload["n_masked"]
        assert payload["n_values"] == 2880 and 0.0 not in {payload["mu"][i] for i in nans if payload["mu"][i] is not None}
        shifted = {(i + 1) % 3400 for i in nans}
        assert len(shifted) == len(nans) and shifted != nulls_mu
    assert "null" in payload["mask_encoding"] and "never 0" in payload["mask_encoding"]
    # the function itself: NaN -> None at its own index; nothing dropped
    assert flatten(np.array([[1.23456, np.nan], [0.0, -2.0]])) == [1.235, None, 0.0, -2.0]


def test_no_export_contains_a_nan_token_and_the_serializer_refuses_one(exports: dict) -> None:
    """json.dumps emits the non-standard token `NaN` for a numpy NaN — Python
    reads it back, a browser's JSON.parse rejects it. Every export parses
    under a strict parser, contains no such token, and `dumps` raises rather
    than emit one."""
    for path in exports["dir"].glob("*.json"):
        _strict(path)  # a bare NaN/Infinity TOKEN fails here; the word inside a string ("nodata (NaN)") does not
        assert b":NaN" not in path.read_bytes() and b",NaN" not in path.read_bytes(), path.name
    with pytest.raises(ValueError, match="Out of range float"):
        dumps({"values": [float("nan")]})


def test_origin_is_computed_and_each_export_carries_its_sources_watermark_form_with_the_right_number_of_reasons(exports: dict) -> None:
    """Surfaces: ONE reason, a string, `watermark_reasons` None, origin
    SYNTHETIC (combine_origins over two SYNTHETIC rasters). Economics: TWO
    reasons per reason with lifted / lifted_by / cause, origin AUTHORED
    (the least-real input), `watermark` None. DISCRIMINATION: an entry
    with the terrain reason lifted exports one lifted and one unlifted."""
    d = exports["dir"]
    for est in ESTIMATORS:
        p = _strict(d / f"{est}.surface.json")
        assert p["data_origin"] == "SYNTHETIC" and "combine_origins" in p["data_origin_note"]
        assert isinstance(p["watermark"], str) and "SYNTHETIC" in p["watermark"] and p["watermark_reasons"] is None
        assert p["watermark_form"].startswith("surface: one reason") and p["publishable"] is False
        assert p["claim_failing_preconditions"] == ["an_acceptance_threshold_existed_before_the_scores"]
    econ = sorted(q for q in d.glob("*.json") if not q.name.endswith(".surface.json"))
    assert len(econ) == 18
    for path in econ:
        p = _strict(path)
        assert p["data_origin"] == "AUTHORED" and p["watermark"] is None and p["watermark_form"].startswith("economics: two")
        reasons = {r["reason"]: r for r in p["watermark_reasons"]}
        assert set(reasons) == {"terrain", "economic_parameters"}
        assert reasons["terrain"]["lifted"] is False and "Checkpoint 1" in reasons["terrain"]["lifted_by"] and reasons["terrain"]["cause"]
        assert reasons["economic_parameters"]["lifted"] is False and "Checkpoint 4" in reasons["economic_parameters"]["lifted_by"]
        assert p["publishable"] is False and p["claim_failing_preconditions"] == ["an_acceptance_threshold_existed_before_the_scores"]
        assert p["encoding"] and (p["kind"] == "difference") == ("SENSITIVITY" in (p.get("meaning") or ""))
    # the lifted-terrain fixture, at the exporter: the record entry says terrain lifted
    record = json.loads((exports["out"] / "economics" / "economics.footprints.json").read_text())
    file = "footprint__MARKET_STANDARD__ordinary_kriging__z0.tif"
    entry = json.loads(json.dumps(record["files"][file]))
    for r in entry["watermark"]["reasons"]:
        if r["reason"] == "terrain":
            r["lifted"] = True
    grid = PredictionGrid.from_stack(exports["out"] / "features" / "stack")
    tmp = exports["tree"] / "lifted_export"
    tmp.mkdir(exist_ok=True)
    path = export_economics_raster(file, entry, exports["out"] / "economics", grid, tmp)
    lifted = {r["reason"]: r["lifted"] for r in _strict(path)["watermark_reasons"]}
    assert lifted == {"terrain": True, "economic_parameters": False}


def test_the_chaining_hashes_match_the_source_rasters_by_recomputation_and_the_manifest_records_each_export(exports: dict) -> None:
    out, d, raw = exports["out"], exports["dir"], exports["raw"]
    for est in ESTIMATORS:
        p = _strict(d / f"{est}.surface.json")
        for kind in ("prediction", "uncertainty"):
            assert p["source"][kind]["key"] == f"{est}_{kind}.tif"
            assert p["source"][kind]["sha256"] == file_sha256(out / f"{est}_{kind}.tif") == raw["output_hashes"][f"{est}_{kind}.tif"]
        assert p["source"]["sidecar"]["sha256"] == file_sha256(out / f"{est}.provenance.json")
        recorded = raw["surfaces"][est]["export"]
        assert recorded["file"] == f"{est}.surface.json" and recorded["fields"] == ["mu", "sd"]
        assert recorded["sha256"] == file_sha256(d / recorded["file"]) == raw["output_hashes"][f"export/{recorded['file']}"]
    for file, entry in raw["economics"]["rasters"].items():
        p = _strict(d / entry["export"]["file"])
        assert p["source"]["key"] == f"economics/{file}" and p["source"]["sha256"] == file_sha256(out / "economics" / file) == entry["sha256"]
        assert entry["export"]["sha256"] == file_sha256(d / entry["export"]["file"]) == raw["output_hashes"][f"export/{entry['export']['file']}"]
        assert p["data_origin"] == entry["data_origin"] == "AUTHORED"
    assert raw["provenance_chain"]["links"]["exports"]["files"] == 22
    assert sum(k.startswith("export/") for k in raw["output_hashes"]) == 22


def test_two_exports_of_the_same_rasters_are_byte_identical_here_and_from_another_tree(exports: dict, tmp_path: Path) -> None:
    """Determinism at the exporter: the same rasters exported again into a
    fresh directory, and again from a COPY of the run directory in another
    tree, give byte-identical files — no path, no timestamp, no RNG enters.
    (The harness's two-tree test covers the same property through the
    manifest's output_hashes; this one is the exporter alone.)"""
    out = exports["out"]
    written = {est: {"prediction": out / f"{est}_prediction.tif", "uncertainty": out / f"{est}_uncertainty.tif", "provenance": out / f"{est}.provenance.json"} for est in ESTIMATORS}
    grid = PredictionGrid.from_stack(out / "features" / "stack")
    again = export_layers(tmp_path / "again", surfaces_written=written, economics_dir=out / "economics", grid=grid)
    elsewhere_run = tmp_path / "elsewhere" / "deeper" / "run"
    shutil.copytree(out, elsewhere_run)
    written2 = {est: {k: elsewhere_run / v.name for k, v in w.items()} for est, w in written.items()}
    elsewhere = export_layers(tmp_path / "elsewhere_out", surfaces_written=written2, economics_dir=elsewhere_run / "economics", grid=PredictionGrid.from_stack(elsewhere_run / "features" / "stack"))
    assert set(again) == set(elsewhere) == {f"export/{p.name}" for p in exports["dir"].iterdir()} and len(again) == 22
    for key, path in again.items():
        original = exports["dir"] / Path(key).name
        assert path.read_bytes() == original.read_bytes() == elsewhere[key].read_bytes(), key
        assert str(out) not in path.read_text() and str(elsewhere_run) not in elsewhere[key].read_text()


def test_the_export_sizes_match_the_measured_form_pinned_so_inflation_is_visible(exports: dict) -> None:
    """E5.0 §2 measured the arrays-only flat form at 42,643 B (kriging mu +
    sd, 3 dp). The export adds its provenance body (~3.3 KB). Pinned by
    literal for the two registry-independent surfaces; a band for RF (its
    values depend on the registry); the economics exports and the total.
    A format change that inflates the export fails here by number."""
    d = exports["dir"]
    sizes = {p.name: p.stat().st_size for p in d.iterdir()}
    assert sizes["ordinary_kriging.surface.json"] == 45_974
    assert sizes["mean_baseline.surface.json"] == 45_982
    assert 38_000 < sizes["random_forest.surface.json"] < 48_000
    assert all(16_000 < v < 17_500 for k, v in sizes.items() if k.startswith(("footprint__", "difference__")))
    total = sum(sizes.values())
    assert 430_000 < total < 480_000 and len(sizes) == 22
    assert len(gzip.compress((d / "ordinary_kriging.surface.json").read_bytes(), 9)) < 3_500
    assert WHY_NOT_GEOJSON["bytes"]["flat_arrays_3dp"] == 42_643 and WHY_NOT_GEOJSON["bytes"]["geojson_polygons_3dp_masked_cells_DROPPED"] == 584_609
    # the arrays alone reproduce E5.0's number to within the rounding of a few values
    p = _strict(d / "ordinary_kriging.surface.json")
    arrays_only = len(json.dumps({"transform": p["grid"]["transform"], "shape": [p["grid"]["height"], p["grid"]["width"]], "mu": p["mu"], "sd": p["sd"]}, separators=(",", ":")).encode())
    assert abs(arrays_only - 42_643) < 200
