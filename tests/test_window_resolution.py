"""window.py: the ONE metres->cells conversion (Contract 3 v3). These rules
are contract text — square windows to the nearest odd count (ties up, min 3),
radii round half up (min 1), too-coarse DEMs clamp and say so.
"""

from __future__ import annotations

import pytest

from engine.prospectivity.features.window import resolve_radius, resolve_square_window


def test_exact_multiple_resolves_without_clamping() -> None:
    resolved = resolve_square_window(window_m=2003.76, cell_size_m=222.64)
    assert resolved.cells == 9
    assert not resolved.clamped
    assert resolved.effective_m == pytest.approx(2003.76)


def test_nearest_odd_rounds_down_and_up() -> None:
    # raw 3.9 -> nearest odd 3; raw 2.2 -> nearest odd 3; raw 4.4 -> 5
    assert resolve_square_window(390.0, 100.0).cells == 3
    assert resolve_square_window(220.0, 100.0).cells == 3
    assert resolve_square_window(440.0, 100.0).cells == 5


def test_even_tie_rounds_up() -> None:
    # raw exactly 4: equidistant between 3 and 5 — documented tie rule: up.
    assert resolve_square_window(400.0, 100.0).cells == 5


def test_window_below_minimum_clamps_to_3_and_records_it() -> None:
    # 1400 m on the ~11.1 km synthetic-DEM cells: raw ~0.126 -> clamp.
    resolved = resolve_square_window(window_m=1400.0, cell_size_m=11132.0)
    assert resolved.cells == 3
    assert resolved.clamped
    assert resolved.effective_m == pytest.approx(3 * 11132.0)


def test_radius_rounds_half_up() -> None:
    assert resolve_radius(459.9, 463.8).cells == 1  # raw 0.99
    assert resolve_radius(2300.0, 463.8).cells == 5  # raw 4.96 (real GEBCO)
    assert not resolve_radius(2300.0, 463.8).clamped


def test_radius_below_minimum_clamps_to_1_and_records_it() -> None:
    resolved = resolve_radius(radius_m=460.0, cell_size_m=11132.0)
    assert resolved.cells == 1
    assert resolved.clamped


def test_nonpositive_inputs_raise() -> None:
    with pytest.raises(ValueError):
        resolve_square_window(0.0, 100.0)
    with pytest.raises(ValueError):
        resolve_square_window(100.0, -1.0)
    with pytest.raises(ValueError):
        resolve_radius(-5.0, 100.0)
