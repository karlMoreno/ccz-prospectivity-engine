"""The data-origin audit (P2.0d-1): every tracked file under data/ and
tests/fixtures/ carries a classification, or is excluded here by name with a
reason.

ANTI-TAUTOLOGY STRUCTURE — the load-bearing design decision. Enumeration and
classification come from DIFFERENT authorities: the subject list is what git
tracks (`git ls-files`), the classifications come from the marker resolver.
If the walk ever collected its subjects FROM the resolver, an unclassified
file would be structurally unobservable — that is the mutation this module's
negation fixtures exist to catch (P2.0b's review found exactly this shape).
Enumerating tracked files also makes generated caches (__pycache__,
.DS_Store) a non-problem with NO directory-level exclusion: git does not
track them, so they are never subjects.

The marker locations (P2.0c) the resolver reads, in one pass so
cross-location disagreements — in origin, author, OR citation — are visible
contradictions rather than first-match-wins:

  1. in-file   — top-level `data_origin` in YAML/JSON/GeoJSON, or an
                 importable DATA_ORIGIN constant in a tests/fixtures module.
                 Marker form 2 (`<node>_data_origin` sibling keys, e.g.
                 normalization.yaml's screening block) resolves as its own
                 `path#node` subject, so its evidence rules are enforced
                 without colliding with the file-level declaration.
  2. sidecar   — a sibling data_origin.yaml with a `files:` entry
  3. queue     — the source_queue declaration, resolved through
                 data/corpus/manifest.json's recorded input_path -> the
                 source's data_origin (the manifest is the path-bearing
                 projection of the queue entry)

`study_area.geojson` is the one classified file none of the three can reach:
it is hash-pinned (contract_versions.study_area_content_hash) and its
declaration lives in the contracts README row — so it appears in EXCLUSIONS
with exactly that reason, not silently special-cased.
"""

from __future__ import annotations

import importlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from engine.prospectivity.provenance.origin import (
    AUTHOR_UNRECORDED,
    DataOrigin,
    validate_author,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

SIDECAR_NAME = "data_origin.yaml"

# ---------------------------------------------------------------------------
# EXPLICIT EXCLUSIONS — one file, one reason. No globs, no directories: a
# pattern lets a subtree go dark, the coverage-that-isn't shape three Phase-1
# audits kept finding. A stale entry (file gone) or a shadowing entry (file
# actually classified) fails its own hygiene test below.
EXCLUSIONS: dict[str, str] = {
    "data/aoi/study_area.geojson": (
        "hash-pinned (contract_versions.study_area_content_hash); origin "
        "declared in docs/contracts/README.md contract-2 row (AUTHORED, "
        "author: unrecorded); an in-file marker would move the recorded hash"
    ),
    "data/bathymetry/README.md": (
        "documentation prose, no data values (audit §3); the directory is "
        "reserved for real GEBCO at Checkpoint 1"
    ),
    "data/corpus/data_origin.yaml": (
        "the sidecar declaration mechanism itself, not a subject"
    ),
    "data/fixtures/native/data_origin.yaml": (
        "the sidecar declaration mechanism itself, not a subject"
    ),
    "tests/fixtures/samples/data_origin.yaml": (
        "the sidecar declaration mechanism itself, not a subject"
    ),
    "tests/fixtures/__init__.py": "empty package marker, no values",
    "tests/fixtures/samples/README.md": (
        "documentation prose; its false blanket claim is tracked in "
        "docs/BACKLOG.md §3 (samples README false blanket claim)"
    ),
}

# ---------------------------------------------------------------------------
# THE FROZEN `author: unrecorded` SET (P2.0c walkthrough §c) — the files
# permitted to say "the author is not reconstructible from the repo". Same
# mechanism as DELIBERATELY_UNREACHABLE in test_corpus_invariants.py: an
# honest gap that can only shrink. A NEW use fails by name; a removed use
# also fails, so shrinking is a deliberate edit to this list in the same
# commit. (study_area.geojson's README-row declaration also says unrecorded,
# but it is prose, not machine-readable, so it is not a scanned subject.)
FROZEN_UNRECORDED: frozenset[str] = frozenset(
    {
        # file-level in-file declarations
        "data/aoi/exclusions.geojson",
        "data/config/normalization.yaml",
        "data/economics/scenarios.yaml",
        "data/sources/source_queue.yaml",
        "data/ts6/ts6_reference.yaml",
        # contracts outside the data/+tests/fixtures walk, scanned explicitly
        "docs/contracts/covariates.yaml",
        "docs/contracts/master_observations.schema.json",
        # sidecar-declared hand-typed CSVs
        "data/fixtures/native/synthetic_boxcore_native.csv",
        "data/fixtures/native/synthetic_cover_native.csv",
        "data/fixtures/native/synthetic_grid_native.csv",
        "tests/fixtures/samples/pangaea_boxcore_sample.csv",
        "tests/fixtures/samples/dryad_chamber_sample.csv",
        "tests/fixtures/samples/regional_grid_sample.csv",
        # fixture modules (DATA_AUTHOR constants)
        "tests/fixtures/adapters.py",
        "tests/fixtures/normalizers.py",
        "tests/fixtures/sample_source.py",
    }
)

# Files OUTSIDE the walk that the unrecorded scan must still read, because
# the frozen set includes them (P2.0c marked docs/contracts/ files too).
UNRECORDED_SCAN_EXTRAS: tuple[str, ...] = (
    "docs/contracts/covariates.yaml",
    "docs/contracts/master_observations.schema.json",
)


@dataclass(frozen=True)
class Declaration:
    location: str  # "in-file" | "in-file-node" | "sidecar" | "queue-via-manifest"
    data_origin: str
    author: str | None = None
    citation: str | None = None
    # Resolver-side evidence for the two members d-1 left unchecked
    # (P2.0d-2 §0.1): SYNTHETIC must name its generator import path AND
    # seed(s); DERIVED must name its derivation formula or the artifact
    # recording it. (MEASURED's evidence — a proven hashed file — is the
    # production guard's check, engine side, not resolver-side.)
    generator: str | None = None
    seeds: object | None = None
    derivation: str | None = None


def tracked_subject_files() -> list[str]:
    """The subject list, from git — NOT from the resolver (see module
    docstring). CI checkouts and dev clones both have git."""
    raw = subprocess.run(
        ["git", "ls-files", "-z", "--", "data", "tests/fixtures"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return sorted(path for path in raw.split("\0") if path)


def _load_yaml_top_level(path: Path) -> dict:
    loaded = yaml.safe_load(path.read_text())
    return loaded if isinstance(loaded, dict) else {}


def _in_file_declaration(root: Path, rel_path: str) -> Declaration | None:
    path = root / rel_path
    suffix = path.suffix.lower()
    if path.name == SIDECAR_NAME:
        return None  # the mechanism, not a subject declaration
    if suffix in (".yaml", ".yml"):
        top = _load_yaml_top_level(path)
    elif suffix in (".json", ".geojson"):
        loaded = json.loads(path.read_text())
        top = loaded if isinstance(loaded, dict) else {}
    elif suffix == ".py" and rel_path.startswith("tests/fixtures/"):
        module = importlib.import_module(
            rel_path[: -len(".py")].replace("/", ".")
        )
        origin = getattr(module, "DATA_ORIGIN", None)
        if origin is None:
            return None
        # No DataOrigin() call here: a bogus constant must surface as a
        # named entry in findings.invalid (audit() validates uniformly),
        # not crash collection with a traceback naming the resolver.
        return Declaration(
            location="in-file",
            data_origin=origin.value if isinstance(origin, DataOrigin) else str(origin),
            author=getattr(module, "DATA_AUTHOR", None),
            generator=getattr(module, "DATA_GENERATOR", None),
            seeds=getattr(module, "DATA_SEEDS", getattr(module, "DATA_SEED", None)),
        )
    else:
        return None
    if top.get("data_origin") is None:
        return None
    return Declaration(
        location="in-file",
        data_origin=str(top["data_origin"]),
        author=top.get("author"),
        citation=top.get("citation"),
        generator=top.get("generator"),
        seeds=top.get("seeds", top.get("seed")),
        derivation=top.get("derivation"),
    )


def _node_declarations(root: Path, rel_path: str) -> dict[str, Declaration]:
    """Marker form 2: `<node>_data_origin` sibling keys beside an iterated
    mapping (normalization.yaml's screening block is the one instance today).
    Each becomes its own `path#node` subject so its evidence rules are
    enforced, without colliding with the file-level declaration — a file's
    two declared blocks differing is the entries→file combine rule at work,
    not a cross-location contradiction."""
    path = root / rel_path
    if path.suffix.lower() not in (".yaml", ".yml") or path.name == SIDECAR_NAME:
        return {}
    top = _load_yaml_top_level(path)
    subjects: dict[str, Declaration] = {}
    for key, value in top.items():
        if key == "data_origin" or not key.endswith("_data_origin"):
            continue
        node = key[: -len("_data_origin")]
        subjects[f"{rel_path}#{node}"] = Declaration(
            location="in-file-node",
            data_origin=str(value),
            author=top.get(f"{node}_author"),
            citation=top.get(f"{node}_citation"),
        )
    return subjects


def _sidecar_declaration(root: Path, rel_path: str) -> Declaration | None:
    sidecar = (root / rel_path).parent / SIDECAR_NAME
    if not sidecar.is_file():
        return None
    entry = (_load_yaml_top_level(sidecar).get("files") or {}).get(Path(rel_path).name)
    if not entry:
        return None
    return Declaration(
        location="sidecar",
        data_origin=str(entry.get("data_origin")),
        author=entry.get("author"),
        citation=entry.get("citation"),
        generator=entry.get("generator"),
        seeds=entry.get("seeds", entry.get("seed")),
        derivation=entry.get("derivation"),
    )


def manifest_projection(root: Path) -> dict[str, str]:
    """input_path -> the source's declared data_origin, from the corpus
    manifest — the path-bearing record of each source_queue declaration."""
    manifest_path = root / "data" / "corpus" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    manifest = json.loads(manifest_path.read_text())
    return {
        source["input_path"]: source["data_origin"]
        for source in manifest.get("sources", [])
        if source.get("input_path") and source.get("data_origin")
    }


def collect_declarations(
    root: Path, rel_paths: list[str], projection: dict[str, str]
) -> dict[str, list[Declaration]]:
    """ALL declarations per file, from all three locations — never
    first-match, so a two-location disagreement is a visible contradiction."""
    collected: dict[str, list[Declaration]] = {}
    for rel_path in rel_paths:
        declarations = []
        in_file = _in_file_declaration(root, rel_path)
        if in_file:
            declarations.append(in_file)
        sidecar = _sidecar_declaration(root, rel_path)
        if sidecar:
            declarations.append(sidecar)
        if rel_path in projection:
            declarations.append(
                Declaration(location="queue-via-manifest", data_origin=projection[rel_path])
            )
        if declarations:
            collected[rel_path] = declarations
        for subject, declaration in _node_declarations(root, rel_path).items():
            collected.setdefault(subject, []).append(declaration)
    return collected


@dataclass(frozen=True)
class AuditFindings:
    unclassified: tuple[str, ...]
    contradictions: tuple[str, ...]
    invalid: tuple[str, ...]


def audit(
    rel_paths: list[str],
    declarations: dict[str, list[Declaration]],
    exclusions: dict[str, str],
) -> AuditFindings:
    unclassified = tuple(
        path for path in rel_paths if path not in exclusions and not declarations.get(path)
    )
    def _conflicting(found: list[Declaration]) -> bool:
        # A disagreement in ANY declared fact is a contradiction: origin,
        # author (model vs a person is the load-bearing P2.0b distinction),
        # or citation. None means "not declared here", not "disagrees".
        origins = {d.data_origin for d in found}
        authors = {d.author for d in found if d.author is not None}
        citations = {d.citation for d in found if d.citation is not None}
        return len(origins) > 1 or len(authors) > 1 or len(citations) > 1

    contradictions = tuple(
        path for path, found in sorted(declarations.items()) if _conflicting(found)
    )
    invalid = []
    for path, found in sorted(declarations.items()):
        for declaration in found:
            try:
                origin = DataOrigin(declaration.data_origin)
            except ValueError:
                invalid.append(f"{path}: unknown origin {declaration.data_origin!r}")
                continue
            if origin is DataOrigin.AUTHORED:
                try:
                    validate_author(declaration.author)
                except ValueError:
                    invalid.append(
                        f"{path}: AUTHORED with author {declaration.author!r}"
                    )
            if origin is DataOrigin.LITERATURE and not (
                declaration.citation and str(declaration.citation).strip()
            ):
                invalid.append(f"{path}: LITERATURE without a citation")
            if origin is DataOrigin.SYNTHETIC:
                # The only thing separating a seeded generator from hand-typed
                # values under a "synthetic_" filename (P2.0d-2 §0.1).
                if not (declaration.generator and str(declaration.generator).strip()):
                    invalid.append(f"{path}: SYNTHETIC without a generator import path")
                if declaration.seeds is None:
                    invalid.append(f"{path}: SYNTHETIC without a recorded seed")
            if origin is DataOrigin.DERIVED and not (
                declaration.derivation and str(declaration.derivation).strip()
            ):
                invalid.append(
                    f"{path}: DERIVED without a derivation formula or the "
                    "artifact that records it"
                )
    return AuditFindings(unclassified, contradictions, tuple(invalid))


def _contains_unrecorded_author(node: object) -> bool:
    """Recursively true if ANY nested mapping carries author: unrecorded.
    Top-level-only scanning was a hole the P2.0d-1 review probed live: a new
    file declaring `author: model` at top level could smuggle a nested entry
    with `author: unrecorded` past the frozen set — and per-entry authors are
    the blessed marker form (covariates.yaml carries eight today)."""
    if isinstance(node, dict):
        if node.get("author") == AUTHOR_UNRECORDED:
            return True
        return any(_contains_unrecorded_author(value) for value in node.values())
    if isinstance(node, list):
        return any(_contains_unrecorded_author(item) for item in node)
    return False


def _deep_unrecorded_files(root: Path, rel_paths: list[str]) -> set[str]:
    """Non-sidecar YAML/JSON files containing author: unrecorded at ANY
    depth. Sidecars are skipped here because their entries attribute to the
    files they declare (via the declarations), not to the sidecar itself."""
    found: set[str] = set()
    for rel_path in rel_paths:
        path = root / rel_path
        if path.name == SIDECAR_NAME or not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            loaded = yaml.safe_load(path.read_text())
        elif suffix in (".json", ".geojson"):
            loaded = json.loads(path.read_text())
        else:
            continue
        if _contains_unrecorded_author(loaded):
            found.add(rel_path)
    return found


def unrecorded_subjects(
    declarations: dict[str, list[Declaration]], root: Path, rel_paths: list[str],
    extras: tuple[str, ...],
) -> set[str]:
    """Every file whose machine-readable declaration says author: unrecorded —
    from the walk's declarations (which cover sidecar-attributed CSVs and .py
    DATA_AUTHOR constants), a deep scan of tracked YAML/JSON for nested
    per-entry uses, and the named extras outside the walk."""
    subjects = {
        # node subjects (path#node) collapse to their file for the frozen set
        path.split("#")[0]
        for path, found in declarations.items()
        if any(declaration.author == AUTHOR_UNRECORDED for declaration in found)
    }
    subjects |= _deep_unrecorded_files(root, rel_paths)
    subjects |= _deep_unrecorded_files(root, list(extras))
    return subjects


def dangling_sidecar_entries(root: Path, rel_paths: list[str]) -> list[str]:
    """`files:` keys in any tracked sidecar that name a non-tracked sibling —
    the sidecar analogue of a stale EXCLUSIONS entry. Without this, a sidecar
    entry for a deleted or renamed file rots silently (the MEASURED
    so268_nodules_sample entry is not in the frozen set, so nothing else
    would notice)."""
    tracked = set(rel_paths)
    dangling: list[str] = []
    for rel_path in rel_paths:
        if Path(rel_path).name != SIDECAR_NAME:
            continue
        directory = str(Path(rel_path).parent)
        entries = _load_yaml_top_level(root / rel_path).get("files") or {}
        for name in entries:
            subject = f"{directory}/{name}"
            if subject not in tracked:
                dangling.append(f"{rel_path}: entry for non-tracked {name!r}")
    return dangling


def _real_tree() -> tuple[list[str], dict[str, list[Declaration]]]:
    rel_paths = tracked_subject_files()
    return rel_paths, collect_declarations(
        REPO_ROOT, rel_paths, manifest_projection(REPO_ROOT)
    )


# ---------------------------------------------------------------------------
# The audit, on the real tree.


def test_every_tracked_file_under_data_and_tests_fixtures_is_classified_or_excluded() -> None:
    rel_paths, declarations = _real_tree()
    findings = audit(rel_paths, declarations, EXCLUSIONS)
    assert not findings.unclassified, (
        "files with no origin classification in any of the three marker "
        f"locations and no exclusion entry: {list(findings.unclassified)} — "
        "classify each in the same commit that adds it, or add an explicit "
        "exclusion with a reason."
    )


def test_no_subject_has_locations_disagreeing_on_origin_author_or_citation() -> None:
    rel_paths, declarations = _real_tree()
    findings = audit(rel_paths, declarations, EXCLUSIONS)
    assert not findings.contradictions, (
        f"cross-location contradictions: {list(findings.contradictions)} "
        "— two markers disagreeing (origin, author, or citation) is a "
        "contradiction, not a redundancy."
    )


def test_declarations_use_known_origins_and_carry_their_resolver_side_evidence() -> None:
    """The origin label must be a DataOrigin member, and four of the five
    members carry their evidence at the declaration: AUTHORED -> allow-listed
    author; LITERATURE -> citation; SYNTHETIC -> generator import path AND
    seed(s); DERIVED -> derivation formula or the artifact recording it.
    MEASURED's evidence (a proven hashed file) is the production guard's
    check on the engine side — it cannot be a resolver check because the
    proof is a re-hash of bytes, not a field."""
    rel_paths, declarations = _real_tree()
    findings = audit(rel_paths, declarations, EXCLUSIONS)
    assert not findings.invalid, list(findings.invalid)


def test_exclusions_name_tracked_files_and_never_shadow_a_classification() -> None:
    """Hygiene in both directions: a stale entry (file deleted) must be
    removed rather than rot, and an entry for a file that IS classified would
    silently mask the classification."""
    rel_paths, declarations = _real_tree()
    tracked = set(rel_paths)
    stale = [path for path in EXCLUSIONS if path not in tracked]
    assert not stale, f"exclusion entries for files git no longer tracks: {stale}"
    shadowing = [path for path in EXCLUSIONS if declarations.get(path)]
    assert not shadowing, (
        f"exclusion entries shadowing real classifications: {shadowing}"
    )


def test_files_carrying_author_unrecorded_match_the_frozen_set_exactly() -> None:
    rel_paths, declarations = _real_tree()
    detected = unrecorded_subjects(
        declarations, REPO_ROOT, rel_paths, UNRECORDED_SCAN_EXTRAS
    )
    unpermitted = sorted(detected - FROZEN_UNRECORDED)
    assert not unpermitted, (
        f"files newly carrying author: unrecorded: {unpermitted} — "
        "'unrecorded' names a frozen pre-P2.0 gap and is NOT available to new "
        "work; declare 'model' or a named person."
    )
    vanished = sorted(FROZEN_UNRECORDED - detected)
    assert not vanished, (
        f"frozen-set entries no longer detected: {vanished} — if an author was "
        "recorded (good), shrink FROZEN_UNRECORDED in the same commit."
    )


# ---------------------------------------------------------------------------
# Negation fixtures: the audit run on deliberately dirty tmp trees. These are
# what make the mandatory tautology mutation observable — an audit that has
# only ever seen a clean tree is not known to detect a dirty one.


def _write(root: Path, rel_path: str, text: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_audit_reports_an_unclassified_file_by_name(tmp_path: Path) -> None:
    """*** THE SOLE OBSERVER OF THE AUDIT'S OWN BLINDNESS — DO NOT DELETE OR
    WEAKEN WITHOUT A REPLACEMENT. *** The mandatory d-1 mutation (audit()
    collecting its subjects from the resolver) left EVERY real-tree test
    green — a clean tree cannot distinguish a working audit from a
    structurally blind one — and THIS test was the only failure:
    `AssertionError: assert () == ('orphan.csv',)`. Re-verified against the
    final module structure with the same result. Delete this fixture and the
    entire audit can be made decorative while the suite stays green."""
    _write(tmp_path, "good.yaml", "data_origin: AUTHORED\nauthor: model\n")
    _write(tmp_path, "orphan.csv", "a,b\n1,2\n")
    rel_paths = ["good.yaml", "orphan.csv"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert findings.unclassified == ("orphan.csv",)


def test_audit_reports_a_cross_location_origin_contradiction(tmp_path: Path) -> None:
    _write(tmp_path, "both.yaml", "data_origin: AUTHORED\nauthor: model\n")
    _write(
        tmp_path,
        SIDECAR_NAME,
        "files:\n  both.yaml:\n    data_origin: MEASURED\n",
    )
    rel_paths = ["both.yaml"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert findings.contradictions == ("both.yaml",)


def test_audit_reports_an_unknown_origin_label_and_a_missing_author(tmp_path: Path) -> None:
    _write(tmp_path, "bogus.yaml", "data_origin: FABRICATED\n")
    _write(tmp_path, "authorless.yaml", "data_origin: AUTHORED\n")
    rel_paths = ["bogus.yaml", "authorless.yaml"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert any("FABRICATED" in item for item in findings.invalid)
    assert any("authorless.yaml" in item for item in findings.invalid)


def test_audit_reports_synthetic_declarations_missing_generator_or_seed(tmp_path: Path) -> None:
    """SYNTHETIC's evidence bar, both halves independently: no generator at
    all, and a generator with no seed. This is the check separating a seeded
    generator from hand-typed values under a synthetic_* filename."""
    _write(tmp_path, "bare.yaml", "data_origin: SYNTHETIC\n")
    _write(tmp_path, "seedless.yaml", "data_origin: SYNTHETIC\ngenerator: pkg.gen\n")
    _write(tmp_path, "proper.yaml", "data_origin: SYNTHETIC\ngenerator: pkg.gen\nseed: 7\n")
    rel_paths = ["bare.yaml", "seedless.yaml", "proper.yaml"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert "bare.yaml: SYNTHETIC without a generator import path" in findings.invalid
    assert "bare.yaml: SYNTHETIC without a recorded seed" in findings.invalid
    assert "seedless.yaml: SYNTHETIC without a recorded seed" in findings.invalid
    assert not any("proper.yaml" in item for item in findings.invalid)


def test_audit_reports_derived_declarations_missing_their_derivation(tmp_path: Path) -> None:
    _write(tmp_path, "underived.yaml", "data_origin: DERIVED\n")
    _write(tmp_path, "complete.yaml", "data_origin: DERIVED\nderivation: 'x = y / z'\n")
    rel_paths = ["underived.yaml", "complete.yaml"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert any("underived.yaml: DERIVED without" in item for item in findings.invalid)
    assert not any("complete.yaml" in item for item in findings.invalid)


def test_unrecorded_scan_reports_an_unpermitted_file_by_name(tmp_path: Path) -> None:
    _write(tmp_path, "sneaky.yaml", "data_origin: AUTHORED\nauthor: unrecorded\n")
    rel_paths = ["sneaky.yaml"]
    declarations = collect_declarations(tmp_path, rel_paths, {})
    detected = unrecorded_subjects(declarations, tmp_path, rel_paths, ())
    unpermitted = sorted(detected - FROZEN_UNRECORDED)
    assert unpermitted == ["sneaky.yaml"]


def test_unrecorded_scan_detects_a_nested_per_entry_use(tmp_path: Path) -> None:
    """The P2.0d-1 review's live probe, kept as a fixture: a clean top-level
    author hiding a nested entry-level `author: unrecorded` — the shape a new
    file copying covariates.yaml's per-entry form would take."""
    _write(
        tmp_path,
        "nested.yaml",
        "data_origin: AUTHORED\nauthor: model\n"
        "entries:\n  - name: x\n    author: unrecorded\n",
    )
    rel_paths = ["nested.yaml"]
    declarations = collect_declarations(tmp_path, rel_paths, {})
    detected = unrecorded_subjects(declarations, tmp_path, rel_paths, ())
    assert detected == {"nested.yaml"}


def test_audit_reports_an_author_disagreement_across_locations(tmp_path: Path) -> None:
    """Same origin, different authors — 'model' vs a person is the
    load-bearing P2.0b distinction, so locations disagreeing on it is a
    contradiction, not a redundancy."""
    _write(tmp_path, "who.yaml", "data_origin: AUTHORED\nauthor: karl\n")
    _write(
        tmp_path,
        SIDECAR_NAME,
        "files:\n  who.yaml:\n    data_origin: AUTHORED\n    author: isaac\n",
    )
    rel_paths = ["who.yaml"]
    findings = audit(rel_paths, collect_declarations(tmp_path, rel_paths, {}), {})
    assert findings.contradictions == ("who.yaml",)


def test_sidecar_entries_name_only_tracked_files(tmp_path: Path) -> None:
    """Both halves: the real tree has no dangling sidecar entries, and a
    dangling entry IS detected (the negation, on a tmp tree)."""
    rel_paths, _ = _real_tree()
    assert dangling_sidecar_entries(REPO_ROOT, rel_paths) == []

    _write(tmp_path, SIDECAR_NAME, "files:\n  ghost.csv:\n    data_origin: AUTHORED\n")
    dangling = dangling_sidecar_entries(tmp_path, [SIDECAR_NAME])
    assert dangling == [f"{SIDECAR_NAME}: entry for non-tracked 'ghost.csv'"]


def test_the_screening_node_declaration_is_resolved_and_carries_its_citation() -> None:
    """Marker form 2's one instance: normalization.yaml's screening block
    must resolve as its own subject with the TS-6 Table 2 citation — deleting
    screening_citation or corrupting screening_data_origin must fail the
    evidence test, not pass silently."""
    _, declarations = _real_tree()
    subject = "data/config/normalization.yaml#screening"
    assert subject in declarations
    (declaration,) = declarations[subject]
    assert declaration.data_origin == "LITERATURE"
    assert "Table 2" in (declaration.citation or "")


def test_the_readme_row_declaration_for_study_area_is_pinned() -> None:
    """study_area.geojson's declaration lives in prose (the contracts README
    contract-2 row) because the file is hash-pinned — so the prose is pinned
    here, or it could drift or vanish with the suite green."""
    readme = (REPO_ROOT / "docs" / "contracts" / "README.md").read_text()
    assert "study_area.geojson — data_origin: AUTHORED" in readme
    assert "author: unrecorded (it also self-marks" in readme


def test_unrecorded_scan_extras_carry_valid_declarations() -> None:
    """The two docs/contracts extras sit outside the walk, so audit() never
    validates them — do it here: known origin label, and AUTHORED carries an
    allow-listed author."""
    for rel_path in UNRECORDED_SCAN_EXTRAS:
        declaration = _in_file_declaration(REPO_ROOT, rel_path)
        assert declaration is not None, rel_path
        origin = DataOrigin(declaration.data_origin)
        if origin is DataOrigin.AUTHORED:
            validate_author(declaration.author)


def test_the_real_manifest_projection_classifies_both_tab_files() -> None:
    """The queue-via-manifest resolver is load-bearing for exactly two files;
    pin them so a manifest rename or field change fails here, not as a
    mysterious unclassified-.tab failure."""
    projection = manifest_projection(REPO_ROOT)
    assert projection == {
        "data/sources/SO268-bc-nodules-summary-PANGAEA-904967.tab": "MEASURED",
        "data/sources/SO268-bc-nodules-PANGAEA-904962.tab": "MEASURED",
    }


def test_git_enumeration_is_independent_of_the_resolver() -> None:
    """The anti-tautology structure, asserted: the subject list includes files
    the resolver can NOT classify (the excluded ones) — proof the walk does
    not derive from the resolver's successes."""
    rel_paths, declarations = _real_tree()
    subjects_without_declarations = [p for p in rel_paths if not declarations.get(p)]
    assert subjects_without_declarations, (
        "every tracked file resolved a declaration — either the tree has no "
        "excluded files left (update EXCLUSIONS) or the walk is enumerating "
        "from the resolver."
    )
    assert set(subjects_without_declarations) <= set(EXCLUSIONS)
