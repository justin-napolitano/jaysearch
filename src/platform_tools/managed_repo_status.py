from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.execplan_discovery import discover_execplan
from platform_tools.plan_utils import parse_plan


COMMAND = "managed-repo-status"
REQUIRED_PATHS = (
    ".agent/execplans",
    "artifacts/planner/research/remaining-work-graph.json",
    "artifacts/provider-sync/github-projects-field-map.json",
    "docs/queued-execplans.md",
    "spec/workflow.yaml",
)


def _load_graph(root: Path) -> dict[str, Any]:
    path = root / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _required_artifact_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            findings.append(f"missing_required_artifact:{rel}")
    return findings


def _field_map_findings(root: Path) -> list[str]:
    path = root / "artifacts" / "provider-sync" / "github-projects-field-map.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["provider_field_map_invalid_json"]
    if not isinstance(payload, dict):
        return ["provider_field_map_not_object"]
    project_id = str(payload.get("project_id", "")).strip()
    findings: list[str] = []
    if not project_id:
        findings.append("provider_field_map_missing_project_id")
    elif project_id.startswith("pending:"):
        findings.append("managed_repo_board_bootstrap_incomplete")
    fields = payload.get("fields", {}) if isinstance(payload.get("fields"), dict) else {}
    if "completion_pr" not in fields:
        findings.append("provider_field_map_missing_completion_pr")
    return findings


def _active_node(graph: dict[str, Any], *, branch: str, execplan_id: str) -> dict[str, Any] | None:
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if str(node.get("implementation_branch", "")).strip() == branch:
            return node
        if execplan_id and str(node.get("target_execplan_id", "")).strip() == execplan_id:
            return node
    return None


def get_managed_repo_status(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root)
    blockers = _required_artifact_findings(root_path)
    blockers.extend(_field_map_findings(root_path))
    current_branch = branch or get_current_branch(root=root_path)
    branch_policy = evaluate_branch_policy(current_branch, root=root_path) if current_branch else {
        "ok": False,
        "findings": ["branch_detection_failed"],
        "allowed_branch_patterns": [],
        "forbidden_branches": [],
        "current_branch": "",
    }
    blockers.extend(str(item) for item in branch_policy.get("findings", []) if str(item).strip())

    selected_execplan_path = execplan_path
    strategy = "explicit"
    candidates: list[str] = []
    if selected_execplan_path is None and not blockers:
        selected, candidates, strategy = discover_execplan(root_path, current_branch, base_ref)
        selected_execplan_path = selected.as_posix() if selected else None
        if strategy.startswith("ambiguous_"):
            blockers.append(f"active_execplan_not_deterministic:{strategy}")

    active_execplan: dict[str, Any] | None = None
    active_node: dict[str, Any] | None = None
    if selected_execplan_path and not blockers:
        parsed = parse_plan(Path(selected_execplan_path))
        execplan_id = str(parsed.frontmatter.get("id", "")).strip()
        active_execplan = {
            "id": execplan_id,
            "path": selected_execplan_path,
            "status": str(parsed.frontmatter.get("status", "")).strip(),
            "title": str(parsed.frontmatter.get("title", "")).strip(),
        }
        graph = _load_graph(root_path)
        active_node = _active_node(graph, branch=current_branch, execplan_id=execplan_id)

    next_actions: list[dict[str, str]] = []
    if blockers:
        if any(item.startswith("managed_repo_board_bootstrap_") or item.startswith("provider_field_map_") for item in blockers):
            next_actions.append({"action": "run_bootstrap_managed_repo", "reason": "managed_repo_bootstrap_incomplete"})
        next_actions.append({"action": "resolve_managed_repo_blockers", "reason": "managed_repo_blocked"})
    elif active_node and str(active_node.get("status", "")).strip() in {"decision_gated", "review_gated"}:
        next_actions.append({"action": "finalize_or_review_plan", "reason": "managed_repo_plan_not_ready"})
    elif active_node and str(active_node.get("status", "")).strip() == "ready":
        next_actions.append({"action": "start_managed_slice", "reason": "managed_repo_ready_slice"})
    else:
        next_actions.append({"action": "inspect_managed_repo_queue", "reason": "managed_repo_no_active_ready_slice"})

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "root": root_path.as_posix(),
        "branch": current_branch,
        "blockers": sorted(set(blockers)),
        "required_artifacts": list(REQUIRED_PATHS),
        "branch_policy": branch_policy,
        "execplan_discovery": {
            "strategy": strategy,
            "candidates": candidates,
            "selected": selected_execplan_path or "",
        },
        "active_execplan": active_execplan,
        "active_node": active_node,
        "next_actions": next_actions,
    }
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--base-ref", default="main")
    args = parser.parse_args()
    code, report = get_managed_repo_status(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
