"""The refuse-to-validate guard (E2.5) — STRUCTURAL REFUSAL, not a convention.

The P1 `_require_production_path()` posture, at claim time: make the invalid
state UNREACHABLE rather than documented. No run may be emitted as a VALIDATED
CLAIM unless every declared precondition holds, and each precondition raises
its OWN refusal naming its OWN failure — "not eligible" sends a reader hunting.

    RunManifest + the design being claimed + the feature-stack manifest
                 │
                 ▼
      ┌────────────────────────────────────────────────────────┐
      │  Precondition (Enum)  ──  _CHECKERS  (one per member)   │
      │  exhaustive BOTH WAYS, enforced at import:              │
      │    every member has a checker  (a precondition with no  │
      │        guard is a rule nobody enforces)                 │
      │    every checker has a member  (a guard with no member  │
      │        is a refusal nobody can discover)                │
      └────────────────────────────────────────────────────────┘
                 │  each checker raises ClaimRefused(precondition, message)
                 ▼
      evaluate_claim() -> ClaimVerdict          require_validated_claim()
        every result, pass and fail              raises if ANY failed,
        + the watermark (never a refusal)        naming EVERY failure

WHY AN ENUM AND A CHECKER MAP, rather than six inline `if`s: the
`Resolution` dispatch precedent (ingestion/pipeline.py). An enum makes the
precondition SET a declared thing, so "did anyone add a rule without a guard"
is answerable mechanically. The reverse direction matters just as much and is
the one usually missed — a guard that no member declares is a refusal that
cannot be found, reported, or tested by anyone who reads the enum.

REFUSAL vs WATERMARK — the distinction is load-bearing and is NOT a
precondition. A synthetic-origin run is WATERMARKED non-scientific, not
refused: building on fixtures is legitimate, publishing from them is not. The
watermark DERIVES from the run's computed origin (`run_watermark` →
`matrix_watermark`, P2.0d-3, default-ON) — this module adds no flag and
re-implements no derivation. It mirrors `scenarios.yaml`'s `illustrative_only`
IN SPIRIT (a non-scientific label travels with the output) and not by copying
its boolean, because the origin is COMPUTED and a boolean would be declared.

WHAT THIS GUARD READS, AND WHAT IT REFUSES TO INFER: declarations and recorded
facts only. `spatially_blocked` comes from the fold assignment's RECORD (which
`split()` writes from the class declaration), never from a design's name —
scheme A (`leave_one_station_out`) and `random_k_fold` both declare False, and
they are refused by that declaration, not because anyone matched on "random".
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.estimators.registry import MEAN_BASELINE_NAME
from engine.prospectivity.model_config import DeclaredField, acceptance_thresholds
from engine.prospectivity.validation.runner import STATUS_SCORED, run_watermark

# The DEM-identity facts precondition 4 re-asserts. Imported from the
# extraction guard rather than restated: one list, two call sites (E2.0-2
# checks it when the matrix is built; this checks the SAME fields at claim
# time, over the recorded stack manifest).
from engine.prospectivity.features.extraction import _DEM_IDENTITY_FIELDS

REQUIRED_UPSTREAM_HASHES = ("corpus", "feature_stack", "training_matrix")


class Precondition(Enum):
    """The declared set. Adding a member without a checker fails at import
    (see `assert_preconditions_exhaustive`); adding a checker without a member
    fails the same way, from the other direction."""

    SPATIALLY_BLOCKED_CV = "spatially_blocked_cross_validation_ran"
    BASELINE_IN_EVERY_FOLD = "mean_baseline_ran_in_every_fold"
    PAIRED_UNCERTAINTY = "every_prediction_carries_paired_uncertainty"
    SINGLE_DEM_RESOLUTION = "all_feature_layers_share_one_dem"
    PROVENANCE_CHAIN = "provenance_records_corpus_stack_and_matrix_hashes"
    PRE_REGISTERED_THRESHOLD = "an_acceptance_threshold_existed_before_the_scores"


class ClaimRefused(ValueError):
    """One precondition's refusal, carrying WHICH one so a caller can report
    the set rather than the first."""

    def __init__(self, precondition: Precondition, message: str) -> None:
        super().__init__(f"[{precondition.value}] {message}")
        self.precondition = precondition
        self.message = message


@dataclass(frozen=True)
class ClaimInputs:
    """What a precondition may read. `contract` is Contract 8's testability
    seam (the `target_definition` / `build_default_registry` precedent):
    production callers omit it and the accessor loads the real file."""

    manifest: RunManifest
    design: str
    stack: Mapping
    contract: dict | None = None


@dataclass(frozen=True)
class PreconditionResult:
    precondition: Precondition
    passed: bool
    detail: str

    def to_record(self) -> dict:
        return {
            "precondition": self.precondition.value,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ClaimVerdict:
    """Every precondition's outcome, plus the watermark — which is NOT a
    precondition and never a refusal."""

    design: str
    results: tuple[PreconditionResult, ...]
    watermark: str | None
    data_origin: str | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def failures(self) -> tuple[PreconditionResult, ...]:
        return tuple(r for r in self.results if not r.passed)

    @property
    def eligible(self) -> bool:
        """DERIVED, never stored: eligibility IS "no precondition failed", so
        the state "not eligible with nothing failing" cannot be represented.
        A stored flag could drift from the results it summarizes — and the
        first thing that would drift into it is the watermark, which must
        never gate eligibility (see the module docstring)."""
        return not self.failures

    @property
    def is_scientific(self) -> bool:
        """A watermarked run is not scientific EVEN IF eligible — the two
        questions are separate, which is the whole point of §1's distinction."""
        return self.eligible and self.watermark is None

    def to_record(self) -> dict:
        return {
            "design": self.design,
            "eligible": self.eligible,
            "is_scientific": self.is_scientific,
            "watermark": self.watermark,
            "data_origin": self.data_origin,
            "preconditions": [r.to_record() for r in self.results],
            "notes": list(self.notes),
        }


# --------------------------------------------------------------- the checkers
# Each raises ClaimRefused with ITS OWN message. Each returns a detail string
# on success, so a passing precondition is reportable too — §2's "report which
# preconditions PASS as well as which fail", which is what shows the guard
# discriminates rather than blanket-refuses.


def _design_record(inputs: ClaimInputs) -> dict:
    designs = {d["name"]: d for d in (inputs.manifest.cross_validation or {}).get("designs", [])}
    if inputs.design not in designs:
        raise ClaimRefused(
            Precondition.SPATIALLY_BLOCKED_CV,
            f"the run manifest records no design named {inputs.design!r} — it carries "
            f"{sorted(designs)}; a claim cannot cite a design the run did not execute",
        )
    return designs[inputs.design]


def _check_spatially_blocked(inputs: ClaimInputs) -> str:
    record = _design_record(inputs)
    if record["spatially_blocked"] is not True:
        raise ClaimRefused(
            Precondition.SPATIALLY_BLOCKED_CV,
            f"design {inputs.design!r} declares spatially_blocked={record['spatially_blocked']!r} — "
            "random k-fold does not satisfy spatial cross-validation, and neither does "
            "leave-one-station-out, which is unbuffered by declaration "
            f"(required_separation_km={record.get('required_separation_km')}). The guard "
            "reads the RECORDED DECLARATION, never the design's name",
        )
    if inputs.design not in (inputs.manifest.claim_eligible_designs or []):
        raise ClaimRefused(
            Precondition.SPATIALLY_BLOCKED_CV,
            f"design {inputs.design!r} declares spatially_blocked=True but is absent from the "
            f"manifest's claim_eligible_designs {manifest.claim_eligible_designs!r} — the "
            "runner and the record disagree about the same run",
        )
    return (
        f"{inputs.design}: spatially_blocked=True, required_separation_km="
        f"{record.get('required_separation_km')}, measured minimum "
        f"{record.get('measured_min_separation_km')} km over {len(record['assignment']['folds'])} folds"
    )


def _check_baseline_every_fold(inputs: ClaimInputs) -> str:
    record = _design_record(inputs)
    fold_names = [f["name"] for f in record["assignment"]["folds"]]
    baseline_rows = {
        r["fold_name"]: r for r in record["results"] if r["estimator_name"] == MEAN_BASELINE_NAME
    }
    missing = [name for name in fold_names if name not in baseline_rows]
    unscored = [
        name for name in fold_names
        if name in baseline_rows and baseline_rows[name]["status"] != STATUS_SCORED
    ]
    if missing or unscored:
        raise ClaimRefused(
            Precondition.BASELINE_IN_EVERY_FOLD,
            f"the mean baseline did not run in every fold of {inputs.design!r}: "
            f"{len(missing)} fold(s) carry no baseline row {missing} and {len(unscored)} "
            f"recorded a non-scored status {unscored}. CLAUDE.md requires the baseline "
            "alongside EVERY model claim, per fold — an averaged baseline is not one",
        )
    return f"{inputs.design}: the mean baseline scored all {len(fold_names)} folds"


def _check_paired_uncertainty(inputs: ClaimInputs) -> str:
    record = _design_record(inputs)
    checked = 0
    for row in record["results"]:
        if row["status"] != STATUS_SCORED:
            continue
        mean, sd = row["predicted_mean"], row["predicted_sd"]
        if len(mean) != len(sd) or not mean:
            raise ClaimRefused(
                Precondition.PAIRED_UNCERTAINTY,
                f"{row['estimator_name']} on fold {row['fold_name']!r} of {inputs.design!r} recorded "
                f"{len(mean)} prediction(s) and {len(sd)} uncertainty value(s) — every "
                "prediction carries ITS OWN paired uncertainty or it is not a deliverable",
            )
        bad = [v for v in sd if not math.isfinite(v) or v < 0]
        if bad:
            raise ClaimRefused(
                Precondition.PAIRED_UNCERTAINTY,
                f"{row['estimator_name']} on fold {row['fold_name']!r} of {inputs.design!r} recorded "
                f"{len(bad)} non-finite or negative uncertainty value(s) — a NaN uncertainty "
                "is an absent uncertainty wearing a float dtype",
            )
        checked += len(mean)
    return f"{inputs.design}: {checked} predictions, each with a finite non-negative paired sd"


def _check_single_dem(inputs: ClaimInputs) -> str:
    """E2.0-2's rule, RE-ASSERTED at claim time over the recorded stack — the
    same `_DEM_IDENTITY_FIELDS` the extraction guard compares, so the two
    cannot drift apart."""
    layers = (inputs.stack or {}).get("layers")
    if not layers:
        raise ClaimRefused(
            Precondition.SINGLE_DEM_RESOLUTION,
            "the feature-stack manifest handed to the guard records no layers — the "
            "single-DEM rule cannot be re-asserted at claim time over a stack that "
            "does not describe itself",
        )
    seen: dict[tuple, list[str]] = {}
    for layer in layers:
        dem = layer.get("dem") or {}
        key = tuple(_normalize(dem.get(f)) for f in _DEM_IDENTITY_FIELDS)
        seen.setdefault(key, []).append(layer.get("name", "<unnamed>"))
    if len(seen) > 1:
        detail = "; ".join(
            f"{dict(zip(_DEM_IDENTITY_FIELDS, key))} <- {names}" for key, names in seen.items()
        )
        raise ClaimRefused(
            Precondition.SINGLE_DEM_RESOLUTION,
            f"the feature layers do not share one DEM: {len(seen)} distinct "
            f"{list(_DEM_IDENTITY_FIELDS)} combinations — {detail}. Mixing resolutions (or "
            "two different DEMs at one resolution) makes every sampled cell describe a "
            "different seafloor; Contract 3 v3 forbids it and E2.0-2 refuses it at build "
            "time — this is the same rule at claim time",
        )
    key = next(iter(seen))
    return f"all {len(layers)} layers share one DEM: {dict(zip(_DEM_IDENTITY_FIELDS, key))}"


def _normalize(value: Any) -> Any:
    """Lists (resolution_deg comes back as [0.1, 0.1] from JSON) are unhashable
    and must compare as tuples."""
    return tuple(value) if isinstance(value, list) else value


def _check_provenance_chain(inputs: ClaimInputs) -> str:
    recorded = inputs.manifest.upstream_hashes or {}
    missing = [k for k in REQUIRED_UPSTREAM_HASHES if not recorded.get(k)]
    if missing:
        raise ClaimRefused(
            Precondition.PROVENANCE_CHAIN,
            f"the run's provenance does not record upstream hash(es) {missing} — a claim "
            "must trace to exactly one corpus, one feature stack and one training matrix "
            f"by mechanical lookup; it records {sorted(recorded)}",
        )
    unhashed = [k for k in REQUIRED_UPSTREAM_HASHES if not str(recorded.get(k, "")).startswith("sha256:")]
    if unhashed:
        raise ClaimRefused(
            Precondition.PROVENANCE_CHAIN,
            f"upstream reference(s) {unhashed} are not sha256 content hashes — a name is "
            "not an identity",
        )
    return "upstream_hashes records corpus, feature_stack and training_matrix, all sha256"


def _check_pre_registered_threshold(inputs: ClaimInputs) -> str:
    """PRECONDITION 6 — the pre-registration clock (docs/BACKLOG.md §2).

    THE TIMESTAMP'S HONESTY LIMIT, STATED WHERE THE COMPARISON HAPPENS and not
    only in a doc: `scores_first_visible` lives OUTSIDE the substance hash (the
    `generated_at` parallel, so identical inputs hash identically across days),
    which makes it MUTABLE METADATA — nothing detects a hand-edited value, and
    this comparison is therefore honest BY CONVENTION, not by mechanism. THE
    AUTHORITATIVE WITNESS IS THE COMMIT that introduced the scores. A guard
    that compared two mutable dates and called the result proof would be
    laundering a convention into a guarantee; this one names the limit and
    still performs the comparison, because a convention that is checked is
    worth more than one that is only written down.
    """
    try:
        declared: DeclaredField = acceptance_thresholds(inputs.contract)
    except ValueError as absent:
        raise ClaimRefused(
            Precondition.PRE_REGISTERED_THRESHOLD,
            f"no pre-registered gate existed when these scores were computed. {absent}",
        ) from absent
    if declared.value is None:
        raise ClaimRefused(
            Precondition.PRE_REGISTERED_THRESHOLD,
            "Contract 8 declares acceptance_thresholds explicitly NULL — a declared "
            "absence is still an absence: no gate existed when these scores were computed",
        )
    if declared.data_origin == "AUTHORED":
        raise ClaimRefused(
            Precondition.PRE_REGISTERED_THRESHOLD,
            f"the acceptance threshold is declared AUTHORED (author "
            f"{declared.author!r}) — a number someone typed is not a pre-registered gate; "
            "it arrives as LITERATURE with a citation that locates it, or as a MEASURED "
            "or DERIVED value with its evidence",
        )
    raw_field = (inputs.contract or {}).get("acceptance_thresholds", {}) if inputs.contract else _raw_threshold_field()
    if raw_field.get("set_after_scores") is True:
        raise ClaimRefused(
            Precondition.PRE_REGISTERED_THRESHOLD,
            "the acceptance threshold declares set_after_scores: true — post-hoc for this "
            "dataset by its own record",
        )
    threshold_date = _declared_date(raw_field)
    scores_visible = inputs.manifest.scores_first_visible
    if threshold_date is not None and scores_visible is not None and threshold_date > scores_visible:
        raise ClaimRefused(
            Precondition.PRE_REGISTERED_THRESHOLD,
            f"the acceptance threshold's provenance ({threshold_date.isoformat()}) POST-DATES "
            f"scores_first_visible ({scores_visible.isoformat()}) — every threshold set after "
            "the scores exist is post-hoc for this dataset, permanently. (Both dates are "
            "mutable metadata; the COMMIT that introduced the scores is the authoritative "
            "witness, and this comparison is honest by convention, not by mechanism.)",
        )
    return (
        f"acceptance threshold declared {declared.data_origin}"
        + (f", dated {threshold_date.isoformat()}" if threshold_date else "")
        + (f", not after scores_first_visible {scores_visible.isoformat()}" if scores_visible else "")
        + " — honest by convention; the commit is the authoritative witness"
    )


def _raw_threshold_field() -> dict:
    """The contract's own acceptance_thresholds mapping, for the two keys the
    DeclaredField does not carry (`declared_at`, `set_after_scores`)."""
    from engine.prospectivity.model_config import load_model_config

    return load_model_config().get("acceptance_thresholds", {}) or {}


def _declared_date(raw_field: Mapping) -> datetime | None:
    raw = raw_field.get("declared_at")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    parsed = datetime.fromisoformat(str(raw))
    return parsed


Checker = Callable[[ClaimInputs], str]

_CHECKERS: dict[Precondition, Checker] = {
    Precondition.SPATIALLY_BLOCKED_CV: _check_spatially_blocked,
    Precondition.BASELINE_IN_EVERY_FOLD: _check_baseline_every_fold,
    Precondition.PAIRED_UNCERTAINTY: _check_paired_uncertainty,
    Precondition.SINGLE_DEM_RESOLUTION: _check_single_dem,
    Precondition.PROVENANCE_CHAIN: _check_provenance_chain,
    Precondition.PRE_REGISTERED_THRESHOLD: _check_pre_registered_threshold,
}


def assert_preconditions_exhaustive(
    members: Any = Precondition, checkers: Mapping[Any, Checker] | None = None
) -> None:
    """THE EXHAUSTIVENESS CHECK, BOTH DIRECTIONS (the `Resolution` dispatch
    precedent). Takes its subjects as arguments so a test can hand it a
    doctored pair and watch it refuse — a completeness check that can only be
    run against the real thing cannot be shown to work.

    Direction 1: every declared precondition has a guard — otherwise a rule in
    the contract is a rule nobody enforces.
    Direction 2: every guard has a declared precondition — otherwise a refusal
    exists that nobody reading the enum can discover, report or test. This is
    the direction usually missed, and it is how a refusal becomes invisible."""
    checkers = _CHECKERS if checkers is None else checkers
    declared = set(members)
    guarded = set(checkers)
    unguarded = sorted(p.value if isinstance(p, Enum) else str(p) for p in declared - guarded)
    if unguarded:
        raise ValueError(
            f"precondition(s) {unguarded} are DECLARED but have no guard — a validation "
            "precondition added to the contract without a corresponding guard is a rule "
            "nobody enforces; add its checker to _CHECKERS"
        )
    undeclared = sorted(p.value if isinstance(p, Enum) else str(p) for p in guarded - declared)
    if undeclared:
        raise ValueError(
            f"guard(s) {undeclared} exist but are NOT declared in the Precondition enum — a "
            "refusal nobody can discover from the declared set; declare it or delete it"
        )


assert_preconditions_exhaustive()  # structural: a divergence cannot be imported


# ------------------------------------------------------------------ the guard


def evaluate_claim(
    manifest: RunManifest,
    *,
    design: str,
    feature_stack_manifest: Mapping | None = None,
    contract: dict | None = None,
) -> ClaimVerdict:
    """Every precondition, evaluated — passes AND failures — plus the
    watermark. Never raises for a failed precondition: the caller who wants
    the refusal calls `require_validated_claim`, and the caller who wants the
    REPORT calls this."""
    inputs = ClaimInputs(
        manifest=manifest, design=design, stack=feature_stack_manifest or {}, contract=contract
    )
    results = []
    for precondition in Precondition:  # enum order is the reporting order
        checker = _CHECKERS[precondition]
        try:
            detail = checker(inputs)
        except ClaimRefused as refusal:
            results.append(PreconditionResult(precondition, False, refusal.message))
        else:
            results.append(PreconditionResult(precondition, True, detail))
    watermark = run_watermark(manifest)
    notes = ()
    if watermark is not None:
        notes = (
            "WATERMARKED, NOT REFUSED: the run's computed origin is "
            f"{manifest.data_origin} — building on fixtures is legitimate, publishing "
            "from them is not. The watermark derives from the origin (P2.0d-3), it is "
            "not a flag, and it does not gate eligibility.",
        )
    return ClaimVerdict(
        design=design,
        results=tuple(results),
        watermark=watermark,
        data_origin=manifest.data_origin,
        notes=notes,
    )


def require_validated_claim(
    manifest: RunManifest,
    *,
    design: str,
    feature_stack_manifest: Mapping | None = None,
    contract: dict | None = None,
) -> ClaimVerdict:
    """The guard. Returns the verdict when every precondition holds; otherwise
    raises naming EVERY failing precondition, each with its own message.

    A watermarked run that satisfies all six is ELIGIBLE and returns — the
    watermark rides on the verdict (`is_scientific` is False) rather than
    blocking it."""
    verdict = evaluate_claim(
        manifest, design=design, feature_stack_manifest=feature_stack_manifest, contract=contract
    )
    if verdict.eligible:
        return verdict
    failures = verdict.failures
    assert failures, "eligible is derived from failures; an empty-failure refusal is unrepresentable"
    detail = "\n".join(f"  - [{r.precondition.value}] {r.detail}" for r in failures)
    raise ClaimRefused(
        failures[0].precondition,
        f"REFUSING to emit run {manifest.run_id!r} (design {design!r}) as a validated "
        f"claim: {len(failures)} of {len(verdict.results)} preconditions failed.\n{detail}",
    )
