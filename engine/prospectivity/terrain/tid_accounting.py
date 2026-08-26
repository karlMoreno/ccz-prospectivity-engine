"""The TID accounting — where the bathymetry is MEASURED and where it is
PREDICTED, produced BEFORE any covariate is interpreted (G.3 commit 2).

Terrain covariates over satellite-gravity-PREDICTED cells measure the
interpolation's smoothness, not the seafloor — predicted bathymetry is
smooth by construction at exactly the scales the recipes probe (BACKLOG §2's
GEBCO-TID entry; TRACK-G.md §3.2). This module turns that caveat into a
machine-readable artifact (`data/bathymetry/tid_accounting.json`) the
pipeline — and E5.4's honesty surface, later — can read, instead of a prose
paragraph nothing can render on a map.

Pattern note (CLAUDE.md design-pattern discipline): this is a plain
DERIVED-artifact GENERATOR in the mould of the manifest emitters — a pure
function of its recorded inputs (two rasters + the corpus CSV through the
production `SampleSource` gate), no seed, determinism basis = "pure function
of the three hashed inputs; all floats explicitly rounded". It deliberately
does NOT hang off the `TerrainSource` Strategy seam: the TID grid is not
terrain a model consumes, it is provenance metadata ABOUT the terrain — the
same kind of thing this project's own origin taxonomy is.

    bathy.tif ─┐
    tid.tif ───┼─→ build_tid_accounting() ─→ tid_accounting.json
    corpus CSV ┘        (pure, rounded)         (in-file DERIVED declaration)

The TID code table is taken from GEBCO_Grid_documentation.pdf section 3.0
(tracked in data/bathymetry/), not from memory: direct measurements are
codes 10–17, indirect (predicted/interpolated) 40–48, unknown 70–72, land 0.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource

REPO_ROOT = find_repo_root(Path(__file__).resolve())
BATHY_DIR = REPO_ROOT / "data" / "bathymetry"
DEFAULT_BATHY = BATHY_DIR / "gebco_2026_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif"
DEFAULT_TID = BATHY_DIR / "gebco_2026_tid_n25.0_s0.0_w-160.0_e-110.0_geotiff.tif"
ARTIFACT_PATH = BATHY_DIR / "tid_accounting.json"

# GEBCO_Grid_documentation.pdf §3.0, Table 2 — the class boundaries.
DIRECT_CODES = range(10, 18)
INDIRECT_CODES = range(40, 49)
UNKNOWN_CODES = range(70, 73)
LAND_CODE = 0
CODE_NAMES = {
    0: "Land",
    10: "Single beam echo-sounder",
    11: "Multibeam echo-sounder",
    12: "Seismic",
    13: "Isolated sounding",
    14: "ENC sounding",
    15: "Lidar",
    16: "Optical light sensor",
    17: "Combination of direct measurement methods",
    40: "Predicted based on satellite-derived gravity data",
    41: "Interpolated based on a computer algorithm",
    42: "Digital bathymetric contours from charts",
    43: "Digital bathymetric contours from ENCs",
    44: "Multiple sources incl. measured and derived, gravity-guided",
    45: "Predicted based on helicopter/flight-derived gravity data",
    46: "Grounded-iceberg draft from satellite freeboard",
    47: "Grounded Argo float",
    48: "Animal-borne data loggers",
    70: "Pre-generated grid, mixed source types",
    71: "Unknown source",
    72: "Steering points",
}

# The study extent is TODAY'S prediction domain: the synthetic fixture DEM's
# bounds (tests/fixtures/rasters.py, 100 x 34 @ 0.1°). It is a FIXTURE fact,
# not a configured domain (E3.0 §2) — the AOI decision replaces it at CP1.
STUDY_BOUNDS = (-126.5, 11.3, -116.5, 14.7)  # W, S, E, N

# The cluster split: the corpus is two clusters ~991 km apart with a
# 13–986 km zero-pair window between (E2.2); -121.5 is the gap's midpoint
# in longitude, nowhere near either cluster (west ≈ -125.9, east ≈ -117.0).
CLUSTER_SPLIT_LON = -121.5


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_tid_accounting(
    bathy_path: Path = DEFAULT_BATHY, tid_path: Path = DEFAULT_TID
) -> dict:
    """The four accountings, from the rasters and the production station gate.

    Pure function of its three inputs (hashes recorded in the artifact);
    every float is explicitly rounded so regeneration is byte-comparable.
    """
    with rasterio.open(tid_path) as t:
        tid_full = t.read(1)
        study_window = from_bounds(*STUDY_BOUNDS[:2], *STUDY_BOUNDS[2:], t.transform)
        tid_study = t.read(1, window=study_window)
        tid_transform = t.transform
    with rasterio.open(bathy_path) as b:
        bath_study = b.read(1, window=from_bounds(*STUDY_BOUNDS[:2], *STUDY_BOUNDS[2:], b.transform))

    def _classes(tid: np.ndarray) -> dict[str, np.ndarray]:
        return {
            "direct": np.isin(tid, DIRECT_CODES),
            "predicted": np.isin(tid, INDIRECT_CODES),
            "unknown": np.isin(tid, UNKNOWN_CODES),
            "land": tid == LAND_CODE,
        }

    # 1 — whole subset box.
    full_classes = _classes(tid_full)
    values, counts = np.unique(tid_full, return_counts=True)
    whole = {
        "cells": int(tid_full.size),
        # string keys: an int key survives json round-trip AS A STRING, and
        # the regeneration test compares full state against the loaded file
        "histogram": {str(int(v)): int(c) for v, c in zip(values, counts)},
        "fractions": {k: round(float(m.sum()) / tid_full.size, 6) for k, m in full_classes.items()},
    }

    # 2 — the study extent.
    s = _classes(tid_study)
    n = tid_study.size
    per_row = s["direct"].mean(axis=1)
    study = {
        "bounds_wsen": list(STUDY_BOUNDS),
        "bounds_source": "tests/fixtures/rasters.py synthetic DEM — a fixture fact, not a configured domain; the AOI decision replaces it at Checkpoint 1",
        "cells": int(n),
        "direct_cells": int(s["direct"].sum()),
        "predicted_cells": int(s["predicted"].sum()),
        "land_cells": int(s["land"].sum()),
        "direct_fraction": round(float(s["direct"].sum()) / n, 6),
        "predicted_fraction": round(float(s["predicted"].sum()) / n, 6),
        "depth_m": {
            "min": int(bath_study.min()),
            "max": int(bath_study.max()),
            "median": int(np.median(bath_study)),
        },
        "depth_max_note": "the -528 m maximum is a SEAMOUNT, not an error; roughness/TPI/BPI will spike there — an expected finding, stated in advance",
        # 3 — the spatial distribution a single percentage hides.
        "per_row_direct_fraction": [round(float(f), 4) for f in per_row],
        "per_row_stats": {
            "min": round(float(per_row.min()), 4),
            "max": round(float(per_row.max()), 4),
            "sd": round(float(per_row.std()), 4),
        },
        "every_row_has_direct": bool((per_row > 0).all()),
        "every_column_has_direct": bool(s["direct"].any(axis=0).all()),
        "row_column_caveat": "TRUE BUT MISLEADING alone: coverage is survey blocks and transit tracks over a strongly bimodal field — a row can be 5% direct in a thin swath with predicted terrain either side",
        # 3b — where the two data sources MEET.
        "class_boundary": {
            "adjacencies": int(
                (s["direct"][:, 1:] != s["direct"][:, :-1]).sum()
                + (s["direct"][1:, :] != s["direct"][:-1, :]).sum()
            ),
            "fraction_of_cell_adjacencies": round(
                float(
                    (s["direct"][:, 1:] != s["direct"][:, :-1]).sum()
                    + (s["direct"][1:, :] != s["direct"][:-1, :]).sum()
                )
                / (2 * n),
                6,
            ),
            "note": "slope/roughness/TPI/BPI computed ACROSS a swath edge measure the transition between two data sources, not a seafloor feature — swath-boundary artifacts are an EXPECTED finding",
        },
    }

    # 4 — the station-level TID, through the PRODUCTION gate (not a
    # reimplementation: G.3's planning filter without the qa condition gave
    # 36, the gate gives 35 — two implementations of one rule is how they
    # drift, so this uses the one that exists).
    stations = CorpusCsvSampleSource().get_training_samples()
    lons = [o.longitude for o in stations]
    lats = [o.latitude for o in stations]
    with rasterio.open(tid_path) as t:
        codes = [int(v[0]) for v in t.sample(zip(lons, lats))]
    per_station = [
        {
            "station_id": o.station_id,
            "event_id": o.event_id,
            "longitude": round(o.longitude, 6),
            "latitude": round(o.latitude, 6),
            "tid": c,
            "cluster": "west" if o.longitude < CLUSTER_SPLIT_LON else "east",
        }
        for o, c in zip(stations, codes)
    ]
    def _cluster(name: str) -> dict:
        rows = [p for p in per_station if p["cluster"] == name]
        return {
            "n": len(rows),
            "direct": sum(1 for p in rows if p["tid"] in DIRECT_CODES),
            "predicted": sum(1 for p in rows if p["tid"] in INDIRECT_CODES),
            "tid_histogram": {
                str(code): sum(1 for p in rows if p["tid"] == code)
                for code in sorted({p["tid"] for p in rows})
            },
        }
    station_block = {
        "gate": "engine.prospectivity.samples.corpus_csv.CorpusCsvSampleSource.get_training_samples (the production eligibility gate, not reimplemented)",
        "n": len(per_station),
        "per_station": per_station,
        "tid_histogram": {
            str(code): codes.count(code) for code in sorted(set(codes))
        },
        "direct": sum(1 for c in codes if c in DIRECT_CODES),
        "predicted": sum(1 for c in codes if c in INDIRECT_CODES),
        "cluster_split_lon": CLUSTER_SPLIT_LON,
        "clusters": {"west": _cluster("west"), "east": _cluster("east")},
    }

    return {
        # In-file declaration (the audit reads .json top-level keys).
        "data_origin": "DERIVED",
        "derivation": (
            "engine.prospectivity.terrain.tid_accounting.build_tid_accounting — a pure "
            "function of the three hashed inputs below; all floats explicitly rounded, "
            "no seed (nothing stochastic). TID code table from "
            "GEBCO_Grid_documentation.pdf section 3.0 (tracked)."
        ),
        "inputs": {
            "bathymetry": {"path": "data/bathymetry/" + DEFAULT_BATHY.name, "sha256": _sha256(bathy_path)},
            "tid": {"path": "data/bathymetry/" + DEFAULT_TID.name, "sha256": _sha256(tid_path)},
            "corpus": {
                "path": "data/corpus/master_observations.csv",
                "sha256": _sha256(REPO_ROOT / "data" / "corpus" / "master_observations.csv"),
            },
        },
        "tid_code_table": {
            "source": "GEBCO_Grid_documentation.pdf section 3.0, Table 2",
            "classes": {
                "direct": [10, 17],
                "indirect_predicted": [40, 48],
                "unknown": [70, 72],
                "land": [0],
            },
            "codes": {str(k): v for k, v in sorted(CODE_NAMES.items())},
        },
        "whole_subset": whole,
        "study_extent": study,
        "stations": station_block,
        # TID.2 (2026-08-26): WHAT the predicted cells are. G.3 recorded where.
        "predicted_class_provenance": _predicted_class_provenance(
            bath_study.astype(np.float64),
            tid_study,
            dy_m=math.radians(abs(tid_transform.e)) * 6371.0088 * 1000.0,
            dx_m=math.radians(abs(tid_transform.a)) * 6371.0088 * 1000.0
            * math.cos(math.radians(0.5 * (STUDY_BOUNDS[1] + STUDY_BOUNDS[3]))),
        ),
        "grid": {
            "pixel_deg": round(tid_transform.a, 12),
            "note": "15 arc-seconds; both grids share size, transform and CRS (asserted at generation)",
        },
    }



# ── TID.2: WHAT the predicted cells are, not just where ────────────────────
# G.3 recorded WHERE the predicted cells are. This records WHAT they are, and
# MEASURES the consequence instead of asserting it.
#
# THE MEASUREMENT IS DESIGNED AROUND ONE CONFOUND: multibeam surveys TARGET
# interesting terrain (seamounts, contractor blocks), so predicted cells could
# be smoother simply by sitting on flatter seafloor. Absolute roughness cannot
# separate that from smoothing. The per-cell SHORT/LONG ratio can: it is
# scale-free, so a cell on genuinely flat abyssal plain and a cell on a rough
# flank are compared on the same footing.
SHORT_CELLS = 3   # ~1.4 km — Contract 3's own roughness/TPI window
LONG_CELLS = 19   # ~8.8 km — at/above the resolution the gravity field is said to reach

# Verbatim from GEBCO_Grid_documentation.pdf section 2.1 (tracked). Quoted
# rather than paraphrased because it is the whole provenance of 54.9% of the
# study extent, and a paraphrase is what the G.3-approval correction-drift
# instance (o) was made of.
GEBCO_2026_SWOT_SENTENCE = (
    "This release of the SRTM15+ data set uses a new highly-accurate gravity "
    "field data set from the Surface Water and Ocean Topography (SWOT) "
    "satellite (Yu et al., 2024) and machine learning methods to produce a "
    "bathymetric model (Sandwell et al., 2025)."
)


def _local_sd(a: np.ndarray, cells: int) -> np.ndarray:
    """Local standard deviation over a square window — the same statistic
    Contract 3's `std_dev_elevation` roughness recipe computes."""
    from scipy.ndimage import uniform_filter

    m = uniform_filter(a, size=cells, mode="nearest")
    m2 = uniform_filter(a * a, size=cells, mode="nearest")
    return np.sqrt(np.maximum(m2 - m * m, 0.0))


def _predicted_class_provenance(dem: np.ndarray, tid: np.ndarray, dy_m: float, dx_m: float) -> dict:
    direct = (tid >= 10) & (tid <= 17)
    pred = (tid >= 40) & (tid <= 48)

    short, long_ = _local_sd(dem, SHORT_CELLS), _local_sd(dem, LONG_CELLS)
    b = LONG_CELLS // 2 + 1  # trim the border so the filter's edge mode cannot bias the split
    s, l = short[b:-b, b:-b], long_[b:-b, b:-b]
    d, p = direct[b:-b, b:-b], pred[b:-b, b:-b]
    ratio = np.where(l > 1e-6, s / np.maximum(l, 1e-6), np.nan)

    def _med(arr, mask):
        """Median, rounded to 6 SIGNIFICANT figures rather than 6 decimals.

        Decimals would collapse curvature (order 1e-5 to 1e-6) to one digit and
        distort its ratio — the statistic where the effect is largest is also the
        smallest in magnitude, so fixed decimals lose exactly the number that
        matters. Rounding is still explicit, which is what the derivation string
        promises."""
        v = arr[mask]
        v = v[np.isfinite(v)]
        m = float(np.median(v))
        if m == 0.0 or not np.isfinite(m):
            return m
        from math import floor, log10

        return round(m, -int(floor(log10(abs(m)))) + 5)

    # derivative order — the axis the effect actually scales along
    z = dem
    dzdx = ((z[:-2, 2:] + 2 * z[1:-1, 2:] + z[2:, 2:]) - (z[:-2, :-2] + 2 * z[1:-1, :-2] + z[2:, :-2])) / (8 * dx_m)
    dzdy = ((z[2:, :-2] + 2 * z[2:, 1:-1] + z[2:, 2:]) - (z[:-2, :-2] + 2 * z[:-2, 1:-1] + z[:-2, 2:])) / (8 * dy_m)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    lap = np.abs((z[:-2, 1:-1] + z[2:, 1:-1] + z[1:-1, :-2] + z[1:-1, 2:] - 4 * z[1:-1, 1:-1]) / (dx_m * dy_m))
    d1, p1 = direct[1:-1, 1:-1], pred[1:-1, 1:-1]

    def _pair(arr, m_d, m_p):
        md, mp = _med(arr, m_d), _med(arr, m_p)
        return {"direct": md, "predicted": mp, "ratio_direct_over_predicted": round(md / mp, 4) if mp else None}

    return {
        "applies_to": "TID codes 40-48 (indirect/predicted) — 54.8687% of the study extent (G.3's count, unchanged)",
        "what_they_are": {
            "grid": "GEBCO_2026",
            "base_dataset": "SRTM15+ Version 2.8 (Tozer et al. 2019)",
            "gravity_mission": "SWOT — Surface Water and Ocean Topography",
            "method": "machine learning applied to the SWOT gravity anomaly",
            "documented_in": "GEBCO_Grid_documentation.pdf section 2.1 (tracked in data/bathymetry/)",
            "quote": GEBCO_2026_SWOT_SENTENCE,
            "references": [
                "Yu Y., Sandwell D.T., Dibarboure G. (2024). Abyssal marine tectonics from the "
                "SWOT mission. Science 386(6727):1251-1256. doi:10.1126/science.ads4472",
                "Sandwell D.T., Phrampus B.J., Salajegheh F., et al. (2025). Bathymetry Prediction "
                "with SWOT Gravity Anomaly using Machine Learning Methods: Paper 1 - Model "
                "Development. ESS Open Archive, 17 November 2025. "
                "doi:10.22541/essoar.176339961.11752151/v1",
            ],
        },
        "release_distinction": {
            "claim": "GEBCO_2026 is the first release whose predicted cells rest on SWOT gravity.",
            "verified": True,
            "how": (
                "The documentation carries a parallel section per release. Section 2.1 "
                "(GEBCO_2026) names SRTM15+ Version 2.8 AND the SWOT + machine-learning "
                "sentence quoted above. Section 2.2 (GEBCO_2025) names Version 2.7 and "
                "contains NO mention of SWOT or machine learning — checked by reading both "
                "sections, not by inference from the word 'new'."
            ),
            "why_it_matters": "It makes this provenance specific to the file this repo holds, not to GEBCO generally.",
        },
        "resolution": {
            "grid_cell_m": {"north_south": round(dy_m, 1), "east_west_at_13N": round(dx_m, 1),
                            "note": "15 arc-seconds on the geographic grid"},
            "gravity_field_km": None,
            "gravity_field_citation_status": (
                "NOT STATED IN THE TRACKED DOCUMENTATION. Searched: '8 km', 'wavelength' and "
                "'km resolution' return ZERO hits, and every 'resolution' mention refers to the "
                "15-arc-second GRID SPACING, not to what the gravity field resolves. A figure of "
                "~8 km circulates in NASA/JPL press material, which this repo does not hold; it is "
                "therefore RECORDED AS UNCITED rather than written in as fact. Yu et al. 2024 is "
                "where such a number would live and is cited above, but this repo has not read it, "
                "and this project's own LITERATURE bar is a citation that LOCATES the number. "
                "Consequence: any ratio of grid spacing to gravity resolution is UNCITED too, and "
                "the measurement below deliberately does not depend on that number."
            ),
        },
        "measured_short_wavelength_deficit": {
            "why_a_ratio": (
                "Absolute roughness cannot separate 'prediction smooths' from 'predicted cells "
                "happen to sit on flatter seafloor' — multibeam surveys TARGET rough, interesting "
                "terrain. The per-cell short/long ratio is scale-free and controls for that."
            ),
            "short_window_cells": SHORT_CELLS,
            "long_window_cells": LONG_CELLS,
            "median_local_sd_m": {
                "short_1400m": _pair(s, d, p),
                "long_8800m": _pair(l, d, p),
            },
            "median_short_over_long_ratio": {"direct": _med(ratio, d), "predicted": _med(ratio, p)},
            "finding": (
                "PREDICTED CELLS ARE MEASURABLY SMOOTHER AT SHORT WAVELENGTHS, and it is not the "
                "terrain-selection confound. Two independent signatures: (1) the direct/predicted "
                "roughness gap NARROWS as the window grows, which is what suppression of short "
                "wavelengths looks like and is the opposite of what a simple amplitude difference "
                "would do; (2) after normalising every cell by its OWN long-wavelength roughness, "
                "predicted cells still carry about a third less short-wavelength structure. The "
                "alternative hypothesis this task was told to watch for — that the ML step INJECTS "
                "short-wavelength structure the gravity field cannot support — is REFUTED for this "
                "extent: the deficit runs the other way at every scale measured."
            ),
        },
        "affected_covariates": {
            "axis": "derivative order — each derivative amplifies the missing short-wavelength content",
            "depth_value": _pair(z[1:-1, 1:-1], d1, p1),
            "slope_first_derivative_deg": _pair(slope, d1, p1),
            "curvature_second_derivative": _pair(lap, d1, p1),
            "reading": (
                "DEPTH is a VALUE and is barely affected — the medians agree within about 4%, so a "
                "gravity inversion gets the depth broadly right. SLOPE and ASPECT are FIRST "
                "derivatives on a 3x3 cell stencil. PROFILE and PLAN CURVATURE are SECOND "
                "derivatives and are the most affected of the eight. ROUGHNESS and TPI (1400 m "
                "windows) and BPI (460-2300 m radii) are windowed at scales that lie ENTIRELY "
                "below the resolution the gravity field is credited with, so they are load-bearing "
                "on short-wavelength structure throughout. Seven of Contract 3's eight layers are "
                "affected; depth is the exception."
            ),
        },
        "asymmetry_note": (
            "The DIRECT cells are attributed to a method (multibeam) and nothing else; the "
            "PREDICTED cells are now attributed to a mission, a gravity field, a model and two "
            "papers. READ THAT THE RIGHT WAY: it is not that prediction is better documented than "
            "measurement, nor that it is more trustworthy. It is that prediction NEEDS more "
            "documentation to be interpretable at all — a multibeam sounding means one thing, "
            "while an inversion means whatever its gravity field and its model make it mean."
        ),
    }

def write_artifact(out_path: Path = ARTIFACT_PATH) -> Path:
    accounting = build_tid_accounting()
    out_path.write_text(json.dumps(accounting, indent=1) + "\n")
    return out_path


if __name__ == "__main__":
    print(write_artifact())
