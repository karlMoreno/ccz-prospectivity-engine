"""Terrain feature engineering (AR-P03, Contract 3: covariates.yaml).

Reserved for Phase 1 (E1.4): deterministic, versioned recipes (slope,
roughness, curvature, TPI, BPI, ...) reading covariates.yaml. Not a
class-based Strategy hierarchy like the other seams — covariates.yaml already
makes each recipe a versioned, data-driven entry, so ProspectivityEngine takes
a plain `feature_builder` callable (see engine.py) rather than a new ABC.
"""
