"""CorpusManifest — the ingestion-stage provenance artifact.

Every test here runs the REAL production build (`build_corpus_with_manifest`)
against the real downloaded PANGAEA files, not a re-implementation: the whole
value of this artifact is that it describes what production actually did.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.prospectivity.domain.evidence import QAStatus
from engine.prospectivity.ingestion.corpus_builder import (
    REAL_ADAPTER_BUILDERS,
    build_corpus,
    build_corpus_with_manifest,
    write_corpus_csv,
)
from engine.prospectivity.provenance.recorder import ProvenanceRecorder

ABSORBED_SOURCE = "src_so268_nodules"  # [05]
SURVIVING_SOURCE = "src_so268_boxcore"  # [01]
FAILED_BOX_CORE_EVENT = "SO268/1_12-2"


# --- 1: the fully-absorbed source is still a contributing source ------------


def test_fully_absorbed_source_appears_in_contributing_sources() -> None:
    """The finding this artifact exists for: [05] supplies mean_nodule_mass_g
    for all 36 events, but dedup absorbs every one of its rows into [01]'s, so
    it appears in NO corpus row. A reader of the CSV sees one source; two
    contributed."""
    corpus, manifest = build_corpus_with_manifest()

    source_ids_in_corpus = {obs.source_id for obs in corpus}
    assert ABSORBED_SOURCE not in source_ids_in_corpus  # invisible in the CSV
    assert ABSORBED_SOURCE in manifest.contributing_sources  # visible here
    assert manifest.sources_absorbed_entirely == [ABSORBED_SOURCE]

    absorbed = next(s for s in manifest.sources if s.source_id == ABSORBED_SOURCE)
    assert absorbed.fully_absorbed is True
    assert absorbed.admitted_rows == 0
    assert absorbed.absorbed_rows == 72  # 36 events x MASS+COUNT


def test_absorbed_sources_contribution_is_still_present_in_the_corpus() -> None:
    """Absorbed is not discarded: D1's gap-fill merge means [05]'s
    mean_nodule_mass_g survives on [01]'s rows. The manifest claims [05]
    contributed; this checks the claim is true."""
    corpus, _ = build_corpus_with_manifest()
    mass_rows = [obs for obs in corpus if obs.evidence_class.value == "MASS"]
    assert mass_rows
    assert all(obs.mean_nodule_mass_g is not None for obs in mass_rows)


# --- 2: the chain reconciles for every source -------------------------------


def test_every_source_reconciles_no_rows_vanish_unaccounted_for() -> None:
    """adapted == admitted + absorbed + rejected, for every source.

    NOTE the identity is stated on ADAPTED records, not FETCHED rows: one raw
    row fans out into one record per evidence class ([01]: 36 rows -> 108
    records) and [05] AGGREGATES many rows into few (1,658 rows -> 72
    records), so fetched is not a disposition total. `flagged` is a SUBSET of
    admitted (a quality mark on rows that are in the corpus), not a fourth
    disposition — asserted here so a future change that starts dropping
    flagged rows fails."""
    _, manifest = build_corpus_with_manifest()
    assert manifest.sources
    for source in manifest.sources:
        assert source.reconciles is True, source.source_id
        assert source.adapted_records == (
            source.admitted_rows + source.absorbed_rows + source.rejected_rows
        ), source.source_id
        assert source.flagged_admitted_rows <= source.admitted_rows
        assert source.fetched_rows > 0


def test_corpus_row_count_equals_total_admitted_across_sources() -> None:
    corpus, manifest = build_corpus_with_manifest()
    assert manifest.corpus_row_count == len(corpus)
    assert manifest.corpus_row_count == sum(s.admitted_rows for s in manifest.sources)


# --- 3: training_eligible_count is its own number ---------------------------


def test_training_eligible_count_is_separate_from_admitted_and_excludes_flagged() -> None:
    corpus, manifest = build_corpus_with_manifest()
    # The two numbers that must never be conflated again.
    assert manifest.corpus_row_count == 108
    assert manifest.training_eligible_count == 35
    assert manifest.training_eligible_count != manifest.corpus_row_count

    # And the gap explains itself in the same object.
    assert manifest.rows_by_evidence_class == {"COUNT": 36, "COVER": 36, "MASS": 36}
    assert manifest.rows_by_qa_status[QAStatus.FLAGGED.value] == 3

    eligible = [obs for obs in corpus if obs.is_training_eligible()]
    assert len(eligible) == manifest.training_eligible_count
    assert all(
        obs.qa_status not in (QAStatus.FLAGGED, QAStatus.FAIL) for obs in eligible
    )


def test_training_eligible_excludes_the_real_failed_box_core() -> None:
    """D5.3's concrete case: SO268/1_12-2 ("GER Trial; failed") is a
    well-formed MASS row with a real abundance and must not be trainable."""
    corpus, manifest = build_corpus_with_manifest()
    eligible_events = {obs.event_id for obs in corpus if obs.is_training_eligible()}
    assert FAILED_BOX_CORE_EVENT not in eligible_events
    flagged_events = {
        obs.event_id for obs in corpus if obs.qa_status == QAStatus.FLAGGED
    }
    assert FAILED_BOX_CORE_EVENT in flagged_events


# --- 4: deterministic across builds -----------------------------------------


def _manifest_without_timestamp(manifest) -> dict:
    payload = json.loads(manifest.to_json())
    payload.pop("generated_at")
    return payload


def test_manifest_is_identical_across_two_builds_apart_from_the_timestamp() -> None:
    _, first = build_corpus_with_manifest()
    _, second = build_corpus_with_manifest()
    assert _manifest_without_timestamp(first) == _manifest_without_timestamp(second)
    # content_hash excludes generated_at by design, so it must match outright.
    assert first.content_hash == second.content_hash


# --- 5: order-independent (reuses P2's testability hook) --------------------


def test_manifest_is_identical_when_adapter_order_is_reversed() -> None:
    """Reuses build_corpus_with_manifest's `adapter_builders` parameter (P2's
    hook) rather than mutating the module global, so this exercises the real
    production path. If survivorship regresses to depending on run order, the
    per-source dispositions diverge and this fails.

    Source lists are sorted by source_id, so the WHOLE manifest — including
    its content_hash — must match, not merely agree field by field. This test
    found a real defect when first written (2026-07-29): `admitted` had been
    counted from pipeline appends, and because the dedup merge overwrites a
    corpus slot in place rather than appending, attribution flipped with order
    while the CSV stayed identical. Admitted is now counted from the finished
    corpus."""
    _, forward = build_corpus_with_manifest()
    _, reversed_build = build_corpus_with_manifest(
        adapter_builders=list(reversed(REAL_ADAPTER_BUILDERS))
    )

    assert _manifest_without_timestamp(forward) == _manifest_without_timestamp(
        reversed_build
    )
    assert forward.content_hash == reversed_build.content_hash

    # And the specific attribution the defect got wrong:
    assert forward.sources_absorbed_entirely == [ABSORBED_SOURCE]
    assert reversed_build.sources_absorbed_entirely == [ABSORBED_SOURCE]


# --- 6: recording is side-effect free ---------------------------------------


def test_recording_does_not_change_the_corpus(tmp_path: Path) -> None:
    """THE invariant of the Observer wiring: a recorded build and an
    unrecorded build must produce a byte-identical corpus. If an observer
    could influence a pipeline decision, every number in the manifest would
    describe a build that only happens when someone is watching."""
    unobserved = build_corpus()
    observed = build_corpus(observer=ProvenanceRecorder())

    unobserved_path = tmp_path / "unobserved.csv"
    observed_path = tmp_path / "observed.csv"
    write_corpus_csv(unobserved, unobserved_path)
    write_corpus_csv(observed, observed_path)
    assert unobserved_path.read_bytes() == observed_path.read_bytes()


def test_null_observer_is_the_default_so_unobserved_pipelines_are_unchanged() -> None:
    """Belt-and-braces on the Null Object default: build_corpus() with no
    observer argument still works and still produces the full corpus."""
    assert len(build_corpus()) == 108


# --- licenses + geometry: recorded, not judged ------------------------------


def test_licenses_are_recorded_per_source_with_a_corpus_level_non_commercial_flag() -> None:
    """[01] and [05] are both CC BY-NC 4.0, so everything derived from this
    corpus inherits a non-commercial constraint. One field lookup, not a
    survey of 13 source-queue entries."""
    _, manifest = build_corpus_with_manifest()
    assert manifest.any_non_commercial_input is True
    for source in manifest.sources:
        assert source.license == "CC-BY-NC-4.0"
        assert source.is_non_commercial is True


def test_every_source_records_a_real_computed_input_hash_not_a_placeholder() -> None:
    _, manifest = build_corpus_with_manifest()
    for source in manifest.sources:
        assert source.input_content_hash is not None
        assert source.input_content_hash.startswith("sha256:")
        assert len(source.input_content_hash) == len("sha256:") + 64
        assert "synthetic" not in source.input_content_hash
        assert source.backed_by == "real_data"


def test_geometry_records_the_aoi_mismatch_and_the_variogram_support_gap() -> None:
    """Both facts that previously lived only in audit findings: every row falls
    outside the placeholder AOI, and the pairwise distances have a ~974 km hole
    in the middle."""
    _, manifest = build_corpus_with_manifest()

    containment = manifest.study_area_containment
    assert containment["rows_outside_study_area"] == containment["rows_total"] == 108
    assert containment["fraction_outside"] == 1.0

    summary = manifest.spatial_summary
    assert summary["clusters"] == 2
    assert summary["distinct_locations"] == 36
    assert summary["linkage_distance_km"] == 100.0
    assert len(summary["cluster_extents"]) == 2
    for extent in summary["cluster_extents"]:
        assert extent["max_internal_distance_km"] < 15.0  # tight clusters

    distances = summary["pairwise_distance_km"]
    assert distances["pairs"] == 630  # 36 choose 2
    assert distances["largest_gap_km"] > 900.0
    low, high = distances["largest_gap_between_km"]
    assert low < 15.0 and high > 900.0  # nothing between ~12 km and ~986 km


def test_manifest_declares_its_contract_versions_and_no_upstream_artifacts() -> None:
    _, manifest = build_corpus_with_manifest()
    versions = manifest.contract_versions
    assert versions["master_observations_schema_version"] == 4
    assert versions["covariates_registry_version"] == 3
    assert versions["normalization_policy_version"] == 1
    assert versions["study_area_id"] == "ccz_alpha_aoi"
    # Ingestion is the first stage: raw-download hashes live per source.
    assert manifest.upstream_hashes == {}
    assert manifest.content_hash is not None
