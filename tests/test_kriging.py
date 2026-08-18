"""OrdinaryKrigingEstimator + the variogram fitter (E2.2 §2): known-answer
recovery, exactness, the pure-nugget honesty check, the Lagrange term made
observable, recorded exclusions, and determinism.

Fixture-degeneracy statements (CLAUDE.md rule 4), per fixture:
- The recovery fixtures separate FITTER ARITHMETIC from SAMPLING NOISE:
  exact model-valued bins (zero noise — recovery must be near-exact, so a
  hardcoded range fails) vs a 20-seed averaged realization batch (bounds
  chosen by probing 5 disjoint batches; a one-seed pin would be the
  coin-flip the prompt warns about).
- The exact-bins fixture carries UNEQUAL pair counts arranged so the
  count-weighted fit differs measurably from the equal-weighted one (E2.2
  review: with every bin at count 100 the whole suite stayed green under an
  equal-weights mutation — a 19% shift in the real nugget, unobserved).
- The exactness fixture has a NONZERO nugget — and what bears load is the
  FITTED nugget on that realization (0.62 at seed 3), which the test now
  pins > 0.3 rather than trusting the planted 0.2 (review nit): with zero
  nugget, exactness is trivially satisfiable by any interpolant; with a
  nugget, exactness + near-zero variance AT the datum while sd jumps
  off-datum is specifically kriging's gamma(0)=0 behavior.
- Grid layouts here use UNIT spacing but the fit bins have UNEQUAL widths,
  so no two fitted bins coincide in midpoint or width.
- The planar path's ½ factor is separately observed: a hand-built two-pair
  planar fit whose semivariance literal is exactly half a squared difference.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
from engine.prospectivity.estimators.registry import (
    MEAN_BASELINE_NAME,
    REQUIRED_ESTIMATORS,
    build_default_registry,
)
from engine.prospectivity.estimators.variogram import (
    EmpiricalVariogram,
    VariogramBin,
    VariogramModel,
    fit_variogram,
)
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from tests.fixtures.known_answer import gaussian_process_field, grid_layout

FIXTURE_EDGES = (0.5, 1.5, 2.5, 3.5, 5.0, 7.0, 9.0, 12.0, 16.0)


# UNEQUAL pair counts per bin (rule 4): the count-weighted and equal-weighted
# fits must DIFFER on a noisy fixture, or the weights are unobservable.
UNEQUAL_COUNTS = (400, 40, 200, 40, 120, 40, 90, 40)


def _bins_from_model(
    model: VariogramModel, edges: tuple[float, ...], counts: tuple[int, ...] = UNEQUAL_COUNTS
) -> EmpiricalVariogram:
    """Bins whose semivariances are the TRUE model values at midpoints (no
    mean lag recorded → the fitter's midpoint fallback) — zero sampling
    noise, so recovery tests the fitter's arithmetic alone."""
    bins = []
    for k, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        mid = (lo + hi) / 2.0
        bins.append(VariogramBin(lo, hi, counts[k], float(model.gamma(np.array([mid]))[0])))
    return EmpiricalVariogram(bins=tuple(bins), total_pairs=sum(counts[: len(bins)]))


def _averaged_empirical(coords: np.ndarray, fields: list, edges: tuple) -> EmpiricalVariogram:
    from tests.fixtures.known_answer import empirical_semivariance

    lag_edges = np.asarray(edges, dtype=np.float64)
    semis = [empirical_semivariance(coords, y, lag_edges=lag_edges)[0] for y in fields]
    _, counts = empirical_semivariance(coords, fields[0], lag_edges=lag_edges)
    mean_semi = np.nanmean(semis, axis=0)
    bins = tuple(
        VariogramBin(
            float(lag_edges[k]),
            float(lag_edges[k + 1]),
            int(counts[k]),
            float(mean_semi[k]) if counts[k] else None,
        )
        for k in range(lag_edges.size - 1)
    )
    return EmpiricalVariogram(bins=bins, total_pairs=int(counts.sum()))


# -------------------------------------------------------- parameter recovery


def test_fitter_recovers_exact_model_valued_bins_within_grid_resolution() -> None:
    """Zero sampling noise: bins carry the true exponential gamma at their
    midpoints, so the only error source is the 200-point log candidate
    grid (~3% spacing). Tolerances: range 5%, nugget/sill 2%."""
    planted = VariogramModel(family="exponential", nugget=0.2, partial_sill=0.8, range_km=4.0)
    fit = fit_variogram(
        _bins_from_model(planted, FIXTURE_EDGES),
        family="exponential",
        min_pairs=30,
        max_fit_lag_km=None,
    )
    assert abs(fit.model.range_km - 4.0) / 4.0 < 0.05
    assert abs(fit.model.nugget - 0.2) < 0.02
    assert abs(fit.model.sill - 1.0) < 0.02
    assert not fit.range_at_candidate_ceiling


def test_fitter_recovers_planted_parameters_from_averaged_realizations() -> None:
    """End-to-end with sampling noise: 20 independent GP realizations
    (seeds 0–19) on a 16×16 grid, empirical variograms averaged, then fit.
    Bounds chosen by probing FIVE disjoint 20-seed batches (E2.2 §2 probe:
    range 3.38–6.24 vs planted 4; sill 0.948–1.009; nugget 0.099–0.500;
    partial sill 0.493–0.898) — every batch satisfies these bounds, so the
    pin is a property of the method at this replication level, not a
    lucky seed."""
    coords = grid_layout(16, spacing=1.0)
    fields = [
        gaussian_process_field(coords, variogram_range=4.0, sill=1.0, nugget=0.2, seed=s)
        for s in range(20)
    ]
    fit = fit_variogram(
        _averaged_empirical(coords, fields, FIXTURE_EDGES),
        family="exponential",
        min_pairs=30,
        max_fit_lag_km=None,
    )
    assert 2.0 < fit.model.range_km < 8.0
    assert 0.85 < fit.model.sill < 1.15
    assert fit.model.nugget < 0.55
    assert fit.model.partial_sill > 0.4


def test_pure_nugget_exact_bins_yield_the_explicit_no_structure_verdict() -> None:
    """Flat bins (gamma == nugget at every lag) must produce
    partial_sill == 0.0 AND range_km == 0.0 — the stated verdict form. A
    fitter that always finds structure is broken in the direction that
    flatters."""
    flat = VariogramModel(family="exponential", nugget=1.0, partial_sill=0.0, range_km=0.0)
    fit = fit_variogram(
        _bins_from_model(flat, FIXTURE_EDGES),
        family="exponential",
        min_pairs=30,
        max_fit_lag_km=None,
    )
    assert fit.model.partial_sill == 0.0
    assert fit.model.range_km == 0.0
    assert abs(fit.model.nugget - 1.0) < 0.02


def test_pure_nugget_field_reverts_to_the_mean_with_variance_near_the_sill() -> None:
    """The estimator end to end on a no-structure FIELD (seed 0 probed to
    yield the verdict on a single realization): predictions at off-data
    points equal the training mean (OK weights collapse to 1/n) and the
    OK variance is sill·(1 + 1/n) — just ABOVE the sill, the Lagrange term
    in its purest form."""
    coords = grid_layout(12, spacing=1.0)
    y = gaussian_process_field(coords, variogram_range=10.0, sill=1.0, nugget=1.0, seed=0)
    kriging = OrdinaryKrigingEstimator(
        bin_edges_km=(0.5, 2.0, 10.0, 14.0),
        min_pairs=30,
        max_fit_lag_km=None,
        coordinate_system="planar",
    )
    kriging.fit(coords, y)
    report = kriging.report()
    assert report.partial_sill == 0.0
    assert report.range_km == 0.0

    targets = np.array([[3.3, 4.7], [200.0, 200.0]])
    mean, sd = kriging.predict(targets)
    assert np.allclose(mean, y.mean(), atol=1e-9)
    expected_var = report.sill * (1.0 + 1.0 / len(y))
    assert np.allclose(sd**2, expected_var, rtol=1e-6)
    assert (sd**2 > report.sill).all()


# ------------------------------------------------------------- exactness


def _fitted_fixture_estimator() -> tuple[OrdinaryKrigingEstimator, np.ndarray, np.ndarray]:
    coords = grid_layout(10, spacing=1.0)
    y = gaussian_process_field(coords, variogram_range=4.0, sill=1.0, nugget=0.2, seed=3)
    kriging = OrdinaryKrigingEstimator(
        bin_edges_km=(0.5, 1.5, 2.5, 3.5, 5.0, 7.0, 9.0, 13.0),
        min_pairs=30,
        max_fit_lag_km=None,
        coordinate_system="planar",
    )
    kriging.fit(coords, y)
    return kriging, coords, y


def test_kriging_is_exact_at_data_locations_despite_a_nonzero_nugget() -> None:
    """The gamma(0)=0 convention observable: AT a datum the prediction is
    the observation (|error| < 1e-9) with sd < 1e-6, while 0.4 units OFF
    the datum the sd jumps above √nugget·½ — the discontinuity that
    separates kriging exactness from a generic smoother, which with a
    nugget would NOT honor the data exactly (the fixture's nugget 0.2 is
    the load-bearing part, per the degeneracy rule)."""
    kriging, coords, y = _fitted_fixture_estimator()
    assert kriging.report().nugget > 0.3  # the FITTED nugget bears the load

    mean, sd = kriging.predict(coords[:7])
    assert np.abs(mean - y[:7]).max() < 1e-9
    assert sd.max() < 1e-6

    off_datum = coords[:1] + np.array([[0.4, 0.0]])
    _, off_sd = kriging.predict(off_datum)
    assert off_sd[0] > 0.2  # the nugget discontinuity, not a smooth ramp


def test_variance_increases_monotonically_with_distance_from_the_data() -> None:
    """Along a transect walking away from the grid's corner datum, each
    step's sd strictly exceeds the last — hand-verifiable shape, no
    literal pins (the fitted parameters vary with the fixture field)."""
    kriging, coords, _ = _fitted_fixture_estimator()
    transect = np.array([[0.0, -d] for d in (0.1, 0.5, 1.0, 2.0, 4.0, 8.0)])
    _, sd = kriging.predict(transect)
    assert np.all(np.diff(sd) > 0)


def test_far_field_variance_strictly_exceeds_the_fitted_sill() -> None:
    """The Lagrange term made observable, not just mentioned: far from all
    data OK variance = sill + mu with mu > 0 (only SIMPLE kriging converges
    to the sill). This is the pin behind the E2.4 caveat that kriging's
    far-field uncertainty and the baseline's SD are not the same number."""
    kriging, _, _ = _fitted_fixture_estimator()
    _, far_sd = kriging.predict(np.array([[500.0, 500.0]]))
    assert far_sd[0] ** 2 > kriging.report().sill


# ------------------------------------------------- exclusions and real data


def test_real_corpus_fit_records_karls_exclusions_and_the_unsupported_range() -> None:
    """The fit on the real 35 stations under the E2.2 decisions records,
    per excluded bin, WHY it was excluded: 2–4 km and 8–10 km below
    min_pairs 30 (decision 1), 13–986 km zero pairs, 986–997 km beyond the
    13 km fit lag (decision 2) — and names 13–986 km as the unsupported
    range every between-cluster prediction extrapolates across. The fitted
    range sits AT the candidate ceiling and is flagged so — on this data
    the range is unconstrained, which is the honest verdict."""
    obs = sorted(
        CorpusCsvSampleSource().get_training_samples(), key=lambda o: o.source_record_id
    )
    coords = np.array([[o.longitude, o.latitude] for o in obs])
    y = np.array([o.abundance_kg_m2 for o in obs])
    kriging = OrdinaryKrigingEstimator()
    kriging.fit(coords, y)
    report = kriging.report()

    reasons = {(lo, hi): reason for (lo, hi, _), reason in report.excluded_bins}
    assert "minimum 30" in reasons[(2.0, 4.0)]
    assert "minimum 30" in reasons[(8.0, 10.0)]
    assert "zero pairs" in reasons[(13.0, 986.0)]
    assert "beyond max fit lag 13.0" in reasons[(986.0, 997.0)]
    assert report.unsupported_km == ((13.0, 986.0),)
    assert [b[:2] for b in report.fitted_bins] == [(0.0, 2.0), (4.0, 6.0), (6.0, 8.0), (10.0, 13.0)]
    assert report.range_at_candidate_ceiling
    assert report.used_model_family == "exponential"
    assert report.alternative.model.family == "spherical"


def test_fit_refuses_when_exclusions_leave_fewer_than_three_bins() -> None:
    flat = VariogramModel(family="exponential", nugget=1.0, partial_sill=0.0, range_km=0.0)
    empirical = _bins_from_model(flat, (0.5, 1.5, 2.5, 3.5))
    with pytest.raises(ValueError, match="fewer than 3 supported bins"):
        fit_variogram(empirical, family="exponential", min_pairs=1000, max_fit_lag_km=None)


# --------------------------------------------------- determinism + refusals


def test_two_fits_and_predictions_are_identical_in_every_field() -> None:
    first, coords, y = _fitted_fixture_estimator()
    second, _, _ = _fitted_fixture_estimator()

    targets = np.array([[1.3, 2.7], [8.1, 0.4], [50.0, 50.0]])
    mean_a, sd_a = first.predict(targets)
    mean_b, sd_b = second.predict(targets)
    assert np.array_equal(mean_a, mean_b)
    assert np.array_equal(sd_a, sd_b)
    assert first.report() == second.report()  # frozen dataclasses: full state


def test_kriging_refusals_name_their_condition() -> None:
    kriging = OrdinaryKrigingEstimator(coordinate_system="planar")
    with pytest.raises(ValueError, match="before fit"):
        kriging.predict(np.zeros((2, 2)))
    with pytest.raises(ValueError, match="features ARE coordinates"):
        kriging.fit(np.zeros((5, 3)), np.zeros(5))
    with pytest.raises(ValueError, match="need >= 3"):
        kriging.fit(np.zeros((2, 2)), np.zeros(2))
    with pytest.raises(ValueError, match="non-finite"):
        kriging.fit(np.array([[0.0, 0.0], [1.0, np.nan], [2.0, 0.0], [3.0, 1.0]]), np.ones(4))

    duplicated = OrdinaryKrigingEstimator(
        bin_edges_km=(0.001, 1.0, 2.0, 3.0, 5.0), min_pairs=1, max_fit_lag_km=None,
        coordinate_system="planar",
    )
    coords = np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [2.0, 1.0], [3.0, 2.0]])
    with pytest.raises(ValueError, match="singular"):
        duplicated.fit(coords, np.array([1.0, 2.0, 3.0, 4.0, 5.0]))


def test_ordinary_kriging_registers_and_the_baseline_stays_the_only_required() -> None:
    registry = build_default_registry()
    assert "ordinary_kriging" in registry.names()
    assert isinstance(registry.get("ordinary_kriging"), OrdinaryKrigingEstimator)
    assert REQUIRED_ESTIMATORS == (MEAN_BASELINE_NAME,)


# ------------------------------------------ review-found guards (E2.2 §2)


def test_pair_count_weights_change_the_fit_on_unequal_count_bins() -> None:
    """The weights are OBSERVABLE: on model-valued bins perturbed by a fixed
    non-uniform noise vector, the count-weighted fit (the code) must differ
    from an equal-weighted fit computed independently here — and the code's
    nugget must match the count-weighted answer, not the equal-weighted one.
    (E2.2 review: with uniform counts an equal-weights mutation left all 344
    tests green.)"""
    planted = VariogramModel(family="exponential", nugget=0.3, partial_sill=0.7, range_km=4.0)
    edges = FIXTURE_EDGES
    noise = np.array([0.15, -0.20, 0.10, -0.25, 0.05, -0.15, 0.20, -0.10])
    bins = []
    for k, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        mid = (lo + hi) / 2.0
        gamma = float(planted.gamma(np.array([mid]))[0]) + noise[k]
        bins.append(VariogramBin(lo, hi, UNEQUAL_COUNTS[k], gamma))
    empirical = EmpiricalVariogram(bins=tuple(bins), total_pairs=sum(UNEQUAL_COUNTS))

    fit = fit_variogram(empirical, family="exponential", min_pairs=1, max_fit_lag_km=None)

    # Independent equal-weight WLS at the SAME fitted range, closed form.
    mids = np.array([(lo + hi) / 2.0 for lo, hi in zip(edges[:-1], edges[1:])])
    gammas = np.array([b.semivariance for b in bins])
    structure = 1.0 - np.exp(-3.0 * mids / fit.model.range_km)
    design = np.column_stack([np.ones_like(structure), structure])
    equal_nugget, _ = np.linalg.lstsq(design, gammas, rcond=None)[0]
    w = np.array(UNEQUAL_COUNTS, dtype=float)
    wd = design * w[:, None]
    count_nugget, _ = np.linalg.solve(design.T @ wd, wd.T @ gammas)

    assert abs(count_nugget - equal_nugget) > 0.02  # the fixture separates them
    assert abs(fit.model.nugget - count_nugget) < 1e-9
    assert abs(fit.model.nugget - equal_nugget) > 0.02


def test_planar_fit_path_uses_the_half_squared_difference_semivariance() -> None:
    """The planar (fixture) path shares bin_pairs with the geographic path
    (review: it used to duplicate the loop with an untested ½). Three
    collinear planar points with values 0, 2, 6 at x = 0, 1, 3: pair
    semivariances are ½·2² = 2.0 (lag 1), ½·6² = 18.0 (lag 3), ½·4² = 8.0
    (lag 2). Asserted through the estimator's report so the assertion is
    on the path the estimator actually runs; dropping the ½ makes 4/36/16."""
    coords = np.array([[0.0, 0.0], [1.0, 0.0], [3.0, 0.0]])
    kriging = OrdinaryKrigingEstimator(
        bin_edges_km=(0.5, 1.5, 2.5, 3.5), min_pairs=1, max_fit_lag_km=None,
        coordinate_system="planar",
    )
    kriging.fit(coords, np.array([0.0, 2.0, 6.0]))
    semis = {(lo, hi): gamma for lo, hi, _, gamma, _ in kriging.report().fitted_bins}
    assert semis == {(0.5, 1.5): 2.0, (1.5, 2.5): 8.0, (2.5, 3.5): 18.0}


def test_a_refused_refit_leaves_the_previous_fit_fully_intact() -> None:
    """fit() is ATOMIC (review must-fix): after a refit is refused, predict
    and report return exactly the FIRST fit's answers — not a chimera of
    new coords with the old system matrix (which used to predict silently
    wrong numbers), and a refused FIRST fit leaves the estimator unfitted."""
    kriging, coords, y = _fitted_fixture_estimator()
    target = np.array([[2.5, 2.5]])
    before_mean, before_sd = kriging.predict(target)
    before_report = kriging.report()

    bad_coords = grid_layout(10, spacing=1.0) + 140.0
    bad_coords[1] = bad_coords[0]  # duplicate -> singular system -> refused
    with pytest.raises(ValueError, match="singular"):
        kriging.fit(bad_coords, y)

    after_mean, after_sd = kriging.predict(target)
    assert np.array_equal(after_mean, before_mean)
    assert np.array_equal(after_sd, before_sd)
    assert kriging.report() == before_report

    fresh = OrdinaryKrigingEstimator(
        bin_edges_km=(0.5, 1.5, 2.5, 3.5, 5.0, 7.0, 9.0, 13.0), min_pairs=30,
        max_fit_lag_km=None, coordinate_system="planar",
    )
    with pytest.raises(ValueError, match="singular"):
        fresh.fit(bad_coords, y)
    with pytest.raises(ValueError, match="before fit"):
        fresh.predict(target)


def test_a_constant_target_is_refused_as_a_zero_variogram_not_duplicate_coords() -> None:
    """Review: 64 distinct grid stations with y = 7.5 everywhere used to be
    refused as 'duplicate station coordinates' — a wrong diagnosis with a
    remedy that cannot work. Named for what it is."""
    kriging = OrdinaryKrigingEstimator(
        bin_edges_km=(0.5, 1.5, 2.5, 3.5, 5.0, 8.0), min_pairs=5, max_fit_lag_km=None,
        coordinate_system="planar",
    )
    with pytest.raises(ValueError, match="identically zero.*constant"):
        kriging.fit(grid_layout(8), np.full(64, 7.5))


def test_a_bin_straddling_the_max_fit_lag_is_excluded_not_fitted() -> None:
    """Decision 2 cannot be diluted by re-binning: a (12, 20) bin under
    max_fit_lag 13 is EXCLUDED with the decision-2 reason (review: the old
    lag_lo test admitted it and fitted at midpoint 16 km)."""
    bins = tuple(
        VariogramBin(lo, hi, 50, gamma)
        for (lo, hi), gamma in zip(((0, 4), (4, 8), (8, 12), (12, 20)), (1.0, 2.0, 2.5, 3.0))
    )
    fit = fit_variogram(
        EmpiricalVariogram(bins=bins, total_pairs=200),
        family="exponential", min_pairs=30, max_fit_lag_km=13.0,
    )
    assert [(b.lag_lo_km, b.lag_hi_km) for b in fit.fitted_bins] == [(0, 4), (4, 8), (8, 12)]
    assert any("decision 2" in reason and b.lag_lo_km == 12 for b, reason in fit.excluded_bins)
    assert fit.residual_dof == 0  # exactly 3 bins: recorded, not hidden


def test_range_below_first_supported_lag_is_flagged_as_unidentifiable() -> None:
    """The floor counterpart of the ceiling flag (review): bins already flat
    at the sill from the first supported lag onward drive the fitted range
    at or below that lag, where nugget and partial sill cannot be told
    apart — flagged, so the reported split is not read as a finding."""
    planted = VariogramModel(family="exponential", nugget=0.3, partial_sill=0.7, range_km=0.4)
    fit = fit_variogram(
        _bins_from_model(planted, FIXTURE_EDGES), family="exponential", min_pairs=1,
        max_fit_lag_km=None,
    )
    assert fit.model.partial_sill > 0.0
    assert fit.range_below_first_supported_lag
    assert not fit.range_at_candidate_ceiling


def test_pairs_beyond_the_last_edge_are_counted_and_the_accounting_reconciles() -> None:
    """Review must-fix: a pair past the last edge used to vanish from every
    bin while total_pairs still counted it. Now counted in
    pairs_beyond_edges, and reconciles() closes the accounting."""
    from engine.prospectivity.estimators.variogram import empirical_variogram

    coords = np.array([[0.0, 0.0], [0.0, 0.01], [0.0, 0.03]])  # 1.11, 2.22, 3.34 km
    ev = empirical_variogram(coords, np.array([1.0, 4.0, 9.0]), (0.5, 2.0, 3.0))
    assert ev.total_pairs == 3
    assert sum(b.pair_count for b in ev.bins) == 2
    assert ev.pairs_beyond_edges == 1
    assert ev.reconciles()


def test_variogram_model_refuses_negative_parameters_and_the_clamp_is_bounded() -> None:
    """Review: VariogramModel(nugget=-0.6) constructed silently and produced
    a genuinely negative OK variance the unbounded clamp rendered as sd=0 —
    false certainty. Refused at construction now; the clamp only absorbs
    float noise (a genuinely negative variance would refuse by name)."""
    with pytest.raises(ValueError, match="non-negative"):
        VariogramModel(family="exponential", nugget=-0.6, partial_sill=1.0, range_km=4.0)
    with pytest.raises(ValueError, match="unknown variogram family"):
        VariogramModel(family="gaussian", nugget=0.1, partial_sill=1.0, range_km=4.0)
