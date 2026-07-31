from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.dedup_rules import DuplicateResolutionPolicy
from engine.prospectivity.ingestion.normalizer import AbundanceNormalizer
from engine.prospectivity.ingestion.pangaea_adapter import PangaeaAdapter
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.regional_grid_adapter import RegionalGridAdapter
from engine.prospectivity.ingestion.resolution import (
    AbsorbInto,
    Admit,
    AlreadyPresent,
    Replace,
    Resolution,
)
from engine.prospectivity.ingestion.source_adapter import RawRecord, SourceAdapter
from engine.prospectivity.ingestion.tabular_file_adapter import TabularFileAdapter

# `Specification` was re-exported here until 2026-07-30. The ABC is deleted:
# after the C2 refactor it had zero implementations, and it had already lost
# its combinators (docs/PATTERNS.md §3.0/§3.1). A genuinely pure future rule
# (AOI/exclusion-zone, publication gate) should get a fresh base class whose
# docstring can promise purity without caveats — not inherit one whose
# documentation is a warning about a class that left.
__all__ = [
    "SourceAdapter",
    "RawRecord",
    "AbundanceNormalizer",
    "DuplicateResolutionPolicy",
    "Resolution",
    "Admit",
    "AlreadyPresent",
    "AbsorbInto",
    "Replace",
    "IngestionPipeline",
    "EvidenceClassMapping",
    "PangaeaAdapter",
    "TabularFileAdapter",
    "RegionalGridAdapter",
]
