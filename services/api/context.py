"""CONTEXT LAYERS (E5.3 commit 2) — the capability; the real data is a separate task.

A SECOND CLASS OF LAYER: geometry that is NOT a run artifact — the CCZ
management-area boundary, ISA contract areas, APEIs, the coastline. They are
not produced by a run, so they have no control-axis coordinates, no watermark
reasons and no claim verdict; putting one in the catalog would break E5.1's
both-directions test (every entry corresponds to an artifact THIS RUN
produced). They are served separately: GET /context (the registry, no
geometry) and GET /context/{id} (the file's bytes, ETag = its sha256).

    context registry (this module)          the page
    ┌────────────────────────────────┐      ┌───────────────────────────────┐
    │ id · file · sha256 · data_origin│ ───► │ checkbox per layer: shown /    │
    │ citation · license · style      │      │ hidden / unavailable (3 states)│
    │ attribution_text                │      │ outline only — never a ramp    │
    └────────────────────────────────┘      │ citation beside the checkbox   │
                                            └───────────────────────────────┘

THEY CARRY THEIR OWN ORIGIN, declared here and distinct from any run's. A
downloaded ISA boundary is not SYNTHETIC and must NEVER inherit a surface's
watermark — a real boundary over a synthetic surface is the MEASURED-
stations-over-SYNTHETIC-surface asymmetry again, worth showing for the same
reason. A registry entry therefore has no `watermark` and no `claim`
field at all, and the test asserts their absence by name.

RENDERED AS GEOMETRY, NOT DATA: outline, no fill, no colour ramp — visually
incapable of being mistaken for a value layer (GFW draws the CCZ in white
outline over the heatmap; that separation is the point).

ATTRIBUTION IS PART OF THE LAYER: each entry's `attribution_text` is shown
beside its checkbox and in the footer — where a user sees it, not only here.

THE FIXTURE IS GONE (G.2, 2026-08-25). It was a RECTANGLE at the published
approximate extent, declared AUTHORED and titled FIXTURE so it could not be
mistaken for the boundary. The real polygon has landed as Contract 2's AOI,
and this registry now points AT THAT FILE — so the map draws the AOI the run
was given rather than a second copy of it. The remaining half of the original
acquisition — the ISA shapefiles (exploration areas, reserved areas, APEIs:
ISA copyright; ISBA/17/LTC/7, ISBA/18/C/22, ISBA/26/C/58, ISBA/26/C/43) — is
still its own task, and the exclusions.geojson decision rides on it (BACKLOG).

THE SCALE SURPRISE, RE-MEASURED against the real polygon (G.2; the earlier
figures compared the CCZ's BOUNDING BOX with the prediction EXTENT, which
flattered both sides): the AOI polygon is 11,399,939 km² — its bounding box
is 13,726,806, so the box overstates the zone by 20 % — and the run's
PREDICTABLE domain is 346,927 km² (2,880 cells; the extent box is 409,553).
Polygon against predictable domain: 32.9×, i.e. the domain this project can
speak about is 3.04 % of the zone. Drawing the boundary makes that visible.
It is honest; the view is not adjusted to hide it.

WHERE THEY LIVE: apps/web/context/ (the fixture) and apps/web/ (the
coastline) — outside the origin audit's walk, which is why the declaration
is recorded HERE and checked at startup: every file's sha256 must equal the
recorded one, and a GeoJSON that declares an origin in-file must declare the
registry's. The real layers, when committed under data/context/, enter the
walk and must declare in-file (a .geojson's top-level `data_origin`) — the
cost E5.7 / the data task inherits.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.prospectivity.provenance.contract_versions import file_sha256
from engine.prospectivity.provenance.origin import DataOrigin
from services.api.web import COASTLINE, WEB_DIR

CONTEXT_DIR = WEB_DIR / "context"
# Contract 2's own file: the AOI is a context layer AND the coverage
# denominator, and pointing at one file keeps those from drifting apart.
AOI_PATH = Path(__file__).resolve().parents[2] / "data" / "aoi" / "study_area.geojson"

CONTEXT_LAYERS: tuple[dict, ...] = (
    {
        "id": "coastline",
        "title": "Coastline (Natural Earth 1:110m)",
        "path": WEB_DIR / COASTLINE["file"],
        "sha256": COASTLINE["sha256"],
        "bytes": COASTLINE["bytes"],
        "data_origin": COASTLINE["data_origin"],
        "citation": COASTLINE["citation"],
        "license": COASTLINE["license"],
        "attribution_text": COASTLINE["attribution_text"],
        "style": {"kind": "outline", "color": "#d0d6e6", "width": 0.8},
        "default_on": True,
        "declared_in_file": False,  # vendored verbatim; its hash IS the record
        "fixture": False,
    },
    {
        # G.2 (2026-08-25): THE REAL BOUNDARY, and it is THE AOI ITSELF — the
        # path points at Contract 2's own file rather than at a copy under
        # apps/web/. The viewer therefore draws the polygon THE RUN WAS GIVEN,
        # not a look-alike of it (E5.3's stations-from-the-manifest rule, one
        # layer over), and the repo holds two copies of these coordinates
        # instead of three. The file is inside the origin audit's walk and
        # declares LITERATURE in-file, so `declared_in_file` below is checked
        # against a real declaration rather than a registry echo.
        "id": "ccz_management_area",
        "title": "CCZ management area (Marine Regions MRGID 64222)",
        "path": AOI_PATH,
        "sha256": "sha256:d8663e5b36814f25cb803a7b540ee62ea118a5156c569029450979f43b749e91",
        "bytes": 152_569,
        "data_origin": DataOrigin.LITERATURE.value,
        "author": None,
        "citation": (
            "International Seabed Authority (2023), geographical limits of the CCZ management area — "
            "ISBA/17/LTC/7, ISBA/18/C/22, ISBA/26/C/58, ISBA/26/C/43; digitised and redistributed by "
            "Marine Regions (Flanders Marine Institute) as MRGID 64222, retrieved 2026-08-25. Ledger "
            "row: src_ccz_boundary_marineregions"
        ),
        "license": "CC-BY 4.0 (Marine Regions); underlying limits are ISA's",
        "attribution_text": "CCZ management area: Marine Regions MRGID 64222 (CC-BY 4.0), from ISA limits ISBA/17/LTC/7 et seq.",
        "style": {"kind": "outline", "color": "#ffffff", "width": 1.2},
        "default_on": True,
        "declared_in_file": True,
        "fixture": False,
    },
)

STATES = {"shown": "shown", "hidden": "hidden (off is not gone: the layer is still loaded)", "unavailable": "unavailable (its file could not be fetched)"}


class ContextLayerError(ValueError):
    """A context layer whose file, hash or declaration does not match its registry entry."""


def verify_context_layers(layers=CONTEXT_LAYERS) -> list[dict]:
    """Every registered file exists, hashes to the recorded value, and — when
    it declares an origin in-file — declares the registry's. Returns the
    public records (no paths, no geometry)."""
    public = []
    ids = [layer["id"] for layer in layers]
    if len(ids) != len(set(ids)):
        raise ContextLayerError(f"context layer ids repeat: {ids}")
    for layer in layers:
        path = Path(layer["path"])
        if not path.is_file():
            raise ContextLayerError(f"context layer {layer['id']!r}: {path} is not a file")
        digest = file_sha256(path)
        if digest != layer["sha256"]:
            raise ContextLayerError(
                f"context layer {layer['id']!r}: {path.name} hashes to {digest}, the registry records "
                f"{layer['sha256']} — the file changed without its record"
            )
        DataOrigin(layer["data_origin"])  # a member, or refused
        if layer.get("declared_in_file"):
            declared = json.loads(path.read_text()).get("data_origin")
            if declared != layer["data_origin"]:
                raise ContextLayerError(
                    f"context layer {layer['id']!r}: the file declares data_origin {declared!r}, the registry "
                    f"{layer['data_origin']!r} — one declaration, not two"
                )
        for forbidden in ("watermark", "watermark_reasons", "claim", "coordinates"):
            if forbidden in layer:
                raise ContextLayerError(f"context layer {layer['id']!r} carries {forbidden!r} — a run artifact's field on context geometry")
        public.append({
            k: layer[k] for k in ("id", "title", "sha256", "bytes", "data_origin", "citation", "license", "attribution_text", "style", "default_on", "fixture")
        } | {"author": layer.get("author"), "url": f"/context/{layer['id']}", "file": path.name,
             "class": "context geometry — not a run artifact: no control-axis coordinates, no watermark reasons, no claim verdict; its own origin and citation"})
    return public


def context_file(layer_id: str, layers=CONTEXT_LAYERS) -> tuple[Path, str]:
    for layer in layers:
        if layer["id"] == layer_id:
            return Path(layer["path"]), layer["sha256"]
    raise KeyError(layer_id)
