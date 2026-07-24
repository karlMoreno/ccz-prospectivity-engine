"""PangaeaAdapter — ADAPTER.

Maps a PANGAEA-hosted dataset onto the master-observation schema. Six
source_queue.yaml entries are all this one native FORMAT family —
src_so268_boxcore [01], src_domes_fewkes1980 [02], src_domes_piper1979 [03],
src_domes_sitec_sorem1989 [04], src_so268_nodules [05], src_apei6_cover [12]
— so adding one of them doesn't mean writing six adapter classes (AR-D01:
"adding a source doesn't modify the pipeline"); it means constructing one
more `PangaeaAdapter(...)` with that source's own column map, taken straight
from its source_queue.yaml entry.

`pangaeapy.PanDataSet(doi).data` already turns a DOI into a clean pandas
DataFrame — pangaeapy owns parsing PANGAEA's own tab-file header block. This
adapter's responsibility starts there: `fetch()` calls pangaeapy (lazily
imported, since it's only needed for a real network fetch — tests inject a
`dataset_loader` that returns a small saved sample instead), and `adapt()`
fans each native row out into one RawRecord per evidence class it carries,
via the shared helper in `_column_mapping.py`. No math happens here —
`abundance_kg_m2` is never set; that's AbundanceNormalizer's job (E1.2).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd

from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping, build_records
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter


def _fetch_via_pangaeapy(doi: str) -> pd.DataFrame:
    from pangaeapy import PanDataSet  # lazy: only needed for a real network fetch

    return PanDataSet(doi).data


class PangaeaAdapter(SourceAdapter):
    """Fetches one PANGAEA DOI and fans it out per `evidence_mappings`."""

    def __init__(
        self,
        source_id: str,
        doi: str,
        shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping],
        is_open: bool,
        static_fields: dict[str, Any] | None = None,
        dataset_loader: Callable[[], pd.DataFrame] | None = None,
    ) -> None:
        self.source_id = source_id
        self._doi = doi
        self._shared_column_map = shared_column_map
        self._evidence_mappings = evidence_mappings
        self._is_open = is_open
        self._static_fields = static_fields or {}
        # Defaults to a real pangaeapy fetch; tests inject a loader that
        # returns a small saved sample instead of hitting the network.
        self._dataset_loader = dataset_loader or (lambda: _fetch_via_pangaeapy(self._doi))

    def fetch(self) -> list[dict[str, Any]]:
        frame = self._dataset_loader()
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
