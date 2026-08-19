"""Result types emitted by ProspectivityEngine.run() (Phase 2-4 fill these in;
Phase 0 only needs the shapes to exist so interfaces can reference them).
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

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
    """One (design, fold, estimator, metric) row of the flat comparison table.
    CLAUDE.md: "Never report a plain random-split score. Always run the mean
    baseline alongside." — every row carries the baseline's value for the
    SAME design, fold and metric beside it (E2.4 original requirement 1:
    uplift per fold, not only averaged).

    E2.4 §2B REVISION of the Phase-0 shape (before: estimator_name,
    cv_strategy, metric_name, metric_value, baseline_metric_value). Added:
    `fold_name` (per-fold results, never only means — requirement 2);
    `metric_status` / `baseline_metric_status` (a value is None exactly when
    its status is not "ok" and the status NAMES why — the validation
    metrics' MetricValue contract, so a confidently-wrong sd=0 point or a
    refused estimator is never a bare null); `uncertainty_method` (BACKLOG
    §3 obligation 7: the short declared key for the KIND of number this
    estimator's sd is, beside every row — the sentence it names lives once per
    estimator in RunManifest.estimator_declarations); `n_test`. `cv_strategy` keeps its Phase-0 name and now carries the
    design name ("leave_one_cluster_out", …). `metric_value` became Optional
    for the REFUSED / undefined cases, each named by status; the stub case
    that motivated Optional baseline_metric_value in Phase 0 no longer
    exists — the runner always fills it."""

    model_config = ConfigDict(extra="forbid")

    estimator_name: str
    cv_strategy: str  # the design name
    fold_name: str
    metric_name: str  # e.g. "rmse"
    metric_value: float | None
    metric_status: str = "ok"
    baseline_metric_value: float | None = None
    baseline_metric_status: str | None = None
    uncertainty_method: str | None = None
    n_test: int | None = None
    # Obligation 3: the sd≈0 counts travel with the FLAT table too, not only
    # inside the structured record's metric details — a zero paired
    # uncertainty is a red flag to show wherever the number is shown.
    # None for metrics that do not involve sd.
    n_sd_zero: int | None = None
    n_sd_zero_wrong: int | None = None


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


SCORES_FIRST_VISIBLE_DESCRIPTION = (
    "When this run's comparison scores first became visible — THE PRE-REGISTRATION "
    "CLOCK (docs/BACKLOG.md §2): every acceptance threshold set after this moment is "
    "post-hoc for this dataset, permanently (for kriging in the FULL sense: it fits "
    "real coordinates against real y, so its scores are real measurements today). "
    "This field sits OUTSIDE the content hash (like generated_at) so identical runs "
    "hash identically across days — and is therefore MUTABLE METADATA: honest by "
    "convention, not by mechanism; nothing detects a hand-edited timestamp. THE "
    "AUTHORITATIVE DATE IS THE COMMIT THAT INTRODUCED THE SCORES — the git history is "
    "the witness, not this JSON."
)


class RunManifest(ProvenanceArtifact):
    """Model-run provenance: the fourth artifact in docs/contracts/PROVENANCE.md
    (corpus -> feature stack -> training matrix -> RUN). Records what one
    modelling run did; it quotes the training-matrix hash it consumed (which
    chains to corpus + feature stack) AND the corpus and feature-stack hashes
    directly in the inherited `upstream_hashes`, so a score traces to exactly
    one of each by lookup (and E2.5's guard can check all three by name).

    Refactored onto ProvenanceArtifact (2026-07-29) WITHOUT changing what it
    records: every original field survives. The one rename is
    `created_at` -> the base's `generated_at` — same fact, same value, the
    name the other two artifacts already use, which is what lets a reader (and
    the shared-field test) treat all three uniformly.

    E2.4 §2B/§2D REVISION — the emitter now exists
    (`validation/runner.py: emit_run_manifest`); this is no longer only a
    shape. Added: `scores_first_visible` (OUTSIDE the content hash — see its
    description; the one wall-clock exception, BACKLOG §2); `data_origin`
    (COMPUTED from the training matrix's origin, never declared by hand —
    SYNTHETIC today; the watermark derives from it at render time, default-on,
    P2.0 rule); `estimator_declarations` (each estimator's input_kind,
    uncertainty_method, uncertainty_semantics and class, read from the
    declarations — E2.4 §2C);
    `cross_validation` (the structured record: every design's fold assignment
    with its required and measured separations, every (design, fold,
    estimator) result with status / refusal / metrics / uplift / the
    estimator's per-fold provenance, and the pooled metrics); and
    `claim_eligible_designs` (designs whose recorded declaration is
    spatially_blocked; random k-fold and leave-one-station-out never appear).
    `cv_scores` remains the flat per-metric table (CVScore, revised). Phase
    3–4 fill ts6_agreement / economic_results / output_hashes.
    """

    # `run_id` joins the two base exclusions and `scores_first_visible`
    # (E2.4 §2 review): it is the IDENTITY of one emission, not a substance
    # — a random uuid inside the hash would make every engine run hash
    # differently on identical inputs, destroying the one property the hash
    # exists to provide (PROVENANCE.md; CLAUDE.md "same inputs + seed ->
    # same outputs"). Two runs that differ in ANY input, decision or score
    # still hash differently; two emissions of the same run do not.
    HASH_EXCLUDED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"content_hash", "generated_at", "scores_first_visible", "run_id"}
    )

    run_id: str
    seed: int
    inputs: dict = Field(default_factory=dict)
    cv_scores: list[CVScore] = Field(default_factory=list)
    ts6_agreement: TS6Agreement | None = None
    economic_results: list[EconomicScenarioResult] = Field(default_factory=list)
    output_hashes: dict[str, str] = Field(default_factory=dict)
    # ---- E2.4 additions
    scores_first_visible: datetime | None = Field(
        default=None, description=SCORES_FIRST_VISIBLE_DESCRIPTION
    )
    # The description above is JSON-SCHEMA metadata: a reader of the emitted
    # JSON never sees it (E2.4 §2 review). The same sentence is therefore
    # emitted as a VALUE, inside the substance hash (it is a constant, so
    # reproducibility is unaffected) — so the caveat travels with the file.
    scores_first_visible_note: str = SCORES_FIRST_VISIBLE_DESCRIPTION
    data_origin: str | None = None
    estimator_declarations: dict[str, dict] = Field(default_factory=dict)
    cross_validation: dict = Field(default_factory=dict)
    claim_eligible_designs: list[str] = Field(default_factory=list)
