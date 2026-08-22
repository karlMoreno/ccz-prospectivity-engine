"""CutoffEconomicModel — Contract 4's minability rule, as specified (E4.1 commit 2).

    per cell, per estimator, per confidence level z:
        metric      = mu - z*sd                      (grade_metric = abundance)
        minable iff predictable
                 AND metric >= cutoff_value          (>=, the contract's "metric >= cutoff")
                 AND slope  <= max_slope_degrees     (spatial_filters)
                 AND not excluded                    (Contract 2's exclusions.geojson)

WHAT IT REFUSES BY NAME rather than computing quietly:
  * `grade_metric: dollar_value` — DEAD ON ARRIVAL today: every
    `price_usd_per_tonne` is 0 and the corpus has ZERO GRADE rows
    (mn/ni/cu/co_pct non-null = 0/0/0/0; [19] never wired; the join is
    blocked on join_tolerance_km). A footprint of zero cells and a
    footprint that COULD NOT BE COMPUTED are different claims, and
    computing zeros would emit the first while meaning the second.
  * a NON-EMPTY exclusion set — rasterising polygons onto the grid is not
    built (no consumer until Track G adds a polygon); Contract 2's file
    "starts EMPTY on purpose", and that emptiness is ASSERTED so the day it
    changes is a visible refusal, not a silently ignored polygon.
  * a stack without a `slope` layer — the filter cannot be applied to a
    layer that is not there.

THE SLOPE FILTER IS PHYSICALLY MEANINGLESS AT THIS RESOLUTION, and is
applied anyway as specified. `max_slope_degrees: 6` is a collector limit;
the stack's `slope` is Horn's 3x3 gradient on ~11 km cells (0.1°), a
regional gradient that has nothing to do with what a collector meets. It
becomes meaningful at Checkpoint 1 with ~460 m cells (BACKLOG §3). The
filter is applied as the contract says — not skipped, not pretended to
mean something today — and the record says so beside the count.

DECISION 2's READING travels with every footprint: z multiplies three
different sd quantities (model.py's docstring), and each estimator's
`uncertainty_semantics` is recorded beside its levels so a reader can
reject the reading.

THE COMPUTED ORIGIN is combine_origins(surface origin, the cutoff's
declared origin) — AUTHORED today, never declared here. The per-reason
verdict beside it says why (watermark.py).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from engine.prospectivity.economics.contract import (
    ExclusionSet,
    ScenarioConfig,
    SpatialFilters,
    grade_metric,
    load_exclusions,
    spatial_filters,
)
from engine.prospectivity.economics.model import (
    DEFAULT_CONFIDENCE_LEVELS,
    EconomicInputs,
    EconomicModel,
    FootprintLevel,
    ScenarioFootprints,
)
from engine.prospectivity.economics.watermark import economic_watermark_verdict
from engine.prospectivity.provenance.origin import combine_origins

SLOPE_LAYER = "slope"
SLOPE_RESOLUTION_NOTE = (
    "applied as Contract 4 specifies, and PHYSICALLY MEANINGLESS at this resolution: a "
    "collector-slope limit against Horn's 3x3 gradient on ~11 km cells is a regional "
    "gradient, not what a collector meets; meaningful at Checkpoint 1 (~460 m cells)"
)


class CutoffEconomicModel(EconomicModel):
    """Contract 4's rule over the mean-minus-z-sd metric.

    `contract` / `exclusions` are testability seams (the `target_definition`
    precedent): production callers omit them and the real files are read.
    """

    def __init__(
        self,
        *,
        confidence_levels: Sequence[float] = DEFAULT_CONFIDENCE_LEVELS,
        contract: dict | None = None,
        exclusions: ExclusionSet | None = None,
    ) -> None:
        levels = tuple(float(z) for z in confidence_levels)
        if not levels or any(z < 0 for z in levels) or len(set(levels)) != len(levels):
            raise ValueError(
                f"confidence_levels must be a non-empty set of distinct z >= 0, got {levels!r}"
            )
        if 0.0 not in levels:
            raise ValueError(
                "confidence_levels must include z = 0 (the footprint at the mean) — the "
                "pessimistic footprints are read AGAINST it"
            )
        self._levels = levels
        self._contract = contract
        self._exclusions = exclusions

    @property
    def confidence_levels(self) -> tuple[float, ...]:
        return self._levels

    def apply(self, inputs: EconomicInputs, scenario: ScenarioConfig) -> ScenarioFootprints:
        metric = grade_metric(self._contract)
        if metric.value == "dollar_value":
            raise ValueError(
                f"grade_metric 'dollar_value' cannot be computed for scenario {scenario.name!r}: "
                "every metal_weights price_usd_per_tonne is 0 and the corpus holds ZERO GRADE "
                "rows ([19] never wired; the join is blocked on join_tolerance_km). A footprint "
                "that cannot be computed is not a footprint of zero cells — refusing rather "
                "than emitting zeros"
            )
        filters = spatial_filters(self._contract)
        exclusions = self._exclusions if self._exclusions is not None else load_exclusions()
        if filters.apply_exclusions and not exclusions.is_empty:
            raise ValueError(
                f"{exclusions.path} carries {len(exclusions.features)} exclusion feature(s) and "
                "rasterising exclusion polygons onto the prediction grid is not built — the "
                "file has been empty by design since Phase 0, and this refusal is what makes "
                "its first polygon a visible change rather than a silently ignored one"
            )
        grid = inputs.grid
        if SLOPE_LAYER not in grid.layer_names:
            raise ValueError(
                f"the feature stack has no {SLOPE_LAYER!r} layer (it has {list(grid.layer_names)}) — "
                "spatial_filters.max_slope_degrees cannot be applied to a layer that is not there"
            )
        if inputs.cell_area_m2.shape != (grid.height, grid.width):
            raise ValueError(
                f"cell_area_m2 has shape {inputs.cell_area_m2.shape}, the grid is "
                f"{(grid.height, grid.width)} — the areas do not describe this grid"
            )
        slope = grid.covariates[grid.layer_names.index(SLOPE_LAYER)]
        max_slope = float(filters.max_slope_degrees.value)  # type: ignore[arg-type]
        cutoff = scenario.cutoff_value
        predictable = grid.predictable
        passes_slope = predictable & (slope <= max_slope)
        not_excluded = np.ones_like(predictable)  # the asserted-empty set excludes nothing

        levels: dict[str, dict[float, FootprintLevel]] = {}
        semantics: dict[str, str] = {}
        for name in sorted(inputs.surfaces):
            surface = inputs.surfaces[name]
            if surface.mu.shape != (grid.height, grid.width):
                raise ValueError(f"surface {name!r} has shape {surface.mu.shape}, the grid is {(grid.height, grid.width)}")
            semantics[name] = surface.uncertainty_semantics
            levels[name] = {}
            for z in self._levels:
                with np.errstate(invalid="ignore"):
                    value = surface.mu - z * surface.sd
                    clears = predictable & (value >= cutoff)
                minable = clears & passes_slope & not_excluded
                minable = np.ascontiguousarray(minable, dtype=bool)
                minable.flags.writeable = False
                n_predictable = int(predictable.sum())
                n = int(minable.sum())
                levels[name][z] = FootprintLevel(
                    z=z,
                    minable=minable,
                    n_minable=n,
                    n_predictable=n_predictable,
                    fraction_of_predictable=(n / n_predictable) if n_predictable else 0.0,
                    area_m2=float(inputs.cell_area_m2[minable].sum()),
                    n_failing_cutoff=int((predictable & ~clears).sum()),
                    n_failing_slope=int((predictable & ~passes_slope).sum()),
                    n_excluded=0,
                )

        origin = combine_origins([inputs.surface_data_origin, scenario.cutoff.data_origin])
        return ScenarioFootprints(
            scenario=scenario,
            grade_metric=str(metric.value),
            confidence_levels=self._levels,
            levels=levels,
            uncertainty_semantics=semantics,
            filters={
                "max_slope_degrees": {
                    "value": max_slope,
                    "data_origin": filters.max_slope_degrees.data_origin,
                    "note": SLOPE_RESOLUTION_NOTE,
                    "cell_size_deg": [grid.res_x_deg, grid.res_y_deg],
                },
                "apply_exclusions": filters.apply_exclusions,
                "exclusions": {
                    "file": exclusions.path,
                    "data_origin": exclusions.data_origin,
                    "n_features": len(exclusions.features),
                    "note": "asserted empty at emission; a non-empty set refuses by name until rasterisation exists",
                },
                "counts_note": (
                    "n_failing_cutoff and n_failing_slope are each over PREDICTABLE cells and may "
                    "overlap; masked cells are never minable and are excluded from n_predictable"
                ),
            },
            data_origin=origin.value,
            watermark=economic_watermark_verdict(inputs.dem_data_origin, scenario),
            cell_area_m2=inputs.cell_area_m2,
            grid_identity=grid.identity(),
            provenance={
                "generator": "engine.prospectivity.economics.cutoff.CutoffEconomicModel.apply",
                "rule": "minable iff predictable AND (mu - z*sd) >= cutoff AND slope <= max_slope AND not excluded",
                "grade_metric_origin": metric.data_origin,
                "surface_data_origin": inputs.surface_data_origin,
                "dem_data_origin": inputs.dem_data_origin,
            },
        )
