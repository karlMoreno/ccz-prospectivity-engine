"""E4.1 commit 2 — CutoffEconomicModel: the known answer, the refusals, the
origin, determinism, the difference, and the measured fractions on today's
surfaces (stated in advance; not findings).

THE KNOWN-ANSWER FIXTURE, and what it separates (CLAUDE.md rule 4):
a 2 x 4 grid, cutoff 10.0, max slope 6°.

    mu     [[ 9.0, 10.0, 11.0, 12.0],     sd   [[0.5, 0.5, 0.5, 3.0],
            [10.5, 13.0,  8.0, 20.0]]           [1.0, 2.0, 1.0, 1.0]]
    slope  [[ 1,    1,    1,    1  ],     area [[1.0, 1.0, 1.0, 1.0],
            [ 7,    1,    1,    1  ]]           [2.0, 2.0, 2.0, 2.0]]
    predictable: all but [1, 3]  (masked — its mu of 20 must never count)

  * [0, 1] sits EXACTLY at the cutoff: separates ">=" from ">".
  * [1, 0] clears the cutoff and FAILS the slope: separates the two filters.
  * z = 1 drops [0, 1] (9.5), [0, 3] (9.0) and [1, 0] (9.5, already out):
    4 minable at z = 0 -> 2 at z = 1 — separates the levels.
  * row areas 1.0 vs 2.0: the z = 0 area is 5.0, not 4 x anything —
    separates "area summed over cells" from "count x constant".
  * the strategic cutoff 5.5 admits [0, 0] and [1, 2] too (6 cells): the
    difference is exactly those two, area 3.0.
"""

from __future__ import annotations

import copy
import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.economics.contract import (
    ExclusionSet,
    ScenarioConfig,
    load_exclusions,
    load_scenarios_yaml,
    scenario,
    scenarios,
)
from engine.prospectivity.economics.cutoff import SLOPE_RESOLUTION_NOTE, CutoffEconomicModel
from engine.prospectivity.economics.model import EconomicInputs, FootprintLevel, ScenarioFootprints
from engine.prospectivity.model_config import DeclaredField
from engine.prospectivity.surfaces.builder import SurfaceResult
from engine.prospectivity.surfaces.grid import PredictionGrid

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ro(a: np.ndarray) -> np.ndarray:
    a = np.ascontiguousarray(a)
    a.flags.writeable = False
    return a


def _grid() -> PredictionGrid:
    depth = np.full((2, 4), -4100.0)
    slope = np.array([[1.0, 1.0, 1.0, 1.0], [7.0, 1.0, 1.0, 1.0]])
    predictable = np.ones((2, 4), dtype=bool)
    predictable[1, 3] = False
    return PredictionGrid(
        transform=(0.1, 0.0, -126.5, 0.0, -0.1, 14.7), crs="EPSG:4326", width=4, height=2,
        res_x_deg=0.1, res_y_deg=0.1, layer_names=("depth", "slope"),
        covariates=_ro(np.stack([depth, slope])), predictable=_ro(predictable),
        dem_content_hash="sha256:dem", stack_content_hash="sha256:stack", stack_dir="<fixture>",
    )


def _surface(name: str = "fixture") -> SurfaceResult:
    mu = np.array([[9.0, 10.0, 11.0, 12.0], [10.5, 13.0, 8.0, 20.0]])
    sd = np.array([[0.5, 0.5, 0.5, 3.0], [1.0, 2.0, 1.0, 1.0]])
    mu = mu.copy(); sd = sd.copy()
    mu[1, 3] = np.nan; sd[1, 3] = np.nan  # masked cells are NaN in both arrays (the builder's rule)
    return SurfaceResult(
        estimator_name=name, input_kind="covariates", uncertainty_method="fixture_sd",
        uncertainty_semantics="a fixture sd: a stated reading, not a moment", determinism_basis="hand-built",
        mu=_ro(mu), sd=_ro(sd), n_predicted=7, n_masked=1, n_sd_zero=0, provenance={},
    )


AREA = np.array([[1.0] * 4, [2.0] * 4])


def _inputs(dem_origin: str | None = "SYNTHETIC", surfaces=None) -> EconomicInputs:
    return EconomicInputs(
        surfaces=surfaces or {"fixture": _surface()}, grid=_grid(), cell_area_m2=_ro(AREA),
        dem_data_origin=dem_origin, surface_data_origin="SYNTHETIC",
    )


def _scenario(name: str, cutoff: float, index: int = 0, flag: bool = True, origin: str = "AUTHORED") -> ScenarioConfig:
    return ScenarioConfig(
        name=name, index=index, description="fixture", illustrative_only=flag,
        cutoff=DeclaredField(value=str(cutoff), data_origin=origin, author="x"), cost_model={}, caveats=("c",),
    )


EMPTY = ExclusionSet(path="exclusions.geojson", data_origin="AUTHORED", author="x", features=())
MARKET = _scenario("MARKET_STANDARD", 10.0)
STRATEGIC = _scenario("STRATEGIC_SUBSIDIZED", 5.5, index=1)


def _model(**kw) -> CutoffEconomicModel:
    return CutoffEconomicModel(**{"contract": load_scenarios_yaml(), "exclusions": EMPTY, **kw})


# ─────────────────────────────────────────────── the known answer


def test_the_known_answer_at_z0_and_z1_with_the_cutoff_the_slope_the_mask_and_the_area_each_separated() -> None:
    fp = _model().apply(_inputs(), MARKET)
    z0, z1 = fp.levels["fixture"][0.0], fp.levels["fixture"][1.0]
    expected_z0 = np.array([[False, True, True, True], [False, True, False, False]])
    expected_z1 = np.array([[False, False, True, False], [False, True, False, False]])
    np.testing.assert_array_equal(z0.minable, expected_z0)
    np.testing.assert_array_equal(z1.minable, expected_z1)
    assert (z0.n_minable, z0.n_predictable, z0.fraction_of_predictable, z0.area_m2) == (4, 7, 4 / 7, 5.0)
    assert (z0.n_failing_cutoff, z0.n_failing_slope, z0.n_excluded) == (2, 1, 0)
    assert (z1.n_minable, z1.area_m2, z1.n_failing_cutoff) == (2, 3.0, 5)
    assert fp.confidence_levels == (0.0, 1.0) and fp.grade_metric == "abundance"
    assert fp.uncertainty_semantics == {"fixture": "a fixture sd: a stated reading, not a moment"}
    assert fp.filters["max_slope_degrees"]["value"] == 6.0 and fp.filters["max_slope_degrees"]["note"] == SLOPE_RESOLUTION_NOTE
    assert fp.filters["exclusions"]["n_features"] == 0


def test_the_difference_is_exactly_the_cells_the_lower_cutoff_admits() -> None:
    model = _model()
    a, b = model.apply(_inputs(), MARKET), model.apply(_inputs(), STRATEGIC)
    assert b.levels["fixture"][0.0].n_minable == 6
    diff = model.difference(a, b)
    expected = np.array([[True, False, False, False], [False, False, True, False]])
    np.testing.assert_array_equal(diff.levels["fixture"][0.0].minable, expected)
    assert (diff.levels["fixture"][0.0].n_minable, diff.levels["fixture"][0.0].area_m2) == (2, 3.0)
    assert diff.pair == ("MARKET_STANDARD", "STRATEGIC_SUBSIDIZED") and diff.data_origin == "AUTHORED"
    record = diff.record()
    assert record.meaning == "cells minable under STRATEGIC_SUBSIDIZED and NOT under MARKET_STANDARD"
    assert record.footprints["fixture"]["0.0"]["n_minable"] == 2


# ───────────────────────────────────────────────── the refusals


def test_dollar_value_is_refused_by_name_not_computed_as_zeros() -> None:
    contract = copy.deepcopy(load_scenarios_yaml())
    contract["grade_metric"] = "dollar_value"
    with pytest.raises(ValueError, match=r"grade_metric 'dollar_value' cannot be computed .* ZERO GRADE rows .* refusing rather than emitting zeros"):
        CutoffEconomicModel(contract=contract, exclusions=EMPTY).apply(_inputs(), MARKET)


def test_a_non_empty_exclusion_set_is_refused_by_name_so_the_first_polygon_is_visible() -> None:
    populated = ExclusionSet(path="exclusions.geojson", data_origin="AUTHORED", author="x", features=({"type": "Feature"},))
    with pytest.raises(ValueError, match=r"carries 1 exclusion feature\(s\) and rasterising exclusion polygons .* is not built"):
        _model(exclusions=populated).apply(_inputs(), MARKET)
    assert load_exclusions().is_empty  # …and the real file is empty, so the production path computes


def test_a_stack_without_a_slope_layer_and_mismatched_areas_are_refused_by_name() -> None:
    grid = dataclasses.replace(_grid(), layer_names=("depth", "aspect"))
    with pytest.raises(ValueError, match=r"has no 'slope' layer"):
        _model().apply(dataclasses.replace(_inputs(), grid=grid), MARKET)
    with pytest.raises(ValueError, match=r"cell_area_m2 has shape \(1, 1\)"):
        _model().apply(dataclasses.replace(_inputs(), cell_area_m2=np.ones((1, 1))), MARKET)


def test_a_null_required_parameter_is_refused_by_the_loader_before_the_model_runs() -> None:
    contract = copy.deepcopy(load_scenarios_yaml())
    contract["spatial_filters"]["max_slope_degrees"] = None
    with pytest.raises(ValueError, match=r"max_slope_degrees is explicitly NULL"):
        CutoffEconomicModel(contract=contract, exclusions=EMPTY).apply(_inputs(), MARKET)
    with pytest.raises(ValueError, match=r"must include z = 0"):
        CutoffEconomicModel(confidence_levels=(1.0,))


# ───────────────────────────── origin, verdict, determinism


def test_the_computed_origin_is_authored_and_derived_never_declared() -> None:
    """combine_origins over the surface's origin and the cutoff's declared
    origin: AUTHORED today; a LITERATURE cutoff on a SYNTHETIC surface is
    SYNTHETIC (least real wins) — the laundering direction, separated."""
    fp = _model().apply(_inputs(), MARKET)
    assert fp.data_origin == "AUTHORED"
    literature = _model().apply(_inputs(), _scenario("MARKET_STANDARD", 10.0, origin="LITERATURE"))
    assert literature.data_origin == "SYNTHETIC"
    assert fp.record().data_origin == "AUTHORED" and fp.record().cutoff == {"value": 10.0, "units": "kg_m2", "data_origin": "AUTHORED", "author": "x"}


def test_the_watermark_verdict_lists_both_reasons_and_a_lifted_dem_lifts_exactly_one() -> None:
    today = _model().apply(_inputs("SYNTHETIC"), MARKET)
    assert [r.lifted for r in today.watermark.reasons] == [False, False]
    after_cp1 = _model().apply(_inputs("MEASURED"), MARKET)
    assert [r.lifted for r in after_cp1.watermark.reasons] == [True, False]
    assert after_cp1.data_origin == "AUTHORED"  # the lattice cannot see the change; the verdict can
    rec = after_cp1.record()
    assert rec.watermark["watermarked"] is True and [r["lifted"] for r in rec.watermark["reasons"]] == [True, False]


def test_determinism_full_state_over_dataclasses_fields() -> None:
    a = _model().apply(_inputs(), MARKET)
    b = _model().apply(_inputs(), MARKET)
    for f in dataclasses.fields(ScenarioFootprints):
        x, y = getattr(a, f.name), getattr(b, f.name)
        if f.name == "levels":
            for est in x:
                for z in x[est]:
                    for lf in dataclasses.fields(FootprintLevel):
                        vx, vy = getattr(x[est][z], lf.name), getattr(y[est][z], lf.name)
                        assert (np.array_equal(vx, vy) if isinstance(vx, np.ndarray) else vx == vy), (est, z, lf.name)
        elif isinstance(x, np.ndarray):
            assert np.array_equal(x, y), f.name
        else:
            assert x == y, f.name
    assert a.record() == b.record() and json.dumps(a.record().model_dump()) == json.dumps(b.record().model_dump())


# ─────────────── today's surfaces: the fractions, stated in advance


@pytest.fixture(scope="module")
def real(surface_assembly) -> dict:
    from engine.prospectivity.features.bundle import cell_areas_m2
    from engine.prospectivity.features.dem_grid import DemGrid

    dem_grid = DemGrid.load(Path(surface_assembly["stack_manifest"]["dem_path"]))
    inputs = EconomicInputs(
        surfaces=surface_assembly["surfaces"], grid=surface_assembly["grid"], cell_area_m2=cell_areas_m2(dem_grid),
        dem_data_origin=surface_assembly["stack_manifest"]["dem_data_origin"], surface_data_origin="SYNTHETIC",
    )
    model = CutoffEconomicModel()
    market, strategic = model.apply(inputs, scenario("MARKET_STANDARD")), model.apply(inputs, scenario("STRATEGIC_SUBSIDIZED"))
    return {"market": market, "strategic": strategic, "difference": model.difference(market, strategic), "inputs": inputs}


def test_on_todays_surfaces_both_scenarios_are_the_whole_predictable_domain_and_the_difference_is_empty(real: dict) -> None:
    """STATED IN ADVANCE (E4.0 §4; the E4.1 prompt): kriging is within 0.5
    kg/m² of the 19.5 training mean over 99.62% of the domain and RF's
    plateaus lie in [15.1, 21.7] — both above cutoffs of 10.0 and 5.5 — so
    the footprint is the WHOLE predictable domain under both scenarios at
    z = 0 AND at z = 1, and the difference is EMPTY. That is a property of
    the CUTOFFS' RELATION TO THE TRAINING MEAN, not of the seafloor. The
    measured sameness is asserted WITH its reason so a change to the
    placeholders becomes visible here: Contract 4's two scenarios bracket
    nothing on these surfaces (BACKLOG, for G4.1)."""
    for name in ("market", "strategic"):
        for estimator, by_z in real[name].levels.items():
            for z, level in by_z.items():
                assert (level.n_minable, level.n_predictable, level.fraction_of_predictable) == (2880, 2880, 1.0), (name, estimator, z)
                assert level.n_failing_cutoff == 0 and level.n_failing_slope == 0
    assert {est: {z: lvl.n_minable for z, lvl in by_z.items()} for est, by_z in real["difference"].levels.items()} == {
        est: {0.0: 0, 1.0: 0} for est in ("mean_baseline", "ordinary_kriging", "random_forest")
    }
    # the slope filter removed nothing at 11-km cells: the max regional gradient on this grid is far below 6°
    slope = real["inputs"].grid.covariates[real["inputs"].grid.layer_names.index("slope")]
    assert np.nanmax(slope) < 6.0
    # and the area is the sum of the cell areas over the domain, in m², not a count
    assert real["market"].levels["ordinary_kriging"][0.0].area_m2 == pytest.approx(float(real["inputs"].cell_area_m2[real["inputs"].grid.predictable].sum()))
    assert real["market"].levels["ordinary_kriging"][0.0].area_m2 > 1e11  # ~2,880 cells of ~1.2e8 m² each


def test_the_real_contract_scenarios_differ_only_in_cutoff_and_that_difference_does_not_reach_the_footprint(real: dict) -> None:
    market, strategic = scenarios()
    assert (market.cutoff_value, strategic.cutoff_value) == (10.0, 5.5) and market.cutoff_value != strategic.cutoff_value
    assert real["market"].record().cutoff["value"] != real["strategic"].record().cutoff["value"]
    assert {e: l[0.0].n_minable for e, l in real["market"].levels.items()} == {e: l[0.0].n_minable for e, l in real["strategic"].levels.items()}
