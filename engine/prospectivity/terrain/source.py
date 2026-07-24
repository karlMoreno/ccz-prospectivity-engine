"""TerrainSource — STRATEGY.

Swappable "where does the bathymetry DEM come from" implementation behind one
interface. A synthetic/fixture DEM and a real GEBCO-class download are both
valid TerrainSource implementations; nothing above this seam (feature
recipes, estimators) needs to know which one it's talking to. Adding a new
terrain provider means adding a class, not touching the pipeline (CLAUDE.md
"program to an interface, not an implementation").

    ┌────────────────┐        ┌───────────────────┐
    │  TerrainSource  │◄───────┤ GEBCOTerrainSource │  (Phase 1, real)
    │     (ABC)       │        └───────────────────┘
    │  .load(area)    │        ┌───────────────────┐
    │  -> TerrainLayer│◄───────┤ FixtureTerrainSrc  │  (tests only)
    └────────────────┘        └───────────────────┘
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prospectivity.domain.study_area import StudyArea
from engine.prospectivity.domain.terrain import TerrainLayer


class TerrainSource(ABC):
    """Produces the bathymetry TerrainLayer for a given StudyArea."""

    @abstractmethod
    def load(self, study_area: StudyArea) -> TerrainLayer:
        """Return the bathymetry layer clipped/aligned to `study_area`.

        Implementations own reprojection to the canonical CRS (EPSG:4326) and
        must set `TerrainLayer.content_hash` (AR-P01: reproject, hash).
        """
        raise NotImplementedError
