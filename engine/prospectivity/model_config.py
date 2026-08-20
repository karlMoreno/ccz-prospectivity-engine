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


@dataclass(frozen=True)
class DeclaredField:
    """A contract value carried WITH its origin declaration, so a consumer
    cannot record the value and lose the caveat. `value` may be None — an
    explicitly-null field is a declared absence, which the loader treats as
    different from a MISSING field (that raises)."""

    value: str | None
    data_origin: str
    author: str | None


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

    THE SLOT DOES NOT EXIST TODAY, and that is the honest state, not an
    oversight: Contract 8's header says `acceptance_thresholds` "arrives with
    E2.5's refuse-to-validate guard", and this accessor is the consumer that
    arrival now has — but the VALUE is Track G's to supply, and the same
    header forbids pre-declaring "a field with no consumer is a field nobody
    has tested the meaning of". Adding the field is a STRUCTURAL contract
    change (version bump + Karl + the contracts README), so E2.5 does not
    make it; it makes the absence REFUSABLE BY NAME instead.

    Three distinct states, three different messages, because a consumer that
    cannot tell them apart cannot report which one it hit:
      * field ABSENT      -> raises: no slot exists at all (today's state);
      * value None        -> DeclaredField(value=None, ...), a declared
                             absence the guard refuses as "not populated";
      * value present     -> returned with its origin, for the guard to
                             classify (an AUTHORED threshold is a number
                             someone typed, and precondition 6 refuses it).

    `contract` is a testability seam (the `target_definition` precedent);
    production callers omit it."""
    contract = contract if contract is not None else load_model_config()
    if "acceptance_thresholds" not in contract:
        raise ValueError(
            "model_config.yaml has no acceptance_thresholds field — Contract 8's "
            "header records that it 'arrives with E2.5's refuse-to-validate guard', "
            "and the guard is here, but the SLOT is a structural contract change "
            "(bump model_config_version, tell Karl, note it in the contracts README) "
            "and the VALUE is Track G's. Until both happen, no acceptance gate "
            "exists and no run can be emitted as a validated claim."
        )
    field = contract["acceptance_thresholds"]
    return DeclaredField(
        value=field.get("value"),
        data_origin=field["data_origin"],
        author=field.get("author"),
    )
