"""E0.5 CI centerpiece: ingest synthetic sources -> corpus -> assert evidence
tagging survives the full fetch/adapt/normalize/validate/dedup/append
sequence (IngestionPipeline.run(), Template Method).

WHAT THESE TESTS CAN AND CANNOT SEE (renamed 2026-07-30, test-name audit).
The `synthetic_corpus` fixture builds its rows through `Observation(**record)`,
and `Observation` itself enforces the COVER / GRID / COUNT evidence-class rules
at construction (domain/observation.py::_enforce_evidence_class_discipline). So
a violation cannot reach these assertions — it raises during fixture setup
instead. What they genuinely prove is that the pipeline's output SATISFIES that
discipline end to end (i.e. the pipeline produces rows the domain type accepts,
and the expected classes are present), not that the rule is independently
upheld.

For checks that CAN observe a violation, see `test_corpus_invariants.py`: it
reads `data/corpus/master_observations.csv` as raw strings with no Pydantic in
the path, so a row written by anything that bypasses `Observation` is visible.
"""

from __future__ import annotations

import pytest

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation
from tests.conftest import NORMALIZERS


def test_synthetic_sources_ingest_into_a_tagged_corpus(synthetic_corpus: list[Observation]) -> None:
    assert len(synthetic_corpus) > 0
    assert all(obs.evidence_class in EvidenceClass for obs in synthetic_corpus)


def test_corpus_contains_every_evidence_class_the_fixtures_produce(
    synthetic_corpus: list[Observation],
) -> None:
    classes_present = {obs.evidence_class for obs in synthetic_corpus}
    assert classes_present == {
        EvidenceClass.MASS,
        EvidenceClass.COUNT,
        EvidenceClass.COVER,
        EvidenceClass.GRID,
    }


def test_pipeline_cover_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    cover_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COVER]
    assert cover_rows
    assert all(o.abundance_kg_m2 is None for o in cover_rows)


def test_pipeline_grid_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    grid_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.GRID]
    assert grid_rows
    assert all(
        o.observation_or_prediction != ObservationOrPrediction.OBSERVED for o in grid_rows
    )


def test_pipeline_count_output_satisfies_evidence_class_discipline(
    synthetic_corpus: list[Observation],
) -> None:
    count_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.COUNT]
    assert count_rows
    for obs in count_rows:
        if obs.abundance_kg_m2 is not None:
            assert obs.mean_nodule_mass_g is not None


def test_synthetic_fixture_mass_rows_all_qualify_for_training(
    synthetic_corpus: list[Observation],
) -> None:
    """A property of THIS FIXTURE, not a general rule (renamed 2026-07-30).
    The old name, `test_mass_rows_are_training_eligible`, stated a rule that is
    false since P1 — a MASS row with qa_status fail/flagged is NOT
    training-eligible — and contradicted `test_sample_source.py`'s
    `test_flagged_row_is_excluded_from_training`, which asserts exactly that.
    """
    mass_rows = [o for o in synthetic_corpus if o.evidence_class == EvidenceClass.MASS]
    assert mass_rows
    assert all(o.is_training_eligible() for o in mass_rows)


# --- Resolution dispatch exhaustiveness (2026-07-30) ------------------------
#
# Mirrors NormalizerRegistry.assert_complete's guarantee, for the other closed
# set in the ingestion layer. `_dedup` decides what happens to every candidate
# by matching on the Resolution variant; a variant added without a branch would
# fall through and drop the row silently. This drives EVERY concrete Resolution
# subclass through the real dispatch, so the failure happens in CI rather than
# in a corpus.

import dataclasses

from engine.prospectivity.ingestion.dedup_rules import DuplicateResolutionPolicy
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.resolution import Resolution
from engine.prospectivity.ingestion.source_adapter import SourceAdapter


def _concrete_resolution_types() -> list[type]:
    """Every public Resolution subclass, however deeply nested.

    Discovered by reflection rather than listed, so a new variant is picked up
    the moment it is defined — a hand-maintained list would be one more thing
    to forget, which is the failure this test exists to prevent. Names starting
    with `_` are shared bases (e.g. `_MergeOutcome`), not decisions."""
    found: list[type] = []
    stack: list[type] = [Resolution]
    while stack:
        for subclass in stack.pop().__subclasses__():
            stack.append(subclass)
            if not subclass.__name__.startswith("_"):
                found.append(subclass)
    return found


def _instantiate(resolution_type: type, observation: Observation) -> Resolution:
    """Build a minimal instance of any Resolution variant, including one this
    test has never heard of: required Observation-typed fields get the sample
    row, everything else takes its default."""
    kwargs = {}
    for field in dataclasses.fields(resolution_type):
        has_default = (
            field.default is not dataclasses.MISSING
            or field.default_factory is not dataclasses.MISSING  # type: ignore[misc]
        )
        if has_default:
            continue
        annotation = field.type if isinstance(field.type, str) else getattr(field.type, "__name__", "")
        kwargs[field.name] = observation if "Observation" in annotation else None
    return resolution_type(**kwargs)


class _FixedResolutionPolicy(DuplicateResolutionPolicy):
    """Returns one pre-built Resolution, so the dispatch can be driven with a
    variant the real policy would never produce."""

    def __init__(self, resolution: Resolution) -> None:
        self._resolution = resolution

    def resolve(self, candidate: Observation) -> Resolution:
        return self._resolution


class _NoRowsAdapter(SourceAdapter):
    source_id = "src_test"

    def fetch(self) -> list[dict]:
        return []

    def adapt(self, raw_records: list[dict]) -> list[dict]:
        return []


def _observation() -> Observation:
    return Observation(
        source_record_id="src_test_MASS_000001",
        source_id="src_test",
        evidence_class=EvidenceClass.MASS,
        latitude=11.9,
        longitude=-117.0,
        abundance_kg_m2=14.6,
        observation_or_prediction=ObservationOrPrediction.OBSERVED,
        is_open=True,
        qa_status="pending",
    )


def test_every_resolution_variant_has_a_dispatch_branch() -> None:
    """Completeness: `_dedup` must handle every Resolution variant explicitly.

    A variant with no branch hits the `case _` guard and raises — which is what
    this asserts does NOT happen for any variant that exists today. Verified by
    mutation (2026-07-30): defining a throwaway Resolution subclass makes this
    test fail with that guard's TypeError."""
    variants = _concrete_resolution_types()
    assert variants, "no Resolution variants discovered — this test checked nothing"

    # DRIVE FIRST, deliberately: this exercises the real dispatch, so an
    # unhandled variant fails with that dispatch's own message naming it
    # ("no branch for Quarantine") rather than a set-difference. The name
    # check below is the secondary tripwire.
    for resolution_type in variants:
        observation = _observation()
        corpus = [observation]  # so AbsorbInto/Replace can locate `existing`
        pipeline = IngestionPipeline(
            adapter=_NoRowsAdapter(),
            normalizers=NORMALIZERS,
            corpus=corpus,
            dedup_policy=_FixedResolutionPolicy(_instantiate(resolution_type, observation)),
        )
        # Must not raise: every variant is dispatched explicitly.
        pipeline._dedup([observation])

    # Secondary: a new variant should also be a deliberate decision, not an
    # accident that happens to be handled.
    assert {v.__name__ for v in variants} == {
        "Admit",
        "AlreadyPresent",
        "AbsorbInto",
        "Replace",
    }


def test_an_unhandled_resolution_variant_fails_loudly() -> None:
    """The guard itself: a Resolution the dispatch does not know must raise,
    not silently drop the row."""

    @dataclasses.dataclass(frozen=True)
    class _UnknownResolution(Resolution):
        candidate: Observation

    observation = _observation()
    pipeline = IngestionPipeline(
        adapter=_NoRowsAdapter(),
        normalizers=NORMALIZERS,
        corpus=[observation],
        dedup_policy=_FixedResolutionPolicy(_UnknownResolution(candidate=observation)),
    )
    with pytest.raises(TypeError, match="no branch for _UnknownResolution"):
        pipeline._dedup([observation])
