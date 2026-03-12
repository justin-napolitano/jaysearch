from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.human_operations_runtime import DEFAULT_FIELD_MAP_PATH, load_field_map_state, review_projection_for_node
from platform_tools.integrations.github_projects_sync import build_github_projects_sync_plan
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "human-operations-status"


def _slice_nodes(report: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for key in ("ready_nodes", "blocked_nodes", "completed_nodes"):
        for node in report.get(key, []):
            if isinstance(node, dict):
                nodes[str(node.get("node_id", "")).strip()] = node
    active = report.get("active_node")
    if isinstance(active, dict):
        nodes[str(active.get("node_id", "")).strip()] = active
    return [nodes[key] for key in sorted(nodes)]


def get_human_operations_status(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    field_map_path: str = DEFAULT_FIELD_MAP_PATH,
) -> tuple[int, dict[str, Any]]:
    remaining_code, remaining_report = check_remaining_work_graph(
        root=root,
        branch=branch,
        execplan_path=execplan_path,
    )
    current_branch = str(remaining_report.get("branch", branch or "")).strip()
    blockers = [f"remaining_work_graph:{item}" for item in remaining_report.get("errors", [])] if remaining_code != 0 else []

    field_map_state = load_field_map_state(root=root, field_map_path=field_map_path)
    if field_map_state["field_map_exists"] and not field_map_state["project_id"]:
        blockers.append("board_runtime:missing_project_id")
    blockers.extend(f"board_runtime:duplicate_item_id:{item}" for item in field_map_state["duplicate_item_ids"])

    sync_summary: dict[str, Any] = {
        "status": "deferred",
        "ok": False,
        "operation_count": 0,
        "create_count": 0,
        "update_count": 0,
        "blockers": [],
    }
    if field_map_state["field_map_exists"]:
        sync_code, sync_plan = build_github_projects_sync_plan(
            root=root,
            field_map_path=field_map_path,
            branch=current_branch or None,
            execplan_path=execplan_path,
        )
        sync_summary = {
            "status": sync_plan.get("status", ""),
            "ok": bool(sync_plan.get("ok", False)),
            "operation_count": int(sync_plan.get("operation_count", 0)),
            "create_count": int(sync_plan.get("create_count", 0)),
            "update_count": int(sync_plan.get("update_count", 0)),
            "blockers": [str(item) for item in sync_plan.get("blockers", [])],
        }
        if sync_code != 0:
            blockers.extend(f"board_sync:{item}" for item in sync_plan.get("blockers", []))

    review_nodes: list[dict[str, Any]] = []
    for node in _slice_nodes(remaining_report):
        review_projection = review_projection_for_node(node, root=root, current_branch=current_branch)
        review_nodes.append(
            {
                "node_id": str(node.get("node_id", "")).strip(),
                "title": str(node.get("title", "")).strip(),
                "status": str(node.get("status", "")).strip(),
                "target_execplan_id": str(node.get("target_execplan_id", "")).strip(),
                "implementation_branch": str(node.get("implementation_branch", "")).strip(),
                "human_review_state": review_projection["human_review_state"],
                "merge_readiness": review_projection["merge_readiness"],
                "finalization_state": review_projection["finalization_state"],
                "pr_url": review_projection["pr_url"],
                "pending_reconciliation": bool(review_projection["pending_reconciliation"]),
                "takeover_needed": bool(review_projection["takeover_needed"]),
                "execplan_status": review_projection["execplan_state"]["status"],
                "execplan_path": review_projection["execplan_state"]["path"],
            }
        )

    counts = {
        "not_requested": 0,
        "ready_for_review": 0,
        "in_review": 0,
        "merged": 0,
    }
    for node in review_nodes:
        state = str(node.get("human_review_state", "")).strip()
        if state in counts:
            counts[state] += 1

    pending_reconciliation = [node for node in review_nodes if node["pending_reconciliation"]]
    takeover_candidates = [node for node in review_nodes if node["takeover_needed"]]

    next_actions: list[dict[str, str]] = []
    if pending_reconciliation:
        next_actions.append(
            {
                "action": "reconcile_completed_execplans",
                "reason": "merged_slice_missing_completed_metadata",
            }
        )
    if field_map_state["board_bootstrapped"] and sync_summary["operation_count"] > 0:
        next_actions.append(
            {
                "action": "sync_review_board",
                "reason": "board_projection_drift_detected",
            }
        )
    if counts["ready_for_review"] > 0:
        next_actions.append(
            {
                "action": "review_ready_items",
                "reason": "review_gated_nodes_detected",
            }
        )
    if takeover_candidates:
        next_actions.append(
            {
                "action": "resume_takeover_candidates",
                "reason": "nonterminal_slice_requires_portable_handoff",
            }
        )
    if not next_actions:
        next_actions.append({"action": "monitor_board_runtime", "reason": "no_human_operations_work_pending"})

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "branch": current_branch,
        "execplan_id": remaining_report.get("execplan_id", ""),
        "active_node": remaining_report.get("active_node"),
        "board_runtime": field_map_state,
        "board_projection": sync_summary,
        "review_summary": {
            "counts": counts,
            "pending_reconciliation_count": len(pending_reconciliation),
            "takeover_candidate_count": len(takeover_candidates),
        },
        "review_nodes": review_nodes,
        "next_actions": next_actions,
        "evidence_refs": sorted(
            {
                "artifacts/planner/research/remaining-work-graph.json",
                str(Path(root) / field_map_path),
                "spec/governance.yaml",
                "spec/providers/github-projects.schema.yaml",
            }
        ),
    }
    return (1 if blockers else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--field-map-path", default=DEFAULT_FIELD_MAP_PATH)
    args = parser.parse_args()
    code, report = get_human_operations_status(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        field_map_path=args.field_map_path,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
