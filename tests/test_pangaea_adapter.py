"""Real PangaeaAdapter (ADAPTER, E1.1) mapping test — no network call: a
saved sample stands in for pangaeapy.PanDataSet(doi).data, which is exactly
where this adapter's own responsibility starts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.pangaea_adapter import PangaeaAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = REPO_ROOT / "tests" / "fixtures" / "samples" / "pangaea_boxcore_sample.csv"

SHARED_COLUMN_MAP = {
    "event_id": "Event",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "water_depth_m": "Depth water [m]",
    "sample_datetime_utc": "Date/Time",
}

EVIDENCE_MAPPINGS = [
    EvidenceClassMapping(
        evidence_class="MASS",
        column_map={"nodule_mass_kg": "Mass nod wet [kg]"},
    ),
    EvidenceClassMapping(
        evidence_class="COUNT",
        column_map={"nodule_count": "Nod count [#]"},
        presence_column="Nod count [#]",
    ),
    EvidenceClassMapping(
        evidence_class="COVER",
        column_map={"visible_cover_percent": "Cover nod [%]"},
        presence_column="Cover nod [%]",
    ),
]


def _sample_loader() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_CSV)


def _make_adapter() -> PangaeaAdapter:
    return PangaeaAdapter(
        source_id="src_so268_boxcore",
        doi="10.1594/PANGAEA.904967",
        shared_column_map=SHARED_COLUMN_MAP,
        evidence_mappings=EVIDENCE_MAPPINGS,
        is_open=True,
        static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
        dataset_loader=_sample_loader,
    )


def test_fetch_reads_the_injected_sample_without_network() -> None:
    adapter = _make_adapter()
    raw = adapter.fetch()
    assert len(raw) == 4
    assert raw[0]["Event"] == "SO268-1_1-1"


def test_adapt_fans_one_native_row_into_mass_count_cover_records() -> None:
    adapter = _make_adapter()
    records = adapter.adapt(adapter.fetch())

    # 4 native rows x 3 evidence classes (every row has count + cover present)
    assert len(records) == 12
    assert {r["evidence_class"] for r in records} == {"MASS", "COUNT", "COVER"}


def test_adapt_stamps_source_id_and_queue_provenance() -> None:
    adapter = _make_adapter()
    records = adapter.adapt(adapter.fetch())

    for record in records:
        assert record["source_id"] == "src_so268_boxcore"
        assert record["is_open"] is True
        assert record["observation_or_prediction"] == "observed"
        assert record["sample_method"] == "box_corer"
        assert record.get("abundance_kg_m2") is None  # no normalization yet

    mass_records = [r for r in records if r["evidence_class"] == "MASS"]
    assert mass_records and all(r["sampled_area_m2"] == 0.25 for r in mass_records)


def test_adapt_output_validates_against_the_master_schema() -> None:
    adapter = _make_adapter()
    records = adapter.adapt(adapter.fetch())
    for record in records:
        Observation(**record)  # raises if the adapter produced something invalid
