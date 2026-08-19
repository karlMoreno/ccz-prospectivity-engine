"""FoldSplitter — STRATEGY (E2.4 §1; the PATTERNS.md §4.2 seam, realized).

One interface, three implementations by the end of E2.4 — leave-one-cluster-
out and within-cluster blocking (spatial, may back a claim) and random k-fold
(the demonstrably-wrong comparison, may NOT) — behind a runner that never
knows which one it holds. Adding a fold design is adding a class.

    ┌───────────────────────────────────────────────────────────┐
    │                    FoldSplitter (ABC)                       │
    │  spatially_blocked : ClassVar[bool]   <- DECLARED, enforced │
    │  name              : str                                    │
    │  split(coords_lonlat) -> FoldAssignment                     │
    │      folds · labels · rule · parameters ·                   │
    │      stability_interval_km (the tie-break plateau)          │
    └───────────────────────────────────────────────────────────┘
        ▲                          ▲                    ▲
  ┌──────────────────────┐  ┌────────────────┐  ┌────────────────────┐
  │SingleLinkageBlock-   │  │(within-cluster  │  │(RandomKFold —       │
  │Splitter — 100 km =   │  │ scheme: Karl's  │  │ Section 2; declares │
  │LOCO; §1A             │  │ §1B pick, §2)   │  │ spatially_blocked   │
  └──────────────────────┘  └────────────────┘  │ = False)            │
                                                 └────────────────────┘

THE DECLARATION (`spatially_blocked`), enforced at class-definition time
by `__init_subclass__` — the E2.1 predict-is-final precedent: a splitter
that does not SAY whether its folds are spatially blocked cannot be
declared, so the E2.5 guard ("random k-fold does not satisfy spatial CV")
reads a declaration, never infers from a name. Name-sniffing is the
inference-over-declaration defect this project has removed three times
(P2.0d-2 path inference, P2.0d-3 title sniffing, E2.4 §2C input routing).

FOLD ASSIGNMENT IS RECORDED, NOT RE-DERIVED: `split()` returns a
`FoldAssignment` — the per-row labels, the rule in words, its parameters,
and the STABILITY INTERVAL of thresholds over which the partition is
unchanged — so the run manifest carries the assignment as data a reader
can check, and the tie-break-insensitivity claim is a recorded fact per
run, not a sentence in a walkthrough.

SINGLE-LINKAGE, and why it cannot be sensitive to tie-breaking here (§1A):
the blocks are the connected components of the graph whose edges are the
station pairs within `linkage_km` (great-circle). Connected components do
not depend on the order edges are visited, and the partition changes ONLY
when the threshold crosses a minimum-spanning-tree edge length; between
two consecutive MST edges it is identical. On the real corpus the last
two MST edges are 10.018 km and 986.036 km, so leave-one-cluster-out is
the same two folds for ANY linkage in [10.018, 986.036) — the corpus
manifest's 100 km (geometry.DEFAULT_LINKAGE_KM) sits in the middle of a
976 km plateau. `stability_interval_km` records that interval per split.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

from engine.prospectivity.provenance.geometry import (
    DEFAULT_LINKAGE_KM,
    haversine_km,
    minimum_spanning_tree_edge_lengths_km,
    single_linkage_labels,
)


@dataclass(frozen=True)
class Fold:
    """One train/test split over matrix ROW INDICES (the TrainingMatrix's
    sorted-station order), with the MEASURED minimum great-circle distance
    between any training and any test station — the number the spatial-
    leakage assertion checks and the manifest records."""

    name: str
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]
    min_train_test_km: float

    def __post_init__(self) -> None:
        train, test = set(self.train_indices), set(self.test_indices)
        if not train or not test:
            raise ValueError(
                f"fold {self.name!r} has an empty {'train' if not train else 'test'} set"
            )
        if train & test:
            raise ValueError(
                f"fold {self.name!r} is not disjoint: rows {sorted(train & test)} are in "
                "both train and test — a station predicting itself is the leakage "
                "spatial CV exists to refuse"
            )
        if len(train) != len(self.train_indices) or len(test) != len(self.test_indices):
            raise ValueError(f"fold {self.name!r} repeats a row index")
        d = self.min_train_test_km
        if not (isinstance(d, (int, float)) and np.isfinite(d) and d >= 0.0):
            raise ValueError(
                f"fold {self.name!r} records min_train_test_km={d!r} — must be a finite, "
                "non-negative distance (a NaN would serialize as a non-standard token)"
            )


@dataclass(frozen=True)
class FoldAssignment:
    """What a splitter decided, as data. `labels[i]` is row i's block; the
    folds are derived from it. `stability_interval_km` is the half-open
    [lo, hi) of thresholds that reproduce this exact partition (None for
    designs with no threshold, e.g. leave-one-station-out)."""

    splitter_name: str
    spatially_blocked: bool
    rule: str
    parameters: dict[str, Any]
    n_rows: int
    labels: tuple[int, ...]
    folds: tuple[Fold, ...]
    stability_interval_km: tuple[float, float | None] | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)
    # SHA-256 over the (n, 2) float64 lon/lat bytes the split was computed
    # from, so the leakage assertion (and the run manifest) can prove the
    # assignment belongs to THESE coordinates in THIS row order — a matrix
    # rebuilt in a different sort has the same length and would otherwise
    # be measured against the wrong stations silently (§1 review).
    coords_sha256: str | None = None

    def __post_init__(self) -> None:
        """Invariants every planned design shares (LOCO, LOSO, site-out,
        random k-fold), refused by name: the declaration is a bool; at least
        two rows and one fold; every index is a valid row; EVERY ROW IS HELD
        OUT EXACTLY ONCE across the folds (a design that never tests some
        rows, or tests one twice, would report a score over a different
        population than it claims); and every fold's test set is exactly the
        rows carrying one label — the labels and the folds are one record,
        not two that may disagree."""
        if not isinstance(self.spatially_blocked, bool):
            raise ValueError(
                f"{self.splitter_name}: spatially_blocked must be a bool declaration, got "
                f"{self.spatially_blocked!r}"
            )
        if self.n_rows < 2 or not self.folds:
            raise ValueError(
                f"{self.splitter_name}: an assignment needs >= 2 rows and >= 1 fold "
                f"(got n_rows={self.n_rows}, folds={len(self.folds)})"
            )
        if len(self.labels) != self.n_rows:
            raise ValueError(
                f"{self.splitter_name}: {len(self.labels)} labels for {self.n_rows} rows"
            )
        seen: dict[int, str] = {}
        for fold in self.folds:
            for idx in fold.train_indices + fold.test_indices:
                if not (0 <= idx < self.n_rows):
                    raise ValueError(
                        f"{self.splitter_name}: fold {fold.name!r} references row {idx}, "
                        f"outside 0..{self.n_rows - 1}"
                    )
            for idx in fold.test_indices:
                if idx in seen:
                    raise ValueError(
                        f"{self.splitter_name}: row {idx} is held out by both "
                        f"{seen[idx]!r} and {fold.name!r} — every row must be tested "
                        "exactly once"
                    )
                seen[idx] = fold.name
        missing = sorted(set(range(self.n_rows)) - set(seen))
        if missing:
            raise ValueError(
                f"{self.splitter_name}: rows {missing} are never held out — every row "
                "must be tested exactly once"
            )
        for fold in self.folds:
            fold_labels = {self.labels[i] for i in fold.test_indices}
            if len(fold_labels) != 1:
                raise ValueError(
                    f"{self.splitter_name}: fold {fold.name!r} holds out rows carrying "
                    f"{len(fold_labels)} different labels {sorted(fold_labels)} — a fold's "
                    "test set must be exactly the rows of ONE label"
                )
            (label,) = fold_labels
            expected = tuple(i for i in range(self.n_rows) if self.labels[i] == label)
            if tuple(sorted(fold.test_indices)) != expected:
                raise ValueError(
                    f"{self.splitter_name}: fold {fold.name!r} tests rows "
                    f"{sorted(fold.test_indices)} but label {label} marks rows "
                    f"{list(expected)} — labels and folds disagree"
                )

    def to_record(self) -> dict:
        """JSON-able form for the run manifest (E2.4 §2D)."""
        return {
            "splitter_name": self.splitter_name,
            "spatially_blocked": self.spatially_blocked,
            "rule": self.rule,
            "parameters": dict(self.parameters),
            "n_rows": self.n_rows,
            "labels": list(self.labels),
            "stability_interval_km": (
                list(self.stability_interval_km) if self.stability_interval_km else None
            ),
            "folds": [
                {
                    "name": f.name,
                    "train_indices": list(f.train_indices),
                    "test_indices": list(f.test_indices),
                    "n_train": len(f.train_indices),
                    "n_test": len(f.test_indices),
                    "min_train_test_km": f.min_train_test_km,
                }
                for f in self.folds
            ],
            "notes": list(self.notes),
            "coords_sha256": self.coords_sha256,
        }


class FoldSplitter(ABC):
    """Strategy interface. Subclasses MUST declare `spatially_blocked`; every
    instance also states `required_separation_km` (the minimum train–test
    great-circle separation the design GUARANTEES, which the runner asserts
    and records — 0.0 means "disjointness only", stated as such) and a
    `purpose` (what the design measures, for the manifest; Karl's E2.4 §1B
    decision made the labels binding)."""

    spatially_blocked: ClassVar[bool]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # MRO lookup, not cls.__dict__: a subclass of a DECLARED splitter
        # inherits the declaration (a grandchild is spatially blocked unless
        # it says otherwise); the ABC itself carries no value, so a hierarchy
        # that never declares is refused at its FIRST subclass, abstract or
        # not — an intermediate base must declare (or inherit) too. Class-
        # creation-time only: E2.5's guard reads the CLASS attribute and the
        # recorded FoldAssignment.spatially_blocked (validated as a bool
        # there), never an instance attribute.
        declared = getattr(cls, "spatially_blocked", None)
        if not isinstance(declared, bool):
            raise TypeError(
                f"{cls.__name__} does not declare `spatially_blocked: ClassVar[bool]` — "
                "a splitter must SAY whether its folds are spatially blocked (may back a "
                "claim) or not (random k-fold: the demonstrably-wrong comparison); the "
                "E2.5 guard reads this declaration and never infers it from a name"
            )

    @property
    @abstractmethod
    def name(self) -> str:
        """The design's name as recorded in provenance."""

    @property
    @abstractmethod
    def purpose(self) -> str:
        """What this design measures — recorded beside its results."""

    @property
    @abstractmethod
    def required_separation_km(self) -> float:
        """The minimum train–test separation the design guarantees (km).
        The runner asserts it on every fold and records it; 0.0 = the
        design is deliberately unbuffered and only disjointness is asserted."""

    @abstractmethod
    def split(self, coords_lonlat: Any) -> FoldAssignment:
        """Deterministic fold assignment from coordinates alone."""


def assert_claim_eligible(assignment: FoldAssignment) -> None:
    """THE GUARD (E2.4 spec: random k-fold "cannot be selected as the
    validation method for a published claim"): a design may back a claim
    only if its recorded declaration says its folds are spatially blocked.
    Reads the RECORD (validated as a bool at construction, written from the
    class declaration), never a name. E2.5's refuse-to-validate re-asserts
    this at claim time; the runner uses it to compute which designs are
    claim-eligible and records the list."""
    if assignment.spatially_blocked is not True:
        raise ValueError(
            f"design {assignment.splitter_name!r} is not spatially blocked "
            "(spatially_blocked=False) — its scores may be REPORTED (as the "
            "demonstrably-wrong comparison or the within-site leakage demonstration) "
            "but can never back a published claim; CLAUDE.md: never report a plain "
            "random-split score as validation"
        )


def _as_latlon_points(coords_lonlat: Any) -> list[tuple[float, float]]:
    coords = np.asarray(coords_lonlat, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError(f"coords must be (n, 2) lon/lat, got {coords.shape}")
    if not np.isfinite(coords).all():
        raise ValueError("coords contain NaN/inf — refusing to assign folds over them")
    # Column order is (lon, lat) — the TrainingMatrix convention. A swapped
    # array on the real corpus (lat ≈ 12–14, lon ≈ −117…−126) would still be
    # (n, 2) and finite and would split into two plausible folds with wrong
    # recorded distances (§1 review) — so the ranges are checked BY NAME:
    if (np.abs(coords[:, 1]) > 90.0).any() or (np.abs(coords[:, 0]) > 180.0).any():
        raise ValueError(
            "coords must be (longitude, latitude) with |lat| <= 90 and |lon| <= 180 — "
            f"got lat range [{coords[:, 1].min():.3f}, {coords[:, 1].max():.3f}], lon range "
            f"[{coords[:, 0].min():.3f}, {coords[:, 0].max():.3f}]; a (lat, lon) array "
            "handed in the wrong column order is the likely cause"
        )
    # geometry.py takes (lat, lon). The swap happens exactly here, once — the
    # pairwise_distances_km rule.
    return [(float(lat), float(lon)) for lon, lat in coords]


def coords_fingerprint(coords_lonlat: Any) -> str:
    """SHA-256 over the (n, 2) float64 lon/lat bytes in row order."""
    coords = np.ascontiguousarray(np.asarray(coords_lonlat, dtype=np.float64))
    return "sha256:" + hashlib.sha256(coords.tobytes()).hexdigest()


def min_train_test_distance_km(
    points: list[tuple[float, float]], train: tuple[int, ...], test: tuple[int, ...]
) -> float:
    return min(haversine_km(*points[i], *points[j]) for i in train for j in test)


class SingleLinkageBlockSplitter(FoldSplitter):
    """Blocks = single-linkage components at `linkage_km`; one fold per block
    (hold the block out, train on everything else). At the corpus manifest's
    100 km this IS leave-one-cluster-out (§1A: two folds, 21 E / 14 W). The
    same class at a within-cluster linkage is one of the §1B candidates.

    `design_name` is a DECLARATION by the caller of what this instance is
    for ("leave_one_cluster_out"); it is not derived from the linkage."""

    spatially_blocked: ClassVar[bool] = True

    def __init__(
        self,
        *,
        linkage_km: float,
        design_name: str,
        min_blocks: int = 2,
        purpose: str = "",
    ) -> None:
        if not (linkage_km > 0 and np.isfinite(linkage_km)):
            raise ValueError(f"linkage_km must be a positive finite number, got {linkage_km!r}")
        if min_blocks < 2:
            raise ValueError("min_blocks must be >= 2 — one block has nothing to hold out")
        self._linkage_km = float(linkage_km)
        self._design_name = str(design_name)
        self._min_blocks = int(min_blocks)
        self._purpose = str(purpose) or (
            f"hold out one single-linkage block at {self._linkage_km:g} km linkage"
        )

    @property
    def name(self) -> str:
        return self._design_name

    @property
    def purpose(self) -> str:
        return self._purpose

    @property
    def required_separation_km(self) -> float:
        """By construction: two stations in DIFFERENT single-linkage
        components at threshold t are more than t apart (otherwise the edge
        between them would have merged the components). So the guaranteed
        separation IS the linkage, derived, not hand-picked; the measured
        minimum per fold is recorded beside it."""
        return self._linkage_km

    def split(self, coords_lonlat: Any) -> FoldAssignment:
        points = _as_latlon_points(coords_lonlat)
        n = len(points)
        if n < 2:
            raise ValueError(f"cannot split {n} row(s)")
        labels = single_linkage_labels(points, self._linkage_km)
        n_blocks = max(labels) + 1
        if n_blocks < self._min_blocks:
            raise ValueError(
                f"{self._design_name}: single linkage at {self._linkage_km} km yields "
                f"{n_blocks} block(s) — fewer than the {self._min_blocks} needed to hold "
                "one out; the corpus is one connected component at this threshold"
            )
        edges = minimum_spanning_tree_edge_lengths_km(points)
        # Partition is constant for thresholds in [largest edge <= t, smallest edge > t).
        below = [e for e in edges if e <= self._linkage_km]
        above = [e for e in edges if e > self._linkage_km]
        stability = (max(below) if below else 0.0, min(above) if above else None)
        folds = []
        for block in range(n_blocks):
            test = tuple(i for i in range(n) if labels[i] == block)
            train = tuple(i for i in range(n) if labels[i] != block)
            lat_c = sum(points[i][0] for i in test) / len(test)
            lon_c = sum(points[i][1] for i in test) / len(test)
            folds.append(
                Fold(
                    name=f"holdout_block_{block}(n={len(test)},centroid_lat={lat_c:.3f},lon={lon_c:.3f})",
                    train_indices=train,
                    test_indices=test,
                    min_train_test_km=min_train_test_distance_km(points, train, test),
                )
            )
        return FoldAssignment(
            splitter_name=self._design_name,
            # Recorded FROM the class declaration, never a literal — the
            # provenance value E2.5 reads must be the enforced one (§1 review).
            spatially_blocked=type(self).spatially_blocked,
            notes=(self._purpose, f"required_separation_km={self._linkage_km:g} (= the linkage, by construction)"),
            rule=(
                "blocks are the connected components of the graph joining station pairs "
                "within linkage_km (great-circle); one fold per block: hold the block "
                "out, train on all other rows. Order-independent (components are a "
                "graph property); identical for every linkage in stability_interval_km."
            ),
            parameters={"linkage_km": self._linkage_km, "min_blocks": self._min_blocks},
            n_rows=n,
            labels=tuple(labels),
            folds=tuple(folds),
            stability_interval_km=stability,
            coords_sha256=coords_fingerprint(coords_lonlat),
        )


LOCO_PURPOSE = (
    "ACROSS-CLUSTER EXTRAPOLATION (~991 km): the geometry measurement — how much the "
    "clusters differ. Per the two-fold geometry theorem (BACKLOG §3 obligation 8) "
    "kriging ≈ baseline here BY CONSTRUCTION; this design measures cluster A's mean "
    "against cluster B's values and cannot rank estimators."
)
SITE_PURPOSE = (
    "WITHIN-CLUSTER, site-to-site interpolation at 4.6–10 km (sites = single-linkage "
    "blocks at 2 km; plateau [0.857, 4.614) km): THE HEADLINE within-cluster gate — "
    "the scale the spec's '1–13 km' meant; DEM-stable because sites are physical "
    "deployment locations, not cell artifacts (Karl, E2.4 §1B decision)."
)
LOSO_PURPOSE = (
    "SUB-KILOMETRE WITHIN-SITE interpolation (every held-out station has a site-mate "
    "within 0.86 km in training): labelled for exactly what it is — and, for RF, the "
    "real-data leakage demonstration beside the known-answer number. Deliberately "
    "UNBUFFERED (required_separation_km = 0; disjointness only). Never cited as a "
    "generalization result (Karl, E2.4 §1B decision)."
)
RANDOM_PURPOSE = (
    "THE DEMONSTRABLY-WRONG COMPARISON: random k-fold on autocorrelated data — reported "
    "beside the spatial designs to show the inflation random splitting produces; can "
    "never back a claim (spatially_blocked = False; assert_claim_eligible refuses it)."
)


def leave_one_cluster_out(linkage_km: float = DEFAULT_LINKAGE_KM) -> SingleLinkageBlockSplitter:
    """§1A: the across-cluster design. Default linkage = the corpus
    manifest's DEFAULT_LINKAGE_KM, so the CV clusters and the manifest's
    `spatial_summary_training_eligible.clusters` are one computation."""
    return SingleLinkageBlockSplitter(
        linkage_km=linkage_km, design_name="leave_one_cluster_out", purpose=LOCO_PURPOSE
    )


SITE_LINKAGE_KM = 2.0  # mid-plateau: any value in [0.857, 4.614) km gives the same five sites


def leave_one_site_out(linkage_km: float = SITE_LINKAGE_KM) -> SingleLinkageBlockSplitter:
    """§1B decision, design B — the headline within-cluster gate."""
    return SingleLinkageBlockSplitter(
        linkage_km=linkage_km, design_name="leave_one_site_out", purpose=SITE_PURPOSE
    )


class LeaveOneStationOutSplitter(FoldSplitter):
    """§1B decision, design A: n folds, each holding out ONE station and
    training on all others. `spatially_blocked = False` — deliberately: the
    held-out station's site-mates (≤ 0.86 km) are in training, so this
    design measures WITHIN-SITE interpolation and the real-data leakage RF
    shows; it is the unbuffered design and can never back a claim (the
    declaration is what E2.5 reads — the same bucket as random k-fold for
    claim purposes, for a different, stated reason)."""

    spatially_blocked: ClassVar[bool] = False

    @property
    def name(self) -> str:
        return "leave_one_station_out"

    @property
    def purpose(self) -> str:
        return LOSO_PURPOSE

    @property
    def required_separation_km(self) -> float:
        return 0.0  # disjointness only — stated, not hidden

    def split(self, coords_lonlat: Any) -> FoldAssignment:
        points = _as_latlon_points(coords_lonlat)
        n = len(points)
        if n < 3:
            raise ValueError(f"leave-one-station-out needs >= 3 rows (got {n}): a 2-row "
                             "fold would train on one station")
        folds = []
        for i in range(n):
            train = tuple(j for j in range(n) if j != i)
            folds.append(
                Fold(
                    name=f"holdout_station_{i}",
                    train_indices=train,
                    test_indices=(i,),
                    min_train_test_km=min_train_test_distance_km(points, train, (i,)),
                )
            )
        return FoldAssignment(
            splitter_name=self.name,
            spatially_blocked=type(self).spatially_blocked,
            rule="one fold per row: hold row i out, train on every other row; labels = row index",
            parameters={},
            n_rows=n,
            labels=tuple(range(n)),
            folds=tuple(folds),
            stability_interval_km=None,
            notes=(LOSO_PURPOSE, "required_separation_km=0 (unbuffered: disjointness only)"),
            coords_sha256=coords_fingerprint(coords_lonlat),
        )


class RandomKFoldSplitter(FoldSplitter):
    """The demonstrably-wrong comparison. Seeded, deterministic, and
    DECLARED `spatially_blocked = False`, so `assert_claim_eligible` refuses
    it by record. Its fold record still carries the measured min train–test
    separation — which, on the real corpus, is the leakage made visible as a
    number (a held-out station's site-mate ~0.3 km away in training)."""

    spatially_blocked: ClassVar[bool] = False

    def __init__(self, *, k: int, seed: int) -> None:
        if k < 2:
            raise ValueError("k must be >= 2")
        self._k = int(k)
        self._seed = int(seed)

    @property
    def name(self) -> str:
        return "random_k_fold"

    @property
    def purpose(self) -> str:
        return RANDOM_PURPOSE

    @property
    def required_separation_km(self) -> float:
        return 0.0

    def split(self, coords_lonlat: Any) -> FoldAssignment:
        points = _as_latlon_points(coords_lonlat)
        n = len(points)
        if n < self._k:
            raise ValueError(f"cannot make {self._k} folds from {n} rows")
        rng = np.random.default_rng(self._seed)
        order = rng.permutation(n)
        labels = [0] * n
        for position, row in enumerate(order):
            labels[int(row)] = position % self._k
        folds = []
        for fold_id in range(self._k):
            test = tuple(i for i in range(n) if labels[i] == fold_id)
            train = tuple(i for i in range(n) if labels[i] != fold_id)
            folds.append(
                Fold(
                    name=f"random_fold_{fold_id}",
                    train_indices=train,
                    test_indices=test,
                    min_train_test_km=min_train_test_distance_km(points, train, test),
                )
            )
        return FoldAssignment(
            splitter_name=self.name,
            spatially_blocked=type(self).spatially_blocked,
            rule="rows permuted by a seeded RNG and dealt round-robin into k folds; ignores geography",
            parameters={"k": self._k, "seed": self._seed},
            n_rows=n,
            labels=tuple(labels),
            folds=tuple(folds),
            stability_interval_km=None,
            notes=(RANDOM_PURPOSE,),
            coords_sha256=coords_fingerprint(coords_lonlat),
        )


def assert_spatially_separated(
    assignment: FoldAssignment, coords_lonlat: Any, *, min_separation_km: float
) -> dict[str, float]:
    """THE SPATIAL-LEAKAGE ASSERTION (E2.4 original requirement 4): for every
    fold, train and test are disjoint (Fold refuses otherwise at
    construction) AND separated by at least `min_separation_km`,
    RE-MEASURED here from the coordinates — not read back from the fold's
    recorded number, so a splitter that mis-recorded its own separation
    is caught rather than trusted. Raises by fold name, and RETURNS the
    measurements {fold name -> measured min km} so a caller records what was
    MEASURED rather than re-quoting what the splitter claimed (E2.4 §2
    review). The fold's own recorded number must equal the measurement."""
    points = _as_latlon_points(coords_lonlat)
    if len(points) != assignment.n_rows:
        raise ValueError(
            f"assignment covers {assignment.n_rows} rows but {len(points)} coordinates given"
        )
    if assignment.coords_sha256 is not None:
        actual = coords_fingerprint(coords_lonlat)
        if actual != assignment.coords_sha256:
            raise ValueError(
                f"{assignment.splitter_name}: these coordinates ({actual}) are not the ones "
                f"the assignment was split from ({assignment.coords_sha256}) — same length, "
                "different stations or row order; refusing to measure the wrong geometry"
            )
    measurements: dict[str, float] = {}
    for fold in assignment.folds:
        measured = min_train_test_distance_km(points, fold.train_indices, fold.test_indices)
        measurements[fold.name] = measured
        if measured < min_separation_km:
            raise ValueError(
                f"fold {fold.name!r}: a training station lies {measured:.3f} km from a "
                f"test station — below the stated minimum separation of "
                f"{min_separation_km} km; this fold leaks spatial structure across "
                "the train/test boundary"
            )
        if not np.isclose(measured, fold.min_train_test_km, rtol=1e-9, atol=1e-9):
            raise ValueError(
                f"fold {fold.name!r} records min_train_test_km="
                f"{fold.min_train_test_km:.6f} but the coordinates measure "
                f"{measured:.6f} km — the recorded separation is not a measurement"
            )
    return measurements
