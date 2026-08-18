"""Empirical variogram + fitter — the E2.2 support report and, after
Karl's three decisions (2026-08-14), the fit itself.

The decisions the fitter encodes (E2.2 §1-STOP, answered):
  1. min_pairs = 30 — bins below it are RECORDED EXCLUSIONS with reasons,
     never silently zero-weighted;
  2. the fit sees 0–13 km only; the 986–997 km bin is reported beside the
     fit as the far-field contrast, never fed to it;
  3. exponential is the fitted family (known_answer.py plants it, so the
     recovery test has something to recover), spherical the reported
     alternative; the nugget is FITTED, bounded [0, sill].

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
    # The MEAN pair lag inside the bin — the fit abscissa (E2.2 review: the
    # real 0–2 km bin's 102 pairs sit at mean lag 0.727 km, not the 1.0 km
    # midpoint; fitting at midpoints biased the headline nugget ~12%).
    # None for an empty bin; hand-built bins may omit it (midpoint fallback).
    mean_lag_km: float | None = None


@dataclass(frozen=True)
class EmpiricalVariogram:
    bins: tuple[VariogramBin, ...]
    total_pairs: int
    # Pairs whose distance fell OUTSIDE [edges[0], edges[-1]) — counted, not
    # lost (E2.2 review: the real corpus's farthest pair sits 1.003 km under
    # the last default edge; the next between-cluster delivery would have
    # silently vanished from every bin while total_pairs still counted it).
    pairs_beyond_edges: int = 0

    def unsupported(self) -> tuple[VariogramBin, ...]:
        """The bins with ZERO pairs — the lags where any fitted curve is an
        assumption, not an estimate. Named so a report cannot omit them."""
        return tuple(b for b in self.bins if b.pair_count == 0)

    def reconciles(self) -> bool:
        """sum(bin counts) + pairs_beyond_edges == total_pairs — the pair
        accounting closes, or a pair fell somewhere no row records."""
        return sum(b.pair_count for b in self.bins) + self.pairs_beyond_edges == self.total_pairs


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


def bin_pairs(
    pair_distances: np.ndarray,
    half_sq_diff: np.ndarray,
    bin_edges: tuple[float, ...] | np.ndarray,
) -> EmpiricalVariogram:
    """The ONE binning implementation, shared by the geographic report path
    and the estimator's planar fixture path (E2.2 review: the planar path
    had silently duplicated this loop inside kriging.fit — skipping the
    edge validation, so decreasing edges were misreported as a data-support
    failure, and leaving its ½ factor covered by no test). Records the mean
    pair lag per bin and counts pairs beyond the edges instead of losing
    them; empty bins are REPORTED (count 0, semivariance None), never
    dropped — the zero-pair bins are the finding."""
    edges = np.asarray(bin_edges, dtype=np.float64)
    if edges.ndim != 1 or edges.size < 2 or not np.all(np.diff(edges) > 0):
        raise ValueError(
            f"bin_edges_km must be at least two strictly increasing edges, got {bin_edges!r}"
        )
    distances = np.asarray(pair_distances, dtype=np.float64)
    half_sq = np.asarray(half_sq_diff, dtype=np.float64)
    if distances.shape != half_sq.shape or distances.ndim != 1:
        raise ValueError(
            f"pair_distances {distances.shape} and half_sq_diff {half_sq.shape} must be "
            "matching 1-D arrays"
        )
    bins: list[VariogramBin] = []
    for b in range(edges.size - 1):
        in_bin = (distances >= edges[b]) & (distances < edges[b + 1])
        count = int(in_bin.sum())
        bins.append(
            VariogramBin(
                lag_lo_km=float(edges[b]),
                lag_hi_km=float(edges[b + 1]),
                pair_count=count,
                semivariance=float(half_sq[in_bin].mean()) if count else None,
                mean_lag_km=float(distances[in_bin].mean()) if count else None,
            )
        )
    beyond = int(((distances >= edges[-1]) | (distances < edges[0])).sum())
    return EmpiricalVariogram(
        bins=tuple(bins), total_pairs=int(distances.size), pairs_beyond_edges=beyond
    )


def empirical_variogram(
    coords_lonlat: np.ndarray,
    values: np.ndarray,
    bin_edges_km: tuple[float, ...] | np.ndarray = DEFAULT_BIN_EDGES_KM,
) -> EmpiricalVariogram:
    """The support report over GEOGRAPHIC coordinates: great-circle pair
    distances, then `bin_pairs`. Refuses a non-finite y — a NaN target
    would otherwise yield NaN semivariance rows without a named refusal."""
    coords = np.asarray(coords_lonlat, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if y.ndim != 1 or coords.shape[0] != y.shape[0]:
        raise ValueError(
            f"values must be (n,) matching coords (n, 2); got {y.shape} vs {coords.shape}"
        )
    if not np.isfinite(y).all():
        raise ValueError("values contain NaN/inf — refusing to compute semivariances over them")
    distances = pairwise_distances_km(coords)
    i, j = np.triu_indices(coords.shape[0], k=1)
    return bin_pairs(distances, 0.5 * (y[i] - y[j]) ** 2, bin_edges_km)


# --------------------------------------------------------------- the fitter


@dataclass(frozen=True)
class VariogramModel:
    """A fitted isotropic variogram. gamma(0) is EXACTLY 0 (the kriging
    convention that makes ordinary kriging an exact interpolator even with
    a nonzero nugget); gamma(h→0+) jumps to the nugget.

    The no-structure verdict, stated (E2.2 §2): a fit that finds no
    spatial structure reports partial_sill == 0.0 AND range_km == 0.0 —
    explicit zeros, not a flag — and gamma(h>0) is then the flat nugget.
    A fitter that always finds structure is broken in the direction that
    flatters; zeros are the honest output for a pure-nugget field."""

    family: str  # "exponential" | "spherical"
    nugget: float
    partial_sill: float
    range_km: float

    def __post_init__(self) -> None:
        # Validity is what makes the OK variance non-negative in exact
        # arithmetic (E2.2 review: a hand-built nugget=-0.6 model produced a
        # genuinely negative variance that the sd clamp rendered as sd=0 —
        # false certainty). Refuse the invalid model at construction so the
        # clamp downstream only ever absorbs float noise.
        if self.family not in ("exponential", "spherical"):
            raise ValueError(f"unknown variogram family {self.family!r}")
        if not (np.isfinite(self.nugget) and np.isfinite(self.partial_sill) and np.isfinite(self.range_km)):
            raise ValueError("variogram parameters must be finite")
        if self.nugget < 0.0 or self.partial_sill < 0.0 or self.range_km < 0.0:
            raise ValueError(
                f"variogram parameters must be non-negative (nugget={self.nugget}, "
                f"partial_sill={self.partial_sill}, range_km={self.range_km})"
            )

    @property
    def sill(self) -> float:
        return self.nugget + self.partial_sill

    def gamma(self, h: np.ndarray) -> np.ndarray:
        h = np.asarray(h, dtype=np.float64)
        if self.partial_sill == 0.0 or self.range_km <= 0.0:
            structure = np.ones_like(h)
        elif self.family == "exponential":
            # gamma(h) = nugget + ps*(1 - exp(-3h/a)), a = EFFECTIVE range
            # (~95% of the sill at h = a) — the known_answer.py convention.
            structure = 1.0 - np.exp(-3.0 * h / self.range_km)
        elif self.family == "spherical":
            ratio = np.clip(h / self.range_km, 0.0, 1.0)
            structure = 1.5 * ratio - 0.5 * ratio**3
        else:  # exhaustive dispatch, explicit raise (house convention)
            raise ValueError(f"unknown variogram family {self.family!r}")
        return np.where(h > 0.0, self.nugget + self.partial_sill * structure, 0.0)


@dataclass(frozen=True)
class FittedVariogram:
    """The fit plus everything a consumer needs to judge it: which bins the
    fit SAW, which were excluded and WHY (per bin, named — Karl's decisions
    1 and 2 made auditable), and the unsupported lag range every prediction
    between the clusters extrapolates across."""

    model: VariogramModel
    fitted_bins: tuple[VariogramBin, ...]
    excluded_bins: tuple[tuple[VariogramBin, str], ...]
    unsupported_km: tuple[tuple[float, float], ...]  # zero-pair bin ranges
    weighted_sse: float
    # True when the best range sat at the candidate grid's upper end
    # (2×max fitted lag): the data did not constrain it — the fit "found"
    # the largest range it was allowed to consider, which a consumer must
    # read as unconstrained FROM ABOVE, not as an estimate (real-corpus
    # verdict: the 10–13 km bin is still rising at the edge of support).
    range_at_candidate_ceiling: bool = False
    # The symmetric FLOOR failure (E2.2 review): a range at or below the
    # first supported lag saturates the structure term at every fitted
    # bin, so nugget and partial sill are UNIDENTIFIABLE — the reported
    # split between them is arbitrary and must not be read as a finding.
    range_below_first_supported_lag: bool = False
    # len(fitted_bins) − 3 parameters (E2.2 review): 0 means the curve
    # threads the bins with nothing left to check — an unfalsifiable near-
    # interpolation whose small SSE reads as support.
    residual_dof: int = 0
    # Carried from the empirical table so a provenance consumer sees pairs
    # that fell outside every bin (0 on today's corpus).
    pairs_beyond_edges: int = 0


def fit_variogram(
    empirical: EmpiricalVariogram,
    *,
    family: str,
    min_pairs: int = 30,
    max_fit_lag_km: float | None = 13.0,
    n_range_candidates: int = 200,
) -> FittedVariogram:
    """Weighted least squares over each bin's MEAN PAIR LAG (midpoint
    fallback for hand-built bins without one), weights = PAIR COUNTS —
    both load-bearing and each guarded by a test: the E2.2 review showed
    the whole suite green under an equal-weights mutation (a 19% shift in
    the real nugget) and a ~12% nugget bias from midpoint abscissas.
    DETERMINISTIC by construction: for each candidate range on a fixed
    log-spaced grid the (nugget, partial_sill) pair is solved in closed
    form (linear once the range is fixed) with non-negativity by clamped
    re-solve — proven the exact constrained optimum for this 2-variable
    problem (review lens (c), 200k randomized trials vs an exact QP);
    the best candidate by weighted SSE wins, first-wins tie-break. No
    iterative optimizer, no seeds.

    Defaults are Karl's E2.2 decisions (min_pairs 30; fit lags within
    13 km — a bin that STRADDLES the boundary is excluded, so a re-binning
    cannot silently dilute decision 2); both are parameters so the
    known-answer tests can exercise the fitter on planar fixture geometry.
    """
    if family not in ("exponential", "spherical"):
        raise ValueError(
            f"unknown variogram family {family!r} — the E2.2 decision set is "
            "exponential (fitted) + spherical (reported alternative); Gaussian was "
            "declined and Matérn deferred, see docs/walkthroughs/E2.2.md"
        )
    fitted: list[VariogramBin] = []
    excluded: list[tuple[VariogramBin, str]] = []
    for b in empirical.bins:
        if b.pair_count == 0:
            excluded.append((b, "zero pairs — unsupported lag range"))
        elif b.pair_count < min_pairs:
            excluded.append((b, f"pairs {b.pair_count} < minimum {min_pairs} (decision 1)"))
        elif max_fit_lag_km is not None and b.lag_hi_km > max_fit_lag_km:
            excluded.append(
                (b, f"extends beyond max fit lag {max_fit_lag_km} km (decision 2)")
            )
        else:
            fitted.append(b)
    if len(fitted) < 3:
        raise ValueError(
            f"only {len(fitted)} bin(s) survive the exclusions — cannot fit "
            "nugget + partial sill + range from fewer than 3 supported bins; "
            f"exclusions: {[(f'{b.lag_lo_km}-{b.lag_hi_km} km', reason) for b, reason in excluded]}"
        )

    lags = np.array(
        [
            b.mean_lag_km if b.mean_lag_km is not None else (b.lag_lo_km + b.lag_hi_km) / 2.0
            for b in fitted
        ]
    )
    gammas = np.array([b.semivariance for b in fitted], dtype=np.float64)
    if not np.isfinite(gammas).all():
        raise ValueError(
            "a fitted bin carries a non-finite semivariance — refusing to fit over NaN "
            "(a NaN target upstream should have been refused there)"
        )
    weights = np.array([b.pair_count for b in fitted], dtype=np.float64)

    def _solve_linear(structure: np.ndarray) -> tuple[float, float, float]:
        """Weighted LS for gamma ~= nugget + ps*structure with both >= 0:
        unconstrained closed form first, then clamped re-solves."""
        w = weights
        design = np.column_stack([np.ones_like(structure), structure])
        wd = design * w[:, None]
        try:
            coef = np.linalg.solve(design.T @ wd, wd.T @ gammas)
        except np.linalg.LinAlgError:
            coef = np.array([np.average(gammas, weights=w), 0.0])
        nugget, ps = float(coef[0]), float(coef[1])
        if nugget < 0.0:
            nugget = 0.0
            denom = float(np.sum(w * structure**2))
            ps = float(np.sum(w * structure * gammas) / denom) if denom > 0 else 0.0
            ps = max(ps, 0.0)
        if ps < 0.0:
            ps = 0.0
            nugget = float(np.average(gammas, weights=w))
        sse = float(np.sum(w * (gammas - (nugget + ps * structure)) ** 2))
        return nugget, ps, sse

    h_max = float(lags.max())
    candidates = np.geomspace(0.05 * h_max, 2.0 * h_max, n_range_candidates)
    best: tuple[float, float, float, float] | None = None  # (sse, nugget, ps, range)
    for a in candidates:
        if family == "exponential":
            structure = 1.0 - np.exp(-3.0 * lags / a)
        else:
            ratio = np.clip(lags / a, 0.0, 1.0)
            structure = 1.5 * ratio - 0.5 * ratio**3
        nugget, ps, sse = _solve_linear(structure)
        if best is None or sse < best[0] - 1e-12:  # strict improvement: first wins ties
            best = (sse, nugget, ps, float(a))
    assert best is not None
    sse, nugget, ps, range_km = best
    at_ceiling = ps > 0.0 and range_km == float(candidates[-1])
    first_supported_lag = float(min(b.lag_hi_km for b in fitted))
    below_floor = ps > 0.0 and range_km <= first_supported_lag
    if ps == 0.0:
        range_km = 0.0  # the explicit no-structure verdict (see VariogramModel)

    model = VariogramModel(family=family, nugget=nugget, partial_sill=ps, range_km=range_km)
    unsupported = tuple(
        (b.lag_lo_km, b.lag_hi_km) for b in empirical.bins if b.pair_count == 0
    )
    return FittedVariogram(
        model=model,
        fitted_bins=tuple(fitted),
        excluded_bins=tuple(excluded),
        unsupported_km=unsupported,
        weighted_sse=sse,
        range_at_candidate_ceiling=at_ceiling,
        range_below_first_supported_lag=below_floor,
        residual_dof=len(fitted) - 3,
        pairs_beyond_edges=empirical.pairs_beyond_edges,
    )
