"""Terrain feature engineering (AR-P03, Contract 3: covariates.yaml) — E1.4.

Phase 0 sketched this as "a plain feature_builder callable, not a class
hierarchy"; E1.4 (with the engineer of record, 2026-07-28) built it as the
same Strategy + Registry pairing the ingestion seams use, because the
completeness guarantee mattered: build_default_registry() proves every
enabled contract entry has exactly one implementation at matching
recipe_version, the way NormalizerRegistry.assert_complete does for evidence
classes. engine.py's `feature_builder` callable seam is unchanged —
registry.build_all is what will be plugged into it in Phase 2.

    covariates.yaml (Contract 3, v3: metre-based windows)
        │  loaded, never duplicated (_contract.py)
        ▼
    build_default_registry() ──► CovariateRegistry ──► CovariateRecipe (x8)
        (REGISTRY, registry.py)      │                    (STRATEGY +
                                     │                     TEMPLATE METHOD,
                                     ▼                     recipe.py/recipes.py)
                              build_covariate_stack()
                                 (stack.py: rasters + provenance.json)

    DemGrid (dem_grid.py) — the ONE home of the CRS decision (per-row
    longitude scaling) and the metres cell geometry every recipe consumes.
    window.py — the ONE metres->cells resolution (Contract 3 v3).
"""

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipe import BORDER_POLICY, CovariateRecipe, CovariateResult
from engine.prospectivity.features.registry import CovariateRegistry, build_default_registry
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.features.window import ResolvedWindow, resolve_radius, resolve_square_window

__all__ = [
    "BORDER_POLICY",
    "CovariateRecipe",
    "CovariateResult",
    "CovariateRegistry",
    "DemGrid",
    "ResolvedWindow",
    "build_covariate_stack",
    "build_default_registry",
    "resolve_radius",
    "resolve_square_window",
]
