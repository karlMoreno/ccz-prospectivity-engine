"""Known-answer fixture generators for the estimators (E2.1 §3; closes the
BACKLOG §3 item recorded at E2.0-1).

data_origin: SYNTHETIC — deterministic seeded generators, import path below.
Seeds are ARGUMENTS, not module constants: E2.2 needs a planted variogram
range to recover and E2.4 needs a known correlation length, at parameters
of their choosing, without forking the generator. DATA_SEEDS therefore
documents the convention (every generator takes an explicit `seed`); the
per-use seed is visible at each call site.

THE PROBLEM THIS ADDRESSES: the corpus carries real abundance while every
covariate is synthetic noise, so the expected and honest Phase-2 result is
that no model beats the mean baseline — but that result is
indistinguishable from a broken estimator. The real corpus proves the
pipeline runs; it cannot prove the arithmetic is right. These generators
plant answers the estimator tests recover.

THE PROHIBITION, WHICH IS THE PART THAT MUST SURVIVE: do NOT make the
synthetic DEM correlate with the real abundance values. That would produce
a corpus where y genuinely depends on X, and every subsequent model result
becomes uninterpretable — did the model work, or did it find a relationship
we planted? Under the taxonomy that corpus is AUTHORED wearing real data's
shape. This fixture stays STRICTLY SEPARATE from the corpus: it lives in
tests/fixtures/ (refused from production paths by the P1/P2.0d-2 location
rule), it is never a corpus, and it is never an input to a claim.

DEFERRED CONSUMERS, so E2.2–E2.4 know what is waiting here:
  E2.2 (kriging)  — exactness at data locations; recovery of a planted
                    variogram range and sill on `grid_layout` (a
                    well-supported layout — the real two-cluster geometry
                    is precisely what makes real data unable to test the
                    fitter); the pure-nugget degenerate case (near-zero
                    range fitted, reversion to the mean).
  E2.3 (RF)       — `covariate_driven_field`: importance must rank the one
                    driving column first, at n=35 AND n=500 — if the
                    planted signal is only recoverable at n=500, that is a
                    quantitative statement about what our dataset supports.
  E2.4 (CV)       — a `gaussian_process_field` with known range, then
                    random k-fold vs leave-one-cluster-out on the same
                    data: the leakage measured as a number in our own
                    suite, not asserted as methodology.
"""

from __future__ import annotations

import numpy as np

from engine.prospectivity.provenance.origin import DataOrigin

DATA_ORIGIN = DataOrigin.SYNTHETIC
DATA_GENERATOR = "tests.fixtures.known_answer"
DATA_SEEDS = "argument-per-call: every generator takes an explicit `seed`; see call sites"


def grid_layout(
    n_side: int, *, spacing: float = 1.0, origin: tuple[float, float] = (0.0, 0.0)
) -> np.ndarray:
    """A regular (n_side × n_side, 2) planar point grid — the WELL-SUPPORTED
    layout: pairs exist at every lag from `spacing` up to the diagonal, so
    an empirical variogram is estimable across its whole domain. Planar
    arbitrary units, deliberately not geographic: this fixture tests
    arithmetic, not geodesy. Deterministic without a seed (no randomness)."""
    if n_side < 2:
        raise ValueError(f"n_side must be >= 2, got {n_side}")
    axis = origin[0] + spacing * np.arange(n_side, dtype=np.float64)
    xs, ys = np.meshgrid(axis, origin[1] + spacing * np.arange(n_side, dtype=np.float64))
    return np.column_stack([xs.ravel(), ys.ravel()])


def gaussian_process_field(
    coords: np.ndarray,
    *,
    variogram_range: float,
    sill: float,
    nugget: float,
    seed: int,
    mean: float = 0.0,
) -> np.ndarray:
    """y at `coords` drawn from a Gaussian process with an EXPONENTIAL
    covariance model — stated, since the recovery tests must know what was
    planted:

        semivariance  γ(h) = nugget + (sill − nugget)·(1 − exp(−3h/a))
        covariance    C(h) = (sill − nugget)·exp(−3h/a),  C(0) = sill

    with `a = variogram_range` the EFFECTIVE range (γ reaches ~95% of the
    sill at h = a; the 3 is that convention). `nugget` is spatially
    uncorrelated variance added on the diagonal. Sampling: Cholesky of the
    covariance matrix (tiny jitter for conditioning) times seeded standard
    normals — same coords, params, and seed → the identical field, always.

    The pure-nugget degenerate case E2.2 needs: nugget == sill gives zero
    spatial structure (C(h>0) = 0) — a correct fitter should find a
    near-zero range and revert to the mean."""
    coords = np.asarray(coords, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError(f"coords must be (n, 2), got {coords.shape}")
    if not (sill > 0 and 0 <= nugget <= sill and variogram_range > 0):
        raise ValueError(
            f"need sill > 0, 0 <= nugget <= sill, range > 0 "
            f"(got sill={sill}, nugget={nugget}, range={variogram_range})"
        )
    n = coords.shape[0]
    distances = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=2))
    covariance = (sill - nugget) * np.exp(-3.0 * distances / variogram_range)
    covariance += (nugget + 1e-10 * sill) * np.eye(n)
    rng = np.random.default_rng(seed)
    return mean + np.linalg.cholesky(covariance) @ rng.standard_normal(n)


def covariate_driven_field(
    n: int,
    k: int,
    *,
    driving_column: int,
    coefficient: float,
    noise_sd: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """(X, y) where X is (n, k) standard-normal noise and
    y = coefficient · X[:, driving_column] + ε, ε ~ N(0, noise_sd²) — one
    named column genuinely drives y, the other k−1 are pure noise. The
    signal-to-noise ratio is stated by the caller (|coefficient| vs
    noise_sd). E2.3's importance test must rank `driving_column` first —
    at n=35 and at n=500."""
    if not 0 <= driving_column < k:
        raise ValueError(f"driving_column {driving_column} outside 0..{k - 1}")
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, k))
    y = coefficient * X[:, driving_column] + noise_sd * rng.standard_normal(n)
    return X, y


def empirical_semivariance(
    coords: np.ndarray, values: np.ndarray, *, lag_edges: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Binned empirical semivariance: for each lag bin, mean of
    ½(yᵢ − yⱼ)² over point pairs whose separation falls in the bin, plus
    the pair counts (so a consumer can see which bins are supported).
    Deliberately NOT a variogram FITTER — building and testing the fitter
    against this fixture is E2.2's job; this is the measuring stick."""
    coords = np.asarray(coords, dtype=np.float64)
    values = np.asarray(values, dtype=np.float64)
    i, j = np.triu_indices(coords.shape[0], k=1)
    distances = np.sqrt(((coords[i] - coords[j]) ** 2).sum(axis=1))
    half_sq_diff = 0.5 * (values[i] - values[j]) ** 2
    semivariances = np.full(len(lag_edges) - 1, np.nan)
    counts = np.zeros(len(lag_edges) - 1, dtype=int)
    for b in range(len(lag_edges) - 1):
        in_bin = (distances >= lag_edges[b]) & (distances < lag_edges[b + 1])
        counts[b] = int(in_bin.sum())
        if counts[b]:
            semivariances[b] = float(half_sq_diff[in_bin].mean())
    return semivariances, counts
