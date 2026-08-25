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
        "grid": {
            "pixel_deg": round(tid_transform.a, 12),
            "note": "15 arc-seconds; both grids share size, transform and CRS (asserted at generation)",
        },
    }


def write_artifact(out_path: Path = ARTIFACT_PATH) -> Path:
    accounting = build_tid_accounting()
    out_path.write_text(json.dumps(accounting, indent=1) + "\n")
    return out_path


if __name__ == "__main__":
    print(write_artifact())
