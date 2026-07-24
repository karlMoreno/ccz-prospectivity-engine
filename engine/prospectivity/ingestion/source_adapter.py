"""SourceAdapter — ADAPTER.

One SourceAdapter per Phase-A source-family (source_queue.yaml, Contract 5)
maps that family's native format (a PANGAEA tab-file, a Dryad workbook, a
Mendeley CSV, ...) onto the master-observation schema (Contract 1). Adding a
new source means writing one new SourceAdapter subclass; nothing else in the
ingestion pipeline changes (AR-D01). Track E writes and tests every adapter
against SYNTHETIC data that matches a source family's shape; Track G's real
downloads drop into the same adapter unchanged.

    native format A ──► SourceAdapter A ──┐
    native format B ──► SourceAdapter B ──┼──► RawRecord (uniform shape) ──► AbundanceNormalizer
    native format C ──► SourceAdapter C ──┘

RawRecord is deliberately looser than Observation: an adapter's job is only
"get this source's fields into a common shape with the right names," not
"compute abundance_kg_m2" — that normalization step belongs to
AbundanceNormalizer (Strategy), one seam downstream.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

RawRecord = dict[str, Any]
"""A source record after adapting, before normalization: master-schema field
names, but abundance_kg_m2 not yet computed and QA/dedup not yet applied."""


class SourceAdapter(ABC):
    """Adapts one Phase-A source family's native format to RawRecord shape."""

    source_id: str

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """Retrieve the source's native records (a download, a file read, ...)."""
        raise NotImplementedError

    @abstractmethod
    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        """Map native records onto master-observation field names.

        Must record `source_id`, `source_record_id`, `evidence_class`, and the
        raw abundance/count/cover fields as reported — but must NOT populate
        `abundance_kg_m2` itself (AbundanceNormalizer's job, AR-D03).
        """
        raise NotImplementedError
