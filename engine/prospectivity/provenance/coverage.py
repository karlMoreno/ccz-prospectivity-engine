"""AOI coverage — what fraction of the region this project is ABOUT has
variogram support (G.2, 2026-08-25).

WHY THIS IS ITS OWN MODULE AND NOT A SECOND COPY OF THE VIEWER'S GEOMETRY.
`services/api/viewer_model.no_information()` already answers a neighbouring
question — which PREDICTION-GRID CELLS lie beyond one fitted range of every
station (E5.4's hatch). It cannot answer this one: the AOI is ~33x larger
than the prediction grid, so a grid-cell loop has nothing to say about the
CCZ's other 97%. What the two share is the PREDICATE — "is this point within
`range_km` of any station?" — and that is what lives here, imported by both.
Two implementations of one rule with nothing observing their agreement is the
defect that would otherwise arrive; `test_aoi_coverage.py` observes it.

    viewer_model.no_information()          coverage.aoi_coverage()
    per prediction-grid cell               per AOI, by area
              \\                                 /
               \\___ within_range_of_any() ____/
                        haversine_km()
                     EARTH_RADIUS_KM (one earth)

ONE EARTH RADIUS. `geometry.py` and `ts6/comparison.py` both use the IUGG mean
6371.0088 km; `viewer_model` had its own 6371.0. Unified here on the named
constant. The difference is 1.4 ppm (0.03 m on a 21.6 km range) and moves no
recorded count — measured, not assumed, in `test_aoi_coverage.py`.

THE TWO HALVES USE DIFFERENT SCHEMES, DELIBERATELY, AND BOTH ARE RECORDED:

  * THE AOI'S AREA is CLOSED FORM — the spherical-excess formula over each
    ring (Chamberlain & Duquette), exact for a spherical polygon, no
    resolution parameter to argue about.
  * THE SUPPORTED AREA is QUADRATURE — the union of geodesic discs has no
    closed form once discs overlap, and ours do (35 stations in two tight
    clusters). So it is integrated on a lat/lon lattice with cos(lat) cell
    weighting, over the stations' bounding box grown by `range_km` (the union
    cannot extend past that), intersected with the AOI.

PINNING THE METHOD IS PART OF THE CLAIM. G.2-PRE and the planning pass agreed
on AREA to the last digit and diverged in the THIRD significant figure on the
FRACTIONS (0.036% vs 0.037%; 14.72% vs 14.545%) — consistent with different
quadrature resolution, largest where disc-edge effects dominate. A number
quoted without its scheme cannot be compared to a later recomputation, only
differed from. So every emitted block carries `method`, including the step and
the convergence measurement.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from engine.prospectivity.provenance.geometry import EARTH_RADIUS_KM

# The quadrature step, in degrees. 0.01 deg ~ 1.1 km at the equator, so a
# 21.6 km disc is resolved by ~20 cells across its radius. Chosen from the
# convergence measurement recorded in METHOD_NOTE (the FRACTION is stable at
# four significant figures from here down, while halving the step again costs
# 4x the time for no change), not by taste.
QUADRATURE_STEP_DEG = 0.01

METHOD_NOTE = (
    "AOI area: closed-form spherical excess per ring (Chamberlain & Duquette) "
    f"on a sphere of radius {EARTH_RADIUS_KM} km (IUGG mean); exact, no "
    "resolution parameter. Supported area: quadrature on a lat/lon lattice of "
    f"{QUADRATURE_STEP_DEG} deg with cos(lat) cell weighting, over the "
    "stations' bounding box grown by one range (the union of discs cannot "
    "extend past it), intersected with the AOI. CONVERGENCE, measured with "
    "THIS integrator at G.2 (steps 0.04 / 0.02 / 0.01 / 0.005 / 0.0025 deg): "
    "supported area 4,143.8 / 4,134.3 / 4,124.6 / 4,124.6 / 4,122.1 km2 — so "
    "4,124 +/- 12 km2 at steps 0.02 and finer, while the FRACTION is stable "
    "at 0.0362% from 0.01 down. The area's third significant figure is the "
    "scheme's, not the seafloor's; the fraction's fourth is converged. "
    "(G.2-PRE reported 4,120 +/- 3 for the same quantity using a DIFFERENT "
    "integrator — no AOI clip, different bbox padding — which is why that "
    "number is not quoted here: a spread measured on one instrument does not "
    "describe another.) Quote the fraction with this note or it cannot be "
    "compared to a recomputation, only differed from."
)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance on the IUGG mean sphere. The ONE distance
    function behind both the viewer's hatch and this module's coverage."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d = math.radians(lon2 - lon1)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def within_range_of_any(
    lon: float, lat: float, stations: Sequence[tuple[float, float]], range_km: float
) -> bool:
    """True where the point lies within `range_km` of at least one station.

    THE PREDICATE, in one place. `no_information()` is its complement over a
    grid; this module integrates it over a polygon. Boundary convention: `<=`,
    so a point exactly one range away counts as supported — stated because the
    complement in `no_information()` uses strict `>` and the two must not
    disagree about the boundary, which is a set of measure zero in area terms
    and a real disagreement in cell-count terms.
    """
    return any(haversine_km(lon, lat, x, y) <= range_km for x, y in stations)


def ring_area_km2(coords: Sequence[Sequence[float]]) -> float:
    """Spherical excess of one closed ring, in km^2. Sign discarded: callers
    subtract interiors explicitly rather than relying on winding order, which
    published data does not reliably respect."""
    total = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i][0], coords[i][1]
        lon2, lat2 = coords[i + 1][0], coords[i + 1][1]
        total += math.radians(lon2 - lon1) * (
            2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2))
        )
    return abs(total * EARTH_RADIUS_KM * EARTH_RADIUS_KM / 2.0)


def polygon_area_km2(geometry) -> float:
    """Area of a shapely Polygon or MultiPolygon by the closed form above.

    Handles the MultiPolygon case explicitly because the AOI IS one — the
    published CCZ boundary carries a 1.41 km2 spur touching the main ring at
    its own closure vertex, kept as published (G.2). A single-part assumption
    here would silently drop it.
    """
    parts = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
    total = 0.0
    for part in parts:
        total += ring_area_km2(list(part.exterior.coords))
        for interior in part.interiors:
            total -= ring_area_km2(list(interior.coords))
    return total


def supported_area_km2(
    aoi_geometry,
    stations: Sequence[tuple[float, float]],
    range_km: float,
    step_deg: float = QUADRATURE_STEP_DEG,
) -> float:
    """Area within one `range_km` of any station AND inside the AOI."""
    from shapely.geometry import Point
    from shapely.prepared import prep

    if not stations or range_km is None or range_km <= 0:
        return 0.0
    # One range in degrees, generously: the union cannot reach past this box.
    pad_lat = range_km / (math.pi / 180 * EARTH_RADIUS_KM)
    max_abs_lat = max(abs(lat) for _, lat in stations) + pad_lat
    pad_lon = pad_lat / max(math.cos(math.radians(min(max_abs_lat, 89.0))), 1e-9)
    lo_lon = min(x for x, _ in stations) - pad_lon
    hi_lon = max(x for x, _ in stations) + pad_lon
    lo_lat = min(y for _, y in stations) - pad_lat
    hi_lat = max(y for _, y in stations) + pad_lat

    prepared = prep(aoi_geometry)
    cell_deg2 = step_deg * step_deg
    scale = (math.pi / 180 * EARTH_RADIUS_KM) ** 2
    total = 0.0
    lat = lo_lat + step_deg / 2
    while lat < hi_lat:
        weight = math.cos(math.radians(lat)) * cell_deg2 * scale
        near_lat = [s for s in stations if abs(s[1] - lat) <= pad_lat]
        if near_lat:
            lon = lo_lon + step_deg / 2
            while lon < hi_lon:
                if within_range_of_any(lon, lat, near_lat, range_km) and prepared.covers(
                    Point(lon, lat)
                ):
                    total += weight
                lon += step_deg
        lat += step_deg
    return total


def aoi_coverage(
    aoi_geometry,
    aoi_id: str,
    aoi_content_hash: str,
    stations: Sequence[tuple[float, float]],
    range_km: float | None,
    range_source: str | None,
    range_at_candidate_ceiling: bool | None,
    prediction_grid_area_km2: float | None = None,
    step_deg: float = QUADRATURE_STEP_DEG,
) -> dict:
    """The coverage block, in the shape the ordering problem forces.

    THE ORDERING PROBLEM, resolved in the OUTPUT rather than in a doc
    (G.2-PRE §3). The fitted range comes from a FIT, which comes from a RUN,
    so coverage-against-the-AOI is a per-run derived value that MOVES when the
    fit moves. What does NOT move is the denominator. So the block separates
    them by name:

      * `stable` — run-independent and citable on its own: the AOI's identity,
        hash and area. External, fixed, and the reason (b) was chosen over a
        data-defined boundary.
      * `per_run` — must be quoted WITH its run: the range, the supported
        area, the fraction.

    and `statement` emits the honest form directly — a fixed denominator with
    a dated numerator — so a reader who quotes one sentence quotes a true one.

    `range_km` None (no estimator fitted a range) yields a block with
    `per_run: None` rather than a zero: no support MEASURED and no support
    COMPUTABLE are different facts, and a 0.0 would read as the first.
    """
    aoi_area = polygon_area_km2(aoi_geometry)
    stable = {
        "aoi_id": aoi_id,
        "aoi_content_hash": aoi_content_hash,
        "aoi_area_km2": aoi_area,
        "n_training_stations": len(stations),
        "note": (
            "RUN-INDEPENDENT. The AOI is externally defined (Contract 2) and does "
            "not move as the corpus grows — which is what makes a coverage "
            "fraction comparable across runs at all. Citable without a run id."
        ),
    }
    if prediction_grid_area_km2 is not None:
        stable["prediction_grid_area_km2"] = prediction_grid_area_km2
        stable["prediction_grid_fraction_of_aoi"] = (
            prediction_grid_area_km2 / aoi_area if aoi_area else None
        )

    if range_km is None or not stations:
        return {
            "stable": stable,
            "per_run": None,
            "method": METHOD_NOTE,
            "statement": (
                f"The AOI is {aoi_area:,.0f} km2 ({aoi_id}). No estimator in this run "
                "fitted a correlation range, so the supported fraction is NOT COMPUTABLE "
                "here — which is not the same as zero."
            ),
        }

    supported = supported_area_km2(aoi_geometry, stations, range_km, step_deg)
    fraction = supported / aoi_area if aoi_area else None
    ceiling_clause = (
        " itself AT ITS CANDIDATE CEILING, so the supported area is a LOWER BOUND"
        if range_at_candidate_ceiling
        else ""
    )
    return {
        "stable": stable,
        "per_run": {
            "range_km": range_km,
            "range_source": range_source,
            "range_at_candidate_ceiling": range_at_candidate_ceiling,
            "supported_area_km2": supported,
            "fraction_of_aoi_supported": fraction,
            "quadrature_step_deg": step_deg,
            "note": (
                "PER-RUN. The range comes from a fit, which comes from this run, so "
                "these three numbers move when the fit moves. Never quote them without "
                "the run that produced them."
            ),
        },
        "method": METHOD_NOTE,
        "statement": (
            f"{fraction * 100:.3f}% of the {aoi_area:,.0f} km2 AOI ({aoi_id}) lies within "
            f"one fitted variogram range ({range_km:.3f} km, from {range_source}"
            f"{ceiling_clause}) of any of the {len(stations)} training stations "
            f"— {supported:,.0f} km2. The denominator is fixed; the numerator is this "
            "run's."
        ),
    }


def grid_predictable_area_km2(
    transform: Sequence[float], width: int, height: int, predictable
) -> float:
    """Area of the PREDICTABLE cells, cos(lat)-weighted.

    The predictable set, not the full extent: masked cells are cells the
    covariates do not define, so counting them would overstate the domain the
    run can actually speak about. (On today's synthetic stack that is 2,880 of
    3,400 cells; the extent-box area would be ~18% larger and would be the
    wrong number to compare against the AOI.)
    """
    a, _, _, _, e, f = transform[:6]
    scale = (math.pi / 180 * EARTH_RADIUS_KM) ** 2
    cell = abs(a) * abs(e) * scale
    total = 0.0
    for row in range(height):
        lat = f + (row + 0.5) * e
        weight = math.cos(math.radians(lat)) * cell
        base = row * width
        for col in range(width):
            if predictable[base + col]:
                total += weight
    return total
