"""Test-only SampleSource (STRATEGY) wrapping an in-memory corpus list.

data_origin: AUTHORED (author: unrecorded) — hand-written test double.
"""

from __future__ import annotations

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.provenance.origin import AUTHOR_UNRECORDED, DataOrigin
from engine.prospectivity.samples.source import SampleSource

DATA_ORIGIN = DataOrigin.AUTHORED
DATA_AUTHOR = AUTHOR_UNRECORDED


class FixtureSampleSource(SampleSource):
    def __init__(self, observations: list[Observation]) -> None:
        self._observations = observations

    def load_observations(self) -> list[Observation]:
        return list(self._observations)
