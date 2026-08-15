"""Estimator — STRATEGY + TEMPLATE METHOD (E2.1 revision of the Phase-0 ABC).

One interface behind ordinary kriging (TS-6 parity, E2.2), random forest
(E2.3), and the mandatory mean baseline (E2.1, CLAUDE.md "always run the
mean baseline alongside"). `predict` returns a (mean, std) pair rather than
a bare array — CLAUDE.md: "Uncertainty is always paired with any prediction
surface. Never emit a prediction without its uncertainty."

E2.1 REVISION (the Section-1 ABC check; before/after in
docs/walkthroughs/E2.1.md): the Phase-0 shape could EXPRESS pairing — one
call returns both — but could not ENFORCE it: an implementation returning
`(mean, None)`, a bare array (which unpacks positionally into two rows!),
or a 3-tuple sailed through, so the pairing rule was documentary. `predict`
is now the TEMPLATE METHOD — validate the pair, never skippable — and
concrete estimators implement the `_predict` hook, exactly the
`build()/_compute()` split CovariateRecipe uses.

    ┌────────────────────────────────────────────────┐
    │                Estimator (ABC)                  │
    │  fit(features, target)            <- abstract   │
    │  predict(features) -> (mean, std) <- TEMPLATE:  │
    │      pair = self._predict(features)   validate  │
    │  _predict(features)               <- hook       │
    └────────────────────────────────────────────────┘
        ▲                ▲                ▲
  ┌────────────┐  ┌────────────┐  ┌────────────────┐
  │ MeanBaseline│  │ Kriging     │  │ RandomForest    │
  │ (E2.1)      │  │ (E2.2)      │  │ (E2.3)          │
  └────────────┘  └────────────┘  └────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class Estimator(ABC):
    """A fitted spatial estimator that predicts abundance with paired uncertainty."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """FINAL, enforced — not by convention. The E2.1 adversarial review
        probe-demonstrated that a subclass overriding `predict` itself
        bypasses the pairing validation entirely (and still passes the
        registry's isinstance gate), which would put the express-but-not-
        enforce gap right back one level up. Refused at class-definition
        time, so a bypassing estimator cannot even be declared."""
        super().__init_subclass__(**kwargs)
        if "predict" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} overrides Estimator.predict — predict() is the "
                "pairing-validation template method and is final; implement the "
                "_predict hook instead"
            )

    @abstractmethod
    def fit(self, features: Any, target: Any) -> None:
        """Fit the estimator on training features + the MASS abundance target."""
        raise NotImplementedError

    def predict(self, features: Any) -> tuple[Any, Any]:
        """Return `(mean, std)` — TEMPLATE METHOD, final (enforced by
        `__init_subclass__` above): concrete estimators implement
        `_predict`, and the pairing rule is validated HERE. Refuses, naming
        the estimator: a non-pair return (a bare array unpacks positionally
        — a (2, n) array would silently become "mean" and "std"), wrong
        arity, a None member, a SHAPE-mismatched pair (a (5,) mean with a
        (3,) std leaves two predictions with no paired uncertainty — the
        exact forbidden condition, hidden inside a well-formed tuple), and
        an ndarray std carrying NaN or negative values (a NaN uncertainty
        is an absent uncertainty wearing a float dtype)."""
        result = self._predict(features)
        if not isinstance(result, tuple) or len(result) != 2:
            raise ValueError(
                f"{type(self).__name__}._predict returned "
                f"{type(result).__name__} — the contract is a (mean, std) "
                "2-tuple; a prediction is never emitted without its paired "
                "uncertainty"
            )
        mean, std = result
        if mean is None or std is None:
            missing = "mean" if mean is None else "std"
            raise ValueError(
                f"{type(self).__name__}._predict returned None for {missing} — "
                "an unpaired prediction is not a deliverable in this project "
                "(CLAUDE.md: uncertainty is always paired)"
            )
        if np.shape(mean) != np.shape(std):
            raise ValueError(
                f"{type(self).__name__}._predict returned mean of shape "
                f"{np.shape(mean)} with std of shape {np.shape(std)} — every "
                "prediction must have ITS OWN paired uncertainty, so the shapes "
                "must match exactly"
            )
        if isinstance(std, np.ndarray) and std.size:
            if not np.isfinite(std).all():
                raise ValueError(
                    f"{type(self).__name__}._predict returned a non-finite std — "
                    "a NaN/inf uncertainty is an absent uncertainty wearing a "
                    "float dtype"
                )
            if (std < 0).any():
                raise ValueError(
                    f"{type(self).__name__}._predict returned a negative std — "
                    "not a standard deviation"
                )
        return mean, std

    @abstractmethod
    def _predict(self, features: Any) -> tuple[Any, Any]:
        """Hook: the estimator's math. Must return the (mean, std) pair;
        the template method above validates it. NEVER call `_predict`
        directly from consumer code — a caller reaching around `predict`
        skips the validation the hook's underscore exists to route through."""
        raise NotImplementedError
