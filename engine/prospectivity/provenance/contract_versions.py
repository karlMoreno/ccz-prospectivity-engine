"""The `contract_versions` block, read from the frozen contracts themselves.

Never hardcoded: every value here is loaded from the contract file that owns
it, so a version bump shows up in the next manifest without anyone editing
Python. `study_area.geojson` has no version field (Contract 2 was frozen
without one), so it is identified by `area_id` + a content hash instead —
recorded honestly as what it is rather than invented.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.prospectivity.ingestion._contract_paths import find_repo_root, load_normalization_yaml

REPO_ROOT = find_repo_root(Path(__file__).resolve())
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "master_observations.schema.json"
STUDY_AREA_PATH = REPO_ROOT / "data" / "aoi" / "study_area.geojson"


def file_sha256(path: Path) -> str:
    """Real computed SHA-256 of a file's bytes. The one hash function every
    input in this project is measured with — no placeholders (the E1.4 audit
    found `content_hash="sha256:synthetic-fixture"` hardcoded in a fixture;
    this is where that stops being acceptable)."""
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contract_versions() -> dict[str, str | int | None]:
    """Versions of every contract in effect for an ingestion/feature run.

    `load_covariates_yaml` is imported HERE, not at module scope: features/
    's package __init__ imports stack.py, which imports this module, so a
    top-level import would be a cycle. Deferring it to call time breaks that
    without either package having to know about the other's import order.
    """
    from engine.prospectivity.features._contract import load_covariates_yaml

    schema = json.loads(SCHEMA_PATH.read_text())
    study_area = json.loads(STUDY_AREA_PATH.read_text())
    area_id = study_area["features"][0]["properties"].get("area_id")
    return {
        "master_observations_schema_version": schema["schema_version"],
        "normalization_policy_version": load_normalization_yaml()["policy_version"],
        "covariates_registry_version": load_covariates_yaml()["registry_version"],
        # Contract 2 carries no version field — identify it by area_id + hash.
        "study_area_id": area_id,
        "study_area_content_hash": file_sha256(STUDY_AREA_PATH),
    }
