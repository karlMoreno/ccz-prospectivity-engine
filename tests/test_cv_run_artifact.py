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

RE-STAMPED ONCE, AT E3.4 (2026-08-22). `RunManifest.substance()` dumps every
field, defaults included, so the four fields E3.4 added (`prediction_grid`,
`surfaces`, `claim`, `provenance_chain`) re-hashed this committed artifact.
The file was reloaded under the new shape and `finalize()`d: the four new
fields are `null`, `content_hash` moved from `sha256:7f6c7fae…` to
`sha256:e3ac1561…`, and EVERY OTHER BYTE is identical — including
`generated_at`, `scores_first_visible` and the path-dependent upstream
hashes, which a regeneration would have moved. The commit is the witness.
So the self-hash test below still means "not hand-edited": the one edit it
has had is the shape's, and it is on record.
"""

from __future__ import annotations

import json
import re
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


# --------------------------------------------- obligation 7's ONE observer
#
# F-6 RESIDUE (E2.4 audit; closed at P2.CLOSE commit 2, 2026-08-20). The
# finding, RE-VERIFIED before this test was written: the uncertainty-semantics
# column was deleted from §3's fold table and the full suite stayed GREEN at
# 470 passed. Obligation 7 was structural on the MANIFEST side and merely
# documentary on the REPORT side, which is the distinction this project draws
# everywhere else.
#
# THE CHOICE, and its trade-off. The audit offered three shapes: (a) parse the
# tables, (b) generate them from the manifest, (c) assert on the renderer.
# Karl leaned (c) — but (c)'s premise does not hold: THERE IS NO RENDERER.
# `grep` over engine/ finds no markdown emitter, the §3 tables are
# hand-written, and the audit's own table-verification script was never
# committed. Implementing (c) would mean BUILDING a renderer and regenerating
# a walkthrough — converting a frozen historical record into generated output,
# against the convention C8.1 just re-affirmed. So this is (a), knowingly:
#
#   WHAT IT CATCHES: the exact defect found — an sd-derived table losing the
#     column that says what its sd MEANS.
#   WHAT IT DOES NOT CATCH: a WRONG semantics value (it checks the column
#     exists, not that the sentence is right); a renamed column heading, which
#     reads as removal and fails loudly rather than silently; and drift in any
#     document this list does not name. A test that parses prose is brittle by
#     nature — that brittleness is the price of observing a hand-written file
#     at all, and it is paid here rather than pretended away.
#
# SCOPE FENCE (the audit's finding names one gap, not a class): one obligation,
# one observer, one document list. No walkthrough-verification framework —
# that is the ceremony PATTERNS.md §3 refuses.

WALKTHROUGHS = Path(__file__).resolve().parent.parent / "docs" / "walkthroughs"
SD_DERIVED_COLUMNS = {"cov ±1σ", "z-RMS"}
DOCS_REPORTING_SD_NUMBERS = ("E2.4.md",)
_SEPARATOR = re.compile(r"\|[\s:|-]+\|")


def _tables_with_sd_columns(markdown: str) -> list[list[str]]:
    """Header cells of every table whose HEADER declares an sd-derived column.

    TWO SEPARATE GUARDS, and it is worth being exact about which does what —
    a mutation run proved the obvious explanation wrong:

    * EXACT CELL EQUALITY (`SD_DERIVED_COLUMNS & set(cells)`) is what keeps
      this lint off PROSE. E2.4.md's test inventory has a row whose cell
      mentions "z-RMS 0" in a sentence; substring matching would fire on
      documentation ABOUT the metric instead of a report OF it.
    * The header-and-separator pairing is what makes "header" mean header, so
      a data ROW whose first cell were exactly "z-RMS" is not mistaken for
      one.

    Removing the separator check is a NO-OP on today's file — measured, not
    assumed — because the exact-match guard already excludes the only prose
    candidate. It stays because the two guards answer different questions.
    """
    lines = markdown.splitlines()
    headers = []
    for i in range(len(lines) - 1):
        if lines[i].startswith("|") and _SEPARATOR.fullmatch(lines[i + 1].strip()):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if SD_DERIVED_COLUMNS & set(cells):
                headers.append(cells)
    return headers


def test_every_walkthrough_table_printing_sd_derived_numbers_declares_its_uncertainty_semantics() -> None:
    """OBLIGATION 7, ON THE REPORT SIDE — the half that was documentary until
    now. Every hand-written table that prints `cov ±1σ` or `z-RMS` must also
    carry the column naming what its sd MEANS, because those three numbers are
    not comparable across estimators whose sd means different things (a
    quantile half-width is not a Gaussian σ, and the baseline's sample SD is
    neither).

    SOLE OBSERVER of the report side: `test_every_sd_shaped_number_in_the_artifact_carries_its_semantics`
    reads the ARTIFACT and cannot see the markdown; measured at P2.CLOSE, the
    column was deleted from §3's fold table with the whole suite green.
    """
    examined = [
        (name, tuple(header))
        for name in DOCS_REPORTING_SD_NUMBERS
        for header in _tables_with_sd_columns((WALKTHROUGHS / name).read_text())
    ]
    # POSITIVE CONTROL, not decoration: without it a parser that matched
    # nothing — a renamed file, changed table syntax, a broken regex — would
    # pass vacuously on an empty result.
    assert len(examined) >= 2, (
        f"expected at least the two §3 report tables, parsed {len(examined)} — "
        "the lint found nothing to check, which is a broken lint, not a clean file"
    )
    # A POSITIVE FULL-STATE COMPARISON (CLAUDE.md rule 3), for the reason
    # commit 1 hit an hour earlier in this same batch: collecting what is
    # MISSING and asserting the list is empty stays GREEN when the collecting
    # CONDITION is broken to `if False`. Comparing what DECLARED against what
    # was EXAMINED fails in both directions.
    declaring = [
        (name, header)
        for name, header in examined
        if any("semantics" in cell.lower() for cell in header)
    ]
    assert declaring == examined, (
        "a table printing sd-derived numbers has no uncertainty-semantics "
        f"column: {[e for e in examined if e not in declaring]}"
    )
