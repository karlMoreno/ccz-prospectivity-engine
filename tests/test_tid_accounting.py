"""G.3 commit 2 — the TID accounting artifact's guards.

Two layers, by what CI can see: the committed JSON is always checkable
(declaration, internal consistency, cross-record agreement with the ledger
row); regeneration against the real rasters self-activates when the
gitignored files are present (the ledger-test pattern).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "data" / "bathymetry" / "tid_accounting.json"


def _artifact() -> dict:
    return json.loads(ARTIFACT.read_text())


def _ledger_hashes() -> dict:
    queue = yaml.safe_load((REPO_ROOT / "data/sources/source_queue.yaml").read_text())
    (row,) = [s for s in queue["sources"] if s["source_id"] == "src_bathymetry_primary"]
    return row["content_hash"]


def test_the_artifact_declares_derived_with_a_derivation_naming_its_generator() -> None:
    a = _artifact()
    assert a["data_origin"] == "DERIVED"
    assert "tid_accounting.build_tid_accounting" in a["derivation"]


def test_the_artifact_quotes_the_same_raster_hashes_as_the_ledger_row() -> None:
    """Cross-record consistency: the accounting's recorded inputs and the
    ledger row must name the SAME bytes — a re-cut subset whose accounting
    was not regenerated (or vice versa) is visible as a disagreement between
    two committed records, without either raster present."""
    a = _artifact()
    ledger = _ledger_hashes()
    assert a["inputs"]["bathymetry"]["sha256"] == ledger[Path(a["inputs"]["bathymetry"]["path"]).name]
    assert a["inputs"]["tid"]["sha256"] == ledger[Path(a["inputs"]["tid"]["path"]).name]


def test_the_class_boundaries_match_the_documented_tid_table() -> None:
    """The code-class mapping is the documentation's (§3.0 Table 2), not an
    invention: direct 10–17, indirect 40–48, unknown 70–72, land 0. The
    whole-box fractions separate a swapped mapping (0.266 direct vs 0.731
    predicted — a swap cannot survive both)."""
    a = _artifact()
    classes = a["tid_code_table"]["classes"]
    assert classes == {
        "direct": [10, 17],
        "indirect_predicted": [40, 48],
        "unknown": [70, 72],
        "land": [0],
    }
    frac = a["whole_subset"]["fractions"]
    assert frac["direct"] < 0.5 < frac["predicted"], "the subset box is majority-predicted; a class swap flips this"


def test_the_accountings_are_internally_consistent_counts_and_recomputed_row_stats() -> None:
    """Positive full-consistency checks (convention 7: no vacuous
    collections): class cells sum to the total in both accountings; the
    per-row summary stats are RECOMPUTED here from the shipped array, so a
    hand-edited summary (or a truncated array) disagrees with its own data;
    the every-row flag is re-derived the same way."""
    a = _artifact()
    w = a["whole_subset"]
    assert sum(w["histogram"].values()) == w["cells"] == 72_000_000
    s = a["study_extent"]
    assert s["direct_cells"] + s["predicted_cells"] + s["land_cells"] == s["cells"] == 1_958_400
    rows = np.array(s["per_row_direct_fraction"])
    assert len(rows) == 816
    assert s["per_row_stats"]["min"] == round(float(rows.min()), 4)
    assert s["per_row_stats"]["max"] == round(float(rows.max()), 4)
    assert s["per_row_stats"]["sd"] == round(float(rows.std()), 4)
    assert s["every_row_has_direct"] is bool((rows > 0).all())


def test_the_station_block_uses_the_production_gate_count_and_sums_per_cluster() -> None:
    """35 through the production gate (the planning filter without the qa
    condition gave 36 — the drift the gate exists to prevent), each station
    carried individually, histogram and clusters summing to n, and the
    per-cluster direct/predicted split present for BOTH clusters — the
    confound leave_one_cluster_out would test across."""
    st = _artifact()["stations"]
    assert st["n"] == 35 == len(st["per_station"])
    assert sum(st["tid_histogram"].values()) == 35
    clusters = st["clusters"]
    assert set(clusters) == {"west", "east"}
    assert clusters["west"]["n"] + clusters["east"]["n"] == 35
    for c in clusters.values():
        assert c["direct"] + c["predicted"] == c["n"]
    assert st["direct"] + st["predicted"] == 35


def test_regenerating_from_the_real_rasters_reproduces_the_committed_artifact_exactly() -> None:
    """The full-state comparison (convention 3): rebuild from the actual
    rasters and require dict equality with the committed artifact — not
    selected fields. Skips by name when the gitignored rasters are absent."""
    from engine.prospectivity.terrain import tid_accounting as ta

    missing = [p.name for p in (ta.DEFAULT_BATHY, ta.DEFAULT_TID) if not p.is_file()]
    if missing:
        pytest.skip(f"gitignored GEBCO rasters not present locally: {missing}")
    assert ta.build_tid_accounting() == _artifact()


# ── TID.2: WHAT the predicted cells are ────────────────────────────────────

def test_the_predicted_class_provenance_quotes_the_tracked_pdf_and_both_references() -> None:
    """The provenance of 54.9% of the study extent must trace to the TRACKED
    documentation, not to a paraphrase.

    G.3's correction-drift instance (o) was exactly a paraphrase of a licence
    clause that turned out to omit an obligation, so the sentence is carried
    VERBATIM and pinned here. Both references are asserted by DOI because a
    reference without a locator is what this project's LITERATURE bar refuses."""
    block = _artifact()["predicted_class_provenance"]
    what = block["what_they_are"]
    assert what["grid"] == "GEBCO_2026"
    assert "Version 2.8" in what["base_dataset"]
    assert "SWOT" in what["gravity_mission"] and "machine learning" in what["method"]
    assert "section 2.1" in what["documented_in"]
    # the verbatim sentence, and the two DOIs that make the references locate
    assert "Surface Water and Ocean Topography (SWOT)" in what["quote"]
    assert "machine learning methods" in what["quote"]
    refs = " ".join(what["references"])
    assert "10.1126/science.ads4472" in refs
    assert "10.22541/essoar.176339961.11752151/v1" in refs


def test_the_release_distinction_is_recorded_as_verified_from_both_sections() -> None:
    """The load-bearing claim: GEBCO_2026 is the FIRST release resting on SWOT.

    It is verified by reading the documentation's two PARALLEL release sections
    (2.1 names V2.8 + SWOT; 2.2 names V2.7 and mentions neither), NOT inferred
    from the word "new" in the 2026 sentence — an inference is what would make
    this a premise rather than a check."""
    rd = _artifact()["predicted_class_provenance"]["release_distinction"]
    assert rd["verified"] is True
    assert "2.1" in rd["how"] and "2.2" in rd["how"]
    assert "Version 2.7" in rd["how"] and "NO mention" in rd["how"]


def test_the_gravity_resolution_is_recorded_as_UNCITED_rather_than_asserted() -> None:
    """THE NEGATIVE RESULT, pinned so it cannot drift into fact.

    A ~8 km figure circulates in NASA/JPL press material. The tracked PDF states
    NO resolution for the gravity field, this repo does not hold Yu et al. 2024,
    and this project's LITERATURE bar is a citation that LOCATES the number. So
    the field is null and the status says why. A future edit that fills in 8.0
    without adding the source fails here — which is the point."""
    r = _artifact()["predicted_class_provenance"]["resolution"]
    assert r["gravity_field_km"] is None
    status = r["gravity_field_citation_status"]
    assert "NOT STATED IN THE TRACKED DOCUMENTATION" in status
    assert "UNCITED" in status
    # and the measurement must not secretly depend on the uncited number
    assert "does not depend on that number" in status
    assert r["grid_cell_m"]["north_south"] > 0


def test_the_short_wavelength_deficit_is_measured_and_survives_the_confound() -> None:
    """The finding, asserted as a MEASUREMENT with its confound control.

    Absolute roughness alone cannot separate "prediction smooths" from
    "predicted cells sit on flatter seafloor" — multibeam TARGETS rough terrain.
    Two things must therefore hold together: the gap must NARROW with scale (the
    signature of short-wavelength suppression), and the per-cell short/long
    RATIO — which is scale-free — must still be lower for predicted cells."""
    m = _artifact()["predicted_class_provenance"]["measured_short_wavelength_deficit"]
    short = m["median_local_sd_m"]["short_1400m"]
    long_ = m["median_local_sd_m"]["long_8800m"]
    # direct is rougher at BOTH scales...
    assert short["direct"] > short["predicted"] and long_["direct"] > long_["predicted"]
    # ...but the gap NARROWS as the window grows — suppression, not amplitude
    assert short["ratio_direct_over_predicted"] > long_["ratio_direct_over_predicted"]
    # ...and the scale-free ratio still separates them, which is the confound control
    ratio = m["median_short_over_long_ratio"]
    assert ratio["direct"] > ratio["predicted"]
    assert ratio["predicted"] / ratio["direct"] < 0.8  # ~a third less short-wavelength structure
    # the alternative hypothesis this task was told to watch for is named as refuted
    assert "REFUTED" in m["finding"]


def test_the_effect_scales_with_derivative_order_and_depth_is_the_exception() -> None:
    """WHICH covariates are affected, measured rather than reasoned.

    Each derivative amplifies missing short-wavelength content, so the ordering
    depth < slope < curvature is the claim — and depth being nearly unaffected is
    what makes the other two mean something. A test that only checked "predicted
    differs" would pass on a uniform offset."""
    a = _artifact()["predicted_class_provenance"]["affected_covariates"]
    depth = abs(a["depth_value"]["ratio_direct_over_predicted"] - 1.0)
    slope = a["slope_first_derivative_deg"]["ratio_direct_over_predicted"]
    curv = a["curvature_second_derivative"]["ratio_direct_over_predicted"]
    assert depth < 0.10, "depth is a VALUE — it should agree closely"
    assert slope > 1.5, "slope is a FIRST derivative"
    assert curv > slope, "curvature is a SECOND derivative and must be the most affected"
    assert "depth is the exception" in a["reading"]
