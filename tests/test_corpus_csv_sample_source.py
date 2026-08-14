"""CorpusCsvSampleSource loads the full corpus pool and the inherited gate
selects exactly the training-eligible MASS rows (E2.0-1).

Two data paths, deliberately separate:

* Real-corpus tests read `data/corpus/master_observations.csv` and check the
  counts against `manifest.json` — the manifest equality checks that CSV
  serialization did not alter eligibility (the manifest was computed from the
  in-memory corpus before serialization), while the pinned literals (108/35)
  guard the numbers themselves against a drifting rebuild.

* Constructed-row tests build `Observation`s directly and write them to a tmp
  CSV with the production serializer. Direct construction matters per the
  CLAUDE.md testing conventions: `Observation` does NOT enforce the
  eligibility gate at construction (an ineligible row is representable), so a
  gate violation is observable here — these tests do not load their data
  through the class that enforces the rule they assert. They exist because
  the real corpus cannot distinguish some claims from their negations: every
  real row is is_open=True, so only a constructed closed row can catch the
  is_open gate being dropped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.prospectivity.domain.evidence import EvidenceClass, QAStatus
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.corpus_builder import write_corpus_csv
from engine.prospectivity.samples.corpus_csv import DEFAULT_CORPUS_CSV, CorpusCsvSampleSource

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "corpus" / "manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


# --------------------------------------------------------------- real corpus


def test_default_path_is_the_committed_corpus_csv() -> None:
    assert DEFAULT_CORPUS_CSV == REPO_ROOT / "data" / "corpus" / "master_observations.csv"
    assert DEFAULT_CORPUS_CSV.is_file()


def test_load_observations_returns_the_full_pool_not_the_training_set() -> None:
    """`load_observations` is the pool hook: every row, every evidence class.
    A loader that pre-filtered would make the ABC's gate decorative."""
    observations = CorpusCsvSampleSource().load_observations()
    manifest = _manifest()

    assert len(observations) == manifest["corpus_row_count"] == 108
    by_class: dict[str, int] = {}
    for obs in observations:
        by_class[obs.evidence_class.value] = by_class.get(obs.evidence_class.value, 0) + 1
    assert by_class == manifest["rows_by_evidence_class"] == {
        "COUNT": 36,
        "COVER": 36,
        "MASS": 36,
    }


def test_training_samples_are_35_of_108_matching_the_manifest_count() -> None:
    training = CorpusCsvSampleSource().get_training_samples()
    assert len(training) == _manifest()["training_eligible_count"] == 35


def test_every_excluded_row_fails_a_named_gate_and_every_eligible_row_fails_none() -> None:
    """Per-reason accounting of the 73 exclusions — an aggregate 35-of-108
    does not prove each row was excluded for the RIGHT reason (CLAUDE.md
    testing conventions). Expected breakdown on today's corpus:
    72 non-MASS (36 COUNT + 36 COVER), 1 MASS row gated by qa_status
    (the flagged failed box core), 0 gated by missing abundance, 0 by
    is_open."""
    source = CorpusCsvSampleSource()
    pool = source.load_observations()
    training_ids = {obs.source_record_id for obs in source.get_training_samples()}

    reasons: dict[str, list[str]] = {
        "not_mass": [],
        "no_abundance": [],
        "not_open": [],
        "qa_gated": [],
    }
    for obs in pool:
        if obs.source_record_id in training_ids:
            # Eligible rows must fail no gate.
            assert obs.evidence_class == EvidenceClass.MASS, obs.source_record_id
            assert obs.abundance_kg_m2 is not None, obs.source_record_id
            assert obs.is_open, obs.source_record_id
            assert obs.qa_status not in (QAStatus.FAIL, QAStatus.FLAGGED), obs.source_record_id
            continue
        # Excluded rows must each fail at least one named gate.
        failed_any = False
        if obs.evidence_class != EvidenceClass.MASS:
            reasons["not_mass"].append(obs.source_record_id)
            failed_any = True
        else:
            if obs.abundance_kg_m2 is None:
                reasons["no_abundance"].append(obs.source_record_id)
                failed_any = True
            if not obs.is_open:
                reasons["not_open"].append(obs.source_record_id)
                failed_any = True
            if obs.qa_status in (QAStatus.FAIL, QAStatus.FLAGGED):
                reasons["qa_gated"].append(obs.source_record_id)
                failed_any = True
        assert failed_any, f"{obs.source_record_id} excluded but fails no gate"

    assert len(reasons["not_mass"]) == 72
    assert len(reasons["no_abundance"]) == 0
    assert len(reasons["not_open"]) == 0
    assert len(reasons["qa_gated"]) == 1


def test_the_failed_box_core_is_loaded_but_excluded_from_training_by_name() -> None:
    """SO268/1_12-2 ("GER Trial; failed"): flag-never-drop means the MASS row
    stays IN the pool for audit, and the flag means it never trains. Both
    halves asserted — and that it is excluded for the flag, not for a missing
    value (the RIGHT reason)."""
    source = CorpusCsvSampleSource()
    pool_mass_by_event = {
        obs.event_id: obs
        for obs in source.load_observations()
        if obs.evidence_class == EvidenceClass.MASS
    }
    failed_core = pool_mass_by_event["SO268/1_12-2"]
    assert failed_core.qa_status == QAStatus.FLAGGED
    assert failed_core.abundance_kg_m2 is not None
    assert failed_core.is_open

    training_events = {obs.event_id for obs in source.get_training_samples()}
    assert "SO268/1_12-2" not in training_events


# ------------------------------------------------------------ constructed rows


def _observation(**overrides: object) -> Observation:
    fields = dict(
        source_record_id="src_test_MASS_000001",
        source_id="src_test",
        evidence_class="MASS",
        latitude=11.9,
        longitude=-117.0,
        abundance_kg_m2=14.6,
        observation_or_prediction="observed",
        is_open=True,
        qa_status="pending",
    )
    fields.update(overrides)
    return Observation(**fields)


def _source_over(tmp_path: Path, rows: list[Observation]) -> CorpusCsvSampleSource:
    csv_path = tmp_path / "corpus.csv"
    write_corpus_csv(rows, csv_path)
    return CorpusCsvSampleSource(csv_path)


def test_a_barren_zero_abundance_station_survives_the_round_trip_as_eligible(
    tmp_path: Path,
) -> None:
    """abundance_kg_m2 == 0.0 is a VALID barren measurement, not missing.
    The falsy-zero bug E1.2 found in MassNormalizer would drop exactly these
    rows here, silently biasing the model high — so the assertion checks the
    row is present AND its value is exactly 0.0 (not None, not NaN) after the
    CSV round trip."""
    barren = _observation(source_record_id="src_test_MASS_barren01", abundance_kg_m2=0.0)
    control = _observation(source_record_id="src_test_MASS_control1", abundance_kg_m2=14.6)

    training = _source_over(tmp_path, [barren, control]).get_training_samples()

    by_id = {obs.source_record_id: obs for obs in training}
    assert set(by_id) == {"src_test_MASS_barren01", "src_test_MASS_control1"}
    assert by_id["src_test_MASS_barren01"].abundance_kg_m2 == 0.0


def test_a_closed_mass_row_is_excluded_by_the_is_open_gate(tmp_path: Path) -> None:
    """The one gate the real corpus cannot exercise: all 108 real rows are
    is_open=True, so without this constructed row, dropping the is_open
    condition would leave the whole suite green."""
    closed = _observation(source_record_id="src_test_MASS_closed01", is_open=False)
    control = _observation(source_record_id="src_test_MASS_control1")

    training = _source_over(tmp_path, [closed, control]).get_training_samples()

    assert {obs.source_record_id for obs in training} == {"src_test_MASS_control1"}


def test_flagged_and_fail_mass_rows_are_excluded_through_the_csv_path(tmp_path: Path) -> None:
    flagged = _observation(source_record_id="src_test_MASS_flagged1", qa_status="flagged")
    failed = _observation(source_record_id="src_test_MASS_fail0001", qa_status="fail")
    control = _observation(source_record_id="src_test_MASS_control1")

    training = _source_over(tmp_path, [flagged, failed, control]).get_training_samples()

    assert {obs.source_record_id for obs in training} == {"src_test_MASS_control1"}


def test_count_and_cover_rows_never_train_even_when_count_carries_abundance(
    tmp_path: Path,
) -> None:
    """COUNT may legally carry abundance_kg_m2 (via a recorded
    mean_nodule_mass_g), which is precisely why the gate must key on
    evidence_class and not on 'has an abundance'. COVER carries none by
    contract. Neither may train; the MASS control proves the fixture can
    tell inclusion from exclusion."""
    count_row = _observation(
        source_record_id="src_test_COUNT_000001",
        evidence_class="COUNT",
        abundance_kg_m2=13.5,
        nodule_count=117,
        nodule_density_m2=468.0,
        mean_nodule_mass_g=28.9,
    )
    cover_row = _observation(
        source_record_id="src_test_COVER_000001",
        evidence_class="COVER",
        abundance_kg_m2=None,
        visible_cover_percent=30.0,
    )
    control = _observation(source_record_id="src_test_MASS_control1")

    training = _source_over(tmp_path, [count_row, cover_row, control]).get_training_samples()

    assert {obs.source_record_id for obs in training} == {"src_test_MASS_control1"}


def test_a_missing_corpus_csv_raises_rather_than_returning_an_empty_pool(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        CorpusCsvSampleSource(tmp_path / "absent.csv").load_observations()
