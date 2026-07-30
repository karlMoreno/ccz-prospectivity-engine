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

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from engine.prospectivity.domain.evidence import QAStatus
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.provenance import geometry
from engine.prospectivity.provenance.artifact import ProvenanceArtifact
from engine.prospectivity.provenance.contract_versions import contract_versions, file_sha256
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
    backed_by: str = "real_data"  # "real_data" | "fixture" | "unknown"

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

    corpus_path: str
    corpus_row_count: int = 0
    rows_by_evidence_class: dict[str, int] = Field(default_factory=dict)
    rows_by_qa_status: dict[str, int] = Field(default_factory=dict)
    # Deliberately separate from corpus_row_count: 108 admitted, 35 trainable.
    training_eligible_count: int = 0
    contributing_sources: list[str] = Field(default_factory=list)
    sources_absorbed_entirely: list[str] = Field(default_factory=list)
    any_non_commercial_input: bool = False
    sources: list[SourceProvenance] = Field(default_factory=list)
    bounding_box_all_rows: dict[str, float] | None = None
    bounding_box_training_eligible: dict[str, float] | None = None
    study_area_containment: dict = Field(default_factory=dict)
    spatial_summary: dict = Field(default_factory=dict)


def _source_queue_entries() -> dict[str, dict]:
    import yaml

    queue_path = REPO_ROOT / "data" / "sources" / "source_queue.yaml"
    queue = yaml.safe_load(queue_path.read_text())
    return {entry["source_id"]: entry for entry in queue["sources"]}


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
    queue = _source_queue_entries()
    input_paths = _adapter_input_paths(adapters)

    rows_by_evidence_class: dict[str, int] = {}
    rows_by_qa_status: dict[str, int] = {}
    for observation in corpus:
        evidence_class = observation.evidence_class.value
        qa_status = QAStatus(observation.qa_status).value
        rows_by_evidence_class[evidence_class] = rows_by_evidence_class.get(evidence_class, 0) + 1
        rows_by_qa_status[qa_status] = rows_by_qa_status.get(qa_status, 0) + 1

    training_eligible = [obs for obs in corpus if obs.is_training_eligible()]

    # Final attribution, counted from the FINISHED corpus so it cannot depend
    # on adapter run order (see SourceProvenance's docstring).
    in_corpus_by_source: dict[str, int] = {}
    in_corpus_by_source_class: dict[str, dict[str, int]] = {}
    flagged_by_source: dict[str, int] = {}
    for observation in corpus:
        source_id = observation.source_id
        evidence_class = observation.evidence_class.value
        in_corpus_by_source[source_id] = in_corpus_by_source.get(source_id, 0) + 1
        per_class = in_corpus_by_source_class.setdefault(source_id, {})
        per_class[evidence_class] = per_class.get(evidence_class, 0) + 1
        if observation.qa_status in (QAStatus.FLAGGED, QAStatus.FAIL):
            flagged_by_source[source_id] = flagged_by_source.get(source_id, 0) + 1

    sources: list[SourceProvenance] = []
    for record in recorder.sources():
        entry = queue.get(record.source_id, {})
        admitted_rows = in_corpus_by_source.get(record.source_id, 0)
        admitted_by_class = dict(sorted(in_corpus_by_source_class.get(record.source_id, {}).items()))
        absorbed_rows = record.adapted_records - admitted_rows - record.rejected_rows
        absorbed_by_class = {
            evidence_class: adapted_count - admitted_by_class.get(evidence_class, 0)
            for evidence_class, adapted_count in sorted(
                record.adapted_by_evidence_class.items()
            )
            if adapted_count - admitted_by_class.get(evidence_class, 0) > 0
        }
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
                backed_by=_backed_by(input_path),
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
        spatial_summary=geometry.spatial_summary(corpus),
    )
    return manifest.finalize()


def _backed_by(input_path: Path | None) -> str:
    """Whether this source read real data or a fixture. corpus_builder already
    REFUSES fixture paths in production (`_require_production_path`); recording
    it here means a reader can verify that rather than trust it."""
    if input_path is None:
        return "unknown"
    parts = {part.lower() for part in input_path.parts}
    return "fixture" if {"tests", "fixtures"} <= parts else "real_data"


def write_corpus_manifest(
    manifest: CorpusManifest, output_path: Path = DEFAULT_MANIFEST_PATH
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.to_json())
