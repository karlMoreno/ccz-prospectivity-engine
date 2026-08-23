"""E5.5 commit 1 — the run harness: one command, the production registry,
determinism measured in two trees, and the two file-backed Strategies.

STATED FIRST: the inputs are the test generator's SYNTHETIC rasters, declared
so on the command line; every output is watermarked and every verdict is a
refusal. What is under test is the ENTRY POINT: that it composes the real
engine with `build_default_registry()` and nothing lighter, that it refuses
what it must before computing, and that two invocations in two trees produce
one substance.

The module fixture runs the harness ONCE with three designs (leave-one-
station-out's 35 folds cost ~75 s under the production registry and add
nothing the three cannot separate); the default four-design set is asserted
structurally (the parser's default) rather than run.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from engine.prospectivity import harness
from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.terrain.file_source import FileTerrainSource
from engine.prospectivity.ts6.file_reference import FileTS6Reference
from tests.fixtures.rasters import (
    PIXEL_SIZE_DEG,
    write_synthetic_bathymetry,
    write_synthetic_ts6_raster,
    write_test_raster,
)

THREE_DESIGNS = "leave_one_cluster_out,leave_one_site_out,random_k_fold"
ESTIMATORS = {"mean_baseline", "ordinary_kriging", "random_forest"}
RUN_ID = "e5.5-harness-test"
HASH = re.compile(r"sha256:[0-9a-f]{64}")


def _inputs(tree: Path) -> tuple[Path, Path]:
    tree.mkdir(parents=True, exist_ok=True)
    dem, ts6 = tree / "dem.tif", tree / "ts6.tif"
    write_synthetic_bathymetry(dem)
    write_synthetic_ts6_raster(ts6)
    return dem, ts6


def _argv(dem: Path, ts6: Path, out: Path, *, designs: str = THREE_DESIGNS, run_id: str = RUN_ID) -> list[str]:
    return [
        "--dem", str(dem), "--dem-data-origin", "SYNTHETIC",
        "--ts6", str(ts6), "--ts6-data-origin", "SYNTHETIC",
        "--out", str(out), "--run-id", run_id, "--designs", designs,
    ]


@pytest.fixture(scope="module")
def harness_run(tmp_path_factory) -> dict:
    tree = tmp_path_factory.mktemp("harness_tree_a")
    dem, ts6 = _inputs(tree)
    out = tree / "run"
    assert harness.main(_argv(dem, ts6, out)) == 0
    manifest = RunManifest(**json.loads((out / "run_manifest.json").read_text()))
    return {"tree": tree, "dem": dem, "ts6": ts6, "out": out, "manifest": manifest}


def _rf_trees_per_fold(manifest: RunManifest) -> list[int]:
    return [
        r["provenance"]["n_estimators"]
        for d in manifest.cross_validation["designs"]
        for r in d["results"]
        if r["estimator_name"] == "random_forest" and r["status"] == "scored"
    ]


def test_one_command_produces_the_full_run_inventory_with_the_production_registry_read_back_per_fold(
    harness_run: dict,
) -> None:
    """THE REGISTRY DECISION, verifiable in the record: every scored RF fold
    reads back n_estimators == 500 from the fitted forest (E2.3's read-back),
    and the full-data RF surface carries the production measurement E3.1+2
    pinned (1,842 distinct values in [15.091, 21.681]) — the light registry
    reads 40 per fold and 1,218 distinct values in [14.982, 22.041], so a
    harness that fell back to a test fixture fails here BY THE NUMBER. The
    inventory is the manifest's full listing plus the features directory."""
    m, out = harness_run["manifest"], harness_run["out"]
    assert m.run_id == RUN_ID and m.content_hash == m.compute_content_hash()
    assert set(m.inputs["registry"]) == ESTIMATORS == set(m.surfaces)
    trees = _rf_trees_per_fold(m)
    assert len(trees) == 2 + 5 + 5 and set(trees) == {500}, trees  # a light registry reads {40}
    rf = m.surfaces["random_forest"]
    assert rf["n_distinct_values"] > 1800 and 15.0 < rf["mu_min"] < 15.2 and 21.6 < rf["mu_max"] < 21.8
    # the inventory: every hashed file present with its recorded hash, the
    # features stack beside them, and NOTHING else at the top level
    files = {p.name: file_sha256(p) for p in out.iterdir() if p.is_file() and p.name != "run_manifest.json"}
    files |= {f"economics/{p.name}": file_sha256(p) for p in (out / "economics").iterdir() if p.is_file()}
    assert m.output_hashes == files and len(files) == 10 + 20
    assert {p.name for p in out.iterdir() if p.is_dir()} == {"economics", harness.FEATURES_DIR}
    stack = out / harness.FEATURES_DIR / "stack"
    assert {p.name for p in stack.iterdir()} == {
        "aspect.tif", "bpi.tif", "depth.tif", "plan_curvature.tif", "profile_curvature.tif",
        "roughness.tif", "slope.tif", "tpi.tif", "provenance.json",
    }
    assert [d["name"] for d in m.cross_validation["designs"]] == THREE_DESIGNS.split(",")
    assert m.claim["design"] == harness.DEFAULT_CLAIM_DESIGN
    # the default design set is E2.4's committed four, in its order
    assert harness.DEFAULT_DESIGNS == (
        "leave_one_cluster_out", "leave_one_site_out", "leave_one_station_out", "random_k_fold"
    )


def test_the_run_is_watermarked_and_refused_exactly_as_the_engine_test_records(harness_run: dict) -> None:
    """The harness adds no precondition and lifts none: the failing and
    passing SETS per design equal the e2e test's (E4.3 §3's shape)."""
    gate = "an_acceptance_threshold_existed_before_the_scores"
    verdicts = harness_run["manifest"].claim["verdicts"]
    sets = {
        d: ({p["precondition"] for p in v["preconditions"] if not p["passed"]},
            {p["precondition"] for p in v["preconditions"] if p["passed"]})
        for d, v in verdicts.items()
    }
    assert sets["leave_one_site_out"][0] == {gate} and len(sets["leave_one_site_out"][1]) == 5
    assert sets["leave_one_cluster_out"][0] == {gate} and len(sets["leave_one_cluster_out"][1]) == 5
    assert sets["random_k_fold"][0] == {gate, "spatially_blocked_cross_validation_ran"} and len(sets["random_k_fold"][1]) == 4
    assert harness_run["manifest"].data_origin == "SYNTHETIC"
    assert all(s["publishable"] is False for s in harness_run["manifest"].surfaces.values())


def test_two_invocations_in_two_trees_produce_identical_substance_and_zero_path_dependent_hashes(
    harness_run: dict, tmp_path: Path
) -> None:
    """DETERMINISM AS THE HARNESS'S OWN PROPERTY, measured: the SAME input
    bytes copied into a second tree, the command run again into a second
    directory. Every field outside the hash-excluded set equal, content_hash
    equal, the set of hash values that moved EMPTY and equal to the chain's
    recorded count (0). A path creeping into any record widens the set."""
    tree_b = tmp_path / "harness_tree_b"
    tree_b.mkdir()
    shutil.copyfile(harness_run["dem"], tree_b / "dem.tif")
    shutil.copyfile(harness_run["ts6"], tree_b / "ts6.tif")
    assert file_sha256(tree_b / "dem.tif") == file_sha256(harness_run["dem"])
    out_b = tree_b / "run"
    assert harness.main(_argv(tree_b / "dem.tif", tree_b / "ts6.tif", out_b)) == 0
    a = json.loads(harness_run["manifest"].to_json())
    b = json.loads((out_b / "run_manifest.json").read_text())
    excluded = RunManifest.hash_excluded_fields()
    differing = {k for k in set(a) | set(b) if k not in excluded and a.get(k) != b.get(k)}
    assert differing == set()
    assert a["content_hash"] == b["content_hash"]
    moved = set(HASH.findall(json.dumps({k: v for k, v in a.items() if k != "content_hash"}))) ^ set(
        HASH.findall(json.dumps({k: v for k, v in b.items() if k != "content_hash"}))
    )
    assert moved == set() and a["provenance_chain"]["path_dependent_hashes"]["count"] == 0
    # and the bytes on disk: every hashed output identical across the trees
    for key, digest in a["output_hashes"].items():
        assert file_sha256(out_b / key) == digest, key
    # the stack manifests still say WHERE each DEM was, outside their hashes
    here = json.loads((harness_run["out"] / harness.FEATURES_DIR / "stack" / "provenance.json").read_text())
    there = json.loads((out_b / harness.FEATURES_DIR / "stack" / "provenance.json").read_text())
    assert here["dem_path"] != there["dem_path"] and here["content_hash"] == there["content_hash"]


def test_an_undeclared_or_unknown_input_origin_is_refused_by_name_before_anything_runs(tmp_path: Path) -> None:
    """Declaration or nothing, at the EARLIEST site: the sources cannot be
    constructed without an origin, the CLI rejects a non-member, and no
    output directory is created by a refused invocation."""
    dem, ts6 = _inputs(tmp_path / "t")
    with pytest.raises(ValueError, match="declares no data_origin"):
        FileTerrainSource(dem, data_origin=None)
    with pytest.raises(ValueError, match="declares no data_origin"):
        FileTS6Reference(ts6, data_origin=None)
    with pytest.raises(ValueError, match="not one of"):
        FileTerrainSource(dem, data_origin="GENUINE")
    out = tmp_path / "refused"
    with pytest.raises(SystemExit):  # argparse: not a DataOrigin member
        harness.main(_argv(dem, ts6, out)[:3] + ["REAL"] + _argv(dem, ts6, out)[4:])
    with pytest.raises(ValueError, match="declares no data_origin"):
        harness.build_engine(dem=dem, dem_data_origin=None, ts6=ts6, ts6_data_origin="SYNTHETIC", out=out)
    assert not out.exists()


def test_a_non_empty_output_directory_is_refused_by_name(tmp_path: Path) -> None:
    dem, ts6 = _inputs(tmp_path / "t")
    out = tmp_path / "occupied"
    out.mkdir()
    (out / "leftover.txt").write_text("x")
    with pytest.raises(ValueError, match="is not empty"):
        harness.build_engine(dem=dem, dem_data_origin="SYNTHETIC", ts6=ts6, ts6_data_origin="SYNTHETIC", out=out)
    empty = tmp_path / "empty"
    empty.mkdir()
    harness.build_engine(dem=dem, dem_data_origin="SYNTHETIC", ts6=ts6, ts6_data_origin="SYNTHETIC", out=empty)
    with pytest.raises(ValueError, match="unknown design"):
        harness.build_engine(dem=dem, dem_data_origin="SYNTHETIC", ts6=ts6, ts6_data_origin="SYNTHETIC",
                             out=tmp_path / "d", designs=["leave_one_site_out", "bootstrap"])


def test_file_terrain_source_reads_resolution_and_hash_from_the_raster_not_from_a_constant(tmp_path: Path) -> None:
    """SEPARATES the file's geometry from the fixture's 0.1° constant: a
    0.25° raster must report 0.25, and the hash must be the bytes'. A
    non-square or non-EPSG:4326 raster is refused by name."""
    import numpy as np

    coarse = tmp_path / "coarse.tif"
    write_test_raster(coarse, np.full((4, 5), -4000.0, dtype=np.float32), west=-120.0, north=12.0, pixel_size_deg=0.25)
    layer = FileTerrainSource(coarse, data_origin="SYNTHETIC").load(
        StudyArea(area_id="x", name="x", geometry={"type": "Polygon", "coordinates": [[[-120, 11], [-119, 11], [-119, 12], [-120, 12], [-120, 11]]]})
    )
    assert layer.resolution_deg == 0.25 != PIXEL_SIZE_DEG
    assert layer.content_hash == file_sha256(coarse) and layer.data_origin == "SYNTHETIC"
    assert layer.path == str(coarse) and layer.crs == "EPSG:4326" and layer.source_id == "src_bathymetry_primary"
    surface = FileTS6Reference(coarse, data_origin="DERIVED", title="t").load()
    assert surface.content_hash == file_sha256(coarse) and surface.data_origin == "DERIVED"
    assert surface.role_note == "benchmark_only" and surface.source_id == "src_ts6_grid"


def test_the_production_run_records_the_three_e5_5_additions_with_production_values(harness_run: dict) -> None:
    """E5.5 commit 2 on the PRODUCTION path: the full-data fit read back from
    the fitted objects (RF 500 trees, five importance seeds), the sd ranges,
    and the 35 stations — the values a viewer would meet."""
    m = harness_run["manifest"]
    rf = m.surfaces["random_forest"]["full_data_fit"]
    assert rf["n_estimators"] == 500 and len(rf["importance_by_seed"]) == 5
    kriging = m.surfaces["ordinary_kriging"]["full_data_fit"]
    assert 21.0 < kriging["range_km"] < 22.5 and kriging["range_at_candidate_ceiling"] is True
    assert all(0 < s["sd_min"] <= s["sd_max"] for s in m.surfaces.values())
    assert m.training_stations["n"] == 35 and m.training_stations["data_origin"] == "MEASURED"
    assert m.schema_version == 4


# ═══════════════════════════════ E5.5 commit 3 — the run directory as a product

def test_every_file_in_the_run_directory_is_resolved_by_the_record_and_the_record_names_nothing_absent(
    harness_run: dict,
) -> None:
    """THE LAYOUT, both directions, against the DIRECTORY LISTING (the
    property that caught E4.2's misplaced rasters): every file under <out>
    is either the root record, hashed in output_hashes under the key the
    layout states, or a member of the one unhashed group (features/stack/,
    identified as a whole by the stack manifest's content_hash that the
    record quotes) — and every key the record names exists with its bytes.
    Resolution is checked FROM THE RECORD: each surface's rasters and
    sidecar via surfaces[est], each economics raster via the association
    record, parsing no name."""
    m, out = harness_run["manifest"], harness_run["out"]
    listing = {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()}
    hashed = set(m.output_hashes)
    stack = {f for f in listing if f.startswith(harness.STACK_DIR + "/")}
    assert listing == {"run_manifest.json"} | hashed | stack, listing ^ ({"run_manifest.json"} | hashed | stack)
    assert len(stack) == 9 and all(k.count("/") <= 1 for k in hashed)  # basename or economics/<basename>
    for key, digest in m.output_hashes.items():
        assert file_sha256(out / key) == digest, key
    # the stack is ONE artifact: its manifest's hash is what the record quotes
    stack_manifest = json.loads((out / harness.STACK_DIR / "provenance.json").read_text())
    assert stack_manifest["content_hash"] == m.upstream_hashes["feature_stack"] == m.prediction_grid["stack_content_hash"]
    # resolution from the record, never the name
    for est, block in m.surfaces.items():
        for kind in ("prediction", "uncertainty"):
            assert file_sha256(out / block["rasters"][kind]["file"]) == block["rasters"][kind]["sha256"] == m.output_hashes[block["rasters"][kind]["file"]]
        assert file_sha256(out / block["sidecar"]["file"]) == block["sidecar"]["sha256"]
    record = json.loads((out / "economics" / "economics.footprints.json").read_text())
    assert set(record["files"]) == set(m.economics["rasters"]) == {k[len("economics/"):] for k in hashed if k.startswith("economics/") and k.endswith(".tif")}
    for name, entry in record["files"].items():
        assert file_sha256(out / "economics" / name) == entry["sha256"] == m.economics["rasters"][name]["sha256"]
    # the inputs are identified by hash, not present in the directory
    assert not (out / "dem.tif").exists() and not (out / "ts6.tif").exists()
    assert m.provenance_chain["links"]["ts6_benchmark"]["content_hash"] == file_sha256(harness_run["ts6"])
    assert m.provenance_chain["links"]["feature_stack"]["dem_content_hash"] == file_sha256(harness_run["dem"])
    assert set(harness.RUN_LAYOUT) >= {"run_manifest.json", "economics/*.tif", "features/stack/*"}
