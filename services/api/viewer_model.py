"""The PRESENTATION MODEL the viewer renders (E5.3 commit 1) — the named
exception to E5.1's "the API computes nothing".

    catalog (E5.1)  ──► build_viewer_model() ──► GET /runs/{id}/viewer ──► apps/web/index.html
       grid.axes + labels           controls: one per declared axis, values with labels
       grid.cells / canonical       cells: state + the LABEL for that state (three, distinct)
       layers[].legend.*            layers: bins (rule named), colours, format, readout spec,
       layers[].data_url                    masked treatment, the uniformity note
       training_stations            stations, with THEIR origin (MEASURED), apart from the run's
       claim                        the verdict, passed through

WHY THIS IS NOT A BREACH OF E5.1'S RULE (Karl, 2026-08-23): that rule is
about DATA — the API computes no value, derives no measurement, re-hashes
nothing. Bins, labels and states are RENDERING DECISIONS. E5.1 already
crossed this line honestly with `uniform_today` — a derived fact about
recorded values served beside the counts it compares — and named it as
deriving SHAPE, not VALUE. Same distinction here, with three requirements:
(1) nothing below could be mistaken for a measurement; (2) the binning rule
is named in the model's own body (`binning_rule`); (3) nothing is written
back to the catalog — the catalog's `legend.binning` stays null. Do not
"fix" this by moving the logic into the page: the page would then
re-implement what the tests exercise, and the tests would observe nothing
the user sees (E5.3 §0).

WHAT IS GENERIC AND WHAT IS NOT. This module reads the axes, their values,
their labels, each layer's coordinates, ramp hint, format hint and legend
statistics FROM THE CATALOG — no layer type, model name, axis or unit is
named in this file, and `tests/test_viewer_model.py` asserts that a
catalog with different axes and layer types builds a model with no code
change. The generality stops one layer lower: `catalog.py`'s KINDS and
APPLICABLE_AXES are this project's (E5.3 §0.4) — the viewer is
catalog-driven; the catalog is not yet data-driven (BACKLOG §3).

THE ONE FORMULA THE PAGE MUST ALSO COMPUTE: a hovered (lon, lat) to a flat
index — `cell_index` below, three lines the page's JavaScript repeats on
mouse events because it cannot round-trip to the server per pixel. The
test pins this function against the raster's own georeferencing; the
page's copy is the stated duplication, and the only one.
"""

from __future__ import annotations

import math
from typing import Any

N_BINS = 7
BINNING_RULE = (
    f"equal-interval: {N_BINS} bins over the layer's RECORDED [min, max] (legend.min / legend.max, "
    "from the manifest); a constant layer gets one bin. Edges are presentation, never "
    "measurements, and are never written back to the catalog (legend.binning stays null)"
)
# A perceptually ordered sequential ramp (viridis-like) for value layers. The
# masked colour is chosen OUTSIDE it and outside the categorical palette — a
# test asserts that — so an undefined cell can never read as a value.
SEQUENTIAL_RAMP = ["#440154", "#443983", "#31688e", "#21918c", "#35b779", "#90d743", "#fde725"]
CATEGORICAL_PALETTE = ["#3b4252", "#88c0d0", "#ebcb8b", "#bf616a", "#a3be8c", "#b48ead"]
BACKGROUND = "#0b1020"
MASKED = {
    "label": "undefined (no covariates) — the mask, not a value",
    "color": "#6e6e6e",  # a flat grey in no ramp; drawn hatched by the page
    "pattern": "hatched",
    "note": "null in the export, NaN in the raster: the cell has no covariates; it is not zero and not the ramp's floor",
}
STATE_LABELS = {
    "present": "available",
    "not_applicable": "not an axis of this layer",
    "absent": "no artifact for this combination",
}
MESSAGES = {
    "api_unreachable": "Cannot reach the API at {api} — nothing was loaded. This is a connection failure, not an empty run.",
    "no_runs": "The API is reachable and serves no runs.",
    "no_layers": "This run has no layers: its catalog is empty.",
    "layer_missing": "Layer '{title}': its artifact could not be fetched (HTTP {status}). Not rendered — a broken layer, not an empty one.",
    "loading": "Loading…",
}


# ═══════════════════════════════ E5.4 — THE HONESTY SURFACE (Karl's decisions 3 and 4, 2026-08-23)
#
# Every banner string, reason list, failing set, expiry condition and
# explanation below is SERVED BY THIS MODEL and rendered verbatim by the page.
# E5.3's first draft composed option states in the page and shipped a wrong
# label invisible to every test — at LABEL stakes; a page composing its own
# verdict banner from raw manifest fields would repeat that at VERDICT stakes.
VERDICT_PERSISTENCE_RULE = (
    "visible without interaction and ACROSS RELOADS: no dismiss, no collapsed-by-default state, "
    "no override, nothing persisted — shown on every load where the map is"
)
NO_INFORMATION_STYLE = {
    "pattern": "diagonal-stripes",  # distinct from the mask's hatched grey: a stripe OVER the colour, not instead of it
    "stroke": "rgba(0,0,0,0.55)",
    "note": "drawn over the colour so the value is still visible under it; the mask replaces the colour, this overlays it",
    "contour": "not stroked: the hatched region's own edge is the one-fitted-range boundary; a stroke would add a polygon derivation with no new value",
}
DERIVATION_NOTE = (
    "shape-not-value (the bins precedent): a geometric function of RECORDED values — the training "
    "stations and the fitted range, both from the manifest through the catalog — computed in this "
    "tested model, never in the page, and never a measurement"
)
PAIRING_RULE = (
    "the map pixels are univariate BY CHOICE (Karl's decision 3, option (c)+); the pairing is protected "
    "by the single export file (E5.2), the readout that always carries the paired half with its "
    "semantics, the legend that always carries the paired range, and the absence of any suppression "
    "path in the page — nothing can hide it. Option (b), the paired spread as colour saturation, was "
    "considered and DECLINED: it would encode three different KINDS of spread as one visual channel, "
    "the cross-kind conflation the semantics string exists to prevent, made visual"
)


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d = math.radians(lon2 - lon1)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def _range_source(entries: list[dict]) -> tuple[str | None, dict | None]:
    """The first layer whose full-data fit records a range in km — generic:
    the field name is the catalog's, the layer is whichever carries it."""
    for e in entries:
        fit = e.get("full_data_fit") or {}
        if isinstance(fit.get("range_km"), (int, float)):
            return e["key"], fit
    return None, None


def no_information(grid: dict, stations: dict | None, range_km: float | None, predictable: list[bool] | None = None) -> list[bool] | None:
    """Per flat cell: True where the cell centre lies beyond `range_km` of
    EVERY station — the region where a distance-based model carries no
    information (E5.4 requirement 4). Masked cells (predictable False) are
    never marked: the mask is a different fact. None when the catalog
    carries no stations or no range."""
    if not stations or not stations.get("coordinates") or range_km is None or not grid:
        return None
    a, _, c, _, e, f = grid["transform"][:6]
    width, height = grid["width"], grid["height"]
    points = list(stations["coordinates"].values())
    out = []
    for row in range(height):
        lat = f + (row + 0.5) * e
        for col in range(width):
            i = row * width + col
            if predictable is not None and not predictable[i]:
                out.append(False)
                continue
            lon = c + (col + 0.5) * a
            out.append(all(_haversine_km(lon, lat, x, y) > range_km for x, y in points))
    return out


def verdict_block(claim: dict | None) -> dict | None:
    """The run banner's content: the CLAIM DESIGN's verdict with BOTH its
    failing and its passing sets named, a headline that discriminates in
    both directions, and every other design's verdict reachable."""
    if not claim or not claim.get("verdicts"):
        return None
    design = claim.get("design")
    v = (claim.get("verdicts") or {}).get(design) or {}
    failing, passing = list(v.get("failing") or []), list(v.get("passing") or [])
    n = len(failing) + len(passing)
    eligible = bool(v.get("eligible"))
    watermark = v.get("watermark")
    if eligible:
        headline = f"VALIDATED CLAIM on {design}: all {n} preconditions pass"
        if watermark:
            headline += f" — BUT the run is watermarked: {watermark}"
    else:
        headline = (f"NOT A VALIDATED CLAIM — {len(failing)} of {n} preconditions failed on {design}: "
                    + ", ".join(failing))
    return {
        "design": design,
        "eligible": eligible,
        "is_scientific": bool(v.get("is_scientific")),
        "headline": headline,
        "failing": failing,
        "passing": passing,
        "n_preconditions": n,
        "watermark": watermark,
        "discrimination_note": (
            "both halves are shown: a banner listing only failures cannot be told from a blanket refusal, "
            "and the day the facts change the banner's CHANGE is the whole point"
        ),
        "other_designs": {
            d: {"eligible": bool(x.get("eligible")), "failing": list(x.get("failing") or []), "passing": list(x.get("passing") or [])}
            for d, x in (claim.get("verdicts") or {}).items() if d != design
        },
        "persistence": VERDICT_PERSISTENCE_RULE,
        "applies_to": claim.get("applies_to"),
    }


def bin_edges(lo: float | None, hi: float | None, n: int = N_BINS) -> list[float]:
    if lo is None or hi is None:
        return []
    if hi <= lo:
        return [float(lo), float(hi)]
    return [float(lo + (hi - lo) * i / n) for i in range(n + 1)]


def cell_index(grid: dict, lon: float, lat: float) -> tuple[int, int, int] | None:
    """(row, col, flat index) of the cell containing (lon, lat) under the
    export's north-up affine transform [a, b, c, d, e, f]; None outside the
    grid. The page repeats these three lines on mouse events."""
    a, _, c, _, e, f = grid["transform"][:6]
    col = math.floor((lon - c) / a)
    row = math.floor((lat - f) / e)  # e < 0 for north-up
    if col < 0 or row < 0 or col >= grid["width"] or row >= grid["height"]:
        return None
    return row, col, row * grid["width"] + col


def _kind_axis(axes: dict, applicable: dict) -> str | None:
    """The axis whose values KEY the applicability table — generic: the first
    axis every one of whose values appears in `applicable_axes`. None when
    the catalog declares no applicability (every axis applies everywhere)."""
    for axis, values in axes.items():
        if values and all(str(v) in applicable or v in applicable for v in values):
            return axis
    return None


def _neighbours(axes: dict, applicable: dict, canonical: list[dict], cell: dict) -> dict:
    """For one canonical cell: the state the control panel should show for
    EVERY value of EVERY axis, were that one axis switched — computed here,
    in the tested module, never in the page (E5.3: the page's first draft
    probed cells itself, carried every axis value into the probe, and
    labelled a present layer 'absent'; found by looking, not by a test).
    Per axis, one entry per value IN THE CONTROL'S ORDER (the page looks up
    by option index, so no value has to be re-serialised in JavaScript)."""
    kind_axis = _kind_axis(axes, applicable)
    coords = cell["coordinates"]
    def find(probe: dict) -> dict | None:
        for c in canonical:
            if all(c["coordinates"].get(a) == probe.get(a) for a in axes):
                return c
        return None
    out = {}
    for axis, values in axes.items():
        entries = []
        for v in values:
            probe_kind = v if axis == kind_axis else coords.get(kind_axis)
            applies = applicable.get(str(probe_kind), applicable.get(probe_kind, list(axes))) if kind_axis else list(axes)
            if kind_axis and axis != kind_axis and axis not in applies:
                # switching an axis that is not an axis of this kind: not applicable; the
                # layer stays the cell's own
                entries.append({"state": "not_applicable", "key": cell.get("key")})
                continue
            probe = {a: (v if a == axis else coords.get(a)) for a in axes}
            for a in axes:
                if kind_axis and a != kind_axis and a not in applies:
                    probe[a] = None  # not an axis of the probed kind: the canonical cell carries None there
            hit = find(probe)
            if hit is not None:
                entries.append({"state": hit["state"], "key": hit.get("key")})
            elif axis == kind_axis:
                # another kind whose applicable coordinates this cell does not fix: the
                # first present canonical cell of that kind, so the control can switch kinds
                first = next((c for c in canonical if c["coordinates"].get(kind_axis) == v and c["state"] == "present"), None)
                entries.append({"state": "present" if first else "absent", "key": first.get("key") if first else None, "snap": bool(first)})
            else:
                entries.append({"state": "absent", "key": None})
        out[axis] = entries
    return out


def _title(entry: dict, value_labels: dict) -> str:
    coords = entry["coordinates"]
    parts = []
    for axis, value in coords.items():
        if value is None:
            continue
        label = value_labels.get(axis, {}).get(str(value), str(value))
        parts.append(label)
    return " · ".join(parts)


def _layer(entry: dict, catalog: dict, value_labels: dict, by_key: dict[str, dict]) -> dict:
    legend = entry.get("legend") or {}
    ramp = legend.get("ramp") or "sequential"
    fmt = legend.get("format") or {"kind": "number", "decimals": 2, "unit_label": legend.get("units") or ""}
    if ramp == "categorical":
        labels = (fmt.get("labels") or {}) if fmt.get("kind") == "code" else {}
        codes = [k for k in labels if k != "null"]
        bins = [{"value": float(code), "label": labels[code], "color": CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)]} for i, code in enumerate(codes)]
        edges = None
    else:
        edges = bin_edges(legend.get("min"), legend.get("max"))
        bins = [{"from": edges[i], "to": edges[i + 1], "color": SEQUENTIAL_RAMP[min(i, len(SEQUENTIAL_RAMP) - 1)]} for i in range(max(len(edges) - 1, 0))]
    # the pair: the other half's entry, so the readout always has both fields
    pair = entry.get("pair")
    # THE PAIRED HALF (generic: whatever the catalog pairs this entry with — here a value
    # with its paired spread; the catalog's field names for the semantics are read by name)
    paired = None
    if pair:
        halves = {k: v for k, v in pair.items()}
        other_key = next((v for k, v in halves.items() if v != entry["key"]), None)
        other = by_key.get(other_key) if other_key else None
        if other is not None:
            paired = {
                "label": other["legend"].get("quantity") or other["kind"],
                "field": other["data_field"],
                "semantics": other.get("uncertainty_semantics") or entry.get("uncertainty_semantics"),
                "method": other.get("uncertainty_method") or entry.get("uncertainty_method"),
                "note": "always shown with the value: the pair is structural (one export file holds both)",
            }
    uniform = legend.get("uniform_today")
    # THE LAYER'S OWN REASONS, in its own form (E5.1's asymmetry holds under pressure to normalise):
    # a reason given as a string is served verbatim with "expiry: stated in the reason" — no
    # parsing, no invented field; reasons given per reason carry their own lifted_by.
    if entry.get("watermark_reasons") is not None:
        reasons = [{"reason": r.get("reason"), "lifted": bool(r.get("lifted")), "lifted_by": r.get("lifted_by"), "cause": r.get("cause"), "expiry": r.get("lifted_by")}
                   for r in entry["watermark_reasons"]]
    elif entry.get("watermark"):
        reasons = [{"reason": "terrain", "lifted": entry.get("data_origin") == "MEASURED", "text": entry["watermark"],
                    "expiry": "stated in the reason text"}]
    else:
        reasons = []
    fit = entry.get("full_data_fit")
    fit_facts = {k: v for k, v in (fit or {}).items() if isinstance(v, (int, float, str, bool)) and not isinstance(v, bool) or isinstance(v, bool)} if fit else None
    paired_legend = None
    if paired is not None and other is not None:
        ol = other.get("legend") or {}
        paired_legend = {"label": paired["label"], "min": ol.get("min"), "max": ol.get("max"), "method": paired["method"],
                         "semantics": paired["semantics"], "rule": "always shown beside the value's bins; no path hides it"}
    return {
        "key": entry["key"],
        "full_data_fit": fit,  # E5.4: the pass-through the catalog carried and the model dropped
        "honesty": {
            "data_origin": entry.get("data_origin"),
            "publishable": entry.get("publishable"),
            "watermark_form": entry.get("watermark_form"),
            "reasons": reasons,
            "n_reasons": len(reasons),
            "fit_facts": fit_facts,
            "uniform": None if uniform is None else {
                "flag": bool(uniform),
                "statement": (catalog.get("uniformity_today") or {}).get("statement"),
                "facts": {k: v for k, v in legend.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
                "meaning": legend.get("meaning"),
            },
        },
        "paired_legend": paired_legend,
        "title": _title(entry, value_labels),
        "kind": entry["kind"],
        "coordinates": entry["coordinates"],
        "data_url": entry.get("data_url"),
        "data_field": entry.get("data_field"),
        "ramp": ramp,
        "bins": bins,
        "edges": edges,
        "format": fmt,
        "legend_title": legend.get("quantity") or entry.get("kind"),
        "legend_stats": {k: legend.get(k) for k in ("min", "max", "n_predicted", "n_masked", "n_distinct_values") if k in legend},
        "readout": {
            "value_label": legend.get("quantity") or entry.get("kind"),
            "value_field": entry.get("data_field"),
            "paired": paired,
            "coordinate_format": {"decimals": 3, "order": "lon, lat (EPSG:4326)"},
            "masked_label": MASKED["label"],
        },
        "masked": MASKED,
        "data_origin": entry.get("data_origin"),
        "publishable": entry.get("publishable"),
        "watermark_form": entry.get("watermark_form"),
        "watermark": entry.get("watermark"),
        "watermark_reasons": entry.get("watermark_reasons"),
        "uniform_today": None if uniform is None else {
            "flag": bool(uniform),
            "note": (catalog.get("uniformity_today") or {}).get("statement"),
            # every numeric fact the catalog recorded on the legend, generically — the
            # names are the catalog's, not this module's
            "facts": {k: v for k, v in legend.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
            "meaning": legend.get("meaning"),
        },
    }


def range_source_key(catalog: dict) -> str | None:
    """Which layer's export the API should read for the per-cell mask (E5.4):
    the layer whose full-data fit records the range."""
    key, _ = _range_source(catalog.get("layers") or [])
    return key


def build_viewer_model(catalog: dict, predictable: list[bool] | None = None, export_grid: dict | None = None) -> dict:
    """The presentation model for one run's catalog. Pure: reads the catalog,
    never mutates it, names every rendering rule it applies."""
    grid = catalog.get("grid") or {}
    axes: dict[str, list] = grid.get("axes") or {}
    axis_labels = grid.get("axis_labels") or {a: a for a in axes}
    value_labels = grid.get("value_labels") or {}
    controls = [
        {
            "axis": axis,
            "label": axis_labels.get(axis, axis),
            "values": [{"value": v, "label": value_labels.get(axis, {}).get(str(v), str(v) if not isinstance(v, list) else " → ".join(map(str, v)))} for v in values],
        }
        for axis, values in axes.items()
    ]
    cells = [
        {**cell, "label": STATE_LABELS[cell["state"]]}
        for cell in (grid.get("cells") or [])
    ]
    canonical_cells = (grid.get("canonical") or {}).get("cells") or []
    canonical = [
        {**cell, "label": STATE_LABELS[cell["state"]],
         "neighbours": _neighbours(axes, grid.get("applicable_axes") or {}, canonical_cells, cell)}
        for cell in canonical_cells
    ]
    entries = catalog.get("layers") or []
    by_key = {e["key"]: e for e in entries}
    layers = {e["key"]: _layer(e, catalog, value_labels, by_key) for e in entries}
    stations = catalog.get("training_stations")
    # E5.4 requirement 4 — THE NO-INFORMATION REGION, derived from recorded values only
    range_key, range_fit = _range_source(entries)
    no_info = None
    if range_key and range_fit and stations:
        rk = float(range_fit["range_km"])
        at_ceiling = bool(range_fit.get("range_at_candidate_ceiling"))
        # the GRID (transform, width, height) and the per-cell MASK both come from the
        # range-source layer's export — recorded values the API reads and hands in; the
        # model names no catalog field for them. Without them nothing is derived.
        ni_cells = no_information(export_grid, stations, rk, predictable) if export_grid and export_grid.get("transform") else None
        if ni_cells is not None:
            n_marked = sum(ni_cells)
            n_pred = sum(predictable) if predictable is not None else None
            bound = "; a LOWER BOUND — the fit sat at the candidate ceiling" if at_ceiling else ""
            no_info = {
                "cells": ni_cells,
                "n_marked": n_marked,
                "n_predictable": n_pred,
                "n_cells": len(ni_cells),
                "count_label": (f"{n_marked:,} of {n_pred:,} predictable cells" if n_pred is not None
                                else f"{n_marked:,} of {len(ni_cells):,} grid cells (the mask not separated: no per-cell mask was supplied)"),
                "range_km": rk,
                "range_at_candidate_ceiling": at_ceiling,
                "source": {"layer": range_key, "field": "full_data_fit.range_km", "from": "the manifest, through the catalog — never recomputed here"},
                "direction": ("at the candidate ceiling the TRUE range is at least the fitted one, so the informed region is at least as large as "
                              "drawn — marking beyond-fitted-range as no-information overstates ignorance, the CONSERVATIVE direction for claims")
                             if at_ceiling else "the fitted range",
                "label_range_layer": (f"beyond one fitted variogram range ({rk:.1f} km{bound}) of every station: this model carries no "
                                      f"information here; {n_marked:,} of {n_pred:,} predictable cells. Drawn at its largest defensible extent."
                                      if n_pred is not None else
                                      f"beyond one fitted variogram range ({rk:.1f} km{bound}) of every station: this model carries no "
                                      f"information here; {n_marked:,} of {len(ni_cells):,} grid cells. Drawn at its largest defensible extent."),
                "label_other_layers": (f"no station within {rk:.1f} km (the fitted range of {_title(by_key[range_key], value_labels)}): "
                                       "spatial support is absent here for any model — distance to data is not this layer's information measure, and no variogram is implied"),
                "derivation": DERIVATION_NOTE,
                "style": NO_INFORMATION_STYLE,
                "default_on": True,
                "rule": "default ON for every layer; the mask (null cells) is a different fact and is never marked here",
            }
    for key, layer in layers.items():
        if no_info is None:
            layer["no_information"] = None
            continue
        is_range_layer = (layer["coordinates"].get(next(iter(layer["coordinates"]), "")) is not None
                          and by_key[key].get("full_data_fit", {}) is by_key[range_key].get("full_data_fit", {}))
        same_fit = (by_key[key].get("full_data_fit") or {}).get("range_km") == range_fit["range_km"] and "range_km" in (by_key[key].get("full_data_fit") or {})
        layer["no_information"] = {
            "label": no_info["label_range_layer"] if same_fit else no_info["label_other_layers"],
            "is_range_source": same_fit,
            "n_marked": no_info["n_marked"],
            "n_predictable": no_info["n_predictable"],
            "count_label": no_info["count_label"],
            "range_km": rk,
            "range_at_candidate_ceiling": at_ceiling,
            "direction": no_info["direction"],
            "source": no_info["source"],
            "derivation": DERIVATION_NOTE,
            "style": NO_INFORMATION_STYLE,
            "default_on": True,
        }
    return {
        "run_id": catalog.get("run_id"),
        "content_hash": catalog.get("content_hash"),
        "exception_note": (
            "A PRESENTATION model (Karl, 2026-08-23): bins, labels and states are rendering decisions, "
            "not data — the same shape-not-value distinction as the catalog's uniform_today. Nothing "
            "here is a measurement; the binning rule is named below; nothing is written back to the catalog."
        ),
        "binning_rule": BINNING_RULE,
        "controls": controls,
        # E5.4 requirement 1: the run banner's content — the claim design's verdict, both halves
        "verdict": verdict_block(catalog.get("claim")),
        # E5.4 requirement 4: the per-cell no-information flags (one grid, every layer) and the rules
        "no_information": no_info,
        "pairing_rule": PAIRING_RULE,
        "applicable_axes": grid.get("applicable_axes") or {},
        "state_labels": dict(STATE_LABELS),
        "cells": cells,
        "canonical": canonical,
        "n_layers": len(layers),
        "layers": layers,
        "masked": MASKED,
        "background": BACKGROUND,
        "messages": dict(MESSAGES),
        "stations": None if not stations else {
            "n": stations.get("n"),
            "data_origin": stations.get("data_origin"),
            "origin_note": stations.get("origin_note"),
            "coord_columns": stations.get("coord_columns"),
            "coordinates": stations.get("coordinates"),
            "asymmetry_note": (
                f"the stations are {stations.get('data_origin')}; the surface they sit on is {catalog.get('data_origin')} — "
                "drawn apart on purpose: the clearest single statement of what this project has and has not got"
            ),
            # E5.3 commit 3: what the legend says beside the station swatch — BOTH origins, so the
            # asymmetry is in the legend and not only in the panel
            "legend_label": (
                f"{stations.get('n')} training stations — origin {stations.get('data_origin')} "
                f"(the surface is {catalog.get('data_origin')})"
            ),
            "style": {"kind": "point", "fill": "#ffffff", "outline": "#000000", "radius_px": 4,
                      "note": "a point with an outline, never a ramp colour: a station is a place, not a value"},
            "readout": {"label": "training station", "fields": ["id", "lon", "lat"], "origin_suffix": f"origin {stations.get('data_origin')}"},
            "geometry_note": (
                "the clustering (two groups ~991 km apart; zero pairs between 13 and 986 km — E2.4) is VISIBLE here as "
                "drawn points; the number itself is not computed by this model (E5.5's BACKLOG entry: derive vs record, E5.4 decides)"
            ),
        },
        "claim": catalog.get("claim"),
        "watermark_asymmetry": catalog.get("watermark_asymmetry"),
        "uniformity_today": catalog.get("uniformity_today"),
        # the grid identity is NOT repeated here: the page reads each export's own
        # `grid` block, and naming the catalog's field would name this project
        "run_data_origin": catalog.get("data_origin"),
    }
