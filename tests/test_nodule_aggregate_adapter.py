"""NoduleAggregateAdapter (ADAPTER, E1.3 + D5 review) — proves dedup rule 3
("individual nodules nested within box-core events: the event is the
sample") by aggregating individual nodule rows up to one MASS + one COUNT
record per event. No network call: `so268_nodules_sample.csv` is a VERBATIM
excerpt of the real PANGAEA.904962 file (see that file's own header comment
for provenance/license), not synthetic data — expected values below are
hand-computed from the real rows it contains. The D5.3 "failed event" case
uses a small inline synthetic header instead, since none of the fixture's
three events is the one real failed box core (SO268/1_12-2, 117 rows — too
many for a small fixture).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.nodule_aggregate_adapter import NoduleAggregateAdapter

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FILE = REPO_ROOT / "tests" / "fixtures" / "samples" / "so268_nodules_sample.csv"

SHARED_COLUMN_MAP = {
    "event_id": "Event",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "sample_datetime_utc": "Date/Time",
}
DIMENSION_COLUMNS = ["Nodule l [mm]", "Nodule w [mm]", "Nodule h [mm]"]


def _build_adapter(dataset_loader=None) -> NoduleAggregateAdapter:
    return NoduleAggregateAdapter(
        source_id="src_so268_nodules",
        file_path=SAMPLE_FILE,
        event_column="Event",
        mass_column_g="Nodule m [g]",
        dimension_columns=DIMENSION_COLUMNS,
        shared_column_map=SHARED_COLUMN_MAP,
        is_open=True,
        static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
        dataset_loader=dataset_loader,
    )


def _records_by_event() -> dict[str, dict[str, dict]]:
    adapter = _build_adapter()
    records = adapter.adapt(adapter.fetch())
    by_event: dict[str, dict[str, dict]] = {}
    for record in records:
        by_event.setdefault(record["event_id"], {})[record["evidence_class"]] = record
    return by_event


# --- A: robust header-block parsing -----------------------------------------


def test_fetch_skips_the_pangaea_metadata_block_via_the_terminator_not_a_line_count() -> None:
    """The fixture's header block is a different length than the real file's
    63 lines -- if this adapter hardcoded skiprows, it would misparse either
    one of them."""
    rows = _build_adapter().fetch()
    assert len(rows) == 21  # 3 annotation/label rows + 18 real nodule rows
    assert all("Event" in row for row in rows)  # real columns, not header noise


# --- rule 3 / C: aggregation + annotation-row exclusion ---------------------


def test_adapt_produces_one_mass_and_one_count_record_per_event_not_per_nodule() -> None:
    by_event = _records_by_event()
    assert set(by_event) == {
        "SO268/1_24-3",
        "SO268/2_95-2",
        "SO268/2_129-1",
        "SO268/2_116-1",
    }
    for classes in by_event.values():
        assert set(classes) == {"MASS", "COUNT"}


def test_adapt_excludes_annotation_rows_from_the_mass_sum_and_count() -> None:
    """SO268/1_24-3's fixture rows include one "Numbers above 1000..."
    labelling-note row with neither mass nor dimensions (C) -- it must not
    be counted as a 6th nodule, nor break the mass sum."""
    by_event = _records_by_event()
    mass = by_event["SO268/1_24-3"]["MASS"]
    count = by_event["SO268/1_24-3"]["COUNT"]
    # real masses: 90 + 220 + 100 + 85 + 60 = 555g = 0.555kg, from 5 nodules
    assert mass["nodule_mass_kg"] == pytest.approx(0.555)
    assert count["nodule_count"] == 5
    assert mass["mean_nodule_mass_g"] == pytest.approx(111.0)  # 555 / 5


def test_real_nodule_with_null_mass_counts_but_contributes_no_mass() -> None:
    """SO268/2_129-1 Sample ID 3: dimensions present (45x40x30mm), mass
    absent, Comment "Broken" -- a real nodule (C's predicate), so it counts
    toward nodule_count, but it must not contribute to the mass sum or be
    treated as 0g (that would silently understate the true mean)."""
    by_event = _records_by_event()
    mass = by_event["SO268/2_129-1"]["MASS"]
    count = by_event["SO268/2_129-1"]["COUNT"]
    # 6 qualifying rows total (Sample 1,2,3,4,5,6); only 5 have mass:
    # 370 + 520 + 110 + 140 + 345 = 1485g = 1.485kg
    assert count["nodule_count"] == 6  # includes the null-mass nodule
    assert mass["nodule_mass_kg"] == pytest.approx(1.485)  # excludes it from the sum
    assert mass["mean_nodule_mass_g"] == pytest.approx(297.0)  # 1485 / 5, NOT / 6


# --- D5.4: Broken/Fragment rows each count as ONE nodule (P3) ---------------


def test_d5_4_fragment_and_broken_rows_each_count_as_one_whole_nodule() -> None:
    """D5.4, named explicitly so a regression that starts excluding damaged
    nodules fails loudly. 231 "Broken" + 93 "Fragment" rows are ~19.7% of the
    real file's nodules; the decision (2026-07-27) is NO special-casing —
    each qualifies under C's predicate (mass OR dimensions present) and
    counts as one nodule, contributing its full recorded mass.

    SO268/2_116-1's fixture rows are Sample 2 (plain, 50g) and Samples 31/47
    (both Comment "Fragment", 130g and 45g). If Fragments were excluded, the
    count would be 1 and the mass 0.050kg."""
    by_event = _records_by_event()
    mass = by_event["SO268/2_116-1"]["MASS"]
    count = by_event["SO268/2_116-1"]["COUNT"]
    assert count["nodule_count"] == 3  # 1 plain + 2 Fragment, none dropped
    assert mass["nodule_mass_kg"] == pytest.approx(0.225)  # 50 + 130 + 45
    assert mass["mean_nodule_mass_g"] == pytest.approx(75.0)  # 225 / 3


def test_d5_4_broken_row_with_mass_contributes_that_mass() -> None:
    """The "Broken" half of D5.4: SO268/2_129-1 Sample 4 is Comment "Broken"
    WITH a recorded 110g mass — it contributes that mass in full (unlike
    Sample 3, which is Broken with NO mass and so counts without contributing;
    see test_real_nodule_with_null_mass_counts_but_contributes_no_mass)."""
    by_event = _records_by_event()
    mass = by_event["SO268/2_129-1"]["MASS"]
    # 1.485kg total includes Sample 4's 110g; excluding Broken-with-mass
    # would give 1.375kg.
    assert mass["nodule_mass_kg"] == pytest.approx(1.485)


# --- D5.1: unweighed sub-5g nodules -----------------------------------------


def test_unweighed_nodules_are_parsed_from_the_comment_and_added_to_count_only() -> None:
    """SO268/2_95-2's fixture rows include "Plus 13 Nodules of less than 5g".
    5 real nodules were weighed (370+240+550+265+20=1445g); the 13 unweighed
    ones are added to nodule_count but NOT to the mass sum, and
    mean_nodule_mass_g divides by the MEASURED count (5), not the total (18)."""
    by_event = _records_by_event()
    mass = by_event["SO268/2_95-2"]["MASS"]
    count = by_event["SO268/2_95-2"]["COUNT"]
    assert count["nodule_count"] == 18  # 5 measured + 13 unweighed
    assert mass["nodule_mass_kg"] == pytest.approx(1.445)
    assert mass["mean_nodule_mass_g"] == pytest.approx(289.0)  # 1445 / 5, NOT / 18


# --- D5.2: bias caveat recorded on the row ----------------------------------


def test_mean_mass_bias_caveat_is_recorded_on_rows_with_unweighed_nodules() -> None:
    by_event = _records_by_event()
    for evidence_class in ("MASS", "COUNT"):
        notes = by_event["SO268/2_95-2"][evidence_class]["notes"]
        assert "excludes 13 unweighed sub-5g nodules" in notes
        assert "72%" in notes  # 13 / 18
        assert "biased high" in notes


def test_no_bias_caveat_when_there_are_no_unweighed_nodules() -> None:
    by_event = _records_by_event()
    assert by_event["SO268/1_24-3"]["MASS"]["notes"] is None
    assert by_event["SO268/2_129-1"]["MASS"]["notes"] is None


# --- D5.3: failed box core ---------------------------------------------------

_SYNTHETIC_HEADER_WITH_FAILED_EVENT = """/* DATA DESCRIPTION:
Event(s):\tSO268/1_12-2 (BC-02) * LATITUDE: 11.931333 * LONGITUDE: -117.027183 * COMMENT: GER Trial; failed
\tSO268/1_15-3 (BC-06) * LATITUDE: 11.929833 * LONGITUDE: -117.025500 * COMMENT: GER Trial; Position USBL
*/
Event\tDate/Time\tLatitude\tLongitude\tElevation [m]\tSample ID\tDepth sed [m]\tDepth top [m]\tDepth bot [m]\tNodule l [mm]\tNodule w [mm]\tNodule h [mm]\tNodule m [g]\tNodule vol [ml]\tComment
SO268/1_12-2\t2019-03-02\t11.9313\t-117.0272\t-4051\t1\t0.000\t\t\t43\t30\t22\t25\t10\t
SO268/1_15-3\t2019-03-04\t11.9298\t-117.0255\t-4090\t1\t0.000\t\t\t50\t30\t20\t30\t10\t
"""


def test_event_flagged_failed_in_the_header_is_ingested_qa_status_flagged() -> None:
    """The "failed" flag lives ONLY in the header's Event(s) block (D5.3) --
    this proves it's actually read from there, not from any data row."""
    adapter = _build_adapter(dataset_loader=lambda: _SYNTHETIC_HEADER_WITH_FAILED_EVENT)
    records = adapter.adapt(adapter.fetch())
    by_event = {}
    for record in records:
        by_event.setdefault(record["event_id"], {})[record["evidence_class"]] = record

    failed = by_event["SO268/1_12-2"]["MASS"]
    assert failed["qa_status"] == "flagged"
    assert "failed" in failed["notes"]

    healthy = by_event["SO268/1_15-3"]["MASS"]
    assert healthy["qa_status"] == "pending"
    assert healthy["notes"] is None


# --- B: column mapping corrections ------------------------------------------


def test_water_depth_m_is_the_negated_elevation() -> None:
    """B: Elevation [m] is negative-down (-4088 = 4088m deep); water_depth_m
    is recorded positive-down."""
    by_event = _records_by_event()
    assert by_event["SO268/1_24-3"]["MASS"]["water_depth_m"] == pytest.approx(4088.0)
    assert by_event["SO268/2_95-2"]["MASS"]["water_depth_m"] == pytest.approx(4120.0)
    assert by_event["SO268/2_129-1"]["MASS"]["water_depth_m"] == pytest.approx(4503.0)


def test_cruise_is_derived_per_row_from_the_event_label_not_a_static_value() -> None:
    """B: the file mixes SO268/1 and SO268/2 -- cruise must reflect the
    actual event, not a hardcoded "SO268"."""
    by_event = _records_by_event()
    assert by_event["SO268/1_24-3"]["MASS"]["cruise"] == "SO268/1"
    assert by_event["SO268/2_95-2"]["MASS"]["cruise"] == "SO268/2"
    assert by_event["SO268/2_129-1"]["MASS"]["cruise"] == "SO268/2"


# --- AR-D03 + schema validity ------------------------------------------------


def test_adapt_never_sets_abundance_kg_m2_itself() -> None:
    """AR-D03: aggregation happens here, but abundance_kg_m2 stays the
    AbundanceNormalizer's job, same as every other adapter."""
    adapter = _build_adapter()
    records = adapter.adapt(adapter.fetch())
    assert all(record.get("abundance_kg_m2") is None for record in records)


def test_adapt_output_validates_against_the_master_schema() -> None:
    adapter = _build_adapter()
    records = adapter.adapt(adapter.fetch())
    for record in records:
        Observation(**record)
