"""EstimatorRegistry — REGISTRY (NormalizerRegistry's role,
CovariateRegistry's register conventions: duplicate-refusing + type-gated,
which NormalizerRegistry's silently-overwriting register is not).

Why a registry HERE specifically — and this is a STRONGER justification
than the normalizer registry had: CLAUDE.md requires the mean baseline to
run ALONGSIDE every model claim. What `assert_complete()` makes STRUCTURAL
is "the baseline is REGISTERED and cannot be silently absent" — honest
scope (E2.1 review): registration is not execution. The execution half
lands with E2.4's CV runner, which must iterate `names()` (never
cherry-pick via `get()`) so that a complete registry implies a run
baseline; that obligation is recorded in BACKLOG §3. Together the two
halves replace a convention every call site must remember. The normalizer
registry's completeness protects against a FORGOTTEN evidence class (a
data-shape accident); this one protects against a scientific-integrity
rule being skipped (a claim shipped without its floor), which is the
project's whole point.

STATEFUL-INSTANCE CAVEAT (unlike the two registries mirrored, whose
strategies are stateless): estimators carry fit state, and `get()` returns
the ONE shared instance. Safe today because `fit()` overwrites all state
unconditionally and the engine refits before each predict — but E2.4's CV
runner must refit per fold or build fresh instances per fold
(`build_default_registry()` per run is the cheap discipline). Recorded in
the same BACKLOG entry.

    ┌─────────────────────────┐      ┌──────────────────────────────────┐
    │ caller (E2.4 CV runner,  │─────►│        EstimatorRegistry          │
    │  engine.py run)          │      │  {"mean_baseline": MeanBaseline…} │
    └─────────────────────────┘      │  .get(name) · .names()            │
                                      │  .assert_complete()  ← baseline   │
                                      │      cannot be omitted            │
                                      └──────────────────────────────────┘

`REQUIRED_ESTIMATORS` is exactly the CLAUDE.md-mandated baseline. Kriging
(E2.2) and random forest (E2.3) REGISTER when they arrive but are not
required — models are optional, the floor is not.
"""

from __future__ import annotations

from engine.prospectivity.estimators.base import Estimator
from engine.prospectivity.estimators.mean_baseline import MeanBaselineEstimator

MEAN_BASELINE_NAME = "mean_baseline"

# The mandatory set. Deliberately ONLY the baseline: CLAUDE.md mandates the
# floor alongside every claim; it does not mandate any particular model.
REQUIRED_ESTIMATORS: tuple[str, ...] = (MEAN_BASELINE_NAME,)


class EstimatorRegistry:
    """Maps estimator name -> instance; insertion-ordered, duplicate-refusing
    (the CovariateRegistry conventions)."""

    def __init__(self) -> None:
        self._estimators: dict[str, Estimator] = {}

    def register(self, name: str, estimator: Estimator) -> None:
        if name in self._estimators:
            raise ValueError(f"Estimator {name!r} registered twice")
        if not isinstance(estimator, Estimator):
            raise TypeError(
                f"{name!r} is not an Estimator (got {type(estimator).__name__}) — "
                "only the ABC's implementations enter the registry, or the pairing "
                "rule its template method enforces could be bypassed by registration"
            )
        self._estimators[name] = estimator

    def names(self) -> list[str]:
        return list(self._estimators)

    def get(self, name: str) -> Estimator:
        try:
            return self._estimators[name]
        except KeyError:
            raise KeyError(
                f"No estimator registered under {name!r}; registered: {self.names()}"
            ) from None

    def assert_complete(self) -> None:
        """The structural baseline guarantee: every REQUIRED estimator is
        registered, by name. Callers that run "everything in the registry"
        after this call have necessarily run the baseline."""
        missing = [name for name in REQUIRED_ESTIMATORS if name not in self._estimators]
        if missing:
            raise ValueError(
                f"EstimatorRegistry is missing required estimator(s) {missing} — "
                "CLAUDE.md requires the mean baseline alongside every model claim; "
                "a registry without it cannot back a claim"
            )


def build_default_registry() -> EstimatorRegistry:
    """The production registry: the baseline (E2.1, REQUIRED), ordinary
    kriging (E2.2, Karl's decision defaults), and the quantile random forest
    (E2.3, Karl's uncertainty decision). Imported lazily to keep the module
    import graph flat (kriging pulls variogram + geometry; RF pulls
    quantile-forest)."""
    from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator
    from engine.prospectivity.estimators.random_forest import RandomForestEstimator

    registry = EstimatorRegistry()
    registry.register(MEAN_BASELINE_NAME, MeanBaselineEstimator())
    registry.register("ordinary_kriging", OrdinaryKrigingEstimator())
    registry.register("random_forest", RandomForestEstimator())
    registry.assert_complete()
    return registry
