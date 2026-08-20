"""Contract 8 loader (data/config/model_config.yaml) — Phase-2 model
parameters, as distinct from Contract 7's ingestion policy.

Same spirit as features/_contract.py and ingestion/_contract_paths.py (whose
`find_repo_root` this reuses; no duplicated parsing logic): the YAML stays
the single source of truth. Public, unlike those two, because consumers must
be able to ask "what is y, and is that a finding or a stand-in?" IN ONE CALL
— `target_definition()` returns the value TOGETHER with its declared origin,
so E2.0 can record both into the training-matrix provenance and the caveat
travels with the number instead of being lost at the call site.

Deliberately NO TargetDefinition domain class here: the contract and its
loader are the deliverable; E2.0 wires the consumer. `DeclaredField` is a
generic value-plus-declaration carrier, not a modelling concept.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import yaml

from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.provenance.origin import (
    ORIGIN_ORDER_MOST_REAL_FIRST,
    DataOrigin,
)

# A GATE MUST BE AT LEAST AS REAL AS LITERATURE (C8.1). Derived from the
# taxonomy's own realness order rather than hand-listed, so the rule cannot
# drift from `origin.py` and a new member lands on the correct side by its
# rank: MEASURED > DERIVED > LITERATURE are admissible; SYNTHETIC and
# AUTHORED are not. NOT INVENTED HERE: this is the set E2.5's precondition 6
# already named in prose, in the AUTHORED branch C8.1 moved into this module
# ("it arrives as LITERATURE with a citation that locates it, or as a
# MEASURED or DERIVED value with its evidence"). The rule was written down
# before it was enforced; this turns the prose into the check.
_LEAST_REAL_ADMISSIBLE_GATE = DataOrigin.LITERATURE
ADMISSIBLE_THRESHOLD_ORIGINS: tuple[DataOrigin, ...] = ORIGIN_ORDER_MOST_REAL_FIRST[
    : ORIGIN_ORDER_MOST_REAL_FIRST.index(_LEAST_REAL_ADMISSIBLE_GATE) + 1
]


@dataclass(frozen=True)
class DeclaredField:
    """A contract value carried WITH its origin declaration, so a consumer
    cannot record the value and lose the caveat. `value` may be None — an
    explicitly-null field is a declared absence, which the loader treats as
    different from a MISSING field (that raises).

    `data_origin` may be None ONLY while `value` is None (C8.1): an
    awaiting-classification field has nothing to classify. The invariant
    below makes "populated but unclassified" unrepresentable rather than
    merely checked, so a future accessor cannot forget the rule.
    """

    value: str | None
    data_origin: str | None
    author: str | None

    def __post_init__(self) -> None:
        # AN IMPLICATION, NOT A BICONDITIONAL, deliberately: a value requires
        # an origin, but a NULL value may still carry one — target_definition
        # does exactly that (`value: null` with `data_origin: AUTHORED` is a
        # declared "not decided", still classified). Enforcing the converse
        # here would break that documented state for no stated requirement.
        if self.value is not None and self.data_origin is None:
            raise ValueError(
                f"DeclaredField carries value {self.value!r} with no data_origin — "
                "a value cannot arrive unclassified. The accessors refuse this "
                "first, naming the contract field; this is the structural "
                "backstop that makes the state unrepresentable."
            )


@functools.lru_cache(maxsize=1)
def load_model_config() -> dict:
    """Contract 8, loaded from data/config/model_config.yaml."""
    repo_root = find_repo_root(Path(__file__).resolve())
    contract_path = repo_root / "data" / "config" / "model_config.yaml"
    return yaml.safe_load(contract_path.read_text())


def target_definition(contract: dict | None = None) -> DeclaredField:
    """What abundance_kg_m2 MEANS as y, with its declared origin.

    - A MISSING `target_definition` field raises: a missing field and an
      explicitly-null field must never be the same thing to a consumer.
    - An explicitly-null `value` returns DeclaredField(value=None, ...) —
      a declared "not decided", still carrying its origin.
    - A non-null value outside the contract's own `admissible_values` raises,
      naming the value and the admissible set — the enum is P2.B's verdict
      and dead ends stay dead.

    `contract` is a testability seam (build_default_registry precedent);
    production callers omit it."""
    contract = contract if contract is not None else load_model_config()
    if "target_definition" not in contract:
        raise ValueError(
            "model_config.yaml has no target_definition field — a missing "
            "field is not an explicitly-null one; declare it (value: null is "
            "admissible, absence is not)."
        )
    field = contract["target_definition"]
    value = field.get("value")
    admissible = tuple(field.get("admissible_values") or ())
    if value is not None and value not in admissible:
        raise ValueError(
            f"target_definition value {value!r} is not admissible — P2.B's "
            f"verdict fixed the enum to {list(admissible)!r}. A new value "
            "arrives via the contract (with the evidence that makes it "
            "derivable), never by loosening this check."
        )
    return DeclaredField(
        value=value,
        data_origin=field["data_origin"],
        author=field.get("author"),
    )


def acceptance_thresholds(contract: dict | None = None) -> DeclaredField:
    """The acceptance gate a validated claim must clear, WITH its origin —
    E2.5's precondition 6 (the pre-registration clock, docs/BACKLOG.md §2).

    THE SLOT EXISTS as of C8.1 (2026-08-19, model_config_version 2), closing
    P2.A's deferral on its own stated condition: the field "arrives with
    E2.5's refuse-to-validate guard", and E2.5 built the consumer. It ships
    `value: null` — AWAITING CLASSIFICATION — because no default is
    admissible here (see the asymmetry below).

    THREE STATES, THREE BEHAVIOURS, because a consumer that cannot tell them
    apart cannot report which one it hit:
      * field ABSENT   -> raises. A missing field and a null field are never
                          the same thing (the target_definition rule).
      * value None     -> the AWAITING state: DeclaredField(value=None, ...),
                          NOT an error. Precondition 6 reads it and refuses
                          BY NAME, which is the designed path today.
      * value present  -> returned WITH its declared origin, so a consumer
                          asks "what is the gate, and is it a finding or a
                          stand-in?" in one call.

    AND TWO OUTRIGHT REJECTIONS — a populated field that must never reach a
    consumer at all:
      * no data_origin -> a value cannot arrive unclassified;
      * AUTHORED (or any origin less real than LITERATURE) -> REJECTED, not
        recorded.

    THE ASYMMETRY WITH `target_definition` IS DELIBERATE AND LOOKS LIKE AN
    INCONSISTENCY. That field's provisional default IS AUTHORED
    (`author: model`), and that is fine: a wrong TARGET degrades output
    quality, is recorded, and is swappable — the run stays honest because the
    caveat travels with the number. A wrong THRESHOLD does something else
    entirely: it silently BECOMES THE VERDICT. Same taxonomy, opposite
    admissibility, for a stated reason.

    `contract` is a testability seam (the `target_definition` precedent);
    production callers omit it."""
    contract = contract if contract is not None else load_model_config()
    if "acceptance_thresholds" not in contract:
        raise ValueError(
            "model_config.yaml has no acceptance_thresholds field — a missing "
            "field is not an explicitly-null one. The slot arrived at C8.1 "
            "(model_config_version 2); its absence now means the contract was "
            "edited or a partial dict was passed, not that the gate is undecided."
        )
    field = contract["acceptance_thresholds"] or {}
    value = field.get("value")
    origin = field.get("data_origin")
    author = field.get("author")

    if value is None:
        # AWAITING CLASSIFICATION — the shipped state, and not an error: the
        # guard refuses on it by name. A `data_origin` here is neither
        # required nor forbidden (nothing to classify, but see the
        # DeclaredField note); it is carried through untouched.
        return DeclaredField(value=None, data_origin=origin, author=author)

    if origin is None:
        raise ValueError(
            f"acceptance_thresholds declares value {value!r} with no data_origin — "
            "a value cannot arrive unclassified. A gate whose provenance is "
            "unstated cannot be checked against the scores it is supposed to "
            "predate; declare LITERATURE with a citation that LOCATES the "
            "number, or MEASURED/DERIVED with its evidence."
        )

    declared = DataOrigin(origin)  # unknown labels raise here, not rank silently
    if declared not in ADMISSIBLE_THRESHOLD_ORIGINS:
        if declared is DataOrigin.AUTHORED:
            raise ValueError(
                f"acceptance_thresholds is declared AUTHORED (author {author!r}) and is "
                "REJECTED, NOT RECORDED: an AUTHORED value is one written with no "
                "external source, which for a GATE means Track E (or a model) "
                "inventing the standard its own work is measured against. "
                "THE ASYMMETRY WITH target_definition IS DELIBERATE — an AUTHORED "
                "target is admissible because a wrong target degrades output "
                "quality, recorded and swappable, while a wrong threshold silently "
                "BECOMES THE VERDICT. Same taxonomy, opposite admissibility. "
                f"Admissible here: {[o.value for o in ADMISSIBLE_THRESHOLD_ORIGINS]}."
            )
        raise ValueError(
            f"acceptance_thresholds is declared {declared.value} — a gate must be at "
            f"least as real as {_LEAST_REAL_ADMISSIBLE_GATE.value} on the taxonomy's "
            f"realness order. Admissible: "
            f"{[o.value for o in ADMISSIBLE_THRESHOLD_ORIGINS]}."
        )
    return DeclaredField(value=value, data_origin=declared.value, author=author)
