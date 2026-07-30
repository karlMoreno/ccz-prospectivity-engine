"""NoduleAggregateAdapter — ADAPTER.

For src_so268_nodules [05]: individual nodule measurements that must be
aggregated up to the box-core EVENT before they mean anything as a mass
observation (source_queue.yaml: "aggregate nodules to event -> event mass;
kg/m2 = event_mass / 0.25; also yields mean_nodule_mass_g"; "TRAIN_AGGREGATE").
This is dedup rule 3 ("individual nodules are nested within box-core events:
the event is the sample") — implemented here, in the adapter, rather than as
a dedup Specification, per the engineer of record's decision (2026-07-27
E1.3 review): collapsing many nodule-level rows into one event-level row is
a many-to-one reduction, not a fit for Specification's boolean
is_satisfied_by(one_observation) contract. By the time an aggregated row
reaches dedup, it is already one row per event — there is nothing left for
dedup to nest.

A genuinely different native-to-master-schema mapping shape than
PangaeaAdapter's 1-row-fan-out-to-N-evidence-classes ([01]'s box-core rows
are already one row per event): here each native row is one NODULE, and many
rows share one event. AR-D01 ("one SourceAdapter per source family") argues
for a new adapter class rather than bolting a group-by mode onto
PangaeaAdapter's generic fan-out.

D5 (2026-07-27 review) wired the REAL PANGAEA.904962 file
(SO268-bc-nodules-PANGAEA-904962.tab: a raw PANGAEA tab-export, not a
DataFrame from pangaeapy's parsed API) and fixed several wrong assumptions
the first pass made against synthetic data:

    raw file text
        │  A: split on the "*/" metadata-block terminator (detected, not a
        │     hardcoded skiprows -- other PANGAEA exports have different
        │     header lengths)
        ▼
    header block ──► parse_event_comments()  (D5.3: an event's "failed"
        │                                       recovery is flagged ONLY
        │                                       here, never in a data row)
        ▼
    data block (tab-delimited) ──► one row per NODULE
        │  group by Event
        ▼
    per event:
      qualifying_rows = rows with non-null mass OR non-null dimensions   (C:
        excludes pure free-text annotation/labelling rows, which have
        neither -- a row with dims but no mass, e.g. a "Broken" nodule that
        was measured but not weighed, still counts as a qualifying nodule)
      weighed_count    = qualifying_rows with non-null mass
      unweighed_n      = sum of N parsed from "Plus N nodules of less than
                          5g" annotation comments                          (D5.1)
      nodule_count       = len(qualifying_rows) + unweighed_n
      total_mass_kg      = sum(mass for qualifying_rows with mass) / 1000
      mean_nodule_mass_g = total_mass_kg*1000 / weighed_count   (NOT
                            nodule_count -- see D5.1: the two denominators
                            diverge on purpose once unweighed nodules are
                            counted but not massed)
      water_depth_m       = -Elevation [m]           (B: elevation is
                             negative-down; comment explains the sign flip)
      cruise               = Event.split("_", 1)[0]   (B: "SO268/1_12-2" ->
                             "SO268/1"; the file mixes SO268/1 and SO268/2)

AR-D03 still holds: this adapter never writes abundance_kg_m2 itself. It
produces nodule_mass_kg + sampled_area_m2 (MASS) and nodule_count +
nodule_density_m2 + mean_nodule_mass_g (COUNT) — E1.2's MassNormalizer and
CountNormalizer, unchanged, compute abundance_kg_m2 from these downstream,
exactly like every other adapter's output.

D5.2 (mean_nodule_mass_g is biased high — sub-5g nodules were never weighed,
so the measured mean excludes a measurement-floor-truncated tail) and D5.3
(a failed box core is not a valid abundance measurement) are recorded as
row-level `notes` and, for D5.3, `qa_status="flagged"` — confirmed with the
engineer of record, 2026-07-27: caveats travel with the row, not just in
documentation. D5.4 (231 "Broken" + 93 "Fragment" rows): counted as 1 nodule
each, same as any other qualifying row — no special-casing needed, since
they already carry valid mass and are indistinguishable from any other
qualifying row under the "non-null mass or dimensions" predicate.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from engine.prospectivity.ingestion._pangaea_tab_format import (
    FAILED_RE,
    parse_event_comments,
    split_header_and_data,
)
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter

# D5.1: "Plus 13 Nodules of less than 5g" / "Plus 11 nodules of less than 5g"
# (case varies) -- free-text counts of nodules under the equipment's 5g
# measurement floor, never weighed or individually rowed.
_UNWEIGHED_COMMENT_RE = re.compile(
    r"plus\s+(\d+)\s+nodules?\s+of\s+less\s+than\s+5\s*g", re.IGNORECASE
)


class NoduleAggregateAdapter(SourceAdapter):
    """Reads a raw PANGAEA tab-export of individual-nodule measurements and
    aggregates them to one MASS + one COUNT record per box-core event."""

    def __init__(
        self,
        source_id: str,
        file_path: Path,
        event_column: str,
        mass_column_g: str,
        dimension_columns: list[str],
        shared_column_map: dict[str, str],
        is_open: bool,
        static_fields: dict[str, Any] | None = None,
        dataset_loader: Callable[[], str] | None = None,
    ) -> None:
        self.source_id = source_id
        self._event_column = event_column
        self._mass_column_g = mass_column_g
        self._dimension_columns = dimension_columns
        self._shared_column_map = shared_column_map
        self._is_open = is_open
        self._static_fields = static_fields or {}
        # Injection seam (kept, per D5 instruction) so tests stay offline: a
        # test supplies a small excerpt's raw text directly instead of
        # reading the real multi-hundred-KB file from disk.
        self._dataset_loader = dataset_loader or (lambda: file_path.read_text())
        # Public so the provenance manifest can hash the real input file — see
        # provenance/corpus_manifest.py::_adapter_input_paths.
        self.input_path = file_path

    def fetch(self) -> list[dict[str, Any]]:
        header_text, data_text = split_header_and_data(self._dataset_loader())
        event_comments = parse_event_comments(header_text)

        frame = pd.read_csv(StringIO(data_text), sep="\t")
        frame = frame.astype(object).where(pd.notnull(frame), None)
        rows = frame.to_dict(orient="records")
        for row in rows:
            row["_event_comment"] = event_comments.get(row.get(self._event_column))
        return rows

    def _is_nodule_row(self, row: dict[str, Any]) -> bool:
        """C (2026-07-27 review): a row is a real nodule only if it carries a
        non-null mass or non-null dimensions -- excludes free-text
        annotation rows ("Plus N nodules...") and sample-labelling notes,
        neither of which have either. A "Broken" nodule with dimensions but
        no recorded mass still qualifies (it was measured, just not weighed)."""
        if row.get(self._mass_column_g) is not None:
            return True
        return any(row.get(column) is not None for column in self._dimension_columns)

    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]:
        groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for row in raw_records:
            groups[row[self._event_column]].append(row)

        area_m2 = self._static_fields.get("sampled_area_m2")
        records: list[RawRecord] = []
        for index, event_key in enumerate(sorted(groups, key=str)):
            group = groups[event_key]

            qualifying_rows = [row for row in group if self._is_nodule_row(row)]
            weighed_masses_g = [
                float(row[self._mass_column_g])
                for row in qualifying_rows
                if row.get(self._mass_column_g) is not None
            ]
            weighed_count = len(weighed_masses_g)
            total_mass_g = sum(weighed_masses_g)

            # D5.1: nodules noted but never individually rowed or weighed
            # ("Plus N nodules of less than 5g") still count toward
            # nodule_count -- but NOT toward weighed_count, since their mass
            # is genuinely unknown, not zero.
            unweighed_n = 0
            for row in group:
                comment = row.get("Comment")
                if comment:
                    match = _UNWEIGHED_COMMENT_RE.search(comment)
                    if match:
                        unweighed_n += int(match.group(1))
            nodule_count = len(qualifying_rows) + unweighed_n

            total_mass_kg = total_mass_g / 1000.0
            mean_nodule_mass_g = (total_mass_g / weighed_count) if weighed_count else None

            shared_fields = {
                master_field: group[0].get(native_column)
                for master_field, native_column in self._shared_column_map.items()
            }

            # B: Elevation [m] is negative-down (e.g. -4051 = 4051m deep);
            # water_depth_m is recorded positive-down (Contract 1).
            elevation = group[0].get("Elevation [m]")
            water_depth_m = -float(elevation) if elevation is not None else None

            # B: cruise is not a single static value -- this file mixes
            # SO268/1 and SO268/2, encoded as the event label's prefix
            # (PANGAEA's own "<cruise>_<station>-<cast>" convention).
            cruise = str(event_key).split("_", 1)[0]

            # D5.3: a failed box core's recovery is not a valid abundance
            # measurement -- flagged, never silently dropped or silently
            # trusted (E1.2's screening precedent).
            event_comment = group[0].get("_event_comment") or ""
            is_failed = bool(FAILED_RE.search(event_comment))
            qa_status = "flagged" if is_failed else "pending"

            notes_parts: list[str] = []
            if is_failed:
                notes_parts.append(
                    f'source header flags this event "{event_comment}" (failed recovery)'
                )
            if unweighed_n:
                # D5.2: mean_nodule_mass_g is biased high whenever nodules
                # were noted but never weighed -- record the caveat with the
                # row, not just in documentation.
                fraction = unweighed_n / nodule_count if nodule_count else 0.0
                notes_parts.append(
                    f"mean_nodule_mass_g excludes {unweighed_n} unweighed sub-5g nodules "
                    f"({fraction:.0%} of event); biased high"
                )
            notes = "; ".join(notes_parts) or None

            # D8-C (2026-07-27 review): document the aggregation itself, not
            # just abundance_kg_m2's later derivation (E1.2's normalizers own
            # that one, downstream, and record it in this same field — see
            # mass_normalizer.py / count_normalizer.py, which now APPEND to
            # an existing derivation_formula rather than overwrite it, so
            # this note survives normalization). mean_nodule_mass_g divides
            # by weighed_count, not nodule_count -- and whenever unweighed
            # nodules exist, the mass sum is measured-only, so it is very
            # slightly low by construction (D5.1/D5.2).
            derivation_formula = (
                "nodule_mass_kg = sum(measured nodule masses); "
                "mean_nodule_mass_g = nodule_mass_kg*1000 / weighed_count (not nodule_count)"
            )
            if unweighed_n:
                derivation_formula += (
                    f"; mass sum excludes {unweighed_n} unweighed sub-5g nodules "
                    "(measured-only, so total is very slightly low by construction)"
                )

            base: RawRecord = {
                "source_id": self.source_id,
                "observation_or_prediction": "observed",
                "is_open": self._is_open,
                "qa_status": qa_status,
                "cruise": cruise,
                "water_depth_m": water_depth_m,
                "notes": notes,
                "derivation_formula": derivation_formula,
                **shared_fields,
                **self._static_fields,
            }

            records.append(
                {
                    **base,
                    "source_record_id": f"{self.source_id}_MASS_{index:06d}",
                    "evidence_class": "MASS",
                    "nodule_mass_kg": total_mass_kg,
                    "mean_nodule_mass_g": mean_nodule_mass_g,
                    # P2 (2026-07-27 audit follow-up): explicit "B", not
                    # MassNormalizer's usual "A" default. This is a
                    # SCIENTIFIC ranking, not a tie-break convenience --
                    # [05]'s total is a sum of MEASURED nodules only. It
                    # structurally excludes every "Plus N nodules of less
                    # than 5g" nodule the authors never weighed (D5.1: up to
                    # 60% of an event's population), and each measured
                    # component is itself quantized to the equipment's 5g
                    # floor. [01]'s "Nodules m [kg] (total)" is the authors'
                    # own COMPLETE per-event total, covering every nodule,
                    # weighed or not. [05]'s MASS genuinely is the less
                    # complete measurement of the same physical quantity --
                    # "B" says that plainly. That this also makes [01] win
                    # the D1 merge deterministically (see
                    # boxcore_summary_adapter.py's matching comment) is a
                    # CONSEQUENCE of the grade being correct, not the reason
                    # for setting it.
                    "quality_grade": "B",
                }
            )
            records.append(
                {
                    **base,
                    "source_record_id": f"{self.source_id}_COUNT_{index:06d}",
                    "evidence_class": "COUNT",
                    "nodule_count": nodule_count,
                    "nodule_density_m2": (nodule_count / area_m2) if area_m2 else None,
                    "mean_nodule_mass_g": mean_nodule_mass_g,
                }
            )
        return records
