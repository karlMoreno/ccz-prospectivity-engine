"""Contract 3 (covariates.yaml) loader for the features package.

Same spirit as ingestion/_contract_paths.py (whose `find_repo_root` it
reuses): the YAML stays the single source of truth for which covariates
exist, their recipes, versions, and parameters — never duplicated as Python
literals. Private implementation-sharing infrastructure, not one of
CLAUDE.md's named seams.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml

from engine.prospectivity.ingestion._contract_paths import find_repo_root


@functools.lru_cache(maxsize=1)
def load_covariates_yaml() -> dict:
    """Contract 3, loaded from docs/contracts/covariates.yaml."""
    repo_root = find_repo_root(Path(__file__).resolve())
    contract_path = repo_root / "docs" / "contracts" / "covariates.yaml"
    return yaml.safe_load(contract_path.read_text())


def enabled_covariates(contract: dict | None = None) -> list[dict]:
    """The Option-A entries the engine must implement (enabled: true)."""
    contract = contract if contract is not None else load_covariates_yaml()
    return [entry for entry in contract["covariates"] if entry["enabled"]]


def candidate_covariates(contract: dict | None = None) -> list[dict]:
    """The Option-B entries that must stay disabled and unimplemented."""
    contract = contract if contract is not None else load_covariates_yaml()
    return list(contract.get("candidate_covariates", []))
