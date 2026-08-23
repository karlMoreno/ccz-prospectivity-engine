"""E3.4 commit 2 — `ProspectivityEngine.run()` end to end, on the REAL
composition: the real corpus and 35-station matrix over the synthetic-DEM
stack, every production collaborator except the two Phase-3/4 Strategies
that have no production implementation (TS6Reference — the fixture, since
G3.1 has not delivered; EconomicModel — a stub, since Phase 4 has not begun
and the ABC has zero implementations, PATTERNS.md §3.2).

STATED FIRST: the DEM and the TS-6 raster are SYNTHETIC FIXTURES. Every
manifest here is watermarked, every verdict is a refusal, and no number in
it measures anything about the seafloor or TS-6. What is under test is that
the Template Method composes the Phase-1–3 machinery into ONE record whose
every link is recomputed — and that "same inputs + seed -> same outputs"
holds at the level of the whole run, not only of its parts.

Three of the four designs are run (leave-one-station-out's 35 folds are
omitted for time); the registry is E2.4's light one (RF at 40 trees).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.prospectivity.domain.results import EconomicScenarioResult, RunManifest, TS6Agreement
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer
from engine.prospectivity.economics.model import EconomicModel
from engine.prospectivity.engine import GENERATOR, ProspectivityEngine
from engine.prospectivity.features.bundle import StackFeatureBuilder
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.terrain.source import TerrainSource
from engine.prospectivity.validation.claim import evaluate_claim
from engine.prospectivity.validation.runner import CrossValidationRunner
from engine.prospectivity.validation.splitter import (
    RandomKFoldSplitter,
    leave_one_cluster_out,
    leave_one_site_out,
)
from tests.fixtures.rasters import (
    FixtureTerrainSource,
    FixtureTS6Reference,
    write_synthetic_bathymetry,
    write_synthetic_ts6_raster,
)
from tests.test_cv_runner import _light_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAIM_DESIGN = "leave_one_site_out"
ESTIMATORS = {"mean_baseline", "ordinary_kriging", "random_forest"}


# E4.1 commit 2: the real EconomicModel runs in the composition — Phase 4's
# seam is no longer stubbed (PATTERNS §3.2's last zero-implementation ABC
# after TS6Reference, which waits on G3.1).
from engine.prospectivity.economics.contract import difference_pairs
from engine.prospectivity.economics.cutoff import CutoffEconomicModel


def _study_area() -> StudyArea:
    raw = json.loads((REPO_ROOT / "data" / "aoi" / "study_area.geojson").read_text())
    feature = raw["features"][0]
    return StudyArea(
        area_id=feature["properties"]["area_id"],
        name=feature["properties"].get("name", feature["properties"]["area_id"]),
        geometry=feature["geometry"],
    )


def _scenarios():
    from engine.prospectivity.economics.contract import scenarios

    return scenarios()


def _engine(
    tmp: Path, *, seed: int = 0, run_id: str = "e3.4-engine", out: str = "out", features: str = "features"
) -> ProspectivityEngine:
    tmp.mkdir(parents=True, exist_ok=True)
    dem_path = tmp / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    ts6_path = tmp / "ts6.tif"
    write_synthetic_ts6_raster(ts6_path)
    registry = _light_registry(covariate_names=None)
    return ProspectivityEngine(
        study_area=_study_area(),
        terrain_source=FixtureTerrainSource(dem_path),
        sample_source=CorpusCsvSampleSource(),
        feature_builder=StackFeatureBuilder(tmp / features),
        cv_runner=CrossValidationRunner(
            splitters=[leave_one_cluster_out(), leave_one_site_out(), RandomKFoldSplitter(k=5, seed=seed)],
            registry=registry,
        ),
        estimators=registry,
        ts6_reference=FixtureTS6Reference(ts6_path),
        economic_model=CutoffEconomicModel(),
        scenario_configs=_scenarios(),
        difference_pairs=difference_pairs(),
        output_dir=tmp / out,
        claim_design=CLAIM_DESIGN,
        seed=seed,
        run_id=run_id,
    )


@pytest.fixture(scope="module")
def run(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("engine_run")
    engine = _engine(tmp)
    manifest = engine.run()
    return {"manifest": manifest, "out": tmp / "out", "tmp": tmp, "registry": engine._estimators}


def test_the_real_composition_runs_end_to_end_and_writes_one_record_of_everything(run: dict) -> None:
    manifest, out = run["manifest"], run["out"]
    on_disk = RunManifest(**json.loads((out / "run_manifest.json").read_text()))
    assert on_disk.content_hash == manifest.content_hash == on_disk.compute_content_hash()
    assert manifest.generator == GENERATOR and manifest.run_id == "e3.4-engine"
    assert set(manifest.surfaces) == set(manifest.ts6_agreement) == ESTIMATORS
    assert set(manifest.inputs["registry"]) == ESTIMATORS
    # prompt §5: the mapping's keys are the REGISTRY's names — the object the
    # engine was handed, not only the record of it
    assert sorted(manifest.ts6_agreement) == sorted(run["registry"].names())
    assert [d["name"] for d in manifest.cross_validation["designs"]] == [
        "leave_one_cluster_out", "leave_one_site_out", "random_k_fold"
    ]
    assert set(manifest.claim["verdicts"]) == {"leave_one_cluster_out", "leave_one_site_out", "random_k_fold"}
    assert manifest.claim["design"] == CLAIM_DESIGN
    assert manifest.prediction_grid["n_cells"] == 3400 and manifest.prediction_grid["n_masked"] == 520
    # every written file, hashed by basename (economics/<basename> for the
    # subdirectory), recomputed here from the bytes — the FULL listing
    files = {p.name: file_sha256(p) for p in out.iterdir() if p.is_file() and p.name != "run_manifest.json"}
    files |= {f"economics/{p.name}": file_sha256(p) for p in (out / "economics").iterdir() if p.is_file()}
    files |= {f"export/{p.name}": file_sha256(p) for p in (out / "export").iterdir() if p.is_file()}  # E5.2
    assert manifest.output_hashes == files and len(files) == 10 + 18 + 2 + 21 + 1
    # E4.2/E4.3: 18 rasters and two sidecars, every raster named by a result and resolved from the record
    rasters = {n[len("economics/"):] for n in files if n.startswith("economics/") and n.endswith(".tif")}
    assert len(rasters) == 18 == 12 + 6
    recorded = {v["raster_file"] for r in manifest.economic_results for by_z in r.footprints.values() for v in by_z.values()}
    recorded |= {v["raster_file"] for d in manifest.economic_differences for by_z in d.footprints.values() for v in by_z.values()}
    assert recorded == rasters == set(manifest.economics["rasters"])
    assert (manifest.economics["n_files"], manifest.economics["n_footprint_rasters"], manifest.economics["n_difference_rasters"]) == (20, 12, 6)
    assert manifest.schema_version == 4  # E4.3: 3; E5.5 commit 2: + training_stations
    assert manifest.training_stations['n'] == 35 and all('full_data_fit' in s and 'sd_min' in s for s in manifest.surfaces.values())
    # Phase 4's model ran over Contract 4's two scenarios and its one difference
    # pair; the verdict is DERIVED, both reasons unlifted today; the computed
    # origin is AUTHORED (the lattice's lossy answer, beside the verdict)
    assert [r.scenario_name for r in manifest.economic_results] == ["MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"]
    for r in manifest.economic_results:
        assert r.watermark["watermarked"] and [x["lifted"] for x in r.watermark["reasons"]] == [False, False]
        assert r.data_origin == "AUTHORED" and set(r.footprints) == ESTIMATORS and set(r.footprints["random_forest"]) == {"0.0", "1.0"}
        assert all(v["fraction_of_predictable"] == 1.0 for by_z in r.footprints.values() for v in by_z.values())
    assert [d.pair for d in manifest.economic_differences] == [["MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"]]
    assert all(v["n_minable"] == 0 for by_z in manifest.economic_differences[0].footprints.values() for v in by_z.values())
    assert manifest.economics["scenarios"][0]["cutoff"] == {"value": 10.0, "units": "kg_m2", "data_origin": "AUTHORED", "author": "unrecorded"}


def test_the_run_is_watermarked_refused_and_says_so_as_data(run: dict) -> None:
    """Today's honest output, produced by the machinery: SYNTHETIC origin,
    every surface non-publishable, every verdict a refusal naming its
    preconditions, and the agreement numbers labelled synthetic."""
    manifest = run["manifest"]
    assert manifest.data_origin == "SYNTHETIC"
    assert all(s["data_origin"] == "SYNTHETIC" and s["publishable"] is False for s in manifest.surfaces.values())
    assert all(v["eligible"] is False and v["is_scientific"] is False for v in manifest.claim["verdicts"].values())
    gate = "an_acceptance_threshold_existed_before_the_scores"
    failing = {
        d: sorted(r["precondition"] for r in v["preconditions"] if not r["passed"])
        for d, v in manifest.claim["verdicts"].items()
    }
    assert failing == {
        "leave_one_cluster_out": [gate],
        "leave_one_site_out": [gate],
        "random_k_fold": [gate, "spatially_blocked_cross_validation_ran"],
    }
    assert all(isinstance(a, TS6Agreement) and a.data_origin == "SYNTHETIC" for a in manifest.ts6_agreement.values())
    assert manifest.provenance_chain["verifiable_off_machine"] == ["corpus", "feature_stack", "training_matrix (same-endianness)"]  # HASH.1
    # the verdict in the record IS the guard's verdict on the final record
    for design, recorded in manifest.claim["verdicts"].items():
        stack = json.loads((run["tmp"] / "features" / "stack" / "provenance.json").read_text())
        assert evaluate_claim(manifest, design=design, feature_stack_manifest=stack).to_record() == recorded


def test_the_phase_headline_findings_travel_in_the_record(run: dict) -> None:
    """E3.1+2 pinned the two measured findings as tests on the builder; the
    manifest's `surfaces` block must carry them so a reader of the record
    meets them without re-running anything: RF's ~1,842 distinct values
    inside the entailed [min(y), max(y)] bound (not E3.0's refuted one), and
    kriging's near-constant surface. Loose re-pins — the exact values are
    E3.1+2's to pin; this asserts the RECORD carries them."""
    surfaces = run["manifest"].surfaces
    rf = surfaces["random_forest"]
    assert rf["n_distinct_values"] > 1000 and 11.6 <= rf["mu_min"] and rf["mu_max"] <= 26.8
    kriging = surfaces["ordinary_kriging"]
    assert kriging["mu_max"] - kriging["mu_min"] < 3.0  # [17.866, 20.454] measured at E3.1+2
    assert surfaces["mean_baseline"]["n_distinct_values"] == 1
    assert all(s["n_predicted"] == 2880 and s["n_masked"] == 520 for s in surfaces.values())


def test_same_inputs_and_seed_in_the_same_tree_give_the_same_manifest_hash_across_two_whole_runs(
    run: dict
) -> None:
    """CLAUDE.md's reproducibility rule at the level of the WHOLE run —
    ingestion through the extended manifest — with the same DEM at the same
    path and a different output directory. Full-state: every field outside
    the hash-excluded set equal, content_hash equal."""
    second = _engine(run["tmp"], out="out_again").run()
    excluded = RunManifest.hash_excluded_fields()
    a, b = json.loads(run["manifest"].to_json()), json.loads(second.to_json())
    assert {k: v for k, v in a.items() if k not in excluded} == {k: v for k, v in b.items() if k not in excluded}
    assert second.content_hash == run["manifest"].content_hash


def test_the_same_bytes_in_a_different_tree_reproduce_the_science_and_nothing_that_quotes_the_stack_hash(
    run: dict, tmp_path: Path
) -> None:
    """THE FORMER PATH-HASH LIMIT AT WHOLE-RUN SCALE. At E3.4 this test
    pinned the defect: the same DEM bytes in another directory gave a
    different feature_stack hash, quoted by six top-level fields, and the
    differing set was asserted as an EQUALITY so the fix would turn it red.
    HASH.1 commit 2 did. It now pins the fix at the same scale: the
    differing set is EMPTY — every field outside the hash-excluded four
    equal, content_hash equal, zero moving hash values, the record's count
    equal to the measurement. A path creeping back anywhere in the chain
    widens the set and fails here — the first draft of the fix did exactly
    that, echoing the stack's `dem_path` inside the run's chain block."""
    elsewhere = _engine(tmp_path / "elsewhere").run()
    excluded = RunManifest.hash_excluded_fields()
    a, b = json.loads(run["manifest"].to_json()), json.loads(elsewhere.to_json())
    differing = {k for k in a if k not in excluded and a[k] != b[k]}
    assert differing == set()
    assert elsewhere.content_hash == run["manifest"].content_hash
    import re
    pattern = re.compile(r"sha256:[0-9a-f]{64}")
    moved = set(pattern.findall(json.dumps({k: v for k, v in a.items() if k != "content_hash"}))) - set(
        pattern.findall(json.dumps({k: v for k, v in b.items() if k != "content_hash"}))
    )
    assert len(moved) == a["provenance_chain"]["path_dependent_hashes"]["count"] == 0
    assert a["provenance_chain"]["path_dependent_hashes"]["was"] == 11
    # the stack manifests still say WHERE each DEM was — outside their hashes
    here = json.loads((run["tmp"] / "features" / "stack" / "provenance.json").read_text())
    there = json.loads((tmp_path / "elsewhere" / "features" / "stack" / "provenance.json").read_text())
    assert here["dem_path"] != there["dem_path"] and here["content_hash"] == there["content_hash"]


def test_a_terrain_layer_without_a_declared_origin_is_refused_by_name_before_any_stack_is_built(tmp_path: Path) -> None:
    """Declaration or nothing: the feature builder refuses an undeclared DEM
    origin rather than defaulting it (P2.0d-3), and nothing is written."""
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    builder = StackFeatureBuilder(tmp_path / "features")
    undeclared = TerrainLayer(name="bathymetry", path=str(dem_path), data_origin=None)
    with pytest.raises(ValueError, match=r"declares no data_origin .*declaration or nothing"):
        builder(undeclared, CorpusCsvSampleSource().get_training_samples())
    assert not (tmp_path / "features").exists()
    with pytest.raises(ValueError, match=r"carries no path"):
        builder(TerrainLayer(name="bathymetry", data_origin="SYNTHETIC"), [])


def test_the_prediction_grid_is_the_stack_the_matrix_was_sampled_from(run: dict) -> None:
    """The bundle's point: one stack, read twice. The manifest's grid quotes
    the stack hash the matrix manifest chains to, and the emitter recomputed
    both from the same provenance.json."""
    manifest = run["manifest"]
    stack = json.loads((run["tmp"] / "features" / "stack" / "provenance.json").read_text())
    assert manifest.prediction_grid["stack_content_hash"] == stack["content_hash"]
    assert manifest.upstream_hashes["feature_stack"] == stack["content_hash"]
    assert manifest.provenance_chain["links"]["feature_stack"]["content_hash"] == stack["content_hash"]
    assert manifest.prediction_grid["layer_names"] == manifest.inputs["training_matrix"]["covariate_names"]


def test_the_surfaces_are_marked_with_the_declared_claim_designs_verdict_not_another_designs(
    tmp_path: Path
) -> None:
    """THE SEPARATING FIXTURE: leave_one_site_out and leave_one_cluster_out
    fail the same single precondition today, so a writer handed the FIRST
    design's verdict instead of the DECLARED one would write identical tags
    and no test could tell. random_k_fold fails two, so a run that declares
    it as the claim design must carry BOTH in every raster's tags and
    sidecar — and a run declaring site-out must carry one."""
    manifest = _engine(tmp_path / "rk", run_id="e3.4-claim-rk").run()
    sidecar = json.loads((tmp_path / "rk" / "out" / "ordinary_kriging.provenance.json").read_text())
    failing = {
        d: sorted(r["precondition"] for r in v["preconditions"] if not r["passed"])
        for d, v in manifest.claim["verdicts"].items()
    }
    assert manifest.claim["design"] == CLAIM_DESIGN
    assert sidecar["claim_failing_preconditions"] == failing[CLAIM_DESIGN] and len(failing[CLAIM_DESIGN]) == 1

    declared_random = _engine(tmp_path / "rk", run_id="e3.4-claim-rk", out="out_rk")
    declared_random._claim_design = "random_k_fold"  # the declaration, varied; everything else identical
    manifest_rk = declared_random.run()
    sidecar_rk = json.loads((tmp_path / "rk" / "out_rk" / "ordinary_kriging.provenance.json").read_text())
    assert manifest_rk.claim["design"] == "random_k_fold"
    assert sidecar_rk["claim_failing_preconditions"] == failing["random_k_fold"] and len(failing["random_k_fold"]) == 2
    assert manifest_rk.claim["verdicts"] == manifest.claim["verdicts"]  # every design's verdict, both runs
