"""E1.4 deliverable plot: DEM + training corpus + the 8 Option-A covariates.

Usage (from the repo root; the DEM is passed in, this module never generates
one and never imports tests.*):

    python -m engine.prospectivity.features.plot_stack <dem.tif> <output_dir>

Produces `covariate_stack_synthetic_dem.png`: panel 1 is the DEM with the
corpus's training-eligible MASS stations overlaid (the Phase-2 readiness
check — the points must actually lie on the raster), panels 2-9 the eight
covariates, every panel titled with recipe + version and the resolved window
where one applies. Watermarked SYNTHETIC per CLAUDE.md's honesty rule.

matplotlib is a dev-only dependency (plot deliverables), not an engine
runtime dependency — imported here and nowhere else in engine/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # never require a display; deterministic file output
import matplotlib.pyplot as plt
import numpy as np

from engine.prospectivity.features.dem_grid import DemGrid
from engine.prospectivity.features.registry import build_default_registry
from engine.prospectivity.ingestion.corpus_builder import build_corpus

PLOT_FILENAME = "covariate_stack_synthetic_dem.png"


def _window_note(provenance: dict) -> str:
    """One line per resolved window: requested -> actually computed."""
    notes = []
    for label, window in provenance.get("resolved_windows", {}).items():
        clamp = ", CLAMPED" if window["clamped"] else ""
        notes.append(
            f"{label} {window['requested_m']:.0f} m -> {window['cells']} cells "
            f"(~{window['effective_m'] / 1000:.1f} km{clamp})"
        )
    return "\n".join(notes)


def plot_covariate_stack(dem_path: Path, output_dir: Path) -> Path:
    grid = DemGrid.load(Path(dem_path))
    results = build_default_registry().build_all(grid)

    training = [obs for obs in build_corpus() if obs.is_training_eligible()]
    lons = [obs.longitude for obs in training]
    lats = [obs.latitude for obs in training]
    abundances = [obs.abundance_kg_m2 for obs in training]

    height, width = grid.values.shape
    west, north = grid.transform.c, grid.transform.f
    east = west + width * grid.res_x_deg
    south = north - height * grid.res_y_deg
    extent = (west, east, south, north)

    fig, axes = plt.subplots(3, 3, figsize=(20, 10))
    fig.suptitle(
        "E1.4 Option-A covariate stack — SYNTHETIC DEM (seeded noise; illustrative only. "
        "Real GEBCO bathymetry arrives at Integration Checkpoint 1.)",
        fontsize=13,
        fontweight="bold",
    )

    dem_axis = axes[0][0]
    image = dem_axis.imshow(grid.values, extent=extent, cmap="viridis", aspect="auto")
    fig.colorbar(image, ax=dem_axis, fraction=0.030, label="elevation [m]")
    scatter = dem_axis.scatter(
        lons, lats, c=abundances, cmap="plasma", s=70, edgecolors="white", linewidths=1.0, zorder=3
    )
    fig.colorbar(scatter, ax=dem_axis, fraction=0.030, label="abundance [kg/m²]")
    # The stations sit in two tight geographic clusters ~991 km apart and
    # would read as two anonymous specks at this extent — annotate each
    # cluster (split at the largest longitude gap; cruise labels are NOT a
    # geographic split, both cruise legs visited both areas) with its count.
    ordered = sorted(zip(lons, lats))
    gaps = [ordered[k + 1][0] - ordered[k][0] for k in range(len(ordered) - 1)]
    split_lon = ordered[gaps.index(max(gaps))][0] if gaps else None
    clusters = [
        [(lon, lat) for lon, lat in ordered if lon <= split_lon],
        [(lon, lat) for lon, lat in ordered if lon > split_lon],
    ] if split_lon is not None else [ordered]
    for points in clusters:
        if not points:
            continue
        mean_lon = sum(p[0] for p in points) / len(points)
        mean_lat = sum(p[1] for p in points) / len(points)
        label_lon = min(max(mean_lon + 1.2, west + 1.0), east - 1.0)
        label_lat = min(max(mean_lat - 1.0, south + 0.4), north - 0.4)
        dem_axis.annotate(
            f"{len(points)} stations",
            xy=(mean_lon, mean_lat),
            xytext=(label_lon, label_lat),
            ha="center",
            fontsize=8,
            fontweight="bold",
            color="white",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": "black", "alpha": 0.6},
            arrowprops={"arrowstyle": "->", "color": "white", "linewidth": 1.0},
        )
    dem_axis.set_title(f"synthetic DEM + {len(training)} training-eligible MASS stations")

    for axis, result in zip(axes.flat[1:], results):
        provenance = result.provenance
        image = axis.imshow(
            result.values,
            extent=extent,
            cmap="twilight" if result.name == "aspect" else "viridis",
            aspect="auto",
        )
        fig.colorbar(image, ax=axis, fraction=0.030)
        title = f"{result.name} ({provenance['recipe']} v{provenance['recipe_version']})"
        note = _window_note(provenance)
        axis.set_title(title + ("\n" + note if note else ""), fontsize=9)

    for axis in axes.flat:
        axis.set_xlabel("lon [°]", fontsize=8)
        axis.set_ylabel("lat [°]", fontsize=8)
        axis.tick_params(labelsize=7)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / PLOT_FILENAME
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dem_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    arguments = parser.parse_args(argv)
    written = plot_covariate_stack(arguments.dem_path, arguments.output_dir)
    print(f"wrote {written}")


if __name__ == "__main__":
    main()
