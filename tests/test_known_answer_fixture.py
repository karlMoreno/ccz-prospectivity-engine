"""The known-answer fixture generators (E2.1 §3): deterministic, honestly
parameterized, and consistent with what they claim to plant — plus the loop
closed on the one estimator that exists (the baseline recovers a generated
field's mean and SD).

Deliberately NOT here (deferred, per the fixture docstring): variogram
FITTING (E2.2 builds the fitter and tests it against this fixture), RF
importance recovery (E2.3), CV-leakage measurement (E2.4). The variogram
assertion below is a coarse consistency check against the planted range,
not a fit.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
from engine.prospectivity.provenance.origin import DataOrigin
from tests.fixtures import known_answer
from tests.fixtures.known_answer import (
    covariate_driven_field,
    empirical_semivariance,
    gaussian_process_field,
    grid_layout,
)


def test_the_fixture_module_declares_synthetic_with_generator_and_seed_evidence() -> None:
    """The taxonomy's acceptance shape for a new SYNTHETIC fixture module
    (P2.0d-2 §0.1): origin, generator import path, and seed evidence all
    present — the audit test enumerates tracked files and validates
    exactly these constants."""
    assert known_answer.DATA_ORIGIN == DataOrigin.SYNTHETIC
    assert known_answer.DATA_GENERATOR == "tests.fixtures.known_answer"
    assert known_answer.DATA_SEEDS is not None


def test_generators_are_deterministic_and_seed_sensitive() -> None:
    """Same coords + params + seed → identical output, twice, for every
    generator; a different seed → a different field (the negation, so
    'deterministic' cannot be satisfied by a constant output)."""
    coords = grid_layout(6, spacing=2.0)
    assert np.array_equal(coords, grid_layout(6, spacing=2.0))

    first = gaussian_process_field(coords, variogram_range=8.0, sill=2.0, nugget=0.2, seed=7)
    second = gaussian_process_field(coords, variogram_range=8.0, sill=2.0, nugget=0.2, seed=7)
    other = gaussian_process_field(coords, variogram_range=8.0, sill=2.0, nugget=0.2, seed=8)
    assert np.array_equal(first, second)
    assert not np.array_equal(first, other)

    Xa, ya = covariate_driven_field(50, 4, driving_column=2, coefficient=3.0, noise_sd=1.0, seed=5)
    Xb, yb = covariate_driven_field(50, 4, driving_column=2, coefficient=3.0, noise_sd=1.0, seed=5)
    Xc, yc = covariate_driven_field(50, 4, driving_column=2, coefficient=3.0, noise_sd=1.0, seed=6)
    assert np.array_equal(Xa, Xb) and np.array_equal(ya, yb)
    assert not np.array_equal(ya, yc)


def test_baseline_recovers_a_generated_fields_mean_and_sd() -> None:
    """Closing the loop on the one estimator that exists: on a generated
    field, the baseline returns exactly the field's mean and sample SD —
    both computable from the fixture's own output, so the expected values
    are not the implementation's."""
    coords = grid_layout(8)
    y = gaussian_process_field(coords, variogram_range=5.0, sill=1.5, nugget=0.1, seed=11, mean=6.0)

    baseline = MeanBaselineEstimator()
    baseline.fit(coords, y)
    mean, sd = baseline.predict(coords)

    expected_mean = float(np.asarray(y).mean())
    expected_sd = float(np.asarray(y).std(ddof=1))
    assert np.all(mean == expected_mean)
    assert np.all(sd == expected_sd)
    assert abs(expected_mean - 6.0) < 1.5  # the planted mean, coarsely


def test_generated_field_semivariance_is_consistent_with_the_planted_range() -> None:
    """Coarse consistency, not a fit (the fitter is E2.2's): with range 10
    on a 12×12 unit grid, semivariance at short lags (h < 2) sits well
    below semivariance past the range (h ≥ 10); in the pure-nugget
    degenerate case (nugget == sill, zero spatial structure) the same
    ratio is near 1. Seed pinned; both bins carry hundreds of pairs
    (asserted, so the claim is never made from an empty bin)."""
    coords = grid_layout(12, spacing=1.0)
    edges = np.array([0.5, 2.0, 10.0, 14.0])

    structured = gaussian_process_field(coords, variogram_range=10.0, sill=1.0, nugget=0.1, seed=1)
    semivariance, counts = empirical_semivariance(coords, structured, lag_edges=edges)
    assert counts[0] > 100 and counts[2] > 100
    assert semivariance[0] < 0.5 * semivariance[2]

    flat = gaussian_process_field(coords, variogram_range=10.0, sill=1.0, nugget=1.0, seed=1)
    flat_semivariance, _ = empirical_semivariance(coords, flat, lag_edges=edges)
    assert flat_semivariance[0] > 0.6 * flat_semivariance[2]


def test_covariate_field_is_the_stated_function_of_the_named_column() -> None:
    """y − coefficient·X[:, driving_column] must be exactly the noise term:
    mean near 0, SD near noise_sd, and uncorrelated with the driving
    column — the construction verified from the outputs, coarsely, without
    building the E2.3 recoverer."""
    X, y = covariate_driven_field(500, 8, driving_column=3, coefficient=2.0, noise_sd=1.0, seed=42)

    assert X.shape == (500, 8) and y.shape == (500,)
    residual = y - 2.0 * X[:, 3]
    assert abs(residual.mean()) < 0.15
    assert 0.85 < residual.std(ddof=1) < 1.15
    assert abs(np.corrcoef(residual, X[:, 3])[0, 1]) < 0.1
    # And the driving column really drives: correlation with y far above
    # any noise column's.
    driving_corr = abs(np.corrcoef(y, X[:, 3])[0, 1])
    noise_corrs = [abs(np.corrcoef(y, X[:, j])[0, 1]) for j in range(8) if j != 3]
    assert driving_corr > 0.8
    assert max(noise_corrs) < 0.2


def test_generator_parameter_refusals_name_the_bad_value() -> None:
    coords = grid_layout(4)
    with pytest.raises(ValueError, match="nugget"):
        gaussian_process_field(coords, variogram_range=5.0, sill=1.0, nugget=2.0, seed=0)
    with pytest.raises(ValueError, match="range"):
        gaussian_process_field(coords, variogram_range=0.0, sill=1.0, nugget=0.1, seed=0)
    with pytest.raises(ValueError, match="coords"):
        gaussian_process_field(np.zeros(5), variogram_range=5.0, sill=1.0, nugget=0.1, seed=0)
    with pytest.raises(ValueError, match="driving_column"):
        covariate_driven_field(10, 3, driving_column=3, coefficient=1.0, noise_sd=1.0, seed=0)
    with pytest.raises(ValueError, match="n_side"):
        grid_layout(1)
