"""E3.1+2 commit 3 — the COG writer and the three watermark carriers.

A GeoTIFF has no caption, so the non-scientific status is carried three ways
and each is mutation-tested SEPARATELY: a watermark with one carrier is one
deletion from silence.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.surfaces.writer import (
    ORIGIN_TAG,
    PUBLISHABLE_TAG,
    REFUSED_TAG,
    NO_REFUSALS,
    NO_WATERMARK,
    WATERMARK_TAG,
    compute_surface_origin,
    surface_watermark,
    write_surface,
)
from engine.prospectivity.validation.claim import ClaimVerdict, Precondition, evaluate_claim

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def built(surface_assembly) -> dict:
    return surface_assembly


@pytest.fixture(scope="module")
def refusing_verdict() -> ClaimVerdict:
    """E2.5's REAL verdict on the committed E2.4 run — a refusal, which is
    today's honest answer and the one this writer must mark."""
    manifest = RunManifest(
        **json.loads((REPO_ROOT / "data" / "runs" / "e2.4" / "run_manifest.json").read_text())
    )
    stack = {
        "layers": [
            {
                "name": name,
                "dem_sha256": "sha256:whatever",
                "dem_resolution_deg": [0.1, 0.1],
                "dem_crs": "EPSG:4326",
                "dem_shape": [34, 100],
                "dem_transform": [0.1, 0.0, -126.5, 0.0, -0.1, 14.7],
            }
            for name in ("depth", "slope")
        ]
    }
    return evaluate_claim(manifest, design="leave_one_site_out", feature_stack_manifest=stack)


def _write(tmp_path, built, verdict, origin=None):
    grid, surfaces = built["grid"], built["surfaces"]
    result = surfaces["ordinary_kriging"]
    origin = origin or compute_surface_origin("SYNTHETIC", "SYNTHETIC")
    return write_surface(result, grid, tmp_path, data_origin=origin, verdict=verdict), grid, result


# ────────────────────────────────────────────────── what the raster actually is


def test_the_written_raster_carries_every_field_e30_said_we_could_OBSERVE(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """E3.0 §3's decision, implemented literally: assert driver, tiled,
    block_shapes, overviews, CRS, transform, dtype and nodata — and CLAIM NO
    COG-NESS anywhere.

    The COG DRIVER is used (present at GDAL 3.9.2, no dependency). What is not
    asserted is that the result IS a valid COG, because nothing installed can
    check the IFD/byte-layout property that makes it one — rio_cogeo,
    osgeo.gdal and validate_cloud_optimized_geotiff are all unimportable. A
    test asserting the observable fields and calling that "COG-ness" would be
    a claim with a partial observer, which is the shape this project refuses.

    Note `overviews == []`: at 100x34 the driver generates none, exactly as
    E3.0 measured. That is recorded, not treated as a defect.
    """
    written, grid, _ = _write(tmp_path, built, refusing_verdict)
    with rasterio.open(written["prediction"]) as dataset:
        assert dataset.driver == "GTiff"  # a COG IS a GeoTIFF on read
        assert dataset.profile["tiled"] is True
        assert dataset.block_shapes == [(512, 512)]
        assert dataset.overviews(1) == []
        assert dataset.crs.to_string() == grid.crs
        assert tuple(dataset.transform)[:6] == grid.transform
        assert dataset.dtypes == ("float32",)
        assert np.isnan(dataset.nodata)
        assert (dataset.width, dataset.height) == (grid.width, grid.height)
        assert "cog" not in json.dumps(dataset.tags()).lower(), (
            "the tags must not claim COG-ness — nothing here can validate it"
        )


def test_round_trip_preserves_values_georeferencing_and_the_mask(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """Reading the file back gives the same surface. float32 is the storage
    dtype, so values are compared at float32 precision — and the MASK is
    compared exactly, because a NaN that survived as a number would be a
    prediction invented at a cell with no inputs."""
    written, grid, result = _write(tmp_path, built, refusing_verdict)
    for kind, expected in (("prediction", result.mu), ("uncertainty", result.sd)):
        with rasterio.open(written[kind]) as dataset:
            back = dataset.read(1)
            assert tuple(dataset.transform)[:6] == grid.transform
        np.testing.assert_array_equal(np.isnan(back), np.isnan(expected))
        finite = ~np.isnan(expected)
        np.testing.assert_allclose(back[finite], expected[finite], rtol=0, atol=1e-6)


# ───────────────────────────────────────────── the three carriers, separately


def test_carrier_1_the_geotiff_tags_carry_origin_watermark_and_the_refusal(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """CARRIER 1. A consumer meets this file through GDAL, not through a
    caption, so the tags must say what it is."""
    written, _, _ = _write(tmp_path, built, refusing_verdict)
    for kind in ("prediction", "uncertainty"):
        with rasterio.open(written[kind]) as dataset:
            tags = dataset.tags()
        assert tags[ORIGIN_TAG] == "SYNTHETIC"
        assert "NON-SCIENTIFIC" in tags[WATERMARK_TAG]
        assert tags[PUBLISHABLE_TAG] == "false"
        assert Precondition.PRE_REGISTERED_THRESHOLD.value in tags[REFUSED_TAG]
        assert tags["surface_kind"] == kind


def test_carrier_2_the_sidecar_records_the_same_facts_beside_the_file(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """CARRIER 2. Tags travel inside the raster; a sidecar survives a
    conversion that drops them, and is what the origin audit can read."""
    written, _, _ = _write(tmp_path, built, refusing_verdict)
    sidecar = json.loads(written["provenance"].read_text())
    assert sidecar["data_origin"] == "SYNTHETIC"
    assert "NON-SCIENTIFIC" in sidecar["watermark"]
    assert sidecar["publishable"] is False
    assert sidecar["claim_eligible"] is False
    assert Precondition.PRE_REGISTERED_THRESHOLD.value in sidecar["claim_failing_preconditions"]
    assert sidecar["grid"]["n_masked"] == 520
    assert sidecar["surface"]["estimator_name"] == "ordinary_kriging"


def test_carrier_3_an_ineligible_claim_is_written_but_MARKED_not_refused(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """CARRIER 3 — E2.5's guard consulted AT WRITE TIME, which is what makes
    it load-bearing rather than a thing that only runs in tests.

    Building on fixtures is legitimate, so the file IS written; PUBLISHING
    from fixtures is what the guard prevents, so it is written MARKED. Both
    halves matter: an exception here would stop legitimate work, and an
    unmarked file would be the laundering the guard exists to catch.
    """
    assert refusing_verdict.eligible is False
    written, _, _ = _write(tmp_path, built, refusing_verdict)
    assert written["prediction"].exists() and written["uncertainty"].exists()
    with rasterio.open(written["prediction"]) as dataset:
        assert dataset.tags()[PUBLISHABLE_TAG] == "false"
        assert dataset.tags()[REFUSED_TAG], "the failing preconditions must be NAMED, not implied"


def test_an_eligible_claim_on_measured_lineage_writes_clean_with_no_watermark(
    tmp_path: Path, built: dict
) -> None:
    """THE POSITIVE CONTROL, and the separating case. Without it every
    assertion above would be satisfied by a writer that stamped
    NON-SCIENTIFIC unconditionally — which would pass while telling a future
    reader nothing."""
    eligible = ClaimVerdict(
        design="leave_one_site_out", results=(), watermark=None, data_origin="MEASURED"
    )
    written, _, _ = _write(tmp_path, built, eligible, origin=DataOrigin.MEASURED)
    with rasterio.open(written["prediction"]) as dataset:
        tags = dataset.tags()
    assert tags[ORIGIN_TAG] == "MEASURED"
    assert tags[PUBLISHABLE_TAG] == "true"
    # THE TAGS ARE PRESENT AND EXPLICIT, never empty: GDAL drops empty-string
    # tags, so a clean surface would read back with the tag ABSENT —
    # indistinguishable from a file written before the tag existed.
    assert tags[WATERMARK_TAG] == NO_WATERMARK
    assert tags[REFUSED_TAG] == NO_REFUSALS
    assert json.loads(written["provenance"].read_text())["publishable"] is True


# ──────────────────────────────────────────────────── the origin is COMPUTED


def test_the_origin_is_computed_from_inputs_and_a_real_corpus_cannot_launder_a_synthetic_dem() -> None:
    """THE LAUNDERING CHECK. `combine_origins` returns the LEAST-REAL input,
    so a surface whose target came from a MEASURED corpus but whose covariates
    came from a SYNTHETIC DEM is SYNTHETIC — the whole point of computing the
    origin rather than declaring it.

    Both directions are asserted: mixing does not promote, and a genuinely
    all-MEASURED lineage is not gratuitously demoted."""
    assert compute_surface_origin("SYNTHETIC", "MEASURED") is DataOrigin.SYNTHETIC
    assert compute_surface_origin("MEASURED", "SYNTHETIC") is DataOrigin.SYNTHETIC
    assert compute_surface_origin("DERIVED", "MEASURED") is DataOrigin.DERIVED
    assert compute_surface_origin("MEASURED", "MEASURED") is DataOrigin.MEASURED


def test_the_watermark_is_default_on_absence_of_proof_never_renders_clean() -> None:
    """`watermark UNLESS proven`, not `watermark IF synthetic` (P2.0d-3). The
    None case is the one a negative rule would let through, so it is asserted
    first."""
    assert surface_watermark(None) is not None and "UNRECORDED" in surface_watermark(None)
    for origin in (DataOrigin.SYNTHETIC, DataOrigin.AUTHORED, DataOrigin.LITERATURE, DataOrigin.DERIVED):
        assert surface_watermark(origin) is not None, origin
    assert surface_watermark(DataOrigin.MEASURED) is None


# ──────────────────────────────────── TAX.1 commit 2: the rasters' own origin


def test_the_rasters_are_classified_by_the_audits_own_sidecar_mechanism(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """THE .tif FILES WERE UNCLASSIFIED, and this closes it with the
    ESTABLISHED mechanism rather than a new one.

    A GeoTIFF cannot carry an in-file declaration without changing its bytes —
    which would break the hash it is pinned by (the P2.0c marker-form rule) —
    so the marker is `data_origin.yaml`, the same sidecar
    `tests/fixtures/samples/` and `data/corpus/` already use. **The
    association is one the AUDIT RESOLVES**: a `files:` mapping keyed by
    filename, read by `_sidecar_declaration`, not an inference from adjacent
    names.
    """
    import yaml

    written, _, _ = _write(tmp_path, built, refusing_verdict)
    sidecar = written["origin_sidecar"]
    assert sidecar.name == "data_origin.yaml"
    files = yaml.safe_load(sidecar.read_text())["files"]

    for kind in ("prediction", "uncertainty"):
        entry = files[written[kind].name]
        assert entry["data_origin"] == "SYNTHETIC"
        assert entry["generator"] == "engine.prospectivity.surfaces.builder.build_surfaces"
        # kriging is SEEDLESS, so the evidence is the determinism basis —
        # TAX.1's whole point
        assert "seed" not in entry
        assert len(entry["determinism_basis"]) >= 40


def test_a_second_estimators_rasters_do_not_un_classify_the_first(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """Every estimator writes into the SAME directory, so the sidecar is
    MERGED, not overwritten. A writer that replaced it would classify its own
    rasters and silently un-classify the previous estimator's — and the
    audit would then report the earlier files as unclassified, blaming the
    wrong commit."""
    import yaml

    grid, surfaces = built["grid"], built["surfaces"]
    origin = compute_surface_origin("SYNTHETIC", "SYNTHETIC")
    for name in ("ordinary_kriging", "random_forest"):
        write_surface(
            surfaces[name], grid, tmp_path, data_origin=origin, verdict=refusing_verdict
        )
    files = yaml.safe_load((tmp_path / "data_origin.yaml").read_text())["files"]
    assert set(files) == {
        "ordinary_kriging_prediction.tif",
        "ordinary_kriging_uncertainty.tif",
        "random_forest_prediction.tif",
        "random_forest_uncertainty.tif",
    }
    # AND the two estimators evidence themselves DIFFERENTLY, which is the
    # seed-OR-basis rule doing real work rather than one branch serving both:
    assert "determinism_basis" in files["ordinary_kriging_prediction.tif"]
    assert files["random_forest_prediction.tif"]["seed"] == 0
    assert "determinism_basis" not in files["random_forest_prediction.tif"], (
        "a seed is the stronger evidence; recording both invites them to disagree"
    )


def test_a_surface_whose_estimator_can_evidence_neither_is_refused_by_name(
    tmp_path: Path, built: dict, refusing_verdict: ClaimVerdict
) -> None:
    """An artifact whose reproducibility cannot be evidenced is not labelled
    SYNTHETIC and waved through."""
    import dataclasses

    result = dataclasses.replace(
        built["surfaces"]["ordinary_kriging"], determinism_basis=None
    )
    with pytest.raises(ValueError, match="neither a recorded seed nor a declared"):
        write_surface(
            result,
            built["grid"],
            tmp_path,
            data_origin=compute_surface_origin("SYNTHETIC", "SYNTHETIC"),
            verdict=refusing_verdict,
        )
