"""E1.5 gap fills: corpus-level invariants, three-way evidence-class
agreement, and reachability.

WHY THIS FILE EXISTS SEPARATELY from test_observation_schema.py: that module
reads the corpus through `Observation(**row)`, and `Observation` is the very
thing that enforces the COVER/GRID rules. A violating row on disk makes the
LOADER raise, so the assertions there can never actually observe a violation —
they assert a property construction already guaranteed. The checks here read
the CSV as RAW STRINGS with no Pydantic in the path, so they can see a
violation that some future non-pipeline writer put on disk.

The distinction that matters:
  unit tests  -> the rule is implemented correctly
  these tests -> nothing downstream reintroduced the violation
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from engine.prospectivity.domain.evidence import EvidenceClass
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion.corpus_builder import REAL_ADAPTER_BUILDERS
from engine.prospectivity.ingestion.normalizer_registry import build_default_registry

REPO_ROOT = Path(__file__).resolve().parent.parent
MASTER_CORPUS_CSV = REPO_ROOT / "data" / "corpus" / "master_observations.csv"
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "master_observations.schema.json"
SOURCE_QUEUE_PATH = REPO_ROOT / "data" / "sources" / "source_queue.yaml"


def _raw_corpus_rows() -> list[dict]:
    """The corpus as strings/NaN, exactly as it sits on disk. No Observation,
    no validation, no coercion — that is the whole point."""
    frame = pd.read_csv(MASTER_CORPUS_CSV, dtype=str, keep_default_na=True)
    return frame.to_dict(orient="records")


def _schema_evidence_class_enum() -> set[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    field = next(f for f in schema["fields"] if f["name"] == "evidence_class")
    return set(field["constraints"]["enum"])


def _is_blank(value) -> bool:
    return value is None or pd.isna(value) or str(value).strip() == ""


# --- corpus-level invariants, read raw ---------------------------------------


def test_raw_corpus_every_row_has_exactly_one_in_enum_evidence_class() -> None:
    """"Exactly one" checked as: the column exists once, every row's value is
    non-blank, and every value is drawn from the SCHEMA's enum (not the code
    enum — the schema is the contract)."""
    frame = pd.read_csv(MASTER_CORPUS_CSV, dtype=str)
    assert list(frame.columns).count("evidence_class") == 1

    allowed = _schema_evidence_class_enum()
    rows = _raw_corpus_rows()
    assert rows, "corpus is empty — nothing was checked"
    for index, row in enumerate(rows):
        value = row["evidence_class"]
        assert not _is_blank(value), f"row {index} has no evidence_class"
        assert value in allowed, f"row {index} has out-of-enum evidence_class {value!r}"


def test_raw_corpus_no_cover_row_carries_an_abundance_value() -> None:
    """The hard rule (CLAUDE.md: COVER is NEVER converted to kg/m²), asserted
    against the bytes on disk rather than through the model that forbids it."""
    cover_rows = [r for r in _raw_corpus_rows() if r["evidence_class"] == "COVER"]
    assert cover_rows, "no COVER rows in the corpus — this test checked nothing"
    for row in cover_rows:
        assert _is_blank(row["abundance_kg_m2"]), (
            f"COVER row {row['source_record_id']} carries "
            f"abundance_kg_m2={row['abundance_kg_m2']!r}"
        )


def test_raw_corpus_no_grid_row_is_marked_observed() -> None:
    """GRID is a prior/benchmark, never an observed station. Skips while the
    corpus has no GRID rows ([18] awaits real TS-6 data, P1b) rather than
    passing vacuously — and re-activates automatically when [18] is wired."""
    grid_rows = [r for r in _raw_corpus_rows() if r["evidence_class"] == "GRID"]
    if not grid_rows:
        pytest.skip("no GRID rows in the corpus today (P1b: [18] awaits real TS-6 data)")
    for row in grid_rows:
        assert row["observation_or_prediction"] != "observed"


def test_raw_corpus_count_rows_carry_abundance_only_with_a_recorded_mean_mass() -> None:
    """COUNT -> kg/m² only via a recorded mean_nodule_mass_g, checked on disk."""
    for row in _raw_corpus_rows():
        if row["evidence_class"] == "COUNT" and not _is_blank(row["abundance_kg_m2"]):
            assert not _is_blank(row["mean_nodule_mass_g"]), (
                f"COUNT row {row['source_record_id']} has an abundance with no "
                "mean_nodule_mass_g to justify it"
            )


# --- three-way evidence-class agreement -------------------------------------


def test_schema_enum_code_enum_and_registered_normalizers_name_the_same_classes() -> None:
    """Registry completeness already ties the CODE enum to the registry. This
    ties in the third party — the SCHEMA's own enum — so adding a class to the
    contract without a normalizer (or vice versa) fails loudly instead of
    silently passing through unnormalized."""
    schema_classes = _schema_evidence_class_enum()
    code_classes = {member.value for member in EvidenceClass}
    registered_classes = {member.value for member in build_default_registry().registered_classes()}

    assert schema_classes == code_classes, (
        f"schema enum and EvidenceClass disagree: "
        f"schema-only={schema_classes - code_classes}, code-only={code_classes - schema_classes}"
    )
    assert code_classes == registered_classes, (
        f"EvidenceClass and registered normalizers disagree: "
        f"unregistered={code_classes - registered_classes}"
    )
    assert schema_classes == registered_classes  # transitive, asserted anyway


def test_observation_rejects_a_blank_or_out_of_enum_evidence_class() -> None:
    """"Not zero, not out-of-enum" enforced at the type, not just in the CSV."""
    base = dict(
        source_record_id="src_test_X_000001",
        source_id="src_test",
        latitude=11.9,
        longitude=-117.0,
        observation_or_prediction="observed",
        is_open=True,
        qa_status="pending",
    )
    with pytest.raises(Exception):  # missing entirely
        Observation(**base)
    with pytest.raises(Exception):
        Observation(**base, evidence_class=None)
    with pytest.raises(Exception):
        Observation(**base, evidence_class="ABUNDANCE")  # plausible but not in the enum


# --- reachability: registered != produced -----------------------------------

# A class with a normalizer but no adapter producing it is dead code that
# LOOKS covered. Each entry here is a deliberate, stated absence — if one
# becomes reachable (or a reachable class stops being produced), this fails and
# the expectation has to be updated on purpose.
DELIBERATELY_UNREACHABLE = {
    "GRID": "[18] src_ts6_grid unwired (P1b) until Track G delivers real TS-6 digitization",
    "GRADE": "[19] src_washburn2021_grid never wired; the GRADE join_tolerance_km is unresolved geology input",
}


def _classes_produced_by_wired_adapters() -> dict[str, set[str]]:
    produced: dict[str, set[str]] = {}
    for build_adapter in REAL_ADAPTER_BUILDERS:
        adapter = build_adapter()
        records = adapter.adapt(adapter.fetch())
        produced[adapter.source_id] = {str(record["evidence_class"]) for record in records}
    return produced


def test_every_evidence_class_is_either_produced_by_a_wired_adapter_or_declared_unreachable() -> None:
    produced = set().union(*_classes_produced_by_wired_adapters().values())
    expected_unreachable = set(DELIBERATELY_UNREACHABLE)
    all_classes = {member.value for member in EvidenceClass}

    assert produced == all_classes - expected_unreachable, (
        f"reachability changed: produced={sorted(produced)}, "
        f"expected={sorted(all_classes - expected_unreachable)}"
    )
    # And every unreachable class must still be registered — unreachable is a
    # wiring fact, not permission to leave it unnormalized.
    registered = {member.value for member in build_default_registry().registered_classes()}
    assert expected_unreachable <= registered


def test_each_wired_adapter_produces_exactly_the_classes_its_source_queue_entry_declares() -> None:
    """The fan-out contract: [01] -> MASS+COUNT+COVER, [05] -> MASS+COUNT, per
    source_queue.yaml's own `evidence_classes` list. Catches an adapter whose
    column map silently drops (or invents) an evidence class relative to what
    the contract says that source carries."""
    queue = yaml.safe_load(SOURCE_QUEUE_PATH.read_text())
    declared = {entry["source_id"]: set(entry["evidence_classes"]) for entry in queue["sources"]}

    produced = _classes_produced_by_wired_adapters()
    assert produced, "no wired adapters — nothing was checked"
    for source_id, produced_classes in produced.items():
        assert source_id in declared, f"{source_id} is not in source_queue.yaml"
        assert produced_classes == declared[source_id], (
            f"{source_id} produces {sorted(produced_classes)} but its "
            f"source_queue.yaml entry declares {sorted(declared[source_id])}"
        )
