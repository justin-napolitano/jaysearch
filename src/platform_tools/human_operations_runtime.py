from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any

from platform_tools.plan_utils import parse_plan


DEFAULT_FIELD_MAP_PATH = "artifacts/provider-sync/github-projects-field-map.json"


def _git(root: str, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _github_repo_http_url(remote_url: str) -> str:
    cleaned = remote_url.strip()
    if not cleaned:
        return ""
    http_match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", cleaned)
    if http_match:
        return f"https://github.com/{http_match.group(1)}/{http_match.group(2)}"
    ssh_match = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", cleaned)
    if ssh_match:
        return f"https://github.com/{ssh_match.group(1)}/{ssh_match.group(2)}"
    return ""


def github_repo_http_url(*, root: str = ".") -> str:
    return _github_repo_http_url(_git(root, "config", "--get", "remote.origin.url"))


def _plan_path_for_target(*, root: str, target_execplan_id: str) -> Path | None:
    if not target_execplan_id:
        return None
    candidate = Path(root) / ".agent" / "execplans" / f"{target_execplan_id}.md"
    return candidate if candidate.exists() else None


def load_execplan_state(*, root: str, target_execplan_id: str) -> dict[str, str]:
    path = _plan_path_for_target(root=root, target_execplan_id=target_execplan_id)
    if path is None:
        return {
            "path": "",
            "status": "",
            "finalized_by": "",
            "finalized_at": "",
            "finalized_in_pr": "",
        }
    frontmatter = parse_plan(path).frontmatter
    return {
        "path": path.as_posix(),
        "status": str(frontmatter.get("status", "")).strip(),
        "finalized_by": str(frontmatter.get("finalized_by", "")).strip(),
        "finalized_at": str(frontmatter.get("finalized_at", "")).strip(),
        "finalized_in_pr": str(frontmatter.get("finalized_in_pr", "")).strip(),
    }


def derive_pr_url(*, repo_http_url: str, finalized_in_pr: str) -> str:
    value = finalized_in_pr.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.isdigit() and repo_http_url:
        return f"{repo_http_url}/pull/{value}"
    return ""


def load_field_map_state(*, root: str = ".", field_map_path: str = DEFAULT_FIELD_MAP_PATH) -> dict[str, Any]:
    path = Path(root) / field_map_path
    if not path.exists():
        return {
            "field_map_path": path.as_posix(),
            "field_map_exists": False,
            "project_id": "",
            "field_count": 0,
            "item_id_count": 0,
            "duplicate_item_ids": [],
            "board_bootstrapped": False,
            "board_reuse_required": False,
            "prefer_update_when_item_id_known": False,
        }
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("invalid_field_map")
    item_ids = loaded.get("item_ids_by_node_id", {})
    item_id_values = [str(value).strip() for value in item_ids.values()] if isinstance(item_ids, dict) else []
    duplicates = sorted({value for value in item_id_values if value and item_id_values.count(value) > 1})
    project_id = str(loaded.get("project_id", "")).strip()
    return {
        "field_map_path": path.as_posix(),
        "field_map_exists": True,
        "project_id": project_id,
        "field_count": len(loaded.get("fields", {})) if isinstance(loaded.get("fields"), dict) else 0,
        "item_id_count": len([value for value in item_id_values if value]),
        "duplicate_item_ids": duplicates,
        "board_bootstrapped": bool(project_id),
        "board_reuse_required": bool(project_id),
        "prefer_update_when_item_id_known": bool(item_id_values),
    }


def review_projection_for_node(
    node: dict[str, Any],
    *,
    root: str = ".",
    current_branch: str = "",
) -> dict[str, Any]:
    target_execplan_id = str(node.get("target_execplan_id", "")).strip()
    implementation_branch = str(node.get("implementation_branch", "")).strip()
    node_status = str(node.get("status", "")).strip()
    plan_state = load_execplan_state(root=root, target_execplan_id=target_execplan_id)
    repo_http_url = github_repo_http_url(root=root)
    pr_url = derive_pr_url(repo_http_url=repo_http_url, finalized_in_pr=plan_state["finalized_in_pr"])

    merged = node_status == "completed" or plan_state["status"] == "completed"
    if merged:
        human_review_state = "merged"
        finalization_state = "merged_to_main"
        validation_status = "passed"
        smoke_status = "passed"
        merge_readiness = "ready"
    elif implementation_branch and implementation_branch == current_branch:
        human_review_state = "in_review"
        finalization_state = "not_finalized"
        validation_status = "pending"
        smoke_status = "pending"
        merge_readiness = "local_only"
    elif node_status == "review_gated":
        human_review_state = "ready_for_review"
        finalization_state = "not_finalized"
        validation_status = "passed"
        smoke_status = "passed"
        merge_readiness = "ready"
    elif node_status == "decision_gated":
        human_review_state = "not_requested"
        finalization_state = "not_finalized"
        validation_status = "pending"
        smoke_status = "pending"
        merge_readiness = "blocked"
    elif node_status == "blocked":
        human_review_state = "not_requested"
        finalization_state = "not_finalized"
        validation_status = "pending"
        smoke_status = "pending"
        merge_readiness = "blocked"
    else:
        human_review_state = "not_requested"
        finalization_state = "not_finalized"
        validation_status = "pending"
        smoke_status = "pending"
        merge_readiness = "local_only"

    pending_reconciliation = node_status == "completed" and plan_state["status"] != "completed"
    takeover_needed = bool(
        implementation_branch
        and not merged
        and implementation_branch != current_branch
        and node_status in {"ready", "review_gated", "decision_gated"}
    )

    return {
        "human_review_state": human_review_state,
        "pr_url": pr_url,
        "validation_status": validation_status,
        "smoke_status": smoke_status,
        "merge_readiness": merge_readiness,
        "finalization_state": finalization_state,
        "pending_reconciliation": pending_reconciliation,
        "takeover_needed": takeover_needed,
        "execplan_state": plan_state,
    }
