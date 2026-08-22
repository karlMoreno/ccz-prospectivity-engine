"""run_environment — the run's software environment, recorded beside the
contract versions (E3.4 commit 3; BACKLOG §3 "Dependency versions into the
provenance manifest", whose trigger — "the Phase-3 manifest emitter" — fired
when E3.4 built one).

    requirements.lock ──sha256──┐
    CPython version ────────────┼──► inputs.environment  (INSIDE the substance hash)
    installed versions of the   │
    approved stack ─────────────┘

WHY INSIDE THE HASH: the installed versions are INPUTS to the computation —
a kriging solve under one SciPy and a quantile forest under one
scikit-learn are the run's inputs as much as the seed is. Two machines with
the same lockfile installed hash identically; two that differ in a package
version do not, and a hash that stayed equal across that difference would
claim a reproducibility it cannot deliver. The LOCKFILE hash is the
portable, committed half (the file is tracked); the installed versions are
the measured half, read from the interpreter that ran, never from the
lockfile — a lockfile records what was RESOLVED, `importlib.metadata` what
is INSTALLED, and the two drift (BACKLOG §3: the lock is macOS-arm64 only).

What is NOT recorded, stated: OS, hostname, CPU — environment-derived and
reproducibility-irrelevant at this stage; GDAL's version IS, via rasterio,
because the COG driver's output depends on it.
"""

from __future__ import annotations

import importlib.metadata
import platform
from pathlib import Path

import rasterio

from engine.prospectivity.ingestion._contract_paths import find_repo_root
from engine.prospectivity.provenance.contract_versions import file_sha256

REPO_ROOT = find_repo_root(Path(__file__).resolve())
REQUIREMENTS_LOCK = REPO_ROOT / "requirements.lock"

# The approved stack (CLAUDE.md "Dependency & scope discipline") as installed
# distribution names. Recorded by NAME so a version that is absent shows as
# absent rather than silently dropping out of the record.
RECORDED_PACKAGES = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "quantile-forest",
    "rasterio",
    "shapely",
    "pydantic",
    "pyyaml",
)


def _installed_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_environment() -> dict:
    """The environment block: lockfile hash (recomputed from the committed
    file's bytes), the interpreter, the approved stack's installed versions,
    and GDAL's (through rasterio)."""
    return {
        "requirements_lock": REQUIREMENTS_LOCK.name,
        "requirements_lock_sha256": file_sha256(REQUIREMENTS_LOCK),
        "python": platform.python_version(),
        "packages": {name: _installed_version(name) for name in RECORDED_PACKAGES},
        "gdal": rasterio.__gdal_version__,
        "note": (
            "installed versions are read from the running interpreter, never from "
            "the lockfile; they are INSIDE the content hash because they are inputs "
            "to every number in this record"
        ),
    }
