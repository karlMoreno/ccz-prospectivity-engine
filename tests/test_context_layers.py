"""E5.3 commit 2 — context layers: a second class of layer, never a catalog
entry, carrying its own origin and citation, rendered as geometry.

The mechanism's limit (tests/test_viewer_model.py's docstring) applies: the
page's context section — the checkboxes, the outline rendering, the three
visual treatments — is untested; what is tested is the registry, the API,
and the page's text.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from engine.prospectivity.provenance.contract_versions import file_sha256
from services.api.app import create_app
from services.api.catalog import build_catalog
from services.api.context import CONTEXT_LAYERS, STATES, ContextLayerError, verify_context_layers
from services.api.web import INDEX_HTML


@pytest.fixture(scope="module")
def api(production_run: dict) -> dict:
    app = create_app(production_run["runs_root"])
    return {**production_run, "client": TestClient(app), "run_id": production_run["manifest"].run_id}


def test_every_context_layer_is_on_disk_hashing_as_recorded_with_its_origin_declared_once(api: dict) -> None:
    public = verify_context_layers()
    assert [l["id"] for l in public] == ["coastline", "ccz_management_area"]
    for layer, rec in zip(public, CONTEXT_LAYERS):
        path = Path(rec["path"])
        assert file_sha256(path) == layer["sha256"] and path.stat().st_size == layer["bytes"]
        assert layer["data_origin"] in ("LITERATURE", "AUTHORED") and layer["citation"] and layer["license"] and layer["attribution_text"]
        assert layer["style"]["kind"] == "outline" and "fill" not in json.dumps(layer["style"])
        if rec.get("declared_in_file"):
            assert json.loads(path.read_text())["data_origin"] == layer["data_origin"]
    served = api["client"].get("/context").json()
    assert [l["id"] for l in served["layers"]] == ["coastline", "ccz_management_area"] and served["states"] == STATES
    assert "not catalog entries" in served["note"]
    for layer in served["layers"]:
        r = api["client"].get(layer["url"])
        assert r.status_code == 200 and r.headers["X-Content-Hash"] == layer["sha256"]
        assert "sha256:" + __import__("hashlib").sha256(r.content).hexdigest() == layer["sha256"]
    assert api["client"].get("/context/nope").status_code == 404


def test_a_context_layer_never_appears_in_the_catalog_and_never_inherits_the_runs_watermark(api: dict) -> None:
    """BY NAME: no context layer id or file is a catalog entry; the served
    context records carry NO watermark, watermark_reasons, claim or
    coordinates key, and their origin is their own (LITERATURE / AUTHORED),
    not the run's SYNTHETIC. A registry entry that carries a watermark is
    refused at verification."""
    out = api["out"]
    catalog = build_catalog(json.loads((out / "run_manifest.json").read_text()), out)
    keys = {e["key"] for e in catalog["layers"]}
    served = api["client"].get("/context").json()["layers"]
    for layer in served:
        assert layer["id"] not in keys and layer["file"] not in keys and layer["file"] not in json.dumps(catalog)
        for forbidden in ("watermark", "watermark_reasons", "claim", "coordinates", "publishable"):
            assert forbidden not in layer, (layer["id"], forbidden)
        assert layer["data_origin"] != catalog["data_origin"] == "SYNTHETIC"
        assert layer["class"].startswith("context geometry")
    polluted = [dict(CONTEXT_LAYERS[0]), {**CONTEXT_LAYERS[1], "watermark": catalog["layers"][0]["watermark"]}]
    with pytest.raises(ContextLayerError, match="carries 'watermark' — a run artifact's field on context geometry"):
        verify_context_layers(polluted)
    changed = [{**CONTEXT_LAYERS[0], "sha256": "sha256:" + "0" * 64}, dict(CONTEXT_LAYERS[1])]
    with pytest.raises(ContextLayerError, match="the file changed without its record"):
        verify_context_layers(changed)
    mismatched = [dict(CONTEXT_LAYERS[0]), {**CONTEXT_LAYERS[1], "data_origin": "LITERATURE"}]
    with pytest.raises(ContextLayerError, match="one declaration, not two"):
        verify_context_layers(mismatched)


def test_the_fixture_says_it_is_one_and_the_scale_ratio_is_what_e5_0_measured(api: dict) -> None:
    rec = next(l for l in CONTEXT_LAYERS if l["id"] == "ccz_management_area")
    geo = json.loads(Path(rec["path"]).read_text())
    assert geo["data_origin"] == "AUTHORED" and geo["author"] == "model" and "FIXTURE" in geo["title"] and "NOT the boundary" in geo["title"]
    assert geo["features"][0]["properties"]["fixture"] is True and rec["fixture"] is True and "FIXTURE" in rec["attribution_text"]
    ring = geo["features"][0]["geometry"]["coordinates"][0]
    lons, lats = [p[0] for p in ring], [p[1] for p in ring]
    assert (min(lons), max(lons), min(lats), max(lats)) == (-160.0, -111.4, 0.0, 23.5)
    extent = json.loads((api["out"] / "run_manifest.json").read_text())["prediction_grid"]["extent"]
    def km2(w, s, e, n):
        return (e - w) * 111.32 * math.cos(math.radians((s + n) / 2)) * (n - s) * 111.32
    ratio = km2(-160.0, 0.0, -111.4, 23.5) / km2(*extent)
    assert 33 < ratio < 35 and 2.8 < 100 / ratio < 3.1  # 33.8x; the study extent is ~2.96 % of the zone


def test_the_page_has_a_context_section_with_three_states_outline_only_and_the_citation_where_the_user_sees_it() -> None:
    page = INDEX_HTML.read_text()
    assert 'fetch(`${api}/context`)' in page and "layer.attribution_text" in page and "reg.states[state]" in page
    for state in STATES:
        assert f"ctx-{state}" in page, state
    assert 'type: "line"' in page and '"fill"' not in page.split("loadContext")[1].split("map.on(\"load\"")[0]
    assert "ccz_management_area" not in page and "coastline" not in page.lower().split("<script>")[1]  # the page names no context layer
