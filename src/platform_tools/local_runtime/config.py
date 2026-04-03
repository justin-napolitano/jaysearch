from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path("spec/local-orchestration.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def load_local_orchestration_config(*, root: str = ".") -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = root_path / CONFIG_PATH
    if not path.exists():
        raise ValueError("missing_local_orchestration_config")
    config = _load_yaml(path)
    if not config:
        raise ValueError("invalid_local_orchestration_config")
    return config


def validate_repo_target(*, config: dict[str, Any], repo_root: str | None) -> list[str]:
    target = (repo_root or "").strip()
    if not target:
        return []
    root_path = Path(target)
    if not root_path.exists():
        return ["target_repo_root_is_missing"]
    if not root_path.is_dir():
        return ["target_repo_root_is_ambiguous"]
    managed = config.get("managed_repo_targeting", {})
    if not isinstance(managed, dict):
        return ["required_target_artifact_missing"]
    required = managed.get("required_target_artifacts", [])
    if not isinstance(required, list):
        return ["required_target_artifact_missing"]
    missing = [item for item in required if not (root_path / str(item)).exists()]
    return ["required_target_artifact_missing"] if missing else []
