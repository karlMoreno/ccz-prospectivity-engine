"""CovariateRegistry: contract completeness (Test 3), the recipe_version
integrity check, and Option B staying out (Test 6). Mirrors E1.2's
NormalizerRegistry guarantees, keyed by covariate name.
"""

from __future__ import annotations

import copy

import pytest

from engine.prospectivity.features._contract import (
    candidate_covariates,
    enabled_covariates,
    load_covariates_yaml,
)
from engine.prospectivity.features.registry import RECIPE_CLASSES, build_default_registry


def test_every_enabled_contract_entry_has_exactly_one_recipe_in_contract_order() -> None:
    registry = build_default_registry()
    expected = [entry["name"] for entry in enabled_covariates()]
    assert registry.names() == expected  # both directions AND order
    assert len(expected) == 8  # the Option-A list


def test_contract_registry_version_is_3() -> None:
    assert load_covariates_yaml()["registry_version"] == 3


def test_recipe_version_mismatch_fails_loudly() -> None:
    """The contract's own rule: recipe math/params and recipe_version move
    together. A contract bump without a code change (or vice versa) must
    refuse to build, not silently compute the old thing."""
    contract = copy.deepcopy(load_covariates_yaml())
    roughness = next(e for e in contract["covariates"] if e["name"] == "roughness")
    roughness["recipe_version"] += 1
    with pytest.raises(ValueError, match="recipe_version mismatch"):
        build_default_registry(contract)


def test_enabling_an_unimplemented_recipe_fails_loudly() -> None:
    """Flipping an Option-B entry to enabled without implementing it must
    raise at registry construction — never a silently absent feature."""
    contract = copy.deepcopy(load_covariates_yaml())
    sediment = next(e for e in contract["candidate_covariates"] if e["name"] == "sediment_type")
    sediment["enabled"] = True
    contract["covariates"].append(sediment)
    with pytest.raises(ValueError, match="no implementation"):
        build_default_registry(contract)


def test_unknown_covariate_name_raises_keyerror() -> None:
    registry = build_default_registry()
    with pytest.raises(KeyError, match="sediment_type"):
        registry.build("sediment_type", grid=None)


def test_option_b_candidates_stay_disabled_and_unimplemented() -> None:
    """Test 6: sediment_type, surface_chlorophyll, ccd_minus_depth,
    bathymetric_regime remain enabled: false in the contract, absent from
    the registry, and their recipe strings have no implementation class."""
    candidates = candidate_covariates()
    names = {entry["name"] for entry in candidates}
    assert names == {"sediment_type", "surface_chlorophyll", "ccd_minus_depth", "bathymetric_regime"}
    assert all(entry["enabled"] is False for entry in candidates)

    registry_names = set(build_default_registry().names())
    assert registry_names.isdisjoint(names)

    candidate_recipes = {entry["recipe"] for entry in candidates}
    assert candidate_recipes.isdisjoint(RECIPE_CLASSES)  # not even implementable
