"""E2.3 §3 — the known-answer tests, consuming what E2.1's fixture planted
for this task: `covariate_driven_field` (X noise, y = c·X[:, j] + N(0, σ²),
one named driving column).

THE RF-SPECIFIC DEGENERACY TRAP, named in advance and checked here (rule
4): on a finite noise draw the driving column can CORRELATE WITH A NOISE
COLUMN BY CHANCE, and importance cannot separate "found the planted
signal" from "found a chance correlate of the planted signal". Every
fixture below states and ASSERTS its realized max |corr(driving, noise)|
under its seed, against a threshold chosen from the probe: at n=500 the
six generator seeds realize 0.06–0.11 (threshold 0.15); at n=35 they
realize 0.24–0.47 (gen seed 1 = 0.47 — a chance correlate at nearly half
strength), so the n=35 tests use gen seeds whose max is < 0.32 and
STATE that the trap is live at this n. The separation claim is what the
threshold protects: below it, a top-1 on the driving column cannot be
the correlate. Weakening the threshold is a mutation (KA2) that must fail
the degeneracy guard.

THE TWO REGIMES (measured, E2.3 §3 probe — 6 generator seeds × 3 forest
seeds each): at SNR 2 (c=2, σ=1) BOTH n=500 and n=35 recover the driving
column top-1 18/18 with margins 32× / 16×; at SNR 0.5 (c=0.5, σ=1) n=500
STILL recovers 18/18 with a 3× margin while n=35 finds it at CHANCE
(9/18, margin ~1×). The contrast is a threshold, and that is the finding:
the planted signal is recoverable at n=35 only when it is at least as
strong as the noise; below that, importance claims on 35 examples are
noise. The tests pin the strong regime's recovery at both sizes and the
weak regime's asymmetry — recovery at 500, INSTABILITY (not recovery)
at 35, asserted as such.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.prospectivity.estimators.random_forest import RandomForestEstimator
from tests.fixtures.known_answer import covariate_driven_field

DRIVING = 3
K = 8
NOISE_SD = 1.0
STRONG_COEF, WEAK_COEF = 2.0, 0.5
CORR_THRESHOLD_500 = 0.15
CORR_THRESHOLD_35 = 0.32
GEN_SEEDS_500 = (0, 1, 2)
GEN_SEEDS_35 = (0, 3, 5)  # realized max |corr| 0.289 / 0.250 / 0.244 — below 0.32
FOREST_SEEDS = (0, 1, 2)


def _max_chance_correlation(X: np.ndarray) -> float:
    return max(abs(np.corrcoef(X[:, DRIVING], X[:, j])[0, 1]) for j in range(K) if j != DRIVING)


def _importance_ranks(X: np.ndarray, y: np.ndarray) -> list[tuple[int, float]]:
    """(rank of the driving column, margin over the runner-up) per forest seed."""
    rf = RandomForestEstimator(seed=FOREST_SEEDS[0], n_estimators=200, importance_seeds=FOREST_SEEDS)
    rf.fit(X, y)
    out = []
    for values in rf.report().importance_by_seed.values():
        order = list(np.argsort(values)[::-1])
        runner_up = sorted(values, reverse=True)[1]
        out.append((order.index(DRIVING) + 1, values[DRIVING] / max(runner_up, 1e-12)))
    return out


# ------------------------------------------------ the degeneracy guard itself


@pytest.mark.parametrize("n,seeds,threshold", [(500, GEN_SEEDS_500, CORR_THRESHOLD_500), (35, GEN_SEEDS_35, CORR_THRESHOLD_35)])
def test_fixture_seeds_separate_the_driving_column_from_every_noise_column(n, seeds, threshold) -> None:
    """The trap's guard: under each generator seed used below, the realized
    max |corr(driving, noise)| is below the stated threshold, so a top-1 on
    the driving column is the planted signal, not a chance correlate.
    Mutation KA2 (threshold weakened to admit gen seed 1 at n=35, corr
    0.47) must fail here."""
    for gs in seeds:
        X, _ = covariate_driven_field(n, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=gs)
        realized = _max_chance_correlation(X)
        assert realized < threshold, (n, gs, realized)


def test_the_degeneracy_guard_can_fail_a_seed_with_a_chance_correlate() -> None:
    """The guard's negation (rule 4 corollary): gen seed 1 at n=35 realizes
    |corr| ≈ 0.47 with a noise column — the guard REJECTS it, so the guard
    is not vacuous."""
    X, _ = covariate_driven_field(35, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=1)
    assert _max_chance_correlation(X) > CORR_THRESHOLD_35


# ---------------------------------------------- strong regime: both recover


def test_at_n500_strong_signal_importance_ranks_the_driving_column_first_by_a_margin() -> None:
    """The arithmetic check: a forest that cannot find a planted signal in
    500 well-separated examples is broken. Every gen seed × forest seed
    ranks the driving column FIRST with ≥ 10× the runner-up (measured 32×).
    Mutation KA1 (the driving column shuffled post-generation) must fail."""
    for gs in GEN_SEEDS_500:
        X, y = covariate_driven_field(500, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=gs)
        for rank, margin in _importance_ranks(X, y):
            assert rank == 1, (gs, rank)
            assert margin > 10.0, (gs, margin)


def test_at_n35_strong_signal_is_still_recovered_and_the_result_is_reported_not_assumed() -> None:
    """At SNR 2 the planted signal IS recoverable at n=35 (18/18 in the
    probe, margin 16×) — reported plainly rather than tuned away: the
    contrast the prompt anticipates lives at weaker SNR (next test), not
    here. Margin bound 5× (measured 16×; the n=35 realized correlates up to
    0.29 under these seeds cost some margin)."""
    for gs in GEN_SEEDS_35:
        X, y = covariate_driven_field(35, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=gs)
        for rank, margin in _importance_ranks(X, y):
            assert rank == 1, (gs, rank)
            assert margin > 5.0, (gs, margin)


# ---------------------------------- weak regime: the n=500 vs n=35 contrast


def test_at_snr_half_n500_recovers_while_n35_is_at_chance_the_contrast_is_the_finding() -> None:
    """THE FINDING, as a test: with the planted coefficient at HALF the
    noise sd, n=500 still ranks the driving column first in every gen seed
    × forest seed (probe 18/18, margin 3×), while n=35 does NOT reliably —
    the test asserts the INSTABILITY at 35 (top-1 hit rate well below 1,
    median margin near 1×), not recovery. Do not tune the fixture until 35
    passes; the number is the statement about what 35 examples support."""
    hits_500 = 0
    for gs in GEN_SEEDS_500:
        X, y = covariate_driven_field(500, K, driving_column=DRIVING, coefficient=WEAK_COEF, noise_sd=NOISE_SD, seed=gs)
        for rank, margin in _importance_ranks(X, y):
            hits_500 += rank == 1
            assert margin > 1.5, (gs, margin)
    assert hits_500 == len(GEN_SEEDS_500) * len(FOREST_SEEDS)

    hits_35 = 0
    margins_35 = []
    for gs in (0, 1, 2, 3, 4, 5):  # all six: the instability claim needs the spread
        X, y = covariate_driven_field(35, K, driving_column=DRIVING, coefficient=WEAK_COEF, noise_sd=NOISE_SD, seed=gs)
        for rank, margin in _importance_ranks(X, y):
            hits_35 += rank == 1
            margins_35.append(margin)
    total_35 = 6 * len(FOREST_SEEDS)
    assert hits_35 < 0.8 * total_35, hits_35  # NOT reliable recovery (probe: 9/18)
    assert np.median(margins_35) < 2.0  # runner-up is competitive: the ranking is unstable


# --------------------------------------------- uncertainty on the known field


def test_predictions_track_the_planted_function_and_intervals_cover_near_nominal() -> None:
    """Uncertainty sanity on the known field with GENERATION-LEVEL holdout
    (a second draw of the same generated field — not CV machinery, which is
    E2.4's): predictions near the planted 2·X₃ (RMSE within 1.5× the noise
    sd at n=500), and the QRF 5–95% interval covers the held-out y at
    ≥ 0.75 (nominal 0.90; §1 measured 0.84 — mild under-coverage is the
    honest QRF behaviour, stated). ddof=0 sd near the planted noise."""
    X, y = covariate_driven_field(500, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=42)
    X_hold, y_hold = covariate_driven_field(1000, K, driving_column=DRIVING, coefficient=STRONG_COEF, noise_sd=NOISE_SD, seed=1042)
    rf = RandomForestEstimator(seed=0, n_estimators=300, importance_seeds=(0,))
    rf.fit(X, y)

    mean, sd = rf.predict(X_hold)
    rmse = float(np.sqrt(np.mean((y_hold - mean) ** 2)))
    assert rmse < 1.5 * NOISE_SD
    assert 0.7 * NOISE_SD < sd.mean() < 1.5 * NOISE_SD

    q = rf.predict_quantiles(X_hold, quantiles=(0.05, 0.95))
    coverage = float(np.mean((y_hold >= q[:, 0]) & (y_hold <= q[:, 1])))
    assert coverage >= 0.75
