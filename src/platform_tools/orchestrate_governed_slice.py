from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.game_status import get_game_status
from platform_tools.human_operations_status import get_human_operations_status
from platform_tools.managed_repo_status import get_managed_repo_status
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.orchestrator_status import get_orchestrator_status
from platform_tools.reconcile_governed_graph_events import reconcile_governed_graph_events
from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions


COMMAND = "orchestrate-governed-slice"


def run_orchestrate_governed_slice(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    local_repo_path = Path(".").resolve()
    if root_path != local_repo_path:
        managed_code, managed_report = get_managed_repo_status(
            root=root,
            branch=branch,
            execplan_path=execplan_path,
            base_ref=base_ref,
        )
        report = {
            "command": COMMAND,
            "status": managed_report.get("status", ""),
            "ok": bool(managed_report.get("ok", False)),
            "blockers": managed_report.get("blockers", []),
            "branch": managed_report.get("branch", ""),
            "execplan_path": (
                managed_report.get("active_execplan", {}) or {}
            ).get("path", execplan_path or ""),
            "managed_repo": managed_report,
            "next_actions": managed_report.get("next_actions", []),
        }
        return managed_code, report

    post_merge_reconciliation = reconcile_pending_merge_completions(repo_root=root_path, main_ref=base_ref)

    game_code, game_report = get_game_status(
        root=root,
        branch=branch,
        execplan_path=execplan_path,
        base_ref=base_ref,
    )
    active_execplan = game_report.get("active_execplan") if isinstance(game_report, dict) else None
    resolved_execplan_path = execplan_path or (
        str(active_execplan.get("path", "")).strip() if isinstance(active_execplan, dict) else ""
    )
    current_branch = str(game_report.get("branch", branch or "")).strip() if isinstance(game_report, dict) else (branch or "")

    blockers: list[str] = []
    if game_code != 0:
        blockers.extend(f"game_status:{item}" for item in game_report.get("blockers", []))
    if not resolved_execplan_path:
        blockers.append("active_execplan_not_deterministic")

    reconcile_report: dict[str, Any] = {
        "command": "reconcile-governed-graph-events",
        "status": "deferred",
        "ok": False,
        "steps": [],
    }
    if not blockers and resolved_execplan_path:
        reconcile_report = reconcile_governed_graph_events(
            execplan_path=Path(resolved_execplan_path),
            repo_root=Path(root),
        )
        if not reconcile_report.get("ok", False):
            blockers.append("graph_reconciliation_failed")

    merge_code, merge_report = check_merge_readiness(
        root=root,
        execplan_path=resolved_execplan_path or None,
        base_ref=base_ref,
        include_validation_runs=False,
    )
    if merge_code != 0:
        blockers.extend(f"merge_readiness:{item}" for item in merge_report.get("failing_checks", []))

    _, orchestrator_report = get_orchestrator_status(
        root=root,
        branch=current_branch or None,
        execplan_path=resolved_execplan_path or None,
        base_ref=base_ref,
    )
    _, human_ops_report = get_human_operations_status(
        root=root,
        branch=current_branch or None,
        execplan_path=resolved_execplan_path or None,
    )

    next_actions: list[dict[str, Any]] = []
    if blockers:
        next_actions.append({"action": "resolve_blockers", "reason": "orchestration_blocked"})
    else:
        next_actions.extend(orchestrator_report.get("next_actions", []))
        for action in human_ops_report.get("next_actions", []):
            if action not in next_actions:
                next_actions.append(action)

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "branch": current_branch,
        "execplan_path": resolved_execplan_path,
        "reconciliation": reconcile_report,
        "post_merge_reconciliation": post_merge_reconciliation,
        "merge_readiness": {
            "readiness": bool(merge_report.get("readiness", False)),
            "failing_checks": merge_report.get("failing_checks", []),
        },
        "orchestrator_status": {
            "status": orchestrator_report.get("status", ""),
            "next_actions": orchestrator_report.get("next_actions", []),
        },
        "human_operations_status": {
            "status": human_ops_report.get("status", ""),
            "next_actions": human_ops_report.get("next_actions", []),
        },
        "managed_repo": None,
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
