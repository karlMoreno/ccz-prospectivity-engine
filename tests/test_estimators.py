"""Estimator ABC (pairing enforced by the template method), the
EstimatorRegistry's baseline guarantee, and MeanBaselineEstimator's
hand-computed arithmetic (E2.1).

Fixture-distinguishability notes (CLAUDE.md corollary): the primary
hand-computed fixture is [13, 11, 8, 9, 9] — mean 10.0, sample SD exactly
2.0 (deviations 3, 1, −2, −1, −1; SS 16; 16/4 = 4) — chosen because it
distinguishes the claim from every plausible impostor statistic at once:
median 9, half-range 2.5, mean-absolute-deviation 1.6, population SD
(ddof=0) ≈ 1.789, SE = 2/√5 ≈ 0.894. The E2.1 review found the previous
fixture [2, 4, 6] degenerate three ways (mean == median; SD == half-range
== MAD == 2.0), letting a spread-statistic swap survive every
hand-computed test. The [0, 2, 10] mean-not-median test is kept as the
named observer for that specific claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator
from engine.prospectivity.estimators.registry import (
    MEAN_BASELINE_NAME,
    EstimatorRegistry,
    build_default_registry,
)
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import (
    build_default_registry as build_covariate_registry,
)
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.training_matrix import assemble_training_matrix, matrix_watermark
from tests.fixtures.rasters import write_synthetic_bathymetry

REPO_ROOT = Path(__file__).resolve().parent.parent


# ------------------------------------------------- hand-computed baseline


def test_baseline_predicts_the_hand_computed_mean_and_sample_sd_everywhere() -> None:
    """y = [13, 11, 8, 9, 9]: mean 10.0; deviations (3, 1, −2, −1, −1),
    SS 16, sample variance 16/4 = 4, SD (ddof=1) exactly 2.0. Five
    requested rows all get exactly that pair — not "output is not null".
    The fixture distinguishes SD from half-range (2.5), MAD (1.6), ddof=0
    (≈1.789), and SE (≈0.894) — see the module docstring for why."""
    baseline = MeanBaselineEstimator()
    baseline.fit(features=np.zeros((5, 2)), target=[13.0, 11.0, 8.0, 9.0, 9.0])

    mean, sd = baseline.predict(np.zeros((5, 2)))

    assert mean.shape == sd.shape == (5,)
    assert np.all(mean == 10.0)
    assert np.all(sd == 2.0)


def test_baseline_mean_is_the_mean_not_the_median() -> None:
    """[0, 2, 10]: mean 4.0, median 2.0. The SD fixture above cannot tell
    them apart (its mean equals its median); this one can."""
    baseline = MeanBaselineEstimator()
    baseline.fit(features=np.zeros((3, 1)), target=[0.0, 2.0, 10.0])
    mean, _ = baseline.predict(np.zeros((2, 1)))
    assert np.all(mean == 4.0)


def test_baseline_uncertainty_is_sd_not_standard_error() -> None:
    """The stated decision: predictive spread (SD), not mean-estimation
    error (SE = SD/√n). On [13, 11, 8, 9, 9] SE would be 2/√5 ≈ 0.894 —
    assert the value is exactly 2.0 and explicitly not the SE, so a silent
    SD→SE swap cannot pass as a rounding change."""
    baseline = MeanBaselineEstimator()
    baseline.fit(features=np.zeros((5, 1)), target=[13.0, 11.0, 8.0, 9.0, 9.0])
    _, sd = baseline.predict(np.zeros((1, 1)))
    assert sd[0] == 2.0
    assert not np.isclose(sd[0], 2.0 / np.sqrt(5))


def test_baseline_output_ignores_feature_values_by_construction() -> None:
    """"Predicts the training mean EVERYWHERE": two feature blocks with the
    same row count but wildly different values get identical output."""
    baseline = MeanBaselineEstimator()
    baseline.fit(features=np.zeros((5, 2)), target=[13.0, 11.0, 8.0, 9.0, 9.0])

    first = baseline.predict(np.zeros((4, 2)))
    second = baseline.predict(np.full((4, 2), 1e6))

    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])


def test_baseline_refuses_unfit_predict_tiny_n_non_finite_and_2d_targets() -> None:
    baseline = MeanBaselineEstimator()
    with pytest.raises(ValueError, match="before fit"):
        baseline.predict(np.zeros((2, 1)))
    with pytest.raises(ValueError, match="undefined below n=2"):
        MeanBaselineEstimator().fit(np.zeros((1, 1)), [5.0])
    with pytest.raises(ValueError, match="NaN or infinity"):
        MeanBaselineEstimator().fit(np.zeros((3, 1)), [1.0, np.nan, 3.0])
    # inf is not NaN: the E2.1 review probe showed an isnan-only check
    # accepting [1, inf, 3] and predict then emitting mean=inf, sd=NaN —
    # the exact silent-NaN-uncertainty failure the n<2 refusal names.
    with pytest.raises(ValueError, match="NaN or infinity"):
        MeanBaselineEstimator().fit(np.zeros((3, 1)), [1.0, np.inf, 3.0])
    with pytest.raises(ValueError, match="one-dimensional"):
        MeanBaselineEstimator().fit(np.zeros((2, 1)), [[1.0, 2.0], [3.0, 4.0]])
    fitted = MeanBaselineEstimator()
    fitted.fit(np.zeros((3, 1)), [1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="features with a length"):
        fitted.predict(7)


# ------------------------------------------ the pairing rule is structural


class _UnpairedEstimator(Estimator):
    """Test double whose _predict returns whatever the test plants —
    constructed directly so the ABC's validation (the rule under test) is
    the only thing between the bad return and the caller. Declares the
    E2.4 routing/semantics (required to be declarable at all)."""

    input_kind = "covariates"
    uncertainty_method = "test_double"
    uncertainty_semantics = "test double"

    def __init__(self, result: Any) -> None:
        self._result = result

    def fit(self, features: Any, target: Any) -> None:  # pragma: no cover
        pass

    def _predict(self, features: Any) -> Any:
        return self._result

    def provenance(self) -> dict:  # pragma: no cover
        return {}


def test_predict_refuses_a_none_uncertainty_naming_the_missing_half() -> None:
    with pytest.raises(ValueError, match="None for std"):
        _UnpairedEstimator((np.zeros(3), None)).predict(np.zeros((3, 1)))
    with pytest.raises(ValueError, match="None for mean"):
        _UnpairedEstimator((None, np.zeros(3))).predict(np.zeros((3, 1)))


def test_predict_refuses_bare_array_wrong_arity_and_non_tuple_pairs() -> None:
    """A bare (2, n) array unpacks positionally into two rows and would
    silently impersonate the pair — refused as not-a-tuple, along with a
    3-tuple and a correct-arity 2-LIST (the contract is a tuple, stated —
    a list pair carries both halves but is refused for container type)."""
    for bad in (np.zeros((2, 3)), (np.zeros(3), np.zeros(3), "extra"), [np.zeros(3), np.zeros(3)]):
        with pytest.raises(ValueError, match="2-tuple"):
            _UnpairedEstimator(bad).predict(np.zeros((3, 1)))


def test_predict_refuses_shape_mismatched_nan_and_negative_std_pairs() -> None:
    """The E2.1 review probes: a (5,) mean with a (3,) std leaves two
    predictions with no paired uncertainty inside a well-formed tuple; a
    NaN std is an absent uncertainty wearing a float dtype; a negative std
    is not a standard deviation. All refused by the template method."""
    with pytest.raises(ValueError, match="shapes must match"):
        _UnpairedEstimator((np.zeros(5), np.zeros(3))).predict(np.zeros((5, 1)))
    with pytest.raises(ValueError, match="non-finite std"):
        _UnpairedEstimator((np.zeros(5), np.full(5, np.nan))).predict(np.zeros((5, 1)))
    with pytest.raises(ValueError, match="negative std"):
        _UnpairedEstimator((np.zeros(5), np.array([1.0, 1.0, -1.0, 1.0, 1.0]))).predict(
            np.zeros((5, 1))
        )


def test_a_subclass_overriding_predict_is_refused_at_class_definition() -> None:
    """The must-fix from the E2.1 adversarial review: 'final by convention'
    is no enforcement — a subclass overriding predict() bypassed the
    pairing validation entirely (returning a bare (2, n) array straight
    through the engine seam) and still passed the registry's isinstance
    gate. __init_subclass__ now refuses the override at class-definition
    time, so a bypassing estimator cannot even be declared."""
    with pytest.raises(TypeError, match="overrides Estimator.predict"):

        class _RogueEstimator(Estimator):
            input_kind = "covariates"
            uncertainty_method = "rogue"
            uncertainty_semantics = "rogue"

            def fit(self, features: Any, target: Any) -> None:
                pass

            def predict(self, features: Any) -> Any:  # the bypass
                return np.zeros((2, 5))

            def _predict(self, features: Any) -> Any:
                return np.zeros(5), np.zeros(5)

            def provenance(self) -> dict:
                return {}


# ---------------------------------------------------------- the registry


def test_default_registry_contains_the_baseline_and_passes_completeness() -> None:
    registry = build_default_registry()
    assert MEAN_BASELINE_NAME in registry.names()
    registry.assert_complete()
    assert isinstance(registry.get(MEAN_BASELINE_NAME), MeanBaselineEstimator)


def test_completeness_fails_by_name_when_the_baseline_is_absent() -> None:
    """The structural half of CLAUDE.md's "baseline alongside every claim":
    a registry without the baseline cannot pass assert_complete."""
    registry = EstimatorRegistry()
    with pytest.raises(ValueError, match="mean_baseline"):
        registry.assert_complete()


def test_registry_refuses_duplicates_non_estimators_and_names_unknown_lookups() -> None:
    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    with pytest.raises(ValueError, match="registered twice"):
        registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    with pytest.raises(TypeError, match="not an Estimator"):
        registry.register("impostor", object())  # type: ignore[arg-type]
    with pytest.raises(KeyError, match="impostor"):
        registry.get("impostor")


# ------------------------------------------------- real-matrix end to end


def test_baseline_runs_on_the_real_training_matrix_and_the_watermark_wiring_holds(
    tmp_path: Path,
) -> None:
    """End to end on the E2.0-3 matrix: 35 predictions all equal to the
    training mean, 35 uncertainties all equal to the training SD (ddof=1),
    and the matrix's SYNTHETIC computed origin means whatever consumes this
    is watermarked — the wiring asserted, not just the fixture."""
    dem_path = tmp_path / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    stack_manifest = json.loads(written["provenance"].read_text())
    corpus_manifest = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
    grid = DemGrid.load(dem_path)
    layers = build_covariate_registry().build_all(grid)
    matrix, manifest = assemble_training_matrix(
        CorpusCsvSampleSource(), grid, layers, corpus_manifest, stack_manifest
    )

    baseline = build_default_registry().get(MEAN_BASELINE_NAME)
    baseline.fit(matrix.X, matrix.y)
    mean, sd = baseline.predict(matrix.X)

    assert mean.shape == sd.shape == (35,)
    assert np.all(mean == matrix.y.mean())
    assert np.all(sd == matrix.y.std(ddof=1))
    assert manifest.data_origin == "SYNTHETIC"
    assert matrix_watermark(manifest.data_origin) is not None
