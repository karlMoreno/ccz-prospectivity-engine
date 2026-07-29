"""corpus_builder — Phase 1, E1.3's corpus-assembly entry point: wires every
real SourceAdapter through IngestionPipeline (fetch->adapt->normalize->
validate->dedup->append), using the E1.2 NormalizerRegistry and the E1.3
DuplicateStationSpecification, into ONE shared corpus written to
data/corpus/master_observations.csv.

    build_boxcore()  ──┐
    build_nodules()  ──┼──► IngestionPipeline(adapter, registry, corpus, dedup) ──► corpus
    build_chamber()  ──┤        (same registry + same dedup Specification instance
    build_ts6_grid() ──┘         shared across every adapter's run)

Adapter run ORDER is part of the contract, not incidental: survivor
precedence ties (dedup_rules.py: equal quality_grade) go to whichever row was
accepted first, so re-ordering REAL_ADAPTER_BUILDERS can change which row of
a genuine duplicate pair survives.

Deliberately excludes src_washburn2021_grid [19] (GRID+GRADE): the GRADE
station join (`join_tolerance_km`) is unresolved geology input and out of
scope for E1.3 (per the engineer of record's explicit instruction — GRADE
rows pass through unjoined wherever they occur, but nothing here manufactures
one). [01] and [05] both read their REAL downloaded PANGAEA files (D5/D8,
2026-07-27 review) — the other two sources still read their E1.1 saved
sample files.

Known limitation: dedup only catches a candidate that duplicates a row
ALREADY in the corpus (from an earlier adapter in this list, or an earlier
call to build_corpus() against the same corpus list) — two duplicate rows
arriving in the SAME adapter's own single batch would not catch each other.
None of the four wired sources' sample data has that shape today.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.ingestion.boxcore_summary_adapter import BoxcoreSummaryAdapter
from engine.prospectivity.ingestion.dedup_rules import DuplicateStationSpecification
from engine.prospectivity.ingestion.nodule_aggregate_adapter import NoduleAggregateAdapter
from engine.prospectivity.ingestion.normalizer_registry import build_default_registry
from engine.prospectivity.ingestion.pipeline import IngestionPipeline
from engine.prospectivity.ingestion.regional_grid_adapter import RegionalGridAdapter
from engine.prospectivity.ingestion.source_adapter import SourceAdapter
from engine.prospectivity.ingestion.tabular_file_adapter import TabularFileAdapter

REPO_ROOT = find_repo_root(Path(__file__).resolve())
SAMPLES_DIR = REPO_ROOT / "tests" / "fixtures" / "samples"
SOURCES_DIR = REPO_ROOT / "data" / "sources"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "data" / "corpus" / "master_observations.csv"

# The written CSV's column order: the master schema's own field order
# (Observation.model_fields mirrors docs/contracts/master_observations
# .schema.json field-for-field), never left to dict/set iteration order.
_CSV_COLUMNS = list(Observation.model_fields.keys())


def build_boxcore_adapter() -> BoxcoreSummaryAdapter:
    """src_so268_boxcore [01] — MASS+COUNT+COVER, one row per event, reading
    the REAL downloaded PANGAEA.904967 file (D8, 2026-07-27 review). cruise
    and water_depth_m are derived per row inside the adapter (same reasons
    as [05]) — NOT listed here, since a shared_column_map entry for either
    would be overwritten by the adapter's own computed value.

    The PANGAEA parameter list names three different columns "Nodules" —
    matched here by their FULL header string (see
    boxcore_summary_adapter.py's module docstring for why a substring match
    would be a silent MASS/COUNT/COVER mismatch bug)."""
    return BoxcoreSummaryAdapter(
        source_id="src_so268_boxcore",
        file_path=SOURCES_DIR / "SO268-bc-nodules-summary-PANGAEA-904967.tab",
        shared_column_map={
            "event_id": "Event",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "water_depth_m": "Elevation [m]",
            "sample_datetime_utc": "Date/Time",
        },
        evidence_mappings=[
            EvidenceClassMapping(
                evidence_class="MASS",
                column_map={"nodule_mass_kg": "Nodules m [kg] (total)"},
            ),
            EvidenceClassMapping(
                evidence_class="COUNT",
                column_map={"nodule_count": "Nodules [#]"},
                presence_column="Nodules [#]",
            ),
            EvidenceClassMapping(
                evidence_class="COVER",
                column_map={
                    "visible_cover_percent": "Nodules [%] (seafloor coverage by nodules)"
                },
                presence_column="Nodules [%] (seafloor coverage by nodules)",
            ),
        ],
        is_open=True,
        static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
    )


def build_nodule_aggregate_adapter() -> NoduleAggregateAdapter:
    """src_so268_nodules [05] — aggregated to one MASS+COUNT record per event
    (dedup rule 3), reading the REAL downloaded PANGAEA.904962 file (D5,
    2026-07-27 review). cruise and water_depth_m are derived per row inside
    the adapter (mixed SO268/1 & SO268/2 events; negative Elevation [m]) —
    NOT listed here, since the adapter computes them itself and a
    shared_column_map entry for either would silently overwrite that."""
    return NoduleAggregateAdapter(
        source_id="src_so268_nodules",
        file_path=SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab",
        event_column="Event",
        mass_column_g="Nodule m [g]",
        dimension_columns=["Nodule l [mm]", "Nodule w [mm]", "Nodule h [mm]"],
        shared_column_map={
            "event_id": "Event",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "sample_datetime_utc": "Date/Time",
        },
        is_open=True,
        static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
    )


def build_dryad_chamber_adapter() -> TabularFileAdapter:
    """src_dryad_chamber [06] — MASS, chamber footprint as sampled_area_m2."""
    return TabularFileAdapter(
        source_id="src_dryad_chamber",
        file_path=SAMPLES_DIR / "dryad_chamber_sample.csv",
        shared_column_map={
            "station_id": "chamber_id",
            "latitude": "latitude",
            "longitude": "longitude",
            "water_depth_m": "water_depth_m",
            "sample_datetime_utc": "deploy_date",
            "sampled_area_m2": "chamber_footprint_m2",
        },
        evidence_mappings=[
            EvidenceClassMapping(
                evidence_class="MASS", column_map={"nodule_mass_kg": "nodule_mass_kg"}
            ),
        ],
        is_open=True,
        static_fields={"sample_method": "chamber"},
    )


def build_ts6_grid_adapter() -> RegionalGridAdapter:
    """src_ts6_grid [18] — GRID, compiled/benchmark, never a training station."""
    return RegionalGridAdapter(
        source_id="src_ts6_grid",
        file_path=SAMPLES_DIR / "regional_grid_sample.csv",
        shared_column_map={
            "station_id": "cell_id",
            "latitude": "lat",
            "longitude": "lon",
            "water_depth_m": "depth_m",
        },
        evidence_mappings=[
            EvidenceClassMapping(
                evidence_class="GRID", column_map={"abundance_value_original": "abundance_kg_m2"}
            ),
        ],
        is_open=True,
        observation_or_prediction="compiled",
        static_fields={"sample_method": "compiled", "abundance_unit_original": "kg_m2"},
    )


REAL_ADAPTER_BUILDERS: list[Callable[[], SourceAdapter]] = [
    build_boxcore_adapter,
    build_nodule_aggregate_adapter,
    build_dryad_chamber_adapter,
    build_ts6_grid_adapter,
]


def build_corpus(corpus: list[Observation] | None = None) -> list[Observation]:
    """Runs every real adapter's IngestionPipeline against the shared corpus,
    in REAL_ADAPTER_BUILDERS's fixed order. Safe to call more than once
    against the SAME corpus list: an adapter whose rows are already present
    is a no-op the second time (idempotency) — see DuplicateStationSpecification,
    which checks against this exact live corpus reference."""
    corpus = corpus if corpus is not None else []
    registry = build_default_registry()
    dedup_specification = DuplicateStationSpecification(corpus)
    for build_adapter in REAL_ADAPTER_BUILDERS:
        IngestionPipeline(
            adapter=build_adapter(),
            normalizers=registry,
            corpus=corpus,
            dedup_specification=dedup_specification,
        ).run()
    return corpus


def write_corpus_csv(corpus: list[Observation], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    """Deterministic, byte-identical-across-runs CSV: a fixed column order
    (the schema's own field order) and a stable sort key
    (source_id, source_record_id) — never left to adapter-run order or
    dict/set iteration."""
    sorted_corpus = sorted(corpus, key=lambda obs: (obs.source_id, obs.source_record_id))
    frame = pd.DataFrame(
        [obs.model_dump(mode="json") for obs in sorted_corpus],
        columns=_CSV_COLUMNS,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)


def main() -> None:
    corpus = build_corpus()
    write_corpus_csv(corpus)
    print(f"Wrote {len(corpus)} observations to {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
