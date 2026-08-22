"""The TS-6 comparison (E3.3): one grid, computed origin, declared inflation.

    TS6Surface (Contract 6)          PredictionGrid + SurfaceResult (E3.1+2)
          │                                     │
          ▼                                     │
    resample_ts6_to_grid  ── nearest ──►  ONE GRID: OURS
          │                                     │
          └────────────┬────────────────────────┘
                       ▼
            compare_surface_to_ts6  ──►  TS6Agreement
            (commit 2: r · N_eff · mean difference · refusals)

WHICH GRID, AND WHY (commit 1's decision, recorded here rather than implied):
the comparison happens on OUR grid — the feature stack's native grid that
E3.1+2 inherited without resampling. Resampling OUR surface would introduce
interpolation into values the surface builder just took care NOT to
interpolate; the TS-6 raster is the input that moves. WHAT THAT COSTS, stated
rather than hidden: TS-6 is a compiled coarse product (0.1° native per
Contract 6's grid_note), and upsampling it to a finer grid cannot add
information it does not have. NEAREST NEIGHBOUR is used for exactly that
reason — it repeats the compiled values into blocks instead of inventing
smooth detail between them (bilinear would manufacture gradients TS-6 never
published). The resampling's provenance travels with the comparison.

THE COMPARISON'S ORIGIN IS COMPUTED, NEVER DECLARED. `combine_origins` over
the two inputs — our surface's computed origin and the TS-6 input's DECLARED
origin (`TS6Surface.data_origin`, mirroring Contract 6 v3's
`raster_data_origin`). Least-real wins: a MEASURED TS-6 cannot launder a
synthetic-DEM surface, and a real surface cannot launder a fixture benchmark.
Today both inputs are SYNTHETIC and the comparison is SYNTHETIC — which is
the honest label for a number that exercises machinery and measures nothing
about TS-6.

GRID IS A BENCHMARK CLASS, NEVER A TRAINING STATION (Contract 1's evidence
discipline). This module imports nothing from `ingestion/`, `samples/` or the
corpus path, and the suite asserts that structurally — the comparison CANNOT
feed the corpus, as a test rather than a comment.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from engine.prospectivity.domain.results import TS6Agreement
from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.provenance.origin import DataOrigin, combine_origins
from engine.prospectivity.surfaces.grid import PredictionGrid


@dataclass(frozen=True)
class ResampledTS6:
    """The TS-6 values on OUR grid, with the resampling recorded as data."""

    values: np.ndarray  # (H, W) float64, NaN where TS-6 has no data
    provenance: dict


def comparison_origin(
    surface_data_origin: DataOrigin | str, ts6_data_origin: DataOrigin | str | None
) -> DataOrigin:
    """The comparison artifact's origin: the LEAST-REAL of its two inputs.

    A TS-6 input with NO declared origin is refused rather than defaulted —
    "declaration or nothing" (P2.0d-3): a silent default here would let an
    undeclared benchmark pass as whatever flatters the comparison.
    """
    if ts6_data_origin is None:
        raise ValueError(
            "the TS-6 input carries no declared data_origin — the comparison's "
            "origin is COMPUTED from its inputs and cannot be computed from an "
            "undeclared one. Declare it on the TS6Surface (the fixture declares "
            "SYNTHETIC; the real digitized raster is DERIVED per Contract 6 v3 "
            "raster_data_origin)."
        )
    return combine_origins([surface_data_origin, ts6_data_origin])


def resample_ts6_to_grid(ts6: TS6Surface, grid: PredictionGrid) -> ResampledTS6:
    """TS-6's raster on OUR grid, by nearest neighbour.

    Nearest, not bilinear, deliberately: when the TS-6 grid is coarser than
    ours, nearest REPEATS each compiled value into a block — visibly coarse,
    honestly coarse — where bilinear would invent smooth gradients between
    values TS-6 never published. When the grids already coincide (today's
    fixture) the operation is an identity, and the provenance records that
    too rather than leaving a reader to infer it.
    """
    with rasterio.open(ts6.raster_path) as dataset:
        source = dataset.read(1).astype(np.float64)
        source_transform = dataset.transform
        source_crs = dataset.crs
        source_nodata = dataset.nodata
        source_res = (dataset.transform.a, -dataset.transform.e)

    if source_nodata is not None and not np.isnan(source_nodata):
        source = np.where(source == source_nodata, np.nan, source)

    destination = np.full((grid.height, grid.width), np.nan)
    reproject(
        source=source,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=rasterio.Affine(*grid.transform),
        dst_crs=grid.crs,
        resampling=Resampling.nearest,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )
    destination.flags.writeable = False

    same_grid = (
        tuple(source_transform)[:6] == grid.transform
        and source.shape == (grid.height, grid.width)
    )
    upsampled = source_res[0] > grid.res_x_deg or source_res[1] > grid.res_y_deg
    return ResampledTS6(
        values=destination,
        provenance={
            "target_grid": "ours (the feature stack's native grid) — resampling "
            "our surface would interpolate values the builder took care not to",
            "method": "nearest",
            "method_reason": "repeats compiled values into blocks rather than "
            "inventing smooth detail between them",
            "source_resolution_deg": [float(source_res[0]), float(source_res[1])],
            "target_resolution_deg": [grid.res_x_deg, grid.res_y_deg],
            "identity": bool(same_grid),
            "upsampling_note": (
                "TS-6 is coarser than the target grid: the resampled values "
                "REPEAT in blocks and carry no detail below the source "
                "resolution — the comparison inherits that, it does not hide it"
                if upsampled
                else "no upsampling: source resolution is at or below the target's"
            ),
            "ts6_source_id": ts6.source_id,
            "ts6_content_hash": ts6.content_hash,
        },
    )


# ═══════════════════════════════════════════════ commit 2: the agreement

# The repo root, computed locally rather than via
# `ingestion._contract_paths.find_repo_root` DELIBERATELY: this module's
# structural test asserts its import graph reaches nothing under
# `prospectivity.ingestion` (the comparison cannot feed the corpus), and a
# path helper that happens to live there would trip the fence for a
# convenience import.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TS6_CONTRACT_PATH = _REPO_ROOT / "data" / "ts6" / "ts6_reference.yaml"

# THE SPECIFICITY FLOOR for `digitization_method`, same trade-off as TAX.1's
# MIN_DETERMINISM_BASIS_CHARS and stated the same way: a minimum length is
# CRUDE but MECHANICALLY OBSERVABLE, where "must name figure, edition,
# georeferencing and value extraction" is better in principle and not
# checkable without reading English. Note that all three of Contract 6's
# vocabulary options — "georeferenced raster scan" (24), "table
# interpolation" (19), "contour vectorization" (21) — fall BELOW this floor:
# they name the CATEGORY of procedure, not a re-runnable procedure, and are
# correctly insufficient alone. WHAT THIS DOES NOT CATCH: a long sentence
# naming nothing. The check verifies effort, not meaning; review is the
# observer for vacuity.
MIN_DIGITIZATION_METHOD_CHARS = 40

# THE LIMIT — required in the emitted output NEXT TO the correlation, per
# Karl's decision (E3.0 §5), not only in a doc.
INFLATION_NOTE = (
    "The naive correlation's df is fiction: both surfaces are smooth by "
    "construction, so the effective number of independent observations is far "
    "below the cell count, and n_eff is printed beside r for that reason. NO "
    "p-value is reported: a correction adjusts DEGREES OF FREEDOM; it cannot "
    "manufacture information. The real problem is that the prediction surface "
    "is near-constant over ~99% of its domain, and no test corrects for that."
)


def _load_ts6_contract() -> dict:
    import yaml

    loaded = yaml.safe_load(_TS6_CONTRACT_PATH.read_text())
    return loaded.get("ts6_reference") or {}


def ts6_digitization_uncertainty(contract: dict | None = None) -> float:
    """The benchmark's digitization uncertainty, from Contract 6 — with the
    ABSENT / NULL / PRESENT states kept apart (the C8.1 loader posture).

    TODAY THE SLOT DOES NOT EXIST in Contract 6 — the E3.3 prompt said "that
    field is null", and verification found it ABSENT, which is a different
    state: adding the slot is a STRUCTURAL contract change (version bump,
    Karl), recorded in docs/BACKLOG.md rather than made unilaterally here.
    This accessor is the slot's consumer-in-waiting, exactly as
    `model_config.acceptance_thresholds` was before C8.1.
    """
    contract = contract if contract is not None else _load_ts6_contract()
    if "digitization_uncertainty" not in contract:
        raise ValueError(
            "Contract 6 has no digitization_uncertainty SLOT — a missing field "
            "is not an explicitly-null one. Adding it is a structural contract "
            "change (reference_version bump, Karl; docs/BACKLOG.md carries the "
            "decision). Until it exists, a digitized TS-6 raster cannot state "
            "its own error and the comparison refuses to treat it as exact."
        )
    value = contract["digitization_uncertainty"]
    if value is None:
        raise ValueError(
            "Contract 6's digitization_uncertainty is explicitly NULL — the "
            "digitized raster arrived without its error, and a comparison that "
            "assumed zero would overstate its own precision. The value is Track "
            "G's to fill with the digitization (G3.1)."
        )
    return float(value)


def _require_digitization_evidence(contract: dict | None) -> tuple[float, str]:
    """The REAL path's gate: a digitized (non-SYNTHETIC) benchmark must carry
    its uncertainty and a re-runnable method. The refusals are the OBSERVER
    for both requirements — without them the fields are documentation."""
    uncertainty = ts6_digitization_uncertainty(contract)
    contract = contract if contract is not None else _load_ts6_contract()
    method = contract.get("digitization_method")
    if not (method and str(method).strip()):
        raise ValueError(
            "Contract 6's digitization_method is null — DERIVED's evidence is "
            "the procedure that produced the artifact, and a digitized raster "
            "without one is an unevidenced DERIVED claim (TAX.1's rule, one "
            "field over)."
        )
    if len(str(method).strip()) < MIN_DIGITIZATION_METHOD_CHARS:
        raise ValueError(
            f"Contract 6's digitization_method {str(method).strip()!r} is too "
            f"short to be re-run (< {MIN_DIGITIZATION_METHOD_CHARS} chars) — it "
            "names a CATEGORY of procedure, not a procedure. Record which "
            "figure, which edition, what georeferencing and what value "
            "extraction — the same reason a bare 'deterministic' is refused as "
            "a determinism basis (TAX.1)."
        )
    return uncertainty, str(method).strip()


def _naive_pearson(ours: np.ndarray, ts6: np.ndarray) -> tuple[float | None, str]:
    """Pearson r with the degenerate case handled BY NAME, naming WHICH side
    is constant — the mean baseline's surface IS constant and kriging's is
    nearly so, so this branch is not hypothetical, and 'undefined' without a
    side would send a reader to the wrong surface.

    ZERO IS NUMERICAL, not exact (the E2.4 metrics policy, ZERO_TOL_REL): the
    baseline's constant surface measures sd = 3.55e-15, not 0.0 — mean
    subtraction leaves ULP noise on every element — and an exact-zero test
    let it through to np.corrcoef, which returned an r made entirely of that
    noise, labelled "ok". Found by running the real comparison, not by a
    unit test; the constant-surface fixture below now uses the baseline's
    real surface so the noise is in the test's path too."""
    from engine.prospectivity.validation.metrics import ZERO_TOL_REL

    scale = max(float(np.abs(ours).max()), float(np.abs(ts6).max()), 1e-300)
    tolerance = ZERO_TOL_REL * scale
    ours_sd = float(ours.std())
    ts6_sd = float(ts6.std())
    constant_sides = [
        name
        for name, sd in (("prediction surface", ours_sd), ("ts6 benchmark", ts6_sd))
        if sd <= tolerance
    ]
    if constant_sides:
        return None, (
            "undefined — constant input: "
            + " and ".join(constant_sides)
            + " has zero variance, so correlation does not exist"
        )
    r = float(np.corrcoef(ours, ts6)[0, 1])
    return r, "ok"


def effective_sample_size(
    ours: np.ndarray,
    ts6: np.ndarray,
    centres_lonlat: np.ndarray,
    n_bins: int = 20,
) -> float | None:
    """Clifford–Richardson-style effective sample size for the correlation of
    two spatially autocorrelated surfaces.

    N_eff = N² / Σᵢⱼ ρ̂A(dᵢⱼ)·ρ̂B(dᵢⱼ), with each surface's correlogram ρ̂
    estimated empirically in distance bins over the compared cells. Two
    white-noise surfaces give ρ̂ ≈ 0 off-diagonal → N_eff ≈ N; two smooth
    surfaces give ρ̂ ≈ 1 out to long lags → N_eff collapses toward 1, which
    is the inflation this project already measured as random-k-fold leakage
    wearing a new costume. Clamped to [1, N]; None when either surface is
    constant (its correlogram does not exist — the degenerate case travels
    with the correlation's).
    """
    n = ours.size
    a = ours - ours.mean()
    b = ts6 - ts6.mean()
    from engine.prospectivity.validation.metrics import ZERO_TOL_REL

    scale = max(float(np.abs(ours).max()), float(np.abs(ts6).max()), 1e-300)
    a_var, b_var = float(np.mean(a * a)), float(np.mean(b * b))
    # the same NUMERICAL zero as _naive_pearson: sd (not variance) against
    # the tolerance, so the two degeneracy verdicts cannot disagree
    if np.sqrt(a_var) <= ZERO_TOL_REL * scale or np.sqrt(b_var) <= ZERO_TOL_REL * scale:
        return None

    lon = np.radians(centres_lonlat[:, 0])
    lat = np.radians(centres_lonlat[:, 1])
    half_dlat = (lat[None, :] - lat[:, None]) / 2.0
    half_dlon = (lon[None, :] - lon[:, None]) / 2.0
    haversine = (
        np.sin(half_dlat) ** 2
        + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(half_dlon) ** 2
    )
    distance = 2.0 * 6371.0088 * np.arcsin(np.sqrt(np.clip(haversine, 0.0, 1.0)))

    i_upper, j_upper = np.triu_indices(n, k=1)
    pair_distance = distance[i_upper, j_upper]
    bins = np.linspace(0.0, float(pair_distance.max()) + 1e-9, n_bins + 1)
    which_bin = np.digitize(pair_distance, bins) - 1

    products_a = (a[i_upper] * a[j_upper]) / a_var
    products_b = (b[i_upper] * b[j_upper]) / b_var
    total = float(n)  # the diagonal: ρA·ρB = 1 at lag 0, n times
    for k in range(n_bins):
        in_bin = which_bin == k
        count = int(in_bin.sum())
        if count == 0:
            continue
        rho_a = float(np.clip(products_a[in_bin].mean(), -1.0, 1.0))
        rho_b = float(np.clip(products_b[in_bin].mean(), -1.0, 1.0))
        total += 2.0 * count * rho_a * rho_b  # ×2: each unordered pair twice
    return float(np.clip(n * n / max(total, 1.0), 1.0, n))


def compare_surface_to_ts6(
    result,
    grid: PredictionGrid,
    ts6: TS6Surface,
    *,
    surface_data_origin: DataOrigin | str,
    contract: dict | None = None,
):
    """One surface's agreement with TS-6 — a MEASUREMENT with its inflation
    and its benchmark error declared, never a judgement (the scope fence:
    G3.2's acceptable-agreement slot stays null and E2.5's guard is what
    refuses a claim; this code reports).

    `contract` is the testability seam (the `target_definition` precedent);
    production callers omit it and the real Contract 6 is read.
    """
    from engine.prospectivity.surfaces.writer import surface_watermark

    # REFUSAL 1 — the circularity marker. role_note is what separates an
    # independent benchmark from a circular reproduction check, and a
    # comparison that ASSUMED one would label its own number.
    if ts6.role_note is None:
        raise ValueError(
            "TS6Surface.role_note is null — benchmark_only vs "
            "reproduction_check is the CIRCULARITY marker, and the comparison "
            "refuses to run rather than assume independence. Contract 6's "
            "field is [GEOLOGY — ISAAC]; the fixture declares its own."
        )

    origin = comparison_origin(surface_data_origin, ts6.data_origin)

    # THE TWO PATHS, branched on the DECLARED origin — never on a name or a
    # path. SYNTHETIC is the lenient branch deliberately: nothing was
    # digitized, so there IS no digitization error to demand.
    if ts6.data_origin == DataOrigin.SYNTHETIC.value:
        benchmark_uncertainty = None
        benchmark_note = (
            "not applicable — synthetic fixture, not a digitized surface"
        )
    else:
        benchmark_uncertainty, method = _require_digitization_evidence(contract)
        benchmark_note = (
            f"digitization uncertainty {benchmark_uncertainty} kg/m² "
            f"(Contract 6); method: {method}"
        )

    resampled = resample_ts6_to_grid(ts6, grid)
    valid = grid.predictable & np.isfinite(resampled.values) & np.isfinite(result.mu)
    ours = result.mu[valid]
    benchmark = resampled.values[valid]
    n_cells = int(valid.sum())
    if n_cells == 0:
        raise ValueError(
            "the surfaces share no valid cells — an empty comparison is not a "
            "comparison"
        )

    r, correlation_status = _naive_pearson(ours, benchmark)
    centres = grid.cell_centres()[valid.ravel()]
    n_eff = effective_sample_size(ours, benchmark, centres)

    difference = ours - benchmark
    mean_difference = float(difference.mean())
    rmse = float(np.sqrt(np.mean(difference**2)))

    if r is None or n_eff is None:
        interpretation = (
            f"correlation {correlation_status}; no interpretation is offered "
            "for a number that does not exist"
        )
    else:
        noise_scale = 2.0 / float(np.sqrt(n_eff))
        distinguishable = abs(r) >= noise_scale
        interpretation = (
            f"naive r = {r:+.3f} over {n_cells} cells, but n_eff ≈ "
            f"{n_eff:.1f}: at that effective sample size the sampling-noise "
            f"scale for r is ~{min(noise_scale, 2.0):.2f}, so this correlation "
            + (
                "exceeds it — a descriptive association, still not a claim"
                if distinguishable
                else "is NOT distinguishable from zero — the honest reading is "
                "that the comparison carries no evidence of association"
            )
        )

    return TS6Agreement(
        estimator_name=result.estimator_name,
        spatial_correlation=r,
        correlation_status=correlation_status,
        n_cells=n_cells,
        n_eff=n_eff,
        n_eff_method=(
            "Clifford–Richardson-style: N²/ΣρAρB over binned empirical "
            "correlograms of the two surfaces (20 distance bins)"
        ),
        interpretation=interpretation,
        inflation_note=INFLATION_NOTE,
        mean_difference=mean_difference,
        mean_difference_note=(
            "positive = the prediction surface sits ABOVE the TS-6 benchmark; "
            "interpretable regardless of the correlation problem"
        ),
        rmse=rmse,
        role_note=ts6.role_note,
        benchmark_uncertainty=benchmark_uncertainty,
        benchmark_uncertainty_note=benchmark_note,
        data_origin=origin.value,
        watermark=surface_watermark(origin),
        resampling=resampled.provenance,
    )


def compare_all_to_ts6(
    surfaces,
    grid: PredictionGrid,
    ts6: TS6Surface,
    *,
    surface_data_origin: DataOrigin | str,
    contract: dict | None = None,
) -> dict:
    """Every surface, compared — ITERATE, never cherry-pick (the E2.4
    obligation). Returns a mapping keyed by estimator name; whether the
    MANIFEST records one agreement or many is E3.4's open arity question
    (docs/BACKLOG.md §3), which this shape leaves expressible both ways."""
    return {
        name: compare_surface_to_ts6(
            surfaces[name],
            grid,
            ts6,
            surface_data_origin=surface_data_origin,
            contract=contract,
        )
        for name in sorted(surfaces)
    }
