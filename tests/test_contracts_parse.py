"""Phase 0 done-checklist (docs/contracts/README.md): every contract file
parses, and the AOI geometry loads through the domain type — "study_area
.geojson loads ... in the pipeline (placeholder ok)."
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from engine.prospectivity.domain.study_area import ExclusionZone, StudyArea

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_master_observations_schema_json_parses() -> None:
    schema = json.loads((REPO_ROOT / "docs/contracts/master_observations.schema.json").read_text())
    assert schema["schema_version"] == 4
    assert {f["name"] for f in schema["fields"]} >= {"evidence_class", "abundance_kg_m2"}


def test_covariates_yaml_parses_with_option_a_enabled() -> None:
    covariates = yaml.safe_load((REPO_ROOT / "docs/contracts/covariates.yaml").read_text())
    enabled = {c["name"] for c in covariates["covariates"] if c["enabled"]}
    assert "depth" in enabled and "slope" in enabled
    assert all(not c["enabled"] for c in covariates["candidate_covariates"])


def test_scenarios_yaml_parses_and_is_illustrative_only() -> None:
    scenarios = yaml.safe_load((REPO_ROOT / "data/economics/scenarios.yaml").read_text())
    assert len(scenarios["scenarios"]) == 2
    assert all(s["illustrative_only"] for s in scenarios["scenarios"])


def test_source_queue_yaml_parses_with_open_sources() -> None:
    """Strengthened 2026-07-30: `is_open` was never read, so the name's claim
    ("with open sources") went unverified. Only is_open=true sources may enter
    a published run, so the queue containing at least one is the fact worth
    asserting — and every entry must state the flag explicitly rather than
    leaving it absent."""
    source_queue = yaml.safe_load((REPO_ROOT / "data/sources/source_queue.yaml").read_text())
    sources = source_queue["sources"]
    assert len(sources) > 0
    assert all("source_id" in s for s in sources)
    assert all("is_open" in s for s in sources)
    assert any(s["is_open"] for s in sources)


def test_normalization_yaml_forbids_cover_and_grade_kg_m2() -> None:
    """Renamed 2026-07-30: the body asserts BOTH classes; the old name named
    only COVER."""
    normalization = yaml.safe_load((REPO_ROOT / "data/config/normalization.yaml").read_text())
    assert normalization["normalizers"]["COVER"]["produces_kg_m2"] is False
    assert normalization["normalizers"]["GRADE"]["produces_kg_m2"] is False


def test_ts6_reference_yaml_parses() -> None:
    ts6 = yaml.safe_load((REPO_ROOT / "data/ts6/ts6_reference.yaml").read_text())
    assert ts6["ts6_reference"]["raster"] == "data/ts6/ts6_abundance.tif"


def test_study_area_geojson_loads_through_the_domain_type() -> None:
    feature_collection = json.loads((REPO_ROOT / "data/aoi/study_area.geojson").read_text())
    study_area = StudyArea.from_geojson_feature(feature_collection["features"][0])
    shape = study_area.shapely_geometry()
    assert shape.is_valid
    assert shape.bounds != (0.0, 0.0, 0.0, 0.0)


def test_exclusions_geojson_loads_and_starts_empty() -> None:
    feature_collection = json.loads((REPO_ROOT / "data/aoi/exclusions.geojson").read_text())
    exclusions = [
        ExclusionZone(
            exclusion_id=f["properties"].get("exclusion_id", "unknown"),
            name=f["properties"].get("name", ""),
            kind=f["properties"].get("kind", "other"),
            geometry=f["geometry"],
        )
        for f in feature_collection["features"]
    ]
    assert exclusions == []  # placeholder file starts empty by design
