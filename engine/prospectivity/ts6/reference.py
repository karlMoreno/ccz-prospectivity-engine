"""TS6Reference — STRATEGY: where the TS-6 benchmark surface comes from.

TS6Reference abstracts "how do I load the digitized TS-6 benchmark surface"
(a synthetic raster in Phase 0/CI, the real digitized ts6_abundance.tif from
Phase 3 on — Integration Checkpoint 3). The COMPARISON is not here: it lives
in `ts6/comparison.py` (`compare_surface_to_ts6` / `compare_all_to_ts6`,
E3.3) as plain functions, because there is only one honest way to do it —
the swappable part is only *where the TS-6 surface comes from*.

    ┌─────────────────────┐        ┌─────────────────────────┐
    │   TS6Reference (ABC)  │        │  FixtureTS6Reference      │  (tests only)
    │   .load() -> TS6Surface│◄───────┤                            │
    └─────────────────────┘        └─────────────────────────┘
                │                    ┌─────────────────────────┐
                │                    │  DigitizedTS6Reference     │  (G3.1)
                └───────────────────►│                            │
                                     └─────────────────────────┘

RETIRED AT E3.4 (2026-08-22, the 2B revision protocol): the Phase-0
`compare_to_ts6(prediction: PredictionSurface, ts6_surface) -> TS6Agreement`
stub that used to live here. It never had an implementation; E3.3 built the
real comparison against E3.1+2's in-memory surfaces, and its singular
signature could not express "one agreement per estimator" — the arity Karl
decided for the manifest. `ProspectivityEngine` now calls
`compare_all_to_ts6` directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.ts6 import TS6Surface


class TS6Reference(ABC):
    """Produces the digitized/synthetic TS-6 benchmark surface."""

    @abstractmethod
    def load(self) -> TS6Surface:
        """Return the TS-6 benchmark surface, with `role_note` set (Contract 6:
        "benchmark_only" vs "reproduction_check" — see TS6Surface docstring)."""
        raise NotImplementedError

