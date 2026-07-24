"""Shared fan-out helper for the concrete SourceAdapter implementations
(pangaea_adapter.py, tabular_file_adapter.py, regional_grid_adapter.py).

Not one of CLAUDE.md's named seams (SourceAdapter/AbundanceNormalizer/
Specification) — this is private implementation-sharing infrastructure so the
same "one native row -> N evidence-tagged RawRecords" mapping logic isn't
re-derived three times. Every Phase-A source in source_queue.yaml can carry
more than one evidence class from the same native row (e.g. src_so268_boxcore
[01] is MASS+COUNT+COVER from one box-core event) — `build_records` fans a
native row out into one RawRecord per evidence class it actually carries.

No abundance_kg_m2 math happens here — AR-D03 is AbundanceNormalizer's job
(E1.2), not the adapter's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.prospectivity.ingestion.source_adapter import RawRecord


@dataclass(frozen=True)
class EvidenceClassMapping:
    """One evidence class a native row can produce, and how to read it.

    `column_map` maps master-schema field names -> native column names.
    `presence_column`, if set, means: only emit this evidence class for a
    given native row if that native column is present (not None) — e.g. a
    box-core row with no recorded cover reading shouldn't produce an empty
    COVER record. `None` means "always emit" (used for the source's primary
    evidence class).
    """

    evidence_class: str
    column_map: dict[str, str]
    presence_column: str | None = None


def build_records(
    native_rows: list[dict[str, Any]],
    *,
    source_id: str,
    shared_column_map: dict[str, str],
    evidence_mappings: list[EvidenceClassMapping],
    is_open: bool,
    observation_or_prediction: str,
    static_fields: dict[str, Any] | None = None,
) -> list[RawRecord]:
    """Fan each native row out into one RawRecord per evidence class it carries.

    Field values come from three places, most specific wins: the evidence
    mapping's own `column_map`, then `shared_column_map` (fields common to
    every evidence class from this row — lon/lat/depth/date/...), then
    `static_fields` (constants from source_queue.yaml, e.g. a fixed box-core
    `sampled_area_m2`).
    """

    static_fields = static_fields or {}
    records: list[RawRecord] = []
    for row_index, row in enumerate(native_rows):
        for mapping in evidence_mappings:
            if mapping.presence_column is not None and row.get(mapping.presence_column) is None:
                continue
            record: RawRecord = {
                "source_id": source_id,
                "source_record_id": f"{source_id}_{mapping.evidence_class}_{row_index:06d}",
                "evidence_class": mapping.evidence_class,
                "observation_or_prediction": observation_or_prediction,
                "is_open": is_open,
                "qa_status": "pending",
            }
            record.update(static_fields)
            for master_field, native_column in shared_column_map.items():
                record[master_field] = row.get(native_column)
            for master_field, native_column in mapping.column_map.items():
                record[master_field] = row.get(native_column)
            records.append(record)
    return records
