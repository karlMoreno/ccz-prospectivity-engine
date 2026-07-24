"""Real RegionalGridAdapter (ADAPTER, E1.1) mapping test against a saved
TS-6-style grid sample. observation_or_prediction is fixed at construction —
GRID rows can never be flagged observed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.regional_grid_adapter import RegionalGridAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = REPO_ROOT / "tests" / "fixtures" / "samples" / "regional_grid_sample.csv"

SHARED_COLUMN_MAP = {
    "station_id": "cell_id",
    "latitude": "lat",
    "longitude": "lon",
    "water_depth_m": "depth_m",
}

EVIDENCE_MAPPINGS = [
    EvidenceClassMapping(
        evidence_class="GRID",
        column_map={"abundance_value_original": "abundance_kg_m2"},
    ),
]


def _make_adapter() -> RegionalGridAdapter:
    return RegionalGridAdapter(
        source_id="src_ts6_grid",
        file_path=SAMPLE_CSV,
        shared_column_map=SHARED_COLUMN_MAP,
        evidence_mappings=EVIDENCE_MAPPINGS,
        is_open=True,
        observation_or_prediction="compiled",
        static_fields={"sample_method": "compiled", "abundance_unit_original": "kg_m2"},
    )


def test_fetch_reads_the_grid_csv() -> None:
    adapter = _make_adapter()
    raw = adapter.fetch()
    assert len(raw) == 3
    assert raw[0]["cell_id"] == "TS6-CELL-101"


def test_adapt_tags_every_row_grid_and_never_observed() -> None:
    adapter = _make_adapter()
    records = adapter.adapt(adapter.fetch())

    assert len(records) == 3
    assert all(r["evidence_class"] == "GRID" for r in records)
    assert all(r["observation_or_prediction"] == "compiled" for r in records)
    assert all(r.get("abundance_kg_m2") is None for r in records)  # no normalization yet
    assert [r["abundance_value_original"] for r in records] == [5.80, 4.90, 6.40]


def test_constructor_rejects_observed_for_grid_sources() -> None:
    with pytest.raises(ValueError, match="never 'observed'"):
        RegionalGridAdapter(
            source_id="src_ts6_grid",
            file_path=SAMPLE_CSV,
            shared_column_map=SHARED_COLUMN_MAP,
            evidence_mappings=EVIDENCE_MAPPINGS,
            is_open=True,
            observation_or_prediction="observed",
        )


def test_adapt_output_validates_against_the_master_schema() -> None:
    adapter = _make_adapter()
    records = adapter.adapt(adapter.fetch())
    for record in records:
        Observation(**record)
