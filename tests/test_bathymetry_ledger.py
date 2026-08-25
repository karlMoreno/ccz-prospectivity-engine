"""G.3 — the GEBCO_2026 ledger row and its hash observation.

THE LEDGER IS THE HASH OBSERVER, NOT THE AUDIT (TRACK-G.md §0.5, probed):
the origin audit validates declarations and has no MEASURED/DERIVED hash
branch, so a clean audit says nothing about bytes. These tests are where the
recorded hashes are checked against the files — self-activating whenever the
rasters are present (the `test_grid_rows_are_never_flagged_observed`
pattern: skip by name while the gitignored files are absent, assert the
moment they exist).
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BATHY_DIR = REPO_ROOT / "data" / "bathymetry"
GEBCO_DOI = "10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa"


def _row() -> dict:
    queue = yaml.safe_load((REPO_ROOT / "data/sources/source_queue.yaml").read_text())
    (row,) = [s for s in queue["sources"] if s["source_id"] == "src_bathymetry_primary"]
    return row


def test_the_bathymetry_row_is_filled_derived_open_with_bbox_doi_and_two_hashes() -> None:
    """The G.3 fill: every previously-null field the acquisition owed the
    ledger is present with the recorded value — origin DERIVED (Karl's G.3
    classification), is_open true, the reproducibility-bearing subset bbox,
    the release DOI in both `doi` and `citation`, an accessed date, a
    licence, and one sha256 per file (two files, distinct hashes — a
    single-hash row could not tell the TID grid from the bathymetry)."""
    row = _row()
    assert row["data_origin"] == "DERIVED"
    assert row["is_open"] is True
    assert row["subset_bbox"] == {"north": 25.0, "south": 0.0, "west": -160.0, "east": -110.0}
    assert row["doi"] == GEBCO_DOI and GEBCO_DOI in row["citation"]
    assert row["accessed_date"] == "2026-08-24"
    assert isinstance(row["license"], str) and row["license"].strip()
    assert isinstance(row["derivation"], str) and "publisher" in row["derivation"].lower()
    hashes = row["content_hash"]
    assert set(hashes) == {
        "gebco_2026_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif",
        "gebco_2026_tid_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif",
    }
    values = list(hashes.values())
    assert all(v.startswith("sha256:") and len(v) == len("sha256:") + 64 for v in values)
    assert values[0] != values[1]


def test_the_recorded_hashes_match_the_bytes_whenever_the_rasters_are_present() -> None:
    """The observation itself: per file, sha256 over the actual bytes equals
    the ledger's recorded value. Skips BY NAME when the (deliberately
    untracked) rasters are absent — a clone without them loses this check,
    not the suite; re-obtaining via the row's doi + subset_bbox and rerunning
    this test IS the fetch-at-build verification step."""
    hashes = _row()["content_hash"]
    missing = [name for name in hashes if not (BATHY_DIR / name).is_file()]
    if missing:
        pytest.skip(f"gitignored GEBCO rasters not present locally: {missing}")
    for name, recorded in hashes.items():
        computed = "sha256:" + hashlib.sha256((BATHY_DIR / name).read_bytes()).hexdigest()
        assert computed == recorded, name


def test_the_citation_backing_pdfs_are_tracked_despite_the_global_pdf_ignore() -> None:
    """The DERIVED classification's evidence quote and the TID code table
    live in the two GEBCO PDFs, shipped via scoped .gitignore exceptions. A
    future gitignore edit that silently drops them would leave the ledger
    row citing documents a cloner does not have — this asserts both are in
    the index (git ls-files), which is also what puts them inside the origin
    audit's walk."""
    tracked = subprocess.run(
        ["git", "ls-files", "--", "data/bathymetry"],
        cwd=REPO_ROOT, capture_output=True, check=True, text=True,
    ).stdout.splitlines()
    assert "data/bathymetry/GEBCO_Grid_terms_of_use.pdf" in tracked
    assert "data/bathymetry/GEBCO_Grid_documentation.pdf" in tracked
