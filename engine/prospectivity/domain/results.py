"""Result types emitted by ProspectivityEngine.run() (Phase 2-4 fill these in;
Phase 0 only needs the shapes to exist so interfaces can reference them).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionSurface(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimator_name: str
    grid_crs: str = "EPSG:4326"
    resolution_deg: float
    raster_path: str
    content_hash: str | None = None


class UncertaintySurface(BaseModel):
    """Always paired with a PredictionSurface — CLAUDE.md "uncertainty is always
    paired": nothing in this engine may emit a PredictionSurface without one.
    """

    model_config = ConfigDict(extra="forbid")

    estimator_name: str
    method: str  # e.g. "kriging_variance", "rf_quantile"
    grid_crs: str = "EPSG:4326"
    resolution_deg: float
    raster_path: str
    content_hash: str | None = None


class CVScore(BaseModel):
    """One spatial cross-validation result. CLAUDE.md: "Never report a plain
    random-split score. Always run the mean baseline alongside." — hence
    `baseline_metric_value` is not optional-in-spirit even though it's typed
    Optional here for the empty Phase-0 stub case.
    """

    model_config = ConfigDict(extra="forbid")

    estimator_name: str
    cv_strategy: str  # e.g. "spatial_blocked"
    metric_name: str  # e.g. "rmse"
    metric_value: float
    baseline_metric_value: float | None = None


class TS6Agreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial_correlation: float | None = None
    mean_difference: float | None = None
    rmse: float | None = None
    role_note: str | None = None  # copied from TS6Surface.role_note


class EconomicScenarioResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_name: str
    illustrative_only: bool
    minable_footprint_path: str | None = None
    minable_area_m2: float | None = None


class RunManifest(BaseModel):
    """Provenance manifest (run + corpus). Phase 0 only needs the shape; the
    emitter (provenance/) is built in Phase 3.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime
    seed: int
    inputs: dict = Field(default_factory=dict)
    cv_scores: list[CVScore] = Field(default_factory=list)
    ts6_agreement: TS6Agreement | None = None
    economic_results: list[EconomicScenarioResult] = Field(default_factory=list)
    output_hashes: dict[str, str] = Field(default_factory=dict)
