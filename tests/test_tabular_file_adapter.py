"""Real TabularFileAdapter (ADAPTER, E1.1) mapping test: a saved Dryad-style
csv sample, plus an xlsx generated at test time (no committed binary fixture),
proving both branches of fetch().
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.tabular_file_adapter import TabularFileAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = REPO_ROOT / "tests" / "fixtures" / "samples" / "dryad_chamber_sample.csv"

SHARED_COLUMN_MAP = {
    "station_id": "chamber_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "water_depth_m": "water_depth_m",
    "sample_datetime_utc": "deploy_date",
    "sampled_area_m2": "chamber_footprint_m2",
}

EVIDENCE_MAPPINGS = [
    EvidenceClassMapping(
        evidence_class="MASS",
        column_map={"nodule_mass_kg": "nodule_mass_kg"},
    ),
]


def _make_adapter(path: Path) -> TabularFileAdapter:
    return TabularFileAdapter(
        source_id="src_dryad_chamber",
        file_path=path,
        shared_column_map=SHARED_COLUMN_MAP,
        evidence_mappings=EVIDENCE_MAPPINGS,
        is_open=True,
        static_fields={"sample_method": "chamber"},
    )


def test_fetch_reads_a_csv_workbook() -> None:
    adapter = _make_adapter(SAMPLE_CSV)
    raw = adapter.fetch()
    assert len(raw) == 3
    assert raw[0]["chamber_id"] == "CH-01"


def test_fetch_reads_an_xlsx_workbook(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "dryad_chamber_sample.xlsx"
    pd.read_csv(SAMPLE_CSV).to_excel(xlsx_path, index=False)

    adapter = _make_adapter(xlsx_path)
    raw = adapter.fetch()

    assert len(raw) == 3
    assert raw[0]["chamber_id"] == "CH-01"


def test_adapt_maps_chamber_footprint_as_sampled_area_per_row() -> None:
    """PER ROW is the claim, so the fixture now carries three DISTINCT
    footprints (0.20 / 0.25 / 0.15). Strengthened 2026-07-30: every row
    previously shared 0.20, so an adapter that hardcoded the value and never
    read `chamber_footprint_m2` would have passed."""
    adapter = _make_adapter(SAMPLE_CSV)
    records = adapter.adapt(adapter.fetch())

    assert len(records) == 3
    assert all(r["evidence_class"] == "MASS" for r in records)
    by_station = {r["station_id"]: r for r in records}
    assert by_station["CH-01"]["sampled_area_m2"] == 0.20
    assert by_station["CH-02"]["sampled_area_m2"] == 0.25
    assert by_station["CH-03"]["sampled_area_m2"] == 0.15
    assert all(r.get("abundance_kg_m2") is None for r in records)  # no normalization yet


def test_adapt_output_validates_against_the_master_schema() -> None:
    adapter = _make_adapter(SAMPLE_CSV)
    records = adapter.adapt(adapter.fetch())
    for record in records:
        Observation(**record)
