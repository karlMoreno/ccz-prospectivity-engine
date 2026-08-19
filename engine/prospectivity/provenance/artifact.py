"""ProvenanceArtifact — LAYER SUPERTYPE (Fowler, PoEAA).

One common superclass for every provenance artifact the engine emits, so the
four facts that make artifacts *chainable* are declared once, with identical
field names, instead of being re-invented per stage:

    generated_at       when this artifact was produced
    content_hash       this artifact's OWN identity hash (see below)
    contract_versions  which frozen contracts were in effect
    upstream_hashes    the content_hash of every artifact this one consumed

Why a supertype and not one merged manifest (docs/contracts/PROVENANCE.md):
the four artifacts cover four different stages with four different
lifetimes — a corpus outlives many feature stacks, a feature stack outlives
many training matrices, a matrix may outlive the run it feeds. Merging them
would force a rebuild of everything to record anything. Sharing a supertype
instead gives the chaining rule teeth: because `upstream_hashes` is spelled
the same everywhere, a prediction traces to exactly one matrix, one feature
stack, and one corpus by mechanical lookup, not by convention.

    ┌──────────────────────────────────────────────┐
    │           ProvenanceArtifact (base)            │
    │  generated_at · content_hash                   │
    │  contract_versions · upstream_hashes           │
    │  .finalize() -> sets content_hash              │
    └──────────────────────────────────────────────┘
         ▲              ▲                ▲                ▲
    CorpusManifest  FeatureStack-  TrainingMatrix-   RunManifest
    (ingestion)     Manifest       Manifest           (model run)
                    (E1.4)         (E2.0-3)
         ▲              ▲                │
         └──────────────┴───upstream─────┘
           (corpus + feature_stack hashes)

CONTENT HASH SCHEME — deliberately excludes `content_hash` (self-reference is
impossible) AND `generated_at` (a wall-clock timestamp would make the hash
differ between two otherwise identical builds, which would destroy the one
property the hash exists to provide). So `content_hash` is a hash of the
artifact's SUBSTANCE: same inputs and same decisions produce the same hash on
any machine, at any time. That is what makes it usable as an upstream
reference and as a reproducibility check (CLAUDE.md: "same inputs + seed ->
same outputs").

E2.4 §2D: the exclusion set is a CLASS attribute (`HASH_EXCLUDED_FIELDS`)
that a subclass may EXTEND — RunManifest adds `scores_first_visible`, the one
deliberate exception to "no wall-clock in the substance" (BACKLOG §2, the
pre-registration clock): a date that IS the fact being recorded, kept out of
the hash so identical runs hash identically across days, and therefore
MUTABLE METADATA whose authoritative witness is the commit, not the JSON.
A subclass can only ADD exclusions, never remove the two above.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

# Fields excluded from the content hash, and why — see the module docstring.
_HASH_EXCLUDED_FIELDS = frozenset({"content_hash", "generated_at"})


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ProvenanceArtifact(BaseModel):
    """Base for every emitted provenance artifact. Subclasses add their own
    stage-specific fields; these four are the shared, identically-named
    chaining contract."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime = Field(default_factory=_utc_now)
    content_hash: str | None = None
    contract_versions: dict[str, str | int | None] = Field(default_factory=dict)
    upstream_hashes: dict[str, str | None] = Field(default_factory=dict)

    # The shared field names, asserted identical across all three artifacts by
    # tests/test_provenance_artifact.py. Named here rather than duplicated in
    # the test so the test can't drift from the base.
    SHARED_FIELDS: ClassVar[tuple[str, ...]] = (
        "generated_at",
        "content_hash",
        "contract_versions",
        "upstream_hashes",
    )

    # Fields outside the content hash. Subclasses may EXTEND (RunManifest adds
    # scores_first_visible); the two base exclusions are always kept — see
    # `hash_excluded_fields()`.
    HASH_EXCLUDED_FIELDS: ClassVar[frozenset[str]] = _HASH_EXCLUDED_FIELDS

    @classmethod
    def hash_excluded_fields(cls) -> frozenset[str]:
        """The effective exclusion set: the subclass's declaration UNION the
        two base exclusions, so a subclass cannot pull generated_at or
        content_hash back INTO its own hash by overriding the attribute."""
        return frozenset(cls.HASH_EXCLUDED_FIELDS) | _HASH_EXCLUDED_FIELDS

    def substance(self) -> dict:
        """The artifact's hashable substance: everything except the excluded
        fields, JSON-normalized with sorted keys so ordering is never
        machine- or dict-dependent."""
        payload = self.model_dump(mode="json", exclude=set(type(self).hash_excluded_fields()))
        return payload

    def compute_content_hash(self) -> str:
        canonical = json.dumps(self.substance(), sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def finalize(self) -> "ProvenanceArtifact":
        """Stamp `content_hash` from the current substance. Call once, after
        every other field is populated — a downstream artifact quoting this
        one's hash must be quoting the finished thing."""
        self.content_hash = self.compute_content_hash()
        return self

    def to_json(self) -> str:
        """Canonical serialization for writing to disk: sorted keys, trailing
        newline, no machine-dependent ordering."""
        return json.dumps(self.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
