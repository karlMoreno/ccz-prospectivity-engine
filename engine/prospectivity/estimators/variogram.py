"""Empirical variogram of geographic point data — the E2.2 support report.

REPORT, NOT FIT: this module computes what the data can say (per-lag-bin
pair counts and semivariances, with empty bins named) and deliberately
contains NO fitting code. The fitter arrives in E2.2 Section 2, after
Karl's three decisions (minimum pairs per bin; which lags the fit may see;
model family) — decisions whose INPUT is this report.

Why `tests.fixtures.known_answer.empirical_semivariance` is not reused
(its shape does not fit): it computes PLANAR Euclidean distances, which is
correct for the fixture's arbitrary planar units but wrong for the corpus
— real coordinates are geographic, a degree is not a kilometre, and an
E-W degree at the study latitudes is ~3% shorter than a N-S one
(cos 12–14°). Distances here are great-circle km via the same
`haversine_km` the corpus manifest's spatial summary uses, so this
report's bins and the manifest's pairwise-distance structure are the same
geometry by construction.

    coords (n, 2) lon/lat + values (n,)      [TrainingMatrix.coord order]
        │  haversine_km over all n(n−1)/2 pairs
        ▼
    empirical_variogram(coords, values, bin_edges_km)
        ▼
    EmpiricalVariogram
      .bins: (lag_lo_km, lag_hi_km, pair_count, semivariance | None)
      .total_pairs                       semivariance = mean ½(yᵢ−yⱼ)²
      .unsupported() -> zero-pair bins   None = honest absence, never 0.0

The default bin edges encode the corpus's known support structure
(manifest: 595 training pairs, ALL either < ~12.1 km or in ~986–996 km):
fine 2–3 km bins where the within-cluster structure at 0–13 km is the only
place fine bins have support, ONE wide named bin over the unsupported
13–986 km void, and one bin isolating the between-cluster contrast.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from engine.prospectivity.provenance.geometry import haversine_km

# See module docstring for the rationale; the walkthrough shows the counts
# these edges produce on the real corpus.
DEFAULT_BIN_EDGES_KM = (0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 13.0, 986.0, 997.0)


@dataclass(frozen=True)
class VariogramBin:
    lag_lo_km: float
    lag_hi_km: float
    pair_count: int
    semivariance: float | None  # None for an empty bin — absence, not zero


@dataclass(frozen=True)
class EmpiricalVariogram:
    bins: tuple[VariogramBin, ...]
    total_pairs: int

    def unsupported(self) -> tuple[VariogramBin, ...]:
        """The bins with ZERO pairs — the lags where any fitted curve is an
        assumption, not an estimate. Named so a report cannot omit them."""
        return tuple(b for b in self.bins if b.pair_count == 0)


def pairwise_distances_km(coords_lonlat: np.ndarray) -> np.ndarray:
    """Great-circle km for every unordered pair, in (i, j) upper-triangle
    order. Column order is (longitude, latitude) — the TrainingMatrix
    convention — while haversine_km takes (lat, lon): the swap happens
    exactly here, once."""
    coords = np.asarray(coords_lonlat, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError(f"coords must be (n, 2) lon/lat, got {coords.shape}")
    i, j = np.triu_indices(coords.shape[0], k=1)
    return np.array(
        [
            haversine_km(coords[a, 1], coords[a, 0], coords[b, 1], coords[b, 0])
            for a, b in zip(i, j)
        ]
    )


def empirical_variogram(
    coords_lonlat: np.ndarray,
    values: np.ndarray,
    bin_edges_km: tuple[float, ...] | np.ndarray = DEFAULT_BIN_EDGES_KM,
) -> EmpiricalVariogram:
    """The support report: per lag bin [lo, hi), the pair count and the
    mean semivariance ½(yᵢ−yⱼ)². Empty bins are REPORTED (count 0,
    semivariance None), never dropped — the zero-pair bins are the finding."""
    coords = np.asarray(coords_lonlat, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if y.ndim != 1 or coords.shape[0] != y.shape[0]:
        raise ValueError(
            f"values must be (n,) matching coords (n, 2); got {y.shape} vs {coords.shape}"
        )
    edges = np.asarray(bin_edges_km, dtype=np.float64)
    if edges.ndim != 1 or edges.size < 2 or not np.all(np.diff(edges) > 0):
        raise ValueError(
            f"bin_edges_km must be at least two strictly increasing edges, got {bin_edges_km!r}"
        )

    distances = pairwise_distances_km(coords)
    i, j = np.triu_indices(coords.shape[0], k=1)
    half_sq_diff = 0.5 * (y[i] - y[j]) ** 2

    bins: list[VariogramBin] = []
    for b in range(edges.size - 1):
        in_bin = (distances >= edges[b]) & (distances < edges[b + 1])
        count = int(in_bin.sum())
        bins.append(
            VariogramBin(
                lag_lo_km=float(edges[b]),
                lag_hi_km=float(edges[b + 1]),
                pair_count=count,
                semivariance=float(half_sq_diff[in_bin].mean()) if count else None,
            )
        )
    return EmpiricalVariogram(bins=tuple(bins), total_pairs=int(distances.size))
