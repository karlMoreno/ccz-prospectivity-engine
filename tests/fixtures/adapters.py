"""Test-only concrete SourceAdapter (ADAPTER) implementations, used to exercise
IngestionPipeline in CI on synthetic data (E0.4/E0.5). These stand in for the
real per-source-family adapters (PANGAEA/Dryad/Mendeley), which are Phase 1
(E1.1) work — kept out of engine/prospectivity so the production package
stays interface-only through Phase 0.

data_origin: AUTHORED (author: unrecorded) — and a MISNOMER, recorded rather
than renamed (P2.0 decision): the `src_synthetic_*` source ids and the
`data/fixtures/native/synthetic_*.csv` files these adapters read are
taxonomy-AUTHORED (hand-typed values, no generator, no seed), not
taxonomy-SYNTHETIC, which requires a deterministic generator with a recorded
seed (only tests/fixtures/rasters.py qualifies). Do not trust the filename.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter
from engine.prospectivity.provenance.origin import AUTHOR_UNRECORDED, DataOrigin

DATA_ORIGIN = DataOrigin.AUTHORED
DATA_AUTHOR = AUTHOR_UNRECORDED


def _parse_float(value: str | None) -> float | None:
    value = (value or "").strip()
    return float(value) if value else None


def _read_native_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


class FixtureBoxcoreAdapter(SourceAdapter):
    """Mimics src_so268_boxcore [01]: one native box-core row fans out into
    MASS + COUNT + COVER observations sharing the same event."""

    source_id = "src_synthetic_boxcore"

    def __init__(self, native_csv_path: Path) -> None:
        self._path = native_csv_path

    def fetch(self) -> list[dict[str, Any]]:
        return _read_native_csv(self._path)

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        records: list[RawRecord] = []
        for row in raw_records:
            common: RawRecord = {
                "source_id": self.source_id,
                "longitude": _parse_float(row["lon"]),
                "latitude": _parse_float(row["lat"]),
                "water_depth_m": _parse_float(row["depth_m"]),
                "cruise": row["cruise"],
                "station_id": row["station"],
                "event_id": row["event"],
                "sample_datetime_utc": f"{row['sample_date']}T00:00:00Z",
                "sample_method": "box_corer",
                "sampled_area_m2": _parse_float(row["box_area_m2"]),
                "observation_or_prediction": "observed",
                "is_open": True,
                "qa_status": "pending",
            }
            records.append(
                {
                    **common,
                    "source_record_id": f"SYN_MASS_{row['event']}",
                    "evidence_class": "MASS",
                    "nodule_mass_kg": _parse_float(row["nodule_mass_kg"]),
                    "abundance_basis": "wet",
                    "mn_pct": _parse_float(row["mn_pct"]),
                    "ni_pct": _parse_float(row["ni_pct"]),
                    "cu_pct": _parse_float(row["cu_pct"]),
                    "co_pct": _parse_float(row["co_pct"]),
                }
            )
            records.append(
                {
                    **common,
                    "source_record_id": f"SYN_COUNT_{row['event']}",
                    "evidence_class": "COUNT",
                    "nodule_count": int(float(row["nodule_count"])) if row["nodule_count"] else None,
                }
            )
            records.append(
                {
                    **common,
                    "source_record_id": f"SYN_COVER_{row['event']}",
                    "evidence_class": "COVER",
                    "visible_cover_percent": _parse_float(row["cover_pct"]),
                }
            )
        return records


class FixtureCoverAdapter(SourceAdapter):
    """Mimics src_apei6_cover [12]: a COVER-only native table."""

    source_id = "src_synthetic_cover"

    def __init__(self, native_csv_path: Path) -> None:
        self._path = native_csv_path

    def fetch(self) -> list[dict[str, Any]]:
        return _read_native_csv(self._path)

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        return [
            {
                "source_id": self.source_id,
                "source_record_id": f"SYN_COVER_{row['transect_id']}",
                "evidence_class": "COVER",
                "longitude": _parse_float(row["lon"]),
                "latitude": _parse_float(row["lat"]),
                "water_depth_m": _parse_float(row["depth_m"]),
                "sample_datetime_utc": f"{row['obs_date']}T00:00:00Z",
                "sample_method": "ofos",
                "visible_cover_percent": _parse_float(row["cover_pct"]),
                "observation_or_prediction": "observed",
                "is_open": True,
                "qa_status": "pending",
            }
            for row in raw_records
        ]


class FixtureGridAdapter(SourceAdapter):
    """Mimics src_ts6_grid [18]: a compiled regional grid — prior/benchmark
    only, never an independent station."""

    source_id = "src_synthetic_grid"

    def __init__(self, native_csv_path: Path) -> None:
        self._path = native_csv_path

    def fetch(self) -> list[dict[str, Any]]:
        return _read_native_csv(self._path)

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        return [
            {
                "source_id": self.source_id,
                "source_record_id": f"SYN_GRID_{row['cell_id']}",
                "evidence_class": "GRID",
                "longitude": _parse_float(row["lon"]),
                "latitude": _parse_float(row["lat"]),
                "water_depth_m": _parse_float(row["depth_m"]),
                "sample_method": "compiled",
                "abundance_value_original": _parse_float(row["grid_kg_m2"]),
                "abundance_unit_original": "kg_m2",
                "observation_or_prediction": "compiled",
                "is_open": True,
                "qa_status": "pending",
            }
            for row in raw_records
        ]
