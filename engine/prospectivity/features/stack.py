"""build_covariate_stack — E1.4's deliverable orchestration.

Loads the DEM once, runs every enabled Contract 3 recipe through the
CovariateRegistry, and writes one GeoTIFF per covariate plus a single
provenance.json sidecar (sorted keys, no timestamps — byte-identical across
runs, same determinism bar as E1.3's corpus CSV).

Not a new pattern: this is glue over the registry, the way corpus_builder.py
is glue over IngestionPipeline. ProspectivityEngine's `feature_builder`
callable seam (engine.py) will wrap registry.build_all in Phase 2; this
module exists so E1.4's rasters/provenance can be produced and reviewed now.
"""

from __future__ import annotations

from typing import ClassVar

from pathlib import Path

import numpy as np
import rasterio
from pydantic import Field

from engine.prospectivity.features._contract import load_covariates_yaml
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.contract_versions import contract_versions
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins


class FeatureStackManifest(ProvenanceArtifact):
    """The features-stage provenance artifact (docs/contracts/PROVENANCE.md),
    written as `<stack dir>/provenance.json`.

    Refactored onto ProvenanceArtifact (2026-07-29) WITHOUT changing what it
    records: `contract`, `registry_version`, `dem` and `layers` are byte-for-
    byte the same content as the hand-built dict this replaces. The four
    shared chaining fields are ADDED. `registry_version` is kept at top level
    (existing readers and tests use it) even though `contract_versions` now
    also carries it — preserving what was recorded took precedence over
    de-duplicating it.

    Upstream is the DEM: a raw input rather than an artifact, so its hash is
    quoted in `upstream_hashes` under "dem" and a model run downstream can
    prove which terrain its features came from.

    HASH.1 commit 2 (2026-08-22, schema_version 2): `dem_path` — the path
    string the caller passed, recorded for a reader and EXCLUDED from the
    content hash (the `generated_at` precedent). Until this, the path sat
    inside `dem` and every `layers[i].dem`, nine times in the substance, so
    the same DEM bytes built from another directory — or by a relative
    rather than an absolute path in the same one — produced a different
    stack hash, and everything downstream quoted it (E2.4 audit row M; E3.4
    measured eleven moving hash values). The DEM's identity is its
    `content_hash`; the path never was one.
    """

    contract: str
    registry_version: int
    dem: dict = Field(default_factory=dict)
    layers: list[dict] = Field(default_factory=list)
    # P2.0c: the DEM's DECLARED origin (required at build; no silent default —
    # a default of SYNTHETIC would mislabel real GEBCO at Checkpoint 1, and a
    # default of None is the silent unknown the origin module forbids), and
    # the layers' composition COMPUTED from it: every layer is derived from
    # the one DEM, so each layer's origin is combine(DERIVED, dem origin) —
    # least-real wins, which is how features computed on a synthetic DEM stay
    # SYNTHETIC rather than laundering into DERIVED.
    dem_data_origin: str
    layers_by_data_origin: dict[str, int] = Field(default_factory=dict)
    # HASH.1 commit 2: where the DEM was read from — OUTSIDE the hash.
    dem_path: str | None = None

    HASH_EXCLUDED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"content_hash", "generated_at", "dem_path"}
    )
    # HASH.1: frozen field set (no stack manifest is committed; the set exists
    # so the rule is uniform and a future field cannot reach a legacy hash).
    # SCHEMA_VERSION 2 at commit 2: the shape gained `dem_path`.
    SCHEMA_VERSION: ClassVar[int] = 2
    LEGACY_HASHED_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "contract", "contract_versions", "dem", "dem_data_origin", "layers",
        "layers_by_data_origin", "registry_version", "upstream_hashes",
    })


def build_covariate_stack(
    dem_path: Path, output_dir: Path, *, dem_data_origin: DataOrigin | str
) -> dict[str, Path]:
    """Compute all enabled covariates from `dem_path`; write rasters +
    provenance.json under `output_dir`. Returns {layer_name: written_path,
    ..., "provenance": provenance_path}.

    `dem_data_origin` is the caller's DECLARATION of the DEM's origin
    (P2.0c) — required keyword, validated through DataOrigin so an unknown
    label raises. The synthetic fixture DEM is SYNTHETIC; real GEBCO at
    Checkpoint 1 declares its own class at the TerrainSource seam."""
    dem_origin = DataOrigin(dem_data_origin)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    grid = DemGrid.load(Path(dem_path))
    registry = build_default_registry()
    results = registry.build_all(grid)
    layer_origin = combine_origins([DataOrigin.DERIVED, dem_origin])

    written: dict[str, Path] = {}
    for result in results:
        layer_path = output_dir / f"{result.name}.tif"
        with rasterio.open(
            layer_path,
            "w",
            driver="GTiff",
            height=result.values.shape[0],
            width=result.values.shape[1],
            count=1,
            dtype="float32",
            crs=grid.crs,
            transform=grid.transform,
            nodata=np.nan,
        ) as dataset:
            dataset.write(result.values.astype(np.float32), 1)
        written[result.name] = layer_path

    manifest = FeatureStackManifest(
        contract="docs/contracts/covariates.yaml",
        registry_version=load_covariates_yaml()["registry_version"],
        dem=grid.provenance(),
        layers=[result.provenance for result in results],
        dem_data_origin=dem_origin.value,
        layers_by_data_origin={layer_origin.value: len(results)},
        contract_versions=contract_versions(),
        upstream_hashes={"dem": grid.content_hash},
        dem_path=str(dem_path),  # as given; outside the hash
    ).finalize()
    provenance_path = output_dir / "provenance.json"
    provenance_path.write_text(manifest.to_json())
    written["provenance"] = provenance_path
    return written
