"""Contract 8 (data/config/model_config.yaml) parses, and its loader keeps
missing-vs-null distinct and the P2.B enum closed."""

from __future__ import annotations

import pytest

from engine.prospectivity.model_config import (
    ADMISSIBLE_THRESHOLD_ORIGINS,
    DeclaredField,
    acceptance_thresholds,
    load_model_config,
    target_definition,
)
from engine.prospectivity.provenance.origin import DataOrigin


def test_contract_8_parses_and_every_declared_field_is_present_or_explicitly_null() -> None:
    """Version 2 (C8.1 added acceptance_thresholds), the file-level
    classification, and the rule both accessors enforce: a declared field
    always carries an explicit `value` key — ABSENT and NULL are different
    states, so a field that means "undecided" must SAY null rather than be
    missing."""
    contract = load_model_config()
    assert contract["model_config_version"] == 2
    # The first value-bearing file created under the authoring rule: it is
    # classified in-file (the audit walk enforces this; probed in P2.A).
    assert contract["data_origin"] == "AUTHORED"
    assert contract["author"] == "model"

    declared_fields = {"target_definition", "acceptance_thresholds"}
    assert declared_fields <= set(contract), "a declared field must never be absent"
    for name in declared_fields:
        assert "value" in contract[name], (
            f"{name} has no `value` key — present-or-explicitly-null, never absent"
        )


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


# ------------------------------------------------- C8.1: the acceptance gate
#
# The slot P2.A deferred until a consumer existed. E2.5 built the consumer;
# these tests pin the loader's THREE STATES and its TWO OUTRIGHT REJECTIONS.


def test_the_shipped_gate_is_null_and_unclassified_which_is_the_awaiting_state() -> None:
    """The real contract, not a fixture: the gate ships awaiting Track G, and
    an awaiting field carries NO origin because there is no value to
    classify. This is the state E2.5's precondition 6 refuses by name."""
    declared = acceptance_thresholds()
    assert declared == DeclaredField(value=None, data_origin=None, author=None)


def test_a_missing_acceptance_thresholds_field_raises_and_is_not_treated_as_null() -> None:
    """Missing != null, the same rule target_definition carries. After C8.1 an
    absent field means the contract was edited, not that the gate is
    undecided — so it raises rather than reading as "awaiting"."""
    with pytest.raises(ValueError, match="no acceptance_thresholds field"):
        acceptance_thresholds(contract={"model_config_version": 2})


def test_an_explicitly_null_gate_is_returned_as_the_awaiting_state_without_raising() -> None:
    """NULL is not an error: the guard reads it and refuses BY NAME, which is
    the designed path. A loader that raised here would collapse "no gate yet"
    into "broken contract"."""
    declared = acceptance_thresholds(contract={"acceptance_thresholds": {"value": None}})
    assert declared.value is None and declared.data_origin is None


def test_a_populated_gate_returns_its_value_and_declared_origin_in_one_call() -> None:
    """The whole point of DeclaredField: a consumer asks "what is the gate,
    and is it a finding or a stand-in?" once. The value is carried through
    VERBATIM — a distinctive string, so a loader that returned a canned or
    reformatted value could not pass."""
    declared = acceptance_thresholds(
        contract={
            "acceptance_thresholds": {
                "value": "rmse_uplift >= 0.15 on leave_one_site_out",
                "data_origin": "LITERATURE",
                "author": None,
            }
        }
    )
    assert declared == DeclaredField(
        value="rmse_uplift >= 0.15 on leave_one_site_out",
        data_origin="LITERATURE",
        author=None,
    )


def test_an_authored_gate_is_rejected_outright_naming_the_asymmetry_with_the_target() -> None:
    """THE REFUSAL THIS TASK EXISTS FOR — and the one a task prompt once
    assumed already existed. AUTHORED means "written with no external
    source", which for a GATE is Track E inventing the standard its own work
    is measured against. Rejected at the LOADER, so it never reaches a
    consumer at all.

    The message must carry the asymmetry, because the rule looks inconsistent
    next to target_definition (whose AUTHORED default is fine) and an
    unexplained inconsistency invites someone to "fix" it."""
    with pytest.raises(ValueError, match="declared AUTHORED") as refusal:
        acceptance_thresholds(
            contract={
                "acceptance_thresholds": {
                    "value": "rmse_uplift >= 0.15",
                    "data_origin": "AUTHORED",
                    "author": "model",
                }
            }
        )
    message = str(refusal.value)
    assert "REJECTED, NOT RECORDED" in message
    assert "inventing the standard its own work is measured against" in message
    assert "ASYMMETRY" in message and "target_definition" in message
    assert "BECOMES THE VERDICT" in message


def test_a_synthetic_gate_is_rejected_by_the_realness_order_not_by_a_hand_listed_set() -> None:
    """AUTHORED is not the only inadmissible origin, and the rule is not a
    list someone maintains: a gate must be at least as real as LITERATURE on
    the taxonomy's own order. SYNTHETIC separates the two possible
    implementations — a deny-list of {AUTHORED} would ACCEPT this."""
    with pytest.raises(ValueError, match="declared SYNTHETIC"):
        acceptance_thresholds(
            contract={
                "acceptance_thresholds": {"value": "x", "data_origin": "SYNTHETIC"}
            }
        )


def test_the_admissible_origins_are_exactly_measured_derived_literature() -> None:
    """Guards the slice arithmetic that derives the set from the realness
    order: an off-by-one would silently admit SYNTHETIC, which is precisely
    the failure the previous test would then stop catching."""
    assert ADMISSIBLE_THRESHOLD_ORIGINS == (
        DataOrigin.MEASURED,
        DataOrigin.DERIVED,
        DataOrigin.LITERATURE,
    )
    assert DataOrigin.AUTHORED not in ADMISSIBLE_THRESHOLD_ORIGINS
    assert DataOrigin.SYNTHETIC not in ADMISSIBLE_THRESHOLD_ORIGINS


def test_a_populated_gate_with_no_declared_origin_is_rejected_as_unclassified() -> None:
    """"null, awaiting classification" and "classified" must stay different
    states (P2.A): a value may never arrive without an origin attached, or
    the awaiting state would silently accept a populated-but-unprovenanced
    gate."""
    # Matched on the ACCESSOR's own wording, not the shared phrase "with no
    # data_origin": the DeclaredField backstop raises with that phrase too, so
    # a looser regex would pass while the accessor's check was gone — the
    # assertion would be real and blind (CLAUDE.md convention 4).
    with pytest.raises(ValueError, match=r"acceptance_thresholds declares value 'x'"):
        acceptance_thresholds(contract={"acceptance_thresholds": {"value": "x"}})


def test_an_unknown_origin_label_raises_instead_of_ranking_silently() -> None:
    """A typo must not fall through to "not admissible" by accident — it
    raises on the vocabulary, the same posture combine_origins takes."""
    with pytest.raises(ValueError, match="not a valid DataOrigin"):
        acceptance_thresholds(
            contract={
                "acceptance_thresholds": {"value": "x", "data_origin": "LITERATUR"}
            }
        )


def test_the_carrier_itself_refuses_a_value_with_no_origin() -> None:
    """The structural backstop, tested directly rather than assumed: the
    accessors refuse first with a better message, but the invariant is what
    makes "populated but unclassified" unrepresentable for any FUTURE
    accessor. A null value with an origin stays legal — target_definition
    ships exactly that shape, so the invariant is an implication, not a
    biconditional, and this test pins both halves.

    SOLE OBSERVER (E2.0-1b convention, measured at C8.1): with the invariant
    replaced by `if False`, this test is THE ONLY ONE in the whole suite that
    fails (470 tests, one failure). Weakening it removes the last check that
    a value can never be carried unclassified — the accessors' own refusals
    do not cover a future accessor that forgets."""
    with pytest.raises(ValueError, match="a value cannot arrive unclassified"):
        DeclaredField(value="x", data_origin=None, author=None)
    assert DeclaredField(value=None, data_origin="AUTHORED", author="model").value is None
