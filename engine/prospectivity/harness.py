"""The run harness — ONE COMMAND that runs the full pipeline into a named
directory and produces every artifact the viewer reads (E5.5 commit 1).

    python -m engine.prospectivity.harness \\
        --dem <dem.tif> --dem-data-origin SYNTHETIC \\
        --ts6 <ts6.tif> --ts6-data-origin SYNTHETIC \\
        --out runs/<name> [--run-id <id>] [--seed 0] \\
        [--designs leave_one_cluster_out,leave_one_site_out,leave_one_station_out,random_k_fold] \\
        [--claim-design leave_one_site_out]

TRIPWIRE RESULT (inventoried before building): `ProspectivityEngine.run()`
already sequences everything — ingest → features → CV → manifest → claim →
surfaces → write → TS-6 → economics → extend. This module adds an ENTRY
POINT, an OUTPUT PATH, a REGISTRY CHOICE and nothing that computes. What
leaked, stated rather than absorbed: the composition needs a TerrainSource
and a TS6Reference, and until E5.5 neither seam had a non-test
implementation — `FileTerrainSource` and `FileTS6Reference` are the two
thin, caller-declared-origin Strategies this commit adds beside the
fixtures (PATTERNS.md §3.2's last zero-implementation rows).

    ┌──────────────── harness.main(argv) ─────────────────┐
    │  FileTerrainSource(dem, origin)   CorpusCsvSampleSource│
    │  FileTS6Reference(ts6, origin)    StackFeatureBuilder  │
    │  build_default_registry()  ◄── THE PRODUCTION REGISTRY │
    │  CrossValidationRunner(designs)   CutoffEconomicModel  │
    │  scenarios() · difference_pairs() · the AOI feature    │
    └────────────────┬───────────────────────────────────────┘
                     ▼
          ProspectivityEngine.run()  (unchanged Template Method)
                     ▼
     <out>/run_manifest.json · <out>/*_prediction|uncertainty.tif ·
     <out>/*.provenance.json · <out>/data_origin.yaml ·
     <out>/economics/ (18 rasters + record + sidecar) ·
     <out>/features/stack/ (the 8 covariates + provenance.json)

THE REGISTRY IS A DECISION THIS COMMAND MAKES, and E5.0 measured that it
matters: the e2e test's light registry (40 trees) gives an RF surface of
[14.982, 22.041] with 1,218 distinct values; the production registry (500
trees, five importance seeds) gives [15.091, 21.681] with 1,842 — the
values E3.1+2 pinned. Whichever runs is what a public viewer shows, so
this command offers ONLY `build_default_registry()`: a light configuration
is a test fixture, and a fixture in a deliverable is the leak E5.0 named.
The choice is VERIFIABLE in the record, not only stated here: every fold's
`provenance.n_estimators` is read back from the fitted forest (E2.3), so a
run built by the light registry reads 40 where this one reads 500.

MEASURED COST (E5.5 commit 1, this machine): light registry 2.7 s; the
production registry 31.9 s over three designs and 107.9 s over all four
(leave-one-station-out's 35 folds are the difference). The RF surface is
a full-data fit and is identical across design sets. The default is the
full four-design set E2.4's committed run used; `--designs` narrows it.

THE INPUTS ARE PASSED IN, NEVER GENERATED HERE, and their origins are the
CALLER'S DECLARATIONS — the rule `features/plot_stack.py` wrote for the
E1.4 deliverable ("never generates one and never imports tests.*"). The
only DEM and TS-6 rasters that exist today are synthetic and are written
by `tests/fixtures/rasters.py`; the walkthrough records the two-line
command that produces them. At Checkpoint 1 / 3 the real files replace
them with a different declaration and the same command.

THE OUTPUT DIRECTORY IS ONE RUN. It must not exist or must be empty —
two runs written into one directory would leave the manifest's full
listing describing a mixture (the property E4.2's misplaced rasters were
caught by), so the refusal is by name, before anything is computed.

DETERMINISM IS THIS COMMAND'S OWN PROPERTY: the same inputs at the same
seed in two different trees produce the same substance and the same
content_hash (tests/test_run_harness.py measures it in two trees rather
than reasoning about it — HASH.1's path fix was itself first reintroduced
one layer up and caught only by measurement).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.economics.contract import difference_pairs, scenarios
from engine.prospectivity.economics.cutoff import CutoffEconomicModel
from engine.prospectivity.engine import ProspectivityEngine
from engine.prospectivity.estimators.registry import build_default_registry
from engine.prospectivity.features.bundle import StackFeatureBuilder
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.terrain.file_source import FileTerrainSource
from engine.prospectivity.ts6.file_reference import FileTS6Reference
from engine.prospectivity.validation.runner import CrossValidationRunner
from engine.prospectivity.validation.splitter import (
    FoldSplitter,
    LeaveOneStationOutSplitter,
    RandomKFoldSplitter,
    leave_one_cluster_out,
    leave_one_site_out,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = "features"  # <out>/features/stack/ — the StackFeatureBuilder's layout

# ─────────────────────────────────────────── E5.5 commit 3: THE RUN DIRECTORY AS A PRODUCT
# A human and an API both read this directory, so its layout is stated as a
# contract-shaped thing: what exists, where, and WHAT RESOLVES WHAT. The
# rule is E4.2's — resolution comes from a RECORD, never from a filename;
# the names below are readable, and nothing downstream may parse them.
#
#   <out>/
#   ├── run_manifest.json                 THE ROOT RECORD (RunManifest, schema 4): hashes every
#   │                                     file in output_hashes (basename; economics/<basename>),
#   │                                     names each surface's rasters + sidecar (surfaces.*),
#   │                                     every economics raster (economics.rasters), the claim
#   │                                     verdicts, the training stations, the full-data fits
#   ├── <estimator>_prediction.tif        paired surfaces (E3.1+2) — resolved by surfaces[est].rasters
#   ├── <estimator>_uncertainty.tif         (never from the name); the pair is structural
#   ├── <estimator>.provenance.json       carrier 2: the surface's sidecar — surfaces[est].sidecar
#   ├── data_origin.yaml                  the origin audit's marker for the surface rasters
#   ├── economics/
#   │   ├── footprint__<scenario>__<estimator>__z<z>.tif      12 — resolved by economics.footprints.json
#   │   ├── difference__<a>__<b>__<estimator>__z<z>.tif        6 — (kind, scenario/pair, estimator, z, sha256)
#   │   ├── economics.footprints.json     E4.2's association record — hashed into the chain (E4.3)
#   │   └── data_origin.yaml              the audit's marker for the economics rasters
#   └── features/stack/                   the covariate stack the surfaces were predicted on:
#       ├── <covariate>.tif  × 8            NOT in output_hashes — its identity is the stack's
#       └── provenance.json                 content_hash, quoted by upstream_hashes.feature_stack,
#                                           prediction_grid.stack_content_hash and every raster's tags
#
# The inputs (the DEM, the TS-6 raster) are NOT inside: they are wherever
# the caller keeps them, and the record identifies them by content hash
# (upstream_hashes / provenance_chain.links.*), never by path — HASH.1.
RUN_LAYOUT: dict[str, str] = {
    "run_manifest.json": "the root record; resolves everything below",
    "<estimator>_prediction.tif": "surfaces[<estimator>].rasters.prediction (file + sha256)",
    "<estimator>_uncertainty.tif": "surfaces[<estimator>].rasters.uncertainty (file + sha256)",
    "<estimator>.provenance.json": "surfaces[<estimator>].sidecar (file + sha256)",
    "data_origin.yaml": "output_hashes['data_origin.yaml']; the audit's marker for the rasters beside it",
    "economics/*.tif": "economics.rasters[<basename>] via economics.footprints.json (kind, scenario|pair, estimator, z, sha256)",
    "economics/economics.footprints.json": "economics.association (file + sha256); output_hashes['economics/…']",
    "economics/data_origin.yaml": "output_hashes['economics/data_origin.yaml']; the audit's marker for the economics rasters",
    "features/stack/*": "NOT hashed per file: identified as one artifact by the stack manifest's content_hash, quoted throughout",
}
STACK_DIR = f"{FEATURES_DIR}/stack"
DEFAULT_AOI = REPO_ROOT / "data" / "aoi" / "study_area.geojson"

# E2.4's committed design set, in its order. random_k_fold takes the run's
# seed; the three spatial designs are seedless.
DESIGN_FACTORIES = {
    "leave_one_cluster_out": lambda seed: leave_one_cluster_out(),
    "leave_one_site_out": lambda seed: leave_one_site_out(),
    "leave_one_station_out": lambda seed: LeaveOneStationOutSplitter(),
    "random_k_fold": lambda seed: RandomKFoldSplitter(k=5, seed=seed),
}
DEFAULT_DESIGNS: tuple[str, ...] = tuple(DESIGN_FACTORIES)
DEFAULT_CLAIM_DESIGN = "leave_one_site_out"  # E2.4's headline within-cluster gate


def load_study_area(path: Path | str = DEFAULT_AOI) -> StudyArea:
    """Contract 2's AOI feature — the committed placeholder until the AOI
    decision (BACKLOG §1); read, never invented here."""
    raw = json.loads(Path(path).read_text())
    features = raw.get("features") or []
    if len(features) != 1:
        raise ValueError(f"{path} holds {len(features)} features; the study area is exactly one")
    return StudyArea.from_geojson_feature(features[0])


def build_designs(names: Sequence[str], *, seed: int) -> list[FoldSplitter]:
    unknown = [n for n in names if n not in DESIGN_FACTORIES]
    if unknown:
        raise ValueError(f"unknown design(s) {unknown}; known: {list(DESIGN_FACTORIES)}")
    if len(set(names)) != len(names):
        raise ValueError(f"designs repeat: {list(names)}")
    return [DESIGN_FACTORIES[n](seed) for n in names]


def require_empty_output_dir(out: Path) -> Path:
    out = Path(out)
    if out.exists():
        if not out.is_dir():
            raise ValueError(f"--out {out} exists and is not a directory")
        if any(out.iterdir()):
            raise ValueError(
                f"--out {out} is not empty — a run directory holds ONE run (the manifest's "
                "file listing describes everything beside it); choose a new directory"
            )
    return out


def build_engine(
    *,
    dem: Path | str,
    dem_data_origin: DataOrigin | str | None,
    ts6: Path | str,
    ts6_data_origin: DataOrigin | str | None,
    out: Path | str,
    seed: int = 0,
    run_id: str | None = None,
    designs: Sequence[str] = DEFAULT_DESIGNS,
    claim_design: str = DEFAULT_CLAIM_DESIGN,
    aoi: Path | str = DEFAULT_AOI,
) -> ProspectivityEngine:
    """The production composition, assembled — every collaborator the real
    one; the registry `build_default_registry()` and nothing else."""
    out = require_empty_output_dir(Path(out))
    registry = build_default_registry()  # ONE instance: the engine refuses a runner on another
    return ProspectivityEngine(
        study_area=load_study_area(aoi),
        terrain_source=FileTerrainSource(dem, data_origin=dem_data_origin),
        sample_source=CorpusCsvSampleSource(),
        feature_builder=StackFeatureBuilder(out / FEATURES_DIR),
        cv_runner=CrossValidationRunner(splitters=build_designs(designs, seed=seed), registry=registry),
        estimators=registry,
        ts6_reference=FileTS6Reference(ts6, data_origin=ts6_data_origin),
        economic_model=CutoffEconomicModel(),
        scenario_configs=scenarios(),
        difference_pairs=difference_pairs(),
        output_dir=out,
        claim_design=claim_design,
        seed=seed,
        run_id=run_id,
    )


def run(**kwargs) -> RunManifest:
    return build_engine(**kwargs).run()


def _parser() -> argparse.ArgumentParser:
    origins = [m.value for m in DataOrigin]
    p = argparse.ArgumentParser(prog="python -m engine.prospectivity.harness", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dem", type=Path, required=True, help="bathymetry GeoTIFF, EPSG:4326")
    p.add_argument("--dem-data-origin", required=True, choices=origins,
                   help="the DEM's DECLARED origin (SYNTHETIC for the test generator's raster; MEASURED for real GEBCO)")
    p.add_argument("--ts6", type=Path, required=True, help="TS-6 benchmark GeoTIFF")
    p.add_argument("--ts6-data-origin", required=True, choices=origins,
                   help="the TS-6 raster's DECLARED origin (SYNTHETIC today; DERIVED for G3.1's digitization)")
    p.add_argument("--out", type=Path, required=True, help="the run directory (absent or empty)")
    p.add_argument("--run-id", default=None, help="recorded, outside the hash; a uuid4 when omitted")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--designs", default=",".join(DEFAULT_DESIGNS),
                   help=f"comma-separated subset of {list(DESIGN_FACTORIES)} (default: all four, E2.4's set)")
    p.add_argument("--claim-design", default=DEFAULT_CLAIM_DESIGN)
    p.add_argument("--aoi", type=Path, default=DEFAULT_AOI)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    a = _parser().parse_args(argv)
    manifest = run(
        dem=a.dem, dem_data_origin=a.dem_data_origin, ts6=a.ts6, ts6_data_origin=a.ts6_data_origin,
        out=a.out, seed=a.seed, run_id=a.run_id, designs=[d for d in a.designs.split(",") if d],
        claim_design=a.claim_design, aoi=a.aoi,
    )
    failing = {
        d: [p["precondition"] for p in v["preconditions"] if not p["passed"]]
        for d, v in manifest.claim["verdicts"].items()
    }
    rf_trees = sorted({
        r["provenance"].get("n_estimators")
        for d in manifest.cross_validation["designs"] for r in d["results"]
        if r["estimator_name"] == "random_forest" and r.get("provenance")
    })
    print(f"run_id        {manifest.run_id}")
    print(f"content_hash  {manifest.content_hash}")
    print(f"out           {a.out}")
    print(f"data_origin   {manifest.data_origin}  (every output watermarked; publishable: "
          f"{sorted({s['publishable'] for s in manifest.surfaces.values()})})")
    print(f"registry      {manifest.inputs['registry']}  RF n_estimators read back per fold: {rf_trees}")
    print(f"designs       {[d['name'] for d in manifest.cross_validation['designs']]}  claim design: {manifest.claim['design']}")
    for design, names in failing.items():
        print(f"claim verdict {design}: {'ELIGIBLE' if manifest.claim['verdicts'][design]['eligible'] else 'REFUSED'} "
              f"— failing {names}")
    print(f"output files  {len(manifest.output_hashes)} hashed + {FEATURES_DIR}/stack/ + run_manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
