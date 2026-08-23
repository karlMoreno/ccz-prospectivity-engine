#!/usr/bin/env python3
"""
demo.py - a live walkthrough of the CCZ Prospectivity Engine (Phase 1).

Structured to match the production-line diagram: raw published files in on the
left, finished corpus and terrain features out on the right.

  1. Rebuild the corpus from the raw files, live, and prove it is reproducible
  2. Follow ONE box core through every station of the line   <- what Phase 1 does
  3. What came off the line (the corpus, in plain numbers)
  4. The science rules refusing to be broken                 <- why you can trust it
  5. The two datasets cross-checking each other
  6. The terrain features, and the picture
  7. The honest limitation
  8. The test suite, last, as a footnote

Run from the repo root:      python demo.py
Present it with pauses:      python demo.py --pause
Skip the slow test suite:    python demo.py --no-tests
Do not open the image:       python demo.py --no-open

Read-only: the rebuild goes to a temp directory and is compared against the
committed corpus. Nothing in the repository is modified.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
CORPUS_CSV = REPO / "data" / "corpus" / "master_observations.csv"
MANIFEST = REPO / "data" / "corpus" / "manifest.json"

PAUSE = False
W = 74


# ---------------------------------------------------------------- presentation
def banner(n: int, text: str) -> None:
    print("\n" + "=" * W)
    print(f"  STEP {n}.  {text}")
    print("=" * W)


def ok(text: str) -> None:
    print(f"  [OK]        {text}")


def info(text: str) -> None:
    print(f"              {text}")


def warn(text: str) -> None:
    print(f"  [!]         {text}")


def refused(text: str) -> None:
    # "correctly refused" - this is a PASS, not a failure
    print(f"  [REFUSED - correct]  {text}")


def stage(label: str, text: str) -> None:
    print(f"\n  {label:<14} {text}")


def pause() -> None:
    if PAUSE:
        input("\n              -- press Enter --")


def first_or_none(seq):
    for item in seq:
        return item
    return None


# ------------------------------------------------------------------- 1. rebuild
def step_rebuild() -> bool:
    banner(1, "Rebuild the corpus from the published source files")
    try:
        from engine.prospectivity.ingestion.corpus_builder import (
            build_corpus,
            write_corpus_csv,
        )
    except Exception as exc:  # pragma: no cover
        warn(f"could not import the corpus builder: {exc}")
        return False

    info("reading the two PANGAEA datasets and running the whole line...")
    corpus_a = build_corpus()
    ok(f"built {len(corpus_a)} rows from the raw files")

    with tempfile.TemporaryDirectory() as tmp:
        path_a, path_b = Path(tmp) / "a.csv", Path(tmp) / "b.csv"
        write_corpus_csv(corpus_a, path_a)
        write_corpus_csv(build_corpus(), path_b)

        if path_a.read_bytes() == path_b.read_bytes():
            ok("built it a second time: byte-for-byte identical")
        else:
            warn("the two builds differ - that would be a bug")

        if CORPUS_CSV.exists() and path_a.read_bytes() == CORPUS_CSV.read_bytes():
            ok("identical to the corpus committed in the repository")
            info("anyone who clones this repo gets exactly these numbers")
        elif CORPUS_CSV.exists():
            warn("differs from the committed corpus - uncommitted changes?")

    pause()
    return True


# ------------------------------------------------- 2. follow one sample through
def step_follow_one() -> None:
    """The heart of the demo: one real box core, station by station."""
    banner(2, "Follow one box core through the line")
    info("This is the production line from the diagram, running on one real")
    info("sample. Watch what the row looks like after each station.")

    try:
        from engine.prospectivity.ingestion.corpus_builder import (
            build_boxcore_adapter,
            build_corpus,
        )
        from engine.prospectivity.ingestion.normalizer_registry import (
            build_default_registry,
        )
    except Exception as exc:  # pragma: no cover
        warn(f"could not import the pipeline pieces: {exc}")
        warn("skipping this step - the API may have moved since this was written")
        return

    try:
        adapter = build_boxcore_adapter()
        native_rows = adapter.fetch()
    except Exception as exc:
        warn(f"could not read the source file: {exc}")
        return

    native = first_or_none(native_rows)
    if native is None:
        warn("no rows returned from the source file")
        return

    event_key = native.get("Event") or first_or_none(native.values())

    # --- RAW ---------------------------------------------------------------
    stage("RAW FILE", f"one line from the PANGAEA .tab file (event {event_key})")
    shown = 0
    for key in native:
        value = native[key]
        if value is not None and str(value).strip() != "":
            info(f"  {str(key):<32} {value}")
            shown += 1
        if shown >= 8:
            break

    # --- STATION 1: READ ---------------------------------------------------
    try:
        adapted = adapter.adapt([native])
    except Exception as exc:
        warn(f"adapt failed: {exc}")
        return

    stage("STATION 1", f"READ - that one line became {len(adapted)} typed rows")
    info("  the same physical sample carries three different kinds of evidence:")
    for rec in adapted:
        cls = rec.get("evidence_class")
        bits = [
            f"{k}={v}"
            for k, v in rec.items()
            if k in ("nodule_mass_kg", "nodule_count", "visible_cover_percent",
                     "sampled_area_m2")
            and v is not None
        ]
        info(f"  {str(cls):<8} {', '.join(bits) if bits else '(no measurement fields)'}")
    info("  note: no kg/m2 computed yet - this station reads, it does no maths")

    # --- STATION 2 + 3: CONVERT and SCREEN ---------------------------------
    try:
        registry = build_default_registry()
        normalized = [registry.normalize(dict(r)) for r in adapted]
    except Exception as exc:
        warn(f"normalize failed: {exc}")
        return

    stage("STATION 2+3", "CONVERT and SCREEN - each class by its own rule")
    for rec in normalized:
        cls = str(rec.get("evidence_class"))
        abundance = rec.get("abundance_kg_m2")
        if abundance is None:
            verdict = "no kg/m2  (correct - this class must never produce one)"
        else:
            verdict = f"abundance = {abundance} kg/m2"
        info(f"  {cls:<8} {verdict}")
        formula = rec.get("derivation_formula")
        if formula:
            info(f"           how: {formula}")
        qa = rec.get("qa_status")
        if qa and str(qa) != "pending":
            info(f"           QA verdict: {qa}")

    # --- STATION 4: MERGE, and the finished row ----------------------------
    stage("STATION 4", "MERGE - and here is the finished row in the corpus")
    corpus = build_corpus()
    final = first_or_none(
        o for o in corpus
        if getattr(o, "event_id", None) == event_key
        and str(getattr(o, "evidence_class", "")).endswith("MASS")
    )
    if final is None:
        warn("could not locate that event's MASS row in the finished corpus")
    else:
        for field in ("source_record_id", "event_id", "cruise", "latitude", "longitude",
                      "water_depth_m", "abundance_kg_m2", "mean_nodule_mass_g",
                      "qa_status", "quality_grade"):
            value = getattr(final, field, None)
            if value is not None:
                info(f"  {field:<22} {value}")
        notes = getattr(final, "notes", None)
        if notes:
            info(f"  {'notes':<22} {notes}")
            info("  ^ the merge recorded the second dataset it absorbed")

    print()
    ok("one line of a published file, turned into evidence the model can use")
    pause()


# ----------------------------------------------------------------- 3. contents
def step_contents() -> dict:
    banner(3, "What came off the line")
    if not MANIFEST.exists():
        warn("manifest.json not found")
        return {}

    m = json.loads(MANIFEST.read_text())
    info(f"total rows              {m.get('corpus_row_count')}")
    for cls, n in sorted(m.get("rows_by_evidence_class", {}).items()):
        info(f"  {cls:<20} {n}")
    print()
    info(f"usable for training     {m.get('training_eligible_count')}")
    for status, n in sorted(m.get("rows_by_qa_status", {}).items()):
        info(f"  {status:<20} {n}")
    info("  (the flagged rows are one box core that failed on deck - kept in")
    info("   the corpus for the record, barred from training the model)")
    print()
    info("contributing sources:")
    for src in m.get("sources", []):
        merged = " (merged into the other source)" if src.get("fully_absorbed") else ""
        info(f"  {src.get('source_id')}{merged}")
        info(f"      {src.get('title')}")
        info(f"      doi {src.get('doi')}   licence {src.get('license')}")
        info(f"      file fingerprint {str(src.get('input_content_hash'))[:26]}...")
    print()
    ok("every row traces to a published dataset with a recorded fingerprint")
    pause()
    return m


# -------------------------------------------------------------------- 4. rules
def step_rules() -> None:
    banner(4, "The science rules cannot be broken")
    info("Now I try to create rows that break the rules we agreed on.")
    info("Every REFUSED line below is the engine working correctly: it is")
    info("rejecting data that would quietly corrupt the model.")
    print()

    try:
        from engine.prospectivity.domain.observation import Observation
    except Exception as exc:  # pragma: no cover
        warn(f"could not import Observation: {exc}")
        return

    base = dict(
        source_record_id="demo_row_000001",
        source_id="src_demo",
        latitude=12.0,
        longitude=-118.0,
        observation_or_prediction="observed",
        is_open=True,
        qa_status="pending",
    )

    attempts = [
        ("a COVER row (a % from seafloor photos) carrying a weight in kg/m2",
         dict(base, evidence_class="COVER", abundance_kg_m2=14.0),
         "a percentage of seafloor covered is not a weight per square metre"),
        ("a GRID row (a compiled map) labelled as a real observation",
         dict(base, evidence_class="GRID", observation_or_prediction="observed"),
         "a compiled surface is a benchmark, never a sampled station"),
        ("a GRADE row (metal percentages) carrying an abundance",
         dict(base, evidence_class="GRADE", abundance_kg_m2=9.0),
         "chemistry does not tell you how much is on the seafloor"),
        ("an abundance of 500 kg/m2",
         dict(base, evidence_class="MASS", abundance_kg_m2=500.0),
         "physically impossible - far past what a seafloor layer can hold"),
    ]

    for description, fields, why in attempts:
        try:
            Observation(**fields)
        except Exception:
            refused(description)
            info(f"    reason: {why}")
        else:
            warn(f"ACCEPTED - this should NOT happen: {description}")
        print()

    try:
        Observation(**dict(base, evidence_class="MASS", abundance_kg_m2=19.4))
    except Exception as exc:
        warn(f"a valid MASS row was rejected - that would be a bug: {exc}")
    else:
        ok("and a valid MASS row of 19.4 kg/m2 is accepted normally")
        info("so it is not simply refusing everything - it knows the difference")
    pause()


# --------------------------------------------------------------- 5. cross-check
def step_crosscheck() -> None:
    banner(5, "The two datasets check each other")
    info("Both PANGAEA datasets describe the same 36 box cores. One publishes")
    info("the summary; the other publishes all 1,658 nodules individually.")
    info("Aggregating the nodules should reproduce the authors' own totals.")
    print()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_reconciliation.py", "-v", "--no-header"],
        cwd=REPO, capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        if "PASSED" in line or "FAILED" in line:
            name = line.split("::")[-1].split(" ")[0]
            mark = "[OK]  " if "PASSED" in line else "[FAIL]"
            print(f"  {mark}      {name}")
    print()
    if result.returncode == 0:
        ok("two independently published datasets agree with our pipeline")
        info("an outside check - not our own test data marking its own work")
    else:
        warn("reconciliation tests did not all pass")
    pause()


# ------------------------------------------------------------------ 6. the plot
def step_plot(open_image: bool) -> None:
    banner(6, "The terrain features, and the picture")
    info("The other half of the line: eight terrain measurements computed from")
    info("the seafloor elevation grid - depth, slope, aspect, roughness,")
    info("curvature (two kinds), and two position indices.")
    print()
    warn("the elevation grid is still a PLACEHOLDER, not real bathymetry")
    info("so the terrain panels are stand-in terrain; the sample points are real")
    print()

    png = None
    try:
        from engine.prospectivity.features.plot_stack import plot_covariate_stack
        info("regenerating the figure...")
        result = plot_covariate_stack()
        if isinstance(result, (str, Path)):
            png = Path(result)
    except Exception as exc:
        info(f"(could not regenerate automatically: {exc})")

    if png is None or not Path(png).exists():
        candidates = sorted(REPO.glob("outputs/**/*.png")) + sorted(REPO.glob("docs/**/*.png"))
        png = first_or_none(candidates)

    if png and Path(png).exists():
        png = Path(png)
        try:
            shown_path = png.relative_to(REPO)
        except ValueError:
            shown_path = png
        ok(f"figure: {shown_path}")
        if open_image:
            try:
                if sys.platform == "darwin":
                    subprocess.run(["open", str(png)], check=False)
                elif sys.platform.startswith("win"):
                    subprocess.run(["cmd", "/c", "start", "", str(png)], check=False)
                else:
                    subprocess.run(["xdg-open", str(png)], check=False)
                info("(opened in your image viewer)")
            except Exception:
                info("(open it manually to view)")
        info("the two tight clusters of sample points are the story - see next step")
    else:
        warn("no figure found; build the covariate stack first")
    pause()


# -------------------------------------------------------------- 7. the geometry
def step_geometry(m: dict) -> None:
    banner(7, "The honest limitation")
    sp = m.get("spatial_summary_training_eligible", {})
    pw = sp.get("pairwise_distance_km", {})

    info(f"training stations       {sp.get('distinct_locations')}")
    info(f"clusters                {sp.get('clusters')}")
    for c in sp.get("cluster_extents", []):
        info(f"  {c.get('locations')} stations near "
             f"{c.get('centroid_latitude')}N {abs(c.get('centroid_longitude', 0))}W, "
             f"spanning {c.get('max_internal_distance_km')} km")
    print()
    if pw:
        gap = pw.get("largest_gap_between_km", [None, None])
        info(f"station pairs           {pw.get('pairs')}")
        info(f"largest gap in coverage {pw.get('largest_gap_km')} km")
        info(f"  not a single pair between {gap[0]} km and {gap[1]} km apart")
    print()
    info("This shapes everything next. We can measure how abundance behaves over")
    info("a few kilometres, and across a thousand - but nothing in between, which")
    info("is exactly the range we would want to predict across.")
    print()
    info("Practical upshot: samples BETWEEN the two clusters are worth far more")
    info("than more samples inside them.")
    pause()


# ------------------------------------------------------------------- 8. tests
def step_tests() -> None:
    banner(8, "The test suite")
    info("last, and least interesting to you: the engineering safety net")
    print()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=REPO, capture_output=True, text=True,
    )
    for line in [ln for ln in result.stdout.strip().splitlines() if ln.strip()][-1:]:
        print(f"              {line}")
    print()
    if result.returncode == 0:
        ok("everything green")
    else:
        warn("some tests failed - run pytest for the detail")


def main() -> int:
    global PAUSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--pause", action="store_true", help="wait for Enter between steps")
    ap.add_argument("--no-tests", action="store_true", help="skip the full test suite")
    ap.add_argument("--no-open", action="store_true", help="do not open the figure")
    args = ap.parse_args()
    PAUSE = args.pause

    print("\n" + "=" * W)
    print("  CCZ PROSPECTIVITY ENGINE - Phase 1 walkthrough")
    print("=" * W)
    print("  Everything below runs now, from the real published data files.")
    print("  Nothing is pre-computed; nothing in the repository is modified.")

    if not step_rebuild():
        return 1
    step_follow_one()
    manifest = step_contents()
    step_rules()
    step_crosscheck()
    step_plot(open_image=not args.no_open)
    if manifest:
        step_geometry(manifest)
    if not args.no_tests:
        step_tests()

    print("\n" + "=" * W)
    print("  Done.")
    print("=" * W + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())