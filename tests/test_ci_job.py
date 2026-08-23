"""E5.6 — the named, artifact-producing CI job and its verification step.

The job cannot run here (CI runs on a push; origin/main was 62 commits
behind at E5.6); what the suite can hold it to is that the workflow parses,
names the job, calls the SAME entry points the suite exercises with no
CI-only code path, and that the verification step passes on a real run,
fails by name on a tampered one, and fails by name when the verdict moves.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from engine.prospectivity import verify_run
from engine.prospectivity.verify_run import EXPECTED_VERDICT_SETS, VerificationFailed, verify

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_the_workflow_parses_names_the_job_and_calls_the_entry_points_the_suite_exercises() -> None:
    wf = yaml.safe_load(WORKFLOW.read_text())
    assert set(wf["jobs"]) == {"test", "run-artifact"}
    job = wf["jobs"]["run-artifact"]
    runs = [step.get("run", "") for step in job["steps"]]
    harness_calls = [r for r in runs if "python -m engine.prospectivity.harness" in r]
    assert len(harness_calls) == 2  # two trees
    for call in harness_calls:
        assert "--dem-data-origin SYNTHETIC" in call and "--ts6-data-origin SYNTHETIC" in call
        assert "--designs" not in call  # the harness's own default: all four designs
        assert "light" not in call and "n_estimators" not in call  # the production registry, by the harness's only choice
    assert any("python -m engine.prospectivity.verify_run runs-a/run --same-as runs-b/run" in r for r in runs)
    assert any("tests.fixtures.rasters" in r and "write_synthetic_bathymetry" in r for r in runs)
    upload = next(step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/upload-artifact"))
    assert "${{ github.sha }}" in upload["with"]["name"] and upload["with"]["path"] == "runs-a/run"
    assert upload["with"]["retention-days"] == 30 and upload["with"]["if-no-files-found"] == "error"
    assert "needs" not in job  # not gated on the test job; the verify step is the artifact's own gate
    # the test job is unchanged in what it runs
    assert any("pytest" in (step.get("run") or "") for step in wf["jobs"]["test"]["steps"])


def test_the_verification_step_passes_on_a_real_run_and_reports_what_it_recomputed(production_run: dict) -> None:
    report = verify(production_run["out"])
    assert report["output_files_verified"] == 52 and report["links_recomputed"] == ["corpus", "feature_stack"]
    gate = "an_acceptance_threshold_existed_before_the_scores"
    assert report["verdict_sets"] == {
        "leave_one_cluster_out": ([gate], 5), "leave_one_site_out": ([gate], 5),
        "random_k_fold": (sorted([gate, "spatially_blocked_cross_validation_ran"]), 4),
    }
    assert report["eligible"] == {d: False for d in report["eligible"]} and report["claim_design"] == "leave_one_site_out"
    assert report["environment"] and report["n_output_files"] == 52 and report["bytes"] > 1_000_000  # 1.4 MB with three designs; ~2.75 MB with four
    assert verify_run.main([str(production_run["out"]), "--environment"]) == 0


def test_the_two_tree_claim_holds_for_a_copied_run_and_a_tampered_file_or_a_moved_verdict_fails_by_name(
    production_run: dict, tmp_path: Path, monkeypatch
) -> None:
    copy = tmp_path / "copy" / "run"
    shutil.copytree(production_run["out"], copy)
    assert verify(production_run["out"], same_as=copy)["same_as"]["identical"] is True
    # a tampered output file
    tampered = tmp_path / "tampered" / "run"
    shutil.copytree(production_run["out"], tampered)
    (tampered / "mean_baseline.provenance.json").write_text("{}")
    with pytest.raises(VerificationFailed, match=r"1 output file\(s\) do not hash to the manifest's record: \['mean_baseline.provenance.json'\]"):
        verify(tampered)
    # the verdict moved (the expectation says what the day CP1/CP4 land looks like)
    moved = dict(EXPECTED_VERDICT_SETS); moved["leave_one_site_out"] = (frozenset(), 6)
    monkeypatch.setattr(verify_run, "EXPECTED_VERDICT_SETS", moved)
    with pytest.raises(VerificationFailed, match="THE VERDICT MOVED on 'leave_one_site_out'"):
        verify(production_run["out"])
    monkeypatch.undo()
    # not a run
    with pytest.raises(VerificationFailed, match="not a run directory"):
        verify(tmp_path / "nothing")
    assert verify_run.main([str(tmp_path / "nothing")]) == 1
    # a second run that differs in substance (a different run id is NOT substance: hash-excluded)
    other = json.loads((copy / "run_manifest.json").read_text()); other["run_id"] = "another-id"
    from engine.prospectivity.domain.results import RunManifest
    (copy / "run_manifest.json").write_text(RunManifest(**other).to_json())
    assert verify(production_run["out"], same_as=copy)["same_as"] == {"run_id": "another-id", "identical": True}
