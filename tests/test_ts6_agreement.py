"""E3.3 commit 2 — the agreement, with its inflation and benchmark error
declared.

STATED FIRST: every TS-6 raster here is a SYNTHETIC FIXTURE (or a constructed
known-answer array). Nothing below measures anything about TS-6.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.surfaces.builder import SurfaceResult
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.ts6.comparison import (
    INFLATION_NOTE,
    MIN_DIGITIZATION_METHOD_CHARS,
    compare_all_to_ts6,
    compare_surface_to_ts6,
    effective_sample_size,
)

RERUNNABLE_METHOD = (
    "georeferenced raster scan of TS-6 Figure 5 (2010 edition), GCPs at the "
    "four graticule corners, colour-ramp lookup against the printed legend"
)


@pytest.fixture(scope="module")
def grid(surface_assembly) -> PredictionGrid:
    return surface_assembly["grid"]


@pytest.fixture(scope="module")
def kriging_result(surface_assembly) -> SurfaceResult:
    return surface_assembly["surfaces"]["ordinary_kriging"]


@pytest.fixture(scope="module")
def baseline_result(surface_assembly) -> SurfaceResult:
    return surface_assembly["surfaces"]["mean_baseline"]


def _result_with_mu(template: SurfaceResult, mu: np.ndarray, name: str) -> SurfaceResult:
    mu = mu.copy()
    mu.flags.writeable = False
    return dataclasses.replace(template, estimator_name=name, mu=mu)


def _ts6_raster(tmp_path: Path, grid: PredictionGrid, values: np.ndarray, name: str) -> str:
    """A TS-6 raster holding EXACTLY `values` — float64, so known-answer
    fixtures are not blurred by float32 storage."""
    path = tmp_path / f"{name}.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=grid.height,
        width=grid.width,
        count=1,
        dtype="float64",
        crs=grid.crs,
        transform=rasterio.Affine(*grid.transform),
        nodata=np.nan,
    ) as dataset:
        dataset.write(values.astype(np.float64), 1)
    return str(path)


def _ts6(tmp_path, grid, values, name="ts6", role_note="benchmark_only", origin="SYNTHETIC"):
    return TS6Surface(
        title=f"{name} (constructed)",
        source_id="src_ts6_grid",
        raster_path=_ts6_raster(tmp_path, grid, values, name),
        role_note=role_note,
        data_origin=origin,
    )


# ─────────────────────────────────────────────────────────── known answers


def test_identical_surfaces_agree_perfectly(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """r = 1, mean difference = 0, rmse = 0 — on a VARYING surface (kriging's
    real one), because on a constant surface every comparison method
    degenerates and the claim 'perfect agreement is reported as perfect'
    could not be separated from 'the code returns 1.0 unconditionally'
    (which the negation test below refutes from the other side)."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "identical")
    agreement = compare_surface_to_ts6(
        kriging_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.spatial_correlation == pytest.approx(1.0, abs=1e-12)
    assert agreement.mean_difference == pytest.approx(0.0, abs=1e-12)
    assert agreement.rmse == pytest.approx(0.0, abs=1e-12)
    assert agreement.correlation_status == "ok"
    assert agreement.n_cells == 2880


def test_a_surface_and_its_negation_correlate_minus_one(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The other endpoint: r = −1 exactly for ts6 = −(our surface). Together
    with the identity case this brackets the sign convention — a comparison
    that dropped a minus sign somewhere passes one and fails the other."""
    ts6 = _ts6(tmp_path, grid, -kriging_result.mu, "negated")
    agreement = compare_surface_to_ts6(
        kriging_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.spatial_correlation == pytest.approx(-1.0, abs=1e-12)


def test_a_constant_prediction_surface_degenerates_by_name_naming_our_side(
    tmp_path: Path, grid: PredictionGrid, baseline_result: SurfaceResult
) -> None:
    """NOT HYPOTHETICAL: this is the mean baseline's REAL surface, whose sd is
    3.55e-15 — not 0.0 — because mean subtraction leaves ULP noise. An
    exact-zero test let it through to np.corrcoef, which returned an r made
    entirely of that noise labelled "ok" (found by running the real
    comparison; the fix is the E2.4 ZERO_TOL_REL numerical-zero policy).
    Using the real baseline surface keeps that noise in this test's path, so
    a regression to exact-zero comparison fails HERE."""
    rng = np.random.default_rng(7)
    ts6 = _ts6(tmp_path, grid, rng.normal(10, 2, size=baseline_result.mu.shape), "noise")
    agreement = compare_surface_to_ts6(
        baseline_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.spatial_correlation is None
    assert agreement.n_eff is None
    assert "prediction surface" in agreement.correlation_status
    assert "zero variance" in agreement.correlation_status
    # the interpretable half still reports: mean difference exists regardless
    assert agreement.mean_difference is not None


def test_a_constant_benchmark_degenerates_by_name_naming_the_ts6_side(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The mirror case, asserted separately: the status must name WHICH side
    is constant, or a reader debugs the wrong surface."""
    ts6 = _ts6(tmp_path, grid, np.full(kriging_result.mu.shape, 5.0), "flat")
    agreement = compare_surface_to_ts6(
        kriging_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.spatial_correlation is None
    assert "ts6 benchmark" in agreement.correlation_status
    assert "prediction surface" not in agreement.correlation_status


# ─────────────────────────────────────────── the inflation, both directions


def test_n_eff_collapses_for_two_smooth_surfaces_and_stays_near_n_for_white_noise(
    grid: PredictionGrid,
) -> None:
    """WHICH NEIGHBOURING CLAIMS THIS SEPARATES (the degeneracy rule), both
    ways: "N_eff collapses under shared smoothness" from "N_eff is always
    small" AND from "N_eff is always N". A single fixture can show neither.

    * two SMOOTH fields (long-wave sinusoids of position) → each correlogram
      ≈ 1 out to long lags → N_eff ≪ N. This is the inflation the project
      measured as random-k-fold leakage, in its new costume.
    * two WHITE-NOISE fields → correlograms ≈ 0 off-diagonal → N_eff ≈ N —
      which is also why TODAY'S fixture comparison reports n_eff ≈ N: the
      synthetic TS-6 is white noise, and Clifford–Richardson honestly says
      the naive df is nearly right when one field is white. The E3.0
      "N_eff ≈ 2" expectation assumed BOTH surfaces smooth, which is the
      REAL TS-6 case, not the fixture's.
    """
    centres = grid.cell_centres()[grid.predictable.ravel()]
    lon = centres[:, 0]
    lat = centres[:, 1]
    n = centres.shape[0]

    smooth_a = np.sin(2 * np.pi * (lon - lon.min()) / (lon.max() - lon.min()))
    smooth_b = np.cos(2 * np.pi * (lon - lon.min()) / (lon.max() - lon.min())) + 0.3 * lat
    n_eff_smooth = effective_sample_size(smooth_a, smooth_b, centres)
    assert n_eff_smooth is not None and n_eff_smooth < n / 10, n_eff_smooth

    rng = np.random.default_rng(11)
    n_eff_white = effective_sample_size(
        rng.normal(size=n), rng.normal(size=n), centres
    )
    assert n_eff_white is not None and n_eff_white > n / 2, n_eff_white


def test_the_interpretation_says_not_distinguishable_when_r_is_inside_the_noise_scale(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The honest output the spec called likely: kriging's near-constant
    surface against an unrelated benchmark. The assertion is on the SENTENCE,
    because Karl's decision requires the reading to travel with the number."""
    rng = np.random.default_rng(13)
    ts6 = _ts6(tmp_path, grid, rng.normal(10, 2, size=kriging_result.mu.shape), "unrelated")
    agreement = compare_surface_to_ts6(
        kriging_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.spatial_correlation is not None
    assert "NOT distinguishable from zero" in agreement.interpretation
    assert agreement.inflation_note == INFLATION_NOTE
    assert "cannot manufacture information" in agreement.inflation_note
    assert agreement.n_eff_method and "Clifford" in agreement.n_eff_method


# ──────────────────────────────────────────────────────────── the refusals


def test_a_null_role_note_is_refused_not_assumed(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The circularity marker: a comparison that assumed benchmark_only would
    label its own number independent."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "noro", role_note=None)
    with pytest.raises(ValueError, match="role_note is null"):
        compare_surface_to_ts6(kriging_result, grid, ts6, surface_data_origin="SYNTHETIC")


def test_the_real_path_refuses_when_the_uncertainty_SLOT_does_not_exist(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """ABSENT is not NULL. The E3.3 prompt said Contract 6's
    digitization-uncertainty field 'is null today'; verification found NO
    SUCH FIELD — and the refusal message must say that adding it is a
    STRUCTURAL contract change, because that is a different remedy (Karl,
    version bump) than filling a value (Track G)."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "derived_a", origin="DERIVED")
    with pytest.raises(ValueError, match="no digitization_uncertainty SLOT"):
        compare_surface_to_ts6(
            kriging_result, grid, ts6, surface_data_origin="SYNTHETIC", contract={}
        )


def test_the_real_path_refuses_a_null_uncertainty_with_a_different_message(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The NULL state, separately: the slot exists, the value is unfilled —
    Track G's remedy, named as such, distinct from the structural one."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "derived_b", origin="DERIVED")
    with pytest.raises(ValueError, match="explicitly NULL"):
        compare_surface_to_ts6(
            kriging_result,
            grid,
            ts6,
            surface_data_origin="SYNTHETIC",
            contract={"digitization_uncertainty": None},
        )


def test_the_real_path_refuses_a_category_word_as_digitization_method(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """Contract 6's own vocabulary options name CATEGORIES, not re-runnable
    procedures — 'table interpolation' is 19 characters and says which KIND
    of thing was done, not what was done. Refused for exactly the reason a
    bare 'deterministic' is refused as a determinism basis (TAX.1)."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "derived_c", origin="DERIVED")
    with pytest.raises(ValueError, match="too short to be re-run"):
        compare_surface_to_ts6(
            kriging_result,
            grid,
            ts6,
            surface_data_origin="SYNTHETIC",
            contract={
                "digitization_uncertainty": 2.5,
                "digitization_method": "table interpolation",
            },
        )
    assert len("table interpolation") < MIN_DIGITIZATION_METHOD_CHARS


def test_the_real_path_with_full_evidence_carries_the_uncertainty_into_the_output(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The POSITIVE CONTROL for the three refusals above: with the slot
    present, the value filled and a re-runnable method, the comparison runs
    and the benchmark's error travels in the output — the requirement, not
    just its refusals."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "derived_d", origin="DERIVED")
    agreement = compare_surface_to_ts6(
        kriging_result,
        grid,
        ts6,
        surface_data_origin="SYNTHETIC",
        contract={
            "digitization_uncertainty": 2.5,
            "digitization_method": RERUNNABLE_METHOD,
        },
    )
    assert agreement.benchmark_uncertainty == 2.5
    assert "2.5" in agreement.benchmark_uncertainty_note
    assert "georeferenced raster scan of TS-6 Figure 5" in agreement.benchmark_uncertainty_note


def test_the_fixture_path_reports_not_applicable_rather_than_zero(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """The other half — one without the other cannot distinguish 'handled'
    from 'ignored': a SYNTHETIC benchmark was never digitized, so there IS no
    digitization error, and reporting 0.0 would claim an exact benchmark."""
    ts6 = _ts6(tmp_path, grid, kriging_result.mu, "fixture_path")
    agreement = compare_surface_to_ts6(
        kriging_result, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert agreement.benchmark_uncertainty is None
    assert "not applicable — synthetic fixture" in agreement.benchmark_uncertainty_note


# ────────────────────────────────────────────── origin, watermark, coverage


def test_the_agreements_origin_is_computed_and_a_synthetic_input_watermarks_it(
    tmp_path: Path, grid: PredictionGrid, kriging_result: SurfaceResult
) -> None:
    """Computed, never declared — and the watermark derives from it,
    default-on. The MEASURED/DERIVED pairing is the laundering control: a
    comparison that hardcoded SYNTHETIC would fail it, and one that hardcoded
    the surface's own origin would fail the mixed case."""
    synthetic = compare_surface_to_ts6(
        kriging_result,
        grid,
        _ts6(tmp_path, grid, kriging_result.mu, "syn"),
        surface_data_origin="SYNTHETIC",
    )
    assert synthetic.data_origin == "SYNTHETIC"
    assert synthetic.watermark is not None and "NON-SCIENTIFIC" in synthetic.watermark

    mixed = compare_surface_to_ts6(
        kriging_result,
        grid,
        _ts6(tmp_path, grid, kriging_result.mu, "der", origin="DERIVED"),
        surface_data_origin="MEASURED",
        contract={
            "digitization_uncertainty": 2.5,
            "digitization_method": RERUNNABLE_METHOD,
        },
    )
    assert mixed.data_origin == "DERIVED"  # least-real of MEASURED + DERIVED
    assert mixed.watermark is not None  # only proven MEASURED renders clean


def test_compare_all_covers_every_surface_and_none_is_cherry_picked(
    tmp_path: Path, grid: PredictionGrid, surface_assembly
) -> None:
    """ITERATE, never cherry-pick — a POSITIVE FULL-STATE comparison of the
    keys (rule 3 / the vacuous-collection lesson), and each agreement
    self-identifies, so the mapping and its values cannot disagree."""
    surfaces = surface_assembly["surfaces"]
    ts6 = _ts6(tmp_path, grid, surfaces["ordinary_kriging"].mu, "all")
    agreements = compare_all_to_ts6(
        surfaces, grid, ts6, surface_data_origin="SYNTHETIC"
    )
    assert sorted(agreements) == sorted(surfaces)
    for name, agreement in agreements.items():
        assert agreement.estimator_name == name
        assert agreement.role_note == "benchmark_only"
        assert agreement.resampling is not None and agreement.resampling["method"] == "nearest"


# ── G3.1: Contract 6 is filled; the real-data path's gate must now pass ──


def test_contract_6_as_committed_satisfies_the_real_path_digitization_gate() -> None:
    """G3.1 filled Contract 6's five nulls from the Figure 38 digitization.
    `_require_digitization_evidence` is the REAL (non-SYNTHETIC) path's gate:
    before G3.1 it refused this contract twice over — null uncertainty, null
    method. This asserts the committed file now passes it, and that the method
    clears the re-runnability floor rather than merely being non-empty."""
    from engine.prospectivity.ts6.comparison import (
        MIN_DIGITIZATION_METHOD_CHARS,
        _require_digitization_evidence,
    )

    uncertainty, method = _require_digitization_evidence(None)
    assert uncertainty == 2.5
    assert len(method) > MIN_DIGITIZATION_METHOD_CHARS
    # The method must LOCATE the work, not name a category. These tokens are
    # what the VERBATIM script docstring carries; the FIGURE's identity lives in
    # `source_figure` (asserted in the next test), not here — the method block
    # locates the page and the procedure.
    for token in ("page 80", "400 dpi", "graticule", "digitize_fig38.py"):
        assert token in method, f"digitization_method does not mention {token!r}"


def test_the_committed_ts6_contract_records_a_non_circular_role() -> None:
    """role_note was null until G3.1. `benchmark_only` is the contract's own
    PREFERRED case: the corpus trains on [01]/[05] stations, so nothing from
    TS-6 fed the samples and the comparison is not a reproduction check."""
    import yaml

    repo_root = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load(
        (repo_root / "data/ts6/ts6_reference.yaml").read_text()
    )["ts6_reference"]
    assert contract["role_note"] == "benchmark_only"
    assert contract["source_figure"] and "Figure 38" in contract["source_figure"]
