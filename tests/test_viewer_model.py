"""E5.3 — the viewer: the presentation model (tested), the page (what can be
observed without a browser), the pins (asserted without a network).

THE TEST MECHANISM'S LIMIT, stated in those words: nothing here runs
JavaScript. The DOM, the rendering and the interaction are UNTESTED. What
IS tested is the function the page consumes (`build_viewer_model`), the
page's text (which names it references, which it must not contain, which
hashes it declares), and the one formula the page repeats (`cell_index`),
pinned against the raster's own georeferencing. A visual defect — a wrong
colour drawn, a banner not shown, a select that does not disable — cannot
fail any test in this file.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest
import rasterio

from services.api.catalog import build_catalog
from services.api.viewer_model import (
    BACKGROUND,
    BINNING_RULE,
    CATEGORICAL_PALETTE,
    MASKED,
    MESSAGES,
    SEQUENTIAL_RAMP,
    STATE_LABELS,
    build_viewer_model,
    cell_index,
)
from services.api.web import CDN_PINS, COASTLINE, INDEX_HTML, STATIC_FILES, WEB_DIR
from engine.prospectivity.provenance.contract_versions import file_sha256

REPO_ROOT = Path(__file__).resolve().parent.parent
# THE NAMES THE VIEWER MUST NOT KNOW: this project's layer types, estimators,
# axes and unit. The model module and the page are grepped for them.
PROJECT_NAMES = ("mean_baseline", "ordinary_kriging", "random_forest", "prediction", "uncertainty",
                 "footprint", "difference", "estimator", "scenario", "kg_m2", "kg/m", "MARKET_STANDARD")


@pytest.fixture(scope="module")
def model(production_run: dict) -> dict:
    out = production_run["out"]
    catalog = build_catalog(json.loads((out / "run_manifest.json").read_text()), out)
    before = json.dumps(catalog, sort_keys=True)
    built = build_viewer_model(catalog)
    assert json.dumps(catalog, sort_keys=True) == before  # never mutates the catalog
    return {**production_run, "catalog": catalog, "model": built}


def test_the_model_builds_controls_cells_and_layers_from_the_catalog_and_names_its_rules(model: dict) -> None:
    m, c = model["model"], model["catalog"]
    assert [x["axis"] for x in m["controls"]] == list(c["grid"]["axes"])
    for control in m["controls"]:
        assert control["label"] == c["grid"]["axis_labels"][control["axis"]]
        assert [v["value"] for v in control["values"]] == c["grid"]["axes"][control["axis"]]
        assert all(v["label"] for v in control["values"])
    assert m["n_layers"] == 24 == len(m["layers"]) and set(m["layers"]) == {e["key"] for e in c["layers"]}
    assert len(m["cells"]) == 72 and len(m["canonical"]) == 24
    assert m["binning_rule"] == BINNING_RULE and "never written back" in m["binning_rule"]
    assert all(e["legend"]["binning"] is None for e in c["layers"])  # the catalog's slot stays null
    assert "PRESENTATION" in m["exception_note"] and "uniform_today" in m["exception_note"]
    # every present canonical cell resolves to exactly one layer, and every layer is some cell's
    keys = [cell["key"] for cell in m["canonical"] if cell["state"] == "present"]
    assert len(keys) == len(set(keys)) == 24 and set(keys) == set(m["layers"])
    # THE NEIGHBOUR STATES the control panel shows, precomputed per canonical cell in the
    # control's value order: from a value-layer cell, the other two layer kinds are PRESENT
    # (switching kinds snaps to their first present cell) and z / scenario / pair are
    # not_applicable; from a categorical cell, z and scenario are present, pair not_applicable
    by_key = {cell["key"]: cell for cell in m["canonical"]}
    first = by_key[keys[0]]
    states = {axis: [n["state"] for n in ns] for axis, ns in first["neighbours"].items()}
    assert states[m["controls"][0]["axis"]] == ["present"] * 4  # the page's first draft showed 'absent' here
    assert all(v == "present" for v in states[m["controls"][1]["axis"]])
    assert all(all(x == "not_applicable" for x in states[a]) for a in list(states)[2:])
    categorical = next(cell for cell in m["canonical"] if cell["coordinates"].get("pair") is None and cell["coordinates"].get("scenario") is not None)
    cstates = {axis: [n["state"] for n in ns] for axis, ns in categorical["neighbours"].items()}
    assert set(cstates["z"]) == {"present"} and set(cstates["scenario"]) == {"present"} and set(cstates["pair"]) == {"not_applicable"}
    assert all(n["key"] in m["layers"] for cell in m["canonical"] for ns in cell["neighbours"].values() for n in ns if n["state"] != "absent")


def test_the_three_states_carry_three_distinct_labels_and_the_page_has_three_treatments(model: dict) -> None:
    m = model["model"]
    assert set(STATE_LABELS) == {"present", "not_applicable", "absent"} and len(set(STATE_LABELS.values())) == 3
    seen = {cell["state"]: cell["label"] for cell in m["cells"]}
    assert seen == {"present": STATE_LABELS["present"], "not_applicable": STATE_LABELS["not_applicable"]}  # no absent cell today
    assert m["state_labels"] == STATE_LABELS
    page = INDEX_HTML.read_text()
    for state in STATE_LABELS:
        assert f"state-{state}" in page, state  # three option classes, one per state
    assert "model.state_labels[st]" in page and "cell.neighbours[control.axis]" in page  # labels AND states come from the model, never computed by the page


def test_a_foreign_catalog_with_different_axes_layer_types_and_names_builds_a_model_with_no_code_change() -> None:
    """THE FLEXIBILITY REQUIREMENT'S ONLY REAL TEST — and it tests a FUNCTION,
    not a rendered panel (E5.3 §0). Three axes this project does not have,
    layer types and probe names nobody has written, a unit that is not kg/m².
    The grid's cells are part of the catalog contract and are supplied by the
    fixture the way catalog.py would supply them."""
    axes = {"quantity": ["temperature", "ice_fraction"], "probe": ["alpha", "beta", "gamma"], "season": ["winter", "summer"]}
    applicable = {"temperature": ["probe", "season"], "ice_fraction": ["probe"]}
    entries, canonical, cells = [], [], []
    def entry(q, p, s):
        key = f"{q}__{p}" + (f"__{s}" if s else "") + ".tif"
        entries.append({
            "key": key, "sha256": "sha256:" + "1" * 64, "kind": q, "coordinates": {"quantity": q, "probe": p, "season": s},
            "axes_not_applicable": [a for a in axes if a not in applicable[q] and a != "quantity"], "pair": None,
            "data_origin": "MEASURED", "publishable": True, "watermark_form": "none", "watermark": None, "watermark_reasons": None,
            "legend": {"min": -40.0, "max": 5.0, "quantity": "surface temperature, K", "units": "K", "binning": None,
                       "ramp": "sequential", "format": {"kind": "number", "decimals": 1, "unit_label": "K"}},
            "export": {"file": key + ".json", "sha256": "sha256:" + "2" * 64}, "data_url": f"/runs/r/files/export/{key}.json", "data_field": "values",
        })
        return key
    present = {}
    for q in axes["quantity"]:
        for p in axes["probe"]:
            for s in (axes["season"] if "season" in applicable[q] else [None]):
                present[(q, p, s)] = entry(q, p, s)
                canonical.append({"coordinates": {"quantity": q, "probe": p, "season": s}, "state": "present", "key": present[(q, p, s)]})
    for q in axes["quantity"]:
        for p in axes["probe"]:
            for s in axes["season"]:
                if "season" in applicable[q]:
                    cells.append({"coordinates": {"quantity": q, "probe": p, "season": s}, "state": "present", "axes_not_applicable": [], "key": present[(q, p, s)]})
                else:
                    cells.append({"coordinates": {"quantity": q, "probe": p, "season": s}, "state": "not_applicable", "axes_not_applicable": ["season"], "key": present[(q, p, None)]})
    catalog = {
        "run_id": "lunar-volatiles-01", "content_hash": "sha256:" + "3" * 64, "data_origin": "MEASURED",
        "layers": entries, "training_stations": None, "claim": {"design": "x", "verdicts": {}},
        "grid": {"axes": axes, "axis_labels": {"quantity": "Quantity", "probe": "Probe", "season": "Season"},
                 "value_labels": {"quantity": {"temperature": "Temperature", "ice_fraction": "Ice fraction"}},
                 "applicable_axes": applicable, "cells": cells, "canonical": {"cells": canonical}},
    }
    m = build_viewer_model(catalog)
    assert [c["axis"] for c in m["controls"]] == ["quantity", "probe", "season"] and len(m["controls"]) == 3
    assert m["controls"][0]["values"][1]["label"] == "Ice fraction" and m["controls"][1]["values"][0]["label"] == "alpha"
    assert m["n_layers"] == 6 + 3 == 9 and all(l["format"]["unit_label"] == "K" and l["ramp"] == "sequential" for l in m["layers"].values())
    assert all(len(l["bins"]) == 7 and l["edges"][0] == -40.0 and l["edges"][-1] == 5.0 for l in m["layers"].values())
    assert {cell["state"] for cell in m["cells"]} == {"present", "not_applicable"} and len(m["cells"]) == 12
    assert m["stations"] is None
    # neighbours on the foreign axes: from a temperature cell, season values are present; from an
    # ice_fraction cell, season is not an axis; switching quantity snaps to a present cell
    temp = next(c for c in m["canonical"] if c["coordinates"]["quantity"] == "temperature")
    ice = next(c for c in m["canonical"] if c["coordinates"]["quantity"] == "ice_fraction")
    assert [n["state"] for n in temp["neighbours"]["season"]] == ["present", "present"]
    assert [n["state"] for n in ice["neighbours"]["season"]] == ["not_applicable", "not_applicable"]
    assert [n["state"] for n in ice["neighbours"]["quantity"]] == ["present", "present"] and temp["neighbours"]["quantity"][1]["key"].startswith("ice_fraction__")
    # the model module and the page know none of THIS project's names
    # the model reads two CATALOG FIELD NAMES by name (uncertainty_semantics / uncertainty_method —
    # E5.1's, inherited from the manifest); those two strings are stripped before the grep, and
    # nothing else containing a project name may remain. The page is grepped whole.
    src = (REPO_ROOT / "services" / "api" / "viewer_model.py").read_text().replace("uncertainty_semantics", "").replace("uncertainty_method", "")
    page = INDEX_HTML.read_text()
    for name in PROJECT_NAMES:
        assert name not in src, f"viewer_model.py names {name!r}"
        assert name not in page, f"index.html names {name!r}"


def test_the_paired_uncertainty_is_in_every_surface_readout_with_its_semantics_and_the_pair_is_one_file(model: dict) -> None:
    m = model["model"]
    paired = [l for l in m["layers"].values() if l["readout"]["paired"] is not None]
    unpaired = [l for l in m["layers"].values() if l["readout"]["paired"] is None]
    assert len(paired) == 6 and len(unpaired) == 18
    for l in paired:
        u = l["readout"]["paired"]
        assert u["field"] in ("mu", "sd") and u["field"] != l["data_field"] and u["semantics"] and u["method"]
        assert "always shown with the value" in u["note"]
        other = next(x for x in m["layers"].values() if x["data_url"] == l["data_url"] and x["key"] != l["key"])
        assert other["data_field"] == u["field"]  # the other half, from the same export file
    semantics = {l["readout"]["paired"]["semantics"] for l in paired}
    assert len(semantics) == 3  # three estimators, three KINDS of sd — the string travels with the number
    page = INDEX_HTML.read_text()
    assert "current.readout.paired" in page and "unc.semantics" in page


def test_the_hover_formula_matches_the_rasters_own_georeferencing_and_values_spot_checked_against_the_raster(model: dict) -> None:
    """cell_index (the one formula the page repeats) against rasterio's
    `index()` on the raster, and the export's value at that index against the
    raster's pixel — not against the export's own transform."""
    out = model["out"]
    layer = model["model"]["layers"]["ordinary_kriging_prediction.tif"]
    export = json.loads((out / "export" / Path(layer["data_url"]).name).read_text())
    grid = export["grid"]
    with rasterio.open(out / "ordinary_kriging_prediction.tif") as ds:
        pixels = ds.read(1)
        # interior points only: on an exact cell EDGE (lat 12.0 = 14.7 - 27 x 0.1) floor((lat - f) / e)
        # and rasterio's inverse-transform floor disagree by one in the last float place —
        # implementation-defined on the edge, identical everywhere inside a cell
        for lon, lat in [(-121.23, 12.87), (-126.49, 14.69), (-116.51, 11.31), (-118.05, 13.95), (-125.03, 12.04)]:
            row, col = ds.index(lon, lat)
            got = cell_index(grid, lon, lat)
            assert got == (row, col, row * ds.width + col), (lon, lat)
            value, pixel = export[layer["data_field"]][got[2]], pixels[row, col]
            if value is None:
                assert not np.isfinite(pixel)
            else:
                assert abs(value - float(pixel)) <= 0.0005
        assert cell_index(grid, -130.0, 12.0) is None and cell_index(grid, -120.0, 20.0) is None
    sd_field = layer["readout"]["paired"]["field"]
    with rasterio.open(out / "ordinary_kriging_uncertainty.tif") as ds:
        row, col = ds.index(-121.23, 12.87)
        assert abs(export[sd_field][row * ds.width + col] - float(ds.read(1)[row, col])) <= 0.0005


def test_masked_cells_have_a_treatment_outside_every_ramp_and_the_background(model: dict) -> None:
    m = model["model"]
    assert MASKED["color"] not in SEQUENTIAL_RAMP and MASKED["color"] not in CATEGORICAL_PALETTE and MASKED["color"] != BACKGROUND
    assert MASKED["pattern"] == "hatched" and "not a value" in MASKED["label"]
    for l in m["layers"].values():
        colors = {b["color"] for b in l["bins"]}
        assert m["masked"]["color"] not in colors and l["readout"]["masked_label"] == MASKED["label"]
    page = INDEX_HTML.read_text()
    assert "model.masked.color" in page and "swatch masked" in page and "repeating-linear-gradient" in page


def test_the_no_run_states_are_distinct_messages_and_the_page_distinguishes_them(model: dict) -> None:
    assert len({MESSAGES[k] for k in ("api_unreachable", "no_runs", "no_layers", "layer_missing")}) == 4
    assert "connection failure, not an empty run" in MESSAGES["api_unreachable"] and "broken layer, not an empty one" in MESSAGES["layer_missing"]
    page = INDEX_HTML.read_text()
    assert "Cannot reach the API" in page and "serves no runs" in page and "model.messages.no_layers" in page and "model.messages.layer_missing" in page
    assert "overlay.setProps({ layers: [] })" in page  # a missing layer clears the map AND shows the banner
    assert "NO TIMELINE" not in page and "scrubber" not in page.lower() and "timeline" not in page.lower()


def test_the_uniform_layers_carry_their_explanation_and_the_page_shows_it(model: dict) -> None:
    m = model["model"]
    uniform = [l for l in m["layers"].values() if l["uniform_today"] is not None]
    assert len(uniform) == 18 and all(l["uniform_today"]["flag"] is True and "not of the seafloor" in l["uniform_today"]["note"] for l in uniform)
    assert sum("SENSITIVITY" in (l["uniform_today"]["meaning"] or "") for l in uniform) == 6
    assert "UNIFORM today" in INDEX_HTML.read_text()


def test_the_stations_come_from_the_manifest_with_their_own_origin_kept_apart_from_the_runs(model: dict) -> None:
    s = model["model"]["stations"]
    assert s["n"] == 35 == len(s["coordinates"]) and s["data_origin"] == "MEASURED" != model["model"]["run_data_origin"] == "SYNTHETIC"
    assert "MEASURED" in s["asymmetry_note"] and "SYNTHETIC" in s["asymmetry_note"]
    page = INDEX_HTML.read_text()
    assert "model.stations.coordinates" in page and "ScatterplotLayer" in page and "master_observations" not in page


def test_the_station_legend_carries_both_origins_and_a_station_reads_as_a_place_not_a_value(model: dict) -> None:
    """E5.3 commit 3 (adversarial review): the legend row names the stations'
    origin AND the surface's — a label naming one origin flattens the
    asymmetry (mutation S1). The station style is a point with an outline
    in no ramp colour; the station readout has no value field; the
    clustering NUMBER is not computed here (stated), the points are drawn."""
    m = model["model"]; s = m["stations"]
    assert s["legend_label"] == "35 training stations — origin MEASURED (the surface is SYNTHETIC)"
    assert "MEASURED" in s["legend_label"] and "SYNTHETIC" in s["legend_label"]
    assert s["style"]["kind"] == "point" and s["style"]["fill"] not in SEQUENTIAL_RAMP + CATEGORICAL_PALETTE and s["style"]["fill"] != MASKED["color"]
    assert s["readout"]["fields"] == ["id", "lon", "lat"] and "value" not in s["readout"]["fields"] and s["readout"]["origin_suffix"] == "origin MEASURED"
    assert "991 km" in s["geometry_note"] and "not computed" in s["geometry_note"]
    page = INDEX_HTML.read_text()
    assert "model.stations.legend_label" in page and "pickable: true" in page and "model.stations.readout" in page
    assert "layers.push(stationLayer())" in page  # drawn over every surface layer, not optional


def test_the_cdn_pins_are_exact_versions_with_integrity_hashes_equal_to_the_recorded_ones_without_a_network() -> None:
    page = INDEX_HTML.read_text()
    tags = re.findall(r'<(script|link)\b([^>]*)>', page)
    external = []
    for tag, attrs in tags:
        url = re.search(r'(?:src|href)="(https?://[^"]+)"', attrs)
        if url:
            integrity = re.search(r'integrity="([^"]+)"', attrs)
            cross = re.search(r'crossorigin="anonymous"', attrs)
            external.append((tag, url.group(1), integrity.group(1) if integrity else None, bool(cross)))
    recorded = {(p["tag"], p["url"], p["integrity"], True) for p in CDN_PINS}
    assert set(external) == recorded and len(external) == 3
    for p in CDN_PINS:
        assert f"@{p['version']}/" in p["url"] and p["integrity"].startswith("sha384-") and p["license"] in ("BSD-3-Clause", "MIT")
    assert not re.search(r'https?://(?!cdn\.jsdelivr\.net/npm/(maplibre-gl@5\.24\.0|deck\.gl@9\.3\.10)/)', page.split("<script>")[0].split("<!--")[0] + page.split("-->")[1].split("<script>")[0])
    # the vendored coastline: hash recorded, file present, public domain, cited where a user sees it
    assert file_sha256(WEB_DIR / COASTLINE["file"]) == COASTLINE["sha256"] and (WEB_DIR / COASTLINE["file"]).stat().st_size == COASTLINE["bytes"]
    assert COASTLINE["license"] == "public domain" and "Natural Earth" in COASTLINE["citation"] and COASTLINE["data_origin"] == "LITERATURE"
    # the coastline's citation reaches the user through the context registry (E5.3 commit 2), beside its checkbox and in the footer
    assert "layer.attribution_text" in page and set(STATIC_FILES) == {"index.html", COASTLINE["file"]}


def test_the_api_serves_the_viewer_model_the_page_and_the_allow_listed_files(production_run: dict) -> None:
    from fastapi.testclient import TestClient
    from services.api.app import create_app
    client = TestClient(create_app(production_run["runs_root"]))
    run_id = production_run["manifest"].run_id
    m = client.get(f"/runs/{run_id}/viewer").json()
    assert m["n_layers"] == 24 and m["attribution"]["basemap"].startswith("none") and m["attribution"]["coastline"].startswith("Coastline")
    assert client.get("/").status_code == 200 and b"<title>" in client.get("/").content
    assert client.get("/web/ne_110m_coastline.geojson").status_code == 200 and client.get("/web/index.html").status_code == 200
    assert client.get("/web/../pyproject.toml").status_code == 404 and client.get("/web/other.js").status_code == 404
    assert client.post(f"/runs/{run_id}/viewer").status_code == 405


def test_the_first_non_python_files_are_outside_the_origin_audits_walk_confirmed_not_assumed() -> None:
    import subprocess
    walked = subprocess.run(["git", "ls-files", "--", "data", "tests/fixtures"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.split()
    assert not any(p.startswith("apps/web/") for p in walked)
    assert all(Path(p).suffix not in (".html", ".js", ".css") for p in walked)
