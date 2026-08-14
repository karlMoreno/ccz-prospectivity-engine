"""Covariate extraction at station locations + the single-DEM guard (E2.0-2).

Deliberately NOT a pattern (PATTERNS.md §4.4 named this in advance): one
validation function and one sampling function. There is exactly one sampling
method and no second is coming on a schedule, so a PointSampler Strategy
would be a seam without a variation point — the ceremony PATTERNS.md §3
objects to. The recorded `sampling_method` field is what makes a future swap
auditable; promotion to a Strategy happens the day bilinear is actually
wanted, not before.

    DemGrid ──┐
              ├──► require_single_dem(layers[, grid]) ── refuse BY NAME on
    layers ───┤        any dem.resolution_deg / dem.content_hash disagreement
    (CovariateResult,  (Contract 3 v3: "covariates computed from DEMs of
     each carrying      different resolutions must NEVER be mixed in one
     provenance["dem"]) training matrix")
              │
    stations ─┴──► extract_covariates_at_stations(grid, layers, stations)
                        │  nearest cell per station (containing cell)
                        ▼
                   CovariateExtraction
                     .values (n_stations × n_covariates, NaN carried)
                     .sampling_method == "nearest_cell"   (recorded)
                     .shared_cell_count / .cell_groups    (recorded)
                     .nan_stations                        (flagged, never dropped)

THE GUARD'S REAL THREAT (stated so the guard is built against it, not against
the convenient one): every layer of ONE stack copies the same
`DemGrid.provenance()` — a single stack is structurally incapable of
disagreeing with itself. What the guard protects against is an extraction
assembled from layers of DIFFERENT stacks (the Checkpoint-1 transition:
0.1-degree synthetic layers accidentally combined with ~460 m GEBCO layers).
The guard also verifies the sampling grid itself against the layers'
recorded DEM: the transform that geolocates a station must belong to the
same DEM the covariate values were computed from, or every sampled cell is
silently wrong. Honest limit (the P2.0d-2 language): a record-checking
guard checks RECORDS — an array swapped between two DEMs under a copied
provenance dict passes it undetectably; the array-shape check below catches
the detectable subset (stale provenance beside a regenerated raster), and
review is what exists to catch the rest.

SAMPLING METHOD — nearest cell, the E2.0-2 decision, alternative recorded:
bilinear interpolation was considered and declined for the alpha. It
propagates the nan_border inward by a cell, and it invents values between
cells — on a DEM whose derivative covariates are computed with a stated
border policy, interpolating those derivatives compounds two approximations
and makes the recorded provenance less exactly true of the number.

The known consequence of nearest-cell, RECORDED not hidden: on the
0.1-degree synthetic DEM a cell is ~11 km, so several stations within one
~12 km cluster resolve to the SAME cell and receive IDENTICAL covariate
values (they separate on real GEBCO, ~460 m at 13N). Two stations sharing a
cell have identical X and different y — irreducible error no covariate model
can beat — so `shared_cell_count` / `cell_groups` are part of the output:
the effective sample size for anything covariate-driven, not a curiosity.

BORDER / MISSING VALUES: a station whose cell is NaN for some covariate is
NOT dropped and NOT filled — the NaN is carried into `values` and the
station is flagged by name in `nan_stations` (flag-never-drop, the corpus's
own rule). A station OUTSIDE the raster extent is a different condition and
REFUSES by name: it has no cell, so it is not a border-policy consequence
but a broken extent — the E1.4 preflight found the synthetic DEM containing
0 of 35 stations, and a quiet all-NaN row is exactly how that bug class
would hide.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.recipe import CovariateResult

SAMPLING_METHOD_NEAREST_CELL = "nearest_cell"

# The two per-layer DEM-identity facts the guard compares. resolution_deg is
# the contract rule (Contract 3 v3, covariates.yaml "NATIVE-RESOLUTION
# OPERATORS" note); content_hash is the stricter same-terrain identity —
# two different DEMs at the same resolution are equally inadmissible in one
# matrix, because the layers would describe different seafloors.
_DEM_IDENTITY_FIELDS = ("resolution_deg", "content_hash")


@dataclass(frozen=True)
class Station:
    """One point to sample: id + WGS84 coordinate. Kept minimal so tests can
    place stations at exact coordinates without constructing a full
    Observation; production callers use `from_observation`."""

    station_id: str
    longitude: float
    latitude: float

    @classmethod
    def from_observation(cls, obs: Observation) -> "Station":
        # station_id deliberately holds source_record_id, NOT the corpus's
        # own (colliding) Observation.station_id field — which is None for
        # all 35 training rows — and not event_id: source_record_id is the
        # one identity that is unique, non-null, and joins back to a corpus
        # row. E2.0-3 writes these ids into provenance; do not "fix" this
        # toward the same-named field.
        return cls(
            station_id=obs.source_record_id,
            longitude=obs.longitude,
            latitude=obs.latitude,
        )


@dataclass(frozen=True)
class CovariateExtraction:
    """The sampled matrix block plus the facts a reviewer needs with it.

    NOT a provenance artifact (that is E2.0-3's TrainingMatrixManifest) —
    a plain value object carrying the numbers and their recorded caveats.
    """

    station_ids: tuple[str, ...]
    covariate_names: tuple[str, ...]  # matrix column order == registry order
    values: np.ndarray  # (n_stations, n_covariates) float64; NaN carried
    cells: tuple[tuple[int, int], ...]  # (row, col) per station, station order
    sampling_method: str
    distinct_cell_count: int
    # Stations occupying a cell that >= 2 stations occupy — the count E2.0-3
    # records into provenance. 0 means every station carries independent X.
    shared_cell_count: int
    # Every occupied cell's stations, sorted by cell (row, col); station ids
    # sorted within each group. Groups of size 1 included, so the grouping is
    # the full occupancy picture, not only the collisions.
    cell_groups: tuple[tuple[str, ...], ...]
    # (station_id, (covariate names NaN at its cell, ...)) — flagged by name,
    # values carried as NaN in `values`. Never dropped, never filled.
    nan_stations: tuple[tuple[str, tuple[str, ...]], ...] = field(default_factory=tuple)


def _layer_dem_identity(layer: CovariateResult) -> dict:
    dem = layer.provenance.get("dem")
    if not isinstance(dem, dict):
        raise ValueError(
            f"layer {layer.name!r} has no provenance['dem'] block — every covariate "
            "layer must record the DEM it was computed from (recipe.py attaches it; "
            "a layer without one cannot prove single-DEM admissibility)"
        )
    missing = [key for key in _DEM_IDENTITY_FIELDS if key not in dem]
    if missing:
        raise ValueError(
            f"layer {layer.name!r} provenance['dem'] is missing {missing} — cannot "
            "verify the Contract 3 single-DEM rule without them"
        )
    return dem


def require_single_dem(
    layers: list[CovariateResult] | tuple[CovariateResult, ...],
    grid: DemGrid | None = None,
) -> None:
    """The Contract 3 v3 single-DEM rule, enforced at extraction (BACKLOG §3
    item, open since E1.4): refuse if any two layers disagree on the recorded
    DEM resolution or content hash — naming the layers and the field. A
    validation function, deliberately not a pattern.

    When `grid` is given, it must also match: the grid supplies the
    geotransform that maps stations to cells, so a grid that is not the
    layers' DEM would sample every station at a coordinate-shifted cell
    while looking perfectly healthy.
    """
    if not layers:
        raise ValueError(
            "no covariate layers given — refusing to validate an empty stack "
            "(an empty extraction must never look like a passing one)"
        )
    for identity_field in _DEM_IDENTITY_FIELDS:
        by_value: dict[str, list[str]] = {}
        for layer in layers:
            value = _layer_dem_identity(layer)[identity_field]
            by_value.setdefault(repr(value), []).append(layer.name)
        if len(by_value) > 1:
            detail = "; ".join(
                f"{sorted(names)} record {value}" for value, names in sorted(by_value.items())
            )
            raise ValueError(
                f"single-DEM rule (Contract 3 v3): layers disagree on dem.{identity_field} — "
                f"{detail}. Covariates from different DEMs must never be mixed in one "
                "training matrix."
            )
    if grid is not None:
        dem = _layer_dem_identity(layers[0])
        grid_identity = {
            "resolution_deg": [grid.res_x_deg, grid.res_y_deg],
            "content_hash": grid.content_hash,
        }
        for identity_field in _DEM_IDENTITY_FIELDS:
            if dem[identity_field] != grid_identity[identity_field]:
                raise ValueError(
                    f"single-DEM rule (Contract 3 v3): the sampling grid's "
                    f"{identity_field} ({grid_identity[identity_field]!r}) does not match "
                    f"the layers' recorded dem.{identity_field} ({dem[identity_field]!r}) — "
                    "stations would be geolocated on a different DEM than the one the "
                    "covariates were computed from."
                )


def _nearest_cell(grid: DemGrid, longitude: float, latitude: float) -> tuple[int, int] | None:
    """Containing cell == nearest cell centre for any point inside the
    raster. A point exactly on a shared cell edge is equidistant to both
    centres; floor resolves the tie to the east/south cell. Honest caveats,
    both found the hard way: (1) the tie-break only operates when the
    boundary offset is exactly representable in binary floating point (e.g.
    a 0.125-degree grid) — on a 0.1-degree grid a nominal edge coordinate
    lands by float rounding, one side or the other, deterministically for a
    given input. (2) This subtract-then-divide arithmetic agrees with
    rasterio's inverse-affine `index()` for interior points (0 of 200,000
    random probes disagreed; 0 of the 35 real stations, nearest ~0.05 cells
    from an edge) but DIVERGES at nominal cell-boundary decimals on
    non-representable grids — the E2.0-2 adversarial review demonstrated
    lat 14.6 on the 0.1-degree frame resolving one row apart. Kept as our
    own arithmetic anyway, deliberately: delegating to rasterio would make
    the test that compares the two a tautology. The first corpus station
    sitting on a nominal boundary will fail that comparison test loudly —
    which is the correct behavior, since either answer is defensible and a
    human should pick. Returns None when the point is outside the raster
    extent (no containing cell exists)."""
    west = grid.transform.c
    north = grid.transform.f
    col = int(np.floor((longitude - west) / grid.res_x_deg))
    row = int(np.floor((north - latitude) / grid.res_y_deg))
    height, width = grid.values.shape
    if not (0 <= row < height and 0 <= col < width):
        return None
    return (row, col)


def extract_covariates_at_stations(
    grid: DemGrid,
    layers: list[CovariateResult] | tuple[CovariateResult, ...],
    stations: list[Station] | tuple[Station, ...],
) -> CovariateExtraction:
    """Sample every covariate layer at every station by nearest cell.

    Runs `require_single_dem(layers, grid)` first — no extraction happens
    over an inadmissible stack. Row order is the given station order; column
    order is the given layer order (the registry's contract order when the
    layers come from `build_all`). Deterministic: same inputs, same output,
    no dict-iteration or set-order dependence anywhere.
    """
    require_single_dem(layers, grid)
    names = [layer.name for layer in layers]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(
            f"duplicate covariate layer name(s) {duplicates} — two layers under one "
            "name would silently shadow each other in the matrix"
        )
    if not stations:
        raise ValueError("no stations given — refusing to extract an empty matrix")
    station_ids = [station.station_id for station in stations]
    duplicate_ids = sorted({sid for sid in station_ids if station_ids.count(sid) > 1})
    if duplicate_ids:
        raise ValueError(
            f"duplicate station id(s) {duplicate_ids} — the same station twice would "
            "silently double-weight one physical location"
        )

    # Layer arrays must be the grid's own geometry: a stale or copied
    # provenance beside a regenerated/cropped raster passes the record check
    # but shows up here as a shape mismatch — refuse by name rather than
    # silently sampling the wrong geometry or dying in an anonymous
    # IndexError (E2.0-2 adversarial review, probe-demonstrated).
    misshapen = sorted(
        f"{layer.name} {layer.values.shape}"
        for layer in layers
        if layer.values.shape != grid.values.shape
    )
    if misshapen:
        raise ValueError(
            f"layer array shape does not match the sampling grid {grid.values.shape}: "
            f"{misshapen} — the recorded DEM identity agrees but the arrays are not "
            "that DEM's geometry (stale provenance beside a regenerated raster?)"
        )

    non_finite = sorted(
        station.station_id
        for station in stations
        if not (np.isfinite(station.longitude) and np.isfinite(station.latitude))
    )
    if non_finite:
        raise ValueError(
            f"station(s) with non-finite coordinates: {non_finite} — refusing by name "
            "rather than dying in an unnamed conversion error"
        )

    cells: list[tuple[int, int]] = []
    off_raster: list[str] = []
    for station in stations:
        cell = _nearest_cell(grid, station.longitude, station.latitude)
        if cell is None:
            off_raster.append(station.station_id)
            cells.append((-1, -1))  # placeholder; the refusal below fires
        else:
            cells.append(cell)
    if off_raster:
        raise ValueError(
            f"station(s) outside the DEM extent: {off_raster} — no containing cell "
            "exists, so this is a broken extent (the E1.4 preflight bug class), not a "
            "border case. Fix the DEM extent or the station coordinates; refusing "
            "loudly rather than emitting all-NaN rows that would hide it."
        )

    values = np.empty((len(stations), len(layers)), dtype=np.float64)
    for j, layer in enumerate(layers):
        for i, (row, col) in enumerate(cells):
            values[i, j] = float(layer.values[row, col])

    nan_stations: list[tuple[str, tuple[str, ...]]] = []
    for i, station in enumerate(stations):
        nan_names = tuple(names[j] for j in range(len(layers)) if np.isnan(values[i, j]))
        if nan_names:
            nan_stations.append((station.station_id, nan_names))

    occupancy: dict[tuple[int, int], list[str]] = {}
    for station, cell in zip(stations, cells):
        occupancy.setdefault(cell, []).append(station.station_id)
    cell_groups = tuple(
        tuple(sorted(occupancy[cell])) for cell in sorted(occupancy)
    )
    shared_cell_count = sum(len(group) for group in cell_groups if len(group) >= 2)

    # The accounting above was computed from `values`; freeze the array so a
    # downstream caller cannot silently invalidate it (freshly allocated, so
    # nothing else aliases it — review finding, E2.0-2).
    values.flags.writeable = False

    return CovariateExtraction(
        station_ids=tuple(station.station_id for station in stations),
        covariate_names=tuple(names),
        values=values,
        cells=tuple(cells),
        sampling_method=SAMPLING_METHOD_NEAREST_CELL,
        distinct_cell_count=len(occupancy),
        shared_cell_count=shared_cell_count,
        cell_groups=cell_groups,
        nan_stations=tuple(nan_stations),
    )
