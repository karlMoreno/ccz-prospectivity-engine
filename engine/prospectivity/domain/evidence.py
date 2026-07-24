"""Evidence-class vocabulary (Contract 1 / CLAUDE.md "Evidence classes are sacred").

Every observation in the master corpus carries exactly one of these five tags.
Nothing downstream (SampleSource, AbundanceNormalizer, estimators) is allowed
to treat two classes as interchangeable — see normalization.yaml (Contract 7)
for the per-class conversion rules this enum gates.
"""

from __future__ import annotations

from enum import Enum


class EvidenceClass(str, Enum):
    """The kind of evidence a corpus row represents.

    MASS  kg/m2          -> the ONLY class the model trains on.
    COUNT nodules/m2      -> covariate; -> kg/m2 ONLY via a recorded mean nodule mass.
    COVER percent cover   -> covariate; NEVER converted to kg/m2.
    GRID  compiled/interp -> prior + TS-6 benchmark; NEVER an independent station.
    GRADE Mn/Ni/Cu/Co     -> joins to abundance stations; feeds metals + economics.
    """

    MASS = "MASS"
    COUNT = "COUNT"
    COVER = "COVER"
    GRID = "GRID"
    GRADE = "GRADE"


class ObservationOrPrediction(str, Enum):
    """Whether a row is a real sample or a compiled/modelled value (Contract 1)."""

    OBSERVED = "observed"
    COMPILED = "compiled"
    INTERPOLATED = "interpolated"
    MODELLED = "modelled"


class SampleMethod(str, Enum):
    BOX_CORER = "box_corer"
    GRAB_SAMPLER = "grab_sampler"
    FREE_FALL_GRAB = "free_fall_grab"
    DREDGE = "dredge"
    IMAGE = "image"
    AUV = "auv"
    OFOS = "ofos"
    CHAMBER = "chamber"
    COMPILED = "compiled"
    OTHER = "other"


class AbundanceBasis(str, Enum):
    WET = "wet"
    DRY = "dry"
    UNKNOWN = "unknown"


class QualityGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class QAStatus(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    FLAGGED = "flagged"
