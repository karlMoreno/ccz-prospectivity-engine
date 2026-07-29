"""CovariateRegistry — REGISTRY, mirroring E1.2's NormalizerRegistry.

Same division of labour: the CovariateRecipe classes are the STRATEGIES (one
per Contract 3 recipe); the registry decouples recipe *selection* from any
caller — nothing above this seam branches on a covariate name to pick an
implementation, it asks the registry. Adding covariate #9 is one contract
entry plus one class in RECIPE_CLASSES, never an if/elif anywhere (AR-D01).

    ┌─────────────────────────┐      ┌──────────────────────────────────┐
    │ caller (stack builder,   │─────►│        CovariateRegistry          │
    │  Phase-2 feature matrix) │      │  {"depth": DepthRecipe(...),      │
    └─────────────────────────┘      │   "slope": HornSlopeRecipe(...)}  │
                                      │  .build(name, grid)               │
                                      │  .build_all(grid)  (contract order)│
                                      └──────────────────────────────────┘

`build_default_registry()` constructs recipes FROM the contract (names,
params, versions all read from covariates.yaml — never duplicated in Python)
and enforces, at construction time:
- every ENABLED contract entry has an implementation (completeness, the
  NormalizerRegistry.assert_complete guarantee);
- the contract's recipe_version equals the class's RECIPE_VERSION — the
  contract's own rule ("any change to a recipe's math or parameters REQUIRES
  bumping recipe_version") enforced in both directions;
- Option-B candidates stay out: only `covariates:` entries with
  enabled: true are built, and their recipe strings (external_raster,
  classify_from_dem) have no class here at all.
"""

from __future__ import annotations

from engine.prospectivity.features._contract import enabled_covariates, load_covariates_yaml
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipe import CovariateRecipe, CovariateResult
from engine.prospectivity.features.recipes import (
    BpiRecipe,
    DepthRecipe,
    HornAspectRecipe,
    HornSlopeRecipe,
    PlanCurvatureRecipe,
    ProfileCurvatureRecipe,
    RoughnessRecipe,
    TpiRecipe,
)

# The recipe-string -> implementation map. Deliberately does NOT contain
# Option B's "external_raster" / "classify_from_dem": enabling those in the
# contract without building them fails loudly here.
RECIPE_CLASSES: dict[str, type[CovariateRecipe]] = {
    DepthRecipe.RECIPE: DepthRecipe,
    HornSlopeRecipe.RECIPE: HornSlopeRecipe,
    HornAspectRecipe.RECIPE: HornAspectRecipe,
    RoughnessRecipe.RECIPE: RoughnessRecipe,
    ProfileCurvatureRecipe.RECIPE: ProfileCurvatureRecipe,
    PlanCurvatureRecipe.RECIPE: PlanCurvatureRecipe,
    TpiRecipe.RECIPE: TpiRecipe,
    BpiRecipe.RECIPE: BpiRecipe,
}


class CovariateRegistry:
    """Maps covariate name -> CovariateRecipe; preserves registration
    (= contract) order so build_all() output order is deterministic."""

    def __init__(self) -> None:
        self._recipes: dict[str, CovariateRecipe] = {}  # insertion-ordered

    def register(self, recipe: CovariateRecipe) -> None:
        if recipe.name in self._recipes:
            raise ValueError(f"Covariate {recipe.name!r} registered twice")
        self._recipes[recipe.name] = recipe

    def names(self) -> list[str]:
        return list(self._recipes)

    def build(self, name: str, grid: DemGrid) -> CovariateResult:
        try:
            recipe = self._recipes[name]
        except KeyError:
            raise KeyError(f"No CovariateRecipe registered for {name!r}") from None
        return recipe.build(grid)

    def build_all(self, grid: DemGrid) -> list[CovariateResult]:
        return [recipe.build(grid) for recipe in self._recipes.values()]


def build_default_registry(contract: dict | None = None) -> CovariateRegistry:
    """The production registry: one recipe per ENABLED Contract 3 entry.
    `contract` is a testability seam (same precedent as build_corpus's
    adapter_builders, P2) — production callers pass nothing and get
    docs/contracts/covariates.yaml."""
    contract = contract if contract is not None else load_covariates_yaml()
    registry = CovariateRegistry()
    for entry in enabled_covariates(contract):
        try:
            recipe_class = RECIPE_CLASSES[entry["recipe"]]
        except KeyError:
            raise ValueError(
                f"Contract enables covariate {entry['name']!r} with recipe "
                f"{entry['recipe']!r}, but no implementation is registered — "
                "implement it (or disable the entry) before building features"
            ) from None
        if recipe_class.RECIPE_VERSION != entry["recipe_version"]:
            raise ValueError(
                f"recipe_version mismatch for {entry['name']!r}: contract says "
                f"{entry['recipe_version']}, implementation is {recipe_class.RECIPE_VERSION} — "
                "the contract requires these to move together"
            )
        registry.register(recipe_class(entry["name"], entry.get("params", {})))
    return registry
