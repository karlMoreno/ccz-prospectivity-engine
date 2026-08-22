"""EconomicModel — STRATEGY, plus the in-memory footprint types (E4.1).

Turns the per-estimator prediction surfaces into a minable footprint per
scenario from scenarios.yaml (Contract 4). Track E ships this mechanism
only; every number it reads is a Track-G-owned placeholder until Contract
4's `illustrative_only` flags flip to false (Checkpoint 4).

    ┌──────────────────────────────────────────────────────────────┐
    │                    EconomicModel (ABC)                          │
    │  apply(inputs, scenario)  -> ScenarioFootprints    ← abstract   │
    │  difference(a, b)         -> FootprintDifference   ← concrete,  │
    │                              the same set logic for every model │
    └──────────────────────────────────────────────────────────────┘
            ▲
    ┌──────────────────────┐
    │ CutoffEconomicModel    │  (E4.1 commit 2; economics/cutoff.py)
    └──────────────────────┘

E4.1 2B REVISION of the Phase-0 shape (the CVScore / ts6_agreement
precedent). BEFORE: `apply(prediction: PredictionSurface, scenario_config:
dict) -> EconomicScenarioResult`, with the result carrying `scenario_name`,
a COPIED `illustrative_only` boolean, ONE `minable_footprint_path` and ONE
`minable_area_m2`. E4.0 §2 found it could express none of what Contract 4
asks: the headline output (`difference_pairs`) is CROSS-scenario and the
seam is per scenario; a scenario is a per-ESTIMATOR question (three
surfaces → three footprints per scenario) and the result was keyed by
scenario only; Decision 2 wants several confidence levels, not one raster;
and the copied boolean is exactly what the origin machinery forbids — a
declared flag standing in for a computed origin. AFTER:

  * `apply(inputs: EconomicInputs, scenario: ScenarioConfig) ->
    ScenarioFootprints` — every estimator's surface at once (never
    cherry-picked), the grid, the per-cell AREA (a deliberate seam
    addition: `FeatureBundle.cell_area_m2`, computed from DemGrid, the one
    home of the CRS decision — never reconstructed from the transform at a
    call site), and the two DECLARED facts the watermark derives from;
  * `ScenarioFootprints` — arrays in memory (the SurfaceResult precedent:
    E4.2 writes them), one `FootprintLevel` per estimator per confidence
    level z, the COMPUTED origin, the per-reason WATERMARK VERDICT
    (economics/watermark.py), and `record()` → the manifest's
    `EconomicScenarioResult` (domain/results.py, revised in the same commit);
  * `difference(a, b)` — concrete on the ABC: minable under b and not under
    a, per estimator per level; `record()` → `EconomicDifferenceResult`.

DECISION 2 (Karl, E4.0 §5) — CONFIDENCE-LEVEL FOOTPRINTS. At each z the
metric is `mu − z·sd`, z ∈ {0, 1} minimum. A probability surface was
DECLINED: it asserts a distribution the three estimators' declared
semantics do not jointly support. z is a STATED READING of three different
quantities — the baseline's sample SD (a sample moment), kriging's model sd
(a model moment under the fitted variogram), QRF's quantile half-width
("equal to the SD under normality; a distribution-free analogue otherwise")
— and NOT a common one. Each footprint therefore carries its estimator's
`uncertainty_semantics` string so a reader can REJECT the reading; that is
the whole reason this option beat the probability surface, and if the
semantics did not travel it would lose its advantage.

THE COMPUTED ORIGIN is `combine_origins` over the surface's origin and
Contract 4's file-level origin — AUTHORED today, DERIVED never declared.
The verdict beside it says why, per reason (the lattice is correct but
lossy; watermark.py records the argument).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np

from engine.prospectivity.domain.results import EconomicDifferenceResult, EconomicScenarioResult
from engine.prospectivity.economics.contract import ScenarioConfig
from engine.prospectivity.economics.watermark import WatermarkReason, WatermarkVerdict
from engine.prospectivity.provenance.origin import combine_origins
from engine.prospectivity.surfaces.builder import SurfaceResult
from engine.prospectivity.surfaces.grid import PredictionGrid

DEFAULT_CONFIDENCE_LEVELS: tuple[float, ...] = (0.0, 1.0)


@dataclass(frozen=True)
class EconomicInputs:
    """What a scenario is applied TO: every estimator's surface, the grid, the
    per-cell area in m², and the two declared facts the watermark derives
    from. `surface_data_origin` is the surfaces' COMPUTED origin (the writer's
    `compute_surface_origin`); `dem_data_origin` is the stack's DECLARED one."""

    surfaces: Mapping[str, SurfaceResult]
    grid: PredictionGrid
    cell_area_m2: np.ndarray  # (H, W) float64
    dem_data_origin: str | None
    surface_data_origin: str


@dataclass(frozen=True)
class FootprintLevel:
    """One (estimator, z): the boolean footprint and its counts. Masked
    (unpredictable) cells are never minable and are COUNTED, not dropped."""

    z: float
    minable: np.ndarray  # (H, W) bool
    n_minable: int
    n_predictable: int
    fraction_of_predictable: float
    area_m2: float
    n_failing_cutoff: int
    n_failing_slope: int
    n_excluded: int

    def summary(self) -> dict:
        return {
            "z": self.z,
            "metric": "mu - z*sd",
            "n_minable": self.n_minable,
            "n_predictable": self.n_predictable,
            "fraction_of_predictable": self.fraction_of_predictable,
            "area_m2": self.area_m2,
            "n_failing_cutoff": self.n_failing_cutoff,
            "n_failing_slope": self.n_failing_slope,
            "n_excluded": self.n_excluded,
            "raster_file": None,  # E4.2 writes the raster and fills this
        }


@dataclass(frozen=True)
class ScenarioFootprints:
    scenario: ScenarioConfig
    grade_metric: str
    confidence_levels: tuple[float, ...]
    levels: Mapping[str, Mapping[float, FootprintLevel]]  # estimator -> z -> level
    uncertainty_semantics: Mapping[str, str]
    filters: dict
    data_origin: str  # COMPUTED
    watermark: WatermarkVerdict  # DERIVED from declared facts
    cell_area_m2: np.ndarray  # (H, W) — the areas the footprints were built on; E4.2 and difference() reuse it
    provenance: dict = field(default_factory=dict)  # JSON-able facts only; never an array

    def record(self) -> EconomicScenarioResult:
        return EconomicScenarioResult(
            scenario_name=self.scenario.name,
            description=self.scenario.description,
            grade_metric=self.grade_metric,
            cutoff={
                "value": self.scenario.cutoff_value,
                "units": "kg_m2",
                "data_origin": self.scenario.cutoff.data_origin,
                "author": self.scenario.cutoff.author,
            },
            confidence_levels=list(self.confidence_levels),
            confidence_note=(
                "metric = mu - z*sd; z is a STATED READING of three different sd quantities "
                "(see uncertainty_semantics per estimator), not a common one — a reader may "
                "reject the reading; a probability surface was declined for that reason"
            ),
            footprints={
                estimator: {str(z): level.summary() for z, level in by_z.items()}
                for estimator, by_z in self.levels.items()
            },
            uncertainty_semantics=dict(self.uncertainty_semantics),
            filters=dict(self.filters),
            caveats=list(self.scenario.caveats),
            data_origin=self.data_origin,
            watermark=self.watermark.to_record(),
            provenance=dict(self.provenance),
        )


@dataclass(frozen=True)
class FootprintDifference:
    pair: tuple[str, str]  # (a, b): minable under b and NOT under a
    levels: Mapping[str, Mapping[float, FootprintLevel]]
    data_origin: str
    watermark: WatermarkVerdict

    def record(self) -> EconomicDifferenceResult:
        return EconomicDifferenceResult(
            pair=list(self.pair),
            meaning=f"cells minable under {self.pair[1]} and NOT under {self.pair[0]}",
            footprints={
                estimator: {str(z): level.summary() for z, level in by_z.items()}
                for estimator, by_z in self.levels.items()
            },
            data_origin=self.data_origin,
            watermark=self.watermark.to_record(),
        )


class EconomicModel(ABC):
    """Applies one scenarios.yaml scenario to the prediction surfaces."""

    @abstractmethod
    def apply(self, inputs: EconomicInputs, scenario: ScenarioConfig) -> ScenarioFootprints:
        """Every estimator's footprint at every confidence level for ONE
        scenario. Implementations must derive the watermark verdict from the
        declared facts in `inputs` and `scenario` (economics/watermark.py)
        and compute the origin — the engine is never allowed to present a
        placeholder-cutoff footprint as a real one, and a copied boolean is
        not how that is prevented."""
        raise NotImplementedError

    def difference(self, a: ScenarioFootprints, b: ScenarioFootprints) -> FootprintDifference:
        """Minable under `b` and NOT under `a`, per estimator per level — the
        "strategic-only" footprint when a is the market scenario. Concrete:
        the set logic is the same for every model, and a model that could
        override it could report a difference its own footprints do not
        contain."""
        if set(a.levels) != set(b.levels) or a.confidence_levels != b.confidence_levels:
            raise ValueError(
                f"cannot difference {a.scenario.name!r} and {b.scenario.name!r}: they cover "
                f"estimators {sorted(a.levels)} vs {sorted(b.levels)} at levels "
                f"{a.confidence_levels} vs {b.confidence_levels}"
            )
        levels: dict[str, dict[float, FootprintLevel]] = {}
        for estimator in sorted(a.levels):
            levels[estimator] = {}
            for z in a.confidence_levels:
                la, lb = a.levels[estimator][z], b.levels[estimator][z]
                only_b = lb.minable & ~la.minable
                only_b.flags.writeable = False
                n = int(only_b.sum())
                levels[estimator][z] = FootprintLevel(
                    z=z,
                    minable=only_b,
                    n_minable=n,
                    n_predictable=lb.n_predictable,
                    fraction_of_predictable=(n / lb.n_predictable) if lb.n_predictable else 0.0,
                    area_m2=float(a.cell_area_m2[only_b].sum()),
                    n_failing_cutoff=0,
                    n_failing_slope=0,
                    n_excluded=0,
                )
        if not np.array_equal(a.cell_area_m2, b.cell_area_m2):
            raise ValueError("cannot difference footprints built on different cell areas")
        # The difference's verdict: the terrain reason is shared; the parameter
        # reason is lifted only if BOTH scenarios' are, and cites both flags.
        reasons = tuple(
            ra if ra == rb else WatermarkReason(
                reason=ra.reason, cause=f"{ra.cause} | {rb.cause}", lifted_by=ra.lifted_by,
                lifted=ra.lifted and rb.lifted,
            )
            for ra, rb in zip(a.watermark.reasons, b.watermark.reasons)
        )
        return FootprintDifference(
            pair=(a.scenario.name, b.scenario.name),
            levels=levels,
            data_origin=combine_origins([a.data_origin, b.data_origin]).value,
            watermark=WatermarkVerdict(reasons=reasons),
        )
