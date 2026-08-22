"""build_surfaces — fit on the full matrix, predict over the grid (E3.1+2 §2).

    registry.names()  ─────►  for EACH estimator, never cherry-picked
            │                        │
            │                 route_grid(estimator, grid)   ◄── BY DECLARATION
            │                        │        (input_kind, C8.1's mechanism)
            │            ┌───────────┴───────────┐
            │      "coordinates"            "covariates"
            │      grid.cell_centres()      grid.covariate_rows()
            │            └───────────┬───────────┘
            ▼                        ▼
      SurfaceResult  ◄──  estimator.fit(full matrix) → predict(grid rows)
      mu (H,W) · sd (H,W) · both masked outside the domain

THE PAIR IS STRUCTURAL. `predict()` returns (mu, sd) as an inseparable pair —
the ABC refuses an override — so one call produces both surfaces and there is
no code path here that could emit a prediction without its uncertainty. That
is why E3.1 and E3.2 are one task rather than two.

ROUTING IS A DECLARATION, NEVER A NAME. `route_grid` mirrors
`validation/runner.route` exactly: same `input_kind` values, same exhaustive
dispatch, same explicit raise. One rule, two sources — a training matrix
there, a grid here — so an estimator cannot consume one shape in CV and a
different shape at prediction time.

CHUNKING IS AN OPTIMISATION AND MUST BE A NO-OP. `chunk_size` splits the
predict call only; a chunk boundary that changed a prediction would be a
defect, which is why the suite asserts a chunked build is BYTE-IDENTICAL to
an unchunked one rather than merely close.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from engine.prospectivity.estimators.base import INPUT_KINDS, Estimator
from engine.prospectivity.estimators.registry import EstimatorRegistry
from engine.prospectivity.surfaces.grid import PredictionGrid
from engine.prospectivity.training_matrix import TrainingMatrix
from engine.prospectivity.validation.runner import route


def route_grid(estimator: Estimator, grid: PredictionGrid) -> np.ndarray:
    """The design matrix an estimator PREDICTS from — by its declaration.

    Exhaustive over INPUT_KINDS with an explicit raise, the house convention
    and the same shape as `runner.route`. A new input kind arrives here WITH
    its estimator, never by name-matching (the inference this project has
    removed four times).
    """
    kind = estimator.input_kind
    if kind == "covariates":
        return grid.covariate_rows()
    if kind == "coordinates":
        return grid.cell_centres()
    raise ValueError(  # pragma: no cover — the ABC refuses undeclared kinds at definition
        f"{type(estimator).__name__} declares input_kind={kind!r}, not one of {INPUT_KINDS}"
    )


@dataclass(frozen=True)
class SurfaceResult:
    """One estimator's paired surfaces over the grid, plus what a reader must
    know to interpret them. Masked cells are NaN in BOTH arrays — never
    zero-filled, the same flag-never-drop rule the grid's mask follows."""

    estimator_name: str
    input_kind: str
    uncertainty_method: str
    uncertainty_semantics: str
    mu: np.ndarray  # (H, W) float64, NaN outside the domain
    sd: np.ndarray  # (H, W) float64, NaN outside the domain
    n_predicted: int
    n_masked: int
    n_sd_zero: int
    provenance: dict = field(default_factory=dict)

    def summary(self) -> dict:
        """The per-surface facts a manifest or a tag block records."""
        finite = self.mu[np.isfinite(self.mu)]
        return {
            "estimator_name": self.estimator_name,
            "input_kind": self.input_kind,
            "uncertainty_method": self.uncertainty_method,
            "uncertainty_semantics": self.uncertainty_semantics,
            "n_predicted": self.n_predicted,
            "n_masked": self.n_masked,
            "n_sd_zero": self.n_sd_zero,
            "n_distinct_values": int(np.unique(finite).size),
            "mu_min": float(finite.min()) if finite.size else None,
            "mu_max": float(finite.max()) if finite.size else None,
        }


def _predict_in_chunks(
    estimator: Estimator, features: np.ndarray, chunk_size: int | None
) -> tuple[np.ndarray, np.ndarray]:
    if chunk_size is None or chunk_size >= features.shape[0]:
        mu, sd = estimator.predict(features)
        return np.asarray(mu, dtype=np.float64), np.asarray(sd, dtype=np.float64)
    mus, sds = [], []
    for start in range(0, features.shape[0], chunk_size):
        mu, sd = estimator.predict(features[start : start + chunk_size])
        mus.append(np.asarray(mu, dtype=np.float64))
        sds.append(np.asarray(sd, dtype=np.float64))
    return np.concatenate(mus), np.concatenate(sds)


def build_surfaces(
    grid: PredictionGrid,
    matrix: TrainingMatrix,
    registry: EstimatorRegistry,
    *,
    chunk_size: int | None = None,
) -> dict[str, SurfaceResult]:
    """Every registered estimator, fitted on the FULL training matrix and
    predicted over every predictable grid cell.

    ITERATES `names()` — never cherry-picks. The E2.4 obligation still binds:
    a builder that skipped an estimator would be choosing which model to
    report, and the choice would be invisible.
    """
    registry.assert_complete()
    predictable = grid.predictable.ravel()
    surfaces: dict[str, SurfaceResult] = {}

    for name in registry.names():
        estimator = registry.get(name)
        estimator.fit(route(estimator, matrix), matrix.y)
        features = route_grid(estimator, grid)[predictable]
        mu_flat, sd_flat = _predict_in_chunks(estimator, features, chunk_size)

        # UNCERTAINTY IS ALWAYS PAIRED — AND THIS BUILDER DOES NOT RE-CHECK IT.
        # `Estimator.predict()` is a final Template Method that already
        # refuses a non-pair, a None member, a SHAPE-MISMATCHED pair, a
        # non-finite std and a negative std, naming the estimator. Repeating
        # those here would be unreachable code with tests that appeared to
        # exercise it — the coverage-that-isn't defect C8.1 removed from the
        # claim guard for exactly this reason. The guarantee has ONE site.
        #
        # WHAT THE ABC CANNOT CHECK, because it never sees the request: that
        # the pair has one entry per CELL ASKED FOR. A correctly-paired result
        # of the wrong LENGTH passes every check above and would misalign
        # every value against the grid, so it is refused here.
        if mu_flat.shape[0] != features.shape[0]:
            raise ValueError(
                f"{name} returned {mu_flat.shape[0]} paired prediction(s) for "
                f"{features.shape[0]} requested cells — one (mu, sd) per cell, "
                "or the surface is misaligned against the grid"
            )

        mu = np.full(grid.n_cells, np.nan)
        sd = np.full(grid.n_cells, np.nan)
        mu[predictable] = mu_flat
        sd[predictable] = sd_flat
        mu = mu.reshape(grid.height, grid.width)
        sd = sd.reshape(grid.height, grid.width)
        for array in (mu, sd):
            array.flags.writeable = False

        surfaces[name] = SurfaceResult(
            estimator_name=name,
            input_kind=estimator.input_kind,
            uncertainty_method=estimator.uncertainty_method,
            uncertainty_semantics=estimator.uncertainty_semantics,
            mu=mu,
            sd=sd,
            n_predicted=int(predictable.sum()),
            n_masked=grid.n_masked,
            # COUNTED, NOT FLOORED (E2.3's rule): a zero-width uncertainty is
            # a leaf population that has only ever seen one answer, and
            # flooring it would convert under-information into confidence.
            n_sd_zero=int((sd_flat == 0.0).sum()),
            provenance=dict(estimator.provenance()),
        )
    return surfaces
