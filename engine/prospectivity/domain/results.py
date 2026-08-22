"""Result types emitted by ProspectivityEngine.run().

`CVScore` and `RunManifest` are EMITTED and tested since E2.4 §2 — the run
manifest is written by `validation/runner.py: emit_run_manifest` and a real
one is committed at `data/runs/e2.4/run_manifest.json`; since E3.4 it is
EXTENDED by `provenance/emitter.py: extend_run_manifest` with the surfaces,
the TS-6 agreement mapping, the claim verdict and the recomputed chain.
`TS6Agreement` is filled by `ts6/comparison.py` (E3.3). `PredictionSurface`,
`UncertaintySurface` and `EconomicScenarioResult` are still Phase-0 shapes:
the first two have NO PRODUCER — E3.1+2's writer records a surface's
identity in its sidecar and E3.4's manifest records it under `surfaces`,
neither through these types (a stale-reference finding of the E3.4 2B
sweep, recorded rather than silently retired); economics is Phase 4. (The
former blanket "Phase 2-4 fill these in" was corrected at the E2.4 audit,
F-3: it survived the §2B stale-reference sweep and contradicted the same
file's own contents.)
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
    """One surface's agreement with the TS-6 benchmark (E3.3).

    EXTENDED at E3.3 from the Phase-0 stub (the E2.4 §2B revision protocol:
    every original field survives; the additions are what the implementation
    needed and the stub could not know). The load-bearing additions:

    * `n_eff` beside `spatial_correlation` — Karl's decision (E3.0 §5): a
      naive r over N smooth cells carries a fictional df, so the effective
      sample size is printed BESIDE the number, and there is NO p-value.
    * `inflation_note` — THE LIMIT, required in the output next to the
      number, not only in a doc.
    * `benchmark_uncertainty(_note)` — the benchmark is a raster produced by
      eye from a printed map; a comparison that treats it as exact overstates
      its own precision.
    * `data_origin` / `watermark` — COMPUTED from the inputs, never declared.
    * `estimator_name` — the agreement self-identifies which surface it
      describes. This does NOT decide the manifest's arity (one agreement or
      many is E3.4's open question, docs/BACKLOG.md §3); it makes both
      answers expressible.
    """

    model_config = ConfigDict(extra="forbid")

    spatial_correlation: float | None = None
    mean_difference: float | None = None
    rmse: float | None = None
    role_note: str | None = None  # copied from TS6Surface.role_note
    # ---- E3.3 additions
    estimator_name: str | None = None
    n_cells: int | None = None
    n_eff: float | None = None
    n_eff_method: str | None = None
    correlation_status: str | None = None  # "ok" | names the degenerate case
    interpretation: str | None = None
    inflation_note: str | None = None
    mean_difference_note: str | None = None
    benchmark_uncertainty: float | None = None
    benchmark_uncertainty_note: str | None = None
    data_origin: str | None = None
    watermark: str | None = None
    resampling: dict | None = None


class EconomicScenarioResult(BaseModel):
    """One scenario's footprints, as the manifest records them (E4.1 2B
    REVISION). BEFORE: `scenario_name`, a COPIED `illustrative_only` boolean,
    one `minable_footprint_path`, one `minable_area_m2`. AFTER: the cutoff
    WITH its origin, the confidence levels and the note that z is a stated
    reading, one footprint summary per ESTIMATOR per LEVEL (with the raster
    file E4.2 fills), each estimator's uncertainty semantics (they travel,
    or Decision 2 loses its advantage), the filters applied, the COMPUTED
    origin, and the per-reason WATERMARK VERDICT — nothing copies the flag;
    the verdict's cause CITES it."""

    model_config = ConfigDict(extra="forbid")

    scenario_name: str
    description: str | None = None
    grade_metric: str | None = None
    cutoff: dict | None = None  # value, units, data_origin, author
    confidence_levels: list[float] = Field(default_factory=list)
    confidence_note: str | None = None
    footprints: dict[str, dict[str, dict]] = Field(default_factory=dict)  # estimator -> z -> summary
    uncertainty_semantics: dict[str, str] = Field(default_factory=dict)
    filters: dict = Field(default_factory=dict)
    caveats: list[str] = Field(default_factory=list)
    data_origin: str | None = None  # COMPUTED
    watermark: dict | None = None  # the WatermarkVerdict record, DERIVED
    provenance: dict = Field(default_factory=dict)


class EconomicDifferenceResult(BaseModel):
    """Contract 4's headline output: minable under b and NOT under a (E4.1)."""

    model_config = ConfigDict(extra="forbid")

    pair: list[str]
    meaning: str
    footprints: dict[str, dict[str, dict]] = Field(default_factory=dict)
    data_origin: str | None = None
    watermark: dict | None = None


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
    `cv_scores` remains the flat per-metric table (CVScore, revised).

    E3.4 REVISION (the same 2B protocol; Karl's arity decision at the E3.3
    approval, 2026-08-22). BEFORE: `ts6_agreement: TS6Agreement | None` —
    ONE agreement, unable to say which estimator it described — and
    `output_hashes` populated by nothing. AFTER:

    * `ts6_agreement: dict[str, TS6Agreement] | None` — ONE AGREEMENT PER
      ESTIMATOR, keyed by name, each self-identifying via `estimator_name`.
      Collapsing to one number would force a "which estimator IS the
      comparison" answer nobody has argued for, and the three genuinely
      differ (kriging near-constant, RF ceiling-bound, the baseline flat by
      construction). `None` keeps its meaning — THE COMPARISON STEP DID NOT
      RUN — which is what the committed E2.4 CV-only artifact records; an
      empty mapping would be a comparison over zero estimators, which the
      registry (baseline REQUIRED) makes unrepresentable.
    * `output_hashes` — FILLED: `{basename: sha256}` for every file the run
      wrote, each recomputed from the bytes at emission (basenames, never
      paths — a path in the substance is the E2.4-audit defect one artifact
      over).
    * `prediction_grid`, `surfaces`, `claim`, `provenance_chain` — NEW, all
      defaulting to None so a CV-only manifest still validates. `surfaces`
      is each estimator's surface identity (summary, origin, watermark, the
      two rasters' hashes); `claim` is E2.5's verdict AS DATA — every
      design's preconditions, pass and fail, by name — plus the design the
      caller declared as the claim's basis; `provenance_chain` is every
      upstream link RECOMPUTED at emission with its off-machine
      verifiability stated, because a chain that claims more than it
      delivers is the defect the path-hash BACKLOG entry exists to prevent.

    THE HASH COVERED THE SHAPE — until HASH.1 (2026-08-22). `substance()`
    dumped every field, defaults included, so adding a field re-hashed every
    committed run manifest: the E2.4 artifact was RE-STAMPED at E3.4 (its
    four new fields null, its `content_hash` recomputed, every other byte
    identical). HASH.1 made the scheme shape-tolerant: that artifact is now
    LEGACY (no schema_version) and hashed over the frozen set below, so its
    hash never moves again; fresh manifests hash their present fields plus
    `schema_version`. A new field here must default to None and bump
    SCHEMA_VERSION (`provenance/artifact.py`).
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
    # HASH.1: the field set frozen at 2026-08-22 — what data/runs/e2.4/
    # run_manifest.json (LEGACY, re-stamped at E3.4 with its five nulls IN the
    # substance) is hashed over. A SNAPSHOT; never regenerate from model_fields.
    SCHEMA_VERSION: ClassVar[int] = 2  # E4.1: + economic_differences
    LEGACY_HASHED_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "claim", "claim_eligible_designs", "contract_versions", "cross_validation", "cv_scores",
        "data_origin", "derivation", "economic_results", "estimator_declarations", "generator",
        "inputs", "output_hashes", "prediction_grid", "provenance_chain",
        "scores_first_visible_note", "seed", "surfaces", "ts6_agreement", "upstream_hashes",
    })

    run_id: str
    seed: int
    inputs: dict = Field(default_factory=dict)
    cv_scores: list[CVScore] = Field(default_factory=list)
    # E3.4: a MAPPING, one self-identifying agreement per estimator (see the
    # docstring's revision note). None = the comparison step did not run.
    ts6_agreement: dict[str, TS6Agreement] | None = None
    economic_results: list[EconomicScenarioResult] = Field(default_factory=list)
    # E4.1 (schema_version 2): Contract 4's difference pairs. None = the
    # economics step did not run (the legacy artifacts).
    economic_differences: list[EconomicDifferenceResult] | None = None
    # E3.4: filled by provenance/emitter.py — {basename: sha256 of the bytes}.
    output_hashes: dict[str, str] = Field(default_factory=dict)
    # ---- E3.4 additions (provenance/emitter.py: extend_run_manifest)
    prediction_grid: dict | None = None
    surfaces: dict[str, dict] | None = None
    claim: dict | None = None
    provenance_chain: dict | None = None
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
    # THE EVIDENCE THE ORIGIN TAXONOMY REQUIRES, carried in the artifact so a
    # committed run manifest is SELF-DECLARING (P2.0: a file under data/
    # declares its origin, and each origin has an evidence bar — SYNTHETIC
    # needs the generator's import path AND the seed, DERIVED needs the
    # derivation). A run manifest's origin is COMPUTED from its inputs, so it
    # is SYNTHETIC today and DERIVED at Checkpoint 1; both fields are always
    # recorded, so the artifact satisfies whichever it computes to — and both
    # are honest provenance in their own right: who computed this, from what.
    generator: str | None = None
    derivation: str | None = None
    estimator_declarations: dict[str, dict] = Field(default_factory=dict)
    cross_validation: dict = Field(default_factory=dict)
    claim_eligible_designs: list[str] = Field(default_factory=list)
