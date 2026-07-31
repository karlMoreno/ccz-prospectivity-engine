"""Resolution — the decision a DuplicateResolutionPolicy returns.

A small closed set of value objects naming WHAT SHOULD HAPPEN to one
candidate. The policy computes a Resolution and mutates nothing;
`IngestionPipeline._dedup` applies it. That split is the point of the C2
refactor (2026-07-30, docs/PATTERNS.md §3.0): before it, the decision and its
side effects were the same call, hidden behind a method named
`is_satisfied_by` returning a bare `bool`.

    Admit           nothing matched — append the candidate
    AlreadyPresent  this exact record is already in the corpus — do nothing
    AbsorbInto      a better/equal row holds the slot — write `merged` there,
                    do not append the candidate
    Replace         the candidate outranks the row in the slot — write
                    `merged` there, do not append the candidate

AbsorbInto and Replace both end with `merged` in the slot; they differ in
WHOSE row won, which is exactly what the provenance recorder needs in order
to attribute rows without inferring them from the finished corpus.

`AlreadyPresent` is a fourth variant beyond the three named in the C2 brief,
and it earns its place: an adapter re-run offers rows that are already in the
corpus, and calling that "absorbed" is what made the event stream
order-dependent in the first place. It is a distinct decision — "no change" —
and recording it as such is what lets the recorder stop inferring.

Every field a resolution carries is a fact the policy already computed, so
nothing downstream needs to recompute or guess: `donated_fields` (D1
gap-fill), `note` (the D4 provenance link, or None when it was already
recorded), and `escalated_status` (the sticky QA verdict, 2026-07-30 —
carried EXPLICITLY rather than left as a side effect of applying the merge).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.prospectivity.domain.evidence import QAStatus
from engine.prospectivity.domain.observation import Observation


@dataclass(frozen=True)
class Resolution:
    """Base for the closed set below. Not abstract on purpose — the variants
    carry no shared behavior, only a shared role."""


@dataclass(frozen=True)
class Admit(Resolution):
    """No duplicate found. The pipeline appends the candidate unchanged."""

    candidate: Observation


@dataclass(frozen=True)
class AlreadyPresent(Resolution):
    """The candidate IS the corpus row (same source_id + source_record_id) —
    an adapter re-run offering what it already produced. Nothing to merge,
    nothing to append, nothing to record as a disposition."""

    candidate: Observation
    existing: Observation


@dataclass(frozen=True)
class _MergeOutcome(Resolution):
    """Shared shape of the two merging outcomes."""

    candidate: Observation
    existing: Observation  # the corpus row whose slot is written
    merged: Observation  # what that slot must hold afterwards
    donated_fields: tuple[str, ...] = ()
    note: str | None = None  # None => the link was already recorded
    escalated_status: QAStatus | None = None


@dataclass(frozen=True)
class AbsorbInto(_MergeOutcome):
    """`existing` won the slot (higher or equal quality_grade; ties go to
    first-encountered). The candidate's non-null fields may have been donated
    into it, and its provenance recorded."""


@dataclass(frozen=True)
class Replace(_MergeOutcome):
    """The candidate outranked `existing` on quality_grade, so the merged row
    is built on the CANDIDATE and written into the existing row's slot. The
    displaced row's source loses a row in the corpus — which is precisely the
    attribution the recorder previously had to infer."""
