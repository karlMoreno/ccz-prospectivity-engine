"""corpus_builder (E1.3) — the end-to-end wiring test: IngestionPipeline.run()
through all four real adapters (PangaeaAdapter, NoduleAggregateAdapter,
TabularFileAdapter, RegionalGridAdapter), the E1.2 NormalizerRegistry, and the
E1.3 DuplicateStationSpecification, into one corpus. Plus the three required
end-to-end properties: idempotency, flagged/failed retention, and
deterministic (byte-identical, stably-sorted) CSV output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.corpus_builder import build_corpus, write_corpus_csv
from engine.prospectivity.ingestion.dedup_rules import DuplicateStationSpecification
from engine.prospectivity.ingestion.normalizer_registry import build_default_registry
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter


def test_build_corpus_wires_all_four_real_adapters_end_to_end() -> None:
    """D8-F (2026-07-27 review): [01] and [05] describe the SAME 36 real
    events, and [01] is now authoritative for MASS+COUNT (explicit
    quality_grade="A" in BoxcoreSummaryAdapter) -- so every one of [05]'s
    MASS/COUNT rows merges into [01]'s survivor via D1, and
    src_so268_nodules never appears as a standalone source_id in the final
    corpus. Its contribution isn't lost: it's absorbed (mean_nodule_mass_g
    etc. gap-filled) and provenance-linked (rule 2), asserted below."""
    corpus = build_corpus()
    assert len(corpus) > 0

    sources_seen = {obs.source_id for obs in corpus}
    assert sources_seen == {
        "src_so268_boxcore",
        "src_dryad_chamber",
        "src_ts6_grid",
    }

    classes_seen = {obs.evidence_class for obs in corpus}
    # GRADE is deliberately out of scope (no GRADE-carrying source wired; the
    # station join is unresolved geology input) -- everything else appears.
    assert classes_seen == {
        EvidenceClass.MASS,
        EvidenceClass.COUNT,
        EvidenceClass.COVER,
        EvidenceClass.GRID,
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


def test_build_corpus_normalizes_through_the_e12_registry_not_ad_hoc() -> None:
    """abundance_kg_m2 only ever appears where NormalizerRegistry (E1.2) would
    put it -- e.g. src_dryad_chamber's CH-01 (0.85kg / 0.20m2 = 4.25 kg/m2)
    matches MassNormalizer's own formula exactly, proving the real
    end-to-end build actually routes through the registry, not an ad-hoc
    computation. (D8, 2026-07-27 review: this test previously checked a
    barren MASS row from [01]'s old synthetic fixture -- [01] now reads the
    real PANGAEA.904967 file, which has no zero-mass event; the zero-mass
    regression itself is still covered directly in test_normalizers.py.)"""
    corpus = build_corpus()
    chamber_row = next(
        obs
        for obs in corpus
        if obs.source_id == "src_dryad_chamber"
        and obs.evidence_class == EvidenceClass.MASS
        and obs.station_id == "CH-01"
    )
    assert chamber_row.abundance_kg_m2 == pytest.approx(4.25)


def test_idempotency_rerunning_against_the_same_corpus_adds_nothing() -> None:
    corpus: list[Observation] = []
    build_corpus(corpus)
    first_run_len = len(corpus)
    first_run_ids = sorted(obs.source_record_id for obs in corpus)

    build_corpus(corpus)  # same adapters, same shared corpus, run again

    assert len(corpus) == first_run_len
    assert sorted(obs.source_record_id for obs in corpus) == first_run_ids


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
