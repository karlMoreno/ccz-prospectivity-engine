"""E5.7 commit 2 — VERIFY THE DEPLOYMENT THROUGH ITS URL (adversarial review).

    python deploy/verify_deployment.py http://localhost:8000     (the rehearsal)
    python deploy/verify_deployment.py https://<public-host>     (before any URL is shared)

The same checks the suite runs against the app in-process, run HERE through
HTTP against whatever is at the URL — the deployed failure modes (a proxy's
502 page, a stale image, a swapped CDN bundle) are new and must map onto the
designed ones, not around them. Each check is a function of `get` and
`post` callables so the suite runs them against the TestClient and this
script runs them with httpx2; nothing here is a second implementation of a
rule — it reads what the API serves and compares it to what the repo
records (the pins, the watermark forms, the three-state vocabulary).

THE CLAIM VERDICT TRAVELS WITH THE DEPLOYMENT: a public URL is the strongest
claim this project will make, and these checks are the gate on sharing it.
Passing them is necessary; the fresh-run look by eye through the URL is the
other half and is reported separately (E5.4's rule).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.api.web import CDN_PINS  # noqa: E402  (the recorded tool hashes)


class DeploymentCheckFailed(AssertionError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DeploymentCheckFailed(message)


def checks(get: Callable[[str], object], post: Callable[[str], object]) -> dict:
    """Run every check; return a report; raise DeploymentCheckFailed by name.
    `get(path)`/`post(path)` return objects with .status_code, .content, .headers, .json()."""
    report: dict = {}

    # 1. the page, with the pins that matter on the user's machine
    r = get("/")
    _require(r.status_code == 200 and b"<title>" in r.content, f"GET / did not serve the page (HTTP {r.status_code})")
    page = r.content.decode("utf-8")
    external = re.findall(r'<(?:script|link)\b[^>]*?(?:src|href)="(https?://[^"]+)"[^>]*?integrity="([^"]+)"', page)
    _require(set(external) == {(p["url"], p["integrity"]) for p in CDN_PINS} and len(external) == 3,
             f"the served page's CDN pins differ from the recorded ones: {external}")
    _require("non-scientific" in page.lower() and "<meta" in page and 'name="description"' in page,
             "the served page carries no standing non-scientific status in its title/description")
    report["pins"] = "3 recorded pins served with integrity attributes"

    # 2. the run, named and hashed
    runs = get("/runs").json()
    _require(isinstance(runs, list) and len(runs) >= 1, "GET /runs served no run — the container should have refused to start")
    run = runs[0]
    run_id = run["run_id"]
    report["run"] = {"run_id": run_id, "content_hash": run["content_hash"], "schema_version": run["schema_version"]}
    manifest_bytes = get(f"/runs/{run_id}/manifest").content
    manifest = json.loads(manifest_bytes)
    _require(manifest["content_hash"] == run["content_hash"], "the manifest served does not carry the hash /runs advertises")

    # 3. the verdict, both halves, not dismissable (the model's own rule)
    model = get(f"/runs/{run_id}/viewer").json()
    v = model.get("verdict")
    _require(v is not None and isinstance(v.get("failing"), list) and isinstance(v.get("passing"), list),
             "the served model carries no verdict with both halves")
    _require(v["headline"] and (v["failing"] or v["eligible"]), "the verdict headline is empty or inconsistent")
    _require("no dismiss" in v.get("persistence", ""), "the verdict's persistence rule is missing")
    report["verdict"] = {"headline": v["headline"], "failing": v["failing"], "n_passing": len(v["passing"]), "eligible": v["eligible"]}

    # 4. both watermark forms, per layer; the hatch's two labels; the stations; the mask
    layers = model["layers"]
    forms = {"surface": 0, "economics": 0}
    for key, layer in layers.items():
        h = layer["honesty"]
        if h["watermark_form"].startswith("surface"):
            _require(h["n_reasons"] == 1 and h["reasons"][0]["expiry"] == "stated in the reason text" and "lifted_by" not in h["reasons"][0],
                     f"{key}: a surface's one reason is not served in its own form")
            forms["surface"] += 1
        elif h["watermark_form"].startswith("economics"):
            _require(h["n_reasons"] == 2 and all(r.get("lifted_by") for r in h["reasons"]), f"{key}: an economics layer's two reasons are not served with lifted_by")
            forms["economics"] += 1
        else:
            raise DeploymentCheckFailed(f"{key}: unknown watermark form {h['watermark_form']!r}")
        _require(layer.get("no_information") and layer["no_information"]["label"], f"{key}: no no-information label served")
    ni = model.get("no_information")
    _require(ni is not None and ni["n_marked"] > 0 and ni["range_km"] > 0, "the no-information region is not served")
    labels = {l["no_information"]["label"] for l in layers.values()}
    _require(any("LOWER BOUND" in x or "fitted variogram range" in x for x in labels) and any("spatial support" in x for x in labels),
             "the hatch's two label forms are not both served")
    _require(ni["style"]["pattern"] != model["masked"]["pattern"], "the mask and the hatch share a pattern")
    s = model.get("stations")
    _require(s and s["data_origin"] != model["run_data_origin"], "the stations' origin is not served apart from the run's")
    report["layers"] = {"n": len(layers), **forms, "no_information": ni["count_label"], "stations": f"{s['n']} ({s['data_origin']})"}

    # 5. context layers with citations
    ctx = get("/context").json()
    _require(all(l["attribution_text"] and l["data_origin"] for l in ctx["layers"]), "a context layer is served without its citation or origin")
    report["context"] = [l["id"] for l in ctx["layers"]]

    # 6. a content hash THROUGH the URL against the manifest
    key, digest = next(iter(manifest["output_hashes"].items()))
    f = get(f"/runs/{run_id}/files/{key}")
    _require(f.status_code == 200 and "sha256:" + hashlib.sha256(f.content).hexdigest() == digest and f.headers.get("ETag") == f'"{digest}"',
             f"{key}: the bytes served do not hash to the manifest's record")
    report["spot_check"] = {key: digest}

    # 7. the deployed failure modes map onto the designed ones: JSON 404s with a detail, never a proxy page
    for path, expect in ((f"/runs/nope/manifest", "no run"), (f"/runs/{run_id}/files/features/stack/depth.tif", "not a recorded output"), ("/web/other.js", "not a served web file")):
        r = get(path)
        _require(r.status_code == 404, f"{path}: expected the designed 404, got HTTP {r.status_code}")
        try:
            detail = r.json().get("detail", "")
        except ValueError:
            raise DeploymentCheckFailed(f"{path}: the 404 body is not the API's JSON (a proxy page?)")
        _require(expect in detail, f"{path}: the 404 is not the designed one ({detail[:80]!r})")
    r = post(f"/runs/{run_id}/manifest")
    _require(r.status_code == 405, f"POST was not refused (HTTP {r.status_code})")
    report["refusals"] = "three designed JSON 404s and a 405, through the URL"
    return report


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python deploy/verify_deployment.py <base-url>", file=sys.stderr)
        return 2
    import httpx2

    base = argv[0].rstrip("/")
    client = httpx2.Client(base_url=base, timeout=30.0, follow_redirects=True)
    try:
        report = checks(lambda p: client.get(p), lambda p: client.post(p))
    except DeploymentCheckFailed as error:
        print(f"DEPLOYMENT CHECK FAILED at {base}: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"url": base, **report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
