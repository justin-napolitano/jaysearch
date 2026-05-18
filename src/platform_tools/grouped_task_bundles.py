from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GROUPED_BUNDLES_DIR = Path("artifacts/planner/grouped-bundles")


def _bundle_files(root: Path) -> list[Path]:
    directory = root / GROUPED_BUNDLES_DIR
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def load_grouped_bundles(*, root: Path) -> list[dict[str, Any]]:
    bundles: list[dict[str, Any]] = []
    for path in _bundle_files(root):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_path"] = path.as_posix()
            bundles.append(payload)
    return bundles


def bundle_node_ids(bundle: dict[str, Any]) -> list[str]:
    node_ids = bundle.get("node_ids", [])
    if not isinstance(node_ids, list):
        return []
    return [str(item).strip() for item in node_ids if str(item).strip()]


def bundle_validation_findings(
    *,
    bundle: dict[str, Any],
    allowed_node_ids: set[str],
) -> list[str]:
    findings: list[str] = []
    if str(bundle.get("bundle_id", "")).strip() == "":
        findings.append("bundle_id_missing")
    if str(bundle.get("dag_id", "")).strip() == "":
        findings.append("dag_id_missing")
    if str(bundle.get("title", "")).strip() == "":
        findings.append("bundle_title_missing")
    if str(bundle.get("status", "")).strip() not in {"draft", "ready", "in_progress", "blocked", "done"}:
        findings.append("bundle_status_invalid")
    node_ids = bundle_node_ids(bundle)
    if not node_ids:
        findings.append("bundle_node_ids_missing")
    missing = [node_id for node_id in node_ids if node_id not in allowed_node_ids]
    if missing:
        findings.append("bundle_references_unknown_node_ids")
    return findings


def select_active_grouped_bundle(
    *,
    root: Path,
    initiative_branch: str,
    allowed_node_ids: set[str],
    candidate_node_ids: set[str],
) -> dict[str, Any] | None:
    for bundle in load_grouped_bundles(root=root):
        if str(bundle.get("status", "")).strip() != "ready":
            continue
        bundle_branch = str(bundle.get("initiative_branch", "")).strip()
        if bundle_branch and bundle_branch != initiative_branch:
            continue
        findings = bundle_validation_findings(bundle=bundle, allowed_node_ids=allowed_node_ids)
        if findings:
            continue
        node_ids = bundle_node_ids(bundle)
        pending_node_ids = [node_id for node_id in node_ids if node_id in candidate_node_ids]
        if not pending_node_ids:
            continue
        selected = dict(bundle)
        selected["pending_node_ids"] = pending_node_ids
        return selected
    return None
