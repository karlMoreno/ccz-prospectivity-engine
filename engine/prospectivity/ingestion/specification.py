"""Specification — SPECIFICATION.

One dedup/QA rule per class: a named predicate over an Observation, rather
than one tangled dedup function. `IngestionPipeline` depends on this interface
and nothing more, so the dedup policy is swappable (and omittable — the
pipeline's `dedup_specification` is optional).

    ┌───────────────────────────────┐
    │        Specification (ABC)      │
    │  is_satisfied_by(obs) -> bool    │
    └───────────────────────────────┘
                   ▲
      DuplicateStationSpecification (E1.3, dedup_rules.py)

NO AND/OR/NOT COMBINATORS — removed 2026-07-29 (E1.5 reverse audit), and
deliberately not coming back without a reason:

1. **Nothing composed them.** Phase 0 froze `&`/`|`/`~` on the assumption that
   the dedup rules would compose. They didn't: Contract 7's rules 4 and 5
   collapsed into a single guard (`_comparable_evidence`), rule 3 moved into an
   adapter (`NoduleAggregateAdapter`) because a many-to-one aggregation isn't a
   boolean predicate at all, and rules 1 and 2 turned out to be the same
   mechanical key-match. What shipped is ONE production Specification. The
   combinators had zero production composition sites and three tests that
   tested only themselves.

2. **The shipped Specification is STATEFUL, which makes composition unsafe.**
   `DuplicateStationSpecification.is_satisfied_by()` does not merely answer a
   question — on a match it MERGES the candidate into the corpus row and
   returns False (D1/D4). Under `a & b`, short-circuit evaluation would decide
   whether `b`'s merge happens at all; under `~a`, a False that means "already
   merged, don't append" would silently become "append this". Evaluation order
   would be load-bearing and invisible at the call site. Offering the operators
   is an invitation to a bug that would corrupt the corpus quietly.

If a genuinely stateless, genuinely composable rule appears, reintroducing
`__and__` is a few lines — cheaper than keeping a trap. Any such rule should
also be paired with an idempotency test like
`test_dedup_rules.py::test_calling_is_satisfied_by_twice_on_the_same_duplicate_is_idempotent`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.observation import Observation


class Specification(ABC):
    """A named admission rule over an Observation.

    ⚠ NOT A PURE PREDICATE, despite the name and despite the canonical pattern.
    In the textbook Specification, `is_satisfied_by` is side-effect free and
    safe to evaluate any number of times, in any order. **That is false here.**
    The one shipped implementation (`DuplicateStationSpecification`) READS the
    corpus and, on a match, MUTATES it — replacing a row in place with a merged
    survivor and appending a provenance note — then returns False to mean "do
    not also append this", not "this candidate is uninteresting".

    So a caller must treat `is_satisfied_by` as potentially side-effecting:
    call it exactly once per candidate, in a defined order.
    `IngestionPipeline._dedup` documents that contract at its own call site.

    THIS IS NOT A THEORETICAL CAUTION. Two calls to something named
    `is_satisfied_by` were assumed to be free, and that assumption produced a
    real bug (E1.5, 2026-07-29): the provenance note was re-appended on the
    second call, and on a `build_corpus()` re-run a row ended up recording
    itself as its own duplicate. Row counts stayed correct throughout, so the
    length-only idempotency test never saw it.

    REQUIREMENTS FOR ANY NEW IMPLEMENTATION:

    - If it is pure, say so in its docstring — that is the exception here, not
      the assumption, and it is worth stating.
    - If it mutates, it MUST ship with a paired idempotency test asserting that
      a second identical call changes nothing: not the corpus length, not any
      surviving field, and not `notes` (the field that actually broke — an
      append is the easiest thing to make non-idempotent and the hardest to
      notice, because every count-based assertion still passes).

    See docs/PATTERNS.md §3.1 for why the AND/OR/NOT combinators were deleted
    rather than kept: composing a mutating rule with `&`/`|` would make
    evaluation order decide how many times a merge ran, invisibly.
    """

    @abstractmethod
    def is_satisfied_by(self, observation: Observation) -> bool:
        raise NotImplementedError
