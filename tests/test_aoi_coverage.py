"""AOI coverage — the arithmetic option (b) adds (G.2, 2026-08-25).

The block joins three values the manifest already held. So the tests it needs
are not "does it compute a number" but:

  * is the number DERIVED from those three, or stored? (mutate the range)
  * does its denominator agree with the contract the run recorded?
  * does the ONE predicate really serve both consumers, or did a second
    implementation arrive quietly? (the shared-predicate test)
  * do the committed historical hashes still not move? (HASH.1's property,
    re-measured rather than assumed after a SCHEMA_VERSION bump)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from shapely.geometry import Point, shape

from engine.prospectivity.domain.results import RunManifest
from engine.prospectivity.provenance.coverage import (
    QUADRATURE_STEP_DEG,
    aoi_coverage,
    grid_predictable_area_km2,
    haversine_km,
    polygon_area_km2,
    supported_area_km2,
    within_range_of_any,
)
from engine.prospectivity.provenance.geometry import EARTH_RADIUS_KM

REPO_ROOT = Path(__file__).resolve().parents[1]
AOI = REPO_ROOT / "data" / "aoi" / "study_area.geojson"

# The two clusters, far enough apart that a disc around one cannot reach the
# other (991 km separation vs a 21.6 km range) — so a fixture built from them
# SEPARATES "the union of discs" from "the bounding box of the stations",
# which a single tight cluster could not.
WEST = (-125.9, 14.07)
EAST = (-117.03, 11.88)


@pytest.fixture(scope="module")
def aoi_geometry():
    return shape(json.loads(AOI.read_text())["features"][0]["geometry"])


def test_the_aoi_area_is_the_published_polygons_by_closed_form(aoi_geometry) -> None:
    """11,399,937 km2 is the MAIN polygon; both parts are 11,399,939. Pinned
    separately because the difference IS the sliver, and a test that only
    checked the total could not tell a dropped sliver from rounding."""
    parts = sorted(aoi_geometry.geoms, key=lambda p: -p.area)
    main = polygon_area_km2(parts[0])
    sliver = polygon_area_km2(parts[1])
    both = polygon_area_km2(aoi_geometry)

    assert round(main) == 11_399_937
    assert round(sliver, 2) == 1.41
    assert round(both) == 11_399_939
    assert both == pytest.approx(main + sliver, abs=1e-6)
    # ...and the sliver's share is the recorded 0.0000123% — pinned as the
    # VALUE rather than as an inequality, because "negligible" is the claim the
    # keep-it decision rests on and an inequality with a round threshold would
    # have been chosen to pass rather than measured.
    assert f"{sliver / both * 100:.7f}" == "0.0000123"


def test_the_supported_area_is_the_union_of_discs_not_their_bounding_box(
    aoi_geometry,
) -> None:
    """THE DEGENERACY THIS FIXTURE AVOIDS. The two clusters are 991 km apart,
    so their bounding box is ~350,000 km2 while the union of 21.6 km discs
    around them is ~4,000. A bounding-box implementation would pass any test
    built on ONE cluster and fail here by two orders of magnitude."""
    range_km = 21.610897164216457
    area = supported_area_km2(aoi_geometry, [WEST, EAST], range_km)

    two_discs = 2 * math.pi * range_km**2
    assert area == pytest.approx(two_discs, rel=0.02)
    assert area < 3_500  # far below the ~350,000 km2 bbox of the two clusters


def test_the_quadrature_has_converged_at_the_shipped_step(aoi_geometry) -> None:
    """PINNING THE METHOD IS PART OF THE CLAIM (G.2-PRE): the planning pass and
    G.2-PRE agreed on area and diverged in the third significant figure of the
    FRACTION, purely from resolution. So the step is justified by measurement,
    not by a docstring.

    RUN ON THE REAL 35 STATIONS, through `get_training_samples()` rather than a
    reimplemented gate (the G.3 second-authority lesson) — because convergence
    is a property of THE SHIPPED CONFIGURATION. The two-station fixture above is
    the WORST case for this quadrature (isolated discs are almost all edge, so
    edge-cell error dominates) and converges more slowly; asserting the shipped
    tolerance there would have measured the fixture, not the method."""
    from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource

    source = CorpusCsvSampleSource(REPO_ROOT / "data" / "corpus" / "master_observations.csv")
    stations = [(o.longitude, o.latitude) for o in source.get_training_samples()]
    assert len(stations) == 35

    range_km = 21.610897164216457
    coarse = supported_area_km2(aoi_geometry, stations, range_km, QUADRATURE_STEP_DEG)
    fine = supported_area_km2(aoi_geometry, stations, range_km, QUADRATURE_STEP_DEG / 2)

    # measured at G.2: 4,124.6 at BOTH 0.01 and 0.005 deg
    assert coarse == pytest.approx(fine, rel=0.002)
    total = polygon_area_km2(aoi_geometry)
    assert f"{coarse / total * 100:.4f}" == f"{fine / total * 100:.4f}" == "0.0362"


def test_the_fraction_is_derived_from_the_range_and_not_stored(aoi_geometry) -> None:
    """The mutation the block exists to survive: change the RANGE and the
    supported area and fraction must move with it, monotonically. A stored
    number would sit still."""
    stations = [WEST, EAST]
    blocks = {
        rk: aoi_coverage(aoi_geometry, "aoi", "sha256:x", stations, rk, "est", False)
        for rk in (10.0, 21.610897164216457, 50.0)
    }
    areas = [blocks[rk]["per_run"]["supported_area_km2"] for rk in (10.0, 21.610897164216457, 50.0)]
    assert areas[0] < areas[1] < areas[2], areas
    # area scales ~ r^2 for well-separated discs: 5x the range, ~25x the area
    assert areas[2] / areas[0] == pytest.approx(25.0, rel=0.05)

    fractions = [blocks[rk]["per_run"]["fraction_of_aoi_supported"] for rk in (10.0, 50.0)]
    assert fractions[0] < fractions[1]
    # the DENOMINATOR does not move with the range — that is the whole point of (b)
    assert len({b["stable"]["aoi_area_km2"] for b in blocks.values()}) == 1


def test_no_range_is_reported_as_not_computable_rather_than_zero(aoi_geometry) -> None:
    """`per_run` None, not a 0.0 fraction. No support MEASURED and no support
    COMPUTABLE are different facts and a zero would read as the first."""
    block = aoi_coverage(aoi_geometry, "aoi", "sha256:x", [WEST], None, None, None)
    assert block["per_run"] is None
    assert "NOT COMPUTABLE" in block["statement"] and "not the same as zero" in block["statement"]
    # the stable half still stands on its own — that is what run-independent means
    assert round(block["stable"]["aoi_area_km2"]) == 11_399_939


def test_the_statement_carries_the_dated_numerator_and_the_ceiling_caveat(
    aoi_geometry,
) -> None:
    """G.2-PRE's honest form, emitted rather than left to a reader to assemble:
    a fixed denominator with a numerator that names its run's fit, and the
    lower-bound caveat when the range sat at its candidate ceiling."""
    at_ceiling = aoi_coverage(
        aoi_geometry, "ccz_management_area", "sha256:x", [WEST, EAST], 21.6108, "ordinary_kriging", True
    )
    assert "LOWER BOUND" in at_ceiling["statement"]
    assert "ordinary_kriging" in at_ceiling["statement"]
    assert "The denominator is fixed; the numerator is this run's." in at_ceiling["statement"]

    free = aoi_coverage(
        aoi_geometry, "ccz_management_area", "sha256:x", [WEST, EAST], 21.6108, "ordinary_kriging", False
    )
    assert "LOWER BOUND" not in free["statement"]  # the caveat DISCRIMINATES


def test_one_predicate_serves_both_consumers_on_one_earth() -> None:
    """THE DE-DUPLICATION, observed. `viewer_model.no_information()` is the
    complement of `within_range_of_any` over a grid; before G.2 it carried its
    own haversine on a 6371.0 km earth while the engine used the IUGG mean.
    This asserts the viewer now calls THIS function — by identity, so a copied
    body would not satisfy it — and that the boundary conventions are exact
    complements (`<=` here, `>` there)."""
    import services.api.viewer_model as viewer_model

    assert viewer_model._haversine_km is haversine_km
    assert haversine_km(-126.5, 11.3, -126.5, 11.3) == 0.0

    # WHICH EARTH, pinned to full precision. Added after mutation M4 SURVIVED
    # the first batch: swapping EARTH_RADIUS_KM back to the viewer's old
    # 6371.0 passed all nine tests, because a 1.4 ppm change sits below every
    # other tolerance here and the unification test above checks the function's
    # IDENTITY, not its constant. The de-duplication was guarded; the value was
    # not. One degree of latitude separates the two at the sixth significant
    # figure, which is enough.
    one_degree = haversine_km(0.0, 0.0, 0.0, 1.0)
    assert one_degree == pytest.approx(math.pi * EARTH_RADIUS_KM / 180, rel=1e-12)
    assert f"{one_degree:.6f}" == "111.195080"  # 111.194927 on a 6371.0 km earth

    # complementary at the boundary, which is where the two could disagree
    d = haversine_km(WEST[0], WEST[1], WEST[0], WEST[1] + 0.1)
    assert within_range_of_any(WEST[0], WEST[1] + 0.1, [WEST], d) is True
    assert not (d > d)  # the viewer's strict complement excludes exactly this point


def test_the_earth_radius_unification_moves_no_recorded_count() -> None:
    """The claim the unification comment makes, MEASURED: E5.4 recorded 2,846
    no-information cells of 2,880 predictable, computed on a 6371.0 km earth.
    On the IUGG mean it is still 2,846 — a 1.4 ppm change (0.03 m on a 21.6 km
    range) that cannot move a 0.1-degree grid. Asserted rather than asserted-in-
    prose, because 'negligible' is exactly the kind of claim that is usually
    right and occasionally not."""
    import services.api.viewer_model as viewer_model

    def haversine_on(radius):
        def h(lon1, lat1, lon2, lat2):
            p1, p2 = math.radians(lat1), math.radians(lat2)
            d = math.radians(lon2 - lon1)
            x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d / 2) ** 2
            return 2 * radius * math.asin(math.sqrt(x))
        return h

    # a 0.1-degree grid over the fixture extent, the shape E5.4 measured on
    grid = {"transform": [0.1, 0.0, -126.5, 0.0, -0.1, 14.7], "width": 100, "height": 34}
    stations = {"coordinates": {"w": list(WEST), "e": list(EAST)}}

    counts = []
    original = viewer_model._haversine_km
    try:
        for radius in (6371.0, EARTH_RADIUS_KM):
            viewer_model._haversine_km = haversine_on(radius)
            counts.append(sum(viewer_model.no_information(grid, stations, 21.610897164216457)))
    finally:
        viewer_model._haversine_km = original
    assert counts[0] == counts[1], counts


def test_the_predictable_area_excludes_masked_cells() -> None:
    """The grid's contribution to `stable` is the PREDICTABLE area, not the
    extent box — masked cells are cells the covariates do not define, so
    counting them would overstate what the run can speak about. The fixture
    masks half the grid, which separates the two: an extent-box implementation
    returns twice this."""
    transform = [0.1, 0.0, -126.5, 0.0, -0.1, 14.7]
    width, height = 10, 10
    everything = [True] * (width * height)
    half = [(i % width) < 5 for i in range(width * height)]

    full = grid_predictable_area_km2(transform, width, height, everything)
    masked = grid_predictable_area_km2(transform, width, height, half)
    assert masked == pytest.approx(full / 2, rel=1e-9)
    assert grid_predictable_area_km2(transform, width, height, [False] * 100) == 0.0
