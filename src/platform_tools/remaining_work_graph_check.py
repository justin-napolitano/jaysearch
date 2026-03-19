from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import get_current_branch
from platform_tools.plan_utils import parse_plan


COMMAND = "remaining-work-graph-check"
TERMINAL_STATUSES = {"completed"}
BLOCKED_STATUSES = {"blocked", "review_gated", "decision_gated"}
READY_STATUSES = {"ready"}
QUEUE_ACTION_PATTERN = re.compile(r"canonical_last_graph_action_id:\s*`([^`]+)`")
QUEUE_READY_PATTERN = re.compile(r"canonical_ready_order:\s*`([^`]+)`")
QUEUE_AUTHORITY_PATTERN = re.compile(r"projection_authority:\s*`([^`]+)`")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _dependency_map(edges: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("relation") != "depends_on":
            continue
        mapping.setdefault(str(edge.get("from", "")).strip(), []).append(str(edge.get("to", "")).strip())
    return {key: sorted(set(value for value in values if value)) for key, values in mapping.items()}


def _gating_map(edges: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("relation") != "gated_by":
            continue
        mapping.setdefault(str(edge.get("from", "")).strip(), []).append(str(edge.get("to", "")).strip())
    return {key: sorted(set(value for value in values if value)) for key, values in mapping.items()}


def _is_slice_node(node: dict[str, Any]) -> bool:
    goal_area = str(node.get("goal_area", "")).strip()
    return bool(goal_area) and goal_area != "reference"


def _queue_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "canonical_last_graph_action_id": "", "canonical_ready_order": [], "projection_authority": ""}
    text = path.read_text(encoding="utf-8")
    action_match = QUEUE_ACTION_PATTERN.search(text)
    ready_match = QUEUE_READY_PATTERN.search(text)
    authority_match = QUEUE_AUTHORITY_PATTERN.search(text)
    ready_values = []
    if ready_match:
        ready_values = [item.strip() for item in ready_match.group(1).split(",") if item.strip()]
    return {
        "exists": True,
        "canonical_last_graph_action_id": action_match.group(1).strip() if action_match else "",
        "canonical_ready_order": ready_values,
        "projection_authority": authority_match.group(1).strip() if authority_match else "",
    }


def _ordering_tuple(item: dict[str, Any]) -> tuple[int, str, str]:
    ordering = item.get("ordering", {}) if isinstance(item.get("ordering"), dict) else {}
    ready_order = ordering.get("ready_order")
    if not isinstance(ready_order, int):
        ready_order = 999999
    tie_breaker = str(ordering.get("tie_breaker", "")).strip()
    return (ready_order, tie_breaker, str(item.get("node_id", "")).strip())


def _node_projection(
    node: dict[str, Any],
    *,
    dependency_map: dict[str, list[str]],
    gating_map: dict[str, list[str]],
    nodes: dict[str, dict[str, Any]],
    branch: str,
    execplan_id: str | None,
) -> dict[str, Any]:
    node_id = str(node.get("node_id", "")).strip()
    depends_on = dependency_map.get(node_id, [])
    gated_by = gating_map.get(node_id, [])
    dependency_states = [
        {
            "node_id": dep_id,
            "status": str(nodes.get(dep_id, {}).get("status", "")).strip(),
        }
        for dep_id in depends_on
    ]
    dependencies_complete = all(item["status"] in TERMINAL_STATUSES for item in dependency_states)
    implementation_branch = str(node.get("implementation_branch", "")).strip()
    target_execplan_id = str(node.get("target_execplan_id", "")).strip()
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    action_state = node.get("action_state", {}) if isinstance(node.get("action_state"), dict) else {}
    active = bool(
        _is_slice_node(node)
        and (
            (implementation_branch and implementation_branch == branch)
            or (execplan_id and execplan_id == target_execplan_id)
        )
    )
    return {
        "node_id": node_id,
        "title": str(node.get("title", "")).strip(),
        "status": str(node.get("status", "")).strip(),
        "status_reason": str(node.get("status_reason", "")).strip(),
        "gating_class": str(node.get("gating_class", "")).strip(),
        "goal_area": str(node.get("goal_area", "")).strip(),
        "target_execplan_id": target_execplan_id,
        "implementation_branch": implementation_branch,
        "initiative_branch": str(node.get("initiative_branch", "")).strip(),
        "parent_initiative_node": str(node.get("parent_initiative_node", "")).strip(),
        "integration_mode": str(node.get("integration_mode", "")).strip(),
        "availability_target_ref": str(node.get("availability_target_ref", "")).strip(),
        "availability_status": str(node.get("availability_status", "")).strip(),
        "availability_ref": str(node.get("availability_ref", "")).strip(),
        "conflict_domains": sorted(str(item).strip() for item in node.get("conflict_domains", []) if str(item).strip()),
        "expected_artifacts": sorted(str(item).strip() for item in node.get("expected_artifacts", []) if str(item).strip()),
        "depends_on": depends_on,
        "gated_by": gated_by,
        "dependency_states": dependency_states,
        "dependencies_complete": dependencies_complete,
        "active": active,
        "eligible_now": _is_slice_node(node) and str(node.get("status", "")).strip() in READY_STATUSES and dependencies_complete,
        "ordering": {
            "queue_position": ordering.get("queue_position"),
            "ready_order": ordering.get("ready_order"),
            "tie_breaker": str(ordering.get("tie_breaker", "")).strip(),
            "source_action_id": str(ordering.get("source_action_id", "")).strip(),
        },
        "action_state": {
            "last_action_id": str(action_state.get("last_action_id", "")).strip(),
            "last_action": str(action_state.get("last_action", "")).strip(),
            "action_required": bool(action_state.get("action_required", False)),
            "reorder_requires_human": bool(action_state.get("reorder_requires_human", False)),
            "reorder_blockers": sorted(
                str(item).strip() for item in action_state.get("reorder_blockers", []) if str(item).strip()
            ),
        },
    }


def check_remaining_work_graph(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    graph_path = cwd / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    schema_path = cwd / "spec" / "remaining-work-graph.schema.yaml"
    queue_path = cwd / "docs" / "queued-execplans.md"

    if not graph_path.exists():
        return 1, {"command": COMMAND, "status": "blocked", "ok": False, "errors": ["missing_remaining_work_graph"]}
    if not schema_path.exists():
        return 1, {"command": COMMAND, "status": "blocked", "ok": False, "errors": ["missing_remaining_work_schema"]}

    graph = _load_json(graph_path)
    schema = _load_yaml(schema_path)
    errors: list[str] = []

    for field in schema.get("required", []):
        if field not in graph:
            errors.append(f"missing_graph_field:{field}")

    nodes_list = graph.get("nodes", [])
    edges_list = graph.get("edges", [])
    actions_list = graph.get("graph_actions", [])
    ordering_policy = graph.get("ordering_policy", {})
    queue_projection = graph.get("queue_projection", {})
    if not isinstance(nodes_list, list):
        errors.append("invalid_nodes_type")
        nodes_list = []
    if not isinstance(edges_list, list):
        errors.append("invalid_edges_type")
        edges_list = []
    if not isinstance(actions_list, list):
        errors.append("invalid_graph_actions_type")
        actions_list = []
    if not isinstance(ordering_policy, dict):
        errors.append("invalid_ordering_policy_type")
        ordering_policy = {}
    if not isinstance(queue_projection, dict):
        errors.append("invalid_queue_projection_type")
        queue_projection = {}

    node_props = schema.get("properties", {}).get("nodes", {}).get("items", {}).get("properties", {})
    node_required = schema.get("properties", {}).get("nodes", {}).get("items", {}).get("required", [])
    edge_props = schema.get("properties", {}).get("edges", {}).get("items", {}).get("properties", {})
    edge_required = schema.get("properties", {}).get("edges", {}).get("items", {}).get("required", [])
    action_required = schema.get("properties", {}).get("graph_actions", {}).get("items", {}).get("required", [])
    action_props = schema.get("properties", {}).get("graph_actions", {}).get("items", {}).get("properties", {})

    nodes: dict[str, dict[str, Any]] = {}
    for node in nodes_list:
        if not isinstance(node, dict):
            errors.append("invalid_node_entry_type")
            continue
        node_id = str(node.get("node_id", "")).strip()
        for field in node_required:
            if field not in node:
                errors.append(f"missing_node_field:{node_id or '?'}:{field}")
        if node_id in nodes:
            errors.append(f"duplicate_node_id:{node_id}")
        if node_id:
            nodes[node_id] = node
        status = str(node.get("status", "")).strip()
        allowed_statuses = set(node_props.get("status", {}).get("enum", []))
        if allowed_statuses and status not in allowed_statuses:
            errors.append(f"invalid_node_status:{node_id}:{status}")
        gating_class = str(node.get("gating_class", "")).strip()
        allowed_gating = set(node_props.get("gating_class", {}).get("enum", []))
        if allowed_gating and gating_class not in allowed_gating:
            errors.append(f"invalid_gating_class:{node_id}:{gating_class}")

    allowed_relations = set(edge_props.get("relation", {}).get("enum", []))
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in edges_list:
        if not isinstance(edge, dict):
            errors.append("invalid_edge_entry_type")
            continue
        for field in edge_required:
            if field not in edge:
                errors.append(f"missing_edge_field:{field}")
        from_id = str(edge.get("from", "")).strip()
        to_id = str(edge.get("to", "")).strip()
        relation = str(edge.get("relation", "")).strip()
        edge_key = (from_id, to_id, relation)
        if edge_key in seen_edges:
            errors.append(f"duplicate_edge:{from_id}:{to_id}:{relation}")
        seen_edges.add(edge_key)
        if allowed_relations and relation not in allowed_relations:
            errors.append(f"invalid_edge_relation:{relation}")
        if from_id and from_id not in nodes:
            errors.append(f"edge_missing_from_node:{from_id}")
        if to_id and to_id not in nodes:
            errors.append(f"edge_missing_to_node:{to_id}")

    allowed_actions = set(action_props.get("action", {}).get("enum", []))
    action_map: dict[str, dict[str, Any]] = {}
    for action in actions_list:
        if not isinstance(action, dict):
            errors.append("invalid_graph_action_entry_type")
            continue
        for field in action_required:
            if field not in action:
                errors.append(f"missing_graph_action_field:{field}")
        action_id = str(action.get("action_id", "")).strip()
        node_id = str(action.get("node_id", "")).strip()
        action_name = str(action.get("action", "")).strip()
        if action_id in action_map:
            errors.append(f"duplicate_graph_action_id:{action_id}")
        if action_id:
            action_map[action_id] = action
        if allowed_actions and action_name not in allowed_actions:
            errors.append(f"invalid_graph_action:{action_name}")
        if node_id and node_id not in nodes:
            errors.append(f"graph_action_missing_node:{node_id}")

    dependency_map = _dependency_map([edge for edge in edges_list if isinstance(edge, dict)])
    gating_map = _gating_map([edge for edge in edges_list if isinstance(edge, dict)])
    current_branch = branch or get_current_branch()
    execplan_id = None
    if execplan_path:
        execplan_id = str(parse_plan(Path(execplan_path)).frontmatter.get("id", "")).strip()

    projections = [
        _node_projection(
            node,
            dependency_map=dependency_map,
            gating_map=gating_map,
            nodes=nodes,
            branch=current_branch,
            execplan_id=execplan_id,
        )
        for node in nodes.values()
    ]
    projection_map = {item["node_id"]: item for item in projections}
    slice_projections = [item for item in projections if _is_slice_node(nodes[item["node_id"]])]

    active_nodes = [item for item in projections if item["active"]]
    if len(active_nodes) > 1:
        errors.append("multiple_active_remaining_work_nodes")

    for item in slice_projections:
        node_id = item["node_id"]
        status = item["status"]
        gating_class = item["gating_class"]
        ordering = item["ordering"]
        action_state = item["action_state"]
        queue_position = ordering.get("queue_position")
        integration_mode = item.get("integration_mode", "")
        initiative_branch = item.get("initiative_branch", "")
        parent_initiative_node = item.get("parent_initiative_node", "")

        if status != "completed":
            if not isinstance(queue_position, int):
                errors.append(f"slice_missing_queue_position:{node_id}")
            if not ordering.get("tie_breaker"):
                errors.append(f"slice_missing_tie_breaker:{node_id}")
            if _is_slice_node(nodes[node_id]) and status in READY_STATUSES:
                if not integration_mode:
                    errors.append(f"slice_missing_integration_mode:{node_id}")
                elif integration_mode == "via_initiative":
                    if not initiative_branch:
                        errors.append(f"initiative_branch_required:{node_id}")
                    if not parent_initiative_node:
                        errors.append(f"parent_initiative_node_required:{node_id}")
                elif integration_mode not in {"direct_to_main_hotfix", "direct_to_main_patch"}:
                    errors.append(f"invalid_integration_mode:{node_id}:{integration_mode}")
        if parent_initiative_node:
            parent_node = nodes.get(parent_initiative_node)
            if parent_node is None:
                errors.append(f"missing_parent_initiative_node:{node_id}:{parent_initiative_node}")
            else:
                parent_branch = str(parent_node.get("initiative_branch", "")).strip()
                if initiative_branch and parent_branch != initiative_branch:
                    errors.append(
                        f"initiative_branch_parent_mismatch:{node_id}:{initiative_branch}:{parent_initiative_node}:{parent_branch}"
                    )

        if action_state["last_action_id"]:
            action = action_map.get(action_state["last_action_id"])
            if action is None:
                errors.append(f"unknown_last_action_id:{node_id}:{action_state['last_action_id']}")
            else:
                if str(action.get("node_id", "")).strip() != node_id:
                    errors.append(f"last_action_node_mismatch:{node_id}:{action_state['last_action_id']}")
                if action_state["last_action"] and str(action.get("action", "")).strip() != action_state["last_action"]:
                    errors.append(f"last_action_mismatch:{node_id}:{action_state['last_action_id']}")

        if status in READY_STATUSES:
            if gating_class != "auto_runnable":
                errors.append(f"ready_node_wrong_gating:{node_id}:{gating_class}")
            if not item["dependencies_complete"]:
                errors.append(f"ready_node_with_incomplete_dependencies:{node_id}")
            if _is_slice_node(nodes[node_id]) and not item["implementation_branch"]:
                errors.append(f"ready_slice_missing_implementation_branch:{node_id}")
            if integration_mode != "via_initiative":
                errors.append(f"ready_slice_wrong_integration_mode:{node_id}:{integration_mode}")
        availability_target_ref = str(item.get("availability_target_ref", "")).strip()
        availability_status = str(item.get("availability_status", "")).strip()
        availability_ref = str(item.get("availability_ref", "")).strip()
        if availability_target_ref and not availability_status:
            errors.append(f"availability_status_required:{node_id}")
        if availability_status and availability_status not in {"not_required", "pending", "active"}:
            errors.append(f"invalid_availability_status:{node_id}:{availability_status}")
        if availability_status == "active" and not availability_ref:
            errors.append(f"availability_ref_required:{node_id}")
        if availability_status == "not_required" and availability_target_ref:
            errors.append(f"availability_target_not_allowed_for_not_required:{node_id}")
            if not isinstance(ordering.get("ready_order"), int):
                errors.append(f"ready_node_missing_ready_order:{node_id}")
            if action_state["last_action"] != "promote_ready":
                errors.append(f"ready_node_missing_promote_action:{node_id}")
            if action_state["action_required"]:
                errors.append(f"ready_node_requires_action:{node_id}")
        if status == "blocked":
            if item["dependencies_complete"]:
                errors.append(f"blocked_node_without_open_dependency:{node_id}")
            if not item["status_reason"]:
                errors.append(f"blocked_node_missing_status_reason:{node_id}")
        if status in {"review_gated", "decision_gated"}:
            expected_gating = status
            if gating_class != expected_gating:
                errors.append(f"gated_node_wrong_gating:{node_id}:{gating_class}:{expected_gating}")
            if not item["status_reason"]:
                errors.append(f"gated_node_missing_status_reason:{node_id}")
        if status == "completed" and not item["dependencies_complete"] and item["depends_on"]:
            errors.append(f"completed_node_with_incomplete_dependencies:{node_id}")
        if status == "completed" and action_state["last_action"] and action_state["last_action"] != "complete":
            errors.append(f"completed_node_wrong_last_action:{node_id}:{action_state['last_action']}")

        for gate_id in item["gated_by"]:
            gate_projection = projection_map.get(gate_id)
            if gate_projection is None:
                errors.append(f"missing_gate_node:{node_id}:{gate_id}")
                continue
            if status in {"ready", "completed"} and gate_projection["status"] not in TERMINAL_STATUSES:
                errors.append(f"gated_node_released_before_gate_complete:{node_id}:{gate_id}:{gate_projection['status']}")

    ready_nodes = sorted((item for item in slice_projections if item["eligible_now"]), key=_ordering_tuple)
    blocked_nodes = sorted(
        (item for item in slice_projections if item["status"] in BLOCKED_STATUSES),
        key=lambda item: (
            item["ordering"].get("queue_position") if isinstance(item["ordering"].get("queue_position"), int) else 999999,
            item["ordering"].get("tie_breaker", ""),
            item["node_id"],
        ),
    )
    completed_nodes = sorted(
        (item for item in slice_projections if item["status"] in TERMINAL_STATUSES),
        key=lambda item: (
            item["ordering"].get("queue_position") if isinstance(item["ordering"].get("queue_position"), int) else 999999,
            item["ordering"].get("tie_breaker", ""),
            item["node_id"],
        ),
    )

    ready_orders = [item["ordering"].get("ready_order") for item in ready_nodes]
    if len(ready_orders) != len({value for value in ready_orders if isinstance(value, int)}):
        errors.append("duplicate_ready_order_values")

    computed_ready_execplan_ids = [str(item["target_execplan_id"]).strip() for item in ready_nodes]
    queue_metadata = _queue_metadata(queue_path)
    latest_action_id = str(actions_list[-1].get("action_id", "")).strip() if actions_list else ""
    projection_last_action = str(queue_projection.get("last_reconciled_action_id", "")).strip()
    projection_ready_execplan_ids = [
        str(item).strip() for item in queue_projection.get("ready_execplan_ids", []) if str(item).strip()
    ]
    projection_authority = str(queue_projection.get("projection_authority", "")).strip()

    if ordering_policy.get("board_projection_authority") != "projection_only":
        errors.append("board_projection_authority_invalid")
    if projection_authority != "projection_only":
        errors.append("queue_projection_authority_invalid")
    if latest_action_id and projection_last_action != latest_action_id:
        errors.append("stale_queue_projection_last_action")
    if projection_ready_execplan_ids != computed_ready_execplan_ids:
        errors.append("queue_projection_ready_order_mismatch")

    if not queue_metadata["exists"]:
        errors.append("missing_queue_mirror")
    else:
        if queue_metadata["canonical_last_graph_action_id"] != latest_action_id:
            errors.append("queued_execplans_stale_last_action")
        if queue_metadata["canonical_ready_order"] != computed_ready_execplan_ids:
            errors.append("queued_execplans_ready_order_mismatch")
        if queue_metadata["projection_authority"] != "projection_only":
            errors.append("queued_execplans_projection_authority_invalid")

    action_required_nodes = [
        {
            "node_id": item["node_id"],
            "target_execplan_id": item["target_execplan_id"],
            "status": item["status"],
            "reorder_requires_human": item["action_state"]["reorder_requires_human"],
            "reorder_blockers": item["action_state"]["reorder_blockers"],
        }
        for item in slice_projections
        if item["action_state"]["action_required"]
    ]
    action_required_nodes = sorted(action_required_nodes, key=lambda item: (item["target_execplan_id"], item["node_id"]))

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "graph_id": str(graph.get("graph_id", "")).strip(),
        "graph_path": graph_path.as_posix(),
        "node_count": len(nodes),
        "edge_count": len(seen_edges),
        "graph_action_count": len(action_map),
        "branch": current_branch,
        "execplan_id": execplan_id or "",
        "error_count": len(sorted(set(errors))),
        "errors": sorted(set(errors)),
        "active_node": active_nodes[0] if len(active_nodes) == 1 else None,
        "ready_nodes": ready_nodes,
        "blocked_nodes": blocked_nodes,
        "completed_nodes": completed_nodes,
        "action_required_nodes": action_required_nodes,
        "ordering": {
            "ready_execplan_ids": computed_ready_execplan_ids,
            "ready_node_ids": [item["node_id"] for item in ready_nodes],
            "ready_sort_fields": list(ordering_policy.get("ready_sort_fields", [])),
            "reorder_requires_explicit_action": bool(ordering_policy.get("reorder_requires_explicit_action", False)),
        },
        "queue_projection": {
            "path": str(queue_projection.get("path", "")).strip(),
            "projection_authority": projection_authority,
            "last_reconciled_action_id": projection_last_action,
            "latest_graph_action_id": latest_action_id,
            "ready_execplan_ids": projection_ready_execplan_ids,
            "queue_doc": queue_metadata,
        },
        "evidence_refs": sorted(
            {
                "artifacts/planner/research/remaining-work-graph.json",
                "spec/remaining-work-graph.schema.yaml",
                "docs/queued-execplans.md",
                "docs/remaining-work-graph.md",
            }
        ),
    }
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    args = parser.parse_args()
    code, report = check_remaining_work_graph(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
