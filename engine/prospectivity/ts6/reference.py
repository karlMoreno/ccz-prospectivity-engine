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
    """Phase-0 seam, SUPERSEDED at E3.3: the real comparison lives in
    `engine.prospectivity.ts6.comparison` (`compare_surface_to_ts6` /
    `compare_all_to_ts6`), which consumes E3.1+2's in-memory surfaces rather
    than this signature's file record.

    THIS STUB STILL RAISES, deliberately: `ProspectivityEngine.run()` passes a
    `dict[str, (mu, sd)]` predicted at the 35 TRAINING locations — not grid
    surfaces — so wiring run() to the real comparison is E3.4's assembly, and
    it carries the OPEN ARITY QUESTION (`RunManifest.ts6_agreement` is
    singular; the comparison returns one agreement PER ESTIMATOR — Karl's
    call, docs/BACKLOG.md §3). A silent adapter here would decide that by
    accident.
    """
    raise NotImplementedError(
        "compare_to_ts6's engine wiring is E3.4's: the real comparison is "
        "engine.prospectivity.ts6.comparison.compare_all_to_ts6, which needs "
        "E3.1+2 grid surfaces, and the manifest's ts6 arity is undecided "
        "(docs/BACKLOG.md §3)"
    )
