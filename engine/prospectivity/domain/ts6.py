"""TS6Surface — the digitized TS-6 2010 benchmark raster (Contract 6)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TS6Surface(BaseModel):
    """Mirrors data/ts6/ts6_reference.yaml's `ts6_reference` block.

    `role_note` is load-bearing, not decorative: "benchmark_only" means the
    comparison in compare_to_ts6() is an independent check; "reproduction_check"
    means TS-6's own grid also fed the training samples, so the comparison must
    be labeled circular rather than presented as validation (see Contract 6 and
    the "circular validation" risk in the alpha proposal).
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    source_id: str
    raster_path: str
    unit: str = "kg_m2"
    crs: str = "EPSG:4326"
    role_note: str | None = None  # "benchmark_only" | "reproduction_check"
    content_hash: str | None = None
    # The raster's DECLARED origin class (E3.3, mirroring Contract 6 v3's
    # `raster_data_origin`): the fixture declares SYNTHETIC; the real
    # digitized surface is DERIVED — a raster WE compute from a published
    # figure by a recorded procedure. None is "undeclared", which the
    # comparison REFUSES rather than defaults (declaration or nothing).
    data_origin: str | None = None
