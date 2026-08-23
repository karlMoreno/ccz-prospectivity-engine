"""The LAYER CATALOG (E5.1 commit 2) — what the viewer reads to discover the
layers of one run. RESOLVED FROM THE MANIFEST, never from a directory listing
and never by parsing a filename (E4.2 built the association record for
exactly this; TAX.1 refused name-inference once already).

    manifest.surfaces[est]            ──► 2 entries per estimator (prediction, uncertainty),
      .rasters.{prediction,uncertainty}    each naming its PAIR — the pairing rule is
      .mu_min/mu_max/sd_min/sd_max         structural in the code (E2.1) and stays so here
      .watermark (ONE reason, a string)
    manifest.economics.rasters[file]  ──► 18 entries: kind · scenario | pair · estimator · z
      .counts · .watermark{terrain, economic_parameters}   (TWO reasons, per reason)
    manifest.economics.scenarios[]    ──► the cutoff WITH its origin; each reason's cause + expiry
    manifest.claim                    ──► the verdict, ONCE: the guard's unit is (run, design), E3.1+2 §3
    <association record>             ──► the encodings and the difference's MEANING sentence
                                          (named by economics.association.file; hashed in the chain)

THREE SHAPE DECISIONS E5.0 §1 ESTABLISHED:

1. NOT-APPLICABLE IS A THIRD STATE. The naive cross-product kind × estimator
   × z × scenario-or-pair is 72 cells; 24 artifacts exist; the other 48 are
   INAPPLICABLE — a prediction has no z-axis and no scenario axis, a
   footprint has no pair, a difference has no single scenario — and none is
   MISSING. `grid` serves every cell with one of three states, so E5.3's
   control panel can say "not an axis of this layer" where a two-state model
   would say "no artifact". ABSENT is reserved for a cell whose axes apply
   and whose artifact the record does not name.

2. THE WATERMARK ASYMMETRY IS BY DESIGN AND IS NOT TIDIED. Surfaces carry ONE
   reason (terrain) as a string; economics rasters carry TWO, per reason,
   with expiry conditions. No second reason is invented for surfaces and
   the two are not collapsed — each entry names its `watermark_form`, and
   the catalog says once why the forms differ.

3. EIGHTEEN OF THE TWENTY-FOUR RASTERS ARE UNIFORM today, and the catalog
   carries the recorded FACTS that explain it — n_minable == n_predictable,
   difference_fraction_of_predictable = 0.0, the meaning sentence — so E5.4
   can say why instead of the viewer looking broken. Served, not computed.

WHAT IS NOT HERE, on purpose: legend BINNING (a viewer choice — E5.0 §3;
the rule is E5.3's to state, and a bin computed silently here would be a
second source of truth), and the per-cell values (E5.2's export).
"""

from __future__ import annotations

import json
from pathlib import Path

KINDS = ("prediction", "uncertainty", "footprint", "difference")
# Which axes APPLY to which kind — the applicability rule, stated once.
APPLICABLE_AXES: dict[str, tuple[str, ...]] = {
    "prediction": ("estimator",),
    "uncertainty": ("estimator",),
    "footprint": ("estimator", "z", "scenario"),
    "difference": ("estimator", "z", "pair"),
}
STATE_RULE = (
    "present: the record names an artifact at these coordinates; not_applicable: at least "
    "one coordinate is not an axis of this kind (a prediction has no z and no scenario; a "
    "footprint has no pair; a difference has no single scenario); absent: every coordinate "
    "applies and the record names no artifact — a broken promise if a control offers it"
)
WATERMARK_ASYMMETRY = (
    "BY DESIGN, not normalised: a surface's watermark is ONE reason (terrain — the covariates "
    "are computed on a synthetic DEM; lifts at Checkpoint 1) carried as a string; an economics "
    "raster carries TWO INDEPENDENT reasons with SEPARATE expiry conditions (terrain ↔ "
    "Checkpoint 1; economic_parameters ↔ Checkpoint 4) because fixing one leaves the other. "
    "A second reason for surfaces would be invented; one reason for economics would be lossy."
)
EXCLUSIONS: tuple[dict[str, str], ...] = (
    {"pattern": "run_manifest.json", "reason": "the root record, served at /manifest — not a layer"},
    {"pattern": "<estimator>.provenance.json", "reason": "carrier 2 of a surface (its sidecar) — served at /files/<key>, not a layer"},
    {"pattern": "data_origin.yaml", "reason": "the origin audit's marker sidecar for the rasters beside it — not a layer"},
    {"pattern": "economics/data_origin.yaml", "reason": "the same, for the economics rasters"},
    {"pattern": "economics/economics.footprints.json", "reason": "E4.2's association record — what the economics entries RESOLVE FROM, not a layer"},
    {"pattern": "features/stack/*", "reason": "the covariate stack the surfaces were predicted on: SYNTHETIC covariates, one artifact by the stack hash, not a viewer layer (E5.0 §1)"},
)


def _surface_entries(manifest: dict) -> list[dict]:
    entries = []
    surfaces = manifest.get("surfaces") or {}
    output_hashes = manifest.get("output_hashes") or {}
    for est in sorted(surfaces):
        block = surfaces[est]
        files = {kind: block["rasters"][kind]["file"] for kind in ("prediction", "uncertainty")}
        for kind in ("prediction", "uncertainty"):
            key = files[kind]
            legend = (
                {"min": block.get("mu_min"), "max": block.get("mu_max"), "quantity": "predicted abundance, kg/m² (mu)"}
                if kind == "prediction"
                else {"min": block.get("sd_min"), "max": block.get("sd_max"), "quantity": "paired uncertainty (sd) — " + str(block.get("uncertainty_method"))}
            )
            entries.append({
                "key": key,
                "sha256": block["rasters"][kind]["sha256"],
                "recorded_in": f"surfaces.{est}.rasters.{kind}",
                "kind": kind,
                "coordinates": {"kind": kind, "estimator": est, "z": None, "scenario": None, "pair": None},
                "axes_not_applicable": [a for a in ("z", "scenario", "pair") if a not in APPLICABLE_AXES[kind]],
                "pair": {"prediction": files["prediction"], "uncertainty": files["uncertainty"]},
                "pairing_note": "prediction and uncertainty are one structural pair (Estimator.predict, E2.1); neither is shown without the other",
                "data_origin": block.get("data_origin"),
                "publishable": block.get("publishable"),
                "watermark_form": "surface: one reason (terrain), a string",
                "watermark": block.get("watermark"),
                "watermark_reasons": None,  # NOT invented — see WATERMARK_ASYMMETRY
                "uncertainty_method": block.get("uncertainty_method"),
                "uncertainty_semantics": block.get("uncertainty_semantics"),
                "legend": {**legend, "units": "kg_m2", "n_predicted": block.get("n_predicted"), "n_masked": block.get("n_masked"),
                           "n_distinct_values": block.get("n_distinct_values"), "binning": None,
                           "binning_note": "a viewer choice, not recorded (E5.0 §3) — E5.3 states its rule"},
                "full_data_fit": block.get("full_data_fit"),
                "sidecar": block.get("sidecar"),
                "_hashed_under": key if key in output_hashes else None,
            })
    return entries


def _economics_entries(manifest: dict, record: dict) -> list[dict]:
    economics = manifest.get("economics") or {}
    rasters = economics.get("rasters") or {}
    scenarios = {s["name"]: s for s in economics.get("scenarios") or []}
    output_hashes = manifest.get("output_hashes") or {}
    causes = {}
    for name, s in scenarios.items():
        causes[name] = {r["reason"]: r for r in (s.get("watermark") or {}).get("reasons") or []}
    entries = []
    for file in sorted(rasters):
        r = rasters[file]
        kind = r["kind"]
        key = f"economics/{file}"
        scenario, pair = r.get("scenario"), r.get("pair")
        # the per-reason verdict AS RECORDED, with each reason's cause from the scenario block
        reasons = []
        for reason, state in (r.get("watermark") or {}).items():
            cause_src = causes.get(scenario) if scenario else (causes.get((pair or [None])[1]) or causes.get((pair or [None])[0]))
            cause = (cause_src or {}).get(reason, {}).get("cause")
            reasons.append({"reason": reason, "lifted": state.get("lifted"), "lifted_by": state.get("lifted_by"), "cause": cause})
        counts = r.get("counts") or {}
        if kind == "footprint":
            legend = {"encoding": record.get("footprint_encoding"), "values": [0.0, 1.0], "n_minable": counts.get("n_minable"),
                      "n_predictable": counts.get("n_predictable"), "fraction_of_predictable": counts.get("fraction_of_predictable"),
                      "area_m2": counts.get("area_m2"), "uniform_today": counts.get("n_minable") == counts.get("n_predictable")}
            cutoff = (scenarios.get(scenario) or {}).get("cutoff")
        else:
            legend = {"encoding": record.get("difference_encoding"), "values": [0.0, 1.0, 2.0, 3.0], **{k: counts.get(k) for k in ("both", "neither", "only_a", "only_b", "undefined")},
                      "difference_fraction_of_predictable": counts.get("difference_fraction_of_predictable"), "area_m2": counts.get("area_m2"),
                      "meaning": record.get("difference_meaning"), "uniform_today": counts.get("only_a") == 0 and counts.get("only_b") == 0 and counts.get("neither") == 0}
            cutoff = {name: (scenarios.get(name) or {}).get("cutoff") for name in (pair or [])}
        entries.append({
            "key": key,
            "sha256": r.get("sha256"),
            "recorded_in": f"economics.rasters.{file}",
            "kind": kind,
            "coordinates": {"kind": kind, "estimator": r.get("estimator"), "z": r.get("z"), "scenario": scenario, "pair": pair},
            "axes_not_applicable": [a for a in ("z", "scenario", "pair") if a not in APPLICABLE_AXES[kind]],
            "pair": None,
            "data_origin": (scenarios.get(scenario) or scenarios.get((pair or [None])[0]) or {}).get("data_origin"),
            "publishable": False,
            "watermark_form": "economics: two independent reasons, per reason, each with its expiry condition",
            "watermark": None,
            "watermark_reasons": reasons,
            "cutoff": cutoff,
            "legend": {**legend, "units": "kg_m2 cutoff; raster values are codes", "binning": None, "binning_note": "categorical — the encoding IS the legend"},
            "_hashed_under": key if key in output_hashes else None,
        })
    return entries


def _grid(manifest: dict, entries: list[dict]) -> dict:
    registry = list((manifest.get("inputs") or {}).get("registry") or [])
    economics = manifest.get("economics") or {}
    scenarios = [s["name"] for s in economics.get("scenarios") or []]
    z_levels = sorted({float(z) for s in economics.get("scenarios") or [] for z in s.get("confidence_levels") or []})
    pairs = [list(p) for p in {tuple(e["coordinates"]["pair"]) for e in entries if e["coordinates"]["pair"]}]
    pairs.sort()
    present = {}
    for e in entries:
        c = e["coordinates"]
        present[(c["kind"], c["estimator"], c["z"], c["scenario"], tuple(c["pair"]) if c["pair"] else None)] = e["key"]
    cells = []
    # the cross-product over ONE "scenario-or-pair" axis: each scenario and each pair is a value
    scenario_axis = [("scenario", s) for s in scenarios] + [("pair", tuple(p)) for p in pairs]
    for kind in KINDS:
        for est in registry:
            for z in z_levels:
                for axis_name, axis_value in scenario_axis:
                    applicable = APPLICABLE_AXES[kind]
                    inapplicable = [a for a, v in (("z", z), (axis_name, axis_value)) if a not in applicable]
                    coords = {"kind": kind, "estimator": est, "z": z, "scenario": axis_value if axis_name == "scenario" else None,
                              "pair": list(axis_value) if axis_name == "pair" else None}
                    if inapplicable:
                        state, key = "not_applicable", None
                        # the ONE artifact these inapplicable coordinates collapse onto, if any
                        lookup = (kind, est, z if "z" in applicable else None,
                                  axis_value if (axis_name == "scenario" and "scenario" in applicable) else None,
                                  axis_value if (axis_name == "pair" and "pair" in applicable) else None)
                        key = present.get(lookup)
                    else:
                        lookup = (kind, est, z, axis_value if axis_name == "scenario" else None, axis_value if axis_name == "pair" else None)
                        key = present.get(lookup)
                        state = "present" if key else "absent"
                    cells.append({"coordinates": coords, "state": state, "axes_not_applicable": inapplicable, "key": key})
    counts = {s: sum(1 for c in cells if c["state"] == s) for s in ("present", "not_applicable", "absent")}
    # THE CANONICAL CELLS: one per (kind, applicable coordinates) — a surface's
    # canonical cell has no z and no scenario, so it never appears among the
    # naive 72 and is "present" only here. E5.0 §1's "24 present / 48
    # inapplicable" counted this way loosely; the precise accounting is both.
    canonical = []
    for kind in KINDS:
        applicable = APPLICABLE_AXES[kind]
        for est in registry:
            z_values = z_levels if "z" in applicable else [None]
            axis_values = ([("scenario", s) for s in scenarios] if "scenario" in applicable
                           else [("pair", tuple(p)) for p in pairs] if "pair" in applicable else [(None, None)])
            for z in z_values:
                for axis_name, axis_value in axis_values:
                    lookup = (kind, est, z, axis_value if axis_name == "scenario" else None, axis_value if axis_name == "pair" else None)
                    key = present.get(lookup)
                    canonical.append({"coordinates": {"kind": kind, "estimator": est, "z": z,
                                                      "scenario": axis_value if axis_name == "scenario" else None,
                                                      "pair": list(axis_value) if axis_name == "pair" else None},
                                      "state": "present" if key else "absent", "key": key})
    canonical_counts = {s: sum(1 for c in canonical if c["state"] == s) for s in ("present", "absent")}
    return {
        "axes": {"kind": list(KINDS), "estimator": registry, "z": z_levels, "scenario": scenarios, "pair": pairs},
        "applicable_axes": {k: list(v) for k, v in APPLICABLE_AXES.items()},
        "rule": STATE_RULE,
        "n_cells": len(cells),
        "counts": counts,
        "cells": cells,
        "canonical": {
            "note": "one cell per (kind × the axes that APPLY to it): the coordinates a control panel should offer; "
                    "every naive cell marked not_applicable collapses onto one of these via its `key`",
            "n_cells": len(canonical),
            "counts": canonical_counts,
            "cells": canonical,
        },
    }


def build_catalog(manifest: dict, run_dir: Path) -> dict:
    """The catalog for one run, from its manifest (a parsed dict) and the
    association record the manifest names. No directory listing, no name
    parsing, no raster read, no number computed."""
    economics = manifest.get("economics") or {}
    association = (economics.get("association") or {}).get("file")
    record = {}
    if association:
        record = json.loads((run_dir / "economics" / association).read_text())
    entries = _surface_entries(manifest) + _economics_entries(manifest, record)
    for e in entries:
        if e.pop("_hashed_under") is None:
            raise ValueError(f"catalog entry {e['key']!r} is not in output_hashes — the record names a layer it did not hash")
    claim = manifest.get("claim") or {}
    verdicts = {}
    for design, v in (claim.get("verdicts") or {}).items():
        verdicts[design] = {
            "eligible": v.get("eligible"), "is_scientific": v.get("is_scientific"), "watermark": v.get("watermark"),
            "failing": sorted(p["precondition"] for p in v.get("preconditions") or [] if not p.get("passed")),
            "passing": sorted(p["precondition"] for p in v.get("preconditions") or [] if p.get("passed")),
            "preconditions": v.get("preconditions"),
        }
    return {
        "run_id": manifest.get("run_id"),
        "content_hash": manifest.get("content_hash"),
        "schema_version": manifest.get("schema_version"),
        "data_origin": manifest.get("data_origin"),
        "resolved_from": "the run manifest (surfaces, economics.rasters, economics.scenarios, claim, output_hashes) and the association record it names — never a listing, never a filename",
        "n_layers": len(entries),
        "layers": entries,
        "grid": _grid(manifest, entries),
        "claim": {
            "applies_to": "every layer: the guard's unit is (run, design), never an estimator or a raster (E3.1+2 §3)",
            "design": claim.get("design"),
            "verdicts": verdicts,
            "note": claim.get("note"),
            "watermark_is_not_a_refusal": "the synthetic-covariates reason lives in each verdict's `watermark`, which is structurally never a precondition (validation/claim.py); the failing sets name preconditions only",
        },
        "watermark_asymmetry": WATERMARK_ASYMMETRY,
        "economics_watermark_note": economics.get("watermark_note"),
        "uniformity_today": {
            "statement": "every footprint is minable over the whole predictable domain and every difference is empty under today's placeholder cutoffs — a property of the cutoffs' relation to the training mean, not of the seafloor (E4.1 §2)",
            "difference_fraction_of_predictable": economics.get("difference_fraction_of_predictable"),
            "difference_meaning": record.get("difference_meaning"),
        },
        "training_stations": manifest.get("training_stations"),
        "prediction_grid": manifest.get("prediction_grid"),
        "excluded_from_the_catalog": list(EXCLUSIONS),
    }
