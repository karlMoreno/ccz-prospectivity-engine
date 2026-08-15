"""TrainingMatrix assembly + TrainingMatrixManifest, the fourth provenance
artifact (E2.0-3): determinism, chaining, the target's identity in the
hash, the computed origin, the derived watermark, and the NaN refusal.

Real-path tests build the actual stack artifact (build_covariate_stack →
provenance.json) over the synthetic DEM and read the committed corpus
manifest — upstream hashes are compared against those ACTUAL artifacts,
never against literals. Constructed-path tests (NaN refusal) use the E2.0-2
border-station shape with a FixtureSampleSource, because zero real stations
hit a border cell today (pinned in test_covariate_extraction.py).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.features.stack import build_covariate_stack
from engine.prospectivity.model_config import DeclaredField
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.training_matrix import (
    TrainingMatrix,
    assemble_training_matrix,
    matrix_watermark,
)
from tests.fixtures.rasters import write_synthetic_bathymetry, write_test_raster
from tests.fixtures.sample_source import FixtureSampleSource

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_MANIFEST_PATH = REPO_ROOT / "data" / "corpus" / "manifest.json"

WEST, NORTH, RES = -126.5, 14.7, 0.1  # the synthetic-DEM frame (rasters.py)


@pytest.fixture(scope="module")
def real_assembly(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """The production shape end to end: real corpus + synthetic-DEM stack
    artifact, assembled once and shared read-only across tests."""
    tmp = tmp_path_factory.mktemp("stack")
    dem_path = tmp / "dem.tif"
    write_synthetic_bathymetry(dem_path)
    written = build_covariate_stack(dem_path, tmp / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    stack_manifest = json.loads(written["provenance"].read_text())
    corpus_manifest = json.loads(CORPUS_MANIFEST_PATH.read_text())
    grid = DemGrid.load(dem_path)
    layers = build_default_registry().build_all(grid)
    matrix, manifest = assemble_training_matrix(
        CorpusCsvSampleSource(), grid, layers, corpus_manifest, stack_manifest
    )
    return {
        "dem_path": dem_path,
        "grid": grid,
        "layers": layers,
        "corpus_manifest": corpus_manifest,
        "stack_manifest": stack_manifest,
        "matrix": matrix,
        "manifest": manifest,
    }


# ------------------------------------------------------------- determinism


def test_two_independent_builds_are_identical_in_every_field_and_hash(
    real_assembly: dict,
) -> None:
    """Full-state comparison over dataclasses.fields — the E2.0-2
    phantom-field lesson: an 'identical' that compares selected fields
    passes while an omitted field drifts."""
    again_matrix, again_manifest = assemble_training_matrix(
        CorpusCsvSampleSource(),
        real_assembly["grid"],
        real_assembly["layers"],
        real_assembly["corpus_manifest"],
        real_assembly["stack_manifest"],
    )
    first_matrix = real_assembly["matrix"]

    for data_field in dataclasses.fields(TrainingMatrix):
        first_value = getattr(first_matrix, data_field.name)
        again_value = getattr(again_matrix, data_field.name)
        if isinstance(first_value, np.ndarray):
            assert np.array_equal(first_value, again_value, equal_nan=True), data_field.name
        else:
            assert first_value == again_value, data_field.name
    assert real_assembly["manifest"].content_hash == again_manifest.content_hash


# ----------------------------------------------------- shape, order, values


def test_matrix_is_35x8_sorted_by_source_record_id_with_y_from_the_corpus(
    real_assembly: dict,
) -> None:
    matrix: TrainingMatrix = real_assembly["matrix"]
    assert matrix.X.shape == (35, 8)
    assert matrix.y.shape == (35,)
    assert matrix.coords.shape == (35, 2)
    assert matrix.covariate_names == tuple(build_default_registry().names())
    assert list(matrix.station_ids) == sorted(matrix.station_ids)

    by_id = {
        obs.source_record_id: obs for obs in CorpusCsvSampleSource().get_training_samples()
    }
    for i, station_id in enumerate(matrix.station_ids):
        obs = by_id[station_id]
        assert matrix.y[i] == obs.abundance_kg_m2, station_id
        assert tuple(matrix.coords[i]) == (obs.longitude, obs.latitude), station_id


def test_matrix_arrays_are_read_only(real_assembly: dict) -> None:
    matrix: TrainingMatrix = real_assembly["matrix"]
    for array in (matrix.X, matrix.y, matrix.coords):
        with pytest.raises(ValueError, match="read-only"):
            array[(0,) * array.ndim] = 1.0


def test_reordered_layers_produce_a_matrix_matching_its_own_manifest(
    real_assembly: dict,
) -> None:
    """Column order is the given layer order, and the manifest names columns
    in THAT order — a reordered registry cannot desynchronize data from its
    own description."""
    reversed_layers = list(reversed(real_assembly["layers"]))
    matrix, manifest = assemble_training_matrix(
        CorpusCsvSampleSource(),
        real_assembly["grid"],
        reversed_layers,
        real_assembly["corpus_manifest"],
        real_assembly["stack_manifest"],
    )
    assert list(matrix.covariate_names) == manifest.covariate_names
    assert matrix.covariate_names == tuple(reversed(real_assembly["matrix"].covariate_names))

    baseline: TrainingMatrix = real_assembly["matrix"]
    for name in matrix.covariate_names:
        column = matrix.covariate_names.index(name)
        baseline_column = baseline.covariate_names.index(name)
        assert np.array_equal(
            matrix.X[:, column], baseline.X[:, baseline_column], equal_nan=True
        ), name


# ------------------------------------------------------- provenance chaining


def test_upstream_hashes_match_the_actual_corpus_and_stack_manifests(
    real_assembly: dict,
) -> None:
    manifest = real_assembly["manifest"]
    assert manifest.upstream_hashes == {
        "corpus": real_assembly["corpus_manifest"]["content_hash"],
        "feature_stack": real_assembly["stack_manifest"]["content_hash"],
    }
    # And those are the real artifacts' finalized hashes, present and typed.
    assert manifest.upstream_hashes["corpus"].startswith("sha256:")
    assert manifest.upstream_hashes["feature_stack"].startswith("sha256:")


def test_contract_versions_include_model_config_version(real_assembly: dict) -> None:
    """The matrix is Contract 8's first consumer, so the manifest records
    which model_config version defined its y."""
    assert real_assembly["manifest"].contract_versions["model_config_version"] == 1


def test_changing_the_recorded_target_value_changes_the_content_hash(
    real_assembly: dict,
) -> None:
    """THE property the fourth artifact exists for: upstream hashes are
    invariant to the target, so the target must have identity HERE. Value
    change asserted at manifest level (only one value is assemblable
    today); the origin PROMOTION (AUTHORED→LITERATURE, Isaac's citation
    arriving) asserted through real assembly — same matrix bytes, different
    artifact identity."""
    manifest = real_assembly["manifest"]
    relabelled = manifest.model_copy(
        update={
            "target_definition": {
                "value": "surface_only_hypothetical",
                "data_origin": "AUTHORED",
                "author": "model",
            }
        }
    )
    assert relabelled.compute_content_hash() != manifest.content_hash

    _, promoted = assemble_training_matrix(
        CorpusCsvSampleSource(),
        real_assembly["grid"],
        real_assembly["layers"],
        real_assembly["corpus_manifest"],
        real_assembly["stack_manifest"],
        target=DeclaredField(
            value="total_as_published", data_origin="LITERATURE", author="isaac"
        ),
    )
    assert promoted.matrix_sha256 == manifest.matrix_sha256  # same numbers
    assert promoted.content_hash != manifest.content_hash  # different identity


def test_cell_groups_match_the_extraction_and_the_ceiling_recomputes_to_0348(
    real_assembly: dict,
) -> None:
    """The grouping is recorded so the covariate-model R² ceiling is
    recomputable NEXT TO any model score — recomputed here from the
    manifest alone (groups + y) and pinned at 0.348 on today's fixture.
    Re-report at Checkpoint 1 when the cells shrink."""
    manifest = real_assembly["manifest"]
    matrix: TrainingMatrix = real_assembly["matrix"]

    assert manifest.shared_cell_count == 35
    assert manifest.distinct_cell_count == 4
    assert sorted(len(group) for group in manifest.cell_groups) == [7, 7, 7, 14]
    assert sorted(sid for group in manifest.cell_groups for sid in group) == list(
        matrix.station_ids
    )

    y_by_id = dict(zip(matrix.station_ids, matrix.y))
    all_y = np.array(list(y_by_id.values()))
    ss_total = float(((all_y - all_y.mean()) ** 2).sum())
    ss_within = 0.0
    for group in manifest.cell_groups:
        group_y = np.array([y_by_id[sid] for sid in group])
        ss_within += float(((group_y - group_y.mean()) ** 2).sum())
    assert round(1 - ss_within / ss_total, 3) == 0.348


# ----------------------------------------------- computed origin + watermark


def test_origin_is_synthetic_computed_from_the_inputs_not_declared(
    real_assembly: dict, tmp_path: Path
) -> None:
    """SYNTHETIC on today's fixture, and COMPUTED: the same assembly over a
    stack whose DEM was declared MEASURED (layers therefore DERIVED)
    produces DERIVED — the origin follows the inputs, so there is no
    hand-declared constant to go stale (the P2.0c laundering direction,
    which SYNTHETIC-only fixtures could not observe)."""
    assert real_assembly["manifest"].data_origin == "SYNTHETIC"

    written = build_covariate_stack(
        real_assembly["dem_path"], tmp_path / "stack_m", dem_data_origin=DataOrigin.MEASURED
    )
    measured_stack = json.loads(written["provenance"].read_text())
    _, manifest = assemble_training_matrix(
        CorpusCsvSampleSource(),
        real_assembly["grid"],
        real_assembly["layers"],
        real_assembly["corpus_manifest"],
        measured_stack,
    )
    assert manifest.data_origin == "DERIVED"


def test_watermark_is_present_for_synthetic_and_disappears_on_a_measured_stack(
    real_assembly: dict, tmp_path: Path
) -> None:
    """End-to-end verification that the watermark DERIVES (P2.0d-3 posture:
    default-ON, no stored flag): present on today's synthetic fixture;
    gone when the stack's DEM is declared MEASURED — the Checkpoint-1
    direction."""
    watermark = matrix_watermark(real_assembly["manifest"].data_origin)
    assert watermark is not None and "SYNTHETIC" in watermark

    written = build_covariate_stack(
        real_assembly["dem_path"], tmp_path / "stack_m", dem_data_origin=DataOrigin.MEASURED
    )
    measured_stack = json.loads(written["provenance"].read_text())
    _, manifest = assemble_training_matrix(
        CorpusCsvSampleSource(),
        real_assembly["grid"],
        real_assembly["layers"],
        real_assembly["corpus_manifest"],
        measured_stack,
    )
    assert matrix_watermark(manifest.data_origin) is None


def test_matrix_watermark_helper_is_default_on_and_clean_only_for_measured_lineage() -> None:
    """Helper-level observers (the d-3 precedent): MEASURED and DERIVED are
    the two computed origins that trace every value to a measurement this
    repo holds — everything else stamps, absence stamps, unknown raises.
    The deliberate divergence from dem_watermark (which stamps DERIVED) is
    documented in the helper: a DECLARED-DERIVED input DEM is suspicious; a
    COMPUTED-DERIVED matrix is the intended Checkpoint-1 state."""
    assert matrix_watermark(DataOrigin.MEASURED) is None
    assert matrix_watermark("DERIVED") is None
    for stamped in (DataOrigin.SYNTHETIC, "LITERATURE", "AUTHORED"):
        watermark = matrix_watermark(stamped)
        assert watermark is not None and str(DataOrigin(stamped).value) in watermark
    assert matrix_watermark(None) is not None
    with pytest.raises(ValueError):
        matrix_watermark("FABRICATED")


# ------------------------------------------------------------- the refusals


def _small_dem(path: Path, size: int = 20) -> None:
    values = -(4000.0 + np.arange(size * size, dtype=np.float64).reshape(size, size))
    write_test_raster(path, values.astype("float32"), west=WEST, north=NORTH, pixel_size_deg=RES)


def _constructed_setup(tmp_path: Path, latitude: float, longitude: float) -> dict:
    """A one-station corpus at the given coordinate over a small DEM, with a
    real stack artifact and a minimal (hand-built, test-only) corpus
    manifest."""
    from tests.test_corpus_csv_sample_source import _observation

    dem_path = tmp_path / "dem.tif"
    _small_dem(dem_path)
    written = build_covariate_stack(dem_path, tmp_path / "stack", dem_data_origin=DataOrigin.SYNTHETIC)
    stack_manifest = json.loads(written["provenance"].read_text())
    grid = DemGrid.load(dem_path)
    layers = build_default_registry().build_all(grid)
    observation = _observation(
        source_record_id="src_test_MASS_border01", latitude=latitude, longitude=longitude
    )
    corpus_manifest = {
        "content_hash": "sha256:" + "0" * 64,
        "training_eligible_count": 1,
        "admitted_rows_by_data_origin": {"MEASURED": 1},
    }
    return {
        "source": FixtureSampleSource([observation]),
        "grid": grid,
        "layers": layers,
        "corpus_manifest": corpus_manifest,
        "stack_manifest": stack_manifest,
    }


def test_a_nan_covariate_refuses_to_assemble_naming_station_and_covariates(
    tmp_path: Path,
) -> None:
    """The NaN policy: REFUSE, never exclude-with-a-record, never impute
    (rationale in training_matrix.py's module docstring). The station sits
    on the DEM's corner cell, so every stencil covariate is NaN.

    SOLE OBSERVER (E2.0-1b convention): zero real stations hit a border
    cell today (pinned in test_covariate_extraction.py), so this
    constructed fixture is the only test that can observe the refusal —
    under mutation MU1 (the NaN check deleted) it was the ONLY failing
    test in the suite."""
    setup = _constructed_setup(
        tmp_path, latitude=NORTH - 0.5 * RES, longitude=WEST + 0.5 * RES
    )
    with pytest.raises(ValueError, match=r"src_test_MASS_border01.*slope"):
        assemble_training_matrix(
            setup["source"],
            setup["grid"],
            setup["layers"],
            setup["corpus_manifest"],
            setup["stack_manifest"],
        )


def test_an_interior_station_assembles_cleanly_in_the_constructed_shape(
    tmp_path: Path,
) -> None:
    """The refusal test's control: same constructed shape, interior cell —
    assembles. Without this, the refusal test cannot distinguish 'refuses
    NaN' from 'refuses everything constructed'."""
    setup = _constructed_setup(
        tmp_path, latitude=NORTH - 9.5 * RES, longitude=WEST + 9.5 * RES
    )
    matrix, manifest = assemble_training_matrix(
        setup["source"],
        setup["grid"],
        setup["layers"],
        setup["corpus_manifest"],
        setup["stack_manifest"],
    )
    assert matrix.X.shape == (1, 8)
    assert manifest.n_stations == 1
    assert not np.isnan(matrix.X).any()


def test_a_count_mismatch_with_the_corpus_manifest_refuses(real_assembly: dict) -> None:
    """The manifest's training_eligible_count is the check (E2.0-1's rule);
    a source/manifest disagreement means one of them is stale."""
    tampered = dict(real_assembly["corpus_manifest"])
    tampered["training_eligible_count"] = 34
    with pytest.raises(ValueError, match="training_eligible_count=34"):
        assemble_training_matrix(
            CorpusCsvSampleSource(),
            real_assembly["grid"],
            real_assembly["layers"],
            tampered,
            real_assembly["stack_manifest"],
        )


def test_a_stack_manifest_for_a_different_dem_refuses(real_assembly: dict) -> None:
    """upstream_hashes must chain to the stack that actually produced the
    sampled layers — a manifest describing another DEM is refused."""
    tampered = dict(real_assembly["stack_manifest"])
    tampered["upstream_hashes"] = {"dem": "sha256:" + "f" * 64}
    with pytest.raises(ValueError, match="different stack"):
        assemble_training_matrix(
            CorpusCsvSampleSource(),
            real_assembly["grid"],
            real_assembly["layers"],
            real_assembly["corpus_manifest"],
            tampered,
        )


def test_an_unassemblable_target_value_refuses_with_the_known_set(
    real_assembly: dict,
) -> None:
    """Exhaustive dispatch with an explicit raise: a new admissible value
    arrives via Contract 8 WITH its assembly rule, never silently."""
    with pytest.raises(ValueError, match="no assembly rule.*surface_only_from_05_depths"):
        assemble_training_matrix(
            CorpusCsvSampleSource(),
            real_assembly["grid"],
            real_assembly["layers"],
            real_assembly["corpus_manifest"],
            real_assembly["stack_manifest"],
            target=DeclaredField(
                value="surface_only_from_05_depths", data_origin="AUTHORED", author="model"
            ),
        )


def test_a_manifest_missing_required_fields_refuses_naming_them(
    real_assembly: dict,
) -> None:
    incomplete = {"content_hash": "sha256:" + "0" * 64}
    with pytest.raises(ValueError, match="training_eligible_count"):
        assemble_training_matrix(
            CorpusCsvSampleSource(),
            real_assembly["grid"],
            real_assembly["layers"],
            incomplete,
            real_assembly["stack_manifest"],
        )
