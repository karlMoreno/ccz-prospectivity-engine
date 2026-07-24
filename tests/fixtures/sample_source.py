"""Test-only SampleSource (STRATEGY) wrapping an in-memory corpus list."""

from __future__ import annotations

from engine.prospectivity.domain.observation import Observation
from engine.prospectivity.samples.source import SampleSource


class FixtureSampleSource(SampleSource):
    def __init__(self, observations: list[Observation]) -> None:
        self._observations = observations

    def load_observations(self) -> list[Observation]:
        return list(self._observations)
