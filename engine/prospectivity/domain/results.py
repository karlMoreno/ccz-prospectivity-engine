"""Result types emitted by ProspectivityEngine.run() (Phase 2-4 fill these in;
Phase 0 only needs the shapes to exist so interfaces can reference them).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from engine.prospectivity.provenance.artifact import ProvenanceArtifact


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


class RunManifest(ProvenanceArtifact):
    """Model-run provenance: the third artifact in docs/contracts/PROVENANCE.md
    (ingestion -> features -> RUN). Records what one modelling run did; it
    quotes the corpus and feature-stack hashes it consumed in the inherited
    `upstream_hashes`, so a prediction traces to exactly one of each.

    Refactored onto ProvenanceArtifact (2026-07-29) WITHOUT changing what it
    records: every original field survives. The one rename is
    `created_at` -> the base's `generated_at` — same fact, same value, the
    name the other two artifacts already use, which is what lets a reader (and
    the shared-field test) treat all three uniformly. Field VALUES for Phase
    2-4 are still filled by the emitter; this remains a shape until then.
    """

    run_id: str
    seed: int
    inputs: dict = Field(default_factory=dict)
    cv_scores: list[CVScore] = Field(default_factory=list)
    ts6_agreement: TS6Agreement | None = None
    economic_results: list[EconomicScenarioResult] = Field(default_factory=list)
    output_hashes: dict[str, str] = Field(default_factory=dict)
