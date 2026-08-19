"""Run the cross-validation comparison and write its RunManifest (E2.4 §3).

The command that produced the committed run artifact — so the numbers in
`docs/walkthroughs/E2.4.md` §3 are REGENERABLE, not transcribed:

    python -m engine.prospectivity.validation.run_cv <dem.tif> <output_dir> \\
        --dem-data-origin SYNTHETIC --seed 0

The DEM is an ARGUMENT (the `plot_stack.py` convention): this module is a
production path and never imports `tests.*`, so the synthetic fixture DEM is
supplied by the caller — and its declared origin travels into the feature
stack, through the training matrix's COMPUTED origin, into the run manifest's
`data_origin`, and out as the watermark. Omitting `--dem-data-origin` leaves
the origin undeclared, which watermarks (default-ON, P2.0d-3).

THE FOUR DESIGNS, in the order the report reads them (Karl's §1B decision):

    leave_one_cluster_out   the GEOMETRY measurement — how much the clusters
                            differ; cannot rank estimators (the theorem)
    leave_one_site_out      THE headline within-cluster gate, 4.6-10 km
    leave_one_station_out   sub-km within-site; declared unblocked; for RF
                            also the real-data leakage demonstration
    random_k_fold           the demonstrably-wrong comparison; declared
                            unblocked, refused by assert_claim_eligible

Nothing here decides anything: it composes the E2.0 matrix assembly, the
E2.1-E2.3 estimators and the E2.4 runner, and writes what they produce.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.estimators.registry import build_default_registry
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry as build_covariates
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.training_matrix import assemble_training_matrix
from engine.prospectivity.validation.runner import (
    CrossValidationRunner,
    emit_run_manifest,
    run_watermark,
)
from engine.prospectivity.validation.splitter import (
    LeaveOneStationOutSplitter,
    RandomKFoldSplitter,
    leave_one_cluster_out,
    leave_one_site_out,
)

GENERATOR = "engine.prospectivity.validation.run_cv"
MANIFEST_NAME = "run_manifest.json"
DEFAULT_RANDOM_K = 5


def build_splitters(*, random_k: int = DEFAULT_RANDOM_K, seed: int = 0) -> list:
    """The four designs. Random k-fold is seeded from the run seed so the
    "wrong comparison" is as reproducible as the right ones."""
    return [
        leave_one_cluster_out(),
        leave_one_site_out(),
        LeaveOneStationOutSplitter(),
        RandomKFoldSplitter(k=random_k, seed=seed),
    ]


def run_cross_validation(
    dem_path: Path,
    output_dir: Path,
    *,
    dem_data_origin: str | None = None,
    seed: int = 0,
    random_k: int = DEFAULT_RANDOM_K,
    run_id: str | None = None,
) -> tuple[RunManifest, Path]:
    """Assemble the matrix over `dem_path`, run every design, write the
    manifest into `output_dir`, and return both."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stack_dir = output_dir / "stack"
    written = build_covariate_stack(dem_path, stack_dir, dem_data_origin=dem_data_origin)
    stack_manifest = json.loads(written["provenance"].read_text())
    corpus_manifest = json.loads(
        (Path(__file__).resolve().parents[3] / "data" / "corpus" / "manifest.json").read_text()
    )
    grid = DemGrid.load(dem_path)
    layers = build_covariates().build_all(grid)
    matrix, matrix_manifest = assemble_training_matrix(
        CorpusCsvSampleSource(), grid, layers, corpus_manifest, stack_manifest
    )

    runner = CrossValidationRunner(
        splitters=build_splitters(random_k=random_k, seed=seed),
        registry=build_default_registry(),  # fresh instances per run (obligation 2)
    )
    report = runner.run(matrix, seed=seed)
    manifest = emit_run_manifest(
        report,
        matrix=matrix,
        matrix_manifest=matrix_manifest,
        run_id=run_id,
        generator=GENERATOR,
    )
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(manifest.to_json())
    return manifest, manifest_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dem_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--dem-data-origin",
        default=None,
        help=(
            "The DEM's DECLARED origin (a DataOrigin member name, e.g. SYNTHETIC). "
            "Omitted -> undeclared, which watermarks the run."
        ),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--random-k", type=int, default=DEFAULT_RANDOM_K)
    parser.add_argument("--run-id", default=None)
    arguments = parser.parse_args(argv)

    manifest, path = run_cross_validation(
        arguments.dem_path,
        arguments.output_dir,
        dem_data_origin=arguments.dem_data_origin,
        seed=arguments.seed,
        random_k=arguments.random_k,
        run_id=arguments.run_id,
    )
    watermark = run_watermark(manifest)
    print(f"wrote {path} ({path.stat().st_size / 1e6:.2f} MB)")
    print(f"  content_hash   {manifest.content_hash}")
    print(f"  data_origin    {manifest.data_origin}")
    print(f"  watermark      {watermark or 'none (clean)'}")
    print(f"  claim-eligible {manifest.claim_eligible_designs}")


if __name__ == "__main__":
    main()
