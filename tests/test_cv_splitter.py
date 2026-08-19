"""E2.4 §1 — FoldSplitter Strategy, single-linkage fold assignment, and the
spatial-leakage assertion.

Fixture note (CLAUDE.md rule 4): the hand-built line at 0 / 1 / 3 / 7 km has
three DISTINCT consecutive gaps (1, 2, 4 km), so each threshold crossing
changes the partition in a way no other threshold reproduces — a
symmetric layout (equal gaps) could not distinguish "labels follow the
threshold" from "labels are hardcoded by count".
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

from engine.prospectivity.provenance.geometry import (
    DEFAULT_LINKAGE_KM,
    minimum_spanning_tree_edge_lengths_km,
    single_linkage_labels,
)
from engine.prospectivity.samples.corpus_csv import CorpusCsvSampleSource
from engine.prospectivity.validation.splitter import (
    Fold,
    FoldAssignment,
    FoldSplitter,
    SingleLinkageBlockSplitter,
    assert_spatially_separated,
    coords_fingerprint,
    leave_one_cluster_out,
)

# Four points on a meridian at 0, ~1, ~3, ~7 km (0.009° ≈ 1.001 km).
LINE_LATLON = [(0.0, 0.0), (0.009, 0.0), (0.027, 0.0), (0.063, 0.0)]
LINE_LONLAT = np.array([[lon, lat] for lat, lon in LINE_LATLON])


def _real_training_coords_lonlat() -> np.ndarray:
    """The 35 training stations in TrainingMatrix row order (sorted
    source_record_id) — coordinates only, no DEM needed."""
    obs = sorted(CorpusCsvSampleSource().get_training_samples(), key=lambda o: o.source_record_id)
    return np.array([[o.longitude, o.latitude] for o in obs], dtype=np.float64)


# ------------------------------------------------------------ geometry


def test_single_linkage_labels_follow_each_threshold_crossing_on_the_line() -> None:
    assert single_linkage_labels(LINE_LATLON, 1.5) == [0, 0, 1, 2]
    assert single_linkage_labels(LINE_LATLON, 2.5) == [0, 0, 0, 1]
    assert single_linkage_labels(LINE_LATLON, 5.0) == [0, 0, 0, 0]
    assert single_linkage_labels(LINE_LATLON, 0.5) == [0, 1, 2, 3]


def test_single_linkage_partition_is_identical_under_input_permutation() -> None:
    """Order-independence, asserted as PARTITIONS (sets of index sets mapped
    back through the permutation), not as label sequences."""
    rng = np.random.default_rng(7)
    perm = rng.permutation(len(LINE_LATLON))
    shuffled = [LINE_LATLON[i] for i in perm]
    original = single_linkage_labels(LINE_LATLON, 2.5)
    permuted = single_linkage_labels(shuffled, 2.5)

    def partition(labels: list[int], index_map: list[int]) -> set[frozenset[int]]:
        groups: dict[int, set[int]] = {}
        for pos, lab in enumerate(labels):
            groups.setdefault(lab, set()).add(index_map[pos])
        return {frozenset(g) for g in groups.values()}

    assert partition(original, list(range(4))) == partition(permuted, list(perm))


def test_mst_edge_lengths_on_the_line_are_its_three_consecutive_gaps() -> None:
    edges = minimum_spanning_tree_edge_lengths_km(LINE_LATLON)
    assert np.allclose(edges, [1.001, 2.002, 4.003], atol=2e-3)
    assert minimum_spanning_tree_edge_lengths_km(LINE_LATLON[:1]) == []


# ------------------------------------------------------------- the ABC


def test_splitter_without_the_spatially_blocked_declaration_cannot_be_declared() -> None:
    with pytest.raises(TypeError, match="spatially_blocked"):

        class Undeclared(FoldSplitter):  # noqa: D401 — the probe
            @property
            def name(self) -> str:
                return "undeclared"

            def split(self, coords_lonlat):  # type: ignore[override]
                raise NotImplementedError

    with pytest.raises(TypeError, match="spatially_blocked"):

        class WronglyTyped(FoldSplitter):
            spatially_blocked = "yes"  # a string is not a declaration

            @property
            def name(self) -> str:
                return "wrong"

            def split(self, coords_lonlat):  # type: ignore[override]
                raise NotImplementedError


def test_a_subclass_of_a_declared_splitter_inherits_the_declaration() -> None:
    """Inheritance is a declaration: a grandchild of SingleLinkageBlockSplitter
    that does not restate `spatially_blocked` is accepted and reads True
    (MRO lookup, not cls.__dict__ — a false refusal here would make
    subclassing a declared splitter impossible)."""

    class Narrower(SingleLinkageBlockSplitter):
        pass

    assert Narrower.spatially_blocked is True
    assert Narrower(linkage_km=1.0, design_name="narrower").name == "narrower"


# ---------------------------------------------------------------- Fold


def test_fold_refuses_overlap_repeats_and_empty_sets_by_name() -> None:
    with pytest.raises(ValueError, match="not disjoint"):
        Fold("f", (0, 1), (1, 2), 1.0)
    with pytest.raises(ValueError, match="repeats"):
        Fold("f", (0, 0), (1,), 1.0)
    with pytest.raises(ValueError, match="empty test"):
        Fold("f", (0, 1), (), 1.0)
    with pytest.raises(ValueError, match="empty train"):
        Fold("f", (), (0,), 1.0)


def test_fold_assignment_refuses_out_of_range_rows_a_row_tested_twice_and_a_row_never_tested() -> None:
    def build(folds, n=4):
        return FoldAssignment("probe", True, "hand-built", {}, n, tuple([0] * n), folds)

    with pytest.raises(ValueError, match="row 4, outside 0..3"):
        build((Fold("a", (0, 1), (4,), 1.0), Fold("b", (0, 4), (1, 2, 3), 1.0)))
    with pytest.raises(ValueError, match="row 1 is held out by both 'a' and 'b'"):
        build((Fold("a", (0, 2), (1, 3), 1.0), Fold("b", (0, 3), (1, 2), 1.0)))
    with pytest.raises(ValueError, match="rows \\[3\\] are never held out"):
        build((Fold("a", (0, 1), (2,), 1.0), Fold("b", (2, 3), (0, 1), 1.0)))
    with pytest.raises(ValueError, match="3 labels for 4 rows"):
        FoldAssignment("probe", True, "r", {}, 4, (0, 0, 0), (Fold("a", (0, 1, 2), (3,), 1.0),))


def test_fold_assignment_refuses_labels_that_disagree_with_the_folds_and_degenerate_shapes() -> None:
    """Labels and folds are ONE record: a fold holding out rows of two labels,
    or a fold whose test set is not exactly the rows of its label, is
    refused by name; so are a non-bool declaration, n_rows < 2 and zero
    folds, and a fold recording a NaN or negative distance."""
    ok_folds = (Fold("a", (2, 3), (0, 1), 1.0), Fold("b", (0, 1), (2, 3), 1.0))
    FoldAssignment("probe", True, "r", {}, 4, (0, 0, 1, 1), ok_folds)  # consistent: accepted
    with pytest.raises(ValueError, match="2 different labels"):
        FoldAssignment("probe", True, "r", {}, 4, (0, 1, 2, 2), ok_folds)
    with pytest.raises(ValueError, match="labels and folds disagree"):
        FoldAssignment(
            "probe", True, "r", {}, 4, (0, 0, 0, 1),
            (Fold("a", (2, 3), (0, 1), 1.0), Fold("b", (0, 1), (2, 3), 1.0)),
        )
    with pytest.raises(ValueError, match="must be a bool declaration"):
        FoldAssignment("probe", "yes", "r", {}, 4, (0, 0, 1, 1), ok_folds)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=">= 2 rows and >= 1 fold"):
        FoldAssignment("probe", True, "r", {}, 4, (0, 0, 1, 1), ())
    with pytest.raises(ValueError, match="min_train_test_km=nan"):
        Fold("a", (0,), (1,), float("nan"))
    with pytest.raises(ValueError, match="min_train_test_km=-1.0"):
        Fold("a", (0,), (1,), -1.0)


def test_splitter_refuses_coordinates_in_lat_lon_order_by_name() -> None:
    """The real corpus handed in as (lat, lon) is still (n, 2) and finite and
    would split into two plausible folds with wrong distances — the range
    check names the likely cause."""
    swapped = _real_training_coords_lonlat()[:, ::-1]
    with pytest.raises(ValueError, match="wrong column order"):
        leave_one_cluster_out().split(swapped)


def test_recorded_spatially_blocked_comes_from_the_class_declaration_not_a_literal() -> None:
    class Unblocked(SingleLinkageBlockSplitter):
        spatially_blocked = False  # a (contrived) re-declaration

    a = Unblocked(linkage_km=2.5, design_name="unblocked").split(LINE_LONLAT)
    assert a.spatially_blocked is False
    assert leave_one_cluster_out().split(_real_training_coords_lonlat()).spatially_blocked is True


# ------------------------------------------------- SingleLinkageBlockSplitter


def test_line_split_at_2_5km_gives_two_folds_with_the_measured_4km_separation() -> None:
    splitter = SingleLinkageBlockSplitter(linkage_km=2.5, design_name="probe")
    assignment = splitter.split(LINE_LONLAT)
    assert assignment.labels == (0, 0, 0, 1)
    assert len(assignment.folds) == 2
    by_test = {f.test_indices: f for f in assignment.folds}
    assert set(by_test) == {(0, 1, 2), (3,)}
    for f in assignment.folds:
        assert f.min_train_test_km == pytest.approx(4.003, abs=2e-3)
    lo, hi = assignment.stability_interval_km
    assert lo == pytest.approx(2.002, abs=2e-3) and hi == pytest.approx(4.003, abs=2e-3)
    assert assignment.spatially_blocked is True and assignment.splitter_name == "probe"


def test_splitter_refuses_by_name_when_the_threshold_yields_one_block() -> None:
    with pytest.raises(ValueError, match="1 block"):
        SingleLinkageBlockSplitter(linkage_km=100.0, design_name="probe").split(LINE_LONLAT)


def test_leave_one_cluster_out_on_the_real_corpus_is_two_folds_21_E_and_14_W_986_km_apart() -> None:
    """The §1A rule on the real 35 stations: two blocks; the E cluster
    (longitude > -120) holds 21, the W 14; every training station is
    >= 986 km from every test station in both folds; and the recorded
    stability interval is [10.018, 986.036) km — the plateau within which
    ANY linkage reproduces this assignment."""
    coords = _real_training_coords_lonlat()
    assignment = leave_one_cluster_out().split(coords)
    assert assignment.n_rows == 35 and len(assignment.folds) == 2
    labels = np.array(assignment.labels)
    east = coords[:, 0] > -120.0
    assert len(set(labels[east])) == 1 and len(set(labels[~east])) == 1
    assert east.sum() == 21 and (~east).sum() == 14
    sizes = sorted(len(f.test_indices) for f in assignment.folds)
    assert sizes == [14, 21]
    for f in assignment.folds:
        assert f.min_train_test_km >= 986.0
        assert len(f.train_indices) + len(f.test_indices) == 35
    lo, hi = assignment.stability_interval_km
    assert lo == pytest.approx(10.018, abs=1e-3)
    assert hi == pytest.approx(986.036, abs=1e-3)
    assert assignment.parameters == {"linkage_km": DEFAULT_LINKAGE_KM, "min_blocks": 2}
    assert_spatially_separated(assignment, coords, min_separation_km=900.0)


def test_fold_assignment_is_deterministic_and_identical_across_the_stability_interval() -> None:
    """Full-state comparison of labels AND folds (frozen dataclasses) across
    three linkages inside [10.018, 986.036) km and across two calls."""
    coords = _real_training_coords_lonlat()
    a = leave_one_cluster_out().split(coords)
    b = leave_one_cluster_out().split(coords)
    c = SingleLinkageBlockSplitter(linkage_km=11.0, design_name="leave_one_cluster_out").split(coords)
    d = SingleLinkageBlockSplitter(linkage_km=900.0, design_name="leave_one_cluster_out").split(coords)
    assert a == b  # full FoldAssignment equality (dataclass __eq__)
    for other in (c, d):
        # FULL state (rule 3): only `parameters` (the linkage) legitimately differs
        assert dataclasses.replace(other, parameters=a.parameters) == a
    # The interval is HALF-OPEN [lo, hi): a linkage EXACTLY at lo (the
    # 10.018 km MST edge, bit-identical because the same haversine computes
    # both) reproduces the assignment; exactly at hi (986.036 km) the two
    # clusters merge into one block and the splitter refuses by name.
    lo, hi = a.stability_interval_km
    at_lo = SingleLinkageBlockSplitter(linkage_km=lo, design_name="leave_one_cluster_out").split(coords)
    assert dataclasses.replace(at_lo, parameters=a.parameters) == a
    with pytest.raises(ValueError, match="1 block"):
        SingleLinkageBlockSplitter(linkage_km=hi, design_name="leave_one_cluster_out").split(coords)


def test_leave_one_cluster_out_changes_when_the_linkage_leaves_the_plateau() -> None:
    """The plateau's edges are real: at 10.0 km (just under the 10.018 km
    MST edge) the W cluster splits into its two sites → three blocks."""
    coords = _real_training_coords_lonlat()
    a = SingleLinkageBlockSplitter(linkage_km=10.0, design_name="probe").split(coords)
    assert len(a.folds) == 3
    labels = np.array(a.labels)
    east = coords[:, 0] > -120.0
    assert len(set(labels[east])) == 1  # E stays whole (its largest internal MST edge is 6.219 km)
    assert len(set(labels[~east])) == 2  # W splits into its two sites (10.018 km apart)


# ------------------------------------------ the spatial-leakage assertion


def test_assert_spatially_separated_remeasures_from_coordinates_and_fails_by_fold_name() -> None:
    """A fold that RECORDS a comfortable separation (999 km) but whose
    stations are actually ~1 km apart must fail: the assertion measures,
    it does not trust the fold's own number."""
    # Train sets are deliberately NOT "all other rows" (the buffered-design
    # generality): the ONLY fold with a sub-2 km crossing is the liar, so a
    # trusting implementation would pass everything (DID NOT RAISE) and a
    # measuring one names near_pair.
    lying = FoldAssignment(
        splitter_name="probe",
        spatially_blocked=True,
        rule="hand-built",
        parameters={},
        n_rows=4,
        labels=(0, 1, 2, 2),
        folds=(
            Fold("near_pair", (1,), (0,), min_train_test_km=999.0),  # really ~1.001 km
            Fold("honest_pair", (2, 3), (1,), min_train_test_km=2.002),  # really ~2.002 km
            Fold("far_pair", (0, 1), (2, 3), min_train_test_km=2.002),  # really ~2.002 km
        ),
    )
    with pytest.raises(ValueError, match="near_pair.*1\\.001 km"):
        assert_spatially_separated(lying, LINE_LONLAT, min_separation_km=2.0)
    assert_spatially_separated(lying, LINE_LONLAT, min_separation_km=1.0)  # all folds >= 1 km
    with pytest.raises(ValueError, match="35 rows"):
        assert_spatially_separated(
            leave_one_cluster_out().split(_real_training_coords_lonlat()),
            LINE_LONLAT,
            min_separation_km=1.0,
        )
    # same length, different row ORDER: the fingerprint refuses before any
    # distance is measured against the wrong stations
    coords = _real_training_coords_lonlat()
    assignment = leave_one_cluster_out().split(coords)
    reordered = coords[::-1].copy()
    with pytest.raises(ValueError, match="not the ones the assignment was split from"):
        assert_spatially_separated(assignment, reordered, min_separation_km=1.0)


def test_fold_assignment_record_is_json_serializable_and_complete() -> None:
    """COMPLETE means every top-level and every per-fold key is present and
    equal to the assignment's own state — the §2D manifest form cannot drop
    a field silently."""
    assignment = leave_one_cluster_out().split(_real_training_coords_lonlat())
    record = json.loads(json.dumps(assignment.to_record()))
    assert set(record) == {
        "splitter_name", "spatially_blocked", "rule", "parameters", "n_rows", "labels",
        "stability_interval_km", "folds", "notes", "coords_sha256",
    }
    assert record["coords_sha256"] == assignment.coords_sha256
    assert assignment.coords_sha256 == coords_fingerprint(_real_training_coords_lonlat())
    assert record["splitter_name"] == assignment.splitter_name == "leave_one_cluster_out"
    assert record["spatially_blocked"] is True
    assert record["rule"] == assignment.rule and record["notes"] == list(assignment.notes)
    assert record["parameters"] == assignment.parameters
    assert record["n_rows"] == 35 and record["labels"] == list(assignment.labels)
    assert record["stability_interval_km"] == pytest.approx([10.018, 986.036], abs=1e-3)
    assert len(record["folds"]) == len(assignment.folds) == 2
    for rec, fold in zip(record["folds"], assignment.folds):
        assert set(rec) == {"name", "train_indices", "test_indices", "n_train", "n_test", "min_train_test_km"}
        assert rec["name"] == fold.name
        assert rec["train_indices"] == list(fold.train_indices)
        assert rec["test_indices"] == list(fold.test_indices)
        assert rec["n_train"] == len(fold.train_indices) and rec["n_test"] == len(fold.test_indices)
        assert rec["n_train"] + rec["n_test"] == 35
        assert rec["min_train_test_km"] == fold.min_train_test_km
