"""NormalizerRegistry — REGISTRY, decoupling normalizer *selection* from the
pipeline (a companion to the AbundanceNormalizer Strategy, not one of
CLAUDE.md's four named seams itself). Strategy says each evidence class
encapsulates one interchangeable normalization policy; Registry says the
pipeline never branches on evidence_class to pick one — it maps
evidence_class -> normalizer instance and exposes a single `normalize(record)`
call. Adding evidence class #6 later is one `.register(...)` line here, never
a new if/elif in IngestionPipeline (AR-D01: adding X means adding a class,
not rewriting the pipeline).

    ┌───────────────────────────┐        ┌────────────────────────────────┐
    │   IngestionPipeline          │──────► │      NormalizerRegistry           │
    │   ._normalize(record)        │        │  {MASS: MassNormalizer(),         │
    └───────────────────────────┘        │   COUNT: CountNormalizer(), ...}  │
                                           │                                    │
                                           │  .normalize(record):               │
                                           │    normalizer = self[evidence_cls] │
                                           │    record = normalizer.normalize() │
                                           │    record = apply_screening(record)│
                                           └────────────────────────────────┘

`apply_screening` is Contract 7's `screening:` block — TS-6 Table 2 bounds on
abundance_kg_m2/mn_pct/ni_pct/cu_pct/co_pct. It is deliberately NOT part of
any one evidence class's Strategy: it's a cross-cutting rule that runs after
whichever normalizer produced a value, and it only ever flags (qa_status=
"flagged"), never drops, an out-of-range row. Keeping it here means each
*_normalizer.py stays single-purpose: it only knows its own class's formula.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml

from engine.prospectivity.domain.evidence import EvidenceClass, QAStatus
from engine.prospectivity.ingestion.cover_normalizer import CoverNormalizer
from engine.prospectivity.ingestion.count_normalizer import CountNormalizer
from engine.prospectivity.ingestion.grade_normalizer import GradeNormalizer
from engine.prospectivity.ingestion.grid_normalizer import GridNormalizer
from engine.prospectivity.ingestion.mass_normalizer import MassNormalizer
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.source_adapter import RawRecord


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(f"Could not locate repo root (no pyproject.toml above {start})")


@functools.lru_cache(maxsize=1)
def _screening_bounds() -> dict[str, dict[str, float]]:
    """Contract 7's `screening:` block, loaded (not duplicated in Python) from
    data/config/normalization.yaml so the YAML stays the single source of truth."""
    repo_root = _find_repo_root(Path(__file__).resolve())
    config_path = repo_root / "data" / "config" / "normalization.yaml"
    normalization = yaml.safe_load(config_path.read_text())
    return normalization["screening"]


def apply_screening(record: RawRecord) -> RawRecord:
    """Flags (never drops) any screened field outside its normalization.yaml
    bound. Bounds are inclusive; 0 is valid for abundance_kg_m2 (barren)."""
    record = dict(record)
    for field, bounds in _screening_bounds().items():
        value = record.get(field)
        if value is None:
            continue
        if value < bounds["min"] or value > bounds["max"]:
            record["qa_status"] = QAStatus.FLAGGED.value
    return record


class NormalizerRegistry:
    """Maps evidence_class -> AbundanceNormalizer and applies the shared
    Contract 7 screening step. The pipeline calls only `.normalize(record)`;
    it never branches on evidence_class itself."""

    def __init__(self) -> None:
        self._normalizers: dict[EvidenceClass, AbundanceNormalizer] = {}

    def register(self, evidence_class: EvidenceClass, normalizer: AbundanceNormalizer) -> None:
        self._normalizers[evidence_class] = normalizer

    def assert_complete(self) -> None:
        """Fails loudly if any EvidenceClass member has no registered
        normalizer — the alternative is a class silently passing through
        unnormalized the first time a real source emits it."""
        missing = set(EvidenceClass) - set(self._normalizers)
        if missing:
            names = sorted(m.value for m in missing)
            raise ValueError(f"NormalizerRegistry is missing normalizers for: {names}")

    def normalize(self, record: RawRecord) -> RawRecord:
        evidence_class = EvidenceClass(record["evidence_class"])
        try:
            normalizer = self._normalizers[evidence_class]
        except KeyError:
            raise KeyError(
                f"No AbundanceNormalizer registered for evidence_class={evidence_class!r}"
            ) from None
        return apply_screening(normalizer.normalize(record))


def build_default_registry() -> NormalizerRegistry:
    """The real production registry: one normalizer per evidence_class, per
    normalization.yaml. Adding evidence class #6 is one more `.register(...)`
    line here."""
    registry = NormalizerRegistry()
    registry.register(EvidenceClass.MASS, MassNormalizer())
    registry.register(EvidenceClass.COUNT, CountNormalizer())
    registry.register(EvidenceClass.COVER, CoverNormalizer())
    registry.register(EvidenceClass.GRID, GridNormalizer())
    registry.register(EvidenceClass.GRADE, GradeNormalizer())
    registry.assert_complete()
    return registry
