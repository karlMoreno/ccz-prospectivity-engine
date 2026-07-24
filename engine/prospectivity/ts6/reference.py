"""TS6Reference — STRATEGY, plus the compare_to_ts6() mechanism it feeds.

TS6Reference abstracts "how do I load the digitized TS-6 benchmark surface"
(a synthetic raster in Phase 0/CI, the real digitized ts6_abundance.tif from
Phase 3 on — Integration Checkpoint 3). `compare_to_ts6` is the fixed
resample-then-score sequence (AR-P07); it is a plain function, not a class,
because there is only one honest way to do this comparison — the swappable
part is only *where the TS-6 surface comes from*, which is TS6Reference's job.

    ┌─────────────────────┐        ┌─────────────────────────┐
    │   TS6Reference (ABC)  │        │  FixtureTS6Reference      │  (tests only)
    │   .load() -> TS6Surface│◄───────┤                            │
    └─────────────────────┘        └─────────────────────────┘
                │                    ┌─────────────────────────┐
                │                    │  DigitizedTS6Reference     │  (Phase 3)
                └───────────────────►│                            │
                                     └─────────────────────────┘
    compare_to_ts6(prediction, ts6_surface) -> TS6Agreement   (Phase 3, E3.3)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.results import PredictionSurface, TS6Agreement
from engine.prospectivity.domain.ts6 import TS6Surface


class TS6Reference(ABC):
    """Produces the digitized/synthetic TS-6 benchmark surface."""

    @abstractmethod
    def load(self) -> TS6Surface:
        """Return the TS-6 benchmark surface, with `role_note` set (Contract 6:
        "benchmark_only" vs "reproduction_check" — see TS6Surface docstring)."""
        raise NotImplementedError


def compare_to_ts6(prediction: PredictionSurface, ts6_surface: TS6Surface) -> TS6Agreement:
    """Resample both surfaces to a common grid and score agreement (AR-P07).

    Phase 3 (E3.3) implements the resample + spatial-correlation/mean-difference
    /RMSE computation. Left unimplemented in Phase 0 on purpose — no estimator
    exists yet to produce a `prediction` to compare.
    """
    raise NotImplementedError("compare_to_ts6 is implemented in Phase 3 (E3.3)")
