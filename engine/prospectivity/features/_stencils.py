"""Shared neighborhood/stencil arithmetic for the covariate recipes.

Everything here is pure, vectorized numpy on a DemGrid — deterministic by
construction (fixed operations, fixed order, no randomness), which is what
lets the recipes promise byte-identical output for identical input.

BORDER POLICY (one policy, all recipes — E1.4): `_neighbor` returns NaN where
an offset falls off the raster, and NaN propagates through every sum/mean/
std. So any cell whose FULL neighborhood is not on the raster comes out NaN —
no edge padding, no shrunken windows, no fabricated values at the rim. The
policy's name and description live in recipe.py (BORDER_POLICY) and are
recorded in every layer's provenance.

Axis conventions (all formulas below assume them):
- row index increases SOUTH; column index increases EAST;
- p = dz/dx is positive when elevation increases eastward;
- q = dz/dy is positive when elevation increases northward.
"""

from __future__ import annotations

import numpy as np

from engine.prospectivity.features.dem_grid import DemGrid


def _neighbor(values: np.ndarray, di: int, dj: int) -> np.ndarray:
    """out[r, c] = values[r + di, c + dj], NaN where that falls off the edge."""
    height, width = values.shape
    out = np.full((height, width), np.nan, dtype=np.float64)
    row_start, row_stop = max(0, -di), min(height, height - di)
    col_start, col_stop = max(0, -dj), min(width, width - dj)
    if row_start < row_stop and col_start < col_stop:
        out[row_start:row_stop, col_start:col_stop] = values[
            row_start + di : row_stop + di, col_start + dj : col_stop + dj
        ]
    return out


def _dx_column(grid: DemGrid) -> np.ndarray:
    """Per-row E-W cell size as a column vector, broadcastable over the grid
    (CRS strategy A: dx varies with the row's latitude)."""
    return grid.dx_m_per_row[:, np.newaxis]


def horn_gradients(grid: DemGrid) -> tuple[np.ndarray, np.ndarray]:
    """Horn (1981) 3x3 third-order finite differences -> (p, q) in m/m."""
    z = grid.values
    nw, n, ne = _neighbor(z, -1, -1), _neighbor(z, -1, 0), _neighbor(z, -1, 1)
    w, e = _neighbor(z, 0, -1), _neighbor(z, 0, 1)
    sw, s, se = _neighbor(z, 1, -1), _neighbor(z, 1, 0), _neighbor(z, 1, 1)
    p = ((ne + 2.0 * e + se) - (nw + 2.0 * w + sw)) / (8.0 * _dx_column(grid))
    q = ((nw + 2.0 * n + ne) - (sw + 2.0 * s + se)) / (8.0 * grid.dy_m)
    return p, q


def zevenbergen_thorne_derivatives(
    grid: DemGrid,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Zevenbergen & Thorne (1987) 3x3 central differences.

    Returns (p, q, r, s, t): first derivatives p=dz/dx, q=dz/dy and second
    derivatives r=d2z/dx2, s=d2z/dxdy, t=d2z/dy2, all in metre units, with
    dx per-row (strategy A) and dy constant.
    """
    z = grid.values
    nw, n, ne = _neighbor(z, -1, -1), _neighbor(z, -1, 0), _neighbor(z, -1, 1)
    w, e = _neighbor(z, 0, -1), _neighbor(z, 0, 1)
    sw, s_, se = _neighbor(z, 1, -1), _neighbor(z, 1, 0), _neighbor(z, 1, 1)
    dx = _dx_column(grid)
    dy = grid.dy_m
    p = (e - w) / (2.0 * dx)
    q = (n - s_) / (2.0 * dy)
    r = (w - 2.0 * z + e) / (dx**2)
    t = (n - 2.0 * z + s_) / (dy**2)
    s = (ne - nw - se + sw) / (4.0 * dx * dy)
    return p, q, r, s, t


def square_offsets(window_cells: int) -> list[tuple[int, int]]:
    """All (di, dj) offsets of a centered odd window, centre INCLUDED
    (Contract 3: TPI is "cell minus mean(window)", window inclusive)."""
    half = window_cells // 2
    return [(di, dj) for di in range(-half, half + 1) for dj in range(-half, half + 1)]


def annulus_offsets(inner_radius_cells: int, outer_radius_cells: int) -> list[tuple[int, int]]:
    """(di, dj) offsets whose Euclidean CELL distance d satisfies
    inner <= d <= outer. Distances are in cell units (the ~<=3% E-W/N-S
    anisotropy in metres is recorded in provenance, not corrected here)."""
    offsets = []
    for di in range(-outer_radius_cells, outer_radius_cells + 1):
        for dj in range(-outer_radius_cells, outer_radius_cells + 1):
            distance = math_hypot(di, dj)
            if inner_radius_cells <= distance <= outer_radius_cells:
                offsets.append((di, dj))
    return offsets


def math_hypot(di: int, dj: int) -> float:
    return float(np.hypot(di, dj))


def stacked_neighbors(values: np.ndarray, offsets: list[tuple[int, int]]) -> np.ndarray:
    """(len(offsets), H, W) stack of shifted views; NaN off-edge, so any
    statistic over axis 0 inherits the border policy automatically."""
    return np.stack([_neighbor(values, di, dj) for di, dj in offsets], axis=0)
