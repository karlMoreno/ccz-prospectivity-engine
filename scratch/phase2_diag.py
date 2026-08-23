"""THROWAWAY diagnostic — Q3 (lag identifiability), Q4 (OK variance vs sample
density), Q5 (station geometry). Read-only: touches no repo state, writes only
into scratch/. Not committed.

Uses the project's OWN variogram model and kriging system so the numbers match
what E2.2/E2.4 produced, rather than a re-implementation that could disagree.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path("/Users/karlmoreno/CCZ/ccz-prospectivity-engine")
sys.path.insert(0, str(REPO))
OUT = REPO / "scratch"

from engine.prospectivity.estimators.kriging import OrdinaryKrigingEstimator  # noqa: E402
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource  # noqa: E402

EARTH_R = 6371.0088


def haversine_km(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """(n,2) lon/lat degrees -> (n,m) great-circle km."""
    lon1, lat1 = np.radians(a[:, 0])[:, None], np.radians(a[:, 1])[:, None]
    lon2, lat2 = np.radians(b[:, 0])[None, :], np.radians(b[:, 1])[None, :]
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_R * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def single_linkage(d: np.ndarray, threshold: float) -> list[list[int]]:
    n = d.shape[0]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if d[i, j] <= threshold:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: -len(g))


# ────────────────────────────────────────────────── data: the 35 real stations
obs = [o for o in CorpusCsvSampleSource().get_training_samples()]
coords = np.array([[float(o.longitude), float(o.latitude)] for o in obs])
y = np.array([float(o.abundance_kg_m2) for o in obs])
n = len(obs)
D = haversine_km(coords, coords)
iu = np.triu_indices(n, k=1)
pair_d = D[iu]

report: dict = {"n_stations": n, "n_pairs": int(pair_d.size)}

# ───────────────────────────────────────── Q5: clusters, NN distances, density
clusters = single_linkage(D, 100.0)     # the LOCO linkage
sites = single_linkage(D, 2.0)          # the leave-one-site-out linkage
report["n_clusters_at_100km"] = len(clusters)
report["n_sites_at_2km"] = len(sites)

def bbox_area_km2(idx: list[int]) -> float:
    c = coords[idx]
    if len(idx) < 2:
        return 0.0
    lat0 = np.radians(c[:, 1].mean())
    w = (c[:, 0].max() - c[:, 0].min()) * 111.32 * np.cos(lat0)
    h = (c[:, 1].max() - c[:, 1].min()) * 110.57
    return float(w * h)

cluster_rows = []
for k, g in enumerate(clusters):
    sub = D[np.ix_(g, g)].copy()
    np.fill_diagonal(sub, np.inf)
    nn = sub.min(axis=1)
    area = bbox_area_km2(g)
    cluster_rows.append({
        "cluster": k, "n": len(g),
        "nn_min_km": float(nn.min()), "nn_median_km": float(np.median(nn)),
        "nn_max_km": float(nn.max()),
        "bbox_area_km2": area,
        "stations_per_1000km2": (len(g) / area * 1000.0) if area > 0 else None,
        "max_within_km": float(sub[np.isfinite(sub)].max()),
    })
report["clusters"] = cluster_rows
report["site_sizes_at_2km"] = [len(g) for g in sites]

# ───────────────────────────────────── Q3: the lag distribution and its gap
labels = np.empty(n, dtype=int)
for k, g in enumerate(clusters):
    labels[list(g)] = k
same = labels[iu[0]] == labels[iu[1]]
within, between = pair_d[same], pair_d[~same]
report["within_cluster_pairs"] = int(within.size)
report["between_cluster_pairs"] = int(between.size)
report["max_within_cluster_lag_km"] = float(within.max())
report["min_between_cluster_lag_km"] = float(between.min())
report["max_between_cluster_lag_km"] = float(between.max())
report["empty_gap_km"] = [float(within.max()), float(between.min())]
report["gap_width_km"] = float(between.min() - within.max())
report["pairs_in_gap"] = int(((pair_d > within.max()) & (pair_d < between.min())).sum())

# the E2.2 bin edges actually used, read off the estimator
est = OrdinaryKrigingEstimator()
edges = np.asarray(est._bin_edges_km, dtype=float)
report["bin_edges_km"] = [float(e) for e in edges]
report["min_pairs"] = int(est._min_pairs)
report["max_fit_lag_km"] = float(est._max_fit_lag_km)
bins = []
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (pair_d >= lo) & (pair_d < hi)
    cnt = int(m.sum())
    bins.append({"lo_km": float(lo), "hi_km": float(hi), "pairs": cnt,
                 "mean_lag_km": float(pair_d[m].mean()) if cnt else None,
                 "semivariance": float(np.mean(0.5 * (y[iu[0]][m] - y[iu[1]][m]) ** 2)) if cnt else None,
                 "used_in_fit": bool(cnt >= est._min_pairs and hi <= est._max_fit_lag_km)})
report["lag_bins"] = bins

# ─────────────────────────── the FULL 35-station variogram (Q2's headline fit)
est.fit(coords, y)
rep = est.report()
from engine.prospectivity.estimators.variogram import VariogramModel
model = VariogramModel(family=rep.used_model_family, nugget=rep.nugget,
                       partial_sill=rep.partial_sill, range_km=rep.range_km)
report["full_fit"] = {
    "family": rep.used_model_family, "nugget": rep.nugget,
    "partial_sill": rep.partial_sill, "sill": rep.sill,
    "range_km": rep.range_km,
    "nugget_ratio": rep.nugget / rep.sill if rep.sill else None,
    "range_at_candidate_ceiling": rep.range_at_candidate_ceiling,
    "range_below_first_supported_lag": rep.range_below_first_supported_lag,
    "residual_dof": rep.residual_dof,
    "weighted_sse": rep.used_weighted_sse,
    "n_fitted_bins": len(rep.fitted_bins),
    "fitted_bins": [list(b) for b in rep.fitted_bins],
    "excluded_bins": [list(map(str, b)) for b in rep.excluded_bins],
    "unsupported_km": [list(u) for u in rep.unsupported_km],
    "alternative_family": rep.alternative.model.family,
    "alternative_range_km": rep.alternative.model.range_km,
    "alternative_sse": rep.alternative.weighted_sse,
}

# ───────────────────────── Q4: mean OK variance vs added sample density
def ok_variance(sample_xy: np.ndarray, target_xy: np.ndarray) -> np.ndarray:
    """Ordinary-kriging variance at each target. Value-independent."""
    ns = sample_xy.shape[0]
    G = model.gamma(haversine_km(sample_xy, sample_xy))
    A = np.ones((ns + 1, ns + 1))
    A[:ns, :ns] = G
    A[ns, ns] = 0.0
    g0 = model.gamma(haversine_km(sample_xy, target_xy))   # (ns, nt)
    b = np.ones((ns + 1, g0.shape[1]))
    b[:ns, :] = g0
    sol = np.linalg.solve(A, b)
    lam, mu = sol[:ns, :], sol[ns, :]
    return (lam * g0).sum(axis=0) + mu

# study area = the bbox of the EASTERN cluster (the denser one), as the
# evaluation window; a full-CCZ window would be dominated by extrapolation
# far from any datum and would say nothing about added density.
big = max(clusters, key=len)
c = coords[big]
lon0, lon1_ = c[:, 0].min(), c[:, 0].max()
lat0, lat1_ = c[:, 1].min(), c[:, 1].max()
pad = 0.02
gx, gy = np.meshgrid(np.linspace(lon0 - pad, lon1_ + pad, 45),
                     np.linspace(lat0 - pad, lat1_ + pad, 45))
targets = np.column_stack([gx.ravel(), gy.ravel()])
area = bbox_area_km2(big)
current_density = len(big) / area * 1000.0

rows = []
base_mean = float(np.mean(ok_variance(c, targets)))
for mult in (1, 1.5, 2, 3, 4, 5, 6, 8, 10):
    if mult == 1:
        pts = c
    else:
        extra = int(round(len(big) * (mult - 1)))
        side = int(np.ceil(np.sqrt(extra)))
        ax = np.linspace(lon0, lon1_, side)
        ay = np.linspace(lat0, lat1_, side)
        add = np.column_stack([v.ravel() for v in np.meshgrid(ax, ay)])
        # DROP near-coincident additions: a grid node landing on top of an
        # existing station makes the OK system near-singular and the solve
        # returns noise — which is what produced a NEGATIVE marginal rate in
        # the first run of this sweep. 50 m threshold.
        # Keep the WHOLE side x side grid — truncating it row-major (`[:extra]`)
        # covered only part of the box at some multiples, which is what made
        # the marginal rate NON-MONOTONE (negative at x5) in earlier runs.
        keep = haversine_km(add, c).min(axis=1) > 0.05
        add = add[keep]
        pts = np.vstack([c, add])
    v = float(np.mean(ok_variance(pts, targets)))
    rows.append({"multiple_of_current": mult, "n_samples": int(pts.shape[0]),
                 "samples_per_1000km2": pts.shape[0] / area * 1000.0,
                 "mean_ok_variance": v, "mean_ok_sd": float(np.sqrt(v)),
                 "pct_reduction_vs_current": 100.0 * (base_mean - v) / base_mean})
report["q4_density_sweep"] = rows
report["q4_window"] = {"cluster_n": len(big), "bbox_area_km2": area,
                       "current_density_per_1000km2": current_density,
                       "grid_targets": int(targets.shape[0])}

# knee: marginal reduction per added sample < 5% of the initial marginal rate
marg = []
for a, b_ in zip(rows[:-1], rows[1:]):
    dn = b_["n_samples"] - a["n_samples"]
    marg.append((b_["multiple_of_current"], (a["mean_ok_variance"] - b_["mean_ok_variance"]) / dn if dn else 0.0))
if marg:
    r0 = marg[0][1]
    knee = next((m for m, r in marg if r0 > 0 and r < 0.05 * r0), None)
    report["q4_initial_marginal_rate"] = r0
    report["q4_knee_multiple"] = knee
    report["q4_marginal_rates"] = marg
report["q4_asymptote_floor"] = rows[-1]["mean_ok_variance"]
report["q4_nugget_floor"] = model.nugget

(OUT / "phase2_diag.json").write_text(json.dumps(report, indent=1, default=float))

# ── plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].hist(pair_d, bins=60)
    ax[0].set_yscale("log")
    ax[0].set_xlabel("pairwise lag (km)"); ax[0].set_ylabel("pairs (log)")
    ax[0].set_title(f"Q3: lag distribution — gap {within.max():.1f}–{between.min():.1f} km EMPTY")
    d = [r["samples_per_1000km2"] for r in rows]
    ax[1].plot(d, [r["mean_ok_variance"] for r in rows], "o-")
    ax[1].axhline(model.nugget, ls="--", label=f"nugget {model.nugget:.2f}")
    ax[1].set_xlabel("samples / 1000 km²"); ax[1].set_ylabel("mean σ²_OK")
    ax[1].set_title("Q4: OK variance vs density"); ax[1].legend()
    fig.tight_layout(); fig.savefig(OUT / "phase2_diag.png", dpi=110)
    print("plot -> scratch/phase2_diag.png")
except Exception as e:  # pragma: no cover
    print("plot skipped:", e)

print(json.dumps({k: report[k] for k in (
    "n_stations", "n_pairs", "max_within_cluster_lag_km", "min_between_cluster_lag_km",
    "pairs_in_gap", "full_fit", "q4_knee_multiple", "q4_asymptote_floor")}, indent=1, default=float))
