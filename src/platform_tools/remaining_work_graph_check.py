from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import get_current_branch
from platform_tools.plan_utils import parse_plan


COMMAND = "remaining-work-graph-check"
TERMINAL_STATUSES = {"completed"}
BLOCKED_STATUSES = {"blocked", "review_gated", "decision_gated"}


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
        "conflict_domains": sorted(str(item).strip() for item in node.get("conflict_domains", []) if str(item).strip()),
        "expected_artifacts": sorted(str(item).strip() for item in node.get("expected_artifacts", []) if str(item).strip()),
        "depends_on": depends_on,
        "gated_by": gated_by,
        "dependency_states": dependency_states,
        "dependencies_complete": dependencies_complete,
        "active": active,
        "eligible_now": _is_slice_node(node) and str(node.get("status", "")).strip() == "ready" and dependencies_complete,
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
    if not isinstance(nodes_list, list):
        errors.append("invalid_nodes_type")
        nodes_list = []
    if not isinstance(edges_list, list):
        errors.append("invalid_edges_type")
        edges_list = []

    node_props = schema.get("properties", {}).get("nodes", {}).get("items", {}).get("properties", {})
    node_required = schema.get("properties", {}).get("nodes", {}).get("items", {}).get("required", [])
    edge_props = schema.get("properties", {}).get("edges", {}).get("items", {}).get("properties", {})
    edge_required = schema.get("properties", {}).get("edges", {}).get("items", {}).get("required", [])

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

    active_nodes = [item for item in projections if item["active"]]
    if len(active_nodes) > 1:
        errors.append("multiple_active_remaining_work_nodes")

    for item in projections:
        node_id = item["node_id"]
        status = item["status"]
        gating_class = item["gating_class"]
        if status == "ready":
            if gating_class != "auto_runnable":
                errors.append(f"ready_node_wrong_gating:{node_id}:{gating_class}")
            if not item["dependencies_complete"]:
                errors.append(f"ready_node_with_incomplete_dependencies:{node_id}")
            if _is_slice_node(nodes[node_id]) and not item["implementation_branch"]:
                errors.append(f"ready_slice_missing_implementation_branch:{node_id}")
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

        for gate_id in item["gated_by"]:
            gate_projection = projection_map.get(gate_id)
            if gate_projection is None:
                errors.append(f"missing_gate_node:{node_id}:{gate_id}")
                continue
            if status in {"ready", "completed"} and gate_projection["status"] not in TERMINAL_STATUSES:
                errors.append(f"gated_node_released_before_gate_complete:{node_id}:{gate_id}:{gate_projection['status']}")

    ready_nodes = sorted(
        (
            item
            for item in projections
            if item["eligible_now"]
        ),
        key=lambda item: (item["target_execplan_id"], item["node_id"]),
    )
    blocked_nodes = sorted(
        (
            item
            for item in projections
            if _is_slice_node(nodes[item["node_id"]]) and item["status"] in BLOCKED_STATUSES
        ),
        key=lambda item: (item["target_execplan_id"], item["node_id"]),
    )
    completed_nodes = sorted(
        (
            item
            for item in projections
            if _is_slice_node(nodes[item["node_id"]]) and item["status"] in TERMINAL_STATUSES
        ),
        key=lambda item: (item["target_execplan_id"], item["node_id"]),
    )

    report = {
        "command": COMMAND,
        "status": "ok" if not errors else "blocked",
        "ok": not errors,
        "graph_id": str(graph.get("graph_id", "")).strip(),
        "graph_path": graph_path.as_posix(),
        "node_count": len(nodes),
        "edge_count": len(seen_edges),
        "branch": current_branch,
        "execplan_id": execplan_id or "",
        "error_count": len(sorted(set(errors))),
        "errors": sorted(set(errors)),
        "active_node": active_nodes[0] if len(active_nodes) == 1 else None,
        "ready_nodes": ready_nodes,
        "blocked_nodes": blocked_nodes,
        "completed_nodes": completed_nodes,
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
