"""RegionalGridAdapter — ADAPTER.

Maps a compiled regional grid/points table onto the master-observation
schema: src_ts6_grid [18] and src_washburn2021_grid [19]. Both are GRID
evidence — compiled/interpolated priors, never independent training
stations (normalization.yaml's GRID rule; CLAUDE.md "GRID is a prior/
benchmark, never a training station"). Unlike PangaeaAdapter/
TabularFileAdapter, `observation_or_prediction` is a caller-supplied
constant fixed at construction time, not read off a native column — a
compiled grid is compiled/interpolated by definition, so the constructor
refuses "observed" outright rather than trusting the config to get it right.
This is belt-and-suspenders with the Observation validator, which already
rejects a GRID row flagged "observed" — the adapter just never gives it the
chance to reach that far.

No math happens here — `abundance_kg_m2` is never set; that's
AbundanceNormalizer's job (E1.2). The raw grid value stays in
`abundance_value_original` until then.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping, build_records
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter

_NON_OBSERVED_VALUES = {"compiled", "interpolated", "modelled"}


class RegionalGridAdapter(SourceAdapter):
    """Reads a local grid/points CSV and fans it out per `evidence_mappings`."""

    def __init__(
        self,
        source_id: str,
        file_path: Path,
        shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping],
        is_open: bool,
        observation_or_prediction: str,
        static_fields: dict[str, Any] | None = None,
    ) -> None:
        if observation_or_prediction not in _NON_OBSERVED_VALUES:
            raise ValueError(
                f"RegionalGridAdapter sources are compiled/interpolated priors — "
                f"observation_or_prediction must be one of {sorted(_NON_OBSERVED_VALUES)}, "
                f"got {observation_or_prediction!r} (never 'observed'; see normalization.yaml "
                f"GRID rule)."
            )
        self.source_id = source_id
        self._file_path = file_path
        self._shared_column_map = shared_column_map
        self._evidence_mappings = evidence_mappings
        self._is_open = is_open
        self._observation_or_prediction = observation_or_prediction
        self._static_fields = static_fields or {}

    def fetch(self) -> list[dict[str, Any]]:
        frame = pd.read_csv(self._file_path)
        frame = frame.astype(object).where(pd.notnull(frame), None)
        return frame.to_dict(orient="records")

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        return build_records(
            raw_records,
            source_id=self.source_id,
            shared_column_map=self._shared_column_map,
            evidence_mappings=self._evidence_mappings,
            is_open=self._is_open,
            observation_or_prediction=self._observation_or_prediction,
            static_fields=self._static_fields,
        )
