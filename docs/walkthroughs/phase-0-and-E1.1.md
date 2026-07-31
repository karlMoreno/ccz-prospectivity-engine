# Phase 0 + Phase 1 E1.1 — Checkpoint Walkthrough

**Audience:** you, the engineer of record. You know Python; you have not read this
codebase yet. This document is the hand-check — read it top to bottom, or use it as a
reference while you read the code yourself.

**Scope:** everything built so far — Phase 0 (E0.1–E0.5, the scaffold) and Phase 1
task E1.1 (real `SourceAdapter` subclasses). Nothing past E1.1 exists yet.

**Verified against disk:** every file reference, signature, and test name below was
read fresh off disk while writing this document, not recalled from memory. Test count
(44) was confirmed with `pytest --collect-only`.

---

## 1. Reading order

Read top to bottom. Each stage assumes you've read the ones above it.

### Stage A — Ground truth (read before any code)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 1 | `docs/contracts/master_observations.schema.json` | `[REFERENCE ONLY]` | Contract 1 — the schema every `Observation` in the codebase must satisfy. You've already read this with me once; re-skim if it's been a while. |
| 2 | `data/sources/source_queue.yaml` | `[REFERENCE ONLY]` | Contract 5 — the 13 Phase-A sources, their evidence classes, licenses, and derivation notes. E1.1's three adapters are configured straight from this file's field names. |
| 3 | `data/config/normalization.yaml` | `[REFERENCE ONLY]` | Contract 7 — the per-evidence-class math rules. Nothing in the code implements this yet (that's E1.2) but you'll want it open while reading `normalizer.py`. |

### Stage B — Domain vocabulary (the nouns)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 4 | `engine/prospectivity/domain/evidence.py` | `[READ CLOSELY]` | Defines `EvidenceClass` and five supporting enums — the vocabulary everything downstream speaks in. |
| 5 | `engine/prospectivity/domain/observation.py` | `[READ CLOSELY]` | The `Observation` Pydantic model — one row of the corpus, and the single place the scientific-integrity rules are enforced as code. **The most important file in the repo.** |
| 6 | `engine/prospectivity/domain/study_area.py` | `[SKIM]` | `StudyArea` / `ExclusionZone` — thin wrappers around GeoJSON geometry dicts. |
| 7 | `engine/prospectivity/domain/terrain.py` | `[SKIM]` | `TerrainLayer` — metadata + a path to a raster, not the raster itself. |
| 8 | `engine/prospectivity/domain/ts6.py` | `[SKIM]` | `TS6Surface` — mirrors `ts6_reference.yaml`; note the `role_note` field. |
| 9 | `engine/prospectivity/domain/results.py` | `[SKIM]` | The six result types (`PredictionSurface`, `UncertaintySurface`, `CVScore`, `TS6Agreement`, `EconomicScenarioResult`, `RunManifest`) — empty shapes, no logic. |
| 10 | `engine/prospectivity/domain/__init__.py` | `[REFERENCE ONLY]` | Just re-exports everything above. |

### Stage C — Interfaces (the empty-but-frozen seams)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 11 | `engine/prospectivity/terrain/source.py` | `[SKIM]` | `TerrainSource` ABC — one abstract method, `load()`. |
| 12 | `engine/prospectivity/samples/source.py` | `[READ CLOSELY]` | `SampleSource` ABC — has the one piece of *real* logic in the interface layer: the frozen MASS-only training filter. |
| 13 | `engine/prospectivity/estimators/base.py` | `[SKIM]` | `Estimator` ABC — note `predict()` returns `(mean, std)`, never a bare value. |
| 14 | `engine/prospectivity/economics/model.py` | `[SKIM]` | `EconomicModel` ABC — one method, `apply()`. |
| 15 | `engine/prospectivity/ts6/reference.py` | `[SKIM]` | `TS6Reference` ABC + the standalone `compare_to_ts6()` function (currently `raise NotImplementedError`). |
| 16 | `engine/prospectivity/engine.py` | `[READ CLOSELY]` | `ProspectivityEngine` — the top-level Template Method tying all the above together. |

### Stage D — Ingestion machinery (the seams E1.1 actually uses)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 17 | `engine/prospectivity/ingestion/source_adapter.py` | `[READ CLOSELY]` | `SourceAdapter` ABC + `RawRecord` type — the ADAPTER contract every real adapter implements. |
| 18 | `engine/prospectivity/ingestion/normalizer.py` | `[READ CLOSELY]` | `AbundanceNormalizer` ABC — still 100% unimplemented in production; read it to know what E1.2 will fill in. |
| 19 | `engine/prospectivity/ingestion/specification.py` | `[READ CLOSELY]` | `Specification` ABC + the `&`/`|`/`~` combinators — SPECIFICATION pattern, no concrete dedup rule yet (E1.3). |
| 20 | `engine/prospectivity/ingestion/pipeline.py` | `[READ CLOSELY]` | `IngestionPipeline` — the Template Method that runs one adapter through fetch→adapt→normalize→validate→dedup→append. |
| 21 | `engine/prospectivity/ingestion/_column_mapping.py` | `[READ CLOSELY]` | `EvidenceClassMapping` + `build_records()` — the shared fan-out logic all three real adapters call. |
| 22 | `engine/prospectivity/ingestion/__init__.py` | `[REFERENCE ONLY]` | Re-exports everything in this package. |

### Stage E — Real adapters (E1.1, this checkpoint's actual deliverable)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 23 | `engine/prospectivity/ingestion/pangaea_adapter.py` | `[READ CLOSELY]` | `PangaeaAdapter` — real, for the 6 PANGAEA DOIs (`[01]`–`[05]`, `[12]`). |
| 24 | `engine/prospectivity/ingestion/tabular_file_adapter.py` | `[READ CLOSELY]` | `TabularFileAdapter` — real, for Dryad/Mendeley xlsx/csv (`[06]`, `[14]`). |
| 25 | `engine/prospectivity/ingestion/regional_grid_adapter.py` | `[READ CLOSELY]` | `RegionalGridAdapter` — real, for the two GRID sources (`[18]`, `[19]`). |

### Stage F — Reserved / stub packages (confirm they're still empty)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 26 | `engine/prospectivity/features/__init__.py` | `[REFERENCE ONLY]` | Docstring only. Reserved for E1.4. |
| 27 | `engine/prospectivity/validation/__init__.py` | `[REFERENCE ONLY]` | Docstring only. Reserved for Phase 2. |
| 28 | `engine/prospectivity/uncertainty/__init__.py` | `[REFERENCE ONLY]` | Docstring only. Reserved for Phase 2-3. |
| 29 | `engine/prospectivity/provenance/__init__.py` | `[REFERENCE ONLY]` | Docstring only. Reserved for Phase 3 (richer than `RunManifest`). |

### Stage G — Test fixtures (the test-only stand-ins — compare these against Stage D/E)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 30 | `tests/fixtures/adapters.py` | `[SKIM]` | `FixtureBoxcoreAdapter` / `FixtureCoverAdapter` / `FixtureGridAdapter` — Phase 0's fake adapters. Worth comparing against the real ones in Stage E: same shape, hand-rolled instead of configured. |
| 31 | `tests/fixtures/normalizers.py` | `[SKIM]` | `FixtureMassNormalizer` etc. — stand-ins for E1.2's real normalizers. Read the math; it's close to what `normalization.yaml` actually specifies. |
| 32 | `tests/fixtures/sample_source.py` | `[REFERENCE ONLY]` | `FixtureSampleSource` — 6 lines, wraps a list. |
| 33 | `tests/fixtures/rasters.py` | `[SKIM]` | Synthetic raster generation + `FixtureTerrainSource` / `FixtureTS6Reference`. |
| 34 | `tests/conftest.py` | `[SKIM]` | Wires the fixtures above into the `synthetic_corpus`, `synthetic_bathymetry_path`, `synthetic_ts6_raster_path` pytest fixtures every test file uses. |
| 35 | `data/fixtures/native/*.csv` + `tests/fixtures/samples/*.csv` | `[REFERENCE ONLY]` | The actual fake/sample data files. |

### Stage H — Tests (content is fully covered in §4's table; skim the files themselves for style)

| # | File | Mark |
|---|---|---|
| 36 | `tests/test_contracts_parse.py` | `[SKIM]` |
| 37 | `tests/test_observation_schema.py` | `[SKIM]` |
| 38 | `tests/test_ingestion_pipeline.py` | `[SKIM]` |
| 39 | `tests/test_sample_source.py` | `[SKIM]` |
| 40 | `tests/test_specification_combinators.py` | `[SKIM]` |
| 41 | `tests/test_engine_template_method.py` | `[SKIM]` |
| 42 | `tests/test_fixture_rasters.py` | `[SKIM]` |
| 43 | `tests/test_pangaea_adapter.py` | `[SKIM]` |
| 44 | `tests/test_tabular_file_adapter.py` | `[SKIM]` |
| 45 | `tests/test_regional_grid_adapter.py` | `[SKIM]` |

### Stage I — Config (last, and only if curious)

| # | File | Mark | Why this file exists |
|---|---|---|---|
| 46 | `pyproject.toml` | `[REFERENCE ONLY]` | Dependency list + pytest config. |
| 47 | `docker-compose.yml` | `[REFERENCE ONLY]` | Postgres/PostGIS + MinIO — not wired to any code yet. |
| 48 | `.github/workflows/ci.yml` | `[REFERENCE ONLY]` | Runs `pytest -v` on every push. |

---

## 2. How the pieces connect — a raw row's journey

This is `IngestionPipeline.run()` (`engine/prospectivity/ingestion/pipeline.py`), the
Template Method that owns this whole sequence:

```
IngestionPipeline.run()                                     TEMPLATE METHOD (pipeline.py)
│
├─ 1. fetch      ──► adapter.fetch()                         ADAPTER
│                     -> list[native dict rows]                 REAL: PangaeaAdapter /
│                     (whatever shape the source natively has)   TabularFileAdapter /
│                                                                 RegionalGridAdapter
├─ 2. adapt      ──► adapter.adapt(raw_records)               ADAPTER
│                     -> list[RawRecord]                         (_column_mapping.py's
│                     evidence_class SET, abundance_kg_m2=None    build_records() does
│                     one native row -> N evidence-typed rows)    the fan-out for all 3)
│
├─ 3. normalize  ──► normalizers[evidence_class].normalize()  STRATEGY
│                     -> list[RawRecord]                         AbundanceNormalizer —
│                     abundance_kg_m2 filled ONLY where valid     ABC ONLY IN PRODUCTION.
│                     (MASS: always: COUNT: needs mean mass;      Fixture* versions exist
│                      COVER/GRADE: never; GRID: prior-flagged)   only in tests/. E1.2.
│
├─ 4. validate   ──► Observation(**record)                    Pydantic model
│                     -> list[Observation]                       (domain/observation.py)
│                     raises ValueError if COVER/GRADE carry      THE SACRED-RULE GATE —
│                     abundance_kg_m2, GRID says "observed",      cannot be bypassed by
│                     or COUNT has no mean_nodule_mass_g          any adapter or normalizer
│
├─ 5. dedup      ──► dedup_specification.is_satisfied_by(obs) SPECIFICATION
│                     -> list[Observation] (kept only)            Specification ABC +
│                     (currently: no concrete rule exists,        combinators only.
│                      dedup_specification=None -> passthrough)   No dedup rule yet. E1.3.
│
└─ 6. append     ──► corpus.extend(deduped)                   plain list — "the master
                                                                  corpus" for this run
```

**Where this sits in the bigger picture** — the corpus this produces is what
`SampleSource.get_training_samples()` (Stage C, `samples/source.py`) later filters down
to MASS-only rows for `ProspectivityEngine` to train on:

```
IngestionPipeline.run()  ──►  corpus: list[Observation]  ──►  SampleSource
   (per source, repeated                                       .get_training_samples()
    once per entry in                                              │ (frozen filter:
    source_queue.yaml)                                             │  MASS + abundance_kg_m2
                                                                     │  present + is_open)
                                                                     ▼
                                                          ProspectivityEngine.run()
                                                          (ingest→features→CV→predict→
                                                           uncertainty→economics→
                                                           compare_to_ts6→manifest)
```

**What E1.1 actually built:** steps 1 and 2 above, for real, for three source families.
Steps 3 and 5 are still the empty ABC + a `None` passthrough. Step 4 (the sacred-rule
gate) already runs on E1.1's real adapter output today — every adapter test proves this
by round-tripping its records through `Observation(**record)`.

---

## 3. Read-closely files, in detail

### `engine/prospectivity/domain/evidence.py`

**What it does:** defines `EvidenceClass` and five supporting enums (`ObservationOrPrediction`,
`SampleMethod`, `AbundanceBasis`, `QualityGrade`, `QAStatus`) — the controlled vocabulary
every other file in the repo speaks in.

**Pattern:** none — this is vocabulary, not a seam. But every Strategy/Adapter/Specification
downstream is parameterized by these enums.

**Public API:**
```python
class EvidenceClass(str, Enum):
    MASS = "MASS"; COUNT = "COUNT"; COVER = "COVER"; GRID = "GRID"; GRADE = "GRADE"

class ObservationOrPrediction(str, Enum):
    OBSERVED = "observed"; COMPILED = "compiled"; INTERPOLATED = "interpolated"; MODELLED = "modelled"

class SampleMethod(str, Enum):  # BOX_CORER, GRAB_SAMPLER, FREE_FALL_GRAB, DREDGE, IMAGE, AUV, OFOS, CHAMBER, COMPILED, OTHER
class AbundanceBasis(str, Enum):  # WET, DRY, UNKNOWN
class QualityGrade(str, Enum):    # A, B, C
class QAStatus(str, Enum):        # PENDING, PASS, FAIL, FLAGGED
```

**Verify by eye:** `EvidenceClass` has exactly the five values `MASS/COUNT/COVER/GRID/GRADE`
— nothing more, nothing less. Any drift here silently changes what every `in EvidenceClass`
check in the test suite actually allows.

---

### `engine/prospectivity/domain/observation.py`

**What it does:** `Observation`, a Pydantic `BaseModel` mirroring all 30 fields of
`master_observations.schema.json` field-for-field, plus a `model_validator` that enforces
four cross-field rules a JSON Schema can't express on its own.

**Pattern:** none named — this is the domain entity. It's the file CLAUDE.md's
scientific-integrity section is actually about: "encode in code + tests, not just docs."

**Public API:**
```python
class Observation(BaseModel):
    # all 30 Contract-1 fields, typed (source_record_id, source_id, evidence_class,
    # longitude, latitude, water_depth_m, cruise, station_id, event_id,
    # sample_datetime_utc, sample_method, sampled_area_m2, abundance_value_original,
    # abundance_unit_original, abundance_basis, nodule_mass_kg, abundance_kg_m2,
    # nodule_count, nodule_density_m2, visible_cover_percent, mean_nodule_mass_g,
    # mn_pct, ni_pct, cu_pct, co_pct, derivation_formula, observation_or_prediction,
    # is_open, quality_grade, duplicate_group_id, qa_status, notes)

    def is_training_eligible(self) -> bool: ...   # AR-P02 rule, reused by SampleSource
```
Two `@field_validator`s (`source_record_id`, `source_id` — regex patterns) and one
`@model_validator(mode="after")` named `_enforce_evidence_class_discipline`.

**Verify by eye:** read `_enforce_evidence_class_discipline` (lines 102–131) line by line.
It raises on exactly four conditions:
1. `COVER` + `abundance_kg_m2` set
2. `GRADE` + `abundance_kg_m2` set
3. `GRID` + `observation_or_prediction == OBSERVED`
4. `COUNT` + `abundance_kg_m2` set + `mean_nodule_mass_g` is `None`

Confirm you agree these are the complete set of "sacred rules" — this function is the
entire scientific-integrity enforcement of the project in one place.

---

### `engine/prospectivity/samples/source.py`

**What it does:** `SampleSource` ABC with one abstract method and one *concrete* method.

**Pattern:** STRATEGY, with a deliberate twist: the MASS-only training filter is not part
of the swappable surface. It's implemented once, on the base class, so every subclass
inherits it unconditionally.

**Public API:**
```python
class SampleSource(ABC):
    @abstractmethod
    def load_observations(self) -> list[Observation]: ...   # per-strategy

    def get_training_samples(self) -> list[Observation]:    # concrete, frozen
        return [obs for obs in self.load_observations() if obs.is_training_eligible()]
```

**Verify by eye:** `get_training_samples` has no `@abstractmethod` decorator and a real
body — confirm a subclass genuinely cannot change what "training eligible" means without
overriding a method whose own docstring says "Not overridable."

---

### `engine/prospectivity/engine.py`

**What it does:** `ProspectivityEngine` — the top-level Template Method for a whole
prospectivity run: ingest → features → CV → predict → uncertainty → compare_to_ts6 →
economics → manifest.

**Pattern:** TEMPLATE METHOD via composition (constructor-injected Strategies), same
style as `IngestionPipeline`, not subclassing.

**Public API:**
```python
FeatureBuilder = Callable[[TerrainLayer, list[Observation]], tuple[Any, Any]]
CrossValidator = Callable[[Any, Any, Estimator], list[CVScore]]

class ProspectivityEngine:
    def __init__(
        self, study_area: StudyArea, terrain_source: TerrainSource,
        sample_source: SampleSource, feature_builder: FeatureBuilder,
        cross_validator: CrossValidator, estimator: Estimator,
        ts6_reference: TS6Reference, economic_model: EconomicModel,
        scenario_configs: list[dict[str, Any]], seed: int = 0,
        compare_to_ts6_fn: Callable[[Any, Any], TS6Agreement] = compare_to_ts6,
    ) -> None: ...

    def run(self) -> RunManifest: ...
    # private steps: _ingest, _build_features, _cross_validate, _fit_predict,
    #                _compare_to_ts6, _apply_economics, _emit_manifest
```

**Verify by eye:** `run()`'s 8-line body (lines 94–101) — confirm it never contains real
modeling logic, only calls to injected collaborators. If a future edit ever adds real
math directly inside `run()` or its private step methods, that's the "pipeline rewrite"
CLAUDE.md says to stop and flag.

---

### `engine/prospectivity/ingestion/source_adapter.py`

**What it does:** `SourceAdapter` ABC (two abstract methods) + the `RawRecord` type alias.

**Pattern:** ADAPTER — one adapter class per native *format*, not per source entry.

**Public API:**
```python
RawRecord = dict[str, Any]

class SourceAdapter(ABC):
    source_id: str   # class-level annotation only — not enforced by the ABC machinery

    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]: ...
    @abstractmethod
    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]: ...
```

**Verify by eye:** `source_id: str` is a bare type annotation, not a Pydantic field or
enforced property — nothing in the ABC stops a subclass from forgetting to set it.
Confirm each of the three real adapters (Stage E) actually sets `self.source_id` in
`__init__` — they do, but the ABC can't check this for you; a future adapter could
silently omit it.

---

### `engine/prospectivity/ingestion/normalizer.py`

**What it does:** `AbundanceNormalizer` ABC — one method, `normalize()`.

**Pattern:** STRATEGY, one instance per evidence class.

**Public API:**
```python
class AbundanceNormalizer(ABC):
    @abstractmethod
    def normalize(self, record: RawRecord) -> RawRecord: ...
```

**Verify by eye:** there is **no production subclass of this anywhere in `engine/`** —
confirm with `grep -rn "AbundanceNormalizer)" . --include="*.py" | grep -v .venv`. This
matches every `class Foo(AbundanceNormalizer):` line (the bare ABC declaration itself,
`class AbundanceNormalizer(ABC):`, doesn't match this pattern — its own parent is `ABC`,
not `AbundanceNormalizer`). All four hits are in `tests/fixtures/normalizers.py`
(`FixtureMassNormalizer`, `FixtureCountNormalizer`, `FixtureCoverNormalizer`,
`FixtureGridNormalizer`); zero are in `engine/`. That test-only code is never imported by
the production package.

---

### `engine/prospectivity/ingestion/specification.py`

**What it does:** `Specification` ABC + three private combinator classes
(`_AndSpecification`, `_OrSpecification`, `_NotSpecification`) implementing `&`, `|`, `~`.

**Pattern:** SPECIFICATION.

**Public API:**
```python
class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, observation: Observation) -> bool: ...
    def __and__(self, other: "Specification") -> "Specification": ...
    def __or__(self, other: "Specification") -> "Specification": ...
    def __invert__(self) -> "Specification": ...
```

**Verify by eye:** the three combinator classes are private (leading underscore) and
never imported outside this file. Confirm `is_satisfied_by` is the *only* method a future
concrete dedup rule needs to implement — the boolean algebra (`&`/`|`/`~`) is inherited
for free, demonstrated in `tests/test_specification_combinators.py`.

---

### `engine/prospectivity/ingestion/pipeline.py`

**What it does:** `IngestionPipeline` — runs one `SourceAdapter` through the full
fetch→adapt→normalize→validate→dedup→append sequence.

**Pattern:** TEMPLATE METHOD via composition.

**Public API:**
```python
class IngestionPipeline:
    def __init__(
        self, adapter: SourceAdapter,
        normalizers: dict[EvidenceClass, AbundanceNormalizer],
        corpus: list[Observation],
        dedup_specification: Specification | None = None,
    ) -> None: ...
    def run(self) -> list[Observation]: ...
    # private steps: _fetch, _adapt, _normalize, _validate, _dedup, _append
```

**Verify by eye:** read the module docstring's disclosed ordering note — this
implementation runs `validate` (step 4) *before* `dedup` (step 5), while the alpha
proposal's shorthand states "dedup→validate." This is one of the three things flagged at
the end of Phase 0 for your review; it's still true today. Also note: nothing in
production yet constructs an `IngestionPipeline` with a real adapter + real normalizers —
only the fixture-based tests do. There's no `build_corpus.py`-style entry point yet.

---

### `engine/prospectivity/ingestion/_column_mapping.py`

**What it does:** `EvidenceClassMapping` dataclass + `build_records()` — the shared "fan
one native row into N evidence-typed `RawRecord`s" logic all three real adapters call
instead of re-deriving it.

**Pattern:** none named — the module's own docstring says so explicitly: "Not one of
CLAUDE.md's named seams... this is private implementation-sharing infrastructure."

**Public API:**
```python
@dataclass(frozen=True)
class EvidenceClassMapping:
    evidence_class: str
    column_map: dict[str, str]
    presence_column: str | None = None

def build_records(
    native_rows: list[dict[str, Any]], *, source_id: str,
    shared_column_map: dict[str, str], evidence_mappings: list[EvidenceClassMapping],
    is_open: bool, observation_or_prediction: str,
    static_fields: dict[str, Any] | None = None,
) -> list[RawRecord]: ...
```

**Verify by eye:** line 64 — `if mapping.presence_column is not None and
row.get(mapping.presence_column) is None: continue`. Confirm this is an explicit `is
None` check, not a truthiness check (`not row.get(...)`). A truthiness check would
silently drop a legitimate `0` nodule count or `0%` cover reading (both valid, barren
readings per Contract 1) — the `is None` form is what makes that distinction correctly.

---

### `engine/prospectivity/ingestion/pangaea_adapter.py`

**What it does:** `PangaeaAdapter` — the real adapter for the six PANGAEA-hosted
sources (`[01]`–`[05]`, `[12]`).

**Pattern:** ADAPTER. One *class*, configured per source instance — not six classes.

**Public API:**
```python
def _fetch_via_pangaeapy(doi: str) -> pd.DataFrame: ...   # lazy-imports pangaeapy

class PangaeaAdapter(SourceAdapter):
    def __init__(
        self, source_id: str, doi: str, shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping], is_open: bool,
        static_fields: dict[str, Any] | None = None,
        dataset_loader: Callable[[], pd.DataFrame] | None = None,
    ) -> None: ...
    def fetch(self) -> list[dict[str, Any]]: ...
    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]: ...
```

**Verify by eye:** `dataset_loader` defaults to `lambda: _fetch_via_pangaeapy(self._doi)`,
and `_fetch_via_pangaeapy` imports `pangaeapy` *inside* the function body (line 34), not
at module level. Confirm this — it's why importing this file, or running its tests,
never requires network access or even a working `pangaeapy` install at import time.

---

### `engine/prospectivity/ingestion/tabular_file_adapter.py`

**What it does:** `TabularFileAdapter` — the real adapter for Dryad/Mendeley workbooks
(`[06]`, `[14]`).

**Pattern:** ADAPTER.

**Public API:**
```python
class TabularFileAdapter(SourceAdapter):
    def __init__(
        self, source_id: str, file_path: Path, shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping], is_open: bool,
        static_fields: dict[str, Any] | None = None, sheet_name: str | int = 0,
    ) -> None: ...
    def fetch(self) -> list[dict[str, Any]]: ...
    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]: ...
```

**Verify by eye:** `fetch()`'s branch — `if self._file_path.suffix.lower() in {".xlsx",
".xls"}: pd.read_excel(...) else: pd.read_csv(...)`. Confirm both branches are actually
exercised in `tests/test_tabular_file_adapter.py` (they are — one test per branch), not
just one format tested and the other assumed to work.

---

### `engine/prospectivity/ingestion/regional_grid_adapter.py`

**What it does:** `RegionalGridAdapter` — the real adapter for the two GRID sources
(`[18]`, `[19]`).

**Pattern:** ADAPTER, with an added constructor guard not present in the other two.

**Public API:**
```python
_NON_OBSERVED_VALUES = {"compiled", "interpolated", "modelled"}

class RegionalGridAdapter(SourceAdapter):
    def __init__(
        self, source_id: str, file_path: Path, shared_column_map: dict[str, str],
        evidence_mappings: list[EvidenceClassMapping], is_open: bool,
        observation_or_prediction: str,
        static_fields: dict[str, Any] | None = None,
    ) -> None: ...   # raises ValueError if observation_or_prediction not in _NON_OBSERVED_VALUES
    def fetch(self) -> list[dict[str, Any]]: ...
    def adapt(self, raw_records: list[dict[str, Any]]) -> list[RawRecord]: ...
```

**Verify by eye:** the `ValueError` guard runs in `__init__`, before any file is even
read. Confirm there's no code path — no default argument, no optional override — that
could construct this adapter with `"observed"` and have it silently pass through to
`adapt()`. This is intentionally the second line of defense; `Observation`'s own
validator (line 114–121 of `observation.py`) is the first.

---

## 4. Test inventory — all 44 tests

Grouped by what each group protects. "What breaks if this failed" describes a bug the
test exists to catch, worded as a real-world consequence.

### Group 1 — Evidence-class integrity (16 tests)

| Test file :: test name | Asserts | Rule enforced | What breaks in the real world if it failed |
|---|---|---|---|
| `test_ingestion_pipeline.py::test_corpus_contains_every_evidence_class_the_fixtures_produce` | Ingesting all 3 synthetic sources yields exactly `{MASS,COUNT,COVER,GRID}` in the corpus | AR-D02 (mandatory tagging) | A source family's evidence class silently gets dropped or miscategorized during ingestion, and nobody notices until the model trains on the wrong rows. |
| `test_ingestion_pipeline.py::test_pipeline_cover_output_satisfies_evidence_class_discipline` | Every COVER row post-pipeline has `abundance_kg_m2 is None` | AR-D03 / Contract 7 COVER rule | A future normalizer bug converts cover% to kg/m² and it reaches the real corpus undetected. |
| `test_ingestion_pipeline.py::test_pipeline_grid_output_satisfies_evidence_class_discipline` | Every GRID row post-pipeline has `observation_or_prediction != OBSERVED` | AR-D03 / Contract 6 | TS-6's own grid gets treated as an independent training station, making the later TS-6 benchmark comparison circular without anyone flagging it. |
| `test_ingestion_pipeline.py::test_pipeline_count_output_satisfies_evidence_class_discipline` | Every COUNT row with `abundance_kg_m2` set also has `mean_nodule_mass_g` set | AR-D03 / Contract 7 COUNT rule | A count→mass conversion happens without a documented assumption, making the derived value unauditable. |
| `test_ingestion_pipeline.py::test_synthetic_fixture_mass_rows_all_qualify_for_training` | Every MASS row post-pipeline passes `is_training_eligible()` | AR-P02 | The corpus contains MASS rows that *look* trainable but are missing `abundance_kg_m2` or `is_open`, silently shrinking the real training set. |
| `test_observation_schema.py::test_every_row_has_a_tagged_evidence_class` | Every row in the real `master_observations.csv` has a valid `EvidenceClass` | AR-D02 | An untagged or mistyped row enters the published corpus. |
| `test_observation_schema.py::test_cover_rows_never_carry_abundance_kg_m2` | Same check, against the real corpus CSV, not fixtures | AR-D03 | Same as above, but against the actual file Track G edits — the one CI would actually catch a real mistake in. |
| `test_observation_schema.py::test_grid_rows_are_never_flagged_observed` | Same check, against the real corpus CSV | AR-D03 / Contract 6 | Same as above, for GRID rows. |
| `test_observation_schema.py::test_cover_row_with_abundance_kg_m2_is_rejected` | Constructing a COVER `Observation` with `abundance_kg_m2` set raises `ValidationError` | CLAUDE.md sacred rule #1 | This is the regression test for the single most emphasized rule in the whole project — if it ever stops raising, cover-derived "mass" values could poison the model with zero warning. |
| `test_observation_schema.py::test_grid_row_flagged_observed_is_rejected` | Constructing a GRID `Observation` marked `observed` raises `ValidationError` | CLAUDE.md sacred rule / Contract 6 | TS-6's grid could be mistaken for a real station at the type level, not just the data level. |
| `test_observation_schema.py::test_count_row_needs_mean_nodule_mass_to_carry_abundance` | Constructing a COUNT `Observation` with `abundance_kg_m2` but no `mean_nodule_mass_g` raises `ValidationError` | Contract 7 COUNT rule | A count→mass value enters the corpus with an untraceable assumption. |
| `test_observation_schema.py::test_grade_row_never_carries_abundance_kg_m2` | Constructing a GRADE `Observation` with `abundance_kg_m2` set raises `ValidationError` | Contract 7 GRADE rule | Chemistry-only rows could be mistaken for independent mass measurements. |
| `test_regional_grid_adapter.py::test_adapt_tags_every_row_grid_and_never_observed` | `RegionalGridAdapter.adapt()` output is 100% GRID, 100% `compiled` | AR-D01 + AR-D03 | A real GRID adapter instance misconfigured with the wrong `observation_or_prediction` string still produces GRID rows that look observed. |
| `test_regional_grid_adapter.py::test_constructor_rejects_observed_for_grid_sources` | Constructing `RegionalGridAdapter(..., observation_or_prediction="observed")` raises `ValueError` | Contract 6 / defense-in-depth for AR-D03 | A config typo (`"observed"` instead of `"compiled"`) when wiring up `[18]`/`[19]` in Phase 1/3 fails loudly at adapter construction instead of silently at validation, or worse, not at all. |
| `test_sample_source.py::test_get_training_samples_returns_mass_only` | `get_training_samples()` returns only MASS rows, all with `abundance_kg_m2` set, all `is_open` | AR-P02 | The model trains on COUNT/COVER/GRID/GRADE rows it should never see. |
| `test_sample_source.py::test_get_training_samples_excludes_cover_count_and_grid` | The set of training IDs is disjoint from the set of non-MASS IDs in the same corpus | AR-P02 | Same failure mode, checked the other direction (no non-MASS ID leaks through). |

### Group 2 — Schema conformance (12 tests)

| Test file :: test name | Asserts | Rule enforced | What breaks in the real world if it failed |
|---|---|---|---|
| `test_contracts_parse.py::test_master_observations_schema_json_parses` | `schema.json` parses, `schema_version == 3`, has `evidence_class`/`abundance_kg_m2` fields | Contract 1 | The frozen schema file itself is malformed and nobody notices until an adapter breaks. |
| `test_contracts_parse.py::test_covariates_yaml_parses_with_option_a_enabled` | `covariates.yaml` parses; depth/slope enabled; all candidate (Option-B) covariates disabled | Contract 3 | Option-B TS-6 proxies get silently enabled before Phase 6, expanding scope without anyone deciding to. |
| `test_contracts_parse.py::test_scenarios_yaml_parses_and_is_illustrative_only` | `scenarios.yaml` parses; both scenarios still flagged `illustrative_only: true` | Contract 4 / "honesty over impressiveness" | A placeholder economic cutoff gets presented as a real result before Track G delivers real numbers. |
| `test_contracts_parse.py::test_source_queue_yaml_parses_with_open_sources` | `source_queue.yaml` parses; every entry has a `source_id` | Contract 5 | A malformed queue entry breaks every adapter configured against it, at the data level rather than the code level. |
| `test_contracts_parse.py::test_normalization_yaml_forbids_cover_and_grade_kg_m2` | `normalization.yaml` declares `COVER.produces_kg_m2: false` and `GRADE.produces_kg_m2: false` | Contract 7 | The policy file itself — not just the code — could drift to allow cover→mass conversion. |
| `test_contracts_parse.py::test_ts6_reference_yaml_parses` | `ts6_reference.yaml` parses; raster path is `data/ts6/ts6_abundance.tif` | Contract 6 | The benchmark config points at the wrong file once Track G digitizes the real TS-6 surface. |
| `test_contracts_parse.py::test_study_area_geojson_loads_through_the_domain_type` | `study_area.geojson`'s first feature loads via `StudyArea.from_geojson_feature()` and produces a valid shapely geometry | Contract 2 | The AOI geometry is malformed and every downstream terrain-clip step fails at runtime instead of at CI. |
| `test_contracts_parse.py::test_exclusions_geojson_loads_and_starts_empty` | `exclusions.geojson` loads to zero `ExclusionZone`s | Contract 2 | The placeholder exclusions file silently gains a bogus polygon that shrinks the minable footprint for no real reason. |
| `test_observation_schema.py::test_master_observations_csv_validates_against_schema` | Every row of the real `master_observations.csv` constructs a valid `Observation` | Contract 1 | The published corpus file itself contains a row that violates the frozen schema. |
| `test_pangaea_adapter.py::test_adapt_output_validates_against_the_master_schema` | Every `PangaeaAdapter.adapt()` record round-trips through `Observation(**record)` | AR-D01 + Contract 1 | The real PANGAEA adapter produces a record shape `IngestionPipeline`'s `validate` step would reject at real ingestion time. |
| `test_regional_grid_adapter.py::test_adapt_output_validates_against_the_master_schema` | Same, for `RegionalGridAdapter` | AR-D01 + Contract 1 | Same failure mode, for the GRID sources. |
| `test_tabular_file_adapter.py::test_adapt_output_validates_against_the_master_schema` | Same, for `TabularFileAdapter` | AR-D01 + Contract 1 | Same failure mode, for the Dryad/Mendeley sources. |

### Group 3 — Adapter correctness, E1.1 (7 tests)

| Test file :: test name | Asserts | Rule enforced | What breaks in the real world if it failed |
|---|---|---|---|
| `test_pangaea_adapter.py::test_fetch_reads_the_injected_sample_without_network` | `fetch()` returns 4 rows from the injected `dataset_loader`, first row's `Event` matches | AR-D01 | The dependency-injection seam (`dataset_loader`) that lets this adapter be tested without a real network call is broken, which would force every future PANGAEA-adapter test to hit the internet. |
| `test_pangaea_adapter.py::test_adapt_fans_one_native_row_into_mass_count_cover_records` | 4 native rows → 12 records (4×3 evidence classes) | AR-D01 + AR-D02 | A box-core source's COUNT or COVER data silently gets dropped during adapting instead of becoming its own evidence-typed row. |
| `test_pangaea_adapter.py::test_adapt_stamps_source_id_and_queue_provenance` | Every record has correct `source_id`, `is_open`, `observation_or_prediction`, `sample_method`; MASS records carry `sampled_area_m2=0.25`; nothing has `abundance_kg_m2` set | AR-D01 + AR-D04 | A record loses its provenance link back to `source_queue.yaml`, breaking the corpus manifest's ability to trace every row to a source. |
| `test_regional_grid_adapter.py::test_fetch_reads_the_grid_csv` | `fetch()` reads the 3-row sample grid CSV correctly | AR-D01 | The grid-file read path breaks silently (e.g. wrong column parsing). |
| `test_tabular_file_adapter.py::test_fetch_reads_a_csv_workbook` | `fetch()` reads a Dryad-style CSV correctly | AR-D01 | The CSV branch of the xlsx/csv adapter breaks. |
| `test_tabular_file_adapter.py::test_fetch_reads_an_xlsx_workbook` | `fetch()` reads a generated `.xlsx` workbook identically to the CSV version | AR-D01 | The xlsx branch (needed for the real Dryad chamber workbook) breaks while the CSV branch still passes, hiding the bug. |
| `test_tabular_file_adapter.py::test_adapt_maps_chamber_footprint_as_sampled_area_per_row` | Each record's `sampled_area_m2` comes from that row's own `chamber_footprint_m2` column, not a fixed constant | Contract 5 `src_dryad_chamber` note ("record per experiment") | Per-experiment chamber footprints get collapsed into one fixed area, silently corrupting every future kg/m² derivation for this source. |

### Group 4 — Pipeline wiring / Template Method sequencing (5 tests)

| Test file :: test name | Asserts | Rule enforced | What breaks in the real world if it failed |
|---|---|---|---|
| `test_ingestion_pipeline.py::test_synthetic_sources_ingest_into_a_tagged_corpus` | Running 3 fixture adapters through `IngestionPipeline.run()` produces a non-empty, fully-tagged corpus | Template Method (design-pattern discipline) | The fetch→adapt→normalize→validate→dedup→append sequence itself is broken — not any one rule, but the plumbing connecting all of them. |
| `test_engine_template_method.py::test_run_calls_steps_in_the_documented_order` | `ProspectivityEngine.run()` calls ingest→features→cv→fit→predict→ts6:load→ts6:compare→economics(×N) in exactly that order, with a real seed and result count | Template Method (design-pattern discipline) | A future refactor accidentally reorders steps (e.g. runs economics before the TS-6 comparison), and every result downstream is subtly wrong in an order-dependent way (e.g. CV using an un-fit estimator). |
| `test_specification_combinators.py::test_and_specification` | `&` combinator returns true only when both specs are true | SPECIFICATION (design-pattern discipline), foundation for AR-D04 | A future concrete dedup rule built by combining specs (`&`) behaves like `or` instead of `and`. |
| `test_specification_combinators.py::test_or_specification` | `|` combinator returns true when either spec is true | Same | Same failure mode, the other direction. |
| `test_specification_combinators.py::test_not_specification` | `~` combinator inverts correctly | Same | A negated dedup/QA rule (e.g. "keep everything that is NOT a duplicate") silently keeps duplicates instead of excluding them. |

### Group 5 — Terrain/TS6 fixture machinery (4 tests)

| Test file :: test name | Asserts | Rule enforced | What breaks in the real world if it failed |
|---|---|---|---|
| `test_fixture_rasters.py::test_synthetic_bathymetry_is_a_valid_raster` | Synthetic DEM has 1 band, `EPSG:4326`, all-negative depth values | AR-P01 (infrastructure) | The raster-generation helper itself produces an invalid/misprojected file, and every test depending on `synthetic_bathymetry_path` would be silently testing against garbage. |
| `test_fixture_rasters.py::test_fixture_terrain_source_returns_a_terrain_layer` | `FixtureTerrainSource.load()` returns a `TerrainLayer` pointing at the right path | TerrainSource STRATEGY contract | A future real `TerrainSource` subclass could get the same shape wrong and no test would catch it, since this proves the *shape*, not the science. |
| `test_fixture_rasters.py::test_synthetic_ts6_raster_is_a_valid_raster` | Synthetic TS-6 raster has all-positive abundance values | Contract 6 (infrastructure) | Same failure mode as the bathymetry raster test, for the TS-6 benchmark stand-in. |
| `test_fixture_rasters.py::test_fixture_ts6_reference_returns_a_benchmark_surface` | `FixtureTS6Reference.load()` returns a `TS6Surface` with `role_note="benchmark_only"` | TS6Reference STRATEGY contract + Contract 6 | A future real `TS6Reference` could omit `role_note`, silently making every TS-6 comparison ambiguous about whether it's circular. |

---

## 5. How to hand-check this yourself

### 5a. pytest selections

```bash
cd "/Users/karlmoreno/CCZ/ccz-prospectivity-engine"
source .venv/bin/activate

# Everything (should say "44 passed")
pytest -v

# Just the evidence-class integrity group (Group 1 above)
pytest -v tests/test_observation_schema.py tests/test_ingestion_pipeline.py tests/test_sample_source.py tests/test_regional_grid_adapter.py::test_constructor_rejects_observed_for_grid_sources tests/test_regional_grid_adapter.py::test_adapt_tags_every_row_grid_and_never_observed

# Just the four regression tests that prove a sacred-rule violation is REJECTED
pytest -v -k rejected

# Just E1.1's three real adapters
pytest -v tests/test_pangaea_adapter.py tests/test_tabular_file_adapter.py tests/test_regional_grid_adapter.py

# One test, with print() output visible (-s), to watch it work
pytest -v -s tests/test_pangaea_adapter.py::test_adapt_fans_one_native_row_into_mass_count_cover_records

# List every collected test without running them
pytest --collect-only -q
```

### 5b. Watch the machinery work — a REPL script

Paste this into `python3` (after `source .venv/bin/activate`, run from the repo root) to
watch a real adapter turn a saved sample into records, validate them, and then watch the
sacred rule reject a deliberately broken one:

```python
import pandas as pd
from pathlib import Path

from engine.prospectivity.domain.evidence import EvidenceClass, ObservationOrPrediction
from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._column_mapping import EvidenceClassMapping
from engine.prospectivity.ingestion.pangaea_adapter import PangaeaAdapter

SAMPLE = Path("tests/fixtures/samples/pangaea_boxcore_sample.csv")

adapter = PangaeaAdapter(
    source_id="src_so268_boxcore",
    doi="10.1594/PANGAEA.904967",
    shared_column_map={
        "event_id": "Event", "latitude": "Latitude", "longitude": "Longitude",
        "water_depth_m": "Depth water [m]", "sample_datetime_utc": "Date/Time",
    },
    evidence_mappings=[
        EvidenceClassMapping("MASS", {"nodule_mass_kg": "Mass nod wet [kg]"}),
        EvidenceClassMapping("COUNT", {"nodule_count": "Nod count [#]"}, presence_column="Nod count [#]"),
        EvidenceClassMapping("COVER", {"visible_cover_percent": "Cover nod [%]"}, presence_column="Cover nod [%]"),
    ],
    is_open=True,
    static_fields={"sample_method": "box_corer", "sampled_area_m2": 0.25},
    dataset_loader=lambda: pd.read_csv(SAMPLE),   # stand-in for a real pangaeapy fetch
)

raw = adapter.fetch()
print(f"{len(raw)} native rows fetched from the sample\n")

records = adapter.adapt(raw)
for r in records:
    print(f"{r['evidence_class']:6s} {r['source_record_id']:30s} abundance_kg_m2={r.get('abundance_kg_m2')}")

# every adapted record is already schema-valid, even though nothing has been normalized
observations = [Observation(**r) for r in records]
print(f"\n{len(observations)} validated Observations; none has abundance_kg_m2 yet:",
      all(o.abundance_kg_m2 is None for o in observations))

# now break the #1 sacred rule on purpose and watch it get rejected, live
print("\nDeliberately constructing a COVER row with abundance_kg_m2 set...")
try:
    Observation(
        source_record_id="MANUAL_BAD", source_id="src_synthetic_cover",
        evidence_class=EvidenceClass.COVER, longitude=-126.0, latitude=12.0,
        abundance_kg_m2=5.0, observation_or_prediction=ObservationOrPrediction.OBSERVED,
        is_open=True, qa_status="pending",
    )
    print("!! THIS SHOULD NOT PRINT — the sacred rule failed to fire !!")
except Exception as e:
    print("Rejected as expected:", e)
```

Expected output: 4 native rows, 12 records printed (MASS/COUNT/COVER × 4), all showing
`abundance_kg_m2=None`, then the deliberate violation raising a `pydantic.ValidationError`
with the message from `observation.py`'s validator.

---

## 6. What's deliberately missing

### Empty ABCs (interfaces exist, zero production implementations)

| Interface | File | First real subclass arrives |
|---|---|---|
| `TerrainSource` | `terrain/source.py` | Phase 1, G1.1 (real GEBCO bathymetry) |
| `SampleSource` | `samples/source.py` | Phase 1 (a `CorpusCsvSampleSource` reading `data/corpus/master_observations.csv` for real) |
| `Estimator` | `estimators/base.py` | Phase 2 (kriging, random forest, mean baseline) |
| `TS6Reference` | `ts6/reference.py` | Phase 3, G3.1 (digitized `ts6_abundance.tif`) |
| `EconomicModel` | `economics/model.py` | Phase 4 |
| `AbundanceNormalizer` | `ingestion/normalizer.py` | **Phase 1, E1.2 — next** |
| `Specification` (concrete dedup rules) | `ingestion/specification.py` | **Phase 1, E1.3 — next** |
| `compare_to_ts6()` | `ts6/reference.py` | Phase 3, E3.3 |

Everything with a `Fixture*` prefix in `tests/fixtures/` is a test-only stand-in for one
of the above and is never imported by production code — confirmed by the reading-order
comparison in Stage G.

### Reserved, empty directories

- `engine/prospectivity/features/` — Phase 1, E1.4 (terrain feature recipes)
- `engine/prospectivity/validation/` — Phase 2 (spatial CV)
- `engine/prospectivity/uncertainty/` — Phase 2-3
- `engine/prospectivity/provenance/` — Phase 3 (richer manifest emitter; `RunManifest` type + mechanical assembly already exist in `engine.py`)
- `services/api/` — Phase 5 (read-only FastAPI)
- `apps/web/` — Phase 5 (thin viewer)
- `database/migrations/`, `database/fixtures/` — empty `.gitkeep`s, unused until something needs Postgres
- `data/bathymetry/` — empty except a README; real GEBCO `.tif` arrives Phase 1 G1.1, Integration Checkpoint 1
- `data/ts6/ts6_abundance.tif` — doesn't exist yet; real digitized raster arrives Phase 3 G3.1, Integration Checkpoint 3

### Known gaps in E1.1's own coverage

- No adapter test exercises a source with **both** GRID and GRADE evidence classes in one
  row (that's `src_washburn2021_grid [19]`) — `RegionalGridAdapter`'s tests only cover the
  GRID-only case (`src_ts6_grid [18]`). The fan-out mechanism (`build_records`) supports
  multiple `EvidenceClassMapping`s per adapter, so Washburn should work, but it's untested.
- No adapter is wired into a live `IngestionPipeline` with a real `AbundanceNormalizer` —
  every E1.1 test calls `adapter.fetch()`/`adapter.adapt()` directly, not through the
  pipeline. That integration only happens in the fixture tests (`test_ingestion_pipeline.py`),
  never with the real adapters. There is no script/entry point yet that builds a real
  corpus file from `source_queue.yaml`.

### Three things flagged during Phase 0 review (still true today)

1. **Contract path mismatch.** `CLAUDE.md` points to `phase0-contracts-v3/` at the repo
   root; the actual contract files live under `Proposals and contract V3/Contracts_v3/`.
   Resolved by copying the seven files into their canonical locations
   (`docs/contracts/` + `data/*`), but the mismatch in `CLAUDE.md` itself is unchanged.
2. **CSV quoting fix.** `data/corpus/master_observations.csv` (both the copy in this repo
   and the original under `Proposals and contract V3/Contracts_v3/`) had two example rows
   whose `notes` field contained an unescaped comma, breaking `pandas.read_csv`. Fixed by
   quoting the field in both files.
3. **`validate`-before-`dedup` ordering.** `IngestionPipeline.run()` runs `validate` (step
   4) before `dedup` (step 5); the alpha proposal's shorthand states the reverse. Disclosed
   in the `pipeline.py` module docstring. See §3's entry for that file.

### Two scope notes, not yet addressed

1. **No hash-pinned lockfile.** `pyproject.toml` uses version *ranges* (`>=2.6,<3` etc.),
   not exact hash pins. CLAUDE.md's reproducibility rules call for a lockfile. Installing
   currently requires `--only-binary=:all:` to avoid `rasterio` trying to build from
   source (no local GDAL toolchain). Worth revisiting with `uv`/`pip-tools` before a
   published run.
2. **No `source_id` foreign-key enforcement.** `master_observations.schema.json` declares
   a `foreignKeys` constraint (`source_id` → `source_queue.yaml`'s `source_id`), but
   nothing in `Observation` or anywhere else checks that a given `source_id` actually
   exists in `source_queue.yaml`. This is intentional for now — the E1.1 test fixtures use
   synthetic `source_id`s that don't appear in the real queue — but it means a typo'd
   `source_id` on a real adapter would currently pass validation silently.

---

## 7. What to expect next (E1.2 → E1.5)

All four remaining Phase 1 Track E tasks, per the alpha proposal §10. None of this exists
yet — this section is a preview of what "done" should look like so you can tell when it's
actually done.

### E1.2 — Real `AbundanceNormalizer` per evidence class

**Adds:** concrete subclasses of `AbundanceNormalizer` (`ingestion/normalizer.py`) — most
likely one file each or a single `normalizers.py`, e.g. `MassNormalizer`, `CountNormalizer`,
`CoverNormalizer`, `GridNormalizer`, `GradeNormalizer` — reading their parameters (mean
nodule mass source, screening bounds) from `data/config/normalization.yaml` instead of the
hardcoded constants the current `tests/fixtures/normalizers.py` stand-ins use.

**Touches:** `engine/prospectivity/ingestion/` (new files), probably a small
`normalization.yaml` loader shared by all of them.

**New tests should look like:** one test module per normalizer (mirroring the adapter
tests' structure), asserting the exact formula against `normalization.yaml`'s stated math
(`kg_m2 = nodule_mass_kg / sampled_area_m2` for MASS, etc.), plus a repeat of the
COVER/GRADE-never-produces-kg_m2 regression test but against the *real* normalizer class
this time (defense-in-depth on top of `Observation`'s own check). You should be able to
finally construct a real `IngestionPipeline` with a real adapter + real normalizers and
watch `abundance_kg_m2` get filled in for the first time.

### E1.3 — Dedup (`Specification`) + validation; build the master corpus

**Adds:** concrete `Specification` subclasses in `ingestion/` implementing
`normalization.yaml`'s five dedup rules (DOMES families dedupe by
cruise+station+coords+date not DOI; SO268 individual nodules nest within box-core events;
regional grids never merge with observed stations; image cover/count never merges with
recovered mass; coordinate tolerance ~100m). Likely also the first real corpus-builder
entry point — something that wires all three E1.1 adapters + E1.2 normalizers + E1.3
dedup rules through `IngestionPipeline` to actually populate
`data/corpus/master_observations.csv` from real (or Track-G-supplied) downloads.

**Touches:** `engine/prospectivity/ingestion/` (new dedup-rule module), possibly a new
`scripts/` or CLI entry point, `data/corpus/master_observations.csv` (real content
replacing the four `DELETE`-marked example rows).

**New tests should look like:** near-duplicate `Observation` pairs (same
cruise+station+coords+date, different `source_id`) that a dedup `Specification` correctly
flags; a "nodules nest in events" test proving `[05]`'s individual-nodule rows aggregate
to the event rather than each counting as a separate spatial sample; an end-to-end test
proving the *real* pipeline (not fixtures) produces a valid, deduplicated corpus.

### E1.4 — Terrain feature recipes (Option A)

**Adds:** the first real content in `engine/prospectivity/features/` — deterministic,
versioned recipes matching `covariates.yaml`'s enabled Option-A list (`depth`, `slope`,
`aspect`, `roughness`, `profile_curvature`, `plan_curvature`, `tpi`, `bpi`), each reading
a DEM array and each carrying the `recipe_version` from `covariates.yaml`.

**Touches:** `engine/prospectivity/features/` (new files), likely using `richdem` or
`xarray-spatial` (both already on the approved stack, not yet installed).

**New tests should look like:** one test per recipe, run against the synthetic bathymetry
raster already available via `tests/fixtures/rasters.py`, checking output shape and
determinism (same DEM in → same feature array out, every time — CLAUDE.md's "same inputs
+ seed → same outputs" rule applies here too even though there's no randomness involved).
The proposal also mentions "plot corpus [MASS] points over the DEM" — that's a Track G
visual-QA deliverable (a notebook or script producing a figure), not something you should
expect as an automated pytest test.

### E1.5 — Unit tests: evidence tagging, normalization correctness, dedup rules

This task is explicitly about *testing*, not new production code — the wrap-up/hardening
pass across everything E1.1–E1.4 built. Expect it to mean: an end-to-end test proving the
*real* ingestion pipeline (real adapters, real normalizers, real dedup) produces a tagged,
deduplicated corpus — the real-data equivalent of what `test_ingestion_pipeline.py`
already proves for the fixture pipeline today. This is roughly where **Integration
Checkpoint 1** ("swap synthetic DEM → real bathymetry.tif") becomes fully exercised by CI,
closing out Phase 1.
