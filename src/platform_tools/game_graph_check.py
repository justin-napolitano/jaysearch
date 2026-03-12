from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def _edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("from", "")),
        str(edge.get("to", "")),
        str(edge.get("relation", "")),
    )


def _find_cycles(node_ids: list[str], adjacency: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[str] = []

    def visit(node_id: str, trail: list[str]) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            cycle_start = trail.index(node_id)
            cycle = trail[cycle_start:] + [node_id]
            cycles.append("cycle_detected:" + "->".join(cycle))
            return
        visiting.add(node_id)
        next_trail = trail + [node_id]
        for child_id in sorted(adjacency.get(node_id, [])):
            visit(child_id, next_trail)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(node_ids):
        visit(node_id, [])
    return cycles


def check_game_graph(root: str = ".") -> tuple[int, dict[str, Any]]:
    base = Path(root)
    graph_path = base / "artifacts" / "planner" / "research" / "game-graph.json"
    schema_path = base / "spec" / "games.schema.yaml"
    errors: list[str] = []

    if not graph_path.exists():
        return 1, {"tool": "game_graph_check", "ok": False, "errors": ["missing_game_graph"]}
    if not schema_path.exists():
        return 1, {"tool": "game_graph_check", "ok": False, "errors": ["missing_games_schema"]}

    graph = _load_json(graph_path)
    schema = _load_yaml(schema_path)

    for field in schema.get("graph", {}).get("required_fields", []):
        if field not in graph:
            errors.append(f"missing_graph_field:{field}")

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list):
        errors.append("invalid_nodes_type")
        nodes = []
    if not isinstance(edges, list):
        errors.append("invalid_edges_type")
        edges = []

    node_map: dict[str, dict[str, Any]] = {}
    allowed_node_types = set(schema.get("node", {}).get("type_allowed", []))
    allowed_relations = set(schema.get("edge", {}).get("relation_allowed", []))
    game_node_required_fields = schema.get("game_node", {}).get("required_fields", [])
    allowed_game_layers = set(schema.get("game_node", {}).get("allowed_layers", []))
    allowed_game_scopes = set(schema.get("game_node", {}).get("allowed_scopes", []))

    for node in nodes:
        if not isinstance(node, dict):
            errors.append("invalid_node_entry_type")
            continue
        node_id = str(node.get("id", ""))
        for field in schema.get("node", {}).get("required_fields", []):
            if field not in node:
                errors.append(f"missing_node_field:{node_id or '?'}:{field}")
        node_type = str(node.get("type", ""))
        if node_type not in allowed_node_types:
            errors.append(f"invalid_node_type:{node_id or '?'}:{node_type}")
        if node_type == "game":
            for field in game_node_required_fields:
                if field not in node:
                    errors.append(f"missing_game_node_field:{node_id or '?'}:{field}")
            layer = str(node.get("layer", ""))
            if layer and layer not in allowed_game_layers:
                errors.append(f"invalid_game_layer:{node_id or '?'}:{layer}")
            scope = str(node.get("scope", ""))
            if scope and scope not in allowed_game_scopes:
                errors.append(f"invalid_game_scope:{node_id or '?'}:{scope}")
        if node_id in node_map:
            errors.append(f"duplicate_node_id:{node_id}")
        elif node_id:
            node_map[node_id] = node

    edge_set: set[tuple[str, str, str]] = set()
    canonical_relations = {"contains", "terminates_in", "hands_off_to", "inherits"}
    game_adjacency: dict[str, list[str]] = {}
    incoming_contains: dict[str, int] = {}

    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("invalid_edge_entry_type")
            continue
        for field in schema.get("edge", {}).get("required_fields", []):
            if field not in edge:
                errors.append(f"missing_edge_field:{field}")

        relation = str(edge.get("relation", ""))
        from_id = str(edge.get("from", ""))
        to_id = str(edge.get("to", ""))
        edge_tuple = (from_id, to_id, relation)
        if relation not in allowed_relations:
            errors.append(f"invalid_edge_relation:{relation}")
        if edge_tuple in edge_set:
            errors.append(f"duplicate_edge:{from_id}:{to_id}:{relation}")
        edge_set.add(edge_tuple)

        from_node = node_map.get(from_id)
        to_node = node_map.get(to_id)
        if from_node is None:
            errors.append(f"edge_missing_from_node:{from_id}")
        if to_node is None:
            errors.append(f"edge_missing_to_node:{to_id}")
        if from_node is None or to_node is None:
            continue

        from_type = str(from_node.get("type", ""))
        to_type = str(to_node.get("type", ""))
        if relation in canonical_relations and (from_type != "game" or to_type != "game"):
            errors.append(f"canonical_edge_requires_game_nodes:{from_id}:{to_id}:{relation}")
        if relation in {"links_to", "documented_in"} and from_type != "game":
            errors.append(f"artifact_edge_requires_game_source:{from_id}:{relation}")
        if relation == "links_to" and to_type != "artifact":
            errors.append(f"links_to_requires_artifact_target:{to_id}")
        if relation == "documented_in" and to_type != "artifact":
            errors.append(f"documented_in_requires_artifact_target:{to_id}")
        if from_id == to_id:
            errors.append(f"self_edge_not_allowed:{from_id}:{relation}")

        if relation in canonical_relations:
            game_adjacency.setdefault(from_id, []).append(to_id)
        if relation == "contains":
            incoming_contains[to_id] = incoming_contains.get(to_id, 0) + 1

    required_game_ids = [
        str(item).strip()
        for item in schema.get("game_graph", {}).get("required_game_ids", [])
        if str(item).strip()
    ]
    for game_id in sorted(required_game_ids):
        if game_id not in node_map:
            errors.append(f"missing_required_game:{game_id}")
        elif str(node_map[game_id].get("type", "")) != "game":
            errors.append(f"required_game_not_game_type:{game_id}")

    for required_edge in schema.get("game_graph", {}).get("required_edges", []):
        if not isinstance(required_edge, dict):
            continue
        edge_tuple = _edge_key(required_edge)
        if edge_tuple not in edge_set:
            errors.append(f"missing_required_edge:{edge_tuple[0]}:{edge_tuple[1]}:{edge_tuple[2]}")

    root_game_id = str(schema.get("game_graph", {}).get("root_game_id", "")).strip()
    if root_game_id:
        if root_game_id not in node_map:
            errors.append(f"missing_root_game:{root_game_id}")
        elif incoming_contains.get(root_game_id, 0) != 0:
            errors.append(f"root_game_has_parent:{root_game_id}")

    for game_id in required_game_ids:
        if game_id == root_game_id:
            continue
        if incoming_contains.get(game_id, 0) > 1:
            errors.append(f"game_has_multiple_parents:{game_id}")

    for cycle_error in _find_cycles(required_game_ids, game_adjacency):
        errors.append(cycle_error)

    for node_id, node in sorted(node_map.items()):
        if str(node.get("type", "")) != "artifact":
            if str(node.get("type", "")) == "game":
                spec_path = str(node.get("spec_path", "")).strip()
                if spec_path and not (base / spec_path).exists():
                    errors.append(f"missing_game_spec_path:{node_id}:{spec_path}")
                elif spec_path:
                    spec = _load_yaml(base / spec_path)
                    if str(spec.get("game_id", "")).strip() != node_id:
                        errors.append(f"game_spec_id_mismatch:{node_id}:{spec_path}")
            continue
        title = str(node.get("title", "")).strip()
        if title and not (base / title).exists():
            errors.append(f"missing_artifact_path:{node_id}:{title}")

    report = {
        "tool": "game_graph_check",
        "ok": not errors,
        "graph_id": graph.get("graph_id", ""),
        "graph_path": graph_path.as_posix(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "game_count": sum(1 for node in node_map.values() if node.get("type") == "game"),
        "artifact_count": sum(1 for node in node_map.values() if node.get("type") == "artifact"),
        "error_count": len(_sorted_unique(errors)),
        "errors": _sorted_unique(errors),
    }
    return (1 if errors else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_game_graph(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
