"""Contract 4 loader (data/economics/scenarios.yaml) and the Contract 2
companion it depends on (data/aoi/exclusions.geojson) — E4.1 commit 1.

Sits beside the Contract 8 loader (`model_config.py`) and follows its
posture exactly, reusing `find_repo_root` and `DeclaredField`:

    scenarios.yaml ──► load_scenarios_yaml() ──► grade_metric()      DeclaredField
                                             ├─► spatial_filters()   SpatialFilters
                                             ├─► scenarios()         (ScenarioConfig, …)
                                             └─► difference_pairs()  ((a, b), …)
    exclusions.geojson ──► load_exclusions() ──► ExclusionSet

THE THREE-STATE ACCESSOR POSTURE (C8.1; E3.3's digitization_uncertainty):
ABSENT raises naming the structural gap; NULL raises naming the unfilled
value; POPULATED returns the value AND its declared origin together, so a
consumer asks "what is the cutoff, and is it a finding or a stand-in?" in
one call. Contract 4 declares its origin ONCE, at file level (P2.0c:
`data_origin: AUTHORED`, every number "origin: file-level data_origin
above"), so every DeclaredField here carries that file-level origin.

THE illustrative_only QUESTION, RESOLVED (E4.1 commit 1; Karl's Decision 1).
E4.0 found nothing in engine/ read the flag. Under Decision 1 it is the
DECLARED FACT one watermark reason derives FROM — "the economic parameters
are placeholders", lifted at Checkpoint 4 — which is a real job, not a
redundancy with `data_origin`. The two answer DIFFERENT questions: the flag
says whether the value is a STAND-IN; the origin says HOW THE VALUE CAME TO
EXIST. They may legitimately differ in ONE direction — a LITERATURE value
Isaac still flags illustrative is a conservative declaration — and they
CONTRADICT in the other: `illustrative_only: false` on a value whose origin
is less real than LITERATURE claims a defensible number with no defensible
source. `scenarios()` REFUSES that direction by name, so the two cannot be
two sources of truth for one fact. Nothing copies the boolean into a result;
the watermark reason's `cause` CITES it (economics/watermark.py).

WHAT THE TWO SCENARIOS ARE MEANT TO BRACKET: the ground the MARKET would
mine (a commercial cutoff) and the ground a government might SUBSIDIZE into
production (a lower, strategic cutoff) — Contract 4 says the DIFFERENCE is
the headline output. E4.0 stated in advance that on today's surfaces (the
training mean ≈ 19.5 kg/m² over 99% of the domain, both cutoffs below it)
they may bracket NOTHING; that is a finding about the placeholders, not
about this loader (E4.1.md; BACKLOG for G4.1).
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.model_config import ADMISSIBLE_THRESHOLD_ORIGINS, DeclaredField
from engine.prospectivity.provenance.origin import DataOrigin

REPO_ROOT = find_repo_root(Path(__file__).resolve())
SCENARIOS_PATH = REPO_ROOT / "data" / "economics" / "scenarios.yaml"
EXCLUSIONS_PATH = REPO_ROOT / "data" / "aoi" / "exclusions.geojson"

GRADE_METRICS = ("abundance", "dollar_value")


@functools.lru_cache(maxsize=1)
def load_scenarios_yaml() -> dict:
    """Contract 4, loaded from data/economics/scenarios.yaml."""
    return yaml.safe_load(SCENARIOS_PATH.read_text())


def _file_origin(contract: dict) -> tuple[str, str | None]:
    """Contract 4's file-level declaration — the origin every number carries."""
    if "data_origin" not in contract:
        raise ValueError(
            "scenarios.yaml has no file-level data_origin — Contract 4 declares its "
            "origin ONCE at file level (P2.0c) and every value inherits it; an "
            "undeclared contract cannot hand a consumer a classified value"
        )
    return DataOrigin(contract["data_origin"]).value, contract.get("author")


def _require_slot(contract: dict, name: str, where: str = "scenarios.yaml") -> object:
    """ABSENT raises naming the structural gap (a missing field is never a
    null one); the caller decides what NULL means for its field."""
    if name not in contract:
        raise ValueError(
            f"{where} has no {name} field — a missing field is not an explicitly-null "
            "one. Adding it is a structural contract change (config_version bump, "
            "Karl); its absence means the contract was edited or a partial dict was passed"
        )
    return contract[name]


def grade_metric(contract: dict | None = None) -> DeclaredField:
    """How the per-cell metric the cutoff is compared against is computed:
    `abundance` (predicted kg/m² directly) or `dollar_value` (metal grades ×
    prices). `[GEOLOGY — ISAAC]` chooses. With its file-level origin."""
    contract = contract if contract is not None else load_scenarios_yaml()
    value = _require_slot(contract, "grade_metric")
    if value is None:
        raise ValueError(
            "scenarios.yaml declares grade_metric explicitly NULL — the metric is "
            "unfilled, and a footprint cannot be computed against an undeclared metric"
        )
    if value not in GRADE_METRICS:
        raise ValueError(
            f"grade_metric {value!r} is not one of {list(GRADE_METRICS)} — a new metric "
            "arrives via the contract WITH its computation, never by loosening this check"
        )
    origin, author = _file_origin(contract)
    return DeclaredField(value=str(value), data_origin=origin, author=author)


def grade_units(contract: dict | None = None) -> DeclaredField:
    contract = contract if contract is not None else load_scenarios_yaml()
    value = _require_slot(contract, "grade_units")
    if value is None:
        raise ValueError("scenarios.yaml declares grade_units explicitly NULL — unfilled")
    origin, author = _file_origin(contract)
    return DeclaredField(value=str(value), data_origin=origin, author=author)


@dataclass(frozen=True)
class SpatialFilters:
    """Contract 4's `spatial_filters`, each value with the file-level origin."""

    max_slope_degrees: DeclaredField
    apply_exclusions: bool


def spatial_filters(contract: dict | None = None) -> SpatialFilters:
    contract = contract if contract is not None else load_scenarios_yaml()
    block = _require_slot(contract, "spatial_filters")
    if block is None:
        raise ValueError("scenarios.yaml declares spatial_filters explicitly NULL — unfilled")
    slope = _require_slot(block, "max_slope_degrees", "scenarios.yaml spatial_filters")
    if slope is None:
        raise ValueError(
            "spatial_filters.max_slope_degrees is explicitly NULL — the collector slope "
            "limit is unfilled ([GEOLOGY — ISAAC]); the filter cannot be applied"
        )
    apply = _require_slot(block, "apply_exclusions", "scenarios.yaml spatial_filters")
    if apply is None:
        raise ValueError("spatial_filters.apply_exclusions is explicitly NULL — unfilled")
    origin, author = _file_origin(contract)
    return SpatialFilters(
        max_slope_degrees=DeclaredField(value=str(float(slope)), data_origin=origin, author=author),
        apply_exclusions=bool(apply),
    )


@dataclass(frozen=True)
class ScenarioConfig:
    """One Contract 4 scenario: its cutoff WITH its origin, and the declared
    facts the watermark derives from. `illustrative_only` is carried as the
    DECLARED FACT it is — never copied into a result (see the module
    docstring)."""

    name: str
    index: int
    description: str
    illustrative_only: bool
    cutoff: DeclaredField  # value is the kg/m² cutoff as a string (DeclaredField's type)
    cost_model: dict
    caveats: tuple[str, ...]

    @property
    def cutoff_value(self) -> float:
        return float(self.cutoff.value)  # type: ignore[arg-type]


def scenarios(contract: dict | None = None) -> tuple[ScenarioConfig, ...]:
    """Every scenario, in contract order. Per scenario: `cutoff_value` ABSENT
    raises naming the scenario and the structural gap; NULL raises naming
    the unfilled value; `illustrative_only` ABSENT raises (the declared fact
    the watermark derives from cannot be inferred). And THE CONSISTENCY
    RULE: `illustrative_only: false` on a file whose origin is less real
    than LITERATURE is refused — a non-illustrative value must have a source
    a reader could check (C8.1's admissibility, one contract over)."""
    contract = contract if contract is not None else load_scenarios_yaml()
    raw = _require_slot(contract, "scenarios")
    if not raw:
        raise ValueError("scenarios.yaml declares no scenarios — an empty list is not a contract")
    origin, author = _file_origin(contract)
    out = []
    for index, entry in enumerate(raw):
        where = f"scenarios.yaml scenarios[{index}]"
        name = _require_slot(entry, "scenario_name", where)
        where = f"scenarios.yaml scenario {name!r}"
        flag = _require_slot(entry, "illustrative_only", where)
        if flag is None:
            raise ValueError(
                f"{where} declares illustrative_only explicitly NULL — the flag is the "
                "declared fact one watermark reason derives from; it must be true or false"
            )
        if flag is False and DataOrigin(origin) not in ADMISSIBLE_THRESHOLD_ORIGINS:
            raise ValueError(
                f"{where} declares illustrative_only: false while the contract's "
                f"data_origin is {origin} — a NON-illustrative cutoff must have an origin "
                "at least as real as LITERATURE (a citation that locates it, or evidence). "
                "The flag and the origin are two declarations of different facts, and "
                "this is the one direction in which they contradict each other"
            )
        cutoff = _require_slot(entry, "cutoff_value", where)
        if cutoff is None:
            raise ValueError(
                f"{where} declares cutoff_value explicitly NULL — the cutoff is unfilled "
                "([GEOLOGY — ISAAC]); a footprint cannot be computed against it"
            )
        out.append(
            ScenarioConfig(
                name=str(name),
                index=index,
                description=str(entry.get("description") or "").strip(),
                illustrative_only=bool(flag),
                cutoff=DeclaredField(value=str(float(cutoff)), data_origin=origin, author=author),
                cost_model=dict(entry.get("cost_model") or {}),
                caveats=tuple(str(c) for c in (entry.get("caveats") or ())),
            )
        )
    names = [s.name for s in out]
    if len(set(names)) != len(names):
        raise ValueError(f"scenarios.yaml names a scenario twice: {names}")
    return tuple(out)


def scenario(name: str, contract: dict | None = None) -> ScenarioConfig:
    for entry in scenarios(contract):
        if entry.name == name:
            return entry
    raise ValueError(
        f"scenarios.yaml has no scenario named {name!r} — it names "
        f"{[s.name for s in scenarios(contract)]}"
    )


def difference_pairs(contract: dict | None = None) -> tuple[tuple[str, str], ...]:
    """Contract 4's `difference_pairs`: (a, b) means the footprint minable
    under b and NOT under a — "the strategic-only footprint" when a is the
    market scenario. Each name must be a declared scenario."""
    contract = contract if contract is not None else load_scenarios_yaml()
    raw = _require_slot(contract, "difference_pairs")
    names = {s.name for s in scenarios(contract)}
    pairs = []
    for pair in raw or ():
        if len(pair) != 2 or not set(pair) <= names:
            raise ValueError(
                f"difference_pairs entry {pair!r} does not name two declared scenarios "
                f"({sorted(names)})"
            )
        pairs.append((str(pair[0]), str(pair[1])))
    return tuple(pairs)


@dataclass(frozen=True)
class ExclusionSet:
    """Contract 2's companion: the polygons subtracted from every footprint.
    "Starts EMPTY on purpose" — `features` is asserted, never assumed."""

    path: str
    data_origin: str
    author: str | None
    features: tuple[dict, ...]

    @property
    def is_empty(self) -> bool:
        return len(self.features) == 0


def load_exclusions(path: Path | None = None) -> ExclusionSet:
    path = Path(path) if path is not None else EXCLUSIONS_PATH
    raw = json.loads(path.read_text())
    if "data_origin" not in raw:
        raise ValueError(f"{path.name} has no data_origin — declaration or nothing (P2.0d-3)")
    return ExclusionSet(
        path=path.name,
        data_origin=DataOrigin(raw["data_origin"]).value,
        author=raw.get("author"),
        features=tuple(raw.get("features") or ()),
    )
