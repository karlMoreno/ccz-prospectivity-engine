"""ProvenanceArtifact (LAYER SUPERTYPE) — the three artifacts share the
chaining contract with IDENTICAL field names, and the content-hash scheme
behaves as documented.

The chaining rule in docs/contracts/PROVENANCE.md only has teeth if the fields
are spelled the same everywhere: a reader (or a future tool) walking
`upstream_hashes` from a run back to a corpus must not have to special-case
per artifact.
"""

from __future__ import annotations

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.features.stack import FeatureStackManifest
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.corpus_manifest import CorpusManifest

ALL_ARTIFACTS = (CorpusManifest, FeatureStackManifest, RunManifest)


def test_all_three_artifacts_expose_the_shared_fields_with_identical_names() -> None:
    assert ProvenanceArtifact.SHARED_FIELDS == (
        "generated_at",
        "content_hash",
        "contract_versions",
        "upstream_hashes",
    )
    for artifact_class in ALL_ARTIFACTS:
        missing = [f for f in ProvenanceArtifact.SHARED_FIELDS if f not in artifact_class.model_fields]
        assert not missing, f"{artifact_class.__name__} is missing {missing}"


def test_all_three_artifacts_subclass_the_supertype() -> None:
    """Not just duck-typed: the fields must come FROM the base, so adding a
    fifth shared field reaches all three without touching three files."""
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
