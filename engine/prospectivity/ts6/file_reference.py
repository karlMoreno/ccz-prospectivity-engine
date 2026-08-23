"""FileTS6Reference — STRATEGY (the first non-test TS6Reference).

The seam's production implementation is G3.1's `DigitizedTS6Reference`
(Contract 6 v4: `data/ts6/ts6_abundance.tif`, `raster_data_origin: DERIVED`,
the digitization method and uncertainty recorded). That raster does not
exist. What exists is a synthetic benchmark written by a test generator, and
the run harness must be able to point at it from outside the test suite —
so this class loads a TS-6 raster FROM A PATH with the caller's DECLARED
origin, exactly as `FileTerrainSource` does for the DEM.

    ┌──────────────────────┐      ┌────────────────────────────────────────┐
    │  TS6Reference (ABC)   │◄─────┤ FileTS6Reference(path, data_origin=…)   │  this module
    │  .load() -> TS6Surface│      │   hash ← the bytes; origin ← declared    │
    └──────────────────────┘      └────────────────────────────────────────┘
                                  ┌────────────────────────────────────────┐
                                  │ FixtureTS6Reference   (tests only)      │
                                  │ DigitizedTS6Reference (G3.1, not built) │
                                  └────────────────────────────────────────┘

Today the declaration is SYNTHETIC and the comparison's computed origin says
so (E3.3: least-real wins). At Checkpoint 3 the same class loads the
digitized raster declared DERIVED — or G3.1's own class replaces it; either
is a substitution at the seam, not a change to the engine. An undeclared
origin is refused at construction: `compare_all_to_ts6` refuses a None
origin too (declaration or nothing), and this puts the refusal before the
run starts rather than after the CV has been paid for.
"""

from __future__ import annotations

from pathlib import Path

from engine.prospectivity.domain.ts6 import TS6Surface
from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.origin import DataOrigin
from engine.prospectivity.terrain.file_source import _require_declared
from engine.prospectivity.ts6.reference import TS6Reference

DEFAULT_SOURCE_ID = "src_ts6_grid"  # Contract 5's TS-6 grid entry ([18])
DEFAULT_ROLE_NOTE = "benchmark_only"  # Contract 6: the non-circular case


class FileTS6Reference(TS6Reference):
    """A TS-6 benchmark raster on disk, with its origin declared by the caller."""

    def __init__(
        self,
        raster_path: Path | str,
        *,
        data_origin: DataOrigin | str | None,
        title: str = "TS-6 benchmark surface",
        source_id: str = DEFAULT_SOURCE_ID,
        role_note: str = DEFAULT_ROLE_NOTE,
    ) -> None:
        self._raster_path = Path(raster_path)
        self._data_origin = _require_declared(data_origin, f"TS-6 raster {self._raster_path.name!r}")
        self._title = title
        self._source_id = source_id
        self._role_note = role_note

    def load(self) -> TS6Surface:
        path = self._raster_path
        if not path.is_file():
            raise FileNotFoundError(f"TS-6 raster {path} is not a file")
        return TS6Surface(
            title=self._title,
            source_id=self._source_id,
            raster_path=str(path),
            role_note=self._role_note,
            content_hash=file_sha256(path),
            data_origin=self._data_origin.value,
        )
