"""DataOrigin — the five-value origin taxonomy (P2.0b, from the 2026-08-08 audit).

Every value in this project is classified by HOW IT CAME TO EXIST IN THIS
REPO. This module is the single code home for that vocabulary: the enum, the
ordering, and the one combination rule. It deliberately does nothing else —
P2.0c applies the markers (and widens the interim path guards); P2.0d builds
the audit test and replaces path inference with the declaration-based
production-path guard. The input to all three is
docs/audits/2026-08-08-origin-vocabulary-audit.md; the P2.0 decisions this
module cites are recorded in docs/walkthroughs/P2.0.md §b.

What the ordering measures
--------------------------
Provenance distance from a measurement this repo holds and can hash — NOT
trustworthiness. DERIVED outranks LITERATURE because a DERIVED value traces to
a hashed input file by a recorded formula, while a LITERATURE value traces to
a publication with no file in hand. A peer-reviewed constant may well be more
trustworthy than our arithmetic; that is not what this axis ranks.

    MEASURED ──► DERIVED ──► LITERATURE ──► SYNTHETIC ──► AUTHORED
    most real                                             least real

Evidence each label requires (the audit's classification work plus the P2.0b
decisions recorded in docs/walkthroughs/P2.0.md §b; P2.0c applies these):

* MEASURED   — source_id, DOI, and the input file's SHA-256.
* DERIVED    — a derivation_formula plus the origins of its inputs.
* LITERATURE — a citation specific enough to LOCATE the number: document plus
  table/section/page. "TS-6" alone is insufficient. (The audit found
  covariates.yaml's ts6_finding strings cite findings with no table or page
  reference; P2.0c records those as evidence gaps rather than closing them by
  guessing.)
* SYNTHETIC  — the generator's import path and seed. In this repo only
  tests/fixtures/rasters.py currently qualifies (seeds 0 and 1).
* AUTHORED   — author: one of ALLOWED_AUTHORS ("model", "karl", "isaac", or
  "unrecorded" — the last reserved for values predating this rule; see
  validate_author).

combine_origins — one rule, two scales
--------------------------------------
combine_origins returns the LEAST-real input: a real corpus does not launder
a synthetic terrain. The same function serves two scales deliberately —
combining several artifacts' origins into a run's origin, and combining
several entries' origins into a file's origin. One rule, two scales, nothing
for a reader to remember. Empty input RAISES: a silent default here is the
exact failure mode this module exists to prevent.

Pattern note — deliberately NOT a pattern
-----------------------------------------
A value object with a monotone combine — NOT a Strategy and NOT a Registry.
There is one ordering and there will not be a second, so an interface here
would be indirection without a variation point: exactly the ceremony
docs/PATTERNS.md §3 objects to. Do not "fix" this module by adding a seam.

Terminology collision, recorded so no one trusts a filename
-----------------------------------------------------------
This repo's word "synthetic" mostly denotes taxonomy-AUTHORED: the hand-typed
fixture values in data/fixtures/native/*.csv, SYNTHETIC_MEAN_NODULE_MASS_G in
tests/fixtures/normalizers.py, and the src_synthetic_* source ids.
Taxonomy-SYNTHETIC requires a deterministic generator with a recorded seed,
which only tests/fixtures/rasters.py satisfies. Nothing is renamed (P2.0
decision, docs/walkthroughs/P2.0.md §b); the collision is recorded rather
than corrected.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum


class DataOrigin(str, Enum):
    """How a value came to exist in this repo (see module docstring for the
    evidence each label requires). Values equal member names so YAML/JSON
    markers read `data_origin: MEASURED` and round-trip through
    ``DataOrigin(...)`` loudly — an unknown string raises."""

    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    LITERATURE = "LITERATURE"
    SYNTHETIC = "SYNTHETIC"
    AUTHORED = "AUTHORED"


# Most-real first. This tuple IS the ordering; combine_origins ranks by
# position in it. Completeness against the enum is test-enforced in both
# directions (tests/test_data_origin.py), mirroring how CovariateRegistry
# checks recipe_version against the contract.
ORIGIN_ORDER_MOST_REAL_FIRST: tuple[DataOrigin, ...] = (
    DataOrigin.MEASURED,
    DataOrigin.DERIVED,
    DataOrigin.LITERATURE,
    DataOrigin.SYNTHETIC,
    DataOrigin.AUTHORED,
)

_REALNESS_RANK = {origin: rank for rank, origin in enumerate(ORIGIN_ORDER_MOST_REAL_FIRST)}

# The author vocabulary (docs/walkthroughs/P2.0.md §b, tightened P2.0c §0.2):
# a closed allow-list, not free text. Free text let a typo'd "moddel" validate
# as a person's name — the one origin the taxonomy most needs to detect (a
# value a model wrote) failing toward the safe-looking answer. Adding a
# collaborator is one deliberate line here; completeness is test-enforced both
# directions, mirroring NormalizerRegistry.assert_complete().
AUTHOR_MODEL = "model"
AUTHOR_UNRECORDED = "unrecorded"
ALLOWED_AUTHORS: tuple[str, ...] = (AUTHOR_MODEL, "karl", "isaac", AUTHOR_UNRECORDED)


def combine_origins(origins: Iterable[DataOrigin | str]) -> DataOrigin:
    """Return the LEAST-real origin among ``origins`` — the worst input wins.

    A real corpus does not launder a synthetic terrain: any SYNTHETIC or
    AUTHORED ingredient makes the combination SYNTHETIC or AUTHORED. This one
    function serves two scales deliberately: several artifacts' origins →
    a run's origin, and several entries' origins → a file's origin. One rule,
    two scales, nothing for a reader to remember.

    Raw strings are accepted and validated through ``DataOrigin(...)`` so an
    unknown label raises ``ValueError`` instead of ranking silently. Empty
    input raises: a silent default here would fabricate provenance, the exact
    failure mode this module exists to prevent.
    """
    members = [DataOrigin(origin) for origin in origins]
    if not members:
        raise ValueError(
            "combine_origins() requires at least one origin — refusing to "
            "default: a silent origin here would fabricate provenance."
        )
    return max(members, key=_REALNESS_RANK.__getitem__)


def validate_author(author: object) -> str:
    """Validate an ``author`` value against ALLOWED_AUTHORS — exact match only.

    ``"model"`` means a model drafted the value; ``"karl"``/``"isaac"`` are
    the project's two people; ``"unrecorded"`` means the value predates the
    origin rule and its author is not reconstructible from the repo — git
    records committers, not who or what drafted a value. It is an honest gap,
    not a default: P2.0d freezes the explicit list of files permitted to carry
    it, so the set only shrinks. New work uses ``"model"`` or a name.

    Anything outside the allow-list raises, naming the offending value and
    the admissible set (case-sensitive: ``"Isaac"`` and ``"moddel"`` both
    raise). Free text was rejected in P2.0c §0.2 because a typo'd author
    validated as a person's name — a silent failure toward the safe-looking
    answer.
    """
    if not isinstance(author, str) or author not in ALLOWED_AUTHORS:
        raise ValueError(
            f"author must be one of {ALLOWED_AUTHORS!r} — got {author!r}. "
            "Add a new collaborator to ALLOWED_AUTHORS deliberately; do not "
            "widen this check."
        )
    return author
