"""BoxcoreSummaryAdapter (ADAPTER, D8 review) — proves [01]'s three
same-named "Nodules" PANGAEA parameters are matched by full header string,
not a substring, and the D8-B per-row derivations (negated elevation,
derived cruise, re-applied failed-event flag, measurement-derived COVER
note). No network call: a small inline synthetic PANGAEA-shaped text stands
in for the real file for the disambiguation/derivation unit tests; a real
2-row excerpt is used for the "matches the actual file" sanity check.
"""

from __future__ import annotations

import pytest

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.boxcore_summary_adapter import BoxcoreSummaryAdapter

SHARED_COLUMN_MAP = {
    "event_id": "Event",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "water_depth_m": "Elevation [m]",
    "sample_datetime_utc": "Date/Time",
}
EVIDENCE_MAPPINGS = [
    EvidenceClassMapping(
        evidence_class="MASS", column_map={"nodule_mass_kg": "Nodules m [kg] (total)"}
    ),
    EvidenceClassMapping(
        evidence_class="COUNT",
        column_map={"nodule_count": "Nodules [#]"},
        presence_column="Nodules [#]",
    ),
    EvidenceClassMapping(
        evidence_class="COVER",
        column_map={"visible_cover_percent": "Nodules [%] (seafloor coverage by nodules)"},
        presence_column="Nodules [%] (seafloor coverage by nodules)",
    ),
]

# Deliberately distinct values for all three "Nodules" columns (count=100,
# buried=16 [unused], mass=3.4, cover=43) -- a substring-matching bug (e.g.
# picking "Nodules [#] (buried)" for COUNT, or "Nodules [%] ..." for MASS)
# would produce a wrong, immediately-assertable number, not a coincidental
# pass.
_SYNTHETIC_TEXT = """/* DATA DESCRIPTION:
Event(s):\tSO268/1_12-2 (BC-02) * LATITUDE: 11.931333 * LONGITUDE: -117.027183 * COMMENT: GER Trial; not failed here
*/
Event\tDate/Time\tLatitude\tLongitude\tElevation [m]\tDepth sed [m]\tNodules [#]\tNodules [#] (buried)\tNodules size [cm**2] (median nodule size)\tNodules m [kg] (total)\tNodules [%] (seafloor coverage by nodules)
SO268/1_12-2\t2019-03-02\t11.9313\t-117.0272\t-4051\t0\t100\t16\t9.2\t3.4\t43
"""


def _build_adapter(dataset_loader=None) -> BoxcoreSummaryAdapter:
    return BoxcoreSummaryAdapter(
        source_id="src_so268_boxcore",
        file_path=None,
        shared_column_map=SHARED_COLUMN_MAP,
        evidence_mappings=EVIDENCE_MAPPINGS,
        is_open=True,
        static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
        dataset_loader=dataset_loader or (lambda: _SYNTHETIC_TEXT),
    )


def _by_class(records: list[dict]) -> dict[str, dict]:
    return {r["evidence_class"]: r for r in records}


# --- A: the three "Nodules" columns are disambiguated correctly ------------


def test_three_nodules_columns_are_matched_by_full_header_string_not_substring() -> None:
    adapter = _build_adapter()
    records = _by_class(adapter.adapt(adapter.fetch()))
    assert records["COUNT"]["nodule_count"] == 100  # NOT 16 (the buried subset)
    assert records["MASS"]["nodule_mass_kg"] == pytest.approx(3.4)  # NOT 43 (cover %)
    assert records["COVER"]["visible_cover_percent"] == pytest.approx(43)  # NOT 3.4 (mass)


# --- B: per-row derivations --------------------------------------------------


def test_water_depth_m_is_the_negated_elevation() -> None:
    adapter = _build_adapter()
    records = _by_class(adapter.adapt(adapter.fetch()))
    assert records["MASS"]["water_depth_m"] == pytest.approx(4051.0)


def test_cruise_is_derived_from_the_event_label_prefix() -> None:
    adapter = _build_adapter()
    records = _by_class(adapter.adapt(adapter.fetch()))
    assert records["MASS"]["cruise"] == "SO268/1"


def test_cover_notes_record_it_is_measurement_derived_not_image_derived() -> None:
    """B: [01]'s COVER is the summed ellipsoidal footprint of surface nodules
    / corer area -- still COVER, still never abundance_kg_m2, but a
    different derivation than an image/OFOS-based cover estimate."""
    adapter = _build_adapter()
    records = _by_class(adapter.adapt(adapter.fetch()))
    cover_notes = records["COVER"]["notes"]
    assert "measurement-derived" in cover_notes
    assert "not image-derived" in cover_notes
    # the hard rule is unchanged regardless of derivation:
    assert records["COVER"].get("abundance_kg_m2") is None


def test_every_adapted_record_validates_against_the_master_schema() -> None:
    """Renamed 2026-07-30 (test-name audit). The old name,
    `test_cover_hard_rule_still_holds_through_full_schema_validation`, claimed
    a COVER-specific check; the body has no assert at all and validates EVERY
    record, relying on Observation's constructor to raise. That is a real
    check, just a broader and less specific one than the name implied. The
    COVER rule itself is asserted directly on the adapter's dict output in
    `test_cover_notes_record_it_is_measurement_derived_not_image_derived`
    above, and against the corpus bytes in `test_corpus_invariants.py`."""
    adapter = _build_adapter()
    records = adapter.adapt(adapter.fetch())
    for record in records:
        Observation(**record)  # raises if the adapter produced something invalid


# --- D5.3 flag, re-applied independently for [01] ---------------------------

_SYNTHETIC_TEXT_FAILED = """/* DATA DESCRIPTION:
Event(s):\tSO268/1_12-2 (BC-02) * LATITUDE: 11.931333 * LONGITUDE: -117.027183 * COMMENT: GER Trial; failed
\tSO268/1_15-3 (BC-06) * LATITUDE: 11.929833 * LONGITUDE: -117.025500 * COMMENT: GER Trial; Position USBL
*/
Event\tDate/Time\tLatitude\tLongitude\tElevation [m]\tDepth sed [m]\tNodules [#]\tNodules [#] (buried)\tNodules size [cm**2] (median nodule size)\tNodules m [kg] (total)\tNodules [%] (seafloor coverage by nodules)
SO268/1_12-2\t2019-03-02\t11.9313\t-117.0272\t-4051\t0\t117\t16\t9.2\t3.4\t43
SO268/1_15-3\t2019-03-04\t11.9298\t-117.0255\t-4090\t0\t78\t0\t15.0\t3.8\t51
"""


def test_failed_event_flag_is_detected_independently_from_this_files_own_header() -> None:
    """[01]'s own header carries the same 'failed' COMMENT [05]'s does for
    SO268/1_12-2 -- this must be detected here too, not only inherited via a
    later dedup merge with [05] (qa_status is never null, so merge's
    gap-fill would not propagate it from a dropped row)."""
    adapter = _build_adapter(dataset_loader=lambda: _SYNTHETIC_TEXT_FAILED)
    records = adapter.adapt(adapter.fetch())
    by_event: dict[str, dict[str, dict]] = {}
    for r in records:
        by_event.setdefault(r["event_id"], {})[r["evidence_class"]] = r

    failed_mass = by_event["SO268/1_12-2"]["MASS"]
    assert failed_mass["qa_status"] == "flagged"
    assert "failed" in failed_mass["notes"]

    healthy_mass = by_event["SO268/1_15-3"]["MASS"]
    assert healthy_mass["qa_status"] == "pending"
