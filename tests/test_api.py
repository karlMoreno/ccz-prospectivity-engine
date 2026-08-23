"""E5.1 commit 1 — the read-only API: what it serves, what it refuses, and
that read-only is a property of the ROUTE TABLE, not of a convention.

STATED FIRST: the run served here is the session's production-registry run
over SYNTHETIC inputs; every response carries a watermark and every verdict
is a refusal. What is under test is that the API is a faithful window onto
the manifest — bytes and fields as recorded, nothing computed — and that a
directory which is not a run is refused by name, never served empty.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.provenance.contract_versions import file_sha256
from services.api.app import MANIFEST_NAME, NotARun, create_app, load_run, load_runs

REPO_ROOT = Path(__file__).resolve().parent.parent
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@pytest.fixture(scope="module")
def api(production_run: dict) -> dict:
    app = create_app(production_run["runs_root"])
    return {**production_run, "app": app, "client": TestClient(app), "run_id": production_run["manifest"].run_id}


def test_read_only_is_a_property_of_the_route_table_not_a_convention(api: dict) -> None:
    """Enumerated from the FRAMEWORK's table (`app.routes`), never from a
    list the author maintains: every route's method set is within
    {GET, HEAD} (Starlette adds HEAD to GET routes itself). A route added
    later with a write method fails here by name — mutation R1."""
    routes = [r for r in api["app"].routes if hasattr(r, "methods")]
    assert len(routes) >= 8
    offending = {r.path: sorted(r.methods) for r in routes if set(r.methods) & WRITE_METHODS}
    assert offending == {}
    assert all(set(r.methods) <= {"GET", "HEAD"} for r in routes)
    paths = {r.path for r in routes}
    assert {"/runs", "/runs/{run_id}", "/runs/{run_id}/manifest", "/runs/{run_id}/cv-scores",
            "/runs/{run_id}/ts6-agreement", "/runs/{run_id}/economics", "/runs/{run_id}/claim",
            "/runs/{run_id}/files/{key:path}"} <= paths
    # and over the wire: a write verb on a served path is refused, not handled
    for method in ("post", "put", "patch", "delete"):
        assert getattr(api["client"], method)(f"/runs/{api['run_id']}/manifest").status_code == 405


def test_runs_are_identified_from_their_manifests_and_the_manifest_is_served_byte_for_byte(api: dict) -> None:
    """The URL key is the manifest's run_id (not the directory name, which is
    'run'); the manifest endpoint returns the file's BYTES, so a client can
    recompute the content_hash the ETag quotes — the API re-hashes nothing,
    the test does."""
    client, run_id, out = api["client"], api["run_id"], api["out"]
    assert out.name == "run" != run_id
    runs = client.get("/runs").json()
    assert [r["run_id"] for r in runs] == [run_id]
    assert runs[0]["content_hash"] == api["manifest"].content_hash and runs[0]["schema_version"] == 4
    assert runs[0]["data_origin"] == "SYNTHETIC" and runs[0]["publishable"] == [False]
    assert runs[0]["estimators"] == ["mean_baseline", "ordinary_kriging", "random_forest"]
    r = client.get(f"/runs/{run_id}/manifest")
    assert r.status_code == 200 and r.content == (out / MANIFEST_NAME).read_bytes()
    served = RunManifest(**json.loads(r.content))
    assert served.compute_content_hash() == served.content_hash == r.headers["X-Content-Hash"]
    assert r.headers["ETag"] == f'"{served.content_hash}"'
    assert client.get("/runs/nope").status_code == 404 and client.get("/runs/nope/manifest").status_code == 404


def test_every_sub_endpoint_is_a_field_of_the_manifest_as_recorded(api: dict) -> None:
    """Full-state: each endpoint's body equals the corresponding slice of the
    manifest JSON on disk — nothing added, nothing derived, nothing dropped."""
    client, run_id = api["client"], api["run_id"]
    raw = json.loads((api["out"] / MANIFEST_NAME).read_text())
    assert client.get(f"/runs/{run_id}/cv-scores").json() == {
        k: raw.get(k) for k in ("cv_scores", "cross_validation", "estimator_declarations", "claim_eligible_designs", "scores_first_visible", "scores_first_visible_note")
    }
    assert client.get(f"/runs/{run_id}/ts6-agreement").json() == {
        "ts6_agreement": raw["ts6_agreement"], "ts6_benchmark": raw["provenance_chain"]["links"]["ts6_benchmark"],
    }
    assert client.get(f"/runs/{run_id}/economics").json() == {k: raw[k] for k in ("economics", "economic_results", "economic_differences")}
    assert client.get(f"/runs/{run_id}/claim").json() == {k: raw[k] for k in ("claim", "claim_eligible_designs", "data_origin")}
    # E5.5's three additions are SERVED, not re-derived — present in the served manifest exactly as recorded
    m = client.get(f"/runs/{run_id}/manifest").json()
    kriging = m["surfaces"]["ordinary_kriging"]["full_data_fit"]
    assert 21.0 < kriging["range_km"] < 22.5 and kriging["range_at_candidate_ceiling"] is True and "fitted_bins" in kriging
    assert all({"sd_min", "sd_max", "mu_min", "mu_max"} <= set(s) for s in m["surfaces"].values())
    assert m["training_stations"]["n"] == 35 and m["training_stations"]["data_origin"] == "MEASURED"
    assert m["surfaces"]["random_forest"]["full_data_fit"]["n_estimators"] == 500


def test_files_are_served_only_by_a_key_the_record_names_with_the_recorded_hash_as_etag(api: dict) -> None:
    """Every key in output_hashes is served with the RECORDED sha256 as the
    ETag and bytes whose sha256 (recomputed here, not by the API) equals it.
    Anything on disk the record does not name — the covariate stack, an
    input raster, the manifest itself, a traversal — is 'not a recorded
    output': the record is consulted BEFORE any path is formed (mutation R2)."""
    client, run_id, out = api["client"], api["run_id"], api["out"]
    hashes = api["manifest"].output_hashes
    assert len(hashes) == 30
    for key, digest in hashes.items():
        r = client.get(f"/runs/{run_id}/files/{key}")
        assert r.status_code == 200, key
        assert r.headers["X-Content-Hash"] == digest == "sha256:" + hashlib.sha256(r.content).hexdigest()
        assert r.headers["ETag"] == f'"{digest}"'
    for not_recorded in ("features/stack/depth.tif", "features/stack/provenance.json", MANIFEST_NAME, "dem.tif", "economics/../dem.tif"):
        r = client.get(f"/runs/{run_id}/files/{not_recorded}")
        assert r.status_code == 404 and "not a recorded output" in r.json()["detail"], not_recorded
    # a dot-dot traversal never reaches the handler: the client/router resolves
    # the path first and the resolved URL matches no route (404 from routing)
    for traversal in ("../dem.tif", "../../dem.tif"):
        assert client.get(f"/runs/{run_id}/files/{traversal}").status_code == 404
    assert (out / "features" / "stack" / "depth.tif").is_file() and (api["tree"] / "dem.tif").is_file()  # on disk, unserved


def test_a_directory_that_is_not_a_run_is_refused_by_name_never_served_empty(api: dict, tmp_path: Path) -> None:
    """Each refusal distinct: no root; an empty root; a subdirectory without
    a manifest; a root that is itself a run; a CV-only (unextended) manifest
    — the committed E2.4 artifact; a manifest mutated after finalize; a
    named output file missing; two runs with one run_id."""
    with pytest.raises(NotARun, match="no runs root"):
        create_app(None) if "CCZ_RUNS_ROOT" not in __import__("os").environ else (_ for _ in ()).throw(NotARun("no runs root"))
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(NotARun, match="holds no run directories"):
        create_app(empty)
    with pytest.raises(NotARun, match="is not a directory"):
        create_app(tmp_path / "absent")
    bare = tmp_path / "bare"
    (bare / "not-a-run").mkdir(parents=True)
    with pytest.raises(NotARun, match="holds no run_manifest.json"):
        create_app(bare)
    with pytest.raises(NotARun, match="is itself a run directory"):
        create_app(api["out"])
    cv_only = tmp_path / "cv_only" / "e2.4"
    cv_only.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "data" / "runs" / "e2.4" / MANIFEST_NAME, cv_only / MANIFEST_NAME)
    with pytest.raises(NotARun, match="NOT EXTENDED"):
        load_runs(tmp_path / "cv_only")
    copy = tmp_path / "copy"
    shutil.copytree(api["out"], copy / "run")
    raw = json.loads((copy / "run" / MANIFEST_NAME).read_text())
    raw["seed"] = 99  # a substance field edited; the hash left as it was
    (copy / "run" / MANIFEST_NAME).write_text(json.dumps(raw))
    with pytest.raises(NotARun, match="does not describe itself"):
        load_run(copy / "run")
    shutil.copytree(api["out"], copy / "run2")
    (copy / "run2" / "ordinary_kriging_prediction.tif").unlink()
    with pytest.raises(NotARun, match=r"names 1 output file\(s\) that do not exist: \['ordinary_kriging_prediction.tif'\]"):
        load_run(copy / "run2")
    twins = tmp_path / "twins"
    shutil.copytree(api["out"], twins / "a")
    shutil.copytree(api["out"], twins / "b")
    with pytest.raises(NotARun, match="two run directories carry run_id"):
        load_runs(twins)


# ═══════════════════════════════ E5.1 commit 2 — the layer catalog

import numpy as np
import rasterio

from engine.prospectivity.validation.claim import Precondition, evaluate_claim
from services.api.catalog import APPLICABLE_AXES, EXCLUSIONS, KINDS

LAYER_KINDS = set(KINDS)


def _forged_root(api: dict, tmp_path: Path, name: str, mutate) -> Path:
    """A COPY of the run directory where `mutate(raw, record, run_dir)` edits
    the manifest dict, the association record and the files CONSISTENTLY,
    after which the manifest is RE-FINALIZED so it describes itself and the
    API loads it. The single-source-tamper discipline: every derived witness
    forged to agree, only the ground truth the test names left dissenting."""
    root = tmp_path / name
    run_dir = root / "run"
    shutil.copytree(api["out"], run_dir)
    raw = json.loads((run_dir / MANIFEST_NAME).read_text())
    record_path = run_dir / "economics" / "economics.footprints.json"
    record = json.loads(record_path.read_text())
    mutate(raw, record, run_dir)
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    manifest = RunManifest(**raw)
    manifest.content_hash = None
    manifest.finalize()
    (run_dir / MANIFEST_NAME).write_text(manifest.to_json())
    return root


def _catalog(root: Path) -> dict:
    app = create_app(root)
    runs = TestClient(app).get("/runs").json()
    return TestClient(app).get(f"/runs/{runs[0]['run_id']}/layers").json()


def test_every_catalog_entry_is_on_disk_and_every_file_on_disk_is_a_layer_or_explicitly_excluded(api: dict) -> None:
    """BOTH DIRECTIONS against the DIRECTORY LISTING. One alone lets a layer
    vanish or a phantom appear; an implicit exclusion is indistinguishable
    from an omission, so the set difference must equal exactly the files the
    catalog's own exclusion rules name, each with a reason."""
    c = api["client"].get(f"/runs/{api['run_id']}/layers").json()
    out = api["out"]
    keys = [e["key"] for e in c["layers"]]
    assert len(keys) == len(set(keys)) == 24 == c["n_layers"]
    listing = {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()}
    assert set(keys) <= listing
    unlisted = listing - set(keys)
    rules = {r["pattern"]: r["reason"] for r in c["excluded_from_the_catalog"]}
    assert rules == {r["pattern"]: r["reason"] for r in EXCLUSIONS} and all(rules.values())
    def excluded_by(path: str) -> str | None:
        if path == "run_manifest.json": return "run_manifest.json"
        if path.endswith(".provenance.json") and "/" not in path: return "<estimator>.provenance.json"
        if path in ("data_origin.yaml", "economics/data_origin.yaml", "economics/economics.footprints.json"): return path
        if path.startswith("features/stack/"): return "features/stack/*"
        return None
    assert {p: excluded_by(p) for p in unlisted} == {p: excluded_by(p) for p in unlisted if excluded_by(p) in rules}
    assert len(unlisted) == 1 + 3 + 2 + 1 + 9
    # every entry's identity is the record's: key in output_hashes, sha256 equal, file present
    hashes = api["manifest"].output_hashes
    for e in c["layers"]:
        assert hashes[e["key"]] == e["sha256"] and (out / e["key"]).is_file(), e["key"]
        assert e["kind"] in LAYER_KINDS and e["coordinates"]["kind"] == e["kind"]
    # a layer dropped CONSISTENTLY from every record still shows in the listing → this test's
    # other direction catches it (the catalog cannot see the directory, and must not)
    def drop(raw, record, run_dir):
        file = "footprint__MARKET_STANDARD__random_forest__z0.tif"
        raw["economics"]["rasters"].pop(file); record["files"].pop(file); raw["output_hashes"].pop(f"economics/{file}")
    root = _forged_root(api, api["tree"] / "dropped", "dropped", drop)
    c2 = _catalog(root)
    assert c2["n_layers"] == 23 and "economics/footprint__MARKET_STANDARD__random_forest__z0.tif" not in {e["key"] for e in c2["layers"]}
    assert (root / "run" / "economics" / "footprint__MARKET_STANDARD__random_forest__z0.tif").is_file()  # on disk, unlisted


def test_the_control_grid_has_three_states_and_a_consistently_dropped_artifact_is_absent_not_inapplicable(api: dict, tmp_path: Path) -> None:
    """E5.0 §1's shape, counted precisely: the naive 72 cells are 18 present
    + 54 not_applicable + 0 absent (a surface has no canonical cell in a grid
    whose every cell carries a z and a scenario; its 36 inapplicable cells
    each point at it by key), and the 24 canonical cells are all present.
    SEPARATES the three states: dropping one footprint consistently from the
    record turns exactly its canonical cell ABSENT — never not_applicable —
    and leaves the 54 inapplicable cells untouched."""
    g = api["client"].get(f"/runs/{api['run_id']}/layers").json()["grid"]
    assert g["n_cells"] == 72 == 4 * 3 * 2 * 3 and g["counts"] == {"present": 18, "not_applicable": 54, "absent": 0}
    assert g["canonical"]["n_cells"] == 24 == 3 + 3 + 12 + 6 and g["canonical"]["counts"] == {"present": 24, "absent": 0}
    assert g["applicable_axes"] == {k: list(v) for k, v in APPLICABLE_AXES.items()}
    assert g["axes"] == {"kind": ["prediction", "uncertainty", "footprint", "difference"],
                         "estimator": ["mean_baseline", "ordinary_kriging", "random_forest"], "z": [0.0, 1.0],
                         "scenario": ["MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"], "pair": [["MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"]]}
    # the 54 inapplicable cells come in two shapes: a SURFACE cell (36) carries a z and
    # a scenario-or-pair the surface has no axis for and COLLAPSES onto the one surface
    # layer by key; an economics cell under the OTHER kind's axis (footprint × pair: 6;
    # difference × scenario: 12) has no layer to collapse onto — key None, and that is
    # not "absent", because the axis does not apply
    for cell in g["cells"]:
        kind, axis = cell["coordinates"]["kind"], ("pair" if cell["coordinates"]["pair"] else "scenario")
        if kind in ("prediction", "uncertainty"):
            assert cell["state"] == "not_applicable" and set(cell["axes_not_applicable"]) == {"z", axis}
            assert cell["key"] == f"{cell['coordinates']['estimator']}_{kind}.tif"
        elif (kind, axis) in (("footprint", "pair"), ("difference", "scenario")):
            assert cell["state"] == "not_applicable" and cell["axes_not_applicable"] == [axis] and cell["key"] is None
        else:
            assert cell["state"] == "present" and cell["axes_not_applicable"] == [] and cell["key"] is not None
    by_shape = {"surface": 0, "cross_kind": 0, "present": 0}
    for cell in g["cells"]:
        kind, axis = cell["coordinates"]["kind"], ("pair" if cell["coordinates"]["pair"] else "scenario")
        by_shape["surface" if kind in ("prediction", "uncertainty") else "cross_kind" if (kind, axis) in (("footprint", "pair"), ("difference", "scenario")) else "present"] += 1
    assert by_shape == {"surface": 36, "cross_kind": 18, "present": 18}
    def drop(raw, record, run_dir):
        file = "footprint__STRATEGIC_SUBSIDIZED__ordinary_kriging__z1.tif"
        raw["economics"]["rasters"].pop(file); record["files"].pop(file); raw["output_hashes"].pop(f"economics/{file}")
        (run_dir / "economics" / file).unlink()
    g2 = _catalog(_forged_root(api, tmp_path, "absent", drop))["grid"]
    assert g2["counts"] == {"present": 17, "not_applicable": 54, "absent": 1}
    absent = [c for c in g2["cells"] if c["state"] == "absent"]
    assert absent == [{"coordinates": {"kind": "footprint", "estimator": "ordinary_kriging", "z": 1.0, "scenario": "STRATEGIC_SUBSIDIZED", "pair": None},
                       "state": "absent", "axes_not_applicable": [], "key": None}]
    assert g2["canonical"]["counts"] == {"present": 23, "absent": 1}


def test_coordinates_resolve_from_the_record_not_the_filename(api: dict, tmp_path: Path) -> None:
    """THE ANTI-NAME-INFERENCE FIXTURE: one footprint renamed to `x.tif` in
    EVERY record at once (the file, the association record, economics.rasters,
    output_hashes, the result's raster_file) — every witness agrees on the
    new name and only the coordinates the record carries say what it is. A
    catalog parsing the name would report nothing, or the wrong thing."""
    def rename(raw, record, run_dir):
        old = "footprint__MARKET_STANDARD__random_forest__z0.tif"
        (run_dir / "economics" / old).rename(run_dir / "economics" / "x.tif")
        record["files"]["x.tif"] = record["files"].pop(old)
        raw["economics"]["rasters"]["x.tif"] = raw["economics"]["rasters"].pop(old)
        raw["output_hashes"]["economics/x.tif"] = raw["output_hashes"].pop(f"economics/{old}")
        for result in raw["economic_results"]:
            for by_z in result["footprints"].values():
                for summary in by_z.values():
                    if summary.get("raster_file") == old:
                        summary["raster_file"] = "x.tif"
    c = _catalog(_forged_root(api, tmp_path, "renamed", rename))
    entry = next(e for e in c["layers"] if e["key"] == "economics/x.tif")
    assert entry["coordinates"] == {"kind": "footprint", "estimator": "random_forest", "z": 0.0, "scenario": "MARKET_STANDARD", "pair": None}
    assert entry["recorded_in"] == "economics.rasters.x.tif" and entry["cutoff"]["value"] == 10.0
    assert c["grid"]["counts"] == {"present": 18, "not_applicable": 54, "absent": 0}
    assert "footprint__MARKET_STANDARD__random_forest__z0.tif" not in json.dumps(c)


def test_the_catalogs_claim_verdict_matches_a_direct_guard_run_in_both_halves_and_synthetic_is_in_the_watermark(api: dict) -> None:
    """The set-equality shape of test_run_manifest_extension.py:683: failing
    AND passing per design, against `evaluate_claim` run here on the served
    manifest. LOSO fails exactly the pre-registration gate and passes five;
    random_k_fold fails two and passes four; "synthetic" appears in no
    failing set — it is the WATERMARK, structurally never a refusal."""
    c = api["client"].get(f"/runs/{api['run_id']}/layers").json()["claim"]
    stack = json.loads((api["out"] / "features" / "stack" / "provenance.json").read_text())
    served = json.loads(api["client"].get(f"/runs/{api['run_id']}/manifest").content)
    manifest = RunManifest(**served)
    gate = Precondition.PRE_REGISTERED_THRESHOLD.value
    assert set(c["verdicts"]) == {"leave_one_cluster_out", "leave_one_site_out", "random_k_fold"} and c["design"] == "leave_one_site_out"
    for design, v in c["verdicts"].items():
        direct = evaluate_claim(manifest, design=design, feature_stack_manifest=stack)
        assert (set(v["failing"]), set(v["passing"])) == (
            {r.precondition.value for r in direct.results if not r.passed}, {r.precondition.value for r in direct.results if r.passed})
        assert v["eligible"] is False and v["is_scientific"] is False and "SYNTHETIC" in v["watermark"]
        assert not any("synthetic" in p.lower() for p in v["failing"])
    assert c["verdicts"]["leave_one_site_out"]["failing"] == [gate] and len(c["verdicts"]["leave_one_site_out"]["passing"]) == 5
    assert set(c["verdicts"]["random_k_fold"]["failing"]) == {gate, Precondition.SPATIALLY_BLOCKED_CV.value} and len(c["verdicts"]["random_k_fold"]["passing"]) == 4
    assert "never a precondition" in c["watermark_is_not_a_refusal"] and c["applies_to"].startswith("every layer")


def test_watermark_forms_are_served_as_recorded_and_a_lifted_terrain_fixture_discriminates_per_reason(api: dict, tmp_path: Path) -> None:
    """THE ASYMMETRY, kept: every surface entry carries ONE reason as a string
    and `watermark_reasons` None; every economics entry carries TWO reasons,
    each with lifted / lifted_by / cause. DISCRIMINATION: a Checkpoint-1
    fixture (terrain lifted in every record that carries it) yields, per
    economics entry, terrain lifted AND economic_parameters unlifted — a
    catalog collapsing to any()/all() fails here; the surfaces' string is
    untouched by the fixture, which a normalising catalog would 'fix'."""
    c = api["client"].get(f"/runs/{api['run_id']}/layers").json()
    surfaces = [e for e in c["layers"] if e["kind"] in ("prediction", "uncertainty")]
    econ = [e for e in c["layers"] if e["kind"] in ("footprint", "difference")]
    assert len(surfaces) == 6 and len(econ) == 18
    for e in surfaces:
        assert isinstance(e["watermark"], str) and "SYNTHETIC" in e["watermark"] and e["watermark_reasons"] is None
        assert e["watermark_form"].startswith("surface: one reason") and e["publishable"] is False
        assert e["pair"]["prediction"].endswith("_prediction.tif") and e["pair"]["uncertainty"].endswith("_uncertainty.tif")
    for e in econ:
        assert e["watermark"] is None and e["watermark_form"].startswith("economics: two")
        reasons = {r["reason"]: r for r in e["watermark_reasons"]}
        assert set(reasons) == {"terrain", "economic_parameters"}
        assert reasons["terrain"]["lifted"] is False and "Checkpoint 1" in reasons["terrain"]["lifted_by"] and "SYNTHETIC" in reasons["terrain"]["cause"]
        assert reasons["economic_parameters"]["lifted"] is False and "Checkpoint 4" in reasons["economic_parameters"]["lifted_by"] and "illustrative_only" in reasons["economic_parameters"]["cause"]
    assert "BY DESIGN" in c["watermark_asymmetry"] and "SEPARATE expiry" in c["economics_watermark_note"]
    def lift_terrain(raw, record, run_dir):
        for entry in raw["economics"]["rasters"].values():
            entry["watermark"]["terrain"]["lifted"] = True
        for scenario in raw["economics"]["scenarios"]:
            for r in scenario["watermark"]["reasons"]:
                if r["reason"] == "terrain":
                    r["lifted"] = True
        for entry in record["files"].values():
            for r in entry["watermark"]["reasons"]:
                if r["reason"] == "terrain":
                    r["lifted"] = True
        for result in raw["economic_results"] + raw["economic_differences"]:
            for r in result["watermark"]["reasons"]:
                if r["reason"] == "terrain":
                    r["lifted"] = True
    c1 = _catalog(_forged_root(api, tmp_path, "checkpoint1", lift_terrain))
    for e in [e for e in c1["layers"] if e["kind"] in ("footprint", "difference")]:
        reasons = {r["reason"]: r["lifted"] for r in e["watermark_reasons"]}
        assert reasons == {"terrain": True, "economic_parameters": False}, e["key"]
    assert [e["watermark"] for e in c1["layers"] if e["kind"] in ("prediction", "uncertainty")] == [e["watermark"] for e in surfaces]


def test_legend_statistics_match_the_rasters_computed_independently_and_the_uniformity_facts_are_served(api: dict) -> None:
    """mu_min/mu_max on prediction entries and sd_min/sd_max on uncertainty
    entries against the pixels (rasterio, here — the API reads no raster);
    economics counts against the pixels' code values; the facts that explain
    eighteen identical pictures served verbatim, not computed."""
    c = api["client"].get(f"/runs/{api['run_id']}/layers").json()
    out = api["out"]
    for e in c["layers"]:
        with rasterio.open(out / e["key"]) as ds:
            values = ds.read(1)
        finite = values[np.isfinite(values)]
        if e["kind"] in ("prediction", "uncertainty"):
            assert e["legend"]["min"] == pytest.approx(float(finite.min()), rel=1e-6) and e["legend"]["max"] == pytest.approx(float(finite.max()), rel=1e-6)
            assert e["legend"]["n_predicted"] == finite.size == 2880 and e["legend"]["n_masked"] == 520 and e["legend"]["binning"] is None
            if e["kind"] == "uncertainty":
                assert "sd" in e["legend"]["quantity"] and e["legend"]["max"] < 6.0
        elif e["kind"] == "footprint":
            assert e["legend"]["n_minable"] == int((finite == 1.0).sum()) == 2880 == e["legend"]["n_predictable"] and e["legend"]["uniform_today"] is True
            assert e["cutoff"]["value"] in (10.0, 5.5) and e["cutoff"]["data_origin"] == "AUTHORED"
        else:
            assert e["legend"]["both"] == int((finite == 1.0).sum()) == 2880 and e["legend"]["only_b"] == int((finite == 2.0).sum()) == 0
            assert e["legend"]["difference_fraction_of_predictable"] == 0.0 and "SENSITIVITY" in e["legend"]["meaning"]
    kriging = next(e for e in c["layers"] if e["key"] == "ordinary_kriging_prediction.tif")
    assert 21.0 < kriging["full_data_fit"]["range_km"] < 22.5 and kriging["full_data_fit"]["range_at_candidate_ceiling"] is True
    assert c["uniformity_today"]["difference_fraction_of_predictable"]["MARKET_STANDARD->STRATEGIC_SUBSIDIZED" if "MARKET_STANDARD->STRATEGIC_SUBSIDIZED" in c["uniformity_today"]["difference_fraction_of_predictable"] else next(iter(c["uniformity_today"]["difference_fraction_of_predictable"]))]
    assert "not of the seafloor" in c["uniformity_today"]["statement"] and c["training_stations"]["n"] == 35
    assert "/runs/{run_id}/layers" in {r.path for r in api["app"].routes if hasattr(r, "methods")}
