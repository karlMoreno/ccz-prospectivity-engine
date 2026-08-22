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
    inputs = dict(
        base=base, matrix=matrix, matrix_manifest=matrix_manifest, corpus_manifest=corpus,
        stack_manifest=stack, grid=grid, surfaces=surfaces, written=written, ts6=ts6,
        agreements=agreements, verdicts=verdicts, claim_design=CLAIM_DESIGN,
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
    assert a["output_hashes"] == b["output_hashes"] and len(a["output_hashes"]) == 10


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
    assert links["feature_stack"]["dem_content_hash"] == file_sha256(Path(stack["dem"]["path"]))

    assert links["training_matrix"]["matrix_sha256"] == matrix_sha256(run["matrix"])
    assert manifest.upstream_hashes["training_matrix"] == run["matrix_manifest"].compute_content_hash()

    assert links["ts6_benchmark"]["content_hash"] == file_sha256(Path(run["ts6"].raster_path))

    expected = {
        p.name: file_sha256(p)
        for p in out.iterdir()
        if p.name not in ("run_manifest.json", "ts6_fixture.tif")
    }
    assert manifest.output_hashes == expected and len(expected) == 10
    for name, block in manifest.surfaces.items():
        for kind in ("prediction", "uncertainty"):
            assert block["rasters"][kind]["sha256"] == file_sha256(out / block["rasters"][kind]["file"])
        assert block["sidecar"]["sha256"] == file_sha256(out / block["sidecar"]["file"])


def test_output_hashes_are_keyed_by_basename_never_by_path(run: dict) -> None:
    """A path in the substance is the E2.4-audit defect one artifact over:
    the record must not vary with the directory the run wrote into."""
    keys = set(run["manifest"].output_hashes)
    assert keys == {Path(p).name for files in run["written"].values() for p in files.values()}
    assert all("/" not in k and not Path(k).is_absolute() for k in keys)
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


def test_the_chain_limit_is_in_the_output_and_matches_the_measured_blast_radius(
    run: dict, tmp_path: Path
) -> None:
    """THE LIMIT, stated where a reader meets it — and MEASURED, not asserted:
    the same DEM bytes at a different path yield a different stack hash (the
    E2.4 audit's row M, reproduced) AND a different raster for the SAME
    surface, because the raster's tags carry the stack hash. So the chain
    block must say only the corpus is verifiable off-machine.

    This test pins a DEFECT'S PRESENCE on purpose: when the BACKLOG §3 path
    fix lands, `differs` becomes False, this goes red, and the chain block's
    claim must be updated in the same change — which is the point."""
    chain = run["manifest"].provenance_chain
    assert chain["limit"] == CHAIN_LIMIT_NOTE and chain["verifiable_off_machine"] == ["corpus"]
    assert {k: v["verifiable_off_machine"] for k, v in chain["links"].items()} == {
        "corpus": True,
        "feature_stack": False,
        "training_matrix": False,
        "ts6_benchmark": "not measured — a synthetic fixture today; G3.1 delivers the real raster",
        "surfaces": False,
    }
    # the measurement
    dem_path = Path(run["stack_manifest"]["dem"]["path"])
    other_dem = tmp_path / "elsewhere" / "dem.tif"
    other_dem.parent.mkdir()
    shutil.copyfile(dem_path, other_dem)
    assert file_sha256(other_dem) == file_sha256(dem_path)
    other = build_covariate_stack(other_dem, tmp_path / "stack2", dem_data_origin=DataOrigin.SYNTHETIC)
    grid2 = PredictionGrid.from_stack(other["provenance"].parent)
    assert grid2.dem_content_hash == run["grid"].dem_content_hash
    stack_differs = grid2.stack_content_hash != run["grid"].stack_content_hash
    result = run["surfaces"]["ordinary_kriging"]
    rewritten = write_surface(
        result, grid2, tmp_path / "out2", data_origin=run["origin"], verdict=run["verdicts"][CLAIM_DESIGN]
    )
    raster_differs = file_sha256(rewritten["prediction"]) != run["manifest"].output_hashes["ordinary_kriging_prediction.tif"]
    assert (stack_differs, raster_differs) == (True, True), (
        "the path-hash limit no longer reproduces — update provenance_chain's claim (BACKLOG §3)"
    )
    assert np.array_equal(
        rasterio.open(rewritten["prediction"]).read(1), rasterio.open(run["out"] / "ordinary_kriging_prediction.tif").read(1), equal_nan=True
    )  # …while the VALUES are identical: only the identity moved


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
