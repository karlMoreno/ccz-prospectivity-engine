"""corpus_builder (E1.3) — the end-to-end wiring test: IngestionPipeline.run()
through the real adapters, the E1.2 NormalizerRegistry, and the E1.3
DuplicateStationSpecification, into one corpus. Plus the three required
end-to-end properties: idempotency, flagged/failed retention, and
deterministic (byte-identical, stably-sorted) CSV output.

Corpus is single-source today (P1b, 2026-07-27 audit follow-up): only [01]
and [05] (merged under src_so268_boxcore) are wired -- src_dryad_chamber [06]
and src_ts6_grid [18] both still point at E1.1 placeholder fixtures and are
guarded out of REAL_ADAPTER_BUILDERS until real data exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.corpus_builder import (
    REAL_ADAPTER_BUILDERS,
    SAMPLES_DIR,
    SOURCES_DIR,
    build_corpus,
    build_dryad_chamber_adapter,
    build_ts6_grid_adapter,
    write_corpus_csv,
)
from engine.prospectivity.ingestion.corpus_builder import _require_production_path
from engine.prospectivity.ingestion.dedup_rules import DuplicateStationSpecification
from engine.prospectivity.ingestion.normalizer_registry import build_default_registry
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter


# --- P1 / P1b (2026-07-27 audit follow-up): production must refuse fixtures -


def test_require_production_path_raises_for_a_tests_fixtures_path() -> None:
    with pytest.raises(ValueError, match="test fixtures path"):
        _require_production_path(SAMPLES_DIR / "dryad_chamber_sample.csv")


def test_require_production_path_passes_through_a_real_data_path() -> None:
    real_path = SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
    assert _require_production_path(real_path) == real_path


def test_dryad_chamber_builder_itself_raises_until_real_data_exists() -> None:
    """The concrete historical bug this guard exists to catch: [06] still
    points at E1.1's placeholder fixture, so even calling its own builder
    function directly (not just via REAL_ADAPTER_BUILDERS) must fail loudly
    rather than silently constructing a fabricated-data adapter."""
    with pytest.raises(ValueError, match="test fixtures path"):
        build_dryad_chamber_adapter()


def test_ts6_grid_builder_itself_raises_until_real_data_exists() -> None:
    """P1b: the same fix as [06] got, for the same reason -- [18] still
    points at E1.1's synthetic grid fixture (real TS-6 digitization is a
    Track G deliverable that doesn't exist yet), so calling its builder
    directly must fail loudly rather than silently constructing a
    fabricated-data GRID adapter."""
    with pytest.raises(ValueError, match="test fixtures path"):
        build_ts6_grid_adapter()


def test_real_adapter_builders_does_not_include_unguarded_fixture_sources() -> None:
    """Belt-and-suspenders: every builder actually wired into production
    must be constructible without raising -- if a future edit re-adds [06]
    or [18] without also fixing their file_path, build_corpus() itself will
    fail loudly the moment it runs, but this test catches it at collection
    time instead of only during a real build."""
    for build_adapter in REAL_ADAPTER_BUILDERS:
        build_adapter()  # must not raise


def test_build_corpus_is_single_source_until_track_g_delivers() -> None:
    """D8-F (2026-07-27 review): [01] and [05] describe the SAME 36 real
    events, and [01] is now authoritative for MASS+COUNT (explicit
    quality_grade="A" in BoxcoreSummaryAdapter, with [05] explicitly "B" for
    MASS as of P2) -- so every one of [05]'s MASS/COUNT rows merges into
    [01]'s survivor via D1, and src_so268_nodules never appears as a
    standalone source_id in the final corpus. Its contribution isn't lost:
    it's absorbed (mean_nodule_mass_g etc. gap-filled) and provenance-linked
    (rule 2), asserted below.

    P1/P1b (2026-07-27 audit follow-up): src_dryad_chamber [06] and
    src_ts6_grid [18] are both no longer wired into REAL_ADAPTER_BUILDERS --
    both were still E1.1's placeholder fixtures, not real data, and neither
    belongs in a published, citable corpus. The corpus is single-source
    today: everything comes from [01]/[05] merged under src_so268_boxcore.
    This test's own name is the fact worth re-checking on every future
    source addition -- it should start failing the moment a second real
    source is legitimately wired in, which is the point."""
    corpus = build_corpus()
    assert len(corpus) > 0

    sources_seen = {obs.source_id for obs in corpus}
    assert sources_seen == {"src_so268_boxcore"}

    classes_seen = {obs.evidence_class for obs in corpus}
    # GRID and GRADE are both out of scope today: no real GRID source is
    # wired (src_ts6_grid awaits Track G's digitization) and GRADE's station
    # join is unresolved geology input -- MASS/COUNT/COVER only.
    assert classes_seen == {
        EvidenceClass.MASS,
        EvidenceClass.COUNT,
        EvidenceClass.COVER,
    }

    # [05]'s contribution survives as a merge, not a disappearance: every
    # src_so268_boxcore MASS/COUNT row's provenance links back to [05].
    boxcore_mass_and_count = [
        obs
        for obs in corpus
        if obs.source_id == "src_so268_boxcore"
        and obs.evidence_class in (EvidenceClass.MASS, EvidenceClass.COUNT)
    ]
    assert len(boxcore_mass_and_count) == 72  # 36 events x 2 classes
    assert all("src_so268_nodules" in (obs.notes or "") for obs in boxcore_mass_and_count)
    assert all(obs.mean_nodule_mass_g is not None for obs in boxcore_mass_and_count)


def test_mass_and_count_survivors_are_identical_regardless_of_adapter_order(
    tmp_path: Path,
) -> None:
    """P2 (2026-07-27 audit follow-up): the audit found MASS survivorship was
    order-dependent (reversing REAL_ADAPTER_BUILDERS flipped the winner from
    [01] to [05]) -- this is the test that actually guards the fix, unlike
    test_build_corpus_wires_all_four_real_adapters_end_to_end above, which
    only ever exercises the DEFAULT order and would not have caught the bug.

    Runs the real build_corpus() production code path twice -- once in
    REAL_ADAPTER_BUILDERS's normal order, once reversed -- and asserts the
    resulting corpus is identical either way. Deliberately asserts on the
    published CSV (the actual deliverable), not on quality_grade values or
    any other mechanism-specific field, so this test keeps working even if
    the tie-break mechanism changes later (e.g. to the lexicographic-source_id
    or contract-precedence scheme proposed for the general problem)."""
    forward = build_corpus(adapter_builders=REAL_ADAPTER_BUILDERS)
    reversed_corpus = build_corpus(adapter_builders=list(reversed(REAL_ADAPTER_BUILDERS)))

    forward_csv = tmp_path / "forward.csv"
    reversed_csv = tmp_path / "reversed.csv"
    write_corpus_csv(forward, forward_csv)
    write_corpus_csv(reversed_corpus, reversed_csv)
    assert forward_csv.read_bytes() == reversed_csv.read_bytes()

    # Targeted, human-readable check on top of the byte-identical proof
    # above: the specific claim the audit made concrete.
    for corpus, label in [(forward, "forward"), (reversed_corpus, "reversed")]:
        mass = next(
            obs
            for obs in corpus
            if obs.evidence_class == EvidenceClass.MASS and obs.event_id == "SO268/1_12-2"
        )
        count = next(
            obs
            for obs in corpus
            if obs.evidence_class == EvidenceClass.COUNT and obs.event_id == "SO268/1_12-2"
        )
        assert mass.source_id == "src_so268_boxcore", label
        assert count.source_id == "src_so268_boxcore", label


def test_build_corpus_normalizes_through_the_e12_registry_not_ad_hoc() -> None:
    """abundance_kg_m2 only ever appears where NormalizerRegistry (E1.2) would
    put it -- e.g. [01]'s real SO268/1_24-3 event (4.9kg / 0.25m2 = 19.6
    kg/m2) matches MassNormalizer's own formula exactly, proving the real
    end-to-end build actually routes through the registry, not an ad-hoc
    computation. (P1, 2026-07-27 audit follow-up: this test previously used
    src_dryad_chamber's CH-01 -- no longer wired into production, see
    test_build_corpus_wires_all_four_real_adapters_end_to_end.)"""
    corpus = build_corpus()
    boxcore_row = next(
        obs
        for obs in corpus
        if obs.source_id == "src_so268_boxcore"
        and obs.evidence_class == EvidenceClass.MASS
        and obs.event_id == "SO268/1_24-3"
    )
    assert boxcore_row.abundance_kg_m2 == pytest.approx(19.6)


def test_idempotency_rerunning_against_the_same_corpus_adds_nothing() -> None:
    """Strengthened 2026-07-29 (E1.5 follow-up): this test used to compare only
    the row COUNT and the id list, and it passed while re-runs silently grew
    every merged row's `notes` — each re-run appending another provenance link,
    one of them claiming the row was a duplicate of ITSELF. "Adds nothing" now
    means every field of every row is unchanged, which is what the name always
    claimed."""
    corpus: list[Observation] = []
    build_corpus(corpus)
    first_run = [obs.model_dump() for obs in corpus]

    build_corpus(corpus)  # same adapters, same shared corpus, run again
    build_corpus(corpus)  # and again — a fixed point, not just stable once

    assert len(corpus) == len(first_run)
    assert sorted(obs.source_record_id for obs in corpus) == sorted(
        row["source_record_id"] for row in first_run
    )
    assert [obs.model_dump() for obs in corpus] == first_run


class _SingleRecordAdapter(SourceAdapter):
    """Minimal test-only SourceAdapter emitting exactly one pre-built
    RawRecord, so a single out-of-bounds value can be pushed through the
    real IngestionPipeline without needing a native file format."""

    def __init__(self, source_id: str, record: dict[str, Any]) -> None:
        self.source_id = source_id
        self._record = record

    def fetch(self) -> list[dict[str, Any]]:
        return [self._record]

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        return list(raw_records)


def test_flagged_row_from_screening_is_retained_with_qa_status_intact() -> None:
    """An out-of-range abundance gets qa_status="flagged" by E1.2's
    apply_screening -- that status must survive validate/dedup/append."""
    corpus: list[Observation] = []
    adapter = _SingleRecordAdapter(
        "src_synthetic_outlier",
        {
            "source_id": "src_synthetic_outlier",
            "source_record_id": "src_synthetic_outlier_MASS_000000",
            "evidence_class": "MASS",
            "latitude": 5.0,
            "longitude": -150.0,
            "nodule_mass_kg": 15.0,
            # -> 60 kg/m2: past normalization.yaml's screening max (45), but
            # within Observation's own field maximum (100, schema v4) -- the
            # value must reach qa_status="flagged", not raise ValidationError.
            "sampled_area_m2": 0.25,
            "observation_or_prediction": "observed",
            "is_open": True,
            "qa_status": "pending",
        },
    )
    IngestionPipeline(
        adapter=adapter,
        normalizers=build_default_registry(),
        corpus=corpus,
        dedup_specification=DuplicateStationSpecification(corpus),
    ).run()

    assert len(corpus) == 1
    assert corpus[0].qa_status == "flagged"
    assert corpus[0].abundance_kg_m2 == 60.0  # flagged, not dropped or altered


def test_fail_row_already_in_the_corpus_survives_dedup_unchanged() -> None:
    """fail-is-terminal (E1.2 review decision) must hold end-to-end: a row
    already marked "fail" is not touched by a later pipeline run, even one
    that runs dedup against the corpus it lives in."""
    pre_existing_fail_row = Observation(
        source_record_id="src_manual_review_MASS_000000",
        source_id="src_manual_review",
        evidence_class="MASS",
        latitude=-40.0,  # far from every real adapter's sample coordinates
        longitude=10.0,
        abundance_kg_m2=12.0,  # ordinary in-bounds value; this test isn't about screening
        observation_or_prediction="observed",
        is_open=True,
        qa_status="fail",
    )
    corpus: list[Observation] = [pre_existing_fail_row]

    build_corpus(corpus)  # runs all four real adapters against this corpus

    survivor = next(
        obs for obs in corpus if obs.source_record_id == "src_manual_review_MASS_000000"
    )
    assert survivor.qa_status == "fail"
    assert survivor.abundance_kg_m2 == 12.0


def test_write_corpus_csv_is_byte_identical_across_two_independent_builds(
    tmp_path: Path,
) -> None:
    path_a = tmp_path / "a.csv"
    path_b = tmp_path / "b.csv"
    write_corpus_csv(build_corpus(), path_a)
    write_corpus_csv(build_corpus(), path_b)
    assert path_a.read_bytes() == path_b.read_bytes()


def test_write_corpus_csv_sort_order_is_stable_regardless_of_insertion_order(
    tmp_path: Path,
) -> None:
    """The CSV's row order must come from the (source_id, source_record_id)
    sort key, not from whatever order the corpus list happens to be in."""
    forward = build_corpus()
    shuffled = list(reversed(forward))

    path_forward = tmp_path / "forward.csv"
    path_shuffled = tmp_path / "shuffled.csv"
    write_corpus_csv(forward, path_forward)
    write_corpus_csv(shuffled, path_shuffled)

    assert path_forward.read_bytes() == path_shuffled.read_bytes()


def test_write_corpus_csv_columns_match_the_schema_field_order(tmp_path: Path) -> None:
    path = tmp_path / "corpus.csv"
    write_corpus_csv(build_corpus(), path)
    header = pd.read_csv(path, nrows=0).columns.tolist()
    assert header == list(Observation.model_fields.keys())
