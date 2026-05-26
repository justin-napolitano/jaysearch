from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import networkx as nx

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json
from platform_tools.validate_node_readiness import validate_node_readiness


COMMAND = "materialize-selected-dag-execution-units"
DEFAULT_OUTPUT_ROOT = Path("artifacts/dag-execution-units/runs")
DEFAULT_POLICY_PATH = "spec/node-readiness-policy.yaml"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("sdeu-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _resolve_ref(repo_root: Path, ref: str) -> Path:
    path = Path(ref)
    return path if path.is_absolute() else repo_root / path


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "node"


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "").strip()


def _edge_endpoint(edge: dict[str, Any], *names: str) -> str:
    for name in names:
        value = str(edge.get(name, "")).strip()
        if value:
            return value
    return ""


def _owned_changes(node: dict[str, Any]) -> list[str]:
    refs = _string_list(node.get("owned_changes", []))
    refs.extend(_string_list(node.get("owned_surfaces", [])))
    scope = node.get("scope")
    if isinstance(scope, dict):
        refs.extend(_string_list(scope.get("owned_surfaces", [])))
    return sorted(set(refs))


def _validation_commands(node: dict[str, Any]) -> list[str]:
    explicit = _string_list(node.get("validation_commands", []))
    if explicit:
        return explicit
    commands: list[str] = []
    for item in _string_list(node.get("validation_refs", [])) + _string_list(
        node.get("validation_targets", [])
    ):
        if item.startswith(("uv ", "python", "python3 ", "bin/", "bash ")) or "pytest" in item:
            commands.append(item)
    return sorted(set(commands))


def _validation_refs(node: dict[str, Any]) -> list[str]:
    refs = _validation_commands(node)
    refs.extend(_string_list(node.get("acceptance_checks", [])))
    refs.extend(_string_list(node.get("validation_refs", [])))
    refs.extend(_string_list(node.get("validation_targets", [])))
    return sorted(set(refs))


def _evidence_refs(*payloads: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        refs.extend(_string_list(payload.get("evidence_refs", [])))
        refs.extend(_string_list(payload.get("source_artifacts", [])))
    return sorted(set(refs))


def _node_list(dag: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(dag.get("nodes", []))


def _edge_list(dag: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(dag.get("edges", []))


def _is_buildable_type(node: dict[str, Any]) -> bool:
    return str(node.get("node_type", "")).strip() in {"runtime", "validation", "contract", "documentation"}


def _looks_buildable(node: dict[str, Any]) -> bool:
    return _is_buildable_type(node) or bool(_owned_changes(node))


def _build_graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> tuple[nx.DiGraph, list[str]]:
    blockers: list[str] = []
    graph = nx.DiGraph()
    seen: set[str] = set()
    for index, node in enumerate(nodes, start=1):
        node_id = _node_id(node)
        if not node_id:
            blockers.append(f"node_missing_id:{index}")
            continue
        if node_id in seen:
            blockers.append(f"duplicate_node_id:{node_id}")
            continue
        seen.add(node_id)
        graph.add_node(node_id, payload=node)
    for index, edge in enumerate(edges, start=1):
        source = _edge_endpoint(edge, "from_node_id", "from", "source")
        target = _edge_endpoint(edge, "to_node_id", "to", "target")
        if not source or not target:
            blockers.append(f"edge_missing_endpoint:{index}")
            continue
        if source not in graph:
            blockers.append(f"edge_source_missing:{source}")
            continue
        if target not in graph:
            blockers.append(f"edge_target_missing:{target}")
            continue
        graph.add_edge(source, target, payload=edge)
    if graph.number_of_nodes() == 0:
        blockers.append("selected_dag_missing_nodes")
    elif not nx.is_directed_acyclic_graph(graph):
        blockers.append("selected_dag_contains_cycle")
    return graph, blockers


def _policy_path(repo_root: Path) -> str:
    root_policy = repo_root / DEFAULT_POLICY_PATH
    if root_policy.exists():
        return DEFAULT_POLICY_PATH
    return Path(__file__).resolve().parents[2].joinpath(DEFAULT_POLICY_PATH).as_posix()


def _topological_layers(graph: nx.DiGraph, materialized_nodes: set[str]) -> list[list[str]]:
    subgraph = graph.subgraph(materialized_nodes).copy()
    if not nx.is_directed_acyclic_graph(subgraph):
        return []
    # Selected DAG edges are "from depends on to"; reverse for executable order.
    execution_graph = subgraph.reverse(copy=True)
    return [sorted(generation) for generation in nx.algorithms.dag.topological_generations(execution_graph)]


def _implementation_intent(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": str(node.get("goal") or node.get("title") or "").strip(),
        "node_type": str(node.get("node_type", "")).strip(),
        "source_node_id": _node_id(node),
    }


def _execution_unit_packet(
    *,
    node: dict[str, Any],
    selected_dag_ref: str,
    dependency_refs: list[str],
    evidence_refs: list[str],
) -> dict[str, Any]:
    node_id = _node_id(node)
    execution_unit_id = f"execution-unit:{_slug(node_id)}"
    validation_commands = _validation_commands(node)
    acceptance_checks = _string_list(node.get("acceptance_checks", [])) or _validation_refs(node)
    return {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": f"{execution_unit_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "execution_unit_id": execution_unit_id,
        "source_problem_node_ref": f"{selected_dag_ref}#node:{node_id}",
        "selected_option_ref": f"{selected_dag_ref}#selected-node:{node_id}",
        "implementation_intent": _implementation_intent(node),
        "owned_changes": _owned_changes(node),
        "required_inputs": [selected_dag_ref],
        "expected_outputs": _string_list(node.get("expected_outputs", [])),
        "acceptance_checks": acceptance_checks,
        "validation_commands": validation_commands,
        "rollback_plan": str(node.get("rollback_plan", "")).strip()
        or "Revert owned changes from this execution unit.",
        "non_goals": _string_list(node.get("non_goals", [])),
        "dependency_refs": dependency_refs,
        "evidence_refs": evidence_refs,
        "evaluation_method": "node_readiness_policy_v1",
        "completion_evidence_requirements": validation_commands or acceptance_checks,
    }


def materialize_selected_dag_execution_units(
    *,
    root: str = ".",
    selection_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    target_state: str = "implementation_ready",
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    selection_ref = str((repo_root / selection_path).resolve())
    selection = _load_json(repo_root / selection_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(selection.get("packet_type", "")).strip() != "candidate_dag_selection":
        blockers.append("candidate_dag_selection_packet_type_invalid")
    blockers.extend(_string_list(selection.get("blockers", [])))

    selected_dag_ref = str(selection.get("selected_dag_ref", "")).strip()
    dag: dict[str, Any] = {}
    graph = nx.DiGraph()
    if not selected_dag_ref:
        blockers.append("selected_dag_ref_missing")
    else:
        dag_path = _resolve_ref(repo_root, selected_dag_ref)
        selected_dag_ref = str(dag_path.resolve())
        dag = _load_json(dag_path)
        graph, graph_blockers = _build_graph(_node_list(dag), _edge_list(dag))
        blockers.extend(graph_blockers)

    execution_unit_refs: dict[str, str] = {}
    non_buildable_node_refs: list[str] = []
    node_blockers: list[str] = []
    materialized_nodes: set[str] = set()

    if not blockers:
        for node_id, node in graph.nodes(data="payload"):
            if not isinstance(node, dict) or not _looks_buildable(node):
                non_buildable_node_refs.append(f"{selected_dag_ref}#node:{node_id}")
                continue
            if not _owned_changes(node):
                node_blockers.append(f"node_missing_owned_changes:{node_id}")
            if not _validation_refs(node):
                node_blockers.append(f"node_missing_validation_targets:{node_id}")
            if not _string_list(node.get("expected_outputs", [])):
                node_blockers.append(f"node_missing_expected_outputs:{node_id}")
            materialized_nodes.add(node_id)

        for source, target in graph.edges():
            if source in materialized_nodes and target not in materialized_nodes:
                node_blockers.append(f"dependency_not_materialized:{source}->{target}")

    blockers.extend(node_blockers)

    readiness_reports: list[dict[str, Any]] = []
    if not blockers:
        for node_id in sorted(materialized_nodes):
            node = graph.nodes[node_id]["payload"]
            dependency_refs = [
                f"execution-unit:{_slug(target)}"
                for _source, target in graph.out_edges(node_id)
                if target in materialized_nodes
            ]
            packet = _execution_unit_packet(
                node=node,
                selected_dag_ref=selected_dag_ref,
                dependency_refs=sorted(set(dependency_refs)),
                evidence_refs=_evidence_refs(selection, dag, node),
            )
            packet_path = write_json(run_root / f"execution-unit-{_slug(node_id)}.packet.json", packet)
            relative_packet_path = packet_path.relative_to(repo_root).as_posix()
            _, readiness = validate_node_readiness(
                root=repo_root.as_posix(),
                node_path=relative_packet_path,
                target_state=target_state,
                policy_path=_policy_path(repo_root),
            )
            readiness_reports.append(readiness)
            if not readiness.get("ready", False):
                blockers.extend(f"{node_id}:{item}" for item in readiness.get("blockers", []))
                blockers.extend(f"{node_id}:missing:{item}" for item in readiness.get("missing_fields", []))
            execution_unit_refs[node_id] = packet_path.as_posix()

    execution_dependencies = [
        {
            "from_execution_unit_ref": execution_unit_refs[source],
            "to_execution_unit_ref": execution_unit_refs[target],
            "relation": "depends_on",
        }
        for source, target in graph.edges()
        if source in execution_unit_refs and target in execution_unit_refs
    ]

    if not execution_unit_refs and "selected_dag_missing_nodes" not in blockers:
        blockers.append("no_execution_units_materialized")

    manifest = {
        "packet_type": "dag_execution_unit_manifest",
        "packet_version": "v1",
        "packet_id": f"dag-execution-unit-manifest:{run_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "manifest_id": f"dag-execution-unit-manifest:{run_id}",
        "source_selection_ref": selection_ref,
        "selected_dag_ref": selected_dag_ref,
        "execution_unit_refs": [execution_unit_refs[node_id] for node_id in sorted(execution_unit_refs)],
        "execution_dependencies": execution_dependencies,
        "non_buildable_node_refs": sorted(non_buildable_node_refs),
        "topological_layers": _topological_layers(graph, set(execution_unit_refs)),
        "evidence_refs": _evidence_refs(selection, dag),
        "blockers": sorted(set(blockers)),
    }
    manifest_path = write_json(run_root / "dag-execution-unit-manifest.packet.json", manifest)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "source_selection_ref": selection_ref,
            "selected_dag_ref": selected_dag_ref,
            "dag_execution_unit_manifest_path": manifest_path.as_posix(),
            "execution_unit_paths": [execution_unit_refs[node_id] for node_id in sorted(execution_unit_refs)],
            "readiness_reports": readiness_reports,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "dag-execution-unit-materialization.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selection-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--target-state", default="implementation_ready")
    args = parser.parse_args()
    try:
        code, report = materialize_selected_dag_execution_units(
            root=args.root,
            selection_path=args.selection_path,
            output_root=args.output_root,
            target_state=args.target_state,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
