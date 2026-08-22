"""E4.1 commit 1 — Contract 4's loader (three states, each by name), the
illustrative_only / data_origin consistency rule, the difference pairs, the
exclusion set, and the per-reason watermark verdict's DISCRIMINATION.

STATED FIRST: every Contract 4 number is an AUTHORED placeholder. Nothing
here measures an economy; it measures that the loader and the verdict keep
the placeholders' states apart.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from engine.prospectivity.domain.results import EconomicScenarioResult, RunManifest
from engine.prospectivity.economics.contract import (
    GRADE_METRICS,
    ExclusionSet,
    ScenarioConfig,
    difference_pairs,
    grade_metric,
    grade_units,
    load_exclusions,
    load_scenarios_yaml,
    scenario,
    scenarios,
    spatial_filters,
)
from engine.prospectivity.economics.watermark import (
    CHECKPOINT_1,
    CHECKPOINT_4,
    WatermarkVerdict,
    economic_watermark_verdict,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _contract() -> dict:
    return copy.deepcopy(load_scenarios_yaml())


# ───────────────────────────────────────── the file as it is


def test_contract_4_as_shipped_two_illustrative_scenarios_one_pair_abundance_metric_authored() -> None:
    """E4.0 §1, pinned: the structure the loader was written against."""
    contract = load_scenarios_yaml()
    assert contract["config_version"] == 3 and contract["data_origin"] == "AUTHORED"
    loaded = scenarios()
    assert [s.name for s in loaded] == ["MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"]
    assert [s.cutoff_value for s in loaded] == [10.0, 5.5]
    assert all(s.illustrative_only for s in loaded)
    assert all(s.cutoff.data_origin == "AUTHORED" and s.cutoff.author == "unrecorded" for s in loaded)
    assert [s.index for s in loaded] == [0, 1] and all(len(s.caveats) == 3 for s in loaded)
    assert grade_metric().value == "abundance" and grade_metric().data_origin == "AUTHORED"
    assert grade_units().value == "kg_m2"
    assert spatial_filters().max_slope_degrees.value == "6.0" and spatial_filters().apply_exclusions is True
    assert difference_pairs() == (("MARKET_STANDARD", "STRATEGIC_SUBSIDIZED"),)
    assert scenario("STRATEGIC_SUBSIDIZED").cutoff_value == 5.5


# ───────────────────────────────── three states, each BY NAME


def test_an_absent_cutoff_raises_naming_the_scenario_and_the_structural_gap() -> None:
    contract = _contract()
    del contract["scenarios"][1]["cutoff_value"]
    with pytest.raises(ValueError, match=r"scenario 'STRATEGIC_SUBSIDIZED' has no cutoff_value field — a missing field is not an explicitly-null"):
        scenarios(contract)


def test_a_null_cutoff_raises_naming_the_unfilled_value_and_isaac() -> None:
    contract = _contract()
    contract["scenarios"][0]["cutoff_value"] = None
    with pytest.raises(ValueError, match=r"scenario 'MARKET_STANDARD' declares cutoff_value explicitly NULL .*\[GEOLOGY — ISAAC\]"):
        scenarios(contract)


def test_a_populated_cutoff_returns_the_value_with_its_declared_origin_in_one_call() -> None:
    market = scenario("MARKET_STANDARD")
    assert (market.cutoff_value, market.cutoff.data_origin, market.cutoff.author) == (10.0, "AUTHORED", "unrecorded")


def test_the_other_accessors_keep_absent_and_null_apart_by_name() -> None:
    for field, accessor in (("grade_metric", grade_metric), ("grade_units", grade_units), ("spatial_filters", spatial_filters), ("difference_pairs", difference_pairs)):
        contract = _contract()
        del contract[field]
        with pytest.raises(ValueError, match=rf"has no {field} field — a missing field"):
            accessor(contract)
    for field, accessor in (("grade_metric", grade_metric), ("grade_units", grade_units), ("spatial_filters", spatial_filters)):
        contract = _contract()
        contract[field] = None
        with pytest.raises(ValueError, match=rf"{field} explicitly NULL"):
            accessor(contract)
    contract = _contract()
    contract["spatial_filters"]["max_slope_degrees"] = None
    with pytest.raises(ValueError, match=r"max_slope_degrees is explicitly NULL .*\[GEOLOGY — ISAAC\]"):
        spatial_filters(contract)


def test_an_unknown_grade_metric_and_an_undeclared_file_origin_are_refused() -> None:
    contract = _contract()
    contract["grade_metric"] = "tonnes"
    with pytest.raises(ValueError, match=r"grade_metric 'tonnes' is not one of \['abundance', 'dollar_value'\]"):
        grade_metric(contract)
    assert GRADE_METRICS == ("abundance", "dollar_value")
    contract = _contract()
    del contract["data_origin"]
    with pytest.raises(ValueError, match=r"no file-level data_origin"):
        scenarios(contract)


# ─────────────── the flag and the origin: one direction contradicts


def test_illustrative_only_false_on_an_authored_contract_is_refused_as_two_declarations_that_contradict() -> None:
    """THE RESOLUTION of E4.0's illustrative_only question: the flag says
    whether a value is a STAND-IN, the origin says HOW it came to exist.
    `false` on an AUTHORED file claims a defensible number with no source —
    refused by name. The other direction (a LITERATURE value still flagged
    illustrative) is conservative and allowed — the separating case."""
    contract = _contract()
    contract["scenarios"][0]["illustrative_only"] = False
    with pytest.raises(ValueError, match=r"illustrative_only: false while the contract's data_origin is AUTHORED — a NON-illustrative cutoff"):
        scenarios(contract)
    conservative = _contract()
    conservative["data_origin"] = "LITERATURE"
    assert all(s.illustrative_only for s in scenarios(conservative))  # allowed, and still illustrative
    real = _contract()
    real["data_origin"] = "LITERATURE"
    real["scenarios"][0]["illustrative_only"] = False
    assert scenarios(real)[0].illustrative_only is False  # the lifted state, reachable only with a real origin


def test_an_absent_or_null_illustrative_flag_is_refused_never_inferred() -> None:
    contract = _contract()
    del contract["scenarios"][1]["illustrative_only"]
    with pytest.raises(ValueError, match=r"scenario 'STRATEGIC_SUBSIDIZED' has no illustrative_only field"):
        scenarios(contract)
    contract = _contract()
    contract["scenarios"][1]["illustrative_only"] = None
    with pytest.raises(ValueError, match=r"declares illustrative_only explicitly NULL"):
        scenarios(contract)


def test_a_difference_pair_must_name_two_declared_scenarios() -> None:
    contract = _contract()
    contract["difference_pairs"] = [["MARKET_STANDARD", "UTOPIAN"]]
    with pytest.raises(ValueError, match=r"does not name two declared scenarios"):
        difference_pairs(contract)


# ─────────────────────────────────────────── the exclusion set


def test_the_exclusion_set_is_authored_and_empty_and_a_non_empty_one_is_visible(tmp_path: Path) -> None:
    """"Starts EMPTY on purpose" — asserted, never assumed, so the day it is
    not empty is a visible change (E4.1 prompt)."""
    exclusions = load_exclusions()
    assert isinstance(exclusions, ExclusionSet)
    assert (exclusions.data_origin, exclusions.author, exclusions.features, exclusions.is_empty) == ("AUTHORED", "unrecorded", (), True)
    raw = json.loads((REPO_ROOT / "data" / "aoi" / "exclusions.geojson").read_text())
    raw["features"] = [{"type": "Feature", "properties": {"exclusion_id": "x"}, "geometry": None}]
    path = tmp_path / "exclusions.geojson"
    path.write_text(json.dumps(raw))
    assert load_exclusions(path).is_empty is False
    del raw["data_origin"]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match=r"no data_origin — declaration or nothing"):
        load_exclusions(path)


# ─────────────────────────────── the verdict DISCRIMINATES


def _scenario(flag: bool) -> ScenarioConfig:
    from engine.prospectivity.model_config import DeclaredField

    return ScenarioConfig(
        name="MARKET_STANDARD", index=0, description="", illustrative_only=flag,
        cutoff=DeclaredField(value="10.0", data_origin="LITERATURE" if not flag else "AUTHORED", author="x"),
        cost_model={}, caveats=(),
    )


def test_today_both_reasons_are_unlifted_and_each_cites_its_declared_cause() -> None:
    verdict = economic_watermark_verdict("SYNTHETIC", _scenario(True))
    assert [r.reason for r in verdict.reasons] == ["terrain", "economic_parameters"]
    assert [r.lifted for r in verdict.reasons] == [False, False] and verdict.watermarked
    assert verdict.reasons[0].cause == "feature stack dem_data_origin = 'SYNTHETIC'" and verdict.reasons[0].lifted_by == CHECKPOINT_1
    assert verdict.reasons[1].cause == "scenarios.yaml scenarios[0] (MARKET_STANDARD) illustrative_only = True" and verdict.reasons[1].lifted_by == CHECKPOINT_4
    assert "2 independent reason(s)" in verdict.text()


def test_the_verdict_discriminates_one_lifted_and_one_unlifted_after_either_checkpoint() -> None:
    """THE PROPERTY that makes the per-reason verdict more than decoration
    (Decision 1): a Checkpoint-1 world (MEASURED DEM, placeholder economics)
    and a Checkpoint-4 world (synthetic DEM, real economics) each produce
    EXACTLY one lifted reason — different ones — and the lattice would have
    said AUTHORED for both."""
    after_cp1 = economic_watermark_verdict("MEASURED", _scenario(True))
    after_cp4 = economic_watermark_verdict("SYNTHETIC", _scenario(False))
    assert [r.lifted for r in after_cp1.reasons] == [True, False] and after_cp1.watermarked
    assert [r.lifted for r in after_cp4.reasons] == [False, True] and after_cp4.watermarked
    assert "1 independent reason(s)" in after_cp1.text() and "economic_parameters" in after_cp1.text()
    assert "terrain" in after_cp4.text() and "economic_parameters" not in after_cp4.text()
    both = economic_watermark_verdict("MEASURED", _scenario(False))
    assert [r.lifted for r in both.reasons] == [True, True] and not both.watermarked and both.text() is None
    record = both.to_record()
    assert record["watermarked"] is False and [r["lifted"] for r in record["reasons"]] == [True, True]


def test_an_undeclared_dem_origin_is_an_unlifted_reason_never_a_lifted_one() -> None:
    """Absence of proof watermarks (P2.0d-3)."""
    verdict = economic_watermark_verdict(None, _scenario(False))
    assert [r.lifted for r in verdict.reasons] == [False, True]
    assert verdict.reasons[0].cause == "feature stack dem_data_origin = None"
    derived = economic_watermark_verdict("DERIVED", _scenario(False))
    assert derived.reasons[0].lifted is False  # only MEASURED lifts the terrain reason


# ───────────────────────────────────── the 2B shape, recorded


def test_the_result_shape_carries_no_copied_flag_and_the_manifest_is_at_schema_version_2() -> None:
    fields = set(EconomicScenarioResult.model_fields)
    assert "illustrative_only" not in fields and "minable_footprint_path" not in fields
    assert {"cutoff", "confidence_levels", "footprints", "uncertainty_semantics", "data_origin", "watermark"} <= fields
    assert RunManifest.SCHEMA_VERSION == 2 and RunManifest.model_fields["economic_differences"].default is None
