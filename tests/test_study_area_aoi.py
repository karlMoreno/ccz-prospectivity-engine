"""Contract 2's AOI — the CCZ management area (G.2, 2026-08-25).

WHAT THIS MODULE GUARDS, and why each guard exists rather than being obvious:

  * THE EDIT. The committed contract file CANNOT be the publisher's bytes:
    Contract 2 needs `features[0].properties.area_id` (contract_versions.py
    reads it; StudyArea.from_geojson_feature needs area_id + name) and the WFS
    response carries {"dummy": 0, "mrgid": 64222}. So the contract file is
    NECESSARILY an edit, and "only the properties were rewritten" is a claim
    that needs an observer, not a promise. The raw download is preserved
    beside it and `test_the_contract_geometry_is_the_publishers_verbatim`
    compares them.
  * THE HASH. The LEDGER is the hash observer, not the audit (G.3's finding:
    a declaration passes the audit with no hash at all). The ledger row's
    recorded sha256 is checked against the preserved bytes here.
  * THE SLIVER. Kept as published and therefore asserted as published, so a
    library that silently resolves it away fails here.

NOT GUARDED HERE, deliberately: that anything CLIPS on the polygon. Nothing
does (G.2-PRE traced every consumer), and the contracts README no longer says
otherwise.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from shapely.geometry import Point, shape

from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.provenance.contract_versions import contract_versions
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPO_ROOT / "data" / "aoi" / "study_area.geojson"
RAW = REPO_ROOT / "data" / "aoi" / "sources" / "ccz_management_area_mrgid64222.geojson"
QUEUE = REPO_ROOT / "data" / "sources" / "source_queue.yaml"
LEDGER_ROW = "src_ccz_boundary_marineregions"


@pytest.fixture(scope="module")
def contract_doc() -> dict:
    return json.loads(CONTRACT.read_text())


@pytest.fixture(scope="module")
def ledger() -> dict:
    rows = yaml.safe_load(QUEUE.read_text())["sources"]
    (row,) = [r for r in rows if r["source_id"] == LEDGER_ROW]
    return row


def test_the_contract_geometry_is_the_publishers_verbatim(contract_doc: dict) -> None:
    """The one claim the edit rests on: geometry untouched, properties rewritten.

    Compares the PARSED geometry, not bytes — the two files are formatted
    differently on purpose (one is the WFS response, one is a readable contract
    document), so a byte comparison would fail for a reason that is not a
    defect. Python's float repr round-trips exactly, so equal parsed
    coordinates are equal coordinates.

    This separates the two things an edit could do: change the shape (caught
    here) and change the labels (intended). A test that only checked
    `area_id == "ccz_management_area"` would pass on a truncated polygon.
    """
    raw_geometry = json.loads(RAW.read_text())["features"][0]["geometry"]
    assert contract_doc["features"][0]["geometry"] == raw_geometry

    # ...and the properties DID change, or the file would not satisfy Contract 2.
    raw_props = json.loads(RAW.read_text())["features"][0]["properties"]
    contract_props = contract_doc["features"][0]["properties"]
    assert raw_props == {"dummy": 0, "mrgid": 64222}
    assert contract_props["area_id"] == "ccz_management_area"
    assert contract_props["mrgid"] == raw_props["mrgid"]  # the one carried-through label


def test_the_ledger_hash_matches_the_preserved_publisher_bytes(ledger: dict) -> None:
    """The ledger is the hash observer. Recomputed from the bytes, never read
    back from a second record of the same claim."""
    computed = "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest()
    assert ledger["content_hash"] == computed
    assert RAW.stat().st_size == 44_498
    assert ledger["is_open"] is True and ledger["data_origin"] == "LITERATURE"
    # LITERATURE's evidence rule is a citation that LOCATES the value.
    assert "ISBA/17/LTC/7" in ledger["citation"]
    # The staleness fact, recorded so it stays checkable rather than becoming folklore.
    assert ledger["gazetteer_last_edited"] == "2023-03-13"


def test_the_geometry_is_the_published_two_part_multipolygon(contract_doc: dict) -> None:
    """The sliver is KEPT, so it is asserted.

    Its topology is the reason the decision needed making: it touches the main
    polygon at EXACTLY ONE POINT — the main ring's own closure vertex — so it
    is a digitisation spur at the seam, not an island, and a library that
    "cleaned" it would change the AOI silently. Asserting `touches` rather than
    merely `len(geoms) == 2` is what makes this a guard on the SHAPE rather
    than on the part count.
    """
    geom = shape(contract_doc["features"][0]["geometry"])
    assert geom.geom_type == "MultiPolygon" and len(geom.geoms) == 2
    assert geom.is_valid

    sliver, main = geom.geoms[0], geom.geoms[1]
    assert len(sliver.exterior.coords) == 4  # closed ring: 3 distinct vertices
    assert len(main.exterior.coords) == 1629
    assert sliver.touches(main) and not sliver.within(main)
    assert sliver.intersection(main).geom_type == "Point"
    assert main.exterior.coords[0] == sliver.exterior.coords[0]


def test_the_aoi_loads_as_a_study_area_and_identifies_the_contract(
    contract_doc: dict,
) -> None:
    """Both consumers that read the file's PROPERTIES, exercised through the
    real code paths rather than by re-reading the JSON."""
    area = StudyArea.from_geojson_feature(contract_doc["features"][0])
    assert area.area_id == "ccz_management_area"
    assert "Clarion-Clipperton" in area.name
    assert area.shapely_geometry().geom_type == "MultiPolygon"

    versions = contract_versions()
    assert versions["study_area_id"] == "ccz_management_area"
    computed = "sha256:" + hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    assert versions["study_area_content_hash"] == computed


def test_every_corpus_row_falls_inside_the_management_area() -> None:
    """MEASURED, not assumed. The Phase-0 placeholder put 108 of 108 OUTSIDE;
    the real boundary puts 0 outside. A row outside the CCZ management area
    would be a genuine finding about the corpus, so this asserts zero rather
    than a tolerance — and asserts it for the TRAINING set separately, because
    an aggregate over 108 can hide one station."""
    poly = shape(json.loads(CONTRACT.read_text())["features"][0]["geometry"])
    source = CorpusCsvSampleSource(REPO_ROOT / "data" / "corpus" / "master_observations.csv")

    every = source.load_observations()
    training = source.get_training_samples()
    assert len(every) == 108 and len(training) == 35

    for label, rows in (("corpus", every), ("training", training)):
        outside = [
            (obs.observation_id, obs.longitude, obs.latitude)
            for obs in rows
            if not poly.covers(Point(obs.longitude, obs.latitude))
        ]
        assert outside == [], f"{label} rows outside the CCZ management area: {outside}"


def test_the_in_file_declaration_is_reachable_and_carries_its_locator(
    contract_doc: dict,
) -> None:
    """G.2 moved this file's origin from README prose into the file. Assert it
    through the AUDIT'S OWN RESOLVER, not by reading the key here — the claim
    is that the resolver reaches it, and reading the key myself would pass even
    if the resolver did not."""
    from tests.test_data_origin_audit import _in_file_declaration

    declaration = _in_file_declaration(REPO_ROOT, "data/aoi/study_area.geojson")
    assert declaration is not None
    assert declaration.data_origin == "LITERATURE"
    assert "ISBA/17/LTC/7" in (declaration.citation or "")
    assert "MRGID 64222" in (declaration.citation or "")
    # It no longer self-marks as a placeholder, and that must not silently regress.
    assert contract_doc["features"][0]["properties"]["placeholder"] is False
