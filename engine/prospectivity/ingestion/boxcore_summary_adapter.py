"""BoxcoreSummaryAdapter — ADAPTER.

For src_so268_boxcore [01]: PANGAEA.904967, the authors' own published
per-event AGGREGATE (one row per box-core event already — unlike [05]'s
individual-nodule rows, no grouping needed). A thin subclass of
PangaeaAdapter (D8, 2026-07-27 review), not a bare `PangaeaAdapter(...)`
construction like E1.1's other PANGAEA sources, because this file needs two
things `_column_mapping.build_records()` has no hook for:

  1. Reading the REAL raw tab-export directly (same PANGAEA metadata-block
     shape as [05]; `_pangaea_tab_format.py`'s parsing is shared with
     nodule_aggregate_adapter.py rather than duplicated) instead of a
     pre-parsed DataFrame from pangaeapy.
  2. Two per-row derivations B (2026-07-27 review) requires that are pure
     column renames for every OTHER real adapter but need actual
     computation here: water_depth_m = -Elevation [m] (negative-down in the
     file); cruise = event label prefix (this file mixes SO268/1 and
     SO268/2, same as [05]).

It also re-applies the SAME failed-event flag D5.3 established for [05]:
this file's own header carries the identical "GER Trial; failed" COMMENT for
SO268/1_12-2. Independent of whichever row a later dedup merge (D1) keeps as
survivor, the flag must not depend on which of [01]/[05] happened to detect
it — both must carry it from the start (E1.2's qa_status precedence rule:
_merge() gap-fills nulls only, and qa_status is never null, so it does NOT
propagate from a dropped row to a surviving one across a merge).

B also applies to COVER: [01]'s coverage percentage is NOT image-derived
(unlike src_apei6_cover [12] or src_amon2016_frames [11]) — its abstract
defines it as the summed ellipsoidal footprint of surface-visible nodules
divided by the 2500cm^2 corer area, i.e. measurement-derived from the same
physical recovery as the mass/count. Still COVER evidence class, still never
converted to abundance_kg_m2 (the hard rule is unchanged) — but the
different derivation (and different error characteristics) is recorded in
`notes` so a later reader doesn't assume it's an image/OFOS-style estimate.

    Nodules [#]                              -> nodule_count      (COUNT)
    Nodules [#] (buried)                     -> NOT mapped (unused subset)
    Nodules [%] (seafloor coverage...)        -> visible_cover_percent (COVER)
    Nodules m [kg] (total)                   -> nodule_mass_kg    (MASS)

The PANGAEA parameter list names three DIFFERENT columns "Nodules" —
disambiguated only by bracketed unit + trailing comment
(`_column_mapping.EvidenceClassMapping.column_map` matches on the FULL
header string, so this is correct by construction, not by luck — but see
test_boxcore_summary_adapter.py's dedicated disambiguation test, since a
silent mismatch here would put a cover percentage into a mass field).
"""

from __future__ import annotations

from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion._pangaea_tab_format import (
    FAILED_RE,
    parse_event_comments,
    split_header_and_data,
)
from engine.prospectivity.ingestion.pangaea_adapter import PangaeaAdapter
from engine.prospectivity.ingestion.source_adapter import RawRecord


class BoxcoreSummaryAdapter(PangaeaAdapter):
    """PangaeaAdapter's generic fan-out, plus [01]-specific per-row
    derivations and the shared failed-event flag."""

    def __init__(
        self,
        source_id: str,
        file_path: Path,
        shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping],
        is_open: bool,
        static_fields: dict[str, Any] | None = None,
        dataset_loader: Callable[[], str] | None = None,
    ) -> None:
        # Injection seam (offline tests): a test supplies a small excerpt's
        # raw text directly instead of reading the real file from disk.
        self._raw_text_loader = dataset_loader or (lambda: file_path.read_text())
        self._event_comments: dict[str, str] = {}
        super().__init__(
            source_id=source_id,
            doi="10.1594/PANGAEA.904967",
            shared_column_map=shared_column_map,
            evidence_mappings=evidence_mappings,
            is_open=is_open,
            static_fields=static_fields,
            dataset_loader=self._load_dataframe,
        )

    def _load_dataframe(self) -> pd.DataFrame:
        header_text, data_text = split_header_and_data(self._raw_text_loader())
        self._event_comments = parse_event_comments(header_text)
        return pd.read_csv(StringIO(data_text), sep="\t")

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        records = super().adapt(raw_records)
        for record in records:
            # B: Elevation [m] is negative-down; water_depth_m is
            # recorded positive-down (Contract 1) -- shared_column_map maps
            # water_depth_m straight from Elevation [m] (unnegated); negate
            # it here, same convention as nodule_aggregate_adapter.py.
            if record.get("water_depth_m") is not None:
                record["water_depth_m"] = -record["water_depth_m"]

            # B: cruise mixes SO268/1 and SO268/2 -- derive from the event
            # label prefix rather than a static value.
            event_id = record.get("event_id")
            if event_id:
                record["cruise"] = str(event_id).split("_", 1)[0]

            # D5.3, re-applied here: this file's own header carries the same
            # "failed" COMMENT for SO268/1_12-2 as [05]'s does. Flagging
            # independently (not relying on a later dedup merge to inherit
            # it from [05]) matters because _merge()'s gap-fill only fills
            # NULL fields, and qa_status is never null on a valid row -- so
            # if only one of [01]/[05] flagged it, whichever survives a
            # merge could silently lose the flag.
            comment = self._event_comments.get(event_id, "")
            if FAILED_RE.search(comment):
                record["qa_status"] = "flagged"
                note = f'source header flags this event "{comment}" (failed recovery)'
                record["notes"] = f"{record['notes']}; {note}" if record.get("notes") else note

            # B: [01]'s COVER is measurement-derived (summed ellipsoidal
            # nodule footprints / corer area), not image-derived like
            # src_apei6_cover [12] or src_amon2016_frames [11] -- the two
            # have different error characteristics, so record which this is.
            if record.get("evidence_class") == "COVER":
                cover_note = (
                    "measurement-derived cover: summed ellipsoidal footprint of "
                    "surface-visible nodules / corer area (not image-derived)"
                )
                record["notes"] = (
                    f"{record['notes']}; {cover_note}" if record.get("notes") else cover_note
                )

            # F (2026-07-27 review, confirmed with the engineer of record):
            # [01] is authoritative for MASS and COUNT over [05] in D1's
            # merge -- it is the authors' own published per-event aggregate,
            # and its count already includes nodules [05] never weighed for
            # most events (D8-D reconciliation: 31/36 exact). Without this,
            # MassNormalizer/CountNormalizer's own quality_grade defaults
            # decide by accident (MASS ties at "A" and falls to whichever
            # adapter ran first; COUNT has no default at all unless
            # mean_nodule_mass_g is present, which only [05] sets, so [05]
            # would otherwise win COUNT outright with no one having decided
            # that). Explicit "A" makes [01] win deterministically,
            # independent of adapter run order. [05]'s mean_nodule_mass_g
            # still flows into the surviving [01] row via D1's existing
            # gap-fill merge -- unaffected by this change.
            if record.get("evidence_class") in ("MASS", "COUNT"):
                record["quality_grade"] = "A"
        return records
