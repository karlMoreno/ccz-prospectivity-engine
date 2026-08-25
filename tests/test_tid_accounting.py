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
