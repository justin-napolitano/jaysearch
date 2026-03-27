from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.get_graph_state import get_graph_state
from platform_tools.get_worker_status import get_worker_status
from platform_tools.local_runtime.runtime_check import check_local_runtime
from platform_tools.managed_repo_status import get_managed_repo_status
from platform_tools.mergeback_orchestration import (
    prepare_next_impl_branch,
    project_merge_readiness,
    project_pr_integration_contract,
)


API_VERSION = "control-plane.v1"


def envelope(*, command: str, status: str, ok: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "api_version": API_VERSION,
        "command": command,
        "status": status,
        "ok": ok,
    }
    if payload:
        body.update(payload)
    return body


def _load_graph(root: Path) -> dict[str, Any]:
    path = root / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_initiative_branch(*, root: Path, branch: str) -> str:
    if branch.startswith("initiative/"):
        return branch
    if not branch.startswith("impl-execplan/"):
        return ""
    graph = _load_graph(root)
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if str(node.get("implementation_branch", "")).strip() == branch:
            return str(node.get("initiative_branch", "")).strip()
    return ""


def _branch_role(branch: str) -> str:
    if branch.startswith("initiative/"):
        return "initiative"
    if branch.startswith("impl-execplan/"):
        return "implementation_execplan"
    return "other"


def _projection(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(report, dict):
        return None
    return {
        "status": str(report.get("status", "")).strip(),
        "ok": bool(report.get("ok", False)),
        "blockers": [str(item).strip() for item in report.get("blockers", []) if str(item).strip()],
    }


def get_control_plane_status(*, root: str = ".", repo_root: str | None = None) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    target_root = Path(repo_root).resolve() if repo_root else root_path
    current_branch = get_current_branch(root=root_path)
    branch_role = _branch_role(current_branch)
    initiative_branch = _derive_initiative_branch(root=root_path, branch=current_branch)

    graph_code, graph_report = get_graph_state(
        root=target_root.as_posix(),
        initiative_branch=initiative_branch or None,
    )
    runtime_code, runtime_report = check_local_runtime(
        root=root_path.as_posix(),
        repo_root=target_root.as_posix(),
        verify_managed_repo=True,
    )
    worker_code, worker_report = get_worker_status(root=target_root.as_posix())
    managed_repo_code, managed_repo_report = get_managed_repo_status(
        root=target_root.as_posix(),
        branch=initiative_branch or current_branch or None,
    )

    branch_preparation_report: dict[str, Any] | None = None
    merge_readiness_report: dict[str, Any] | None = None
    pr_integration_report: dict[str, Any] | None = None

    if branch_role == "initiative" and initiative_branch:
        _, branch_preparation_report = prepare_next_impl_branch(
            root=root_path.as_posix(),
            initiative_branch=initiative_branch,
        )
    elif branch_role == "implementation_execplan" and initiative_branch:
        _, merge_readiness_report = project_merge_readiness(
            root=root_path.as_posix(),
            source_branch=current_branch,
            initiative_branch=initiative_branch,
        )
        _, pr_integration_report = project_pr_integration_contract(
            root=root_path.as_posix(),
            source_branch=current_branch,
            initiative_branch=initiative_branch,
        )

    blockers: list[str] = []
    for report in (
        managed_repo_report,
        graph_report,
        runtime_report,
        worker_report,
        branch_preparation_report,
        merge_readiness_report,
        pr_integration_report,
    ):
        if isinstance(report, dict):
            blockers.extend(str(item).strip() for item in report.get("blockers", []) if str(item).strip())

    ok = (
        managed_repo_code == 0
        and graph_code == 0
        and runtime_code == 0
        and worker_code == 0
        and not blockers
    )
    return (0 if ok else 1), envelope(
        command="get-control-plane-status",
        status="ok" if ok else "blocked",
        ok=ok,
        payload={
            "current_branch": current_branch,
            "branch_role": branch_role,
            "initiative_branch": initiative_branch,
            "repo_root": target_root.as_posix(),
            "blockers": sorted(set(blockers)),
            "checks": {
                "managed_repo": _projection(managed_repo_report),
                "graph": _projection(graph_report),
                "local_runtime": _projection(runtime_report),
                "worker_status": _projection(worker_report),
                "branch_preparation": _projection(branch_preparation_report),
                "merge_readiness": _projection(merge_readiness_report),
                "pr_integration": _projection(pr_integration_report),
            },
        },
    )


def get_next_orchestration_action(*, root: str = ".", repo_root: str | None = None) -> tuple[int, dict[str, Any]]:
    _, status_report = get_control_plane_status(root=root, repo_root=repo_root)
    current_branch = str(status_report.get("current_branch", "")).strip()
    branch_role = str(status_report.get("branch_role", "")).strip()
    initiative_branch = str(status_report.get("initiative_branch", "")).strip()
    resolved_repo_root = str(status_report.get("repo_root", "")).strip()
    checks = status_report.get("checks", {}) if isinstance(status_report.get("checks"), dict) else {}
    blockers = [str(item).strip() for item in status_report.get("blockers", []) if str(item).strip()]

    recommended_action = "none"
    command_ref = ""
    managed_repo = checks.get("managed_repo") or {}
    if managed_repo.get("blockers"):
        recommended_action = "resolve_control_plane_blockers"
        command_ref = "bin/managed-repo-status"
    elif branch_role == "other":
        recommended_action = "switch_to_initiative_branch"
        command_ref = "git switch initiative/<name>"
    elif checks.get("worker_status", {}).get("blockers"):
        recommended_action = "inspect_worker_sessions"
        command_ref = "bin/get-worker-status"
    elif checks.get("local_runtime", {}).get("blockers"):
        recommended_action = "run_local_runtime_check"
        command_ref = "bin/local-runtime-check"
    elif branch_role == "initiative":
        branch_prep = checks.get("branch_preparation") or {}
        if branch_prep.get("ok", False):
            recommended_action = "cut_impl_branch"
            command_ref = "bin/prepare-next-impl-branch"
        else:
            recommended_action = "resolve_control_plane_blockers"
            command_ref = "bin/prepare-next-impl-branch"
    elif branch_role == "implementation_execplan":
        merge_readiness = checks.get("merge_readiness") or {}
        merge_blockers = merge_readiness.get("blockers", [])
        if "stale_initiative_base" in merge_blockers:
            recommended_action = "restack_on_initiative"
            command_ref = "bin/get-merge-readiness"
        elif merge_readiness.get("ok", False):
            recommended_action = "open_pr_to_initiative"
            command_ref = "bin/get-pr-integration-contract"
        else:
            recommended_action = "resolve_mergeback_blockers"
            command_ref = "bin/get-merge-readiness"

    ok = recommended_action not in {"resolve_control_plane_blockers", "resolve_mergeback_blockers"} and bool(command_ref)
    return (0 if ok else 1), envelope(
        command="get-next-orchestration-action",
        status="ok" if ok else "blocked",
        ok=ok,
        payload={
            "current_branch": current_branch,
            "branch_role": branch_role,
            "initiative_branch": initiative_branch,
            "repo_root": resolved_repo_root,
            "recommended_action": recommended_action,
            "command_ref": command_ref,
            "blockers": blockers,
        },
    )
