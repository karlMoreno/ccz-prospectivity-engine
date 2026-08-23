"""verify_run — the CI artifact job's verification step (E5.6), also a command.

    python -m engine.prospectivity.verify_run <run_dir> [--same-as <other_run_dir>] [--environment]

RUNS THE MACHINERY THAT EXISTS; RE-IMPLEMENTS NOTHING. What a finished run
directory can be held to after the fact, each by recomputation:

  1. the manifest describes itself — `RunManifest.compute_content_hash()`
     equals its `content_hash`, it is EXTENDED, every file it names exists
     (`services.api.app.load_run`, the API's own loader — the same eight
     refusals a deployment would meet);
  2. every OUTPUT FILE's bytes hash to the value the manifest records
     (`output_hashes`, all 52 keys — the surfaces, sidecars, economics
     rasters and record, the exports);
  3. the chain's portable links recompute: the corpus manifest's substance
     (committed under data/) and the feature stack's substance
     (<run>/features/stack/provenance.json) equal what the run quotes;
  4. THE VERDICT'S FAILING AND PASSING SETS EQUAL THE COMMITTED EXPECTATION
     below — E2.5's guard re-run on the manifest (`evaluate_claim`), never
     the recorded sets read back. THE JOB IS NOT A GATE ON THE VERDICT: the
     guard REFUSES today, that is the correct output, and this passes on a
     refusing run. It fails only if the sets MOVE — which is what the day
     CP1/CP4 land looks like, and the expectation is then updated on purpose;
  5. with --same-as: the two-tree claim on one machine — the other run's
     content_hash and output_hashes are identical (HASH.1's promise,
     exercised on infrastructure nobody controls).

KNOWN LIMITS, so a red job is diagnosed rather than debugged (HASH.1): a run
built on ANOTHER machine may differ from a local one in (a) raster bytes
across GDAL versions — which reaches every raster hash, the sidecars and
exports that quote them, and so output_hashes — and (b) `inputs.environment`,
which sits inside the run hash BY DESIGN, so content_hash differs across
machines even when every scientific value is equal. Neither is a substance
difference. --environment prints the block so the two can be compared, and
`--same-as` across machines is a deliberate command on a downloaded artifact,
not this job's assertion. If the VERDICT SETS, the corpus link, the stack
link, or the manifest's self-consistency differ, that IS substance and the
job fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.prospectivity.features.stack import FeatureStackManifest
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.corpus_manifest import CorpusManifest
from engine.prospectivity.validation.claim import evaluate_claim

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# THE COMMITTED EXPECTATION (E2.5 §2; E4.3 §3; unchanged through Phase 5): per
# design, the failing set and the SIZE of the passing set. Both halves, so a
# blanket refusal cannot pass as the discriminating one. Updated deliberately
# the day the facts change; a job that goes red here has found the verdict MOVING.
GATE = "an_acceptance_threshold_existed_before_the_scores"
BLOCKED = "spatially_blocked_cross_validation_ran"
EXPECTED_VERDICT_SETS: dict[str, tuple[frozenset[str], int]] = {
    "leave_one_cluster_out": (frozenset({GATE}), 5),
    "leave_one_site_out": (frozenset({GATE}), 5),
    "leave_one_station_out": (frozenset({GATE, BLOCKED}), 4),
    "random_k_fold": (frozenset({GATE, BLOCKED}), 4),
}


class VerificationFailed(ValueError):
    """A SUBSTANCE problem with a run directory, named."""


def verify(run_dir: Path | str, *, same_as: Path | str | None = None) -> dict:
    """Every check above; raises VerificationFailed by name; returns a report."""
    from services.api.app import NotARun, load_run  # the API's loader: the same refusals a deployment meets

    run_dir = Path(run_dir)
    try:
        run = load_run(run_dir)
    except NotARun as error:
        raise VerificationFailed(f"not a run directory: {error}") from None
    manifest, raw = run.manifest, run.raw
    report: dict = {"run_id": manifest.run_id, "content_hash": manifest.content_hash, "schema_version": manifest.schema_version}

    # 2. every output file's bytes
    mismatched = [k for k, digest in manifest.output_hashes.items() if file_sha256(run_dir / k) != digest]
    if mismatched:
        raise VerificationFailed(f"{len(mismatched)} output file(s) do not hash to the manifest's record: {mismatched[:5]}")
    report["output_files_verified"] = len(manifest.output_hashes)

    # 3. the portable links
    corpus = json.loads((REPO_ROOT / "data" / "corpus" / "manifest.json").read_text())
    corpus_hash = CorpusManifest(**corpus).compute_content_hash()
    if corpus_hash != manifest.upstream_hashes.get("corpus") or corpus_hash != raw["provenance_chain"]["links"]["corpus"]["content_hash"]:
        raise VerificationFailed(f"the corpus link does not recompute: substance {corpus_hash}, run quotes {manifest.upstream_hashes.get('corpus')}")
    stack_path = run_dir / "features" / "stack" / "provenance.json"
    if not stack_path.is_file():
        raise VerificationFailed(f"the feature stack's manifest is missing: {stack_path}")
    stack = json.loads(stack_path.read_text())
    stack_hash = FeatureStackManifest(**stack).compute_content_hash()
    if stack_hash != manifest.upstream_hashes.get("feature_stack") or stack_hash != stack.get("content_hash"):
        raise VerificationFailed(f"the feature-stack link does not recompute: substance {stack_hash}, run quotes {manifest.upstream_hashes.get('feature_stack')}")
    report["links_recomputed"] = ["corpus", "feature_stack"]

    # 4. the verdict, re-run and compared to the committed expectation, both halves
    designs = [d["name"] for d in manifest.cross_validation.get("designs", [])]
    sets = {}
    for design in designs:
        v = evaluate_claim(manifest, design=design, feature_stack_manifest=stack)
        failing = frozenset(r.precondition.value for r in v.results if not r.passed)
        passing = frozenset(r.precondition.value for r in v.results if r.passed)
        sets[design] = (failing, len(passing))
        if design not in EXPECTED_VERDICT_SETS:
            raise VerificationFailed(f"design {design!r} has no committed verdict expectation")
        if sets[design] != EXPECTED_VERDICT_SETS[design]:
            raise VerificationFailed(
                f"THE VERDICT MOVED on {design!r}: failing {sorted(failing)} with {len(passing)} passing, expected "
                f"failing {sorted(EXPECTED_VERDICT_SETS[design][0])} with {EXPECTED_VERDICT_SETS[design][1]} passing — "
                "if the facts changed (a checkpoint landed), update EXPECTED_VERDICT_SETS deliberately"
            )
        recorded = raw["claim"]["verdicts"][design]
        if frozenset(p["precondition"] for p in recorded["preconditions"] if not p["passed"]) != failing:
            raise VerificationFailed(f"the recorded verdict for {design!r} disagrees with the guard re-run")
    report["verdict_sets"] = {d: (sorted(f), n) for d, (f, n) in sets.items()}
    report["claim_design"] = raw["claim"]["design"]
    report["eligible"] = {d: raw["claim"]["verdicts"][d]["eligible"] for d in designs}

    # 5. the two-tree claim on this machine
    if same_as is not None:
        other = load_run(Path(same_as))
        if other.manifest.content_hash != manifest.content_hash:
            raise VerificationFailed(
                f"two runs on this machine differ: {manifest.content_hash} vs {other.manifest.content_hash} — "
                "path dependence or non-determinism has entered the chain (HASH.1's promise broken)"
            )
        if other.manifest.output_hashes != manifest.output_hashes:
            moved = sorted(k for k in manifest.output_hashes if other.manifest.output_hashes.get(k) != manifest.output_hashes[k])
            raise VerificationFailed(f"two runs on this machine wrote different bytes for {moved[:5]}")
        report["same_as"] = {"run_id": other.manifest.run_id, "identical": True}

    report["environment"] = manifest.inputs.get("environment")
    report["n_output_files"] = len(manifest.output_hashes)
    report["bytes"] = sum(p.stat().st_size for p in run_dir.rglob("*") if p.is_file())
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m engine.prospectivity.verify_run", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run_dir", type=Path)
    p.add_argument("--same-as", type=Path, default=None, help="a second run directory that must be byte-identical in substance (the two-tree claim)")
    p.add_argument("--environment", action="store_true", help="print the manifest's inputs.environment block (the by-design hash-bearing limit)")
    a = p.parse_args(argv)
    try:
        report = verify(a.run_dir, same_as=a.same_as)
    except VerificationFailed as error:
        print(f"VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1
    env = report.pop("environment")
    print(json.dumps(report, indent=2, default=str))
    if a.environment:
        print("inputs.environment (inside the run hash BY DESIGN — differs across machines without a substance difference):")
        print(json.dumps(env, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
