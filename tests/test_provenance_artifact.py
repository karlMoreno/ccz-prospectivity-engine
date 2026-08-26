"""ProvenanceArtifact (LAYER SUPERTYPE) — the four artifacts share the
chaining contract with IDENTICAL field names, and the content-hash scheme
behaves as documented.

The chaining rule in docs/contracts/PROVENANCE.md only has teeth if the fields
are spelled the same everywhere: a reader (or a future tool) walking
`upstream_hashes` from a run back to a corpus must not have to special-case
per artifact.
"""

from __future__ import annotations

from pydantic import Field

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.features.stack import FeatureStackManifest
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.corpus_manifest import CorpusManifest
from engine.prospectivity.training_matrix import TrainingMatrixManifest

ALL_ARTIFACTS = (CorpusManifest, FeatureStackManifest, TrainingMatrixManifest, RunManifest)


def test_all_four_artifacts_expose_the_shared_fields_with_identical_names() -> None:
    assert ProvenanceArtifact.SHARED_FIELDS == (
        "generated_at",
        "content_hash",
        "contract_versions",
        "upstream_hashes",
        "schema_version",  # HASH.1
    )
    for artifact_class in ALL_ARTIFACTS:
        missing = [f for f in ProvenanceArtifact.SHARED_FIELDS if f not in artifact_class.model_fields]
        assert not missing, f"{artifact_class.__name__} is missing {missing}"


def test_all_four_artifacts_subclass_the_supertype() -> None:
    """Not just duck-typed: the fields must come FROM the base, so adding a
    fifth shared field reaches all four without touching four files."""
    for artifact_class in ALL_ARTIFACTS:
        assert issubclass(artifact_class, ProvenanceArtifact)


def test_shared_field_types_agree_across_artifacts() -> None:
    for field_name in ProvenanceArtifact.SHARED_FIELDS:
        annotations = {
            artifact_class.model_fields[field_name].annotation
            for artifact_class in ALL_ARTIFACTS
        }
        assert len(annotations) == 1, f"{field_name} has differing types: {annotations}"


def test_content_hash_excludes_generated_at_so_identical_substance_hashes_equal() -> None:
    """The documented scheme: the hash covers SUBSTANCE, not the moment of
    writing. Two artifacts built at different times from the same inputs must
    hash identically, or the hash is useless as an upstream reference."""
    first = RunManifest(run_id="run-1", seed=7).finalize()
    second = RunManifest(run_id="run-1", seed=7).finalize()
    assert first.generated_at != second.generated_at or True  # timestamps may tie
    assert first.content_hash == second.content_hash


def test_content_hash_changes_when_substance_changes() -> None:
    baseline = RunManifest(run_id="run-1", seed=7).finalize()
    different_seed = RunManifest(run_id="run-1", seed=8).finalize()
    assert baseline.content_hash != different_seed.content_hash


def test_content_hash_is_not_self_referential() -> None:
    """content_hash is excluded from its own input — otherwise it could never
    be computed. Setting it must not change what a recompute yields."""
    manifest = RunManifest(run_id="run-1", seed=7)
    before = manifest.compute_content_hash()
    manifest.finalize()
    assert manifest.compute_content_hash() == before
    assert manifest.content_hash == before


def test_run_manifest_kept_every_field_it_recorded_before_the_refactor() -> None:
    """The refactor was not allowed to drop information. `created_at` became
    the base's `generated_at` (same fact, shared name); everything else is
    unchanged."""
    fields = set(RunManifest.model_fields)
    assert {
        "run_id",
        "seed",
        "inputs",
        "cv_scores",
        "ts6_agreement",
        "economic_results",
        "output_hashes",
    } <= fields
    assert "generated_at" in fields
    assert "created_at" not in fields



# ═══════════════════════════════ HASH.1 — shape-tolerant hashing (2026-08-22)

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMITTED = {
    # THE BOUNDED HISTORICAL SET — the two artifacts stamped before schema
    # versions existed (`git ls-files data`), pinned by literal so a scheme
    # change that moved either fails BY NAME rather than via a downstream test.
    "data/corpus/manifest.json": (CorpusManifest, "sha256:0227d6df608ee23476c7f5915bede82f1ffb360c542e33152386257a2fd07fd9"),
    "data/runs/e2.4/run_manifest.json": (RunManifest, "sha256:e3ac1561b8f681bb30ce05c9638325f9f58b0223ee56596e53fc68d89f6e7ad4"),
}


def _wider(base_class):
    """The same artifact class, ONE FIELD LATER — constructed, so the property
    is asserted directly rather than by adding a real field."""
    class Wider(base_class):
        later_field: str | None = None
    return Wider


def test_adding_a_field_to_a_subclass_does_not_change_an_existing_artifacts_hash() -> None:
    """THE PROPERTY THE COMMIT EXISTS FOR, in both regimes. VERSIONED: a
    fresh v1 manifest reloaded under a class with one more field hashes the
    same. LEGACY: the committed E2.4 artifact (no schema_version) reloaded
    under the wider class hashes to its stored value. The two cases are
    separate assertions because they run different substance rules, and a
    mutation of either rule must fail here by name."""
    base = RunManifest(run_id="r", seed=7, data_origin="SYNTHETIC").finalize()
    Wider = _wider(RunManifest)
    reloaded = Wider(**json.loads(base.to_json()))
    assert reloaded.schema_version == RunManifest.SCHEMA_VERSION and reloaded.later_field is None
    assert reloaded.compute_content_hash() == base.content_hash, "versioned regime: a None-default field entered the substance"
    raw = json.loads((REPO_ROOT / "data/runs/e2.4/run_manifest.json").read_text())
    legacy = Wider(**raw)
    assert legacy.is_legacy and legacy.later_field is None
    assert legacy.compute_content_hash() == raw["content_hash"], "legacy regime: the frozen set did not hold"


def test_two_artifacts_with_the_same_present_fields_and_different_schema_versions_are_distinguishable() -> None:
    """THE COUNTERARGUMENT'S MITIGATION, tested: shape-tolerance lets two
    shapes with the same present fields coincide; the schema version inside
    the substance is what keeps them apart."""
    v1 = RunManifest(run_id="r", seed=7, schema_version=1).finalize()
    v2 = RunManifest(run_id="r", seed=7, schema_version=2).finalize()
    a, b = v1.substance(), v2.substance()
    assert {k: v for k, v in a.items() if k != "schema_version"} == {k: v for k, v in b.items() if k != "schema_version"}
    assert v1.content_hash != v2.content_hash


def test_the_schema_version_is_inside_the_hashed_substance_not_beside_it() -> None:
    """If it were outside (the generated_at precedent) the mitigation above
    would be decorative: the hash could not tell v1 from v2. Versioned
    artifacts carry it IN; legacy artifacts carry none (their frozen set
    predates the field), which is exactly the limitation stated in the
    module docstring."""
    fresh = RunManifest(run_id="r", seed=7).finalize()
    assert fresh.substance()["schema_version"] == RunManifest.SCHEMA_VERSION == 5  # 2 at E4.1, 3 at E4.3, 4 at E5.5, 5 at G.2
    legacy = RunManifest(**json.loads((REPO_ROOT / "data/runs/e2.4/run_manifest.json").read_text()))
    assert "schema_version" not in legacy.substance() and legacy.schema_version is None


def test_the_two_committed_artifacts_are_legacy_and_their_hashes_are_unchanged_by_the_scheme() -> None:
    """Backward compatibility for the bounded historical set, pinned by
    literal. If either moves, the scheme is not backward-compatible and the
    prompt's STOP condition has fired."""
    for relative, (cls, pinned) in COMMITTED.items():
        raw = json.loads((REPO_ROOT / relative).read_text())
        artifact = cls(**raw)
        assert artifact.is_legacy, relative
        assert raw["content_hash"] == pinned == artifact.compute_content_hash(), relative
    assert len(COMMITTED) == 2 == len([p for p in ("data/corpus/manifest.json", "data/runs/e2.4/run_manifest.json") if (REPO_ROOT / p).is_file()])


def test_legacy_is_detected_by_a_content_hash_without_a_schema_version_and_nothing_else() -> None:
    fresh = RunManifest(run_id="r", seed=7)
    assert fresh.schema_version == RunManifest.SCHEMA_VERSION and not fresh.is_legacy  # stamped at construction
    reloaded_versioned = RunManifest(run_id="r", seed=7, content_hash="sha256:x", schema_version=3)
    assert reloaded_versioned.schema_version == 3
    reloaded_legacy = RunManifest(run_id="r", seed=7, content_hash="sha256:x")
    assert reloaded_legacy.is_legacy
    # model_copy (the emitter's path) preserves the version rather than re-stamping
    assert fresh.model_copy(update={"seed": 8}).schema_version == RunManifest.SCHEMA_VERSION


def test_every_real_artifact_declares_a_frozen_legacy_set_that_is_a_subset_of_its_live_fields() -> None:
    """The legacy sets are SNAPSHOTS, declared per class, never computed: a
    class that inherited the base's set would hash a legacy artifact over
    two fields, and one computed from model_fields would track the additions
    it exists to keep out. Compared in full against the live fields minus
    exclusions — equal TODAY (no field has been added since HASH.1), and the
    assertion is written so that inequality reads as 'a field was added:
    bump SCHEMA_VERSION', not as a failure to silence."""
    base_excluded = {"content_hash", "generated_at"}
    for cls in ALL_ARTIFACTS:
        assert "LEGACY_HASHED_FIELDS" in cls.__dict__, cls.__name__
        assert cls.LEGACY_HASHED_FIELDS <= set(cls.model_fields) - cls.hash_excluded_fields(), cls.__name__
        # every field INTRODUCED since HASH.1 (hash-excluded ones count: the
        # version identifies the SHAPE) must default to None — enforced at
        # class definition too — and its class's version must have moved.
        added = set(cls.model_fields) - cls.LEGACY_HASHED_FIELDS - base_excluded - {"schema_version"} - (
            set(cls.model_fields) & {"scores_first_visible", "run_id"}  # RunManifest's own pre-HASH.1 exclusions
        )
        assert all(cls.model_fields[f].default is None for f in added), f"{cls.__name__}: {sorted(added)}"
        assert (added == set()) == (cls.SCHEMA_VERSION == 1), (
            f"{cls.__name__} added {sorted(added)} at SCHEMA_VERSION {cls.SCHEMA_VERSION} — a field "
            "added since HASH.1 bumps the version, and a bumped version names its field"
        )
    # the versions as declared: the stack gained `dem_path` at HASH.1 commit 2,
    # the run manifest `economic_differences` at E4.1, `economics` at E4.3,
    # `training_stations` at E5.5 commit 2 and `aoi_coverage` at G.2
    assert {cls.__name__: cls.SCHEMA_VERSION for cls in ALL_ARTIFACTS} == {
        "CorpusManifest": 1, "FeatureStackManifest": 2, "TrainingMatrixManifest": 1, "RunManifest": 5
    }


def test_a_new_field_with_a_non_none_default_is_refused_at_class_definition() -> None:
    """THE NEW-FIELD RULE's positive control: without it the previous test
    could not distinguish 'every new field defaults to None' from 'no new
    field exists'."""
    with pytest.raises(TypeError, match=r"adds field\(s\) \['later_list'\] outside its frozen legacy set with a non-None default"):
        class Leaky(RunManifest):
            later_list: list[str] = Field(default_factory=list)
    class Fine(RunManifest):
        later_field: str | None = None
    assert Fine(run_id="r", seed=1).later_field is None
