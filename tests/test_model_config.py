"""Contract 8 (data/config/model_config.yaml) parses, and its loader keeps
missing-vs-null distinct and the P2.B enum closed."""

from __future__ import annotations

import pytest

from engine.prospectivity.model_config import (
    DeclaredField,
    load_model_config,
    target_definition,
)


def test_contract_8_parses_with_version_1_and_a_file_level_classification() -> None:
    contract = load_model_config()
    assert contract["model_config_version"] == 1
    # The first value-bearing file created under the authoring rule: it is
    # classified in-file (the audit walk enforces this; probed in P2.A).
    assert contract["data_origin"] == "AUTHORED"
    assert contract["author"] == "model"


def test_target_definition_returns_value_and_declared_origin_in_one_call() -> None:
    """The consumer can ask "what is y, and is that a finding or a
    stand-in?" without a second lookup: AUTHORED/model IS the provisional
    marker (no separate flag exists — the origin transition to LITERATURE is
    the promotion)."""
    declared = target_definition()
    assert declared == DeclaredField(
        value="total_as_published", data_origin="AUTHORED", author="model"
    )


def test_a_missing_target_definition_field_raises_and_is_not_treated_as_null() -> None:
    with pytest.raises(ValueError, match="no target_definition field"):
        target_definition(contract={"model_config_version": 1})


def test_an_explicitly_null_value_is_returned_as_a_declared_absence() -> None:
    declared = target_definition(
        contract={
            "target_definition": {
                "value": None,
                "admissible_values": ["total_as_published"],
                "data_origin": "AUTHORED",
                "author": "model",
            }
        }
    )
    assert declared.value is None
    assert declared.data_origin == "AUTHORED"


def test_a_value_outside_the_enum_raises_naming_value_and_admissible_set() -> None:
    with pytest.raises(
        ValueError, match=r"'surface_only_from_05_depths'.*'total_as_published'"
    ):
        target_definition(
            contract={
                "target_definition": {
                    "value": "surface_only_from_05_depths",
                    "admissible_values": ["total_as_published"],
                    "data_origin": "AUTHORED",
                    "author": "model",
                }
            }
        )
