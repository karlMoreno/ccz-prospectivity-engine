"""corpus_builder (E1.3) — the end-to-end wiring test: IngestionPipeline.run()
through the real adapters, the E1.2 NormalizerRegistry, and the E1.3
DuplicateResolutionPolicy, into one corpus. Plus the three required
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

from engine.prospectivity.domain.evidence import EvidenceClass, QAStatus
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
from engine.prospectivity.ingestion.corpus_builder import (
    _require_production_path,
    _require_proven_measured,
)
from engine.prospectivity.ingestion.dedup_rules import DuplicateResolutionPolicy
from engine.prospectivity.provenance.corpus_manifest import (
    file_sha256,
    measured_evidence_failure,
    source_queue_entries,
)
from engine.prospectivity.ingestion.normalizer_registry import build_default_registry
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter


# --- P1 / P1b (2026-07-27 audit follow-up): production must refuse fixtures -


def test_require_production_path_raises_for_a_tests_fixtures_path() -> None:
    with pytest.raises(ValueError, match="outside data/sources"):
        _require_production_path(SAMPLES_DIR / "dryad_chamber_sample.csv")


def test_require_production_path_raises_for_any_path_outside_data_sources() -> None:
    """P2.0d-2: the location rule is POSITIVE (raw downloads live in
    data/sources/, per PROVENANCE.md), so data/fixtures/native/ is refused by
    location too — including the review's probe where a fixture's OWN hash is
    recorded in a queue entry, which the evidence check honestly passes."""
    native = SOURCES_DIR.parent / "fixtures" / "native" / "synthetic_boxcore_native.csv"
    with pytest.raises(ValueError, match="outside data/sources"):
        _require_production_path(native)


def test_require_production_path_passes_through_a_real_data_path() -> None:
    real_path = SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
    assert _require_production_path(real_path) == real_path


# --- P2.0d-2: the declaration-plus-evidence guard. The refusals are the ---
# --- point; each of the three conditions gets its own named case.       ---


def test_native_fixture_csv_is_refused_by_the_full_guard() -> None:
    """THE concrete hole this guard family exists to close: before P2.0c
    these files sat on the real-data side of both path predicates. Under the
    full guard the POSITIVE location rule refuses it first (not under
    data/sources/); even without that layer, its bytes could not reproduce
    [01]'s recorded hash (the wrong-file test below pins that branch), and
    the evidence-only `_backed_by` books it "fixture" for the same reason."""
    native = SOURCES_DIR.parent / "fixtures" / "native" / "synthetic_boxcore_native.csv"
    with pytest.raises(ValueError, match="outside data/sources"):
        _require_proven_measured("src_so268_boxcore", native)


def test_measured_declaration_with_null_hash_is_refused_as_unproven() -> None:
    """One of the seven real undownloaded sources, not a synthetic case:
    [02] declares MEASURED with content_hash: null. A claim with pending
    evidence is refused — the [06] fixtures were not mislabelled, they were
    unproven."""
    with pytest.raises(ValueError, match="content_hash: null"):
        _require_proven_measured(
            "src_domes_fewkes1980", SOURCES_DIR / "PANGAEA-878220.tab"
        )


def test_measured_declaration_whose_file_is_absent_is_refused() -> None:
    """[01] has real recorded evidence, but pointed at a file that does not
    exist the guard must refuse on existence, not crash on hashing."""
    with pytest.raises(ValueError, match="does not exist"):
        _require_proven_measured(
            "src_so268_boxcore", SOURCES_DIR / "SO268-does-not-exist.tab"
        )


def test_measured_declaration_whose_hash_mismatches_the_bytes_is_refused() -> None:
    """[01]'s entry pointed at [05]'s real file: declared MEASURED, file
    exists, recorded hash is a real SHA-256 — and it is the WRONG file. (A
    malformed placeholder like "sha256:synthetic-fixture" hits the 64-hex
    FORMAT branch instead — pinned in test_corpus_manifest.py.)"""
    with pytest.raises(ValueError, match="does not match the bytes on disk"):
        _require_proven_measured(
            "src_so268_boxcore", SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
        )


def test_non_measured_declaration_is_refused_naming_the_declared_origin() -> None:
    """[18] declares LITERATURE — even with a real existing file, only proven
    MEASURED sources are admissible on a production path."""
    with pytest.raises(ValueError, match="LITERATURE"):
        _require_proven_measured(
            "src_ts6_grid", SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
        )


def test_derived_declaration_is_refused_naming_the_declared_origin() -> None:
    """[03] declares DERIVED (WET.4, corrected from MEASURED): Table 8's
    Concentration column is `0.08 x Coverage x Diameter`, a closed form over
    the two columns printed beside it, so it is not a measurement.

    The paired half of that correction. Before it, [03] was refused only
    because its content_hash was still null -- an ACCIDENTAL refusal that would
    have disappeared the moment Track G downloaded the file and filled the
    hash, silently admitting 79 computed rows into a training target as
    measurements. This pins the refusal to the ORIGIN instead."""
    with pytest.raises(ValueError, match="DERIVED"):
        _require_proven_measured(
            "src_domes_piper1979", SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
        )


def test_the_derived_refusal_does_not_depend_on_pending_hash_evidence() -> None:
    """The discriminating half: give [03]'s entry a REAL hash matching a REAL
    file -- the exact state a completed Track G download produces -- and it is
    still refused, on the origin. A test that only checked the null-hash entry
    would pass identically before and after WET.4 and would prove nothing."""
    entry = dict(source_queue_entries()["src_domes_piper1979"])
    path = SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
    entry["content_hash"] = file_sha256(path)   # already carries the "sha256:" prefix

    failure = measured_evidence_failure(entry, path)
    assert failure is not None and "DERIVED" in failure and "not MEASURED" in failure

    # and the mutation that must break it: flip the declaration back and the
    # same fully-evidenced entry is admitted.
    entry["data_origin"] = "MEASURED"
    assert measured_evidence_failure(entry, path) is None


def test_a_source_with_no_queue_entry_is_refused() -> None:
    with pytest.raises(ValueError, match="src_mystery"):
        _require_proven_measured(
            "src_mystery", SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"
        )


def test_the_two_proven_sources_are_admitted() -> None:
    """[01] and [05] are admitted, and remain admitted: declared MEASURED,
    queue hashes filled (P2.0d-2) and matching the bytes."""
    for source_id, filename in (
        ("src_so268_boxcore", "SO268-bc-nodules-summary-PANGAEA-904967.tab"),
        ("src_so268_nodules", "SO268-bc-nodules-PANGAEA-904962.tab"),
    ):
        path = SOURCES_DIR / filename
        assert _require_proven_measured(source_id, path) == path


def test_dryad_chamber_builder_itself_raises_until_real_data_exists() -> None:
    """The concrete historical bug this guard exists to catch: [06] still
    points at E1.1's placeholder fixture, so even calling its own builder
    function directly (not just via REAL_ADAPTER_BUILDERS) must fail loudly
    rather than silently constructing a fabricated-data adapter."""
    with pytest.raises(ValueError, match="outside data/sources"):
        build_dryad_chamber_adapter()


def test_ts6_grid_builder_itself_raises_until_real_data_exists() -> None:
    """P1b: the same fix as [06] got, for the same reason -- [18] still
    points at E1.1's synthetic grid fixture (real TS-6 digitization is a
    Track G deliverable that doesn't exist yet), so calling its builder
    directly must fail loudly rather than silently constructing a
    fabricated-data GRID adapter."""
    with pytest.raises(ValueError, match="outside data/sources"):
        build_ts6_grid_adapter()


def test_real_adapter_builders_does_not_include_unguarded_fixture_sources() -> None:
    """Belt-and-suspenders: every builder actually wired into production
    must be constructible without raising -- if a future edit re-adds [06]
    or [18] without also fixing their file_path, build_corpus() itself will
    fail loudly the moment it runs, but this test catches it at collection
    time instead of only during a real build."""
    for build_adapter in REAL_ADAPTER_BUILDERS:
        adapter = build_adapter()  # must not raise
        # Strengthened 2026-07-30: no-raise alone would still pass if
        # _require_production_path itself were removed. Assert the resolved
        # path directly — the property the name actually claims.
        resolved = Path(adapter.input_path).resolve()
        assert not {"tests", "fixtures"} <= {part.lower() for part in resolved.parts}, resolved
        assert resolved.is_file(), resolved


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
    test_build_corpus_is_single_source_until_track_g_delivers above, which
    only ever exercises the DEFAULT order and would not have caught the bug.
    (Reference corrected 2026-07-30: the cited test was renamed at P1b; the
    old name described a four-adapter wiring that no longer exists.)

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
    test_build_corpus_is_single_source_until_track_g_delivers.)"""
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
        dedup_policy=DuplicateResolutionPolicy(corpus),
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
    before = pre_existing_fail_row.model_dump()

    build_corpus(corpus)  # runs every wired real adapter against this corpus

    survivor = next(
        obs for obs in corpus if obs.source_record_id == "src_manual_review_MASS_000000"
    )
    # "unchanged" means EVERY field, not a chosen few. Strengthened 2026-07-30:
    # this used to check qa_status and abundance_kg_m2 only — exactly the shape
    # of the E1.5 bug, where `notes` grew while every selected assertion passed.
    assert survivor.model_dump() == before


def test_fail_row_that_actually_collides_with_a_real_event_keeps_its_verdict() -> None:
    """The companion the test above could NOT provide (2026-07-30).

    `test_fail_row_already_in_the_corpus_survives_dedup_unchanged` places its
    row at lat -40 / lon 10 — deliberately outside every adapter's coverage —
    so dedup never matches it and "fail survives dedup" was never actually
    exercised END TO END. This row uses [01]'s REAL key for SO268/1_24-3, so a
    merge genuinely fires against real adapter output.

    [01]'s row is quality_grade="A" (D8-F) and this one is "C", so the real
    row wins the slot and its 19.6 kg/m2 measurement is kept — but the fail
    verdict must survive onto the survivor, and the station must drop out of
    training."""
    manual_fail_row = Observation(
        source_record_id="src_manual_review_MASS_000001",
        source_id="src_manual_review",
        evidence_class="MASS",
        cruise="SO268/1",
        event_id="SO268/1_24-3",  # a real [01] event
        latitude=11.9311,
        longitude=-117.0273,
        # The adapter's own format. NOT "2019-03-06T00:00:00Z": that parses to
        # a timezone-AWARE datetime, while the adapter yields a naive one, and
        # the two compare unequal even though they denote the same instant —
        # so _same_station would see a disagreement and refuse the match. See
        # test_reconciliation.py's key-format guard for the same hazard.
        sample_datetime_utc="2019-03-06",
        abundance_kg_m2=99.0,  # deliberately wrong; this is why it's failed
        observation_or_prediction="observed",
        is_open=True,
        qa_status="fail",
        quality_grade="C",  # loses the slot to [01]'s "A"
    )
    corpus: list[Observation] = [manual_fail_row]
    build_corpus(corpus)

    survivor = next(
        obs
        for obs in corpus
        if obs.event_id == "SO268/1_24-3" and obs.evidence_class == EvidenceClass.MASS
    )
    # The better measurement won the slot...
    assert survivor.source_id == "src_so268_boxcore"
    assert survivor.abundance_kg_m2 == pytest.approx(19.6)
    # ...but the verdict was not laundered away, and the trace is auditable.
    assert survivor.qa_status == QAStatus.FAIL
    assert not survivor.is_training_eligible()
    assert "escalated" in survivor.notes
    assert "src_manual_review_MASS_000001" in survivor.notes

    # Exactly one row for the event's MASS class — the fail row was absorbed,
    # not left alongside as a second station.
    mass_rows = [
        obs
        for obs in corpus
        if obs.event_id == "SO268/1_24-3" and obs.evidence_class == EvidenceClass.MASS
    ]
    assert len(mass_rows) == 1


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
