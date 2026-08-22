"""E4.2 commit 1 — the footprint rasters: count, association, grid identity,
the mask kept apart from the footprint, the two-reason watermark PER
REASON on every file, round-trip, determinism.

STATED FIRST (E4.1's measurement): on today's surfaces every footprint is
UNIFORMLY TRUE — 2,880/2,880 — so a real-data raster cannot separate "the
footprint was written" from "ones were written". The CONSTRUCTED fixture
(E4.1's 2×4 grid: a masked cell, not-minable cells, minable cells) is what
separates nodata from 0 from 1, and the real-data tests assert identity,
count, and the stated-in-advance uniformity.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
import yaml

from engine.prospectivity.economics.contract import ExclusionSet, load_scenarios_yaml, scenarios
from engine.prospectivity.economics.cutoff import CutoffEconomicModel
from engine.prospectivity.economics.model import EconomicInputs
from engine.prospectivity.economics.writer import (
    ASSOCIATION_NAME,
    FOOTPRINT_ENCODING,
    footprint_name,
    write_footprints,
)
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.surfaces.writer import SIDECAR_NAME, write_surface
from engine.prospectivity.validation.claim import evaluate_claim
from tests.test_economic_cutoff import AREA, EMPTY, MARKET, STRATEGIC, _grid, _inputs, _ro, _scenario, _surface

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def verdict():
    """E2.5's real verdict on the committed E2.4 run — a refusal, the honest
    mark every economics raster must carry today."""
    from engine.prospectivity.domain.results import RunManifest

    manifest = RunManifest(**json.loads((REPO_ROOT / "data/runs/e2.4/run_manifest.json").read_text()))
    stack = {"layers": [{"name": n, "dem": {"resolution_deg": [0.1, 0.1], "content_hash": "sha256:x"}} for n in ("depth", "slope")]}
    return evaluate_claim(manifest, design="leave_one_site_out", feature_stack_manifest=stack)


def _constructed_model():
    return CutoffEconomicModel(contract=load_scenarios_yaml(), exclusions=EMPTY)


# ──────────────────────────── the constructed fixture: the encoding


def test_the_mask_and_the_footprint_are_different_things_in_the_written_raster(tmp_path: Path, verdict) -> None:
    """nodata (NaN) for UNDEFINED (the masked cell [1,3]); 0.0 for NOT
    minable with covariates present ([0,0], [1,0] slope, [1,2]); 1.0 for
    minable. Separates a raster that conflates undefined with false — the
    masked cell must be NaN and exactly the masked cell."""
    fp = _constructed_model().apply(_inputs(), MARKET)
    written = write_footprints(fp, _grid(), {"fixture": _surface()}, tmp_path, claim_verdict=verdict)
    assert set(written) == {("fixture", 0.0), ("fixture", 1.0)}
    with rasterio.open(written[("fixture", 0.0)]) as ds:
        values = ds.read(1)
        assert np.isnan(ds.nodata)
    expected = np.array([[0.0, 1.0, 1.0, 1.0], [0.0, 1.0, 0.0, np.nan]], dtype=np.float32)
    np.testing.assert_array_equal(values, expected)
    assert int(np.isnan(values).sum()) == 1 and int((values == 0.0).sum()) == 3 and int((values == 1.0).sum()) == 4
    np.testing.assert_array_equal(np.isnan(values), ~np.isfinite(_surface().mu))


def test_a_footprint_that_marks_a_masked_cell_minable_or_was_computed_on_another_grid_is_refused_by_name(tmp_path: Path, verdict) -> None:
    import dataclasses

    fp = _constructed_model().apply(_inputs(), MARKET)
    other_grid = dataclasses.replace(_grid(), stack_content_hash="sha256:another")
    with pytest.raises(ValueError, match=r"computed on a grid whose identity differs .* in \['stack_content_hash'\]"):
        write_footprints(fp, other_grid, {"fixture": _surface()}, tmp_path, claim_verdict=verdict)
    # a surface whose mask is SMALLER than the footprint's masked set: the footprint marks a masked cell
    level = fp.levels["fixture"][0.0]
    forged = level.minable.copy(); forged[1, 3] = True; forged.flags.writeable = False
    tampered = dataclasses.replace(fp, levels={"fixture": {0.0: dataclasses.replace(level, minable=forged), 1.0: fp.levels["fixture"][1.0]}})
    with pytest.raises(ValueError, match=r"marks 1 masked cell\(s\) minable"):
        write_footprints(tampered, _grid(), {"fixture": _surface()}, tmp_path / "b", claim_verdict=verdict)
    with pytest.raises(ValueError, match=r"cover \['fixture'\] but the surfaces cover \['fixture', 'other'\]"):
        write_footprints(fp, _grid(), {"fixture": _surface(), "other": _surface("other")}, tmp_path / "c", claim_verdict=verdict)


# ─────────────────────────── the two reasons, PER REASON, per carrier


def _reason_states(tags: dict) -> dict[str, str]:
    return {k: v.split(":")[0] for k, v in tags.items() if k.startswith("watermark_reason_") and k != "watermark_reasons_unlifted"}


def test_both_reasons_are_on_every_file_per_reason_and_lifting_one_does_not_lift_the_other(tmp_path: Path, verdict) -> None:
    """THE COLLAPSE OBSERVER, both halves. Today: both UNLIFTED on every
    file. A Checkpoint-1 fixture (MEASURED DEM): the terrain tag reads
    lifted and the economic tag still reads UNLIFTED — asserted per reason,
    not by count, so a collapse to one flag that preserved the count (both
    tags derived from the combined state) fails here too."""
    today = _constructed_model().apply(_inputs("SYNTHETIC"), MARKET)
    after_cp1 = _constructed_model().apply(_inputs("MEASURED"), MARKET)
    w_today = write_footprints(today, _grid(), {"fixture": _surface()}, tmp_path / "today", claim_verdict=verdict)
    w_cp1 = write_footprints(after_cp1, _grid(), {"fixture": _surface()}, tmp_path / "cp1", claim_verdict=verdict)
    for path in w_today.values():
        tags = rasterio.open(path).tags()
        assert _reason_states(tags) == {"watermark_reason_terrain": "UNLIFTED", "watermark_reason_economic_parameters": "UNLIFTED"}
        assert tags["watermark_reasons_unlifted"] == "2" and "2 independent reason(s)" in tags["watermark"]
        assert "Checkpoint 1" in tags["watermark_reason_terrain"] and "Checkpoint 4" in tags["watermark_reason_economic_parameters"]
        assert tags["publishable"] == "false" and tags["data_origin"] == "AUTHORED"
    for path in w_cp1.values():
        tags = rasterio.open(path).tags()
        assert _reason_states(tags) == {"watermark_reason_terrain": "lifted", "watermark_reason_economic_parameters": "UNLIFTED"}
        assert tags["watermark_reasons_unlifted"] == "1" and tags["publishable"] == "false"
        assert tags["data_origin"] == "AUTHORED"  # the lattice's lossy answer, unchanged; the tags say what moved
    # carrier 2: the association sidecar carries the same verdict, per reason
    record = json.loads((tmp_path / "cp1" / ASSOCIATION_NAME).read_text())
    entry = record["files"][footprint_name("MARKET_STANDARD", "fixture", 0.0)]
    assert [r["lifted"] for r in entry["watermark"]["reasons"]] == [True, False]


# ───────────────────────────── real surfaces: count, identity, association


@pytest.fixture(scope="module")
def real(surface_assembly, verdict, tmp_path_factory) -> dict:
    from engine.prospectivity.features.bundle import cell_areas_m2
    from engine.prospectivity.features.dem_grid import DemGrid
    from engine.prospectivity.surfaces.writer import compute_surface_origin

    out = tmp_path_factory.mktemp("economics")
    grid, surfaces, stack = surface_assembly["grid"], surface_assembly["surfaces"], surface_assembly["stack_manifest"]
    origin = compute_surface_origin(stack["dem_data_origin"], surface_assembly["matrix_manifest"].data_origin)
    surface_files = {n: write_surface(s, grid, out, data_origin=origin, verdict=verdict) for n, s in surfaces.items()}
    inputs = EconomicInputs(
        surfaces=surfaces, grid=grid, cell_area_m2=cell_areas_m2(DemGrid.load(Path(stack["dem_path"]))),
        dem_data_origin=stack["dem_data_origin"], surface_data_origin=origin.value,
    )
    model = CutoffEconomicModel()
    footprints = {s.name: model.apply(inputs, s) for s in scenarios()}
    written = {name: write_footprints(fp, grid, surfaces, out, claim_verdict=verdict) for name, fp in footprints.items()}
    return {"out": out, "grid": grid, "surfaces": surfaces, "surface_files": surface_files, "footprints": footprints, "written": written, "inputs": inputs}


def test_twelve_footprint_rasters_are_written_and_every_one_is_resolvable_from_the_record_not_the_name(real: dict) -> None:
    """2 scenarios × 3 estimators × 2 levels = 12, counted before and after.
    The association is resolved FROM THE SIDECAR: for every entry, the file
    exists, its sha256 recomputes, and its own tags agree with the entry —
    nothing here parses a filename."""
    files = [p for paths in real["written"].values() for p in paths.values()]
    assert len(files) == 12 == 2 * 3 * 2
    record = json.loads((real["out"] / ASSOCIATION_NAME).read_text())
    assert set(record["files"]) == {p.name for p in files} and record["footprint_encoding"] == FOOTPRINT_ENCODING
    seen = set()
    for basename, entry in record["files"].items():
        path = real["out"] / basename
        assert path.is_file() and file_sha256(path) == entry["sha256"]
        tags = rasterio.open(path).tags()
        assert (tags["kind"], tags["scenario"], tags["estimator"], float(tags["z"])) == ("footprint", entry["scenario"], entry["estimator"], entry["z"])
        seen.add((entry["scenario"], entry["estimator"], entry["z"]))
    assert seen == {(s, e, z) for s in ("MARKET_STANDARD", "STRATEGIC_SUBSIDIZED") for e in ("mean_baseline", "ordinary_kriging", "random_forest") for z in (0.0, 1.0)}
    # the origin sidecar classifies every raster, citing the contract's authorship rather than declaring one
    origin = yaml.safe_load((real["out"] / SIDECAR_NAME).read_text())["files"]
    for p in files:
        assert origin[p.name]["data_origin"] == "AUTHORED" and "scenarios.yaml" in origin[p.name]["author_inherited_from"]
        assert "combine_origins" in origin[p.name]["derivation"]


def test_every_footprint_shares_the_surfaces_grid_and_mask_exactly(real: dict) -> None:
    """Identity against the SURFACE raster's recorded georeferencing, not a
    literal; the masked set exactly the surface's; the value set {0, 1, NaN}."""
    for name, paths in real["written"].items():
        for (estimator, z), path in paths.items():
            with rasterio.open(path) as fp, rasterio.open(real["surface_files"][estimator]["prediction"]) as sp:
                assert (fp.transform, fp.crs, fp.width, fp.height, fp.driver, fp.dtypes) == (sp.transform, sp.crs, sp.width, sp.height, sp.driver, sp.dtypes)
                values, mu = fp.read(1), sp.read(1)
                assert fp.tags()["grid_stack_content_hash"] == sp.tags()["grid_stack_content_hash"]
            np.testing.assert_array_equal(np.isnan(values), np.isnan(mu))
            assert int(np.isnan(values).sum()) == 520 and set(np.unique(values[np.isfinite(values)]).tolist()) == {1.0}
            assert "cog" not in " ".join(rasterio.open(path).tags().values()).lower()


def test_on_todays_surfaces_every_footprint_is_uniformly_true_as_stated_in_advance(real: dict) -> None:
    """E4.1's measurement, on the files: 2,880 ones, 520 NaN, per file —
    asserted as the full value set, with the reason in the tags."""
    for paths in real["written"].values():
        for path in paths.values():
            tags = rasterio.open(path).tags()
            assert (tags["n_minable"], tags["n_predictable"]) == ("2880", "2880")
            assert "PHYSICALLY MEANINGLESS" in tags["slope_filter_note"]


def test_writing_is_deterministic_byte_for_byte(real: dict, tmp_path: Path, verdict) -> None:
    again = write_footprints(real["footprints"]["MARKET_STANDARD"], real["grid"], real["surfaces"], tmp_path, claim_verdict=verdict)
    for key, path in again.items():
        assert path.read_bytes() == real["written"]["MARKET_STANDARD"][key].read_bytes(), key
    a = json.loads((tmp_path / ASSOCIATION_NAME).read_text())["files"]
    b = json.loads((real["out"] / ASSOCIATION_NAME).read_text())["files"]
    assert a == {k: v for k, v in b.items() if v["scenario"] == "MARKET_STANDARD"}
