"""Estimator — STRATEGY.

One interface behind ordinary kriging (TS-6 parity, Phase 2), random forest
(Phase 2), and the mandatory mean baseline (Phase 2, CLAUDE.md "always run the
mean baseline alongside"). `predict` returns a (mean, std) pair rather than a
bare array on purpose — CLAUDE.md: "Uncertainty is always paired with any
prediction surface. Never emit a prediction without its uncertainty." Baking
that into the return type makes an uncertainty-less prediction a type error,
not a code-review catch.

    ┌───────────────────────────────────────────┐
    │                Estimator (ABC)              │
    │  fit(features, target)                      │
    │  predict(features) -> (mean, std)            │
    └───────────────────────────────────────────┘
        ▲            ▲                ▲
  ┌───────────┐ ┌───────────┐ ┌────────────────┐
  │ Kriging    │ │ RandomFor.│ │ MeanBaseline    │   (all Phase 2)
  └───────────┘ └───────────┘ └────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Estimator(ABC):
    """A fitted spatial estimator that predicts abundance with paired uncertainty."""

    @abstractmethod
    def fit(self, features: Any, target: Any) -> None:
        """Fit the estimator on training features + the MASS abundance target."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, features: Any) -> tuple[Any, Any]:
        """Return `(mean, std)` — a prediction is never returned without its
        paired uncertainty (CLAUDE.md "uncertainty is always paired")."""
        raise NotImplementedError
