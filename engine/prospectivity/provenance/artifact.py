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

HASH.1 — SHAPE-TOLERANT HASHING (Karl's decision, 2026-08-22; built 2026-08-22).
THE PROBLEM: `substance()` dumped every field, defaults included, so adding
ANY field to a subclass re-hashed every committed artifact of that type.
E3.4 paid that once (six lines on data/runs/e2.4/run_manifest.json); the
path-hash fix would have charged it again, and so would every future field.
THE DECISION: hash over PRESENT fields; record the SCHEMA VERSION inside the
substance; leave historical artifacts with their original hashes.

    fresh artifact ──finalize()──► schema_version = SCHEMA_VERSION (stamped
                                   at construction, since content_hash is None)
                                   substance = present (non-None) fields,
                                              schema_version INCLUDED
    reloaded artifact with content_hash and NO schema_version
                               ──► LEGACY: substance = the FROZEN field set
                                   LEGACY_HASHED_FIELDS, defaults included —
                                   the pre-HASH.1 rule, so its hash never moves

THE LOSING ARGUMENT, recorded because a later reader would otherwise see
only the cost: two manifests with different SHAPES can now hash identically
when their present fields agree — the hash stops identifying the schema. It
loses because the shape is already recorded elsewhere in the artifact, and
this hash's job is identifying SUBSTANCE; recording `schema_version` inside
the substance restores what is given up explicitly (a v1 and a v2 artifact
with identical present fields hash DIFFERENTLY — tested), rather than as a
side effect of dumping defaults.

WHY A LEGACY MODE AND NOT A PLAIN present-fields RULE — measured before
building: the committed E2.4 run manifest was re-stamped at E3.4 WITH five
null fields in its substance, so `exclude_none` alone moves its hash
(sha256:e3ac1561… → sha256:b649fd96…), and `exclude_defaults` moves the
corpus manifest's too (`upstream_hashes: {}`). "Leave historical artifacts
with their original hashes" therefore requires the old rule for them, over
a field set FROZEN at HASH.1 so future fields cannot reach it.

WHAT THE DECISION DOES NOT FIX, bounded and named: artifacts written before
this landed carry no schema version, so by hash alone they cannot be
distinguished from a differently-shaped artifact. That set is TWO committed
files — data/corpus/manifest.json and data/runs/e2.4/run_manifest.json
(`git ls-files data`); stack and matrix manifests are generated fresh on
every run and are unaffected. THE E3.4 RE-STAMP STAYS: retroactively
un-stamping the run manifest would be the after-the-fact edit this decision
exists to prevent.

THE RULE FOR NEW FIELDS, enforced at class definition: a field outside the
frozen legacy set must default to None — a non-None default would enter the
present-field substance of every artifact and re-hash history by a side
door. `__pydantic_init_subclass__` refuses it by name.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Fields excluded from the content hash, and why — see the module docstring.
_HASH_EXCLUDED_FIELDS = frozenset({"content_hash", "generated_at"})
# The base's own hashed fields, frozen at HASH.1 (subclasses freeze theirs).
_BASE_LEGACY_HASHED_FIELDS = frozenset({"contract_versions", "upstream_hashes"})


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
    # HASH.1: the shape this artifact was written under. None means "stamped
    # before schema versions existed" — LEGACY, hashed under the frozen rule.
    # Inside the substance for versioned artifacts (see the module docstring).
    schema_version: int | None = None

    # The shared field names, asserted identical across all four artifacts by
    # tests/test_provenance_artifact.py. Named here rather than duplicated in
    # the test so the test can't drift from the base.
    SHARED_FIELDS: ClassVar[tuple[str, ...]] = (
        "generated_at",
        "content_hash",
        "contract_versions",
        "upstream_hashes",
        "schema_version",
    )

    # HASH.1: the current shape's version (bump when a field is added) and
    # the field set FROZEN at HASH.1 that legacy artifacts are hashed over.
    # Every real subclass declares its own LEGACY_HASHED_FIELDS as a literal
    # — a snapshot, never computed from the live fields, or it would track
    # the additions it exists to keep out.
    SCHEMA_VERSION: ClassVar[int] = 1
    LEGACY_HASHED_FIELDS: ClassVar[frozenset[str]] = _BASE_LEGACY_HASHED_FIELDS

    # Fields outside the content hash. Subclasses may EXTEND (RunManifest adds
    # scores_first_visible); the two base exclusions are always kept — see
    # `hash_excluded_fields()`.
    HASH_EXCLUDED_FIELDS: ClassVar[frozenset[str]] = _HASH_EXCLUDED_FIELDS

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        """THE NEW-FIELD RULE, structural: a field outside the frozen legacy
        set (and outside the hash exclusions) must default to None."""
        super().__pydantic_init_subclass__(**kwargs)
        # "New" means INTRODUCED by this class: a subclass that merely
        # narrows the exclusion set (test_cv_runner's _Sneaky) un-excludes
        # inherited fields, which is the exclusion test's business, not this
        # rule's.
        inherited = set().union(
            *(getattr(base, "model_fields", {}).keys() for base in cls.__mro__[1:])
        )
        offending = {
            name: field.default
            for name, field in cls.model_fields.items()
            if name not in inherited
            and name not in cls.LEGACY_HASHED_FIELDS
            and name not in cls.hash_excluded_fields()
            and name != "schema_version"
            and not (field.default is None and field.default_factory is None)
        }
        if offending:
            raise TypeError(
                f"{cls.__name__} adds field(s) {sorted(offending)} outside its frozen legacy "
                "set with a non-None default — under HASH.1 a new field must default to None, "
                "or it enters the present-field substance of every artifact and re-hashes "
                "history by a side door (docs/contracts/PROVENANCE.md, 'the content-hash scheme')"
            )

    @model_validator(mode="after")
    def _stamp_schema_version(self) -> "ProvenanceArtifact":
        """Fresh artifacts are versioned at construction; an artifact that
        arrives WITH a content_hash and WITHOUT a schema_version was stamped
        before HASH.1 and stays LEGACY (None) — the one discriminator that
        separates 'reloaded history' from 'built now', since only finalize()
        ever sets content_hash."""
        if self.schema_version is None and self.content_hash is None:
            self.schema_version = type(self).SCHEMA_VERSION
        return self

    @property
    def is_legacy(self) -> bool:
        return self.schema_version is None

    @classmethod
    def hash_excluded_fields(cls) -> frozenset[str]:
        """The effective exclusion set: the subclass's declaration UNION the
        two base exclusions, so a subclass cannot pull generated_at or
        content_hash back INTO its own hash by overriding the attribute."""
        return frozenset(cls.HASH_EXCLUDED_FIELDS) | _HASH_EXCLUDED_FIELDS

    def substance(self) -> dict:
        """The artifact's hashable substance, JSON-normalized with sorted keys
        so ordering is never machine- or dict-dependent.

        HASH.1: two rules, chosen by `schema_version`. LEGACY (None): the
        frozen field set, defaults included — byte-for-byte the pre-HASH.1
        payload, so committed hashes do not move. VERSIONED: every field
        whose value is not None, `schema_version` among them — so a field
        added later at its None default is invisible to every artifact that
        predates it, and two shapes with the same present fields still hash
        apart by version."""
        excluded = set(type(self).hash_excluded_fields())
        if self.is_legacy:
            include = set(type(self).LEGACY_HASHED_FIELDS) - excluded
            return self.model_dump(mode="json", include=include)
        return self.model_dump(mode="json", exclude=excluded, exclude_none=True)

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
