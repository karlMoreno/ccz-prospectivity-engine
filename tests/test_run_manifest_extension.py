"""E3.4 commit 1 — `extend_run_manifest`: the chain asserted by recomputation,
the TS-6 mapping, the claim verdict as data, and the limit in the output.

STATED FIRST: every run here is over the SYNTHETIC DEM and a SYNTHETIC TS-6
fixture. The manifests are watermarked, every claim verdict is a refusal, and
the agreement numbers measure nothing about TS-6. What is under test is the
RECORD: that every hash in it was recomputed, that nothing was cherry-picked,
and that the record says what it cannot verify.

The module fixture runs the real composition once — the real corpus and the
35-station matrix over the synthetic-DEM stack (the session `surface_assembly`),
a CV run over three of the four designs (leave-one-station-out's 35 folds are
omitted for time; the three kept separate "claim-eligible by record" from
"not": two spatially blocked, one random), the writer, the comparison, the
guard — and extends the manifest from it.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.domain.results import RunManifest, TS6Agreement
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME
from engine.prospectivity.features.stack import FeatureStackManifest, build_covariate_stack
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.corpus_manifest import CorpusManifest
from engine.prospectivity.provenance.emitter import CHAIN_LIMIT_NOTE, extend_run_manifest
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import compute_surface_origin, write_surface
from engine.prospectivity.ts6.comparison import compare_all_to_ts6
from engine.prospectivity.validation.claim import Precondition, evaluate_claim
from engine.prospectivity.validation.runner import (
    CrossValidationRunner,
    emit_run_manifest,
    matrix_sha256,
)
from engine.prospectivity.validation.splitter import (
    RandomKFoldSplitter,
    leave_one_cluster_out,
    leave_one_site_out,
)
from tests.fixtures.rasters import FixtureTS6Reference, write_synthetic_ts6_raster
from tests.test_cv_runner import _light_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAIM_DESIGN = "leave_one_site_out"  # E2.4's headline within-cluster gate
RUN_ID = "e3.4-test"


def _designs():
    return [leave_one_cluster_out(), leave_one_site_out(), RandomKFoldSplitter(k=5, seed=0)]


def _compose(built: dict, out: Path, *, run_id: str = RUN_ID) -> dict:
    """The whole Phase-3 composition in one place, so two runs can be compared
    in full: CV → base manifest → verdicts → written surfaces → TS-6
    agreements → extension. Returns every input alongside the result."""
    matrix, matrix_manifest = built["matrix"], built["matrix_manifest"]
    grid, surfaces, stack = built["grid"], built["surfaces"], built["stack_manifest"]
    corpus = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())

    report = CrossValidationRunner(
        splitters=_designs(), registry=_light_registry(matrix.covariate_names)
    ).run(matrix, seed=0)
    base = emit_run_manifest(report, matrix=matrix, matrix_manifest=matrix_manifest, run_id=run_id)
    verdicts = {
        d.name: evaluate_claim(base, design=d.name, feature_stack_manifest=stack) for d in _designs()
    }
    origin = compute_surface_origin(stack["dem_data_origin"], matrix_manifest.data_origin)
    written = {
        name: write_surface(result, grid, out, data_origin=origin, verdict=verdicts[CLAIM_DESIGN])
        for name, result in surfaces.items()
    }
    ts6_path = out / "ts6_fixture.tif"
    write_synthetic_ts6_raster(ts6_path)
    ts6 = FixtureTS6Reference(ts6_path).load()
    agreements = compare_all_to_ts6(surfaces, grid, ts6, surface_data_origin=origin)
    # E4.3: the economics rasters (E4.1 computes, E4.2 writes) into out/economics/
    from engine.prospectivity.economics.contract import difference_pairs, scenarios
    from engine.prospectivity.economics.cutoff import CutoffEconomicModel
    from engine.prospectivity.economics.model import EconomicInputs
    from engine.prospectivity.economics.writer import write_difference, write_footprints
    from engine.prospectivity.features.bundle import cell_areas_m2
    from engine.prospectivity.features.dem_grid import DemGrid

    econ_inputs = EconomicInputs(
        surfaces=surfaces, grid=grid, cell_area_m2=cell_areas_m2(DemGrid.load(Path(stack["dem_path"]))),
        dem_data_origin=stack["dem_data_origin"], surface_data_origin=origin.value,
    )
    model = CutoffEconomicModel()
    footprints = {s.name: model.apply(econ_inputs, s) for s in scenarios()}
    economics_dir = out / "economics"
    economic_results = [
        fp.record({k: p.name for k, p in write_footprints(fp, grid, surfaces, economics_dir, claim_verdict=verdicts[CLAIM_DESIGN]).items()})
        for fp in footprints.values()
    ]
    economic_differences = []
    for a, b in difference_pairs():
        diff = model.difference(footprints[a], footprints[b])
        paths = write_difference(diff, footprints[a], footprints[b], grid, surfaces, economics_dir, claim_verdict=verdicts[CLAIM_DESIGN])
        economic_differences.append(diff.record({k: p.name for k, p in paths.items()}))
    inputs = dict(
        base=base, matrix=matrix, matrix_manifest=matrix_manifest, corpus_manifest=corpus,
        stack_manifest=stack, grid=grid, surfaces=surfaces, written=written, ts6=ts6,
        agreements=agreements, verdicts=verdicts, claim_design=CLAIM_DESIGN,
        economic_results=economic_results, economic_differences=economic_differences, economics_dir=economics_dir,
    )
    manifest = extend_run_manifest(**inputs)
    (out / "run_manifest.json").write_text(manifest.to_json())
    return {**inputs, "manifest": manifest, "out": out, "origin": origin}


@pytest.fixture(scope="module")
def run(surface_assembly, tmp_path_factory) -> dict:
    return _compose(surface_assembly, tmp_path_factory.mktemp("e3.4_run"))


def _extend(run: dict, **overrides) -> RunManifest:
    keys = (
        "base", "matrix", "matrix_manifest", "corpus_manifest", "stack_manifest", "grid",
        "surfaces", "written", "ts6", "agreements", "verdicts", "claim_design",
        "economic_results", "economic_differences", "economics_dir",
    )
    return extend_run_manifest(**{**{k: run[k] for k in keys}, **overrides})


def _copied_outputs(run: dict, tmp_path: Path) -> dict:
    """A private copy of the written files, so a test can damage one without
    touching the module fixture (the mutation-harness rule: copy first)."""
    copy = tmp_path / "outputs"
    shutil.copytree(run["out"], copy)
    written = {
        name: {kind: copy / Path(path).name for kind, path in files.items()}
        for name, files in run["written"].items()
    }
    assert all(p.is_file() for files in written.values() for p in files.values())
    return written


# ─────────────────────────────────────── reproduction and recomputation


def test_two_runs_reproduce_byte_identically_apart_from_the_hash_excluded_fields(
    surface_assembly, run: dict, tmp_path: Path
) -> None:
    """A SECOND full composition — a second CV run, a second output directory,
    a second set of written files — yields the same substance and the same
    content_hash; the only JSON differences are the fields the hash scheme
    excludes by name. Compared in FULL (every top-level field, CLAUDE.md
    rule 3), not on selected fields: output_hashes included, which is what
    proves the written bytes reproduce and that no path reached the record."""
    second = _compose(surface_assembly, tmp_path / "second")
    a = json.loads(run["manifest"].to_json())
    b = json.loads(second["manifest"].to_json())
    excluded = RunManifest.hash_excluded_fields()
    assert excluded == {"content_hash", "generated_at", "scores_first_visible", "run_id"}
    assert {k: v for k, v in a.items() if k not in excluded} == {
        k: v for k, v in b.items() if k not in excluded
    }
    assert run["manifest"].content_hash == second["manifest"].content_hash
    # the two runs wrote into different directories, and the record cannot tell
    assert run["out"] != second["out"]
    assert a["output_hashes"] == b["output_hashes"] and len(a["output_hashes"]) == 30


def test_every_recorded_hash_matches_its_artifact_by_recomputation(run: dict) -> None:
    """Corpus, feature stack, training matrix, benchmark, and every written
    file: each hash in the manifest is recomputed HERE from the artifact it
    names — never read back from another record — and `output_hashes` is
    compared in full against the directory listing, so a file written but not
    recorded (or recorded but not written) fails too."""
    manifest, out = run["manifest"], run["out"]
    links = manifest.provenance_chain["links"]

    corpus = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
    assert links["corpus"]["content_hash"] == CorpusManifest(**corpus).compute_content_hash()
    assert manifest.upstream_hashes["corpus"] == links["corpus"]["content_hash"]

    stack_dir = Path(run["grid"].stack_dir)
    stack = json.loads((stack_dir / "provenance.json").read_text())
    assert links["feature_stack"]["content_hash"] == FeatureStackManifest(**stack).compute_content_hash()
    assert manifest.upstream_hashes["feature_stack"] == links["feature_stack"]["content_hash"]
    assert links["feature_stack"]["dem_content_hash"] == file_sha256(Path(stack["dem_path"]))

    assert links["training_matrix"]["matrix_sha256"] == matrix_sha256(run["matrix"])
    assert manifest.upstream_hashes["training_matrix"] == run["matrix_manifest"].compute_content_hash()

    assert links["ts6_benchmark"]["content_hash"] == file_sha256(Path(run["ts6"].raster_path))

    expected = {
        p.name: file_sha256(p)
        for p in out.iterdir()
        if p.is_file() and p.name not in ("run_manifest.json", "ts6_fixture.tif")
    }
    expected |= {f"economics/{p.name}": file_sha256(p) for p in (out / "economics").iterdir() if p.is_file()}
    assert manifest.output_hashes == expected and len(expected) == 30
    for name, block in manifest.surfaces.items():
        for kind in ("prediction", "uncertainty"):
            assert block["rasters"][kind]["sha256"] == file_sha256(out / block["rasters"][kind]["file"])
        assert block["sidecar"]["sha256"] == file_sha256(out / block["sidecar"]["file"])


def test_output_hashes_are_keyed_by_basename_never_by_path(run: dict) -> None:
    """A path in the substance is the E2.4-audit defect one artifact over:
    the record must not vary with the directory the run wrote into."""
    keys = set(run["manifest"].output_hashes)
    surface_keys = {k for k in keys if not k.startswith("economics/")}
    assert surface_keys == {Path(p).name for files in run["written"].values() for p in files.values()}
    # economics files carry ONE constant relative component — the subdirectory's name — never a directory of the run
    assert all(k.count("/") <= 1 and not Path(k).is_absolute() and (not k.startswith("economics/") or k.count("/") == 1) for k in keys)
    assert str(run["out"]) not in run["manifest"].to_json()


# ───────────────────────────────────────────── refusals, each by name


def test_a_missing_surface_fails_by_name(run: dict, tmp_path: Path) -> None:
    written = _copied_outputs(run, tmp_path)
    written["random_forest"]["uncertainty"].unlink()
    with pytest.raises(ValueError, match=r"uncertainty surface for estimator 'random_forest' is missing"):
        _extend(run, written=written)
    # …and a surface never handed to the emitter at all, distinct from a file that vanished
    written = _copied_outputs(run, tmp_path / "b")
    del written["ordinary_kriging"]["prediction"]
    with pytest.raises(ValueError, match=r"prediction surface for estimator 'ordinary_kriging' is missing"):
        _extend(run, written=written)


def test_a_raster_holding_other_values_is_refused_not_hashed(run: dict, tmp_path: Path) -> None:
    """The raster's VALUES are re-read and compared to the in-memory surface
    — a file that merely exists under the right name with the right tags is
    not accepted as that surface."""
    written = _copied_outputs(run, tmp_path)
    path = written["mean_baseline"]["prediction"]
    with rasterio.open(path) as dataset:
        profile, tags = dataset.profile, dataset.tags()
        values = dataset.read(1)
    values = np.where(np.isfinite(values), values + 1.0, values).astype(np.float32)
    with rasterio.open(path, "w", **profile) as dataset:
        dataset.write(values, 1)
        dataset.update_tags(**tags)
    with pytest.raises(ValueError, match=r"prediction raster for 'mean_baseline' .* does not hold the in-memory"):
        _extend(run, written=written)


def test_a_cherry_picked_surface_set_is_refused(run: dict) -> None:
    """Every cross-validated estimator reaches a surface, and only those:
    dropping one from any of the three per-estimator inputs is refused, naming
    both sets."""
    for key in ("surfaces", "written", "agreements"):
        subset = {k: v for k, v in run[key].items() if k != "ordinary_kriging"}
        with pytest.raises(ValueError, match=rf"the {key if key != 'written' else 'written files'} cover estimators .*never cherry-picked"):
            _extend(run, **{key: subset})


def test_inconsistent_records_of_one_fact_are_refused_naming_every_record(run: dict) -> None:
    # the benchmark's identity: the agreement quotes one hash, the surface another
    forged = run["ts6"].model_copy(update={"content_hash": "sha256:" + "0" * 64})
    with pytest.raises(ValueError, match=r"benchmark hash in mean_baseline's agreement is recorded inconsistently"):
        _extend(run, ts6=forged)
    # an agreement filed under the wrong estimator
    swapped = dict(run["agreements"])
    swapped["mean_baseline"], swapped["random_forest"] = swapped["random_forest"], swapped["mean_baseline"]
    with pytest.raises(ValueError, match=r"recorded under 'mean_baseline' identifies itself as 'random_forest'"):
        _extend(run, agreements=swapped)
    # a verdict set that silently omits a design, and a claim design the run never executed
    fewer = {k: v for k, v in run["verdicts"].items() if k != "random_k_fold"}
    with pytest.raises(ValueError, match=r"verdicts cover designs .* but the run executed"):
        _extend(run, verdicts=fewer)
    with pytest.raises(ValueError, match=r"claim_design 'leave_one_station_out' is not a design this run executed"):
        _extend(run, claim_design="leave_one_station_out")


def test_a_mutated_base_and_a_second_extension_are_both_refused(run: dict) -> None:
    mutated = run["base"].model_copy(update={"seed": run["base"].seed + 1})
    with pytest.raises(ValueError, match=r"run manifest's content_hash does not match its own contents"):
        _extend(run, base=mutated)
    with pytest.raises(ValueError, match=r"has already been extended"):
        _extend(run, base=run["manifest"])


def test_the_written_origin_must_equal_the_recomputed_one(run: dict, tmp_path: Path) -> None:
    """The emitter recomputes the surface origin with combine_origins over the
    stack and the matrix; a sidecar declaring a more real origin than the
    inputs support is refused — the laundering direction, by name."""
    written = _copied_outputs(run, tmp_path)
    sidecar = written["ordinary_kriging"]["provenance"]
    record = json.loads(sidecar.read_text())
    record["data_origin"] = DataOrigin.MEASURED.value
    sidecar.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match=r"declares data_origin 'MEASURED' but combine_origins .* gives 'SYNTHETIC'"):
        _extend(run, written=written)


# ───────────────────────────────── the mapping, the verdict, the limit


def test_ts6_agreement_is_a_mapping_with_one_self_identifying_agreement_per_estimator(run: dict) -> None:
    """Karl's arity decision (E3.3 approval): one agreement PER estimator,
    keyed by name, never collapsed to one number. And the CV-only E2.4
    artifact still records None — the comparison step did not run there."""
    agreements = run["manifest"].ts6_agreement
    assert set(agreements) == {MEAN_BASELINE_NAME, "ordinary_kriging", "random_forest"}
    assert all(isinstance(a, TS6Agreement) and a.estimator_name == name for name, a in agreements.items())
    assert RunManifest.model_fields["ts6_agreement"].annotation == (dict[str, TS6Agreement] | None)
    committed = RunManifest(**json.loads((REPO_ROOT / "data" / "runs" / "e2.4" / "run_manifest.json").read_text()))
    assert committed.ts6_agreement is None and committed.surfaces is None


def test_the_recorded_claim_verdicts_match_the_guard_run_directly_on_the_final_manifest(run: dict) -> None:
    """E2.5's verdict as DATA: for every design the run executed, the record
    equals `evaluate_claim` run directly on the FINAL manifest — full
    `to_record()` equality, not the failing set alone. The failing sets are
    then pinned against E2.5 §2's measured table: the pre-registration gate
    fails everywhere (no threshold exists), and random k-fold additionally
    fails precondition 1 BY RECORD — two different sets, which is what
    separates 'the guard discriminates' from 'the guard refuses everything'."""
    manifest = run["manifest"]
    claim = manifest.claim
    designs = [d["name"] for d in manifest.cross_validation["designs"]]
    assert claim["design"] == CLAIM_DESIGN and set(claim["verdicts"]) == set(designs) and len(designs) == 3
    direct = {
        d: evaluate_claim(manifest, design=d, feature_stack_manifest=run["stack_manifest"]).to_record()
        for d in designs
    }
    assert claim["verdicts"] == direct
    failing = {
        d: {r["precondition"] for r in v["preconditions"] if not r["passed"]}
        for d, v in claim["verdicts"].items()
    }
    gate = Precondition.PRE_REGISTERED_THRESHOLD.value
    assert failing == {
        "leave_one_cluster_out": {gate},
        "leave_one_site_out": {gate},
        "random_k_fold": {gate, Precondition.SPATIALLY_BLOCKED_CV.value},
    }
    assert all(v["eligible"] is False and v["watermark"] for v in claim["verdicts"].values())


def test_surfaces_block_records_each_estimators_summary_origin_and_watermark(run: dict) -> None:
    manifest, out = run["manifest"], run["out"]
    for name, result in run["surfaces"].items():
        sidecar = json.loads((out / f"{name}.provenance.json").read_text())
        expected = {
            **result.summary(),
            "data_origin": "SYNTHETIC",
            "watermark": sidecar["watermark"],
            "publishable": False,
            "rasters": {
                kind: {"file": f"{name}_{kind}.tif", "sha256": file_sha256(out / f"{name}_{kind}.tif")}
                for kind in ("prediction", "uncertainty")
            },
            "sidecar": {"file": f"{name}.provenance.json", "sha256": file_sha256(out / f"{name}.provenance.json")},
        }
        assert manifest.surfaces[name] == expected
    assert manifest.prediction_grid == run["grid"].identity()
    assert manifest.data_origin == "SYNTHETIC"


def test_the_chain_block_states_the_remaining_limits_and_the_former_one_is_measured_gone(
    run: dict, tmp_path: Path
) -> None:
    """UPDATED at HASH.1 commit 2 — this test was written at E3.4 to pin the
    path-hash DEFECT'S PRESENCE (a different stack hash AND a different
    raster for the same surface from the same DEM bytes elsewhere) and to go
    red when the fix landed. It did. Now it pins the fix: the same bytes
    elsewhere give the SAME stack hash and the SAME raster bytes, and the
    chain block says what is true — the corpus, the stack and (for
    same-endianness hosts) the matrix are verifiable off-machine; the
    remaining limits are named rather than waved at."""
    chain = run["manifest"].provenance_chain
    assert chain["limit"] == CHAIN_LIMIT_NOTE
    assert chain["verifiable_off_machine"] == ["corpus", "feature_stack", "training_matrix (same-endianness)"]
    assert {k: v["verifiable_off_machine"] for k, v in chain["links"].items()} == {
        "corpus": True,
        "feature_stack": True,
        "training_matrix": "same-endianness hosts",
        "ts6_benchmark": "not measured — a synthetic fixture today; G3.1 delivers the real raster",
        "surfaces": "directory-independent; cross-GDAL-version byte identity not measured",
        "economics": "directory-independent; cross-GDAL-version byte identity not measured",  # E4.3: the same limit, no fourth
    }
    assert len(chain["path_dependent_hashes"]["remaining_limits"]) == 3
    # the measurement: the former limit is gone
    dem_path = Path(run["stack_manifest"]["dem_path"])
    other_dem = tmp_path / "elsewhere" / "dem.tif"
    other_dem.parent.mkdir()
    shutil.copyfile(dem_path, other_dem)
    assert file_sha256(other_dem) == file_sha256(dem_path)
    other = build_covariate_stack(other_dem, tmp_path / "stack2", dem_data_origin=DataOrigin.SYNTHETIC)
    grid2 = PredictionGrid.from_stack(other["provenance"].parent)
    assert grid2.dem_content_hash == run["grid"].dem_content_hash
    assert grid2.stack_content_hash == run["grid"].stack_content_hash  # was: differs
    result = run["surfaces"]["ordinary_kriging"]
    rewritten = write_surface(
        result, grid2, tmp_path / "out2", data_origin=run["origin"], verdict=run["verdicts"][CLAIM_DESIGN]
    )
    assert file_sha256(rewritten["prediction"]) == run["manifest"].output_hashes["ordinary_kriging_prediction.tif"]  # was: differs


def test_a_stack_manifest_that_embeds_a_dem_path_is_refused_by_name(run: dict) -> None:
    """The emitter ASSERTS the stack substance is path-free rather than
    assuming it, so a path creeping back under `dem` cannot silently make
    every downstream hash directory-dependent again."""
    stack = json.loads(json.dumps(run["stack_manifest"]))
    stack["layers"][3]["dem"]["path"] = "/somewhere/dem.tif"
    with pytest.raises(ValueError, match=r"embeds a DEM path at \['layers\[3\]\.dem'\]"):
        _extend(run, stack_manifest=stack)


# ──────────────────── recomputed, never copied: the separating fixtures


def test_a_tampered_upstream_record_whose_quoted_hash_still_agrees_everywhere_is_refused(run: dict) -> None:
    """THE FIXTURE THAT SEPARATES "recomputed" FROM "copied" (CLAUDE.md rule 4).
    Every other refusal test here makes two RECORDS disagree, which a copying
    emitter would also catch. Here every record of the hash still AGREES —
    only the artifact's SUBSTANCE was edited behind its recorded hash — so
    the refusal can only come from recomputing the hash over that substance.
    Corpus and stack each, by name."""
    corpus = dict(run["corpus_manifest"])
    corpus["corpus_row_count"] = corpus["corpus_row_count"] + 1  # the hash still reads the old value
    with pytest.raises(ValueError, match=r"corpus hash is recorded inconsistently: recomputed_from_substance="):
        _extend(run, corpus_manifest=corpus)
    stack = dict(run["stack_manifest"])
    stack["registry_version"] = stack["registry_version"] + 1
    with pytest.raises(ValueError, match=r"feature-stack hash is recorded inconsistently: recomputed_from_substance="):
        _extend(run, stack_manifest=stack)


def test_the_benchmark_hash_is_recomputed_from_the_raster_bytes_not_trusted(run: dict) -> None:
    """Same separation for the benchmark: the surface AND every agreement quote
    the same forged hash, so only recomputation from the bytes can refuse."""
    forged_hash = "sha256:" + "0" * 64
    forged_ts6 = run["ts6"].model_copy(update={"content_hash": forged_hash})
    forged_agreements = {
        name: a.model_copy(update={"resampling": {**a.resampling, "ts6_content_hash": forged_hash}})
        for name, a in run["agreements"].items()
    }
    with pytest.raises(ValueError, match=r"TS-6 raster hash is recorded inconsistently: recomputed_from_bytes="):
        _extend(run, ts6=forged_ts6, agreements=forged_agreements)


# ──────────────────── commit 3: two BACKLOG triggers fired by the emitter


def test_the_environment_sits_beside_the_contract_versions_and_is_recomputable(run: dict) -> None:
    """BACKLOG §3 "Dependency versions into the provenance manifest" —
    trigger "the Phase-3 manifest emitter", fired here. The lockfile hash is
    recomputed from the committed file; the versions are read from the
    running interpreter — compared in full against an independent read."""
    import importlib.metadata
    import platform

    from engine.prospectivity.provenance.environment import RECORDED_PACKAGES, REQUIREMENTS_LOCK

    env = run["manifest"].inputs["environment"]
    assert env["requirements_lock_sha256"] == file_sha256(REQUIREMENTS_LOCK) == file_sha256(REPO_ROOT / "requirements.lock")
    assert env["python"] == platform.python_version()
    assert env["packages"] == {name: importlib.metadata.version(name) for name in RECORDED_PACKAGES}
    assert len(env["packages"]) == 9 and all(env["packages"].values())
    assert "environment" in run["manifest"].substance()["inputs"]  # INSIDE the hash
    # the CV-only E2.4 artifact predates the block, and its inputs say so by absence
    committed = json.loads((REPO_ROOT / "data" / "runs" / "e2.4" / "run_manifest.json").read_text())
    assert "environment" not in committed["inputs"]


def test_the_corpus_bytes_are_pinned_by_the_run_and_recomputed_from_the_csv(
    run: dict, tmp_path: Path, monkeypatch
) -> None:
    """The other fired trigger (BACKLOG §3, "Corpus CSV bytes are not
    hash-pinned"): the run records the sha256 of the CSV it was trained
    from, recomputed from the file the corpus manifest names — and the link
    says it agrees with nothing upstream yet, which is the honest state.

    The missing-file refusal cannot be reached by editing `corpus_path`:
    that is IN the corpus manifest's substance, so the substance check
    fires first (measured — the first draft of this test tried it). It is
    reached when the manifest is intact and the file is gone, which is
    staged by pointing the emitter's repo root at a tree without the CSV."""
    corpus_link = run["manifest"].provenance_chain["links"]["corpus"]
    assert corpus_link["csv_file"] == "master_observations.csv"
    assert corpus_link["csv_sha256"] == file_sha256(REPO_ROOT / "data" / "corpus" / "master_observations.csv")
    assert "agrees with nothing" in corpus_link["csv_note"]
    import engine.prospectivity.provenance.emitter as emitter

    monkeypatch.setattr(emitter, "_REPO_ROOT", tmp_path)  # an intact manifest, no CSV beneath it
    with pytest.raises(ValueError, match=r"corpus_path 'data/corpus/master_observations.csv', which is not a file"):
        _extend(run)


# ──────────────── the E3.4 prompt's named tests the first pass lacked


def test_each_agreement_entry_carries_r_n_eff_mean_difference_role_note_and_the_benchmark_state(run: dict) -> None:
    """Prompt §3: every mapping entry carries the five facts. The benchmark
    state today is the FIXTURE path's — None with the not-applicable note;
    the real path with a null Contract 6 value REFUSES in E3.3's comparison
    (no manifest exists to carry a 'refused' state), which is the design."""
    entries = json.loads(run["manifest"].to_json())["ts6_agreement"]
    for name, entry in entries.items():
        assert entry["estimator_name"] == name and entry["role_note"] == "benchmark_only"
        assert {"spatial_correlation", "n_eff", "mean_difference"} <= set(entry)
        assert entry["mean_difference"] is not None
        assert entry["benchmark_uncertainty"] is None
        assert entry["benchmark_uncertainty_note"] == "not applicable — synthetic fixture, not a digitized surface"
    assert entries["ordinary_kriging"]["n_eff"] is not None and entries["ordinary_kriging"]["spatial_correlation"] is not None
    assert entries["mean_baseline"]["spatial_correlation"] is None  # constant surface: undefined, by name


def test_an_empty_agreement_mapping_and_a_null_field_are_distinguishable_and_the_emitter_refuses_the_empty_one(run: dict) -> None:
    """Prompt §2: 'no comparison ran' (None) and 'ran and produced nothing'
    ({}) must not read the same. They serialize differently and hash
    differently — and the second cannot be EMITTED at all, because the
    registry always holds the baseline, so an empty mapping is refused by
    name as a cherry-pick of zero estimators."""
    null = RunManifest(run_id="x", seed=0, ts6_agreement=None).finalize()
    empty = RunManifest(run_id="x", seed=0, ts6_agreement={}).finalize()
    assert '"ts6_agreement": null' in null.to_json() and '"ts6_agreement": {}' in empty.to_json()
    assert null.content_hash != empty.content_hash
    with pytest.raises(ValueError, match=r"the agreements cover estimators \[\] but the run cross-validated"):
        _extend(run, agreements={})


def test_the_path_dependent_hash_count_equals_the_measured_two_directory_difference(
    run: dict, tmp_path: Path
) -> None:
    """E3.4: the limit's scope as a NUMBER, MEASURED — then 11 (the stack
    hash, the matrix hash, 9 of 10 files). HASH.1 commit 2 removed the path
    from the stack substance and this test went red as designed; it now
    pins the measured ZERO: a second extension over a stack built from the
    same DEM bytes at another path has exactly the same hash VALUES and the
    same content_hash. A path creeping back anywhere in the chain drives
    the number up and this test red."""
    import re

    from engine.prospectivity.features.dem_grid import DemGrid
    from engine.prospectivity.features.registry import build_default_registry
    from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
    from engine.prospectivity.training_matrix import assemble_training_matrix

    block = run["manifest"].provenance_chain["path_dependent_hashes"]
    assert (block["count"], block["was"]) == (0, 11)  # HASH.1 commit 2: measured below, not assumed

    dem_path = Path(run["stack_manifest"]["dem_path"])
    other_dem = tmp_path / "elsewhere" / "dem.tif"
    other_dem.parent.mkdir()
    shutil.copyfile(dem_path, other_dem)
    written = build_covariate_stack(other_dem, tmp_path / "stack2", dem_data_origin=DataOrigin.SYNTHETIC)
    stack2 = json.loads(written["provenance"].read_text())
    dem_grid = DemGrid.load(other_dem)
    matrix2, mm2 = assemble_training_matrix(
        CorpusCsvSampleSource(), dem_grid, build_default_registry().build_all(dem_grid), run["corpus_manifest"], stack2
    )
    grid2 = PredictionGrid.from_stack(written["provenance"].parent)
    report = CrossValidationRunner(splitters=_designs(), registry=_light_registry(matrix2.covariate_names)).run(matrix2, seed=0)
    base2 = emit_run_manifest(report, matrix=matrix2, matrix_manifest=mm2, run_id=RUN_ID)
    verdicts2 = {d.name: evaluate_claim(base2, design=d.name, feature_stack_manifest=stack2) for d in _designs()}
    out2 = tmp_path / "out2"
    written2 = {
        name: write_surface(result, grid2, out2, data_origin=run["origin"], verdict=verdicts2[CLAIM_DESIGN])
        for name, result in run["surfaces"].items()
    }
    agreements2 = compare_all_to_ts6(run["surfaces"], grid2, run["ts6"], surface_data_origin=run["origin"])
    second = extend_run_manifest(
        base2, matrix=matrix2, matrix_manifest=mm2, corpus_manifest=run["corpus_manifest"], stack_manifest=stack2,
        grid=grid2, surfaces=run["surfaces"], written=written2, ts6=run["ts6"], agreements=agreements2,
        verdicts=verdicts2, claim_design=CLAIM_DESIGN,
        economic_results=run["economic_results"], economic_differences=run["economic_differences"],
        economics_dir=run["economics_dir"],
    )
    pattern = re.compile(r"sha256:[0-9a-f]{64}")
    def values(manifest):
        return set(pattern.findall(json.dumps({k: v for k, v in json.loads(manifest.to_json()).items() if k != "content_hash"})))
    differing = values(run["manifest"]) - values(second)
    assert len(differing) == block["count"] == second.provenance_chain["path_dependent_hashes"]["count"] == 0
    assert values(run["manifest"]) == values(second) and len(values(second)) >= 14
    assert second.content_hash == run["manifest"].content_hash  # the whole extension, from another tree


# ═══════════════════════════════ E4.3 — the economics block (2026-08-22)


def _copied_economics(run: dict, tmp_path: Path) -> Path:
    copy = tmp_path / "economics"
    shutil.copytree(run["economics_dir"], copy)
    assert len(list(copy.glob("*.tif"))) == 18
    return copy


def test_the_economics_block_resolves_every_raster_from_the_record_and_recomputes_it(run: dict) -> None:
    """18 rasters + 2 sidecars, resolved FROM economics.footprints.json (no
    name parsed here either): every block entry's sha256 recomputes from the
    file, equals the record's, and is in output_hashes under economics/;
    the block's scenarios carry the cutoff in the DeclaredField shape."""
    manifest = run["manifest"]
    block = manifest.economics
    record = json.loads((run["economics_dir"] / "economics.footprints.json").read_text())["files"]
    assert set(block["rasters"]) == set(record) and len(record) == 18
    assert (block["n_files"], block["n_footprint_rasters"], block["n_difference_rasters"]) == (20, 12, 6)
    for name, entry in block["rasters"].items():
        assert entry["sha256"] == file_sha256(run["economics_dir"] / name) == record[name]["sha256"] == manifest.output_hashes[f"economics/{name}"]
        assert (entry["kind"], entry["estimator"], entry["z"]) == (record[name]["kind"], record[name]["estimator"], record[name]["z"])
        assert set(entry["watermark"]) == {"terrain", "economic_parameters"} and entry["watermark"]["terrain"]["lifted"] is False
    assert block["association"]["sha256"] == file_sha256(run["economics_dir"] / "economics.footprints.json") == manifest.output_hashes["economics/economics.footprints.json"]
    assert manifest.output_hashes["economics/data_origin.yaml"] == file_sha256(run["economics_dir"] / "data_origin.yaml")
    assert [s["cutoff"] for s in block["scenarios"]] == [
        {"value": 10.0, "units": "kg_m2", "data_origin": "AUTHORED", "author": "unrecorded"},
        {"value": 5.5, "units": "kg_m2", "data_origin": "AUTHORED", "author": "unrecorded"},
    ]
    assert block["difference_fraction_of_predictable"] == {"MARKET_STANDARD->STRATEGIC_SUBSIDIZED": {e: {"0.0": 0.0, "1.0": 0.0} for e in ("mean_baseline", "ordinary_kriging", "random_forest")}}
    assert "SEPARATE expiry" in block["watermark_note"]
    assert manifest.provenance_chain["links"]["economics"]["files"] == 20


def test_a_missing_footprint_raster_fails_by_name(run: dict, tmp_path: Path) -> None:
    copy = _copied_economics(run, tmp_path)
    (copy / "footprint__STRATEGIC_SUBSIDIZED__random_forest__z1.tif").unlink()
    with pytest.raises(ValueError, match=r"record names 18 raster\(s\) but the directory holds 17: only in record \['footprint__STRATEGIC_SUBSIDIZED__random_forest__z1.tif'\]"):
        _extend(run, economics_dir=copy)
    # …and a result that names no file at all, distinct from a file that vanished
    results = [r.model_copy(deep=True) for r in run["economic_results"]]
    results[0].footprints["ordinary_kriging"]["0.0"]["raster_file"] = None
    with pytest.raises(ValueError, match=r"scenario 'MARKET_STANDARD' records no raster_file for 'ordinary_kriging' at z=0.0"):
        _extend(run, economic_results=results)


def test_a_record_that_disagrees_with_the_bytes_or_the_tags_fails_by_name(run: dict, tmp_path: Path) -> None:
    copy = _copied_economics(run, tmp_path)
    record = json.loads((copy / "economics.footprints.json").read_text())
    record["files"]["footprint__MARKET_STANDARD__mean_baseline__z0.tif"]["sha256"] = "sha256:" + "0" * 64
    (copy / "economics.footprints.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match=r"sha256 of footprint__MARKET_STANDARD__mean_baseline__z0.tif is recorded inconsistently: recomputed_from_bytes="):
        _extend(run, economics_dir=copy)
    copy2 = _copied_economics(run, tmp_path / "b")
    record = json.loads((copy2 / "economics.footprints.json").read_text())
    record["files"]["difference__MARKET_STANDARD__STRATEGIC_SUBSIDIZED__random_forest__z0.tif"]["counts"]["only_b"] = 7
    (copy2 / "economics.footprints.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match=r"n_only_b of difference__MARKET_STANDARD__STRATEGIC_SUBSIDIZED__random_forest__z0.tif is recorded inconsistently: recomputed_from_values='0'"):
        _extend(run, economics_dir=copy2)


def test_the_economics_origin_is_recomputed_never_declared_the_laundering_direction(run: dict) -> None:
    """combine_origins(surface SYNTHETIC, cutoff AUTHORED) = AUTHORED is
    recomputed at emission; a result declaring DERIVED is refused by name
    even though its rasters and record agree with each other."""
    results = [r.model_copy(update={"data_origin": "DERIVED"}) if r.scenario_name == "MARKET_STANDARD" else r for r in run["economic_results"]]
    with pytest.raises(ValueError, match=r"data_origin of footprint__MARKET_STANDARD__mean_baseline__z0.tif is recorded inconsistently: recomputed_by_combine_origins='AUTHORED'.*manifest='DERIVED'"):
        _extend(run, economic_results=results)


def test_the_terrain_reason_is_derived_from_the_stacks_declared_dem_origin_not_copied(run: dict, tmp_path: Path) -> None:
    """A record and a result that both claim the terrain reason LIFTED on a
    SYNTHETIC stack agree with each other and are still refused: the state
    is re-derived from the declared DEM origin."""
    copy = _copied_economics(run, tmp_path)
    record = json.loads((copy / "economics.footprints.json").read_text())
    for entry in record["files"].values():
        for reason in entry["watermark"]["reasons"]:
            if reason["reason"] == "terrain":
                reason["lifted"] = True
    (copy / "economics.footprints.json").write_text(json.dumps(record))
    def lifted(records):
        out = []
        for r in records:
            wm = json.loads(json.dumps(r.watermark))
            for reason in wm["reasons"]:
                if reason["reason"] == "terrain":
                    reason["lifted"] = True
            out.append(r.model_copy(update={"watermark": wm}))
        return out
    with pytest.raises(ValueError, match=r"terrain reason of .* is recorded inconsistently: derived_from_stack_dem_origin='False', record='True', manifest='True'"):
        _extend(run, economics_dir=copy, economic_results=lifted(run["economic_results"]), economic_differences=lifted(run["economic_differences"]))


def test_the_claim_verdicts_failing_and_passing_sets_do_not_move_when_the_economics_block_exists(run: dict) -> None:
    """§3: adding an economics layer adds no precondition and lifts none.
    Compared as SETS of precondition names, per design, BEFORE (the CV-only
    base manifest) and AFTER (the final manifest with the economics block) —
    both the failing and the passing sets, because a guard that only pinned
    failures could not be told from a blanket refusal."""
    stack = run["stack_manifest"]
    designs = [d["name"] for d in run["base"].cross_validation["designs"]]
    def sets(manifest):
        out = {}
        for d in designs:
            v = evaluate_claim(manifest, design=d, feature_stack_manifest=stack)
            out[d] = (frozenset(r.precondition.value for r in v.results if not r.passed), frozenset(r.precondition.value for r in v.results if r.passed))
        return out
    before, after = sets(run["base"]), sets(run["manifest"])
    assert before == after
    gate = Precondition.PRE_REGISTERED_THRESHOLD.value
    assert after["leave_one_site_out"][0] == {gate} and len(after["leave_one_site_out"][1]) == 5
    assert after["random_k_fold"][0] == {gate, Precondition.SPATIALLY_BLOCKED_CV.value} and len(after["random_k_fold"][1]) == 4
    assert run["manifest"].economics is not None and run["base"].economics is None


def test_the_two_historical_artifacts_hashes_did_not_move_at_shape_tolerant_hashings_first_real_use() -> None:
    """§4: RunManifest gained `economics` (schema 3); the legacy set of two
    keeps its literal hashes — HASH.1's property at first real exercise."""
    pins = {
        "data/corpus/manifest.json": "sha256:0227d6df608ee23476c7f5915bede82f1ffb360c542e33152386257a2fd07fd9",
        "data/runs/e2.4/run_manifest.json": "sha256:e3ac1561b8f681bb30ce05c9638325f9f58b0223ee56596e53fc68d89f6e7ad4",
    }
    raw = json.loads((REPO_ROOT / "data/runs/e2.4/run_manifest.json").read_text())
    assert raw["content_hash"] == RunManifest(**raw).compute_content_hash() == pins["data/runs/e2.4/run_manifest.json"]
    assert json.loads((REPO_ROOT / "data/corpus/manifest.json").read_text())["content_hash"] == pins["data/corpus/manifest.json"]
    assert RunManifest.SCHEMA_VERSION == 3 and RunManifest.model_fields["economics"].default is None


def test_a_count_forged_consistently_in_tag_record_and_result_is_refused_by_recomputation_from_the_pixels(run: dict, tmp_path: Path) -> None:
    """THE SEPARATING FIXTURE for counts (found by mutation E-M6, which
    survived the first test set: an emitter reading n_minable from the TAG
    passed every test, because the only count-tamper test forged the record
    alone and was caught by tag-vs-record — which a copying emitter also
    catches). Here the tag, the record and the manifest's result all agree
    on a wrong count, the record's sha256 is updated to the re-tagged bytes,
    and only recomputation from the PIXELS can refuse. Both raster kinds."""
    copy = _copied_economics(run, tmp_path)
    record = json.loads((copy / "economics.footprints.json").read_text())

    def forge(name: str, tag: str, value: str, record_key, result_records, kind: str):
        # the file is a COG: re-tagging breaks its layout, which GDAL refuses by
        # default — accepted here on purpose (the forgery must change the bytes)
        with rasterio.open(copy / name, "r+", IGNORE_COG_LAYOUT_BREAK="YES") as ds:
            ds.update_tags(**{tag: value})
        record["files"][name]["sha256"] = file_sha256(copy / name)
        record_key(record["files"][name])
        return result_records

    # a footprint: n_minable 2880 -> 7 everywhere but the pixels
    fp = "footprint__MARKET_STANDARD__mean_baseline__z0.tif"
    forge(fp, "n_minable", "7", lambda e: e.__setitem__("n_minable", 7), None, "footprint")
    results = [r.model_copy(deep=True) for r in run["economic_results"]]
    results[0].footprints["mean_baseline"]["0.0"]["n_minable"] = 7
    (copy / "economics.footprints.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match=rf"n_minable of {fp} is recorded inconsistently: recomputed_from_values='2880', raster_tag='7', record='7', manifest='7'"):
        _extend(run, economics_dir=copy, economic_results=results)

    # a difference: n_only_b 0 -> 7 everywhere but the pixels
    copy2 = _copied_economics(run, tmp_path / "b")
    record2 = json.loads((copy2 / "economics.footprints.json").read_text())
    df = "difference__MARKET_STANDARD__STRATEGIC_SUBSIDIZED__ordinary_kriging__z1.tif"
    with rasterio.open(copy2 / df, "r+", IGNORE_COG_LAYOUT_BREAK="YES") as ds:
        ds.update_tags(n_only_b="7")
    record2["files"][df]["sha256"] = file_sha256(copy2 / df)
    record2["files"][df]["counts"]["only_b"] = 7
    (copy2 / "economics.footprints.json").write_text(json.dumps(record2))
    differences = [d.model_copy(deep=True) for d in run["economic_differences"]]
    differences[0].footprints["ordinary_kriging"]["1.0"]["n_minable"] = 7
    with pytest.raises(ValueError, match=rf"n_only_b of {df} is recorded inconsistently: recomputed_from_values='0', raster_tag='7', record='7', manifest='7'"):
        _extend(run, economics_dir=copy2, economic_differences=differences)
