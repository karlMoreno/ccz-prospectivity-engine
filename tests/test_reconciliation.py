"""Cross-dataset reconciliation between [01] (PANGAEA.904967 — the authors'
own published per-event aggregate) and [05] (PANGAEA.904962 — individual
nodule measurements aggregated by NoduleAggregateAdapter): two
INDEPENDENTLY PUBLISHED datasets describing the SAME 36 box-core events
(D8, 2026-07-27 review). Agreement here is strong external evidence [05]'s
aggregation (D5) is correct; disagreement is an honest, documented residual
that the tolerance must NOT be widened to hide.

Compares raw adapter output (`adapter.adapt(adapter.fetch())`), not the
merged corpus — this test is about whether the two independent SOURCES
agree with each other, which is a fact about the data, not about which row
a later dedup merge happens to keep (that's `dedup_rules.py`'s and D1's
concern, untouched here).
"""

from __future__ import annotations

import pytest

from engine.prospectivity.ingestion.corpus_builder import (
    build_boxcore_adapter,
    build_nodule_aggregate_adapter,
)

# Observed max |nodule_mass_kg delta| across all 36 events (SO268/1_76-1):
# 0.285 kg. Picked FROM the data (not a round number chosen for
# convenience). Two independent rounding effects explain most of the
# spread: [01]'s published mass is rounded to 1 decimal place (+/-0.05kg
# rounding error), and [05]'s individual nodule masses are quantized to 5g
# by the recording equipment itself ("up to the measurement limit (5g)" —
# PANGAEA.904962's own abstract), so summing N quantized values can drift by
# up to a few multiples of 2.5g before either side's own rounding. Most
# events land well under this ceiling (mean |delta| ~0.036kg); 0.285kg is
# the true observed worst case, not a typical one, and the assertion below
# actually needs it (a smaller tolerance would fail on real data).
MASS_TOLERANCE_KG = 0.285

# Confirmed against the raw files, 2026-07-27: [01]'s published Nodules [#]
# does not always include [05]'s "Plus N nodules of less than 5g" unweighed
# counts, even though it does for most of the 12 events carrying such an
# annotation. Four of these residuals were anticipated going into this task;
# SO268/2_205-2 (+16) was NOT — found while writing this test, verified by
# hand against both raw files (see D8 review report), and reported as a
# genuine 5th residual rather than silently folded into "close enough."
KNOWN_COUNT_RESIDUALS = {
    "SO268/1_15-3": 1,
    "SO268/2_95-2": 2,
    "SO268/2_140-1": -6,
    "SO268/2_175-1": -1,
    "SO268/2_205-2": 16,
}


def _load_01_per_event() -> dict[str, dict[str, float]]:
    adapter = build_boxcore_adapter()
    records = adapter.adapt(adapter.fetch())
    by_event: dict[str, dict[str, float]] = {}
    for record in records:
        if record["evidence_class"] == "MASS":
            by_event.setdefault(record["event_id"], {})["mass_kg"] = record["nodule_mass_kg"]
        elif record["evidence_class"] == "COUNT":
            by_event.setdefault(record["event_id"], {})["count"] = record["nodule_count"]
    return by_event


def _load_05_per_event() -> dict[str, dict[str, float]]:
    adapter = build_nodule_aggregate_adapter()
    records = adapter.adapt(adapter.fetch())
    by_event: dict[str, dict[str, float]] = {}
    for record in records:
        if record["evidence_class"] == "MASS":
            by_event.setdefault(record["event_id"], {})["mass_kg"] = record["nodule_mass_kg"]
        elif record["evidence_class"] == "COUNT":
            by_event.setdefault(record["event_id"], {})["count"] = record["nodule_count"]
    return by_event


# --- D: the reconciliation test ---------------------------------------------


def test_nodule_count_reconciles_exactly_for_at_least_31_of_36_events() -> None:
    f01 = _load_01_per_event()
    f05 = _load_05_per_event()
    assert set(f01) == set(f05)  # every event present on both sides
    assert len(f01) == 36

    mismatches = {
        event: f05[event]["count"] - f01[event]["count"]
        for event in f01
        if f05[event]["count"] != f01[event]["count"]
    }

    # An honest, documented residual -- do NOT loosen this to make it pass.
    assert mismatches == KNOWN_COUNT_RESIDUALS
    assert len(f01) - len(mismatches) >= 31


def test_nodule_mass_kg_agrees_within_the_observed_tolerance_for_every_event() -> None:
    f01 = _load_01_per_event()
    f05 = _load_05_per_event()
    max_observed_delta = 0.0
    for event in f01:
        delta = abs(f05[event]["mass_kg"] - f01[event]["mass_kg"])
        max_observed_delta = max(max_observed_delta, delta)
        # +1e-9: float representation slack ONLY (e.g. 0.285 vs
        # 0.28500000000000014 from summing 5g-quantized floats) -- not a
        # loosening of the tolerance itself.
        assert delta <= MASS_TOLERANCE_KG + 1e-9, (
            f"{event}: |{f05[event]['mass_kg']} - {f01[event]['mass_kg']}| = "
            f"{delta:.3f}kg exceeds the {MASS_TOLERANCE_KG}kg tolerance"
        )
    # The tolerance is the observed ceiling, not padding: confirm some event
    # actually reaches it, otherwise the bound above is untested.
    assert max_observed_delta == pytest.approx(MASS_TOLERANCE_KG, abs=1e-6)


def test_boxcore_mass_times_four_lands_in_the_published_ccz_abundance_band() -> None:
    """A future unit error (e.g. forgetting the box-core-area *4 conversion,
    or a kg/g mixup) would push this far outside 11-27 kg/m2 and fail loudly
    -- this is [01]'s OWN published mass, independent of [05] or any
    normalizer math."""
    f01 = _load_01_per_event()
    for event, values in f01.items():
        abundance = values["mass_kg"] * 4
        assert 11 <= abundance <= 27, f"{event}: {abundance:.2f} kg/m2 outside the published CCZ band"


# --- E: key-format guard -----------------------------------------------------


def test_01_and_05_key_fields_match_exactly_for_the_same_event() -> None:
    """The dedup key (event_id, cruise, date, coordinates) must actually
    match across [01] and [05] for D1's merge to fire at all -- this holds
    today (exact string/float equality, not approximate). The test exists
    so a future re-download or a new source family that breaks this (e.g.
    different date precision, different coordinate rounding) fails loudly
    here instead of silently making D1's merge stop firing for real data."""
    f01 = build_boxcore_adapter()
    f05 = build_nodule_aggregate_adapter()
    boxcore_by_event = {
        r["event_id"]: r for r in f01.adapt(f01.fetch()) if r["evidence_class"] == "MASS"
    }
    nodules_by_event = {
        r["event_id"]: r for r in f05.adapt(f05.fetch()) if r["evidence_class"] == "MASS"
    }

    shared_events = set(boxcore_by_event) & set(nodules_by_event)
    assert len(shared_events) == 36  # every event appears in both sources

    for event in shared_events:
        r01 = boxcore_by_event[event]
        r05 = nodules_by_event[event]
        assert r01["event_id"] == r05["event_id"]
        assert r01["cruise"] == r05["cruise"]
        assert r01["sample_datetime_utc"] == r05["sample_datetime_utc"]  # identical date precision
        assert r01["latitude"] == r05["latitude"]  # identical coordinate rounding
        assert r01["longitude"] == r05["longitude"]
