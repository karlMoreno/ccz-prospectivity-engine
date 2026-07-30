"""corpus_builder — Phase 1, E1.3's corpus-assembly entry point: wires every
real SourceAdapter through IngestionPipeline (fetch->adapt->normalize->
validate->dedup->append), using the E1.2 NormalizerRegistry and the E1.3
DuplicateStationSpecification, into ONE shared corpus written to
data/corpus/master_observations.csv.

    build_boxcore()  ──┐
    build_nodules()  ──┴──► IngestionPipeline(adapter, registry, corpus, dedup) ──► corpus
                              (same registry + same dedup Specification instance
                               shared across every adapter's run)

Adapter run ORDER is part of the contract, not incidental: survivor
precedence ties (dedup_rules.py: equal quality_grade) go to whichever row was
accepted first, so re-ordering REAL_ADAPTER_BUILDERS can change which row of
a genuine duplicate pair survives.

Deliberately excludes src_washburn2021_grid [19] (GRID+GRADE): the GRADE
station join (`join_tolerance_km`) is unresolved geology input and out of
scope for E1.3 (per the engineer of record's explicit instruction — GRADE
rows pass through unjoined wherever they occur, but nothing here manufactures
one). [01] and [05] both read their REAL downloaded PANGAEA files (D5/D8,
2026-07-27 review), living under data/sources/, not tests/fixtures/ —
`_require_production_path` enforces that distinction structurally (P1,
2026-07-27 audit follow-up).

**The corpus is single-source until Track G delivers** (P1b, 2026-07-27
audit follow-up): src_dryad_chamber [06] and src_ts6_grid [18] are BOTH
deliberately NOT wired — both still pointed at E1.1 placeholder fixtures
(round coordinates, fake dates for [06]; a synthetic grid for [18]), and
calling either builder directly now raises rather than silently admitting
fabricated data into a published, citable corpus (see each builder's own
docstring). Every row in the corpus today comes from [01]+[05], merged
under src_so268_boxcore. Real Dryad data and real TS-6 digitization
(Contract 6 / ts6_reference.yaml, Track G, Checkpoint 3) are both
prerequisites for re-wiring their sources, not just a path fix.

Known limitation: dedup only catches a candidate that duplicates a row
ALREADY in the corpus (from an earlier adapter in this list, or an earlier
call to build_corpus() against the same corpus list) — two duplicate rows
arriving in the SAME adapter's own single batch would not catch each other.
None of the wired sources' sample data has that shape today.
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
from engine.prospectivity.provenance.corpus_manifest import (
    CorpusManifest,
    build_corpus_manifest,
    write_corpus_manifest,
)
from engine.prospectivity.provenance.recorder import PipelineObserver, ProvenanceRecorder

REPO_ROOT = find_repo_root(Path(__file__).resolve())
SAMPLES_DIR = REPO_ROOT / "tests" / "fixtures" / "samples"
SOURCES_DIR = REPO_ROOT / "data" / "sources"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "data" / "corpus" / "master_observations.csv"

# The written CSV's column order: the master schema's own field order
# (Observation.model_fields mirrors docs/contracts/master_observations
# .schema.json field-for-field), never left to dict/set iteration order.
_CSV_COLUMNS = list(Observation.model_fields.keys())

_FIXTURES_PATH_PARTS = {"tests", "fixtures"}


def _require_production_path(path: Path) -> Path:
    """P1 (2026-07-27 audit follow-up): corpus_builder is a PRODUCTION entry
    point — it must never silently read a test fixture as though it were
    real data. This is the guard the dryad_chamber bug should have tripped:
    a hand-typed placeholder (round coordinates, sequential fake dates, a
    uniform footprint) was wired here with is_open=True and entered the
    published, citable corpus indistinguishable from a real observation.

    A structural check on the path's shape, not a naming convention someone
    has to remember — raises loudly at adapter-construction time. If a real
    source has no real data yet, the fix is to remove its builder from
    REAL_ADAPTER_BUILDERS, not to point it at a fixture and hope no one
    notices."""
    if _FIXTURES_PATH_PARTS <= {part.lower() for part in path.parts}:
        raise ValueError(
            f"corpus_builder refuses to read a test fixtures path in production: {path}. "
            "If this source has no real data yet, remove its builder from "
            "REAL_ADAPTER_BUILDERS instead of pointing it at a fixture."
        )
    return path


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
        file_path=_require_production_path(
            SOURCES_DIR / "SO268-bc-nodules-summary-PANGAEA-904967.tab"
        ),
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
        file_path=_require_production_path(SOURCES_DIR / "SO268-bc-nodules-PANGAEA-904962.tab"),
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
    """src_dryad_chamber [06] — MASS, chamber footprint as sampled_area_m2.

    NOT wired into REAL_ADAPTER_BUILDERS (P1, 2026-07-27 audit follow-up):
    no real Dryad download exists yet. This function still points at the
    E1.1 placeholder fixture on purpose — _require_production_path makes it
    raise if called, so re-adding it to REAL_ADAPTER_BUILDERS without also
    fixing this path fails loudly instead of quietly re-admitting fabricated
    data (the exact bug this cleanup exists to fix: three hand-typed rows
    with round coordinates and a uniform footprint were is_open=True and
    training-eligible in the published corpus)."""
    return TabularFileAdapter(
        source_id="src_dryad_chamber",
        file_path=_require_production_path(SAMPLES_DIR / "dryad_chamber_sample.csv"),
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
    """src_ts6_grid [18] — GRID, compiled/benchmark, never a training station.

    NOT wired into REAL_ADAPTER_BUILDERS (P1b, 2026-07-27 audit follow-up):
    real TS-6 digitization (Contract 6, ts6_reference.yaml) is a Track G
    deliverable that doesn't exist yet — this function still points at the
    E1.1 placeholder fixture on purpose. Same fix as src_dryad_chamber [06]
    got in P1: _require_production_path makes calling this builder directly
    raise rather than silently re-admitting fabricated data into a
    published, citable corpus. GRID rows can never be training-eligible
    (evidence_class != MASS), so this was lower-severity than [06]'s bug,
    but it's still synthetic data that doesn't belong in a corpus described
    as real."""
    return RegionalGridAdapter(
        source_id="src_ts6_grid",
        file_path=_require_production_path(SAMPLES_DIR / "regional_grid_sample.csv"),
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
    # build_dryad_chamber_adapter is deliberately NOT wired (P1, 2026-07-27
    # audit follow-up): no real Dryad download exists yet; see its own
    # docstring for why re-adding it here without a real file_path fails
    # loudly rather than quietly re-admitting fabricated data.
    #
    # build_ts6_grid_adapter is deliberately NOT wired either (P1b,
    # 2026-07-27 audit follow-up): no real digitized TS-6 file exists yet
    # (Track G deliverable, Contract 6 / ts6_reference.yaml); see its own
    # docstring. The corpus is single-source ([01]+[05] merged, under
    # src_so268_boxcore) until Track G delivers real Dryad or TS-6 data.
]


def build_corpus(
    corpus: list[Observation] | None = None,
    adapter_builders: list[Callable[[], SourceAdapter]] | None = None,
    observer: PipelineObserver | None = None,
) -> list[Observation]:
    """Runs every real adapter's IngestionPipeline against the shared corpus,
    in REAL_ADAPTER_BUILDERS's fixed order by default. Safe to call more than
    once against the SAME corpus list: an adapter whose rows are already
    present is a no-op the second time (idempotency) — see
    DuplicateStationSpecification, which checks against this exact live
    corpus reference.

    `adapter_builders` (P2, 2026-07-27 audit follow-up) is a testability
    hook, not a production knob — production always uses the default. It
    exists so test_corpus_builder.py can run the REAL production code path
    with REAL_ADAPTER_BUILDERS reversed, to prove survivorship is actually
    order-independent, rather than re-implementing this loop in the test and
    risking it drifting from what production really does.

    `observer` (OBSERVER, provenance/recorder.py) is optional and defaults to
    nothing being recorded. Pass a ProvenanceRecorder to collect the per-source
    accounting `build_corpus_with_manifest()` turns into
    data/corpus/manifest.json. Recording never changes what this function
    returns — see test_corpus_manifest.py's no-op test."""
    corpus = corpus if corpus is not None else []
    builders = adapter_builders if adapter_builders is not None else REAL_ADAPTER_BUILDERS
    registry = build_default_registry()
    dedup_specification = DuplicateStationSpecification(corpus)
    for build_adapter in builders:
        IngestionPipeline(
            adapter=build_adapter(),
            normalizers=registry,
            corpus=corpus,
            dedup_specification=dedup_specification,
            observer=observer,
        ).run()
    return corpus


def build_corpus_with_manifest(
    adapter_builders: list[Callable[[], SourceAdapter]] | None = None,
    corpus_path: Path = DEFAULT_OUTPUT_PATH,
) -> tuple[list[Observation], CorpusManifest]:
    """build_corpus() + the ingestion-stage provenance artifact.

    Adapters are constructed ONCE here and reused, so the manifest hashes the
    same input files the build actually read rather than re-deriving them."""
    builders = adapter_builders if adapter_builders is not None else REAL_ADAPTER_BUILDERS
    adapters = [build_adapter() for build_adapter in builders]
    recorder = ProvenanceRecorder()
    corpus: list[Observation] = []
    registry = build_default_registry()
    dedup_specification = DuplicateStationSpecification(corpus)
    for adapter in adapters:
        IngestionPipeline(
            adapter=adapter,
            normalizers=registry,
            corpus=corpus,
            dedup_specification=dedup_specification,
            observer=recorder,
        ).run()
    manifest = build_corpus_manifest(
        corpus=corpus, recorder=recorder, adapters=adapters, corpus_path=corpus_path
    )
    return corpus, manifest


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
    corpus, manifest = build_corpus_with_manifest()
    write_corpus_csv(corpus)
    write_corpus_manifest(manifest)
    print(f"Wrote {len(corpus)} observations to {DEFAULT_OUTPUT_PATH}")
    print(
        f"  {manifest.training_eligible_count} training-eligible; "
        f"sources: {', '.join(manifest.contributing_sources)}"
    )


if __name__ == "__main__":
    main()
