from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.game_status import get_game_status
from platform_tools.human_operations_status import get_human_operations_status
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.orchestrator_status import get_orchestrator_status
from platform_tools.plan_utils import parse_plan
from platform_tools.planner_runtime import apply_move, load_graph, validate_move
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "implementation-orchestrator"
IMPLEMENTABLE_NODE_TYPES = {"task", "artifact", "validation", "handoff"}
PRIORITY_ORDER = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}


def _node_projection(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": str(node.get("node_id", "")).strip(),
        "title": str(node.get("title", "")).strip(),
        "node_type": str(node.get("node_type", "")).strip(),
        "status": str(node.get("status", "")).strip(),
        "priority": str(node.get("priority", "")).strip(),
        "changes": sorted(str(item).strip() for item in node.get("changes", []) if str(item).strip()),
        "path": str(node.get("path", "")).strip(),
    }

def _priority_rank(value: str) -> tuple[int, str]:
    cleaned = (value or "").strip()
    return (PRIORITY_ORDER.get(cleaned, 99), cleaned)


def _candidate_nodes(graph: dict[str, Any], statuses: set[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("node_type", "")).strip()
        status = str(node.get("status", "")).strip()
        if status not in statuses:
            continue
        if node_type and node_type not in IMPLEMENTABLE_NODE_TYPES:
            continue
        candidates.append(node)
    return sorted(
        candidates,
        key=lambda node: (
            _priority_rank(str(node.get("priority", ""))),
            str(node.get("title", "")).strip(),
            str(node.get("node_id", "")).strip(),
        ),
    )


def _select_node(
    *,
    graph: dict[str, Any],
    action: str,
    node_id: str | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    if action == "implement":
        allowed_statuses = {"in_progress"}
    else:
        allowed_statuses = {"ready"}

    if node_id:
        for node in graph.get("nodes", []):
            if isinstance(node, dict) and str(node.get("node_id", "")).strip() == node_id:
                status = str(node.get("status", "")).strip()
                if status not in allowed_statuses:
                    return None, [f"selected_node_wrong_status:{node_id}:{status}"]
                return node, []
        return None, [f"missing_graph_node:{node_id}"]

    candidates = _candidate_nodes(graph, allowed_statuses)
    if not candidates:
        return None, [f"no_{action}_candidate_nodes"]
    return candidates[0], []


def _node_scope_blockers(node: dict[str, Any], execplan_changes: list[str]) -> list[str]:
    scope = {item for item in execplan_changes if item}
    if not scope:
        return []
    node_paths = [str(item).strip() for item in node.get("changes", []) if str(item).strip()]
    node_path = str(node.get("path", "")).strip()
    if node_path:
        node_paths.append(node_path)
    if not node_paths:
        return []
    return [f"selected_node_out_of_scope:{path}" for path in sorted(set(node_paths)) if path not in scope]


def _next_actions(
    *,
    action: str,
    selected_node: dict[str, Any] | None,
    blockers: list[str],
) -> list[dict[str, str]]:
    if blockers:
        return [{"action": "resolve_blockers", "reason": "orchestration_blocked"}]
    if selected_node is None:
        return [{"action": "wait_for_graph_candidate", "reason": "no_selectable_node"}]
    if action == "inspect":
        if str(selected_node.get("status", "")).strip() == "ready":
            return [{"action": "select", "node_id": str(selected_node.get("node_id", "")).strip(), "reason": "ready_node_detected"}]
        return [{"action": "implement", "node_id": str(selected_node.get("node_id", "")).strip(), "reason": "in_progress_node_detected"}]
    if action == "select":
        return [{"action": "implement", "node_id": str(selected_node.get("node_id", "")).strip(), "reason": "node_selected"}]
    if action == "implement":
        return [{"action": "verify", "node_id": str(selected_node.get("node_id", "")).strip(), "reason": "implementation_move_applied"}]
    return []


def run_implementation_orchestrator(
    *,
    root: str = ".",
    action: str = "inspect",
    graph_id: str | None = None,
    node_id: str | None = None,
    execplan_path: str | None = None,
    branch: str | None = None,
    base_ref: str = "main",
    selection_ref: str | None = None,
    commit_ref: str | None = None,
    target_status: str = "in_review",
) -> tuple[int, dict[str, Any]]:
    game_code, game_report = get_game_status(
        root=root,
        branch=branch,
        execplan_path=execplan_path,
        base_ref=base_ref,
    )
    branch_name = str(game_report.get("branch", branch or "")).strip()
    active_execplan = game_report.get("active_execplan") or {}
    resolved_execplan_path = str(active_execplan.get("path", execplan_path or "")).strip()
    execplan_id = str(active_execplan.get("id", "")).strip()
    execplan_changes: list[str] = []
    next_validations: list[str] = []
    if resolved_execplan_path:
        parsed = parse_plan(Path(resolved_execplan_path))
        execplan_id = execplan_id or str(parsed.frontmatter.get("id", "")).strip()
        execplan_changes = [str(item).strip() for item in parsed.frontmatter.get("changes", []) if str(item).strip()]
        validation = parsed.frontmatter.get("validation", {})
        tests = validation.get("tests", []) if isinstance(validation, dict) else []
        next_validations = sorted(
            {
                str(item.get("command", "")).strip()
                for item in tests
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            }
        )

    merge_code, merge_report = check_merge_readiness(
        root=root,
        execplan_path=resolved_execplan_path or execplan_path,
        base_ref=base_ref,
        include_validation_runs=False,
    )
    remaining_work_code, remaining_work_report = check_remaining_work_graph(
        root=root,
        branch=branch_name or None,
        execplan_path=resolved_execplan_path or execplan_path,
    )
    _, status_report = get_orchestrator_status(
        root=root,
        branch=branch_name or None,
        execplan_path=resolved_execplan_path or execplan_path,
        base_ref=base_ref,
    )
    _, human_operations_report = get_human_operations_status(
        root=root,
        branch=branch_name or None,
        execplan_path=resolved_execplan_path or execplan_path,
    )

    blockers: list[str] = []
    if game_code != 0:
        blockers.extend(f"game_status:{item}" for item in game_report.get("blockers", []))
    active_game = game_report.get("active_game", {})
    if str(active_game.get("id", "")).strip() != "game-implementation":
        blockers.append(f"active_game_mismatch:{active_game.get('id', '')}")
    if not execplan_id:
        blockers.append("active_execplan_required")

    if merge_code != 0:
        blockers.extend(f"merge_readiness:{item}" for item in merge_report.get("failing_checks", []))

    if remaining_work_code != 0:
        blockers.extend(f"remaining_work_graph:{item}" for item in remaining_work_report.get("errors", []))
    slice_summary = remaining_work_report.get("active_node")
    if execplan_id and slice_summary is None:
        blockers.append(f"current_execplan_not_registered:{execplan_id}")
    elif slice_summary and str(slice_summary.get("target_execplan_id", "")).strip() != execplan_id:
        blockers.append(f"active_slice_execplan_mismatch:{slice_summary.get('target_execplan_id', '')}")
    elif slice_summary and str(slice_summary.get("status", "")).strip() != "ready":
        blockers.append(f"active_slice_not_ready:{slice_summary.get('node_id', '')}:{slice_summary.get('status', '')}")
    elif slice_summary and bool(slice_summary.get("action_state", {}).get("action_required", False)):
        blockers.append(f"active_slice_requires_graph_action:{slice_summary.get('node_id', '')}")

    graph = None
    selected_node = None
    graph_blockers: list[str] = []
    if graph_id:
        try:
            graph = load_graph(root=root, graph_id=graph_id)
            selected_node, graph_blockers = _select_node(graph=graph, action=action, node_id=node_id)
            if selected_node:
                graph_blockers.extend(_node_scope_blockers(selected_node, execplan_changes))
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            graph_blockers.append(f"{exc.__class__.__name__}:{exc}")
    elif action != "inspect":
        graph_blockers.append("graph_id_required_for_mutation")
    blockers.extend(graph_blockers)

    move_validation: dict[str, Any] | None = None
    move_result: dict[str, Any] | None = None
    if not blockers and action in {"select", "implement"} and selected_node is not None and graph_id:
        if action == "select":
            applied_move = "select"
            evidence = {
                "selection_ref": selection_ref or f"{execplan_id}:{selected_node['node_id']}",
            }
            destination_status = "in_progress"
        else:
            applied_move = "implement"
            if not commit_ref:
                blockers.append("commit_ref_required_for_implement")
            evidence = {"commit_ref": commit_ref or ""}
            destination_status = target_status

        if not blockers:
            validation_code, move_validation = validate_move(
                root=root,
                graph_id=graph_id,
                node_id=str(selected_node.get("node_id", "")).strip(),
                phase="implementation",
                move=applied_move,
                target_status=destination_status,
                evidence=evidence,
            )
            if validation_code != 0:
                blockers.extend(f"move_validation:{item}" for item in move_validation.get("errors", []))
            else:
                _, move_result = apply_move(
                    root=root,
                    graph_id=graph_id,
                    node_id=str(selected_node.get("node_id", "")).strip(),
                    phase="implementation",
                    move=applied_move,
                    target_status=destination_status,
                    evidence=evidence,
                )
                graph = load_graph(root=root, graph_id=graph_id)
                selected_node = next(
                    (
                        node
                        for node in graph.get("nodes", [])
                        if isinstance(node, dict) and str(node.get("node_id", "")).strip() == str(selected_node.get("node_id", "")).strip()
                    ),
                    selected_node,
                )

    report = {
        "command": COMMAND,
        "action": action,
        "status": "ok" if not blockers else "blocked",
        "blockers": sorted(set(str(item) for item in blockers if str(item).strip())),
        "next_validations": next_validations,
        "ok": not blockers,
        "branch": branch_name,
        "execplan_id": execplan_id,
        "execplan_path": resolved_execplan_path,
        "graph_id": graph_id or "",
        "active_game": active_game,
        "active_slice": slice_summary,
        "selected_node": _node_projection(selected_node) if selected_node else None,
        "graph_move_validation": move_validation,
        "graph_move_result": move_result,
        "merge_readiness": {
            "readiness": bool(merge_report.get("readiness", False)),
            "failing_checks": merge_report.get("failing_checks", []),
        },
        "orchestrator_status": {
            "status": status_report.get("status", ""),
            "next_actions": status_report.get("next_actions", []),
        },
        "human_operations_status": {
            "status": human_operations_report.get("status", ""),
            "next_actions": human_operations_report.get("next_actions", []),
        },
        "next_actions": _next_actions(action=action, selected_node=selected_node, blockers=blockers),
    }
    return (1 if blockers else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--action", choices=["inspect", "select", "implement"], default="inspect")
    parser.add_argument("--graph-id", default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--selection-ref", default=None)
    parser.add_argument("--commit-ref", default=None)
    parser.add_argument("--target-status", default="in_review")
    args = parser.parse_args()
    code, report = run_implementation_orchestrator(
        root=args.root,
        action=args.action,
        graph_id=args.graph_id,
        node_id=args.node_id,
        execplan_path=args.execplan_path,
        branch=args.branch,
        base_ref=args.base_ref,
        selection_ref=args.selection_ref,
        commit_ref=args.commit_ref,
        target_status=args.target_status,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
