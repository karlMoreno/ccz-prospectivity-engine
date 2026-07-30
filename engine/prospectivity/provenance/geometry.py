"""Corpus geometry summary — RECORD, DON'T JUDGE.

Every number here is descriptive. Nothing in this module decides whether the
sampling is adequate, and nothing warns: the point is that the facts that
determine what modelling is defensible are in the build record, so the
decision is made with them in view instead of rediscovered by audit.

The three that matter today, and why:

- **Rows outside the AOI.** Currently ALL of them. `study_area.geojson` is a
  Phase-0 placeholder that no real corpus row falls inside; the only rows that
  ever did were the fabricated chamber rows removed in P1. A 100% miss between
  the contract's AOI and the actual corpus belongs on every build, not in a
  chat log.
- **Cluster structure** at a stated linkage distance, with within-cluster
  extent — the corpus is two tight clusters, not a spread.
- **Pairwise-distance distribution**, including the largest gap between
  consecutive sorted distances. Every pair is either <13 km or ~991 km apart
  with nothing between, which is what determines whether a variogram can be
  empirically estimated across the range it must predict over.

Single-linkage clustering and haversine are implemented here rather than
pulled in: scipy is not an approved dependency, and both are a handful of
lines on 36 points.
"""

from __future__ import annotations

import math
from pathlib import Path

from engine.prospectivity.domain.observation import Observation

EARTH_RADIUS_KM = 6371.0088  # IUGG mean radius

# Linkage distance for the cluster count. Stated in the manifest alongside the
# result, because "how many clusters" is meaningless without it: at 100 km the
# corpus is 2 clusters; at 1500 km it would be 1.
DEFAULT_LINKAGE_KM = 100.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def unique_locations(observations: list[Observation]) -> list[tuple[float, float]]:
    """Distinct (lat, lon) station locations, sorted for determinism.

    Deduplicated on purpose: one box-core event contributes up to three rows
    (MASS/COUNT/COVER) at identical coordinates, and counting each would
    triple the zero-distance pairs and misstate the spatial structure.
    """
    return sorted({(obs.latitude, obs.longitude) for obs in observations})


def bounding_box(observations: list[Observation]) -> dict[str, float] | None:
    if not observations:
        return None
    lats = [obs.latitude for obs in observations]
    lons = [obs.longitude for obs in observations]
    return {
        "min_latitude": min(lats),
        "max_latitude": max(lats),
        "min_longitude": min(lons),
        "max_longitude": max(lons),
    }


def _pairwise_distances_km(locations: list[tuple[float, float]]) -> list[float]:
    return sorted(
        haversine_km(locations[i][0], locations[i][1], locations[j][0], locations[j][1])
        for i in range(len(locations))
        for j in range(i + 1, len(locations))
    )


def _single_linkage_clusters(
    locations: list[tuple[float, float]], linkage_km: float
) -> list[list[tuple[float, float]]]:
    """Union-find single-linkage: two locations join the same cluster if they
    are within `linkage_km`, transitively."""
    parent = list(range(len(locations)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            if haversine_km(*locations[i], *locations[j]) <= linkage_km:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[max(root_i, root_j)] = min(root_i, root_j)

    grouped: dict[int, list[tuple[float, float]]] = {}
    for index, location in enumerate(locations):
        grouped.setdefault(find(index), []).append(location)
    # Sorted by first member so cluster order never depends on dict iteration.
    return [members for _, members in sorted(grouped.items(), key=lambda kv: kv[1][0])]


def _rounded(value: float | None, digits: int = 4) -> float | None:
    """Round for stable JSON: float repr differences across platforms would
    otherwise show up as manifest diffs that mean nothing."""
    return None if value is None else round(value, digits)


def spatial_summary(
    observations: list[Observation],
    linkage_km: float = DEFAULT_LINKAGE_KM,
    basis: str = "unspecified",
) -> dict:
    """Cluster structure + pairwise-distance distribution. Descriptive only.

    `basis` names the row set this was computed over and is echoed into the
    result. Required in practice, because the manifest records two of these
    side by side and a pair count is meaningless without knowing which
    stations it counted: the variogram question is about the stations that can
    actually TRAIN, so the training-eligible block is the decision-relevant
    one (C(35,2) = 595 pairs), while the all-rows block (C(36,2) = 630) also
    counts the flagged failed box core that will never train.
    """
    locations = unique_locations(observations)
    summary: dict = {
        "basis": basis,
        "distinct_locations": len(locations),
        "linkage_distance_km": linkage_km,
    }
    if len(locations) < 2:
        summary["clusters"] = len(locations)
        summary["pairwise_distance_km"] = None
        summary["cluster_extents"] = []
        return summary

    clusters = _single_linkage_clusters(locations, linkage_km)
    summary["clusters"] = len(clusters)
    summary["cluster_extents"] = [
        {
            "locations": len(members),
            # Max within-cluster separation: the cluster's own extent.
            "max_internal_distance_km": _rounded(
                max(_pairwise_distances_km(members)) if len(members) > 1 else 0.0
            ),
            "centroid_latitude": _rounded(sum(m[0] for m in members) / len(members)),
            "centroid_longitude": _rounded(sum(m[1] for m in members) / len(members)),
        }
        for members in clusters
    ]

    distances = _pairwise_distances_km(locations)
    gaps = [distances[i + 1] - distances[i] for i in range(len(distances) - 1)]
    largest_gap_index = max(range(len(gaps)), key=gaps.__getitem__) if gaps else None
    summary["pairwise_distance_km"] = {
        "pairs": len(distances),
        "min": _rounded(distances[0]),
        "median": _rounded(distances[len(distances) // 2]),
        "max": _rounded(distances[-1]),
        # The support gap: the widest stretch of distance over which the corpus
        # contains NO pair at all. A variogram cannot be empirically estimated
        # across it (see this module's docstring).
        "largest_gap_km": _rounded(max(gaps)) if gaps else None,
        "largest_gap_between_km": (
            [
                _rounded(distances[largest_gap_index]),
                _rounded(distances[largest_gap_index + 1]),
            ]
            if largest_gap_index is not None
            else None
        ),
    }
    return summary


def count_outside_study_area(observations: list[Observation], study_area_path: Path) -> dict:
    """How many rows fall outside Contract 2's AOI polygon. Reported as a
    count and a fraction; never enforced — the AOI itself is an open decision
    (docs/BACKLOG.md §1), so this module states the mismatch and stops."""
    import json

    from shapely.geometry import Point, shape

    geojson = json.loads(Path(study_area_path).read_text())
    polygon = shape(geojson["features"][0]["geometry"])
    outside = sum(
        1 for obs in observations if not polygon.covers(Point(obs.longitude, obs.latitude))
    )
    return {
        "study_area_path": str(study_area_path.name),
        "rows_total": len(observations),
        "rows_outside_study_area": outside,
        "fraction_outside": _rounded(outside / len(observations)) if observations else None,
        "note": (
            "Descriptive only. The AOI is a Phase-0 placeholder and defining "
            "the real one is an open decision (docs/BACKLOG.md section 1); "
            "nothing filters rows on it."
        ),
    }
