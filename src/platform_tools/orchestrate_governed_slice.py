from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.control_plane import get_control_plane_status, get_next_orchestration_action
from platform_tools.plan_utils import parse_plan
from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions


COMMAND = "orchestrate-governed-slice"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")


def _effective_base_ref(
    *,
    repo_root: Path,
    branch: str,
    execplan_path: str,
    default_base_ref: str,
) -> str:
    if not branch.startswith("impl-execplan/") or not execplan_path:
        return default_base_ref
    graph_path = repo_root / GRAPH_PATH
    if not graph_path.exists():
        return default_base_ref
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_base_ref
    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list):
        return default_base_ref
    try:
        execplan_id = str(parse_plan(Path(execplan_path)).frontmatter.get("id", "")).strip()
    except Exception:
        return default_base_ref
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("target_execplan_id", "")).strip() != execplan_id:
            continue
        initiative_branch = str(node.get("initiative_branch", "")).strip()
        integration_mode = str(node.get("integration_mode", "")).strip()
        if integration_mode == "via_initiative" and initiative_branch:
            return initiative_branch
        break
    return default_base_ref


def run_orchestrate_governed_slice(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    local_repo_path = Path(".").resolve()
    target_repo_root = root_path if root_path != local_repo_path else local_repo_path
    post_merge_reconciliation = reconcile_pending_merge_completions(
        repo_root=local_repo_path,
        main_ref=base_ref,
    )

    status_code, control_plane_status = get_control_plane_status(
        root=local_repo_path.as_posix(),
        repo_root=target_repo_root.as_posix(),
    )
    action_code, next_action_report = get_next_orchestration_action(
        root=local_repo_path.as_posix(),
        repo_root=target_repo_root.as_posix(),
    )

    blockers = [
        str(item).strip()
        for item in control_plane_status.get("blockers", [])
        if str(item).strip()
    ]
    if action_code != 0:
        blockers.extend(
            str(item).strip()
            for item in next_action_report.get("blockers", [])
            if str(item).strip()
        )

    next_actions: list[dict[str, Any]] = []
    recommended_action = str(next_action_report.get("recommended_action", "")).strip()
    command_ref = str(next_action_report.get("command_ref", "")).strip()
    if recommended_action and recommended_action != "none":
        next_actions.append(
            {
                "action": recommended_action,
                "command_ref": command_ref,
                "reason": "control_plane_projection",
            }
        )

    ok = status_code == 0 and action_code == 0 and not blockers
    report = {
        "command": COMMAND,
        "status": "ok" if ok else "blocked",
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "branch": str(control_plane_status.get("current_branch", branch or "")).strip(),
        "branch_role": str(control_plane_status.get("branch_role", "")).strip(),
        "initiative_branch": str(control_plane_status.get("initiative_branch", "")).strip(),
        "repo_root": target_repo_root.as_posix(),
        "base_ref": base_ref,
        "execplan_path": execplan_path or "",
        "control_plane_status": control_plane_status,
        "next_orchestration_action": next_action_report,
        "post_merge_reconciliation": post_merge_reconciliation,
        "managed_repo": (control_plane_status.get("checks", {}) or {}).get("managed_repo"),
        "next_actions": next_actions,
    }
    return (0 if ok else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--base-ref", default="main")
    args = parser.parse_args()
    code, report = run_orchestrate_governed_slice(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
