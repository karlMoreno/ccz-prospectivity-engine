"""CorpusCsvSampleSource — the production SampleSource (E2.0-1).

STRATEGY (concrete implementation): this fills the Phase-0 `SampleSource`
seam that had zero production implementations since E1.3 (PATTERNS.md §3.2,
BACKLOG §3). The variation point is "where do the corpus observations come
from" — a CSV corpus today, a database in Phase 5 — while the MASS-only
training gate stays frozen on the ABC and is deliberately NOT reimplemented
here: `get_training_samples()` is inherited, and eligibility is decided by
`Observation.is_training_eligible()` alone. Two implementations of one rule
is how they drift.

    data/corpus/master_observations.csv        (108 rows, all 5 classes)
        │  pd.read_csv → NaN→None → Observation(**row)
        ▼                            └─ Contract-1 validation per row:
    CorpusCsvSampleSource                a forbidden row (COVER+abundance,
        .load_observations()             GRID observed, …) raises at load,
        │                                it never reaches a caller
        ▼
    SampleSource.get_training_samples()   ← inherited, frozen gate
        │  Observation.is_training_eligible():
        │    MASS ∧ abundance present (0.0 VALID) ∧ is_open ∧ qa not fail/flagged
        ▼
    35 training-eligible MASS rows

Constructor injection of `csv_path` is the same seam every adapter has via
`dataset_loader`: tests point it at a tmp CSV; production uses the default.

Loading validates every row through `Observation`, so the production read
path applies the same evidence-class discipline as ingestion — a hand-edit
to the CSV that violates Contract 1 fails loudly here, not downstream.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.samples.source import SampleSource

DEFAULT_CORPUS_CSV = (
    find_repo_root(Path(__file__).resolve()) / "data" / "corpus" / "master_observations.csv"
)


class CorpusCsvSampleSource(SampleSource):
    """Reads the master corpus CSV; the ABC's inherited gate does the filtering."""

    def __init__(self, csv_path: Path = DEFAULT_CORPUS_CSV) -> None:
        self._csv_path = Path(csv_path)

    def load_observations(self) -> list[Observation]:
        """Every corpus row, of every evidence class, validated through
        `Observation`. A missing file raises (FileNotFoundError from the
        reader) rather than returning an empty pool — an absent corpus must
        never look like a corpus with nothing eligible.
        """
        frame = pd.read_csv(self._csv_path)
        # NaN → None so Pydantic sees "absent", not float("nan"); the same
        # round-trip convention test_observation_schema.py established.
        frame = frame.astype(object).where(pd.notnull(frame), None)
        return [Observation(**row) for row in frame.to_dict(orient="records")]
