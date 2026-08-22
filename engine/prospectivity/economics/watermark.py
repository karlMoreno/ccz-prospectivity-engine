"""The economic watermark VERDICT — one entry per independent reason (E4.1;
Karl's Decision 1 at E4.0 §3, on E2.5's ClaimVerdict precedent).

WHY NOT THE LATTICE, recorded here because a later reader will try to
"simplify" to the computed origin alone. `combine_origins({SYNTHETIC,
AUTHORED}) = AUTHORED` is CORRECT and LOSSY: at Checkpoint 1 the DEM becomes
MEASURED and the footprint's origin stays AUTHORED — a reader sees NO change
from a real improvement; at Checkpoint 4 with a synthetic DEM it flips to
SYNTHETIC, which READS AS MORE REAL when only the parameters moved. A single
value that moves in the wrong direction is worse than one that does not
move. So the computed origin stays exactly as it is — least-real, computed,
never declared — and an economic artifact ADDITIONALLY carries this verdict.

    declared facts ─────────────────────────► WatermarkVerdict
      the stack's dem_data_origin    ──► reason "terrain":  lifted iff MEASURED,   lifted_by Checkpoint 1
      the scenario's illustrative_only ─► reason "economic_parameters": lifted iff false, lifted_by Checkpoint 4

DERIVED from declared facts, never hand-set — the same rule as the origin
itself. The property that makes ClaimVerdict credible is preserved: the
verdict DISCRIMINATES. Two unlifted reasons today; one lifted and one not
after either checkpoint; a test observes the transition, or "two reasons"
is decoration.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.prospectivity.economics.contract import ScenarioConfig
from engine.prospectivity.provenance.origin import DataOrigin

CHECKPOINT_1 = "Checkpoint 1 (real bathymetry replaces the synthetic DEM)"
CHECKPOINT_4 = "Checkpoint 4 (Track G supplies real economic parameters; illustrative_only -> false)"


@dataclass(frozen=True)
class WatermarkReason:
    reason: str
    cause: str  # the declared fact this is derived from, cited
    lifted_by: str
    lifted: bool

    def to_record(self) -> dict:
        return {"reason": self.reason, "cause": self.cause, "lifted_by": self.lifted_by, "lifted": self.lifted}


@dataclass(frozen=True)
class WatermarkVerdict:
    reasons: tuple[WatermarkReason, ...]

    @property
    def unlifted(self) -> tuple[WatermarkReason, ...]:
        return tuple(r for r in self.reasons if not r.lifted)

    @property
    def watermarked(self) -> bool:
        """DERIVED, never stored: watermarked iff any reason is unlifted."""
        return bool(self.unlifted)

    def text(self) -> str | None:
        """The watermark string for a raster tag or a caption; None when every
        reason is lifted (the positive rule — clean only when proven)."""
        if not self.watermarked:
            return None
        return "NON-SCIENTIFIC, " + str(len(self.unlifted)) + " independent reason(s): " + "; ".join(
            f"{r.reason} ({r.cause}; lifts at {r.lifted_by})" for r in self.unlifted
        )

    def to_record(self) -> dict:
        return {
            "watermarked": self.watermarked,
            "reasons": [r.to_record() for r in self.reasons],
            "note": (
                "one entry per INDEPENDENT reason, each derived from a declared fact; "
                "the computed data_origin beside this is the least-real input and is "
                "correct but lossy — it cannot say which reason lifted when"
            ),
        }


def economic_watermark_verdict(dem_data_origin: str | None, scenario: ScenarioConfig) -> WatermarkVerdict:
    """Derive the verdict from the two declared facts. An UNDECLARED DEM origin
    is an unlifted reason (absence of proof watermarks; P2.0d-3), never a
    lifted one."""
    terrain_lifted = dem_data_origin is not None and DataOrigin(dem_data_origin) is DataOrigin.MEASURED
    return WatermarkVerdict(
        reasons=(
            WatermarkReason(
                reason="terrain",
                cause=f"feature stack dem_data_origin = {dem_data_origin!r}",
                lifted_by=CHECKPOINT_1,
                lifted=terrain_lifted,
            ),
            WatermarkReason(
                reason="economic_parameters",
                cause=(
                    f"scenarios.yaml scenarios[{scenario.index}] ({scenario.name}) "
                    f"illustrative_only = {scenario.illustrative_only}"
                ),
                lifted_by=CHECKPOINT_4,
                lifted=not scenario.illustrative_only,
            ),
        )
    )
