"""Specification (SPECIFICATION pattern) AND/OR/NOT combinators compose
correctly. Concrete dedup/QA rules are Phase 1 (E1.3); this only proves the
generic machinery those rules will be built on.
"""

from __future__ import annotations

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.specification import Specification


class _EvidenceClassIs(Specification):
    def __init__(self, evidence_class: EvidenceClass) -> None:
        self._evidence_class = evidence_class

    def is_satisfied_by(self, observation: Observation) -> bool:
        return observation.evidence_class == self._evidence_class


class _IsOpen(Specification):
    def is_satisfied_by(self, observation: Observation) -> bool:
        return observation.is_open


def _make_observation(evidence_class: EvidenceClass, is_open: bool) -> Observation:
    return Observation(
        source_record_id=f"SPEC_{evidence_class.value}_{is_open}",
        source_id="src_synthetic_boxcore",
        evidence_class=evidence_class,
        longitude=-126.0,
        latitude=12.0,
        observation_or_prediction=ObservationOrPrediction.OBSERVED,
        is_open=is_open,
        qa_status="pending",
    )


def test_and_specification() -> None:
    spec = _EvidenceClassIs(EvidenceClass.MASS) & _IsOpen()
    assert spec.is_satisfied_by(_make_observation(EvidenceClass.MASS, True))
    assert not spec.is_satisfied_by(_make_observation(EvidenceClass.MASS, False))
    assert not spec.is_satisfied_by(_make_observation(EvidenceClass.COUNT, True))


def test_or_specification() -> None:
    spec = _EvidenceClassIs(EvidenceClass.MASS) | _EvidenceClassIs(EvidenceClass.COUNT)
    assert spec.is_satisfied_by(_make_observation(EvidenceClass.MASS, True))
    assert spec.is_satisfied_by(_make_observation(EvidenceClass.COUNT, True))
    assert not spec.is_satisfied_by(_make_observation(EvidenceClass.COVER, True))


def test_not_specification() -> None:
    spec = ~_IsOpen()
    assert spec.is_satisfied_by(_make_observation(EvidenceClass.MASS, False))
    assert not spec.is_satisfied_by(_make_observation(EvidenceClass.MASS, True))
