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

    ┌──────────────────────────────────────────────────────────────┐
    │                        Estimator (ABC)                         │
    │  input_kind            : ClassVar  <- DECLARED (E2.4 §2C)      │
    │  uncertainty_method    : ClassVar  <- DECLARED (obligation 7)  │
    │  uncertainty_semantics : ClassVar  <- DECLARED (obligation 7)  │
    │  fit(features, target)            <- abstract                  │
    │  predict(features) -> (mean, std) <- TEMPLATE: validate pair   │
    │  _predict(features)               <- hook                      │
    │  provenance() -> dict             <- abstract (obligations 4–6)│
    └──────────────────────────────────────────────────────────────┘
        ▲                ▲                ▲
  ┌────────────┐  ┌────────────┐  ┌────────────────┐
  │ MeanBaseline│  │ Kriging     │  │ RandomForest    │
  │ (E2.1)      │  │ (E2.2)      │  │ (E2.3)          │
  │ covariates  │  │ coordinates │  │ covariates      │
  └────────────┘  └────────────┘  └────────────────┘

E2.4 §2 REVISION — THREE DECLARATIONS, enforced at class definition like
predict-is-final, so the CV runner routes and labels by DECLARATION, never
by name (the inference-over-declaration defect this project removed in
P2.0d-2, P2.0d-3 and again here — `if name == "ordinary_kriging": use
coords` works and is exactly the wrong shape):

  * `input_kind` — which design matrix this estimator consumes:
    "covariates" (TrainingMatrix.X) or "coordinates" (TrainingMatrix.coords).
    A property of the estimator's MATH (kriging consumes coordinates by
    construction), so it lives on the class, not on a registry entry.
  * `uncertainty_method` — a SHORT key naming the sd's kind (RF's
    "qrf_half_width_q16_q84" is the model; the baseline's "sample_sd_ddof1",
    kriging's "sqrt_ordinary_kriging_variance"), carried beside EVERY
    sd-shaped number in the flat score table; and `uncertainty_semantics` —
    the sentence that says what kind of number that is (a sample moment, a
    model moment, a quantile half-width…), carried once per estimator in the
    manifest's declarations and printed in the comparison tables. BACKLOG §3
    obligation 7: a table that prints three "sd" columns without saying so
    invites a reader to compare them as one quantity.
  * `provenance()` — the estimator's reportable fitted state as a JSON-able
    dict, consumed by the runner per fold (obligations 4–6); the runner never
    reaches around it to private state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import numpy as np

# The two design matrices a TrainingMatrix offers. Exhaustive; a new kind is
# added HERE deliberately (with the runner's routing), never improvised.
INPUT_KINDS: tuple[str, ...] = ("covariates", "coordinates")


class Estimator(ABC):
    """A fitted spatial estimator that predicts abundance with paired uncertainty."""

    input_kind: ClassVar[str]
    uncertainty_method: ClassVar[str]
    uncertainty_semantics: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """FINAL predict, and the two declarations — enforced, not by
        convention. The E2.1 adversarial review probe-demonstrated that a
        subclass overriding `predict` itself bypasses the pairing validation
        entirely (and still passes the registry's isinstance gate), which
        would put the express-but-not-enforce gap right back one level up.
        Refused at class-definition time, so a bypassing estimator cannot
        even be declared. E2.4 §2C adds: an estimator that does not SAY which
        design matrix it consumes, or what kind of number its sd is, cannot
        be declared either (looked up through the MRO: inheriting a parent's
        declaration is a declaration)."""
        super().__init_subclass__(**kwargs)
        if "predict" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} overrides Estimator.predict — predict() is the "
                "pairing-validation template method and is final; implement the "
                "_predict hook instead"
            )
        kind = getattr(cls, "input_kind", None)
        if kind not in INPUT_KINDS:
            raise TypeError(
                f"{cls.__name__} does not declare `input_kind` as one of {INPUT_KINDS} "
                f"(got {kind!r}) — which design matrix an estimator consumes is a "
                "DECLARATION on the class (E2.4 §2C); the CV runner routes by it and "
                "never matches on a name"
            )
        method = getattr(cls, "uncertainty_method", None)
        if not isinstance(method, str) or not method.strip() or any(c.isspace() for c in method):
            raise TypeError(
                f"{cls.__name__} does not declare `uncertainty_method` (a short, "
                "whitespace-free key naming the KIND of its paired sd, e.g. "
                "'qrf_half_width_q16_q84') — BACKLOG §3 obligation 7: it travels beside "
                "every sd-shaped number in the score table"
            )
        semantics = getattr(cls, "uncertainty_semantics", None)
        if not isinstance(semantics, str) or not semantics.strip():
            raise TypeError(
                f"{cls.__name__} does not declare `uncertainty_semantics` (a non-empty "
                "string saying what KIND of number its paired sd is) — BACKLOG §3 "
                "obligation 7: the comparison table carries it beside every sd"
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

    @abstractmethod
    def provenance(self) -> dict:
        """The fitted estimator's REPORTABLE STATE as a JSON-able dict — what
        the CV runner carries into run provenance per (design, fold)
        (BACKLOG §3 obligations 4–6). Each estimator decides what it
        exposes here and what it does not: RF's OOB diagnostic is OUTSIDE
        its `validation_facing_fields()` by construction, and the runner
        consumes only this method, never `_forest` or any private field.
        Raises if called before fit."""
        raise NotImplementedError
