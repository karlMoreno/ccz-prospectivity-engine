"""E4.2 commit 2 — the scenario difference map: the three-state encoding,
the meaning in the tags, the consistency check against the difference's own
footprints, and the measured zero with its reason.

THE DEGENERACY WARNING, taken literally. On today's surfaces every
footprint is uniformly true, so every difference is uniformly "both" — a
writer that IGNORED its inputs and wrote a constant raster would satisfy
any real-data assertion. The CONSTRUCTED fixture (E4.1's 2×4 grid under
MARKET 10.0 and STRATEGIC 5.5, both orders) produces ALL FOUR codes plus
undefined, and its docstring names what each separates:

    MARKET  z=0 minable:   [[0,1,1,1],[0,1,0,-]]     (4; [1,0] fails the slope)
    STRATEGIC z=0 minable: [[1,1,1,1],[0,1,1,-]]     (6)
    (MARKET, STRATEGIC):   [[2,1,1,1],[0,1,2,NaN]]   two "only_b", one "neither", four "both"
    (STRATEGIC, MARKET):   [[3,1,1,1],[0,1,3,NaN]]   the same two cells become "only_a"

  * "computes the set difference" from "returns empty": codes 2 appear;
  * "b − a" from "a − b": the reversed pair codes 3, not 2;
  * "neither" from "undefined": [1,0] is 0.0, [1,3] is NaN;
  * "both" from "either": [0,1] (exactly at the market cutoff) is 1, not 2.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.economics.cutoff import CutoffEconomicModel
from engine.prospectivity.economics.writer import (
    ASSOCIATION_NAME,
    DIFFERENCE_CODES,
    DIFFERENCE_ENCODING,
    DIFFERENCE_MEANING,
    difference_name,
    encode_difference,
    write_difference,
    write_footprints,
)
from engine.prospectivity.provenance.contract_versions import file_sha256
from tests.test_economic_cutoff import EMPTY, MARKET, STRATEGIC, _grid, _inputs, _surface
from tests.test_economic_writer import real, verdict  # noqa: F401  (fixtures)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _model():
    from engine.prospectivity.economics.contract import load_scenarios_yaml

    return CutoffEconomicModel(contract=load_scenarios_yaml(), exclusions=EMPTY)


def _pair(a_cfg, b_cfg):
    model = _model()
    a, b = model.apply(_inputs(), a_cfg), model.apply(_inputs(), b_cfg)
    return model, a, b, model.difference(a, b)


# ──────────────────────────────── the constructed fixture: all four codes


def test_the_constructed_difference_carries_all_four_codes_and_undefined_in_both_orders(tmp_path: Path, verdict) -> None:
    model, a, b, diff = _pair(MARKET, STRATEGIC)
    written = write_difference(diff, a, b, _grid(), {"fixture": _surface()}, tmp_path, claim_verdict=verdict)
    with rasterio.open(written[("fixture", 0.0)]) as ds:
        code, tags = ds.read(1), ds.tags()
    expected = np.array([[2.0, 1.0, 1.0, 1.0], [0.0, 1.0, 2.0, np.nan]], dtype=np.float32)
    np.testing.assert_array_equal(code, expected)
    assert (tags["n_neither"], tags["n_both"], tags["n_only_b"], tags["n_only_a"], tags["n_undefined"]) == ("1", "4", "2", "0", "1")
    assert tags["meaning"] == DIFFERENCE_MEANING and tags["encoding"] == DIFFERENCE_ENCODING and tags["kind"] == "difference"
    assert (tags["scenario_a"], tags["scenario_b"], tags["cutoff_a_kg_m2"], tags["cutoff_b_kg_m2"]) == ("MARKET_STANDARD", "STRATEGIC_SUBSIDIZED", "10", "5.5")
    assert "SENSITIVITY map, not a resource map" in tags["meaning"] and "WHICH PLACEHOLDER CUTOFF IS ASSUMED" in tags["meaning"]
    # the reversed pair: the same two cells become "only_a" (code 3), nothing else moves
    model, a2, b2, diff2 = _pair(STRATEGIC, MARKET)
    written2 = write_difference(diff2, a2, b2, _grid(), {"fixture": _surface()}, tmp_path / "rev", claim_verdict=verdict)
    code2 = rasterio.open(written2[("fixture", 0.0)]).read(1)
    np.testing.assert_array_equal(code2, np.array([[3.0, 1.0, 1.0, 1.0], [0.0, 1.0, 3.0, np.nan]], dtype=np.float32))
    assert diff2.levels["fixture"][0.0].n_minable == 0  # "minable under MARKET and not STRATEGIC": none


def test_encode_difference_is_the_set_logic_not_a_constant(tmp_path: Path) -> None:
    """The encoder alone, on hand arrays: every code reachable, the mask
    overriding all of them — separates the computation from "returns empty"
    (the mutation that makes every cell 'neither')."""
    a = np.array([[True, True, False, False]]); b = np.array([[True, False, True, False]]); mask = np.array([[False, False, False, True]])
    np.testing.assert_array_equal(encode_difference(a, b, mask), np.array([[1.0, 3.0, 2.0, np.nan]], dtype=np.float32))
    assert DIFFERENCE_CODES == {"neither": 0.0, "both": 1.0, "only_b": 2.0, "only_a": 3.0}


def test_a_difference_that_disagrees_with_its_own_footprints_is_refused_by_name(tmp_path: Path, verdict) -> None:
    model, a, b, diff = _pair(MARKET, STRATEGIC)
    level = diff.levels["fixture"][0.0]
    forged = level.minable.copy(); forged[0, 2] = True; forged.flags.writeable = False  # claims a "both" cell as the difference
    tampered = dataclasses.replace(diff, levels={"fixture": {0.0: dataclasses.replace(level, minable=forged), 1.0: diff.levels["fixture"][1.0]}})
    with pytest.raises(ValueError, match=r"disagrees with the code recomputed from its two inputs"):
        write_difference(tampered, a, b, _grid(), {"fixture": _surface()}, tmp_path, claim_verdict=verdict)
    with pytest.raises(ValueError, match=r"the difference is \('MARKET_STANDARD', 'STRATEGIC_SUBSIDIZED'\), the footprints handed in are"):
        write_difference(diff, b, a, _grid(), {"fixture": _surface()}, tmp_path / "b", claim_verdict=verdict)


def test_the_difference_carries_the_two_reason_verdict_per_reason_like_the_footprints(tmp_path: Path, verdict) -> None:
    model, a, b, diff = _pair(MARKET, STRATEGIC)
    written = write_difference(diff, a, b, _grid(), {"fixture": _surface()}, tmp_path, claim_verdict=verdict)
    tags = rasterio.open(written[("fixture", 1.0)]).tags()
    assert tags["watermark_reason_terrain"].startswith("UNLIFTED:") and tags["watermark_reason_economic_parameters"].startswith("UNLIFTED:")
    assert tags["publishable"] == "false" and tags["data_origin"] == "AUTHORED"
    record = json.loads((tmp_path / ASSOCIATION_NAME).read_text())
    entry = record["files"][difference_name("MARKET_STANDARD", "STRATEGIC_SUBSIDIZED", "fixture", 1.0)]
    assert entry["kind"] == "difference" and entry["counts"]["only_b"] == diff.levels["fixture"][1.0].n_minable
    assert record["difference_meaning"] == DIFFERENCE_MEANING


# ───────────────────────────── today's surfaces: the measured zero, with its reason


@pytest.fixture(scope="module")
def real_differences(real, verdict) -> dict:  # noqa: F811
    model = CutoffEconomicModel()
    a, b = real["footprints"]["MARKET_STANDARD"], real["footprints"]["STRATEGIC_SUBSIDIZED"]
    diff = model.difference(a, b)
    written = write_difference(diff, a, b, real["grid"], real["surfaces"], real["out"], claim_verdict=verdict)
    return {"diff": diff, "written": written}


def test_on_todays_surfaces_every_unmasked_cell_is_minable_under_both_and_the_difference_fraction_is_zero(real, real_differences) -> None:  # noqa: F811
    """THE MEASURED ZERO, WITH ITS REASON (E4.1; stated in advance): both
    placeholder cutoffs sit below the training mean over the whole domain,
    so every unmasked cell is code 1 ("both") — case (a) of the three the
    encoding keeps apart — and codes 0, 2 and 3 are absent. Asserted as the
    FULL VALUE SET per file, so a change to Contract 4's placeholders shows
    here as a failure, not a silent improvement. The G4.1 BACKLOG entry
    already carries the bracket-nothing ask; this test does not restate it."""
    assert len(real_differences["written"]) == 6 == 3 * 2
    for (estimator, z), path in real_differences["written"].items():
        with rasterio.open(path) as ds:
            code, tags = ds.read(1), ds.tags()
        finite = code[np.isfinite(code)]
        assert set(np.unique(finite).tolist()) == {1.0} and finite.size == 2880 and int(np.isnan(code).sum()) == 520
        assert (tags["n_both"], tags["n_neither"], tags["n_only_b"], tags["n_only_a"], tags["n_undefined"]) == ("2880", "0", "0", "0", "520")
        assert tags["difference_fraction_of_predictable"] == "0.000000"
        assert real_differences["diff"].levels[estimator][z].fraction_of_predictable == 0.0
    # the association now resolves 18 rasters, and every difference file's hash recomputes
    record = json.loads((real["out"] / ASSOCIATION_NAME).read_text())["files"]
    assert len(record) == 18 and sum(1 for e in record.values() if e["kind"] == "difference") == 6
    for name, entry in record.items():
        if entry["kind"] == "difference":
            assert file_sha256(real["out"] / name) == entry["sha256"] and entry["counts"]["both"] == 2880
