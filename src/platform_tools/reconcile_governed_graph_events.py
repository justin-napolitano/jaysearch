from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.plan_utils import parse_plan
from platform_tools.reconcile_remaining_work_merge import reconcile_remaining_work_merge
from platform_tools.reconcile_remaining_work_transition import reconcile_remaining_work_transition
from platform_tools.register_remaining_work_node import register_remaining_work_node


def reconcile_governed_graph_events(
    *,
    execplan_path: Path,
    repo_root: Path,
) -> dict[str, Any]:
    plan = parse_plan(execplan_path)
    execplan_id = str(plan.frontmatter.get("id", "")).strip()
    steps: list[dict[str, Any]] = []

    register_report = register_remaining_work_node(execplan_path=execplan_path, repo_root=repo_root)
    steps.append(register_report)
    if not register_report.get("ok", False):
        return {
            "command": "reconcile-governed-graph-events",
            "status": "blocked",
            "ok": False,
            "execplan_id": execplan_id,
            "steps": steps,
        }

    transition_report = reconcile_remaining_work_transition(execplan_path=execplan_path, repo_root=repo_root)
    steps.append(transition_report)
    if not transition_report.get("ok", False):
        return {
            "command": "reconcile-governed-graph-events",
            "status": "blocked",
            "ok": False,
            "execplan_id": execplan_id,
            "steps": steps,
        }

    merge_report: dict[str, Any] | None = None
    if str(transition_report.get("target_state", "")).strip() == "ready":
        try:
            merge_report = reconcile_remaining_work_merge(execplan_path=execplan_path, repo_root=repo_root)
            steps.append(merge_report)
        except ValueError as exc:
            steps.append(
                {
                    "command": "reconcile-remaining-work-merge",
                    "status": "deferred",
                    "ok": True,
                    "reason": str(exc),
                }
            )

    return {
        "command": "reconcile-governed-graph-events",
        "status": "ok",
        "ok": True,
        "execplan_id": execplan_id,
        "steps": steps,
        "merge_completed": bool(merge_report and merge_report.get("completion_ref")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execplan-path", required=True)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    report = reconcile_governed_graph_events(execplan_path=Path(args.execplan_path), repo_root=Path(args.repo_root))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
