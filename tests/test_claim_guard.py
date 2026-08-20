"""E2.5 — the refuse-to-validate guard.

One test per precondition (each asserting THE SPECIFIC refusal, not a generic
one), the positive case, the watermark path, and the exhaustiveness check in
both directions.

THE POSITIVE FIXTURE'S SEPARATION (CLAUDE.md rule 4). `_eligible_run()` builds
a manifest that satisfies ALL SIX preconditions, and it is the test that keeps
this whole file honest: without it, every other test here would pass against a
guard that returned "refused" unconditionally — the suite would be green and
the guard would discriminate nothing. Each per-precondition test therefore
BREAKS EXACTLY ONE input of that same fixture, so the difference between pass
and fail is the one fact under test and nothing else. The neighbouring claim it
separates: "the guard refuses correctly" from "the guard refuses always".

WHY THE FIXTURE IS HAND-BUILT rather than a real run: no real run can satisfy
precondition 6 today (Contract 8 has no acceptance_thresholds slot — that
absence IS E2.5's headline result), so the positive case must supply a contract
through the loader's testability seam. The real-run behaviour is pinned
separately by `test_the_committed_e2_4_run_is_refused_...`, which asserts the
honest refusal on the actual committed artifact.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.validation.claim import (
    ClaimRefused,
    Precondition,
    _CHECKERS,
    assert_preconditions_exhaustive,
    evaluate_claim,
    require_validated_claim,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORES_VISIBLE = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)

# A Contract 8 mapping whose acceptance threshold is populated, classified
# LITERATURE (not AUTHORED), and dated BEFORE the scores existed.
PRE_REGISTERED_CONTRACT = {
    "acceptance_thresholds": {
        "value": "spatial_cv_rmse_uplift_kg_m2 >= 0.5",
        "data_origin": "LITERATURE",
        "citation": "ISA Technical Study No. 6 (2010), Table 4-2, p. 61",
        "declared_at": "2026-01-01T00:00:00+00:00",
        "set_after_scores": False,
    }
}


def _stack(resolution=(0.1, 0.1), dem_hash="sha256:dem", n_layers=8) -> dict:
    return {
        "layers": [
            {"name": f"layer_{i}", "dem": {"resolution_deg": list(resolution), "content_hash": dem_hash}}
            for i in range(n_layers)
        ]
    }


def _fold(name: str, estimators=("mean_baseline", "ordinary_kriging")) -> tuple[dict, list[dict]]:
    fold = {"name": name, "train_indices": [0, 1], "test_indices": [2, 3],
            "n_train": 2, "n_test": 2, "min_train_test_km": 5.0}
    rows = [
        {
            "design": "leave_one_site_out", "fold_name": name, "estimator_name": est,
            "status": "scored", "refusal": None, "refusal_phase": None,
            "n_train": 2, "n_test": 2, "min_train_test_km": 5.0,
            "input_kind": "covariates", "uncertainty_method": "m", "uncertainty_semantics": "s",
            "test_indices": [2, 3], "observed": [10.0, 12.0],
            "predicted_mean": [10.5, 11.5], "predicted_sd": [1.0, 1.0],
            "metrics": {}, "vs_baseline": {}, "provenance": {},
        }
        for est in estimators
    ]
    return fold, rows


def _eligible_run(*, data_origin: str = "MEASURED") -> RunManifest:
    """A manifest satisfying ALL SIX preconditions. See the module docstring
    for what this fixture separates."""
    folds, results = [], []
    for name in ("fold_a", "fold_b"):
        fold, rows = _fold(name)
        folds.append(fold)
        results.extend(rows)
    return RunManifest(
        run_id="eligible", seed=0,
        scores_first_visible=SCORES_VISIBLE,
        data_origin=data_origin,
        upstream_hashes={"corpus": "sha256:c", "feature_stack": "sha256:f", "training_matrix": "sha256:m"},
        claim_eligible_designs=["leave_one_site_out"],
        cross_validation={
            "designs": [{
                "name": "leave_one_site_out", "purpose": "test", "spatially_blocked": True,
                "claim_eligible": True, "claim_eligibility_note": "", "required_separation_km": 2.0,
                "measured_min_separation_km": 5.0, "measured_separations_km": {"fold_a": 5.0, "fold_b": 5.0},
                "assignment": {"folds": folds}, "results": results, "pooled": {},
            }],
            "n_rows": 4,
        },
    ).finalize()


def _evaluate(manifest, *, stack=None, contract=PRE_REGISTERED_CONTRACT, design="leave_one_site_out"):
    return evaluate_claim(manifest, design=design, feature_stack_manifest=stack or _stack(), contract=contract)


# ------------------------------------------------- THE POSITIVE CASE (first)


def test_a_run_satisfying_all_six_preconditions_is_eligible_and_scientific() -> None:
    """Without this, every refusal test below would pass against a guard that
    refused unconditionally."""
    verdict = require_validated_claim(
        _eligible_run(), design="leave_one_site_out",
        feature_stack_manifest=_stack(), contract=PRE_REGISTERED_CONTRACT,
    )
    assert verdict.eligible is True
    assert [r.precondition for r in verdict.results] == list(Precondition)
    assert all(r.passed for r in verdict.results)
    assert verdict.watermark is None and verdict.is_scientific is True
    assert all(r.detail for r in verdict.results)  # a passing precondition reports WHY


# --------------------------------------------- ONE TEST PER PRECONDITION (6)


def test_precondition_1_refuses_a_design_whose_record_declares_it_not_spatially_blocked() -> None:
    manifest = _eligible_run()
    manifest.cross_validation["designs"][0]["spatially_blocked"] = False
    verdict = _evaluate(manifest)
    failed = {r.precondition for r in verdict.failures}
    assert failed == {Precondition.SPATIALLY_BLOCKED_CV}
    (row,) = [r for r in verdict.failures]
    assert "declares spatially_blocked=False" in row.detail
    assert "reads the RECORDED DECLARATION, never the design's name" in row.detail


def test_precondition_2_refuses_when_the_baseline_is_missing_from_one_fold() -> None:
    manifest = _eligible_run()
    design = manifest.cross_validation["designs"][0]
    design["results"] = [r for r in design["results"]
                         if not (r["fold_name"] == "fold_b" and r["estimator_name"] == "mean_baseline")]
    verdict = _evaluate(manifest)
    assert {r.precondition for r in verdict.failures} == {Precondition.BASELINE_IN_EVERY_FOLD}
    detail = verdict.failures[0].detail
    assert "did not run in every fold" in detail and "fold_b" in detail


def test_precondition_3_refuses_an_unpaired_or_non_finite_uncertainty() -> None:
    short = _eligible_run()
    short.cross_validation["designs"][0]["results"][0]["predicted_sd"] = [1.0]
    verdict = _evaluate(short)
    assert {r.precondition for r in verdict.failures} == {Precondition.PAIRED_UNCERTAINTY}
    assert "carries ITS OWN paired uncertainty" in verdict.failures[0].detail

    nan_sd = _eligible_run()
    nan_sd.cross_validation["designs"][0]["results"][0]["predicted_sd"] = [1.0, float("nan")]
    verdict = _evaluate(nan_sd)
    assert {r.precondition for r in verdict.failures} == {Precondition.PAIRED_UNCERTAINTY}
    assert "absent uncertainty wearing a float dtype" in verdict.failures[0].detail


def test_precondition_4_refuses_feature_layers_that_do_not_share_one_dem() -> None:
    mixed = _stack()
    mixed["layers"][3]["dem"]["resolution_deg"] = [0.01, 0.01]  # a second resolution
    verdict = _evaluate(_eligible_run(), stack=mixed)
    assert {r.precondition for r in verdict.failures} == {Precondition.SINGLE_DEM_RESOLUTION}
    assert "do not share one DEM" in verdict.failures[0].detail

    same_res_other_dem = _stack()
    same_res_other_dem["layers"][3]["dem"]["content_hash"] = "sha256:a-different-seafloor"
    verdict = _evaluate(_eligible_run(), stack=same_res_other_dem)
    assert {r.precondition for r in verdict.failures} == {Precondition.SINGLE_DEM_RESOLUTION}


def test_precondition_5_refuses_a_run_whose_provenance_omits_an_upstream_hash() -> None:
    manifest = _eligible_run()
    manifest.upstream_hashes = {"corpus": "sha256:c", "training_matrix": "sha256:m"}
    verdict = _evaluate(manifest)
    assert {r.precondition for r in verdict.failures} == {Precondition.PROVENANCE_CHAIN}
    # the MISSING-key branch's own message, not merely "feature_stack appears
    # somewhere": the two branches of this precondition (absent vs not-a-hash)
    # must be separately observable, or removing one is masked by the other
    assert "does not record upstream hash(es)" in verdict.failures[0].detail
    assert "feature_stack" in verdict.failures[0].detail
    assert "a name is not an identity" not in verdict.failures[0].detail

    not_a_hash = _eligible_run()
    not_a_hash.upstream_hashes = {"corpus": "the corpus", "feature_stack": "sha256:f",
                                  "training_matrix": "sha256:m"}
    verdict = _evaluate(not_a_hash)
    assert {r.precondition for r in verdict.failures} == {Precondition.PROVENANCE_CHAIN}, \
        "a non-sha256 upstream reference must be refused"
    assert "a name is not an identity" in verdict.failures[0].detail


def test_precondition_6_refuses_an_absent_null_authored_or_post_dated_threshold() -> None:
    """All four ways a gate fails to be pre-registered, each named.

    THE AUTHORED CASE CHANGED ROUTE AT C8.1, not verdict: the loader now
    rejects an AUTHORED threshold OUTRIGHT, so this function never sees one
    and reports the loader's refusal instead of testing the origin itself.
    The assertions below therefore check the reason SURVIVES the hand-off —
    the failure a bare `precondition in failures` check would miss.

    SOLE OBSERVER for the HAND-OFF (E2.0-1b convention, measured at C8.1):
    drop `{unusable}` from the guard's refusal message and this is the only
    test in the suite that fails. Everything else still sees precondition 6
    refuse — the SET is unchanged — while the refusal stops saying WHY. That
    is the whole risk of moving a rule into the loader, and this test is what
    stands between the move and a silent loss of the reason."""
    absent = _evaluate(_eligible_run(), contract={})
    assert {r.precondition for r in absent.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}
    assert "no admissible pre-registered gate existed" in absent.failures[0].detail
    assert "no acceptance_thresholds field" in absent.failures[0].detail

    null = _evaluate(_eligible_run(), contract={
        "acceptance_thresholds": {"value": None, "data_origin": "LITERATURE"}})
    assert {r.precondition for r in null.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}
    assert "explicitly NULL" in null.failures[0].detail

    authored = _evaluate(_eligible_run(), contract={
        "acceptance_thresholds": {"value": "uplift >= 0.5", "data_origin": "AUTHORED", "author": "model"}})
    assert {r.precondition for r in authored.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}, \
        "an AUTHORED threshold must be refused — a number someone typed is not a gate"
    assert "declared AUTHORED" in authored.failures[0].detail
    assert "inventing the standard its own work is measured against" in authored.failures[0].detail

    unclassified = _evaluate(_eligible_run(), contract={
        "acceptance_thresholds": {"value": "uplift >= 0.5"}})
    assert {r.precondition for r in unclassified.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}
    assert "with no data_origin" in unclassified.failures[0].detail

    post_hoc = _evaluate(_eligible_run(), contract={
        "acceptance_thresholds": {"value": "uplift >= 0.5", "data_origin": "LITERATURE",
                                  "declared_at": "2030-01-01T00:00:00+00:00"}})
    assert {r.precondition for r in post_hoc.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}, \
        "a threshold dated after the scores must be refused as post-hoc"
    detail = post_hoc.failures[0].detail
    assert "POST-DATES scores_first_visible" in detail
    # the honesty limit is stated AT the comparison, not only in a doc
    assert "mutable metadata" in detail and "COMMIT" in detail

    flagged = _evaluate(_eligible_run(), contract={
        "acceptance_thresholds": {"value": "uplift >= 0.5", "data_origin": "LITERATURE",
                                  "set_after_scores": True}})
    assert {r.precondition for r in flagged.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}
    assert "set_after_scores: true" in flagged.failures[0].detail


# ----------------------------------------------------- THE WATERMARK PATH


def test_a_synthetic_origin_run_that_satisfies_all_six_is_eligible_AND_watermarked_not_refused() -> None:
    """§1's load-bearing distinction, tested rather than described: building on
    fixtures is legitimate, publishing from them is not."""
    verdict = require_validated_claim(
        _eligible_run(data_origin="SYNTHETIC"), design="leave_one_site_out",
        feature_stack_manifest=_stack(), contract=PRE_REGISTERED_CONTRACT,
    )
    assert [r.precondition for r in verdict.failures] == [], \
        "a watermark must never gate eligibility — it is not a precondition"
    assert verdict.eligible is True          # NOT refused
    assert verdict.watermark is not None     # but not scientific either
    assert "non-scientific" in verdict.watermark
    assert verdict.is_scientific is False
    assert any("WATERMARKED, NOT REFUSED" in note for note in verdict.notes)
    # and the watermark is DERIVED from the origin, not a flag: change only the
    # origin and the watermark follows
    assert require_validated_claim(
        _eligible_run(data_origin="MEASURED"), design="leave_one_site_out",
        feature_stack_manifest=_stack(), contract=PRE_REGISTERED_CONTRACT,
    ).watermark is None


# --------------------------------------------------- THE EXHAUSTIVENESS CHECK


def test_a_declared_precondition_without_a_guard_fails_by_name() -> None:
    class _WithNewRule(Precondition.__class__):  # a stand-in enum, one member richer
        pass

    from enum import Enum

    Extended = Enum("Extended", {p.name: p.value for p in Precondition} | {"NEW_RULE": "a_new_rule"})
    with pytest.raises(ValueError, match="a_new_rule.*DECLARED but have no guard"):
        assert_preconditions_exhaustive(Extended, {p: _CHECKERS[Precondition[p.name]] for p in Extended
                                                   if p.name != "NEW_RULE"})


def test_a_guard_without_a_declared_precondition_fails_by_name() -> None:
    """The direction usually missed: a refusal nobody reading the enum can
    discover, report or test."""
    from enum import Enum

    Extra = Enum("Extra", {"UNDECLARED_GUARD": "an_undeclared_guard"})
    checkers = dict(_CHECKERS)
    checkers[Extra.UNDECLARED_GUARD] = lambda inputs: "never reported"
    with pytest.raises(ValueError, match="an_undeclared_guard.*NOT declared in the Precondition enum"):
        assert_preconditions_exhaustive(Precondition, checkers)


def test_the_shipped_precondition_set_and_guard_set_agree() -> None:
    assert_preconditions_exhaustive()  # the real pair; also asserted at import
    assert set(_CHECKERS) == set(Precondition)
    assert len(Precondition) == 6


# --------------------------------------------------- THE REAL, COMMITTED RUN


def test_the_committed_e2_4_run_is_refused_for_exactly_the_honest_reasons() -> None:
    """E2.5's headline result, pinned against the artifact a reader can open:
    preconditions 1–5 hold on the claim-eligible design and 6 does not,
    because no acceptance gate existed when these scores were computed."""
    manifest = RunManifest(**json.loads((REPO_ROOT / "data" / "runs" / "e2.4" / "run_manifest.json").read_text()))
    stack = _stack(dem_hash="sha256:whatever")  # the real stack is not committed; §4 records why
    verdict = evaluate_claim(manifest, design="leave_one_site_out", feature_stack_manifest=stack)

    passed = {r.precondition for r in verdict.results if r.passed}
    assert passed == set(Precondition) - {Precondition.PRE_REGISTERED_THRESHOLD}
    assert {r.precondition for r in verdict.failures} == {Precondition.PRE_REGISTERED_THRESHOLD}
    # The ROUTE changed at C8.1 and the VERDICT did not: before the slot
    # existed this refused because the FIELD was absent; it now refuses
    # because the field is explicitly NULL. Both assertions above — the
    # passing set and the failing set — are byte-identical across that
    # change, which is the property C8.1 had to preserve.
    assert "explicitly NULL" in verdict.failures[0].detail
    assert "no gate existed when these scores were computed" in verdict.failures[0].detail
    assert verdict.eligible is False
    assert verdict.watermark is not None and verdict.is_scientific is False

    # the two designs that may never back a claim fail precondition 1 as well,
    # by their RECORDED declaration
    for design in ("leave_one_station_out", "random_k_fold"):
        failures = {r.precondition for r in evaluate_claim(
            manifest, design=design, feature_stack_manifest=stack).failures}
        assert Precondition.SPATIALLY_BLOCKED_CV in failures
        assert Precondition.PRE_REGISTERED_THRESHOLD in failures


def test_the_refusal_names_every_failing_precondition_not_just_the_first() -> None:
    manifest = _eligible_run()
    manifest.cross_validation["designs"][0]["spatially_blocked"] = False
    manifest.upstream_hashes = {"corpus": "sha256:c"}
    with pytest.raises(ClaimRefused) as excinfo:
        require_validated_claim(manifest, design="leave_one_site_out",
                                feature_stack_manifest=_stack(), contract={})
    message = str(excinfo.value)
    assert "3 of 6 preconditions failed" in message
    for precondition in (Precondition.SPATIALLY_BLOCKED_CV, Precondition.PROVENANCE_CHAIN,
                         Precondition.PRE_REGISTERED_THRESHOLD):
        assert precondition.value in message


def test_a_claim_citing_a_design_the_run_did_not_execute_is_refused_by_name() -> None:
    verdict = _evaluate(_eligible_run(), design="a_design_that_never_ran")
    assert Precondition.SPATIALLY_BLOCKED_CV in {r.precondition for r in verdict.failures}
    assert "records no design named" in verdict.failures[0].detail
