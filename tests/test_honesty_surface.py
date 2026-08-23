"""E5.4 — the honesty surface, tested at the MODEL layer (the page renders it
verbatim; the DOM limit of tests/test_viewer_model.py applies — a banner not
drawn cannot fail here, and the fresh-run look in the walkthrough is where
that is checked by eye).

STATED FIRST: the surface under test is SYNTHETIC under a refused verdict,
and every requirement below exists to keep that visible without interaction.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.catalog import build_catalog
from services.api.viewer_model import (
    DERIVATION_NOTE,
    MASKED,
    NO_INFORMATION_STYLE,
    PAIRING_RULE,
    VERDICT_PERSISTENCE_RULE,
    build_viewer_model,
    no_information,
    verdict_block,
)
from services.api.web import INDEX_HTML


@pytest.fixture(scope="module")
def served(production_run: dict) -> dict:
    client = TestClient(create_app(production_run["runs_root"]))
    run_id = production_run["manifest"].run_id
    out = production_run["out"]
    catalog = build_catalog(json.loads((out / "run_manifest.json").read_text()), out)
    return {**production_run, "client": client, "run_id": run_id, "catalog": catalog,
            "model": client.get(f"/runs/{run_id}/viewer").json(), "page": INDEX_HTML.read_text()}


# ─────────────────────────────────────────── requirement 1: the verdict, visible, both halves

def test_the_verdict_names_the_design_the_failing_set_and_the_passing_set_and_is_not_dismissable(served: dict) -> None:
    v = served["model"]["verdict"]
    assert v is not None, "the model serves no verdict — the banner would have nothing to show (mutation H1)"
    assert v["design"] == "leave_one_site_out" == served["catalog"]["claim"]["design"]
    assert v["eligible"] is False and v["is_scientific"] is False
    assert v["failing"] == ["an_acceptance_threshold_existed_before_the_scores"] and len(v["passing"]) == 5 and v["n_preconditions"] == 6
    assert v["headline"].startswith("NOT A VALIDATED CLAIM — 1 of 6 preconditions failed on leave_one_site_out: an_acceptance_threshold")
    assert "SYNTHETIC" in v["watermark"] and "both halves" in v["discrimination_note"]
    assert set(v["other_designs"]) == {"leave_one_cluster_out", "random_k_fold"} and v["other_designs"]["random_k_fold"]["failing"] == sorted(["an_acceptance_threshold_existed_before_the_scores", "spatially_blocked_cross_validation_ran"])
    assert v["persistence"] == VERDICT_PERSISTENCE_RULE and "no dismiss" in v["persistence"]
    page = served["page"]
    assert 'id="verdict"' in page and "v.headline" in page and "v.failing.join" in page and "v.passing.join" in page and "v.other_designs" in page
    # no suppression path: no storage, no close control, no collapse state anywhere in the page
    for forbidden in ("localStorage", "sessionStorage", "dismiss", "collapse", "verdict\").style.display = \"none\"", "#verdict { display: none"):
        assert forbidden not in page, forbidden


def test_an_eligible_fixture_renders_the_passing_state_the_other_direction_of_discrimination() -> None:
    """A banner hard-coded to refuse is as undiscriminating as one that never
    does: the post-checkpoint world — every precondition passed, no watermark
    — must render VALIDATED (mutation H6)."""
    names = ["a", "b", "c", "d", "e", "f"]
    claim = {"design": "leave_one_site_out", "verdicts": {
        "leave_one_site_out": {"eligible": True, "is_scientific": True, "watermark": None, "failing": [], "passing": names,
                               "preconditions": [{"precondition": n, "passed": True} for n in names]},
        "random_k_fold": {"eligible": False, "is_scientific": False, "watermark": None, "failing": ["a"], "passing": names[1:]},
    }}
    v = verdict_block(claim)
    assert v["eligible"] is True and v["is_scientific"] is True
    assert v["headline"] == "VALIDATED CLAIM on leave_one_site_out: all 6 preconditions pass"
    assert v["failing"] == [] and len(v["passing"]) == 6 and v["other_designs"]["random_k_fold"]["eligible"] is False
    watermarked = copy.deepcopy(claim); watermarked["verdicts"]["leave_one_site_out"]["watermark"] = "TRAINING MATRIX ORIGIN SYNTHETIC"
    assert "BUT the run is watermarked" in verdict_block(watermarked)["headline"]
    assert verdict_block(None) is None and verdict_block({"design": "x", "verdicts": {}}) is None
    assert "v.eligible ? \"eligible\"" in INDEX_HTML.read_text()  # the page has the passing treatment, not only the refusing one


# ─────────────────────────────────────────── requirement 2: the layer's own reasons, in its form

def test_each_layer_carries_its_own_reasons_in_its_own_form_with_expiry_and_a_lifted_fixture_discriminates(served: dict) -> None:
    layers = served["model"]["layers"]
    surfaces = [l for l in layers.values() if l["honesty"]["watermark_form"].startswith("surface")]
    econ = [l for l in layers.values() if l["honesty"]["watermark_form"].startswith("economics")]
    assert len(surfaces) == 6 and len(econ) == 18
    for l in surfaces:
        r = l["honesty"]["reasons"]
        assert len(r) == 1 == l["honesty"]["n_reasons"] and r[0]["reason"] == "terrain" and r[0]["lifted"] is False
        assert "SYNTHETIC" in r[0]["text"] and r[0]["expiry"] == "stated in the reason text" and "lifted_by" not in r[0]  # no invented field
    for l in econ:
        r = {x["reason"]: x for x in l["honesty"]["reasons"]}
        assert set(r) == {"terrain", "economic_parameters"} and l["honesty"]["n_reasons"] == 2
        assert r["terrain"]["lifted"] is False and "Checkpoint 1" in r["terrain"]["expiry"]
        assert r["economic_parameters"]["lifted"] is False and "Checkpoint 4" in r["economic_parameters"]["expiry"]
    # the one-lifted fixture, economics side: terrain lifted in the catalog entry -> one lifted, one not
    catalog = copy.deepcopy(served["catalog"])
    for e in catalog["layers"]:
        if e.get("watermark_reasons"):
            for x in e["watermark_reasons"]:
                if x["reason"] == "terrain":
                    x["lifted"] = True
    m2 = build_viewer_model(catalog)
    for l in m2["layers"].values():
        if l["honesty"]["watermark_form"].startswith("economics"):
            assert {x["reason"]: x["lifted"] for x in l["honesty"]["reasons"]} == {"terrain": True, "economic_parameters": False}
    page = served["page"]
    assert "h.reasons" in page and "r.expiry" in page and 'id="honesty"' in page


# ─────────────────────────────────────────── requirement 3: the uncertainty is not optional

def test_the_paired_range_is_always_in_the_legend_and_no_path_in_the_page_hides_the_paired_half(served: dict) -> None:
    m = served["model"]
    for l in m["layers"].values():
        if l["readout"]["paired"] is not None:
            pl = l["paired_legend"]
            assert pl and pl["min"] is not None and pl["max"] is not None and pl["method"] and pl["semantics"] and "no path hides it" in pl["rule"]
        else:
            assert l["paired_legend"] is None
    assert "univariate BY CHOICE" in m["pairing_rule"] and "DECLINED" in m["pairing_rule"] and "three different KINDS" in m["pairing_rule"]
    page = served["page"]
    assert "layer.paired_legend" in page and "current.readout.paired" in page
    assert "hideUncertainty" not in page and "toggle" not in page.lower().split("<script>")[1]  # no suppression path


# ─────────────────────────────────────────── requirement 4: the 99 % fact on the map

def test_the_no_information_region_is_derived_from_recorded_values_marks_2846_of_2880_and_never_the_mask(served: dict) -> None:
    m, out = served["model"], served["out"]
    ni = m["no_information"]
    assert ni is not None, "the model serves no no-information region — the 99 % fact would not be on the map (mutation H4)"
    fit = served["catalog"]["layers"][[e["key"] for e in served["catalog"]["layers"]].index("ordinary_kriging_prediction.tif")]["full_data_fit"]
    assert ni["range_km"] == fit["range_km"] and ni["range_at_candidate_ceiling"] is True  # from the catalog, never recomputed
    assert ni["source"]["field"] == "full_data_fit.range_km" and "never recomputed" in ni["source"]["from"]
    assert ni["n_marked"] == 2846 and ni["n_predictable"] == 2880 and ni["count_label"] == "2,846 of 2,880 predictable cells"
    assert len(ni["cells"]) == 3400 and sum(ni["cells"]) == 2846
    with rasterio.open(out / "ordinary_kriging_prediction.tif") as ds:
        pixels = ds.read(1).ravel()
    assert not any(ni["cells"][i] for i in range(3400) if not np.isfinite(pixels[i]))  # the mask is never marked
    assert "LOWER BOUND" in ni["direction"] or "at least" in ni["direction"]
    assert ni["derivation"] == DERIVATION_NOTE and "never in the page" in DERIVATION_NOTE
    assert ni["style"] == NO_INFORMATION_STYLE and ni["style"]["pattern"] != MASKED["pattern"] and "not stroked" in ni["style"]["contour"]
    k = m["layers"]["ordinary_kriging_prediction.tif"]["no_information"]
    r = m["layers"]["random_forest_prediction.tif"]["no_information"]
    assert k["is_range_source"] is True and "LOWER BOUND" in k["label"] and "2,846 of 2,880 predictable cells" in k["label"] and "largest defensible extent" in k["label"]
    assert k["label"].startswith("beyond one fitted variogram range (21.6 km; a LOWER BOUND — the fit sat at the candidate ceiling) of every station")
    assert r["is_range_source"] is False and r["label"].startswith("no station within 21.6 km") and "no variogram is implied" in r["label"]
    assert all(l["no_information"]["default_on"] is True for l in m["layers"].values())
    # the function itself on a tiny grid: 2x2 cells of 1 degree, one station at the first cell's centre, range 50 km
    grid = {"transform": [1.0, 0.0, 0.0, 0.0, -1.0, 2.0], "width": 2, "height": 2}
    assert build_viewer_model(served["catalog"])["no_information"] is None  # no grid, no mask handed in: nothing derived, nothing faked
    flags = no_information(grid, {"coordinates": {"s": [0.5, 1.5]}}, 50.0)
    assert flags == [False, True, True, True]
    assert no_information(grid, {"coordinates": {"s": [0.5, 1.5]}}, 50.0, predictable=[True, False, True, True]) == [False, False, True, True]
    assert no_information(grid, None, 50.0) is None
    page = served["page"]
    assert "model.no_information.cells" in page and "layer.no_information.label" in page and "swatch noinfo" in page


# ─────────────────────────────────────────── requirement 5: the eighteen uniform rasters explained

def test_the_uniform_layers_carry_their_facts_and_explanation_beside_the_map(served: dict) -> None:
    m = served["model"]
    uniform = [l for l in m["layers"].values() if l["honesty"]["uniform"] is not None]
    assert len(uniform) == 18 and all(l["honesty"]["uniform"]["flag"] is True for l in uniform)
    for l in uniform:
        facts = l["honesty"]["uniform"]["facts"]
        assert facts and "not of the seafloor" in l["honesty"]["uniform"]["statement"]
        if l["kind"] == "difference":
            assert facts["difference_fraction_of_predictable"] == 0.0 and facts["both"] == 2880 and "SENSITIVITY" in l["honesty"]["uniform"]["meaning"]
        else:
            assert facts["n_minable"] == 2880 == facts["n_predictable"]
    assert all(l["honesty"]["uniform"] is None for l in m["layers"].values() if l["kind"] not in ("footprint", "difference"))
    page = served["page"]
    assert "h.uniform" in page and "layer.uniform_today.facts" in page


def test_the_full_data_fit_passes_through_the_model_as_the_catalog_carried_it(served: dict) -> None:
    for e in served["catalog"]["layers"]:
        assert served["model"]["layers"][e["key"]]["full_data_fit"] == e.get("full_data_fit")
    rf = served["model"]["layers"]["random_forest_prediction.tif"]["honesty"]["fit_facts"]
    assert rf["n_estimators"] == 500  # the registry dependence, visible in the layer's panel
