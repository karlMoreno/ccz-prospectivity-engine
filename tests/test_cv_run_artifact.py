"""E2.4 §3 — the COMMITTED run artifact (`data/runs/e2.4/run_manifest.json`).

The report's numbers live in a file, so the file is under test: its own hash
must verify against its own contents, its claims must be the ones the code
makes, and the theorem must be visible in it. Regenerate it with

    python -m engine.prospectivity.validation.run_cv <dem.tif> <out> \\
        --dem-data-origin SYNTHETIC --seed 0 --run-id e2.4-report

WHAT REPRODUCES AND WHAT DOES NOT (measured at §3, and the reason this file
does not re-run the CV to compare hashes): identical inputs and seed give
byte-identical `cross_validation`, `cv_scores`, `estimator_declarations` and
`matrix_sha256` — the science. They give a DIFFERENT `content_hash` and
`upstream_hashes`, because `FeatureStackManifest` hashes the DEM's ABSOLUTE
PATH (docs/BACKLOG.md §3, recorded 2026-08-19). So the assertions below pin
the reproducible content and the artifact's internal consistency, and the
non-portable identity is a named backlog item rather than a green test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.validation.runner import run_watermark

ARTIFACT = Path(__file__).resolve().parent.parent / "data" / "runs" / "e2.4" / "run_manifest.json"
CLAIM_ELIGIBLE = ["leave_one_cluster_out", "leave_one_site_out"]
UNBLOCKED = {"leave_one_station_out", "random_k_fold"}


@pytest.fixture(scope="module")
def artifact() -> RunManifest:
    return RunManifest(**json.loads(ARTIFACT.read_text()))


def test_the_committed_artifact_hash_verifies_against_its_own_contents(artifact: RunManifest) -> None:
    """The strongest integrity check available on a committed record: it was
    not hand-edited after emission."""
    assert artifact.content_hash == artifact.compute_content_hash()
    assert artifact.run_id == "e2.4-report" and artifact.seed == 0
    raw = json.loads(ARTIFACT.read_text())
    assert "NaN" not in ARTIFACT.read_text() and "Infinity" not in ARTIFACT.read_text()
    assert raw["generator"] == "engine.prospectivity.validation.run_cv"
    assert raw["derivation"]


def test_the_artifact_is_watermarked_and_chains_to_corpus_stack_and_matrix(artifact: RunManifest) -> None:
    assert artifact.data_origin == "SYNTHETIC"
    watermark = run_watermark(artifact)
    assert watermark is not None and "non-scientific" in watermark
    assert set(artifact.upstream_hashes) == {"corpus", "feature_stack", "training_matrix"}
    assert all(v.startswith("sha256:") for v in artifact.upstream_hashes.values())
    corpus_manifest = json.loads(
        (ARTIFACT.parent.parent.parent / "corpus" / "manifest.json").read_text()
    )
    # the corpus half of the chain is checkable against the committed corpus
    assert artifact.upstream_hashes["corpus"] == corpus_manifest["content_hash"]
    assert artifact.inputs["training_matrix"]["n_stations"] == 35
    assert artifact.inputs["training_matrix"]["distinct_cell_count"] == 4  # the ceiling's cause


def test_the_artifact_records_four_designs_of_which_two_may_back_a_claim(artifact: RunManifest) -> None:
    designs = {d["name"]: d for d in artifact.cross_validation["designs"]}
    assert set(designs) == set(CLAIM_ELIGIBLE) | UNBLOCKED
    assert artifact.claim_eligible_designs == CLAIM_ELIGIBLE
    for name in UNBLOCKED:
        assert designs[name]["claim_eligible"] is False
        assert designs[name]["spatially_blocked"] is False
    assert designs["leave_one_cluster_out"]["measured_min_separation_km"] == pytest.approx(986.036, abs=1e-3)
    assert designs["leave_one_site_out"]["measured_min_separation_km"] == pytest.approx(4.614, abs=1e-3)
    assert designs["leave_one_station_out"]["measured_min_separation_km"] == pytest.approx(0.054, abs=1e-3)


def test_the_theorem_is_visible_in_the_committed_artifact(artifact: RunManifest) -> None:
    """Across the clusters, on the fold kriging could fit: its RMSE, MAE and
    bias equal the baseline's EXACTLY, the fitter's verdict is no-structure,
    and the other fold is a recorded refusal — the geometry theorem, in the
    file a reader opens."""
    loco = next(d for d in artifact.cross_validation["designs"] if d["name"] == "leave_one_cluster_out")
    krig = {r["fold_name"]: r for r in loco["results"] if r["estimator_name"] == "ordinary_kriging"}
    base = {r["fold_name"]: r for r in loco["results"] if r["estimator_name"] == "mean_baseline"}
    refused = [r for r in krig.values() if r["status"] == "refused"]
    scored = [r for r in krig.values() if r["status"] == "scored"]
    assert len(refused) == 1 and refused[0]["n_train"] == 14 and refused[0]["refusal_phase"] == "fit"
    assert len(scored) == 1 and scored[0]["n_train"] == 21
    assert scored[0]["provenance"]["no_structure"] is True
    b = base[scored[0]["fold_name"]]
    for metric in ("rmse", "mae", "mean_error"):
        assert scored[0]["metrics"][metric]["value"] == pytest.approx(
            b["metrics"][metric]["value"], abs=1e-12
        )
    # "the two clusters differ by X" — the measurement the fold DOES make
    assert abs(b["metrics"]["mean_error"]["value"]) == pytest.approx(1.886, abs=0.01)


def test_the_within_cluster_gate_reports_kriging_no_structure_verdicts_not_ties(artifact: RunManifest) -> None:
    """Karl's §1B framing, checkable in the artifact: on the site-out folds
    where kriging finds no structure, the record says so — a per-fold
    analogue of the theorem rather than a tie to be tallied."""
    site = next(d for d in artifact.cross_validation["designs"] if d["name"] == "leave_one_site_out")
    krig = [r for r in site["results"] if r["estimator_name"] == "ordinary_kriging"]
    assert len(krig) == 5
    no_structure = [r for r in krig if r["status"] == "scored" and r["provenance"]["no_structure"]]
    structured = [r for r in krig if r["status"] == "scored" and not r["provenance"]["no_structure"]]
    refused = [r for r in krig if r["status"] == "refused"]
    assert len(no_structure) == 2 and len(structured) == 2 and len(refused) == 1
    for row in no_structure:
        assert "reverts to the training mean" in row["provenance"]["verdict"]
    for row in structured:
        assert row["provenance"]["range_at_candidate_ceiling"] is True
        assert "unconstrained from above" in row["provenance"]["range_km_reported"]


def test_every_sd_shaped_number_in_the_artifact_carries_its_semantics(artifact: RunManifest) -> None:
    methods = {name: d["uncertainty_method"] for name, d in artifact.estimator_declarations.items()}
    assert set(methods.values()) == {
        "sample_sd_ddof1", "sqrt_ordinary_kriging_variance", "qrf_half_width_q16_q84"
    }
    for score in artifact.cv_scores:
        assert score.uncertainty_method == methods[score.estimator_name]
    for design in artifact.cross_validation["designs"]:
        for row in design["results"]:
            assert row["uncertainty_method"] == methods[row["estimator_name"]]
        for name, pooled in design["pooled"].items():
            assert pooled["uncertainty_method"] == methods[name]
    # …and no OOB-derived value anywhere in the committed file
    assert "oob" not in ARTIFACT.read_text().lower()


def test_the_artifact_dates_score_visibility_outside_its_own_hash(artifact: RunManifest) -> None:
    assert artifact.scores_first_visible is not None
    assert "scores_first_visible" not in artifact.substance()
    assert "COMMIT" in artifact.scores_first_visible_note
    assert artifact.content_hash == artifact.compute_content_hash()  # unaffected by the timestamp


def test_the_run_entry_point_composes_the_four_designs_the_report_reads() -> None:
    """`run_cv.build_splitters` is the only place run_cv decides anything —
    WHICH designs the committed artifact contains, in the order §3 reads
    them, with the declarations that decide claim eligibility."""
    from engine.prospectivity.validation.run_cv import DEFAULT_RANDOM_K, build_splitters

    splitters = build_splitters(seed=0)
    assert [s.name for s in splitters] == [
        "leave_one_cluster_out", "leave_one_site_out", "leave_one_station_out", "random_k_fold"
    ]
    assert [s.spatially_blocked for s in splitters] == [True, True, False, False]
    assert [s.required_separation_km for s in splitters] == [100.0, 2.0, 0.0, 0.0]
    assert all(s.purpose for s in splitters)
    # the random design is seeded FROM the run seed, so the wrong comparison
    # is as reproducible as the right ones
    assert build_splitters(seed=7)[3].split.__self__._seed == 7  # type: ignore[attr-defined]
    assert build_splitters()[3].split.__self__._k == DEFAULT_RANDOM_K  # type: ignore[attr-defined]
    committed = json.loads(ARTIFACT.read_text())
    assert [d["name"] for d in committed["cross_validation"]["designs"]] == [s.name for s in splitters]
