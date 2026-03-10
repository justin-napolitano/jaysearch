from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_RULES = {
    "rule-smoke-test-required",
    "rule-clean-merge-state",
    "rule-human-sized-commits",
    "rule-procedural-commit-order",
    "rule-execplan-validation",
    "rule-human-finalization",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def check_rule_graph(root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    graph_path = base / "artifacts" / "planner" / "research" / "rule-graph.json"
    schema_path = base / "spec" / "rule-graph.schema.yaml"
    errors: list[str] = []
    if not graph_path.exists():
        return 1, {"tool": "rule_graph_check", "ok": False, "errors": ["missing_rule_graph"]}
    if not schema_path.exists():
        return 1, {"tool": "rule_graph_check", "ok": False, "errors": ["missing_rule_graph_schema"]}

    graph = _load_json(graph_path)
    schema = _load_yaml(schema_path)

    for field in schema.get("graph", {}).get("required_fields", []):
        if field not in graph:
            errors.append(f"missing_graph_field:{field}")

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_map = {}
    allowed_node_types = set(schema.get("node", {}).get("type_allowed", []))
    allowed_relations = set(schema.get("edge", {}).get("relation_allowed", []))

    for node in nodes:
        if not isinstance(node, dict):
            errors.append("invalid_node_entry_type")
            continue
        for field in schema.get("node", {}).get("required_fields", []):
            if field not in node:
                errors.append(f"missing_node_field:{node.get('id', '?')}:{field}")
        if node.get("type") not in allowed_node_types:
            errors.append(f"invalid_node_type:{node.get('id', '?')}:{node.get('type')}")
        if node.get("id") in node_map:
            errors.append(f"duplicate_node_id:{node.get('id')}")
        node_map[node.get("id")] = node

    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("invalid_edge_entry_type")
            continue
        for field in schema.get("edge", {}).get("required_fields", []):
            if field not in edge:
                errors.append(f"missing_edge_field:{field}")
        if edge.get("relation") not in allowed_relations:
            errors.append(f"invalid_edge_relation:{edge.get('relation')}")
        if edge.get("from") not in node_map:
            errors.append(f"edge_missing_from_node:{edge.get('from')}")
        if edge.get("to") not in node_map:
            errors.append(f"edge_missing_to_node:{edge.get('to')}")

    seen_rules = {node_id for node_id, node in node_map.items() if node.get("type") == "rule"}
    for rule_id in sorted(REQUIRED_RULES - seen_rules):
        errors.append(f"missing_required_rule:{rule_id}")

    for node_id, node in node_map.items():
        if node.get("type") == "artifact":
            title = str(node.get("title", ""))
            if title and not (base / title).exists():
                errors.append(f"missing_artifact_path:{node_id}:{title}")
        if node.get("type") == "validator":
            title = str(node.get("title", ""))
            if title.startswith("bin/") and not (base / title).exists():
                errors.append(f"missing_validator_command:{node_id}:{title}")

    def _edges_from(node_id: str, relation: str | None = None) -> list[dict[str, Any]]:
        return [
            edge
            for edge in edges
            if edge.get("from") == node_id and (relation is None or edge.get("relation") == relation)
        ]

    for rule_id in REQUIRED_RULES:
        applies = _edges_from(rule_id, "applies_to")
        requires = _edges_from(rule_id, "requires")
        satisfied = _edges_from(rule_id, "satisfied_by")
        enforced = _edges_from(rule_id, "enforced_by")
        if not (applies or requires):
            errors.append(f"rule_missing_scope:{rule_id}")
        if not (satisfied or enforced or requires):
            errors.append(f"rule_missing_linkage:{rule_id}")

    merge_rule_edges = _edges_from("rule-smoke-test-required", "enforced_by") + _edges_from(
        "rule-execplan-validation", "enforced_by"
    )
    if not merge_rule_edges:
        errors.append("merge_rules_missing_validator_links")

    report = {
        "tool": "rule_graph_check",
        "ok": not errors,
        "graph_path": graph_path.as_posix(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "error_count": len(errors),
        "errors": errors,
    }
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_rule_graph(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
