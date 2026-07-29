"""Observation — the master-observation row (Contract 1, schema_version 4).

Field-for-field mirror of docs/contracts/master_observations.schema.json. This
is the one place the CLAUDE.md scientific-integrity rules are enforced as code
rather than as documentation:

    * COVER            -> abundance_kg_m2 must be blank (never a bare mass value)
    * GRADE             -> abundance_kg_m2 must be blank (chemistry only)
    * GRID              -> observation_or_prediction must NOT be "observed"
    * COUNT -> kg/m2    -> only valid with a recorded mean_nodule_mass_g

A row that violates one of these fails Pydantic validation at construction
time, so a bug that writes cover->mass (or similar) cannot silently enter the
corpus — it raises immediately, in ingestion and in tests alike.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from engine.prospectivity.domain.evidence import (
    AbundanceBasis,
    EvidenceClass,
    ObservationOrPrediction,
    QAStatus,
    QualityGrade,
    SampleMethod,
)

_SOURCE_RECORD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")
_SOURCE_ID_PATTERN = re.compile(r"^src_[A-Za-z0-9_\-]+$")


class Observation(BaseModel):
    """One row of the master corpus (data/corpus/master_observations.csv)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # -- identity / provenance -------------------------------------------------
    source_record_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    evidence_class: EvidenceClass

    # -- where / when -----------------------------------------------------------
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    water_depth_m: float | None = Field(default=None, ge=0, le=7000)
    cruise: str | None = None
    station_id: str | None = None
    event_id: str | None = None
    sample_datetime_utc: datetime | None = None
    sample_method: SampleMethod | None = None
    sampled_area_m2: float | None = Field(default=None, ge=0)

    # -- raw, as reported --------------------------------------------------------
    abundance_value_original: float | None = None
    abundance_unit_original: str | None = None
    abundance_basis: AbundanceBasis | None = None
    nodule_mass_kg: float | None = Field(default=None, ge=0)

    # -- normalized training value ------------------------------------------------
    # le=100, not 45: 45 is normalization.yaml's TS-6 screening ceiling, a SOFT
    # bound enforced by apply_screening()'s qa_status="flagged", not a hard
    # validation limit. Schema v4 (E1.3 review): at le=45 this field's own
    # maximum exactly matched the screening ceiling, so a value screening
    # should have flagged instead raised ValidationError first, and
    # qa_status="flagged" was never reachable for this field. Widened to
    # match the headroom mn/ni/cu/co_pct already have over their own
    # screening bounds (docs/contracts/master_observations.schema.json).
    abundance_kg_m2: float | None = Field(default=None, ge=0, le=100)

    # -- count / cover covariates --------------------------------------------------
    nodule_count: int | None = Field(default=None, ge=0)
    nodule_density_m2: float | None = Field(default=None, ge=0)
    visible_cover_percent: float | None = Field(default=None, ge=0, le=100)
    mean_nodule_mass_g: float | None = Field(default=None, ge=0)

    # -- grade (chemistry) --------------------------------------------------------
    mn_pct: float | None = Field(default=None, ge=0, le=60)
    ni_pct: float | None = Field(default=None, ge=0, le=5)
    cu_pct: float | None = Field(default=None, ge=0, le=5)
    co_pct: float | None = Field(default=None, ge=0, le=2)

    # -- provenance / QA ------------------------------------------------------------
    derivation_formula: str | None = None
    observation_or_prediction: ObservationOrPrediction
    is_open: bool
    quality_grade: QualityGrade | None = None
    duplicate_group_id: str | None = None
    qa_status: QAStatus
    notes: str | None = None

    @field_validator("source_record_id")
    @classmethod
    def _validate_source_record_id(cls, value: str) -> str:
        if not _SOURCE_RECORD_ID_PATTERN.match(value):
            raise ValueError(f"source_record_id {value!r} does not match ^[A-Za-z0-9_-]+$")
        return value

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str) -> str:
        if not _SOURCE_ID_PATTERN.match(value):
            raise ValueError(f"source_id {value!r} does not match ^src_[A-Za-z0-9_-]+$")
        return value

    @model_validator(mode="after")
    def _enforce_evidence_class_discipline(self) -> "Observation":
        if self.evidence_class == EvidenceClass.COVER and self.abundance_kg_m2 is not None:
            raise ValueError(
                "COVER row carries a bare abundance_kg_m2 — cover is a covariate, "
                "never a mass value (normalization.yaml, Contract 7)."
            )
        if self.evidence_class == EvidenceClass.GRADE and self.abundance_kg_m2 is not None:
            raise ValueError(
                "GRADE row carries abundance_kg_m2 — GRADE is chemistry-only and "
                "joins to a station, it never produces its own mass value."
            )
        if (
            self.evidence_class == EvidenceClass.GRID
            and self.observation_or_prediction == ObservationOrPrediction.OBSERVED
        ):
            raise ValueError(
                "GRID row is flagged observation_or_prediction=observed — GRID is a "
                "compiled/interpolated prior and must never look like a real station."
            )
        if (
            self.evidence_class == EvidenceClass.COUNT
            and self.abundance_kg_m2 is not None
            and self.mean_nodule_mass_g is None
        ):
            raise ValueError(
                "COUNT row has abundance_kg_m2 but no mean_nodule_mass_g — COUNT can "
                "only become kg/m2 via a recorded mean nodule mass (normalization.yaml)."
            )
        return self

    def is_training_eligible(self) -> bool:
        """The AR-P02 / SampleSource selection rule, exposed for reuse in tests.

        P1 (2026-07-27 audit follow-up): also excludes qa_status in
        (fail, flagged). D5.3 deliberately flagged the failed box core
        (SO268/1_12-2) rather than silently dropping it, so it stays in the
        corpus for audit — but "flagged, never silently dropped" only means
        something if flagged rows are actually excluded from training
        somewhere; before this, the flag had no downstream effect and the
        row was training-eligible anyway. "fail" is excluded for the same
        reason it's terminal in the E1.2 review's qa_status precedence rule
        (normalizer_registry.py's apply_screening): a stronger,
        already-adjudicated verdict that nothing downstream should launder
        back into "trainable."
        """

        return (
            self.evidence_class == EvidenceClass.MASS
            and self.abundance_kg_m2 is not None
            and self.is_open
            and self.qa_status not in (QAStatus.FAIL, QAStatus.FLAGGED)
        )
