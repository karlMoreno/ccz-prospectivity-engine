"""E2.4 §2 — the CrossValidationRunner against the eight runner obligations
(docs/BACKLOG.md §3 "E2.4 runner obligations"), the four review probes, and
the §2D manifest/chain requirements.

Fixture notes (CLAUDE.md rule 4): the REAL 35-station matrix is used where
the claim is about the real geometry (the LIVE stale-refit case: kriging
fits the LOCO fold that trains on E and refuses the one that trains on W);
a `_Spy` estimator with a scripted refusal is used where the claim is about
the runner's handling independent of any estimator's math; a `_Dummy`
fourth estimator (constant prediction, records the feature width it was
handed) separates "routed by declaration" from "routed by name".
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import pytest

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
from engine.prospectivity.estimators.random_forest import RandomForestEstimator
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME, EstimatorRegistry
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import (
    build_default_registry as build_covariate_registry,
)
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.training_matrix import (
    TrainingMatrix,
    TrainingMatrixManifest,
    assemble_training_matrix,
)
from engine.prospectivity.validation.metrics import METRIC_NAMES
from engine.prospectivity.validation.runner import (
    STATUS_REFUSED,
    STATUS_SCORED,
    CrossValidationRunner,
    CVReport,
    emit_run_manifest,
    run_watermark,
)
from engine.prospectivity.validation.splitter import (
    LeaveOneStationOutSplitter,
    RandomKFoldSplitter,
    SingleLinkageBlockSplitter,
    assert_claim_eligible,
    leave_one_cluster_out,
    leave_one_site_out,
)
from tests.fixtures.rasters import write_synthetic_bathymetry

REPO_ROOT = Path(__file__).resolve().parent.parent

KRIGING_OBLIGATION_FIELDS = (
    # obligation 4: the fitted + alternative models, the bin table the fit
    # SAW, every excluded bin with its reason, the unsupported lag range
    "used_model_family", "nugget", "partial_sill", "sill", "fitted_bins", "excluded_bins",
    "unsupported_km", "alternative", "used_weighted_sse", "min_pairs", "max_fit_lag_km",
    "coordinate_system", "n_training",
    # obligation 5: the ceiling flag NEXT TO range_km, its floor twin, residual_dof
    "range_km", "range_at_candidate_ceiling", "range_below_first_supported_lag", "residual_dof",
    # obligation 7 + Karl's §1B framing
    "uncertainty_method", "uncertainty_semantics", "no_structure", "verdict",
)


# ------------------------------------------------------------ fixtures


@pytest.fixture(scope="module")
def real_matrix():
    with tempfile.TemporaryDirectory() as tmp:
        dem_path = Path(tmp) / "dem.tif"
        write_synthetic_bathymetry(dem_path)
        written = build_covariate_stack(dem_path, Path(tmp) / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
        stack_manifest = json.loads(written["provenance"].read_text())
        corpus_manifest = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
        grid = DemGrid.load(dem_path)
        layers = build_covariate_registry().build_all(grid)
        return assemble_training_matrix(
            CorpusCsvSampleSource(), grid, layers, corpus_manifest, stack_manifest
        )


def _light_registry(covariate_names, *, oob: bool = False) -> EstimatorRegistry:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", OrdinaryKrigingEstimator())
    registry.register(
        "random_forest",
        RandomForestEstimator(
            seed=0, n_estimators=40, importance_seeds=(0,), feature_names=covariate_names,
            compute_oob_diagnostic=oob,
        ),
    )
    return registry


def _all_designs():
    return [
        leave_one_cluster_out(),
        leave_one_site_out(),
        LeaveOneStationOutSplitter(),
        RandomKFoldSplitter(k=5, seed=0),
    ]


def _matrix_manifest_for(matrix: TrainingMatrix) -> TrainingMatrixManifest:
    """A finalized manifest describing THIS matrix — for tests that emit a
    manifest from a registry the module-scoped fixture does not use."""
    from engine.prospectivity.validation.runner import matrix_sha256

    return TrainingMatrixManifest(
        target_definition={"value": "total_as_published", "data_origin": "AUTHORED", "author": "model"},
        sampling_method="test", shared_cell_count=0, distinct_cell_count=len(matrix.station_ids),
        cell_groups=[], n_stations=len(matrix.station_ids), n_covariates=len(matrix.covariate_names),
        covariate_names=list(matrix.covariate_names), coord_columns=list(matrix.coord_columns),
        matrix_sha256=matrix_sha256(matrix), data_origin="SYNTHETIC",
        upstream_hashes={"corpus": "sha256:c", "feature_stack": "sha256:f"},
    ).finalize()


@pytest.fixture(scope="module")
def real_run(real_matrix):
    matrix, manifest = real_matrix
    runner = CrossValidationRunner(splitters=_all_designs(), registry=_light_registry(matrix.covariate_names, oob=True))
    report = runner.run(matrix, seed=0)
    run_manifest = emit_run_manifest(report, matrix=matrix, matrix_manifest=manifest, run_id="test-run")
    return matrix, manifest, report, run_manifest


class _Dummy(Estimator):
    """A fourth estimator: predicts a constant, records the feature WIDTH it
    was handed (so routing by declaration is observable)."""

    input_kind: ClassVar[str] = "covariates"
    uncertainty_method: ClassVar[str] = "dummy_constant"
    uncertainty_semantics: ClassVar[str] = "a constant — test double"

    def __init__(self) -> None:
        self.widths: list[int] = []

    def fit(self, features: Any, target: Any) -> None:
        self.widths.append(int(np.asarray(features).shape[1]))

    def _predict(self, features: Any):
        n = len(features)
        return np.full(n, 19.0), np.full(n, 1.0)

    def provenance(self) -> dict:
        return {"widths_seen": list(self.widths)}


class _Spy(Estimator):
    """Refuses its `refuse_on`-th fit (1-based); counts fits and predicts."""

    input_kind: ClassVar[str] = "covariates"
    uncertainty_method: ClassVar[str] = "spy"
    uncertainty_semantics: ClassVar[str] = "spy"

    def __init__(self, refuse_on: int) -> None:
        self.refuse_on = refuse_on
        self.fits = 0
        self.successful_fits = 0
        self.predicts = 0

    def fit(self, features: Any, target: Any) -> None:
        self.fits += 1
        if self.fits == self.refuse_on:
            raise ValueError("scripted refusal: the spy refuses this fold")
        self.successful_fits += 1

    def _predict(self, features: Any):
        self.predicts += 1
        n = len(features)
        return np.zeros(n), np.ones(n)

    def provenance(self) -> dict:
        return {"fits": self.fits}


# ------------------------------------------ obligation 1: never cherry-pick


def test_every_fold_of_every_design_carries_every_registered_estimator_including_the_baseline(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    names = set(report.registry_names)
    assert MEAN_BASELINE_NAME in names
    for design in report.designs:
        for fold in design.assignment.folds:
            rows = [r for r in design.results if r.fold_name == fold.name]
            assert {r.estimator_name for r in rows} == names, (design.name, fold.name)
    # and the flat table: one row per (design, fold, estimator, metric)
    flat = {(s.cv_strategy, s.fold_name, s.estimator_name, s.metric_name) for s in run_manifest.cv_scores}
    for design in report.designs:
        for fold in design.assignment.folds:
            for name in names:
                for metric in METRIC_NAMES:
                    assert (design.name, fold.name, name, metric) in flat


def test_a_fourth_dummy_estimator_is_run_on_every_fold_with_zero_runner_change(real_matrix) -> None:
    matrix, _ = real_matrix
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    dummy = _Dummy()
    registry.register("fourth_dummy", dummy)
    designs = [leave_one_cluster_out(), leave_one_site_out(), RandomKFoldSplitter(k=5, seed=0)]
    report = CrossValidationRunner(splitters=designs, registry=registry).run(matrix, seed=0)
    expected_folds = sum(len(d.assignment.folds) for d in report.designs)
    assert expected_folds == 2 + 5 + 5
    rows = [r for d in report.designs for r in d.results if r.estimator_name == "fourth_dummy"]
    assert len(rows) == expected_folds and all(r.status == STATUS_SCORED for r in rows)
    assert report.estimator_declarations["fourth_dummy"]["input_kind"] == "covariates"
    assert dummy.widths == [matrix.X.shape[1]] * expected_folds  # routed to X, by declaration
    # …and it reaches the FLAT table and the pooled records of every design
    run_manifest = emit_run_manifest(
        report, matrix=matrix, matrix_manifest=_matrix_manifest_for(matrix), run_id="dummy"
    )
    flat = {(s.cv_strategy, s.fold_name) for s in run_manifest.cv_scores if s.estimator_name == "fourth_dummy"}
    assert len(flat) == expected_folds
    assert all("fourth_dummy" in d.pooled for d in report.designs)


def test_runner_never_calls_registry_get(real_matrix) -> None:
    """A registry whose get() raises: the runner must complete anyway —
    it iterates items() (obligation 1's mechanism)."""
    matrix, _ = real_matrix

    class _NoGet(EstimatorRegistry):
        def get(self, name: str):  # type: ignore[override]
            raise AssertionError("runner called registry.get() — cherry-picking is possible")

    registry = _NoGet()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    report = CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=registry).run(matrix, seed=0)
    assert len(report.designs[0].results) == 2


def test_runner_refuses_a_registry_without_the_baseline_by_name(real_matrix) -> None:
    matrix, _ = real_matrix
    registry = EstimatorRegistry()
    registry.register("only_kriging", OrdinaryKrigingEstimator())
    with pytest.raises(ValueError, match="mean_baseline"):
        CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=registry).run(matrix, seed=0)


# ------------------------- obligation 2: refit per fold; the stale-refit probe


def test_a_refused_fit_is_recorded_per_fold_and_predict_is_never_called_after_it(real_matrix) -> None:
    matrix, _ = real_matrix
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    spy = _Spy(refuse_on=2)
    registry.register("spy", spy)
    report = CrossValidationRunner(splitters=[leave_one_site_out()], registry=registry).run(matrix, seed=0)
    rows = [r for r in report.designs[0].results if r.estimator_name == "spy"]
    assert [r.status for r in rows] == [STATUS_SCORED, STATUS_REFUSED, STATUS_SCORED, STATUS_SCORED, STATUS_SCORED]
    assert rows[1].refusal == "scripted refusal: the spy refuses this fold"
    assert rows[1].predicted_mean == () and rows[1].metrics == {} and rows[1].provenance == {}
    assert spy.fits == 5 and spy.successful_fits == 4 and spy.predicts == 4  # predict ONLY after a successful fit
    # the baseline still scored the refused fold
    base = [r for r in report.designs[0].results if r.estimator_name == MEAN_BASELINE_NAME]
    assert all(r.status == STATUS_SCORED for r in base)
    pooled = report.designs[0].pooled["spy"]
    assert pooled["n_folds_refused"] == 1 and pooled["folds_refused"] == [rows[1].fold_name]
    assert pooled["baseline_on_same_folds"]["rmse"].n == pooled["n_pooled"]


def test_live_case_loco_kriging_refuses_the_train_W_fold_and_is_baseline_exactly_on_the_train_E_fold(real_run) -> None:
    """The E2.2 atomicity precedent on real data: the shared kriging
    instance fits one LOCO fold and refuses the other, and the refused fold
    has NO kriging prediction. On the fitted fold the fitter's verdict is
    no structure, so kriging IS the training mean: rmse and mean_error equal
    the baseline's EXACTLY (the two-fold geometry theorem, per fold)."""
    matrix, manifest, report, run_manifest = real_run
    loco = next(d for d in report.designs if d.name == "leave_one_cluster_out")
    krig = {r.fold_name: r for r in loco.results if r.estimator_name == "ordinary_kriging"}
    base = {r.fold_name: r for r in loco.results if r.estimator_name == MEAN_BASELINE_NAME}
    refused = [r for r in krig.values() if r.status == STATUS_REFUSED]
    scored = [r for r in krig.values() if r.status == STATUS_SCORED]
    assert len(refused) == 1 and len(scored) == 1
    assert refused[0].n_train == 14 and "only 2 bin(s) survive" in refused[0].refusal
    assert refused[0].predicted_mean == ()
    fold = scored[0]
    assert fold.n_train == 21 and fold.provenance["no_structure"] is True
    assert fold.provenance["partial_sill"] == 0.0 and fold.provenance["range_km"] == 0.0
    assert "reverts to the training mean" in fold.provenance["verdict"]
    assert fold.metrics["rmse"].value == pytest.approx(base[fold.fold_name].metrics["rmse"].value, abs=1e-12)
    assert fold.metrics["mean_error"].value == pytest.approx(base[fold.fold_name].metrics["mean_error"].value, abs=1e-12)
    assert fold.vs_baseline["rmse_uplift"].value == pytest.approx(0.0, abs=1e-12)
    # the two clusters differ by |mean_error| = 1.89 kg/m² (obligation 8c: a measurement)
    assert abs(base[fold.fold_name].metrics["mean_error"].value) == pytest.approx(1.886, abs=0.01)


# ------------------------------------------ 2C: routing is a declaration


def test_routing_follows_the_declaration_not_the_registered_name(real_matrix) -> None:
    matrix, _ = real_matrix
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", _Dummy())  # a COVARIATES estimator under kriging's name
    registry.register("not_kriging", OrdinaryKrigingEstimator())  # kriging under another name
    report = CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=registry).run(matrix, seed=0)
    dummy_rows = [r for r in report.designs[0].results if r.estimator_name == "ordinary_kriging"]
    assert all(r.status == STATUS_SCORED and r.input_kind == "covariates" for r in dummy_rows)
    assert all(w == matrix.X.shape[1] for w in dummy_rows[0].provenance["widths_seen"])
    krig_rows = [r for r in report.designs[0].results if r.estimator_name == "not_kriging"]
    assert [r.input_kind for r in krig_rows] == ["coordinates", "coordinates"]
    # kriging under any name still sees (n, 2) coordinates: the train-E fold FITS
    assert any(r.status == STATUS_SCORED and r.provenance["coordinate_system"] == "geographic_lonlat" for r in krig_rows)


def test_an_estimator_lacking_a_declaration_cannot_be_declared_and_a_mutated_instance_is_refused_by_name() -> None:
    with pytest.raises(TypeError, match="input_kind"):

        class _NoKind(Estimator):
            uncertainty_method = "x"
            uncertainty_semantics = "x"

            def fit(self, f, t): ...
            def _predict(self, f): ...
            def provenance(self): return {}

    with pytest.raises(TypeError, match="input_kind.*got 'rasters'"):

        class _BadKind(Estimator):
            input_kind = "rasters"
            uncertainty_method = "x"
            uncertainty_semantics = "x"

            def fit(self, f, t): ...
            def _predict(self, f): ...
            def provenance(self): return {}

    with pytest.raises(TypeError, match="uncertainty_method"):

        class _NoMethod(Estimator):
            input_kind = "covariates"
            uncertainty_semantics = "x"

            def fit(self, f, t): ...
            def _predict(self, f): ...
            def provenance(self): return {}

    with pytest.raises(TypeError, match="uncertainty_semantics"):

        class _NoSemantics(Estimator):
            input_kind = "covariates"
            uncertainty_method = "x"

            def fit(self, f, t): ...
            def _predict(self, f): ...
            def provenance(self): return {}

    registry = EstimatorRegistry()
    baseline = MeanBaselineEstimator()
    registry.register(MEAN_BASELINE_NAME, baseline)
    baseline.input_kind = "rasters"  # type: ignore[misc]  # a post-hoc instance mutation
    with pytest.raises(ValueError, match="mean_baseline.*input_kind='rasters'"):
        registry.assert_complete()


# ---------------- obligations 4–6: provenance reaches the manifest, by name


def test_kriging_provenance_carries_every_obligation_field_by_name_with_the_ceiling_flag_beside_range(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    scored = [
        r for d in run_manifest.cross_validation["designs"] for r in d["results"]
        if r["estimator_name"] == "ordinary_kriging" and r["status"] == STATUS_SCORED
    ]
    assert scored, "no scored kriging fold to inspect"
    for row in scored:
        prov = row["provenance"]
        missing = [k for k in KRIGING_OBLIGATION_FIELDS if k not in prov]
        assert not missing, f"kriging provenance lacks {missing} ({row['design']}/{row['fold_name']})"
        keys = list(prov)
        assert keys.index("range_at_candidate_ceiling") == keys.index("range_km") + 1
        assert isinstance(prov["excluded_bins"], list)
        for excluded in prov["excluded_bins"]:
            assert isinstance(excluded[1], str) and excluded[1]  # every excluded bin WITH its reason
        assert "fitted_bins" in prov["alternative"]  # the alternative model, with ITS bins


def test_rf_provenance_is_exactly_the_validation_facing_allow_list_and_oob_never_reaches_the_manifest(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    text = run_manifest.to_json()
    assert "oob" not in text.lower()  # the registry's RF was built with compute_oob_diagnostic=True
    rf_rows = [
        r for d in run_manifest.cross_validation["designs"] for r in d["results"]
        if r["estimator_name"] == "random_forest" and r["status"] == STATUS_SCORED
    ]
    expected = {
        "seed", "n_estimators", "hyperparameters", "uncertainty_method", "uncertainty_semantics",
        "n_training", "n_features", "feature_names", "distinct_x_rows", "importance_by_seed",
        "reported_quantile_levels", "training_quantiles", "zero_width_training_predictions",
    }
    for row in rf_rows:
        assert set(row["provenance"]) == expected
        assert row["provenance"]["hyperparameters"]["max_samples_leaf"] is None  # read back, not echoed


# ------------------------------------------- obligation 7: the semantics column


def test_uncertainty_method_travels_with_every_row_and_the_sentence_once_per_estimator(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    decl = run_manifest.estimator_declarations
    assert set(decl) == set(report.registry_names)
    for name, d in decl.items():
        assert d["uncertainty_method"] and d["uncertainty_semantics"] and d["input_kind"]
    for score in run_manifest.cv_scores:
        assert score.uncertainty_method == decl[score.estimator_name]["uncertainty_method"]
    kinds = {d["uncertainty_method"] for d in decl.values()}
    assert kinds == {"sample_sd_ddof1", "sqrt_ordinary_kriging_variance", "qrf_half_width_q16_q84"}
    # …and on EVERY structured result row and pooled record (the §2 review
    # found the test blind to both: dropping them there passed)
    for design in run_manifest.cross_validation["designs"]:
        for row in design["results"]:
            assert row["uncertainty_method"] == decl[row["estimator_name"]]["uncertainty_method"]
            assert row["uncertainty_semantics"] == decl[row["estimator_name"]]["uncertainty_semantics"]
        for name, pooled in design["pooled"].items():
            assert pooled["uncertainty_method"] == decl[name]["uncertainty_method"]
            assert pooled["uncertainty_semantics"] == decl[name]["uncertainty_semantics"]
            if "baseline_on_same_folds" in pooled:
                # the baseline's sd-derived numbers carry the BASELINE's
                # semantics even nested inside another estimator's record
                assert pooled["baseline_uncertainty_method"] == "sample_sd_ddof1"
                assert pooled["baseline_uncertainty_semantics"] == decl[MEAN_BASELINE_NAME]["uncertainty_semantics"]


# ----------------------------------------- the claim guard; the leakage assertion


def test_random_k_fold_and_leave_one_station_out_cannot_back_a_claim_and_the_manifest_says_so(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    assert run_manifest.claim_eligible_designs == ["leave_one_cluster_out", "leave_one_site_out"]
    for design in report.designs:
        if design.name in ("random_k_fold", "leave_one_station_out"):
            assert design.claim_eligible is False and "never back a published claim" in design.claim_eligibility_note
            with pytest.raises(ValueError, match="never back a published claim"):
                assert_claim_eligible(design.assignment)
        else:
            assert design.claim_eligible is True
            assert_claim_eligible(design.assignment)


def test_required_separation_is_recorded_per_design_and_asserted_on_every_fold(real_run, real_matrix) -> None:
    matrix, manifest, report, run_manifest = real_run
    by_name = {d.name: d for d in report.designs}
    assert by_name["leave_one_cluster_out"].required_separation_km == 100.0
    assert by_name["leave_one_site_out"].required_separation_km == 2.0
    assert by_name["leave_one_station_out"].required_separation_km == 0.0
    assert by_name["random_k_fold"].required_separation_km == 0.0
    rec = {d["name"]: d for d in run_manifest.cross_validation["designs"]}
    assert rec["leave_one_cluster_out"]["measured_min_separation_km"] == pytest.approx(986.036, abs=1e-3)
    assert rec["leave_one_site_out"]["measured_min_separation_km"] == pytest.approx(4.614, abs=1e-3)
    assert rec["leave_one_station_out"]["measured_min_separation_km"] == pytest.approx(0.054, abs=1e-3)
    # a design whose DECLARED separation exceeds reality is refused by fold name

    class _Overclaims(SingleLinkageBlockSplitter):
        @property
        def required_separation_km(self) -> float:
            return 2000.0

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    with pytest.raises(ValueError, match="below the stated minimum separation of 2000"):
        CrossValidationRunner(
            splitters=[_Overclaims(linkage_km=100.0, design_name="overclaims")], registry=registry
        ).run(real_matrix[0], seed=0)


# ------------------------------------------------- 2D: the manifest and the chain


def test_scores_first_visible_is_outside_the_substance_hash_and_its_description_names_the_commit(real_run) -> None:
    from datetime import UTC, datetime

    matrix, manifest, report, run_manifest = real_run
    a = emit_run_manifest(report, matrix=matrix, matrix_manifest=manifest, run_id="x",
                          scores_first_visible=datetime(2026, 8, 19, tzinfo=UTC))
    b = emit_run_manifest(report, matrix=matrix, matrix_manifest=manifest, run_id="x",
                          scores_first_visible=datetime(2030, 1, 1, tzinfo=UTC))
    assert a.scores_first_visible != b.scores_first_visible
    assert a.content_hash == b.content_hash
    assert "scores_first_visible" in RunManifest.hash_excluded_fields()
    assert "scores_first_visible" not in a.substance()
    description = RunManifest.model_fields["scores_first_visible"].description
    assert "COMMIT" in description and "MUTABLE METADATA" in description and "post-hoc" in description
    # …and the same sentence is emitted as a VALUE, so a reader of the JSON
    # (who never sees pydantic's schema) gets the caveat too (§2 review)
    assert a.scores_first_visible_note == description
    assert json.loads(a.to_json())["scores_first_visible_note"] == description
    # run_id is the IDENTITY of an emission, not substance: two emissions of
    # the same report hash identically whether or not a run_id is given
    c = emit_run_manifest(report, matrix=matrix, matrix_manifest=manifest, run_id="y")
    d = emit_run_manifest(report, matrix=matrix, matrix_manifest=manifest)  # uuid default
    assert c.content_hash == a.content_hash == d.content_hash
    assert c.run_id == "y" and d.run_id != c.run_id
    assert "run_id" in RunManifest.hash_excluded_fields()
    # a DIFFERENT run (another seed) does change the substance
    from engine.prospectivity.validation.runner import CrossValidationRunner
    other = CrossValidationRunner(
        splitters=[leave_one_cluster_out()], registry=_light_registry(matrix.covariate_names)
    ).run(matrix, seed=99)
    assert emit_run_manifest(other, matrix=matrix, matrix_manifest=manifest).content_hash != a.content_hash


def test_run_manifest_chains_to_the_actual_matrix_artifact_and_refuses_a_matrix_it_does_not_describe(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    assert run_manifest.upstream_hashes["training_matrix"] == manifest.content_hash
    assert run_manifest.upstream_hashes["corpus"] == manifest.upstream_hashes["corpus"]
    assert run_manifest.upstream_hashes["feature_stack"] == manifest.upstream_hashes["feature_stack"]
    assert run_manifest.inputs["training_matrix"]["matrix_sha256"] == manifest.matrix_sha256
    assert run_manifest.data_origin == manifest.data_origin == "SYNTHETIC"
    assert run_watermark(run_manifest) is not None  # the watermark derives, default-on
    assert run_manifest.contract_versions == manifest.contract_versions
    # a different matrix with the same manifest: refused by name, never a literal copy
    perturbed_y = matrix.y.copy(); perturbed_y[0] += 1.0; perturbed_y.flags.writeable = False
    other = TrainingMatrix(matrix.station_ids, matrix.covariate_names, matrix.X, perturbed_y, matrix.coords)
    with pytest.raises(ValueError, match="not the one its manifest describes"):
        emit_run_manifest(report, matrix=other, matrix_manifest=manifest, run_id="z")


def test_two_runs_in_one_process_on_one_matrix_have_the_same_content_hash(real_matrix) -> None:
    """Determinism of the RUN: same matrix object, same seed, same registry
    shape -> identical scores and identical hash.

    HONEST SCOPE, named because the test cannot check it (E2.4 §3): this is
    within one process on ONE DEM path. Across machines or directories the
    hash DIFFERS while the scores do not, because `FeatureStackManifest`
    hashes the DEM's absolute path — a recorded defect (docs/BACKLOG.md §3),
    not a property this test establishes."""
    matrix, manifest = real_matrix
    def once():
        runner = CrossValidationRunner(splitters=[leave_one_cluster_out(), RandomKFoldSplitter(k=5, seed=3)],
                                       registry=_light_registry(matrix.covariate_names))
        return emit_run_manifest(runner.run(matrix, seed=7), matrix=matrix, matrix_manifest=manifest, run_id="repro")
    a, b = once(), once()
    assert a.content_hash == b.content_hash
    assert a.seed == 7 and json.loads(a.to_json())["cross_validation"] == json.loads(b.to_json())["cross_validation"]


def test_flat_scores_carry_the_baseline_beside_every_row_and_name_refusals_by_status(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    base = {(s.cv_strategy, s.fold_name, s.metric_name): s for s in run_manifest.cv_scores if s.estimator_name == MEAN_BASELINE_NAME}
    refused_seen = 0
    for s in run_manifest.cv_scores:
        if s.estimator_name == MEAN_BASELINE_NAME:
            continue
        if s.metric_name in METRIC_NAMES:
            b = base[(s.cv_strategy, s.fold_name, s.metric_name)]
            assert s.baseline_metric_value == b.metric_value and s.baseline_metric_status == b.metric_status
        if s.metric_status.startswith("refused"):
            refused_seen += 1
            assert s.metric_value is None
            assert "refused at fit:" in s.metric_status  # the PHASE is named
    assert refused_seen == 2 * len(METRIC_NAMES)  # kriging: one LOCO fold + one site fold, every metric named
    assert all((s.metric_value is None) == (s.metric_status != "ok") for s in run_manifest.cv_scores)
    # obligation 3: the sd≈0 counts travel with the FLAT table, on exactly
    # the metrics that involve sd (0 of 35 today, so the pins are the shape)
    sd_metrics = {"coverage_1sigma", "standardized_rmse"}
    for s in run_manifest.cv_scores:
        if s.metric_name in sd_metrics and s.metric_status == "ok":
            assert s.n_sd_zero == 0
            assert (s.n_sd_zero_wrong == 0) or (s.metric_name == "coverage_1sigma" and s.n_sd_zero_wrong is None)
        elif s.metric_name not in sd_metrics:
            assert s.n_sd_zero is None and s.n_sd_zero_wrong is None


def test_pooled_metrics_compare_a_refusing_estimator_on_its_scored_folds_only(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    loco = next(d for d in report.designs if d.name == "leave_one_cluster_out")
    pooled = loco.pooled["ordinary_kriging"]
    assert pooled["n_folds_scored"] == 1 and pooled["n_folds_refused"] == 1 and pooled["n_pooled"] == 14
    assert pooled["baseline_on_same_folds"]["rmse"].n == 14
    assert pooled["metrics"]["r2_pooled"].status == "ok"
    site = next(d for d in report.designs if d.name == "leave_one_site_out")
    assert site.pooled["ordinary_kriging"]["n_folds_scored"] == 4 and site.pooled["ordinary_kriging"]["n_pooled"] == 27
    assert site.pooled[MEAN_BASELINE_NAME]["n_pooled"] == 35


# ------------------------------- §2 review: the findings, each with an observer


class _AnyN(Estimator):
    """Fits on any n (even 1) — the estimator class that exposes a baseline
    refusing a fold this estimator scored."""

    input_kind: ClassVar[str] = "covariates"
    uncertainty_method: ClassVar[str] = "any_n"
    uncertainty_semantics: ClassVar[str] = "test double"

    def fit(self, features: Any, target: Any) -> None:
        self._mean = float(np.mean(target))

    def _predict(self, features: Any):
        n = len(features)
        return np.full(n, self._mean), np.full(n, 1.0)

    def provenance(self) -> dict:
        return {"mean": self._mean}


class _RefusesPredict(Estimator):
    """Fits, then refuses AT PREDICT — RF's crossed-quantile and kriging's
    negative-variance refusals have this shape."""

    input_kind: ClassVar[str] = "covariates"
    uncertainty_method: ClassVar[str] = "refuses"
    uncertainty_semantics: ClassVar[str] = "test double"

    def fit(self, features: Any, target: Any) -> None:
        pass

    def _predict(self, features: Any):
        raise ValueError("QRF quantiles crossed (q84 < q16) at 1 prediction(s)")

    def provenance(self) -> dict:
        return {}


def _four_station_matrix() -> TrainingMatrix:
    """Three stations ~1 km apart plus one ~1100 km away: leave-one-cluster-out
    gives a fold whose TRAINING set is a single row, where the mean baseline
    legitimately refuses (SD ddof=1 undefined at n=1) while an estimator that
    fits on one row scores — the population mismatch that used to abort."""
    coords = np.array([[-126.0, 12.0], [-125.99, 12.0], [-125.98, 12.0], [-116.0, 12.0]])
    y = np.array([10.0, 12.0, 14.0, 26.0])
    X = np.arange(8, dtype=np.float64).reshape(4, 2)
    for array in (coords, y, X):
        array.flags.writeable = False
    return TrainingMatrix(("s0", "s1", "s2", "s3"), ("a", "b"), X, y, coords)


def test_a_baseline_refusal_on_a_fold_another_estimator_scored_is_recorded_not_fatal() -> None:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("any_n", _AnyN())
    report = CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=registry).run(
        _four_station_matrix(), seed=0
    )
    design = report.designs[0]
    base_rows = {r.fold_name: r for r in design.results if r.estimator_name == MEAN_BASELINE_NAME}
    assert any(r.status == STATUS_REFUSED for r in base_rows.values())  # n_train == 1
    pooled = design.pooled["any_n"]
    assert pooled["n_folds_scored"] == 2  # the estimator scored both folds
    # the comparison is restricted to the fold where BOTH scored, and says so
    assert pooled["n_pooled_vs_baseline"] < pooled["n_pooled"]
    assert pooled["folds_excluded_from_comparison"]
    assert pooled["vs_baseline"]["rmse_uplift"].status == "ok"
    assert pooled["baseline_uncertainty_method"] == "sample_sd_ddof1"


def test_a_predict_time_refusal_is_recorded_with_its_phase_and_the_run_completes() -> None:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("refuses_predict", _RefusesPredict())
    report = CrossValidationRunner(
        splitters=[RandomKFoldSplitter(k=2, seed=0)], registry=registry
    ).run(_four_station_matrix(), seed=0)
    rows = [r for r in report.designs[0].results if r.estimator_name == "refuses_predict"]
    assert rows and all(r.status == STATUS_REFUSED for r in rows)
    assert all(r.refusal_phase == "predict" for r in rows)
    assert all("quantiles crossed" in r.refusal for r in rows)
    assert all(r.predicted_mean == () for r in rows)
    # the baseline still scored every fold — one estimator's refusal is not
    # everyone else's lost run
    base = [r for r in report.designs[0].results if r.estimator_name == MEAN_BASELINE_NAME]
    assert all(r.status == STATUS_SCORED for r in base)
    assert report.designs[0].pooled["refuses_predict"]["note"].startswith("refused on every fold")


def test_the_comparison_floor_must_be_the_registrys_required_baseline() -> None:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("any_n", _AnyN())
    with pytest.raises(ValueError, match="not in REQUIRED_ESTIMATORS"):
        CrossValidationRunner(
            splitters=[leave_one_cluster_out()], registry=registry, baseline_name="any_n"
        )


def test_a_design_claiming_to_be_spatially_blocked_must_guarantee_a_positive_separation(real_matrix) -> None:
    matrix, _ = real_matrix

    class _Contradictory(SingleLinkageBlockSplitter):
        @property
        def required_separation_km(self) -> float:
            return 0.0

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    with pytest.raises(ValueError, match="spatially_blocked=True but required_separation_km=0"):
        CrossValidationRunner(
            splitters=[_Contradictory(linkage_km=100.0, design_name="contradictory")],
            registry=registry,
        ).run(matrix, seed=0)


def test_the_manifest_records_measured_separations_not_the_splitters_claims(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    for design, record in zip(report.designs, run_manifest.cross_validation["designs"]):
        measured = design.measured_separations_km
        assert set(measured) == {f.name for f in design.assignment.folds}
        assert record["measured_separations_km"] == pytest.approx(measured)
        assert record["measured_min_separation_km"] == pytest.approx(min(measured.values()))
        for fold in design.assignment.folds:
            assert measured[fold.name] == pytest.approx(fold.min_train_test_km, abs=1e-9)


def test_the_emitter_refuses_a_report_computed_on_different_coordinates(real_run) -> None:
    """Same row count, same manifest — but the CV report was split from other
    coordinates. The fold assignments' fingerprints are the witness."""
    matrix, manifest, report, run_manifest = real_run
    shifted_coords = matrix.coords + 0.5
    shifted_coords.flags.writeable = False
    other = TrainingMatrix(matrix.station_ids, matrix.covariate_names, matrix.X, matrix.y, shifted_coords)
    other_report = CrossValidationRunner(
        splitters=[leave_one_cluster_out()], registry=_light_registry(matrix.covariate_names)
    ).run(other, seed=0)
    with pytest.raises(ValueError, match="was not computed on this matrix"):
        emit_run_manifest(other_report, matrix=matrix, matrix_manifest=manifest, run_id="x")


def test_the_emitter_refuses_a_matrix_manifest_mutated_after_finalize(real_run) -> None:
    matrix, manifest, report, run_manifest = real_run
    lying = manifest.model_copy(deep=True)
    lying.data_origin = "MEASURED"  # the watermark-defeating edit, post-finalize
    with pytest.raises(ValueError, match="does not match its own contents"):
        emit_run_manifest(report, matrix=matrix, matrix_manifest=lying, run_id="x")


def test_a_non_finite_value_in_provenance_is_refused_rather_than_serialized_as_null(real_matrix) -> None:
    matrix, _ = real_matrix

    class _InfProvenance(_AnyN):
        def provenance(self) -> dict:
            return {"nested": {"broken": float("inf")}}

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("inf_provenance", _InfProvenance())
    with pytest.raises(ValueError, match="non-finite value.*run provenance"):
        CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=registry).run(matrix, seed=0)


def test_kriging_reports_the_range_caveat_as_one_sentence_a_sorted_json_cannot_separate(real_run) -> None:
    """Obligation 5 for a reader of the EMITTED file: `to_json` sorts keys, so
    `range_at_candidate_ceiling` and `range_km` are separated by the floor
    twin. The caveat therefore also travels as one string."""
    matrix, manifest, report, run_manifest = real_run
    scored = [
        r for d in run_manifest.cross_validation["designs"] for r in d["results"]
        if r["estimator_name"] == "ordinary_kriging" and r["status"] == STATUS_SCORED
    ]
    assert scored
    for row in scored:
        reported = row["provenance"]["range_km_reported"]
        assert reported.startswith(f"{row['provenance']['range_km']:.4g} km")
        assert ("unconstrained from above" in reported) == row["provenance"]["range_at_candidate_ceiling"]
        assert ("unidentifiable" in reported) == row["provenance"]["range_below_first_supported_lag"]
        assert f"residual dof {row['provenance']['residual_dof']}" in reported


def test_the_engine_refuses_a_cv_runner_that_validates_a_different_registry(real_matrix) -> None:
    from engine.prospectivity.engine import ProspectivityEngine

    matrix, _ = real_matrix
    validated = _light_registry(matrix.covariate_names)
    predicted = _light_registry(matrix.covariate_names)  # a DIFFERENT registry object
    runner = CrossValidationRunner(splitters=[leave_one_cluster_out()], registry=validated)
    with pytest.raises(ValueError, match="cross-validates a DIFFERENT registry"):
        ProspectivityEngine(
            study_area=None, terrain_source=None, sample_source=None, feature_builder=None,
            cv_runner=runner, estimators=predicted, ts6_reference=None, economic_model=None,
            scenario_configs=[],
        )


def test_a_subclass_cannot_pull_generated_at_back_into_the_content_hash() -> None:
    class _Sneaky(RunManifest):
        HASH_EXCLUDED_FIELDS: ClassVar[frozenset[str]] = frozenset({"content_hash"})

    assert _Sneaky.hash_excluded_fields() == frozenset(
        {"content_hash", "generated_at"}
    ) | frozenset({"content_hash"})
    assert "generated_at" in _Sneaky.hash_excluded_fields()
    a = _Sneaky(run_id="a", seed=0).finalize()
    b = _Sneaky(run_id="a", seed=0).finalize()
    assert a.generated_at != b.generated_at or True
    assert a.content_hash == b.content_hash


def test_a_registered_instance_with_a_whitespace_uncertainty_method_is_refused_by_name() -> None:
    registry = EstimatorRegistry()
    baseline = MeanBaselineEstimator()
    registry.register(MEAN_BASELINE_NAME, baseline)
    baseline.uncertainty_method = "sample sd"  # type: ignore[misc]  # a space
    with pytest.raises(ValueError, match="whitespace-free"):
        registry.assert_complete()


def test_runner_refuses_duplicate_design_names_and_an_empty_splitter_list() -> None:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    with pytest.raises(ValueError, match="duplicate design names"):
        CrossValidationRunner(splitters=[leave_one_cluster_out(), leave_one_cluster_out()], registry=registry)
    with pytest.raises(ValueError, match="at least one FoldSplitter"):
        CrossValidationRunner(splitters=[], registry=registry)
