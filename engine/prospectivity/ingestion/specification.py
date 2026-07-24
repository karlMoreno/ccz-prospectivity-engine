"""Specification — SPECIFICATION.

Dedup + QA rules (AR-D04: DOMES families dedupe by cruise+station+coords+date
not DOI; individual nodules nest within box-core events; cover is never merged
with mass; ...) as small, composable, testable predicates over an Observation,
rather than one tangled dedup function. Phase 0 defines only the generic
combinators (`&`, `|`, `~`); the concrete domain rules above are Track G/E's
Phase 1 job (E1.3) once real duplicate patterns exist to encode.

    IsDuplicateOf(other) & ~IsNestedNoduleEvent()   # composable via & | ~
    ┌───────────────────────────────┐
    │        Specification (ABC)      │
    │  is_satisfied_by(obs) -> bool    │
    │  __and__, __or__, __invert__     │  <- combinators, frozen now
    └───────────────────────────────┘
       ▲                 ▲
  (Phase 1 concrete specifications: DomesFamilyDuplicate, NestedNoduleEvent, ...)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.observation import Observation


class Specification(ABC):
    """A composable boolean predicate over an Observation."""

    @abstractmethod
    def is_satisfied_by(self, observation: Observation) -> bool:
        raise NotImplementedError

    def __and__(self, other: "Specification") -> "Specification":
        return _AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "Specification":
        return _OrSpecification(self, other)

    def __invert__(self) -> "Specification":
        return _NotSpecification(self)


class _AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, observation: Observation) -> bool:
        return self._left.is_satisfied_by(observation) and self._right.is_satisfied_by(
            observation
        )


class _OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, observation: Observation) -> bool:
        return self._left.is_satisfied_by(observation) or self._right.is_satisfied_by(
            observation
        )


class _NotSpecification(Specification):
    def __init__(self, wrapped: Specification) -> None:
        self._wrapped = wrapped

    def is_satisfied_by(self, observation: Observation) -> bool:
        return not self._wrapped.is_satisfied_by(observation)
