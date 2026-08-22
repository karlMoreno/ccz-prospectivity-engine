"""CorpusManifest — the ingestion-stage provenance artifact
(`data/corpus/manifest.json`), one of the three artifacts defined in
docs/contracts/PROVENANCE.md. Extends ProvenanceArtifact (Layer Supertype).

What the CSV cannot tell you, and this does:

- **Which sources contributed.** `[05]` supplies `mean_nodule_mass_g` for all
  36 events yet appears in no corpus row, because dedup absorbed it into
  `[01]`. `contributing_sources` answers 2, not 1.
- **How many rows can actually train.** `training_eligible_count` (35) is a
  different number from rows admitted (108), and the gap is explained in the
  same object by the qa_status breakdown. This is the single most
  decision-relevant number in the project; it should never again require an
  investigation to learn.
- **Whether the licenses permit what you are about to do.**
  `any_non_commercial_input` is one field lookup, not a survey of 13 source
  entries.
"""

from __future__ import annotations

from typing import ClassVar

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from engine.prospectivity.domain.evidence import QAStatus
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.provenance import geometry
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.contract_versions import contract_versions, file_sha256
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.provenance.recorder import ProvenanceRecorder, SourceRecord

REPO_ROOT = find_repo_root(Path(__file__).resolve())
STUDY_AREA_PATH = REPO_ROOT / "data" / "aoi" / "study_area.geojson"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "data" / "corpus" / "manifest.json"

# Licenses that forbid commercial reuse. A constraint on one input propagates
# to every product derived from the corpus, so it is recorded at corpus level
# as well as per source.
_NON_COMMERCIAL_MARKERS = ("-NC-", "NONCOMMERCIAL", "NON-COMMERCIAL")


def _is_non_commercial(license_text: str | None) -> bool:
    if not license_text:
        return False
    upper = license_text.upper()
    return any(marker in upper for marker in _NON_COMMERCIAL_MARKERS)


class SourceProvenance(BaseModel):
    """One source's contribution: queue metadata + pipeline events + final
    corpus attribution.

    THE RECONCILIATION IDENTITY, and why it is stated the way it is:

        adapted_records == admitted_rows + absorbed_rows + rejected_rows

    - it is anchored on ADAPTED, not FETCHED, because one raw row fans out
      into one record per evidence class it carries ([01]: 36 rows -> 108
      records) and [05] AGGREGATES nodules up to events (1,658 rows -> 72
      records). `fetched_rows` is recorded alongside so that expansion or
      reduction is visible instead of looking like rows went missing.
    - `admitted_rows` counts rows in the FINISHED corpus carrying this
      source_id, not rows this source's pipeline appended. Those differ: the
      dedup merge can overwrite a corpus slot in place with a higher-quality
      row from a later source (D1/D4), so append-order attribution flips with
      adapter order while the finished corpus does not. Deriving it from the
      corpus is what makes this artifact order-independent.
    - `absorbed_rows` is therefore "adapted, but not in the finished corpus
      under its own source_id" — the [05] case.
    - `flagged_admitted_rows` is a SUBSET of admitted (a quality mark on rows
      that ARE in the corpus), never a fourth disposition.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str | None = None
    doi: str | None = None
    url: str | None = None
    license: str | None = None
    is_non_commercial: bool = False
    is_open: bool | None = None
    input_path: str | None = None
    input_content_hash: str | None = None
    # "real_data" = PROVEN (declared MEASURED, recorded hash matches bytes) |
    # "fixture" = unproven — since P2.0d-2 this includes a pending-evidence
    # MEASURED claim, not only literal test fixtures | "unknown" = no input
    # path. Default "unknown": on direct construction nothing is proven.
    backed_by: str = "unknown"
    # The source's DECLARED origin, read from its source_queue.yaml entry
    # (P2.0c) — never inferred. None only on direct construction; the build
    # path raises if a recorded source lacks a declaration.
    data_origin: str | None = None

    fetched_rows: int = 0
    adapted_records: int = 0
    normalized_records: int = 0
    admitted_rows: int = 0
    absorbed_rows: int = 0
    rejected_rows: int = 0
    flagged_admitted_rows: int = 0
    admitted_by_evidence_class: dict[str, int] = Field(default_factory=dict)
    absorbed_by_evidence_class: dict[str, int] = Field(default_factory=dict)
    fully_absorbed: bool = False
    reconciles: bool = True
    reconciliation_identity: str = (
        "adapted_records == admitted_rows + absorbed_rows + rejected_rows "
        "(admitted counted from the finished corpus, not from append order)"
    )

    def check_reconciles(self) -> bool:
        return self.adapted_records == (
            self.admitted_rows + self.absorbed_rows + self.rejected_rows
        )


class CorpusManifest(ProvenanceArtifact):
    """Ingestion-stage provenance for one corpus build."""

    # HASH.1: the field set frozen at 2026-08-22 — what data/corpus/manifest.json
    # (a LEGACY artifact, no schema_version) is hashed over. A SNAPSHOT: do not
    # regenerate it from model_fields, or the committed hash moves.
    SCHEMA_VERSION: ClassVar[int] = 1
    LEGACY_HASHED_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "admitted_rows_by_data_origin", "any_non_commercial_input", "bounding_box_all_rows",
        "bounding_box_training_eligible", "contract_versions", "contributing_sources",
        "corpus_path", "corpus_row_count", "rows_by_evidence_class", "rows_by_qa_status",
        "sources", "sources_absorbed_entirely", "spatial_summary_all_rows",
        "spatial_summary_training_eligible", "study_area_containment",
        "training_eligible_count", "upstream_hashes",
    })

    corpus_path: str
    corpus_row_count: int = 0
    rows_by_evidence_class: dict[str, int] = Field(default_factory=dict)
    rows_by_qa_status: dict[str, int] = Field(default_factory=dict)
    # P2.0c: the corpus's composition by DECLARED source origin — computed
    # from each contributing source's source_queue.yaml declaration, never
    # hand-written. A reviewer opening this file sees what the corpus is made
    # of without reading code.
    admitted_rows_by_data_origin: dict[str, int] = Field(default_factory=dict)
    # Deliberately separate from corpus_row_count: 108 admitted, 35 trainable.
    training_eligible_count: int = 0
    contributing_sources: list[str] = Field(default_factory=list)
    sources_absorbed_entirely: list[str] = Field(default_factory=list)
    any_non_commercial_input: bool = False
    sources: list[SourceProvenance] = Field(default_factory=list)
    bounding_box_all_rows: dict[str, float] | None = None
    bounding_box_training_eligible: dict[str, float] | None = None
    study_area_containment: dict = Field(default_factory=dict)
    # Two summaries, same shape, mirroring the bounding_box_* pair above. The
    # TRAINING-ELIGIBLE one is the decision-relevant block: "can a variogram be
    # estimated" is a question about the stations that can actually train, so
    # its pair count must exclude the flagged failed box core. The all-rows
    # block is kept so the effect of that exclusion is visible rather than
    # having to be taken on trust.
    spatial_summary_training_eligible: dict = Field(default_factory=dict)
    spatial_summary_all_rows: dict = Field(default_factory=dict)


def source_queue_entries() -> dict[str, dict]:
    """Contract 5's entries by source_id, re-parsed on every call (no cache:
    correctness over speed — a stale queue behind the guard would be worse
    than three ~20 KB parses per build). Public since P2.0d-2: the production
    guard in corpus_builder shares it."""
    import yaml

    queue_path = REPO_ROOT / "data" / "sources" / "source_queue.yaml"
    queue = yaml.safe_load(queue_path.read_text())
    return {entry["source_id"]: entry for entry in queue["sources"]}


_SHA256_HEX_LENGTH = 64


def measured_evidence_failure(entry: dict, path: Path) -> str | None:
    """P2.0d-2, the declaration-plus-evidence rule in one place. Returns None
    when the source is PROVEN, else a sentence naming the failing condition.

    A declaration is a CLAIM; a hash over real bytes is the PROOF. Admissible
    means: declared MEASURED, AND the entry records a real 64-hex SHA-256
    (not null, not a placeholder), AND the declared input file exists, AND
    re-hashing those bytes reproduces the recorded hash. A MEASURED
    declaration with pending evidence is refused — the honest reading of the
    [06] incident: those fixtures were not mislabelled, they were unproven.
    Conditions are checked in that order and the FIRST failure is named, so a
    refusal never sends a reader hunting.

    Shared by the production guard (corpus_builder raises on it) and by
    `_backed_by` (the manifest records its outcome) — one rule, one owner,
    replacing P2.0c's interim path-shape predicates.
    """
    declared = entry.get("data_origin")
    if declared != DataOrigin.MEASURED.value:
        return (
            f"declares data_origin={declared!r}, not MEASURED — only proven "
            "MEASURED sources are admissible on a production path"
        )
    recorded = entry.get("content_hash")
    if recorded is None:
        return (
            "declares MEASURED but records content_hash: null — the evidence "
            "is pending, and an unproven claim is refused (fill the hash from "
            "the downloaded bytes)"
        )
    hex_part = str(recorded).removeprefix("sha256:")
    if len(hex_part) != _SHA256_HEX_LENGTH or not all(
        character in "0123456789abcdef" for character in hex_part.lower()
    ):
        return (
            f"records content_hash {recorded!r}, which is not a real 64-hex "
            "SHA-256 — a placeholder is not evidence"
        )
    if not Path(path).is_file():
        return f"declares MEASURED but the declared input file does not exist: {path}"
    actual = file_sha256(path)
    if actual != f"sha256:{hex_part.lower()}":
        return (
            f"recorded content_hash {recorded!r} does not match the bytes on "
            f"disk ({actual}) — the file is not the recorded artifact"
        )
    return None


def _declared_data_origin(entry: dict, source_id: str) -> str:
    """The source's declared origin from its source_queue.yaml entry (P2.0c).

    Raises rather than defaulting: a recorded source with no declaration (or
    an unknown label) would otherwise flow into the composition counts as a
    silent unknown — the failure mode the origin module exists to prevent.
    """
    declared = entry.get("data_origin")
    if declared is None:
        raise ValueError(
            f"source {source_id!r} contributed to this corpus build but its "
            "source_queue.yaml entry declares no data_origin — declare it "
            "there (P2.0c) rather than letting the manifest guess."
        )
    try:
        return DataOrigin(declared).value
    except ValueError as error:
        raise ValueError(
            f"source {source_id!r} declares data_origin={declared!r}, which is "
            "not a DataOrigin — fix its source_queue.yaml entry."
        ) from error


def _admitted_rows_by_origin(sources: list[SourceProvenance]) -> dict[str, int]:
    """Composition by DECLARED origin, computed from the per-source records —
    never hand-written (P2.0c). A source with admitted rows but no declared
    origin raises: on the build path `_declared_data_origin` makes that
    unreachable, and this guard keeps a directly-constructed manifest from
    summing rows into no bucket silently."""
    counts: dict[str, int] = {}
    for source in sources:
        if not source.admitted_rows:
            continue
        if source.data_origin is None:
            raise ValueError(
                f"source {source.source_id!r} has {source.admitted_rows} admitted "
                "rows but no data_origin — its rows would vanish from the "
                "composition counts."
            )
        counts[source.data_origin] = counts.get(source.data_origin, 0) + source.admitted_rows
    return dict(sorted(counts.items()))


def _adapter_input_paths(adapters: list) -> dict[str, Path]:
    """Real input file per source, for hashing. Adapters keep their path
    privately (they only expose `fetch()`), so this reads the one attribute
    they all set — no adapter API change for the sake of reporting."""
    paths: dict[str, Path] = {}
    for adapter in adapters:
        path = getattr(adapter, "input_path", None)
        if path is not None:
            paths[adapter.source_id] = Path(path)
    return paths


def build_corpus_manifest(
    corpus: list[Observation],
    recorder: ProvenanceRecorder,
    adapters: list,
    corpus_path: Path,
) -> CorpusManifest:
    """Assemble the manifest from the built corpus + what the recorder saw.

    Note the two independent viewpoints, deliberately not collapsed: corpus
    totals are counted from the CORPUS (what a reader of the CSV would see),
    while per-source dispositions come from the RECORDER (what happened during
    the build). Where they disagree — as they do for `[05]`, present in the
    recorder and absent from the corpus — that disagreement is the finding.
    """
    queue = source_queue_entries()
    input_paths = _adapter_input_paths(adapters)

    rows_by_evidence_class: dict[str, int] = {}
    rows_by_qa_status: dict[str, int] = {}
    for observation in corpus:
        evidence_class = observation.evidence_class.value
        qa_status = QAStatus(observation.qa_status).value
        rows_by_evidence_class[evidence_class] = rows_by_evidence_class.get(evidence_class, 0) + 1
        rows_by_qa_status[qa_status] = rows_by_qa_status.get(qa_status, 0) + 1

    training_eligible = [obs for obs in corpus if obs.is_training_eligible()]

    # The ~20 lines of attribution INFERENCE that used to sit here are gone
    # (C2, 2026-07-30). They counted the finished corpus and subtracted to
    # recover admitted/absorbed, because the event stream could not be trusted
    # — and an earlier version of that inference, based on append order, was
    # the manifest attribution bug. The recorder now observes each `Resolution`
    # as it is decided, including which source a `Replace` displaced, so these
    # are read directly. `test_corpus_row_count_equals_total_admitted_across_sources`
    # is the cross-check that they still agree with the corpus.
    #
    # qa_status remains a property of the FINISHED row rather than a
    # disposition — a row's verdict can be escalated by a later merge — so it
    # is still counted from the corpus. That is a direct count, not an
    # inference.
    flagged_by_source: dict[str, int] = {}
    for observation in corpus:
        if observation.qa_status in (QAStatus.FLAGGED, QAStatus.FAIL):
            flagged_by_source[observation.source_id] = (
                flagged_by_source.get(observation.source_id, 0) + 1
            )

    sources: list[SourceProvenance] = []
    for record in recorder.sources():
        entry = queue.get(record.source_id, {})
        admitted_rows = record.admitted_rows
        absorbed_rows = record.absorbed_rows
        admitted_by_class = dict(sorted(record.admitted_by_evidence_class.items()))
        absorbed_by_class = dict(sorted(record.absorbed_by_evidence_class.items()))
        input_path = input_paths.get(record.source_id)
        license_text = entry.get("license")
        sources.append(
            SourceProvenance(
                source_id=record.source_id,
                title=entry.get("title"),
                doi=entry.get("doi"),
                url=entry.get("url"),
                license=license_text,
                is_non_commercial=_is_non_commercial(license_text),
                is_open=entry.get("is_open"),
                input_path=str(input_path.relative_to(REPO_ROOT)) if input_path else None,
                input_content_hash=file_sha256(input_path) if input_path else None,
                backed_by=_backed_by(entry, input_path),
                data_origin=_declared_data_origin(entry, record.source_id),
                fetched_rows=record.fetched_rows,
                adapted_records=record.adapted_records,
                normalized_records=record.normalized_records,
                admitted_rows=admitted_rows,
                absorbed_rows=absorbed_rows,
                rejected_rows=record.rejected_rows,
                flagged_admitted_rows=flagged_by_source.get(record.source_id, 0),
                admitted_by_evidence_class=admitted_by_class,
                absorbed_by_evidence_class=absorbed_by_class,
                fully_absorbed=admitted_rows == 0 and absorbed_rows > 0,
            )
        )
        sources[-1].reconciles = sources[-1].check_reconciles()

    # Sorted by source_id, not left in adapter-run order: the corpus itself is
    # order-independent (P2 proved the CSV is byte-identical either way), so an
    # identical corpus must yield an identical manifest content_hash — a
    # downstream artifact quoting it in `upstream_hashes` cannot have that
    # reference flip because someone reordered a build list.
    sources.sort(key=lambda source: source.source_id)

    manifest = CorpusManifest(
        corpus_path=str(corpus_path.relative_to(REPO_ROOT)),
        corpus_row_count=len(corpus),
        rows_by_evidence_class=dict(sorted(rows_by_evidence_class.items())),
        rows_by_qa_status=dict(sorted(rows_by_qa_status.items())),
        admitted_rows_by_data_origin=_admitted_rows_by_origin(sources),
        training_eligible_count=len(training_eligible),
        # EVERY observed source, including fully-absorbed ones — the whole
        # point of this artifact.
        contributing_sources=sorted(record.source_id for record in recorder.sources()),
        sources_absorbed_entirely=sorted(
            source.source_id for source in sources if source.fully_absorbed
        ),
        any_non_commercial_input=any(source.is_non_commercial for source in sources),
        sources=sources,
        contract_versions=contract_versions(),
        # Ingestion is the first stage: nothing upstream of the raw downloads,
        # whose hashes are recorded per source above.
        upstream_hashes={},
        bounding_box_all_rows=geometry.bounding_box(corpus),
        bounding_box_training_eligible=geometry.bounding_box(training_eligible),
        study_area_containment=geometry.count_outside_study_area(corpus, STUDY_AREA_PATH),
        spatial_summary_training_eligible=geometry.spatial_summary(
            training_eligible, basis="training_eligible_rows"
        ),
        spatial_summary_all_rows=geometry.spatial_summary(corpus, basis="all_corpus_rows"),
    )
    return manifest.finalize()


def _backed_by(entry: dict, input_path: Path | None) -> str:
    """Whether this source's input is PROVEN real data. P2.0d-2: derived from
    the declaration-plus-evidence rule (`measured_evidence_failure`), never
    from path shape — the P2.0c interim widening is removed, and this is the
    replacement that owns the rule. corpus_builder REFUSES unproven inputs in
    production; recording the same check's outcome here means a reader can
    verify that rather than trust it.

    Domain unchanged: "real_data" (proven MEASURED — declared, hash recorded,
    bytes match), "fixture" (anything unproven), "unknown" (no input path)."""
    if input_path is None:
        return "unknown"
    return "fixture" if measured_evidence_failure(entry, input_path) else "real_data"


def write_corpus_manifest(
    manifest: CorpusManifest, output_path: Path = DEFAULT_MANIFEST_PATH
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.to_json())
