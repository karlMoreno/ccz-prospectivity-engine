"""Metres -> cells window resolution (Contract 3 v3, E1.4 Preflight 2).

Contract 3 declares neighborhoods as PHYSICAL DISTANCES; this module is the
single runtime conversion to cell counts, from the DEM's actual N-S cell size
(DemGrid.cell_size_ns_m). Keeping it in one tested function pair is what makes
the same recipe_version measure the same physical neighborhood on the
0.1-degree synthetic DEM and on 15-arc-sec GEBCO — the 24x defect the v3
contract change exists to fix.

Rules (mirrored in the contract's v3 comment):
- square windows: nearest odd cell count to window_m / cell_size_m, ties
  round UP, minimum 3 (a 1x1 "window" measures nothing);
- radii: round half up, minimum 1;
- a request the DEM is too coarse to honour CLAMPS to the minimum and records
  `clamped=True`. On the coarse synthetic DEM this is expected and by design
  (approved 2026-07-28); provenance shows it rather than hiding it.

Both the requested metres and the resolved cells are kept on the
ResolvedWindow so provenance can show what was actually computed, not just
what was asked for.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedWindow:
    """One metres->cells resolution, carrying request AND outcome."""

    requested_m: float
    cell_size_m: float
    cells: int  # odd window edge (square) or radius (annulus), in cells
    clamped: bool

    @property
    def effective_m(self) -> float:
        """The physical size actually computed: cells * cell_size_m."""
        return self.cells * self.cell_size_m

    def provenance(self) -> dict:
        return {
            "requested_m": self.requested_m,
            "cell_size_m": self.cell_size_m,
            "cells": self.cells,
            "clamped": self.clamped,
            "effective_m": self.effective_m,
        }


def resolve_square_window(window_m: float, cell_size_m: float, minimum_cells: int = 3) -> ResolvedWindow:
    """Full window span in metres -> nearest ODD cell count (ties up, min 3)."""
    if window_m <= 0 or cell_size_m <= 0:
        raise ValueError(f"window_m and cell_size_m must be positive (got {window_m}, {cell_size_m})")
    raw = window_m / cell_size_m
    # Nearest odd integer to `raw`, ties rounding up: odd candidates are
    # 2k+1, and k = floor((raw-1)/2 + 0.5) picks the k whose 2k+1 is closest.
    cells = 2 * math.floor((raw - 1.0) / 2.0 + 0.5) + 1
    clamped = cells < minimum_cells
    if clamped:
        cells = minimum_cells
    return ResolvedWindow(requested_m=window_m, cell_size_m=cell_size_m, cells=cells, clamped=clamped)


def resolve_radius(radius_m: float, cell_size_m: float, minimum_cells: int = 1) -> ResolvedWindow:
    """Radius in metres -> cell count, round half up, minimum 1."""
    if radius_m <= 0 or cell_size_m <= 0:
        raise ValueError(f"radius_m and cell_size_m must be positive (got {radius_m}, {cell_size_m})")
    cells = math.floor(radius_m / cell_size_m + 0.5)
    clamped = cells < minimum_cells
    if clamped:
        cells = minimum_cells
    return ResolvedWindow(requested_m=radius_m, cell_size_m=cell_size_m, cells=cells, clamped=clamped)
