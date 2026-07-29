"""Shared repo-root / contract-loading helper for E1.2's `normalizer_registry.py`
and E1.3's `dedup_rules.py` — both need values straight from
`data/config/normalization.yaml` (screening bounds; `coordinate_tolerance_deg`)
at runtime rather than duplicated as Python literals. Not one of CLAUDE.md's
named seams — private implementation-sharing infrastructure, same spirit as
`_column_mapping.py`.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(f"Could not locate repo root (no pyproject.toml above {start})")


@functools.lru_cache(maxsize=1)
def load_normalization_yaml() -> dict:
    """Contract 7, loaded (not duplicated in Python) so the YAML stays the
    single source of truth for screening bounds and dedup tuning."""
    repo_root = find_repo_root(Path(__file__).resolve())
    config_path = repo_root / "data" / "config" / "normalization.yaml"
    return yaml.safe_load(config_path.read_text())
