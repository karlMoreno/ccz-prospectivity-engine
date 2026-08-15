"""The empirical-variogram support report (E2.2 §1): great-circle binning,
honest empty bins, and the real corpus's support structure pinned.

Fixture-degeneracy note (CLAUDE.md testing convention 4, added E2.2-0):
the constructed three-point fixture separates its claims deliberately —
UNEQUAL spacings (≈1.11, 2.22, 3.34 km) put each pair in its own bin, so
per-bin semivariance is distinguishable from any global statistic; the
half factor is observable (pair semivariances 4.5, 12.5, 32.0 are halves
of 9, 25, 64, so dropping the ½ fails every literal); and the points sit
on a MERIDIAN with bin edges in km, so a Euclidean-degrees distance
(0.01 ≠ 1.11) would put every pair in the wrong bin — the geographic-vs-
planar claim is load-bearing, not decorative.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.prospectivity.estimators.variogram import (
    DEFAULT_BIN_EDGES_KM,
    empirical_variogram,
    pairwise_distances_km,
)
from engine.prospectivity.provenance.geometry import haversine_km
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource

# Three points on the 0° meridian at 0°, 0.01°, 0.03° latitude:
# great-circle separations ≈ 1.112, 2.224, 3.336 km (one degree of
# latitude ≈ 111.2 km). Values 1, 4, 9 → pair semivariances ½·3²=4.5,
# ½·5²=12.5, ½·8²=32.0 — all distinct.
MERIDIAN_COORDS = np.array([[0.0, 0.0], [0.0, 0.01], [0.0, 0.03]])
MERIDIAN_VALUES = np.array([1.0, 4.0, 9.0])
MERIDIAN_EDGES = (0.5, 2.0, 3.0, 4.0)


def test_hand_computed_semivariances_land_in_their_hand_computed_bins() -> None:
    ev = empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, MERIDIAN_EDGES)

    assert ev.total_pairs == 3
    assert [b.pair_count for b in ev.bins] == [1, 1, 1]
    assert [b.semivariance for b in ev.bins] == [4.5, 12.5, 32.0]


def test_distances_are_great_circle_km_not_euclidean_degrees() -> None:
    """The reason known_answer.empirical_semivariance was not reused: a
    0.01° latitude step is ≈1.112 km (not 0.01 of anything), and an E-W
    step of the same degree size is shorter by cos(latitude) — ≈3% at the
    study's 14°N. Both facts asserted against haversine_km directly."""
    ns = haversine_km(0.0, 0.0, 0.01, 0.0)
    assert 1.10 < ns < 1.12

    ew_at_equator = haversine_km(0.0, 0.0, 0.0, 0.01)
    ew_at_14n = haversine_km(14.0, 0.0, 14.0, 0.01)
    assert abs(ew_at_equator - ns) < 0.01
    assert 0.96 < ew_at_14n / ew_at_equator < 0.98

    distances = pairwise_distances_km(MERIDIAN_COORDS)
    assert np.allclose(sorted(distances), [ns, 2 * ns, 3 * ns], rtol=1e-6)


def test_an_empty_bin_is_reported_as_absent_not_dropped_and_not_zero() -> None:
    """count 0 with semivariance None — a zero would fabricate 'no
    variability at this lag' out of no data, and dropping the bin would
    hide the void the report exists to name."""
    ev = empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, (0.5, 2.0, 2.1, 3.0, 4.0))

    empty = ev.bins[1]
    assert empty.pair_count == 0
    assert empty.semivariance is None
    assert ev.unsupported() == (empty,)
    assert len(ev.bins) == 4  # the empty bin is present in the table


def test_real_corpus_support_structure_is_pinned() -> None:
    """The finding the report exists to state, as literals (the E2.0-2
    pinning precedent — the self-adjusting computation cannot fail when
    the structure changes): 595 pairs; 301 within 0–13 km; 294 between
    986–997 km; the 13–986 km bin has ZERO pairs — the unsupported range
    every fitted curve must cross as an assumption. Re-report when new
    sources land between the clusters (BACKLOG §1 geographic-spread
    item)."""
    obs = sorted(
        CorpusCsvSampleSource().get_training_samples(), key=lambda o: o.source_record_id
    )
    coords = np.array([[o.longitude, o.latitude] for o in obs])
    y = np.array([o.abundance_kg_m2 for o in obs])

    ev = empirical_variogram(coords, y, DEFAULT_BIN_EDGES_KM)

    assert ev.total_pairs == 595
    by_range = {(b.lag_lo_km, b.lag_hi_km): b for b in ev.bins}
    assert by_range[(13.0, 986.0)].pair_count == 0
    assert by_range[(13.0, 986.0)].semivariance is None
    assert ev.unsupported() == (by_range[(13.0, 986.0)],)
    assert by_range[(986.0, 997.0)].pair_count == 294
    within = sum(b.pair_count for b in ev.bins if b.lag_hi_km <= 13.0)
    assert within == 301


def test_two_reports_over_the_same_inputs_are_identical_in_every_field() -> None:
    first = empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, MERIDIAN_EDGES)
    second = empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, MERIDIAN_EDGES)
    assert first == second  # frozen dataclasses: full-state equality


def test_bad_edges_and_mismatched_inputs_are_refused_by_name() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, (2.0, 1.0))
    with pytest.raises(ValueError, match="strictly increasing"):
        empirical_variogram(MERIDIAN_COORDS, MERIDIAN_VALUES, (1.0,))
    with pytest.raises(ValueError, match="matching coords"):
        empirical_variogram(MERIDIAN_COORDS, np.array([1.0, 2.0]), MERIDIAN_EDGES)
    with pytest.raises(ValueError, match="lon/lat"):
        pairwise_distances_km(np.zeros(4))
