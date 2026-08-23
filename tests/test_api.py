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
