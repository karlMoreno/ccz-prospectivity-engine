"""Property tests for the DataOrigin taxonomy (P2.0b).

The domain is five members, so every property is checked EXHAUSTIVELY over the
full cross-product rather than by sampled examples — pairs (25), triples (125).
The ordering itself is pinned as an explicit literal first
(test_the_ordering_is_the_contracted_five_member_sequence), so the property
tests may derive expectations from the constant without becoming tautologies:
if the constant drifts, the literal pin fails before the properties can agree
with a wrong ordering.
"""

from __future__ import annotations

from itertools import product

import pytest

from engine.prospectivity.provenance.origin import (
    ALLOWED_AUTHORS,
    AUTHOR_MODEL,
    AUTHOR_UNRECORDED,
    ORIGIN_ORDER_MOST_REAL_FIRST,
    DataOrigin,
    combine_origins,
    validate_author,
)

ALL = ORIGIN_ORDER_MOST_REAL_FIRST


def _less_real(a: DataOrigin, b: DataOrigin) -> DataOrigin:
    """Expected winner, restated independently: whichever appears LATER in
    the pinned most-real-first tuple."""
    return a if ALL.index(a) >= ALL.index(b) else b


def test_the_ordering_is_the_contracted_five_member_sequence() -> None:
    """Pins the ordering as a literal (the P2.0b contract), so every other
    test may derive expectations from the constant without tautology."""
    assert ORIGIN_ORDER_MOST_REAL_FIRST == (
        DataOrigin.MEASURED,
        DataOrigin.DERIVED,
        DataOrigin.LITERATURE,
        DataOrigin.SYNTHETIC,
        DataOrigin.AUTHORED,
    )


def test_every_enum_member_is_in_the_ordering_and_nothing_else_is() -> None:
    """Completeness in both directions, mirroring CovariateRegistry's
    contract↔code version check. The failure names the offending member."""
    missing = set(DataOrigin) - set(ORIGIN_ORDER_MOST_REAL_FIRST)
    assert not missing, (
        f"ordering constant is missing enum member(s): {sorted(m.name for m in missing)}"
    )
    extra = [o for o in ORIGIN_ORDER_MOST_REAL_FIRST if not isinstance(o, DataOrigin)]
    assert not extra, f"ordering constant contains non-members: {extra!r}"
    duplicated = sorted(
        {o.name for o in ORIGIN_ORDER_MOST_REAL_FIRST if ORIGIN_ORDER_MOST_REAL_FIRST.count(o) > 1}
    )
    assert not duplicated, f"ordering constant duplicates member(s): {duplicated}"


def test_combine_returns_the_least_real_of_every_ordered_pair() -> None:
    for a, b in product(ALL, ALL):
        assert combine_origins([a, b]) == _less_real(a, b), f"pair ({a}, {b})"


def test_a_measured_corpus_does_not_launder_a_synthetic_terrain() -> None:
    """The motivating example, hard-coded rather than derived."""
    assert combine_origins([DataOrigin.MEASURED, DataOrigin.SYNTHETIC]) == DataOrigin.SYNTHETIC


def test_authored_absorbs_every_origin_including_itself() -> None:
    for other in ALL:
        assert combine_origins([other, DataOrigin.AUTHORED]) == DataOrigin.AUTHORED, f"({other}, AUTHORED)"
        assert combine_origins([DataOrigin.AUTHORED, other]) == DataOrigin.AUTHORED, f"(AUTHORED, {other})"


def test_combine_is_commutative_over_all_pairs() -> None:
    for a, b in product(ALL, ALL):
        assert combine_origins([a, b]) == combine_origins([b, a]), f"pair ({a}, {b})"


def test_combine_is_associative_and_flat_call_matches_pairwise_over_all_triples() -> None:
    for a, b, c in product(ALL, ALL, ALL):
        pairwise_left = combine_origins([combine_origins([a, b]), c])
        pairwise_right = combine_origins([a, combine_origins([b, c])])
        flat = combine_origins([a, b, c])
        assert pairwise_left == pairwise_right == flat, f"triple ({a}, {b}, {c})"


def test_combine_is_idempotent_for_singletons_and_repeats() -> None:
    for origin in ALL:
        assert combine_origins([origin]) == origin
        assert combine_origins([origin, origin, origin]) == origin


def test_combine_of_empty_input_raises_instead_of_defaulting() -> None:
    with pytest.raises(ValueError, match="at least one origin"):
        combine_origins([])


def test_combine_of_an_unknown_string_raises_naming_the_value() -> None:
    with pytest.raises(ValueError, match="FABRICATED"):
        combine_origins([DataOrigin.MEASURED, "FABRICATED"])


def test_combine_accepts_string_values_interchangeably_with_members() -> None:
    assert combine_origins(["MEASURED", "SYNTHETIC"]) == DataOrigin.SYNTHETIC
    assert combine_origins([DataOrigin.MEASURED, "SYNTHETIC"]) == DataOrigin.SYNTHETIC
    assert combine_origins(["MEASURED", DataOrigin.DERIVED]) == DataOrigin.DERIVED


def test_author_allow_list_is_the_contracted_set_and_contains_the_reserved_tokens() -> None:
    """Completeness both directions, as the ordering constant is tested: the
    allow-list is exactly the contracted literal (nothing missing, nothing
    extra), it contains both reserved-token constants, and no duplicates."""
    assert ALLOWED_AUTHORS == ("model", "karl", "isaac", "unrecorded")
    assert AUTHOR_MODEL in ALLOWED_AUTHORS
    assert AUTHOR_UNRECORDED in ALLOWED_AUTHORS
    assert len(ALLOWED_AUTHORS) == len(set(ALLOWED_AUTHORS)), "allow-list has duplicates"


def test_validate_author_accepts_every_allow_listed_author() -> None:
    for author in ALLOWED_AUTHORS:
        assert validate_author(author) == author


@pytest.mark.parametrize(
    "bad",
    ["moddel", "Isaac", "", "   ", None, 7],
    ids=["typo-moddel", "case-Isaac", "empty", "whitespace", "none", "int"],
)
def test_validate_author_rejects_unknown_authors_naming_value_and_allow_list(bad: object) -> None:
    """The typo case is the motivating one: under free text, "moddel"
    validated as a person's name — the model-authored origin hiding behind
    the safe-looking answer."""
    with pytest.raises(ValueError, match="author must be one of"):
        validate_author(bad)
