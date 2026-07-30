"""TabularFileAdapter — ADAPTER.

Maps a Dryad or Mendeley workbook onto the master-observation schema:
src_dryad_chamber [06] and src_gsr_mendeley_cover [14]. Different native
format than PANGAEA's (a plain xlsx/csv file, no DOI-resolving client
library needed — read directly with pandas), so a different adapter class
per AR-D01 ("one SourceAdapter per source family"); it shares
PangaeaAdapter's fan-out mechanics via `_column_mapping.build_records()`
rather than re-deriving them, since both families ultimately turn native
rows into evidence-tagged RawRecords the same way.

No math happens here — `abundance_kg_m2` is never set; that's
AbundanceNormalizer's job (E1.2). `fetch()` only reads the file and
normalizes NaN -> None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping, build_records
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter


class TabularFileAdapter(SourceAdapter):
    """Reads a local xlsx/csv workbook and fans it out per `evidence_mappings`."""

    def __init__(
        self,
        source_id: str,
        file_path: Path,
        shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping],
        is_open: bool,
        static_fields: dict[str, Any] | None = None,
        sheet_name: str | int = 0,
    ) -> None:
        self.source_id = source_id
        self._file_path = file_path
        # Public so the provenance manifest can hash the real input file — see
        # provenance/corpus_manifest.py::_adapter_input_paths.
        self.input_path = file_path
        self._shared_column_map = shared_column_map
        self._evidence_mappings = evidence_mappings
        self._is_open = is_open
        self._static_fields = static_fields or {}
        self._sheet_name = sheet_name

    def fetch(self) -> list[dict[str, Any]]:
        if self._file_path.suffix.lower() in {".xlsx", ".xls"}:
            frame = pd.read_excel(self._file_path, sheet_name=self._sheet_name)
        else:
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
            observation_or_prediction="observed",
            static_fields=self._static_fields,
        )
