from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "design-iteration"
DEFAULT_REGISTRY_PATH = Path("spec/contracts/packet-schema-registry.yaml")
DEFAULT_CHECKSET_PATH = Path("spec/contracts/design-iteration-checks.yaml")
DEFAULT_DAG_PATH = Path("artifacts/planner/research/design-iteration-tool-dag-v1.json")
DEFAULT_OUTPUT_ROOT = Path("artifacts/design-iteration/runs")
DEFAULT_PLAN_QUALITY_SCORING_PATH = Path("spec/plan-quality-scoring.yaml")
ALLOWED_NODE_TYPES = {
    "artifact_check",
    "governance_gate",
    "human_gate",
    "selection_gate",
    "tool_invocation",
}
ALLOWED_EDGE_RELATIONS = {"depends_on", "gated_by", "materializes", "emits"}
ALLOWED_IMPLEMENTATION_NODE_TYPES = {"task", "artifact", "validation", "handoff"}
ALLOWED_IMPLEMENTATION_EDGE_RELATIONS = {"depends_on", "blocks", "conflicts_with", "informs"}
ALLOWED_DISCOVERED_PLANNING_EDGE_RELATIONS = {
    "depends_on",
    "gated_by",
    "conflicts_with",
    "informed_by",
    "informs",
}
KNOWN_EXTERNAL_INPUT_PACKETS = {"design_context_packet", "design_review_request_packet"}
MINIMUM_REQUIRED_CONTRACTS = {
    "candidate_plan_comparison_packet",
    "dag_edge",
    "dag_node",
    "evidence_packet",
    "execution_materialization_policy",
    "execution_packet",
    "execution_ready_plan_packet",
    "governance_decision_packet",
    "implementation_graph_packet",
    "message_envelope",
    "packet_base",
    "plan_quality_score_packet",
    "planning_request_packet",
    "planner_to_governance_runnable_contract",
    "ranked_plan_packet",
    "question_to_research_problem_transform",
    "research_problem_packet",
    "research_question_packet",
    "research_recommendation_packet",
    "run_status_packet",
    "selected_solution_scope",
    "workflow_dag_to_implementation_dag_link_contract",
    "workflow_request_packet",
}
BOUNDARY_DOCS = {
    "design_iteration": Path("docs/design-iteration-tool-v1.md"),
    "design_review_automation": Path("docs/design-review-automation-v1.md"),
    "execution_slice_materialization": Path("docs/execution-slice-materialization-v1.md"),
    "governance": Path("docs/governance-tool-v1.md"),
    "orchestration": Path("docs/orchestration-runner-v1.md"),
    "planner": Path("docs/planner-tool-v1.md"),
    "plan_quality_score": Path("docs/plan-quality-score-v1.md"),
    "question": Path("docs/question-tool-v1.md"),
    "research": Path("docs/research-tool-v1.md"),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("dit-%Y%m%dT%H%M%SZ")


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _write_jsonl(path: Path, entries: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return path


def _read_text(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _build_check_index(checkset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for family in checkset.get("validator_families", []):
        if not isinstance(family, dict):
            continue
        family_name = str(family.get("family", "")).strip()
        for check in family.get("checks", []):
            if not isinstance(check, dict):
                continue
            check_id = str(check.get("check_id", "")).strip()
            if check_id:
                entry = dict(check)
                entry["family"] = family_name
                index[check_id] = entry
    return index


def _finding(
    *,
    run_id: str,
    check_index: dict[str, dict[str, Any]],
    check_id: str,
    artifact_refs: list[str],
    summary: str,
    evidence_refs: list[str] | None = None,
    related_contract_refs: list[str] | None = None,
    related_node_refs: list[str] | None = None,
    suggested_fix: str = "",
) -> dict[str, Any]:
    check = check_index.get(check_id, {})
    family = str(check.get("family", "")).strip()
    finding_type = str(check.get("finding_type", "")).strip() or check_id
    violated_invariant = str(check.get("violated_invariant", "")).strip()
    return {
        "finding_id": f"{run_id}:{check_id}:{abs(hash((tuple(sorted(artifact_refs)), summary))) % 10_000_000}",
        "validator_family": family,
        "check_id": check_id,
        "severity": str(check.get("severity", "medium")).strip() or "medium",
        "blocking": bool(check.get("blocking", False)),
        "finding_type": finding_type,
        "artifact_refs": sorted({item for item in artifact_refs if item}),
        "violated_invariant": violated_invariant,
        "summary": summary,
        "evidence_refs": sorted({item for item in (evidence_refs or []) if item}),
        "related_contract_refs": sorted({item for item in (related_contract_refs or []) if item}),
        "related_node_refs": sorted({item for item in (related_node_refs or []) if item}),
        "suggested_fix": suggested_fix.strip(),
    }


def _contract_findings(
    *,
    run_id: str,
    registry: dict[str, Any],
    check_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    contract_families = registry.get("contract_families", [])
    if not isinstance(contract_families, list):
        contract_families = []
    seen_names: dict[str, list[dict[str, Any]]] = {}
    available_names: set[str] = set()

    for item in contract_families:
        if not isinstance(item, dict):
            continue
        contract_name = str(item.get("contract_name", "")).strip()
        if not contract_name:
            continue
        available_names.add(contract_name)
        seen_names.setdefault(contract_name, []).append(item)
        refs = [DEFAULT_REGISTRY_PATH.as_posix()]

        owner = str(item.get("owner", "")).strip()
        if not owner:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="contract_owner_defined",
                    artifact_refs=refs,
                    summary=f"Contract '{contract_name}' is missing a canonical owner.",
                    related_contract_refs=[contract_name],
                    suggested_fix="Declare exactly one owner for this shared contract family.",
                )
            )

        version = str(item.get("current_version", "")).strip()
        if not version:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="contract_version_defined",
                    artifact_refs=refs,
                    summary=f"Contract '{contract_name}' is missing a declared current version.",
                    related_contract_refs=[contract_name],
                    suggested_fix="Add a current_version field to the canonical registry entry.",
                )
            )

        compatibility_policy = str(item.get("compatibility_policy", "")).strip()
        if not compatibility_policy:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="versioning_policy_missing",
                    artifact_refs=refs,
                    summary=f"Contract '{contract_name}' is missing a compatibility policy.",
                    related_contract_refs=[contract_name],
                    suggested_fix="Declare the compatibility policy for this contract family.",
                )
            )

        required_fields = item.get("required_fields")
        if not isinstance(required_fields, list) or not [str(field).strip() for field in required_fields if str(field).strip()]:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="contract_required_fields_defined",
                    artifact_refs=refs,
                    summary=f"Contract '{contract_name}' does not declare required_fields in the machine-readable registry.",
                    related_contract_refs=[contract_name],
                    suggested_fix="Add required_fields to the canonical registry entry so downstream validation is machine-checkable.",
                )
            )

    for contract_name, entries in seen_names.items():
        owners = {str(entry.get("owner", "")).strip() for entry in entries if str(entry.get("owner", "")).strip()}
        if len(entries) > 1 or len(owners) > 1:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="duplicate_contract_authority",
                    artifact_refs=[DEFAULT_REGISTRY_PATH.as_posix()],
                    summary=f"Contract '{contract_name}' has duplicate registry authority declarations.",
                    related_contract_refs=[contract_name],
                    suggested_fix="Collapse duplicate entries and keep one authoritative owner and contract family record.",
                )
            )

    for required_name in sorted(MINIMUM_REQUIRED_CONTRACTS - available_names):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="registry_entry_missing",
                artifact_refs=[DEFAULT_REGISTRY_PATH.as_posix()],
                summary=f"Required contract '{required_name}' is not present in the canonical registry.",
                related_contract_refs=[required_name],
                suggested_fix="Register the missing contract family before tool implementations depend on it.",
            )
        )

    transform_requirements = {
        "question_to_research_problem_transform": {"research_question_packet", "research_problem_packet"},
        "planner_to_governance_runnable_contract": {"execution_packet", "governance_decision_packet"},
        "workflow_dag_to_implementation_dag_link_contract": {"implementation_graph_packet", "dag_node", "dag_edge"},
    }
    for transform_name, dependencies in transform_requirements.items():
        if dependencies.issubset(available_names) and transform_name not in available_names:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="missing_transform_contract",
                    artifact_refs=[DEFAULT_REGISTRY_PATH.as_posix()],
                    summary=f"Transform contract '{transform_name}' is missing even though its upstream and downstream families exist.",
                    related_contract_refs=sorted(dependencies),
                    suggested_fix="Add the missing transform contract to make the handoff canonical.",
                )
            )

    return findings


def _dag_cycle(nodes: list[str], edges: list[tuple[str, str]]) -> bool:
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    indegree: dict[str, int] = {node_id: 0 for node_id in nodes}
    for source, target in edges:
        if source not in adjacency or target not in adjacency:
            continue
        if target in adjacency[source]:
            continue
        adjacency[source].add(target)
        indegree[target] += 1

    queue = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        node_id = queue.pop(0)
        visited += 1
        for target in adjacency[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    return visited != len(nodes)


def _dag_findings(
    *,
    root: Path,
    run_id: str,
    dag: dict[str, Any],
    check_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    artifact_ref = DEFAULT_DAG_PATH.as_posix()
    nodes = dag.get("nodes", [])
    edges = dag.get("edges", [])
    if not isinstance(nodes, list):
        nodes = []
    if not isinstance(edges, list):
        edges = []

    node_map: dict[str, dict[str, Any]] = {}
    producers: dict[str, set[str]] = {}
    governance_nodes: list[str] = []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id", "")).strip()
        node_type = str(node.get("node_type", "")).strip()
        if not node_id:
            continue
        node_map[node_id] = node
        for packet in node.get("output_packet_refs", []):
            packet_name = str(packet).strip()
            if packet_name:
                producers.setdefault(packet_name, set()).add(node_id)

        if node_type == "governance_gate":
            governance_nodes.append(node_id)

        if node_type not in ALLOWED_NODE_TYPES:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="dag_node_type_valid",
                    artifact_refs=[artifact_ref],
                    summary=f"Node '{node_id}' uses unsupported node_type '{node_type}'.",
                    related_node_refs=[node_id],
                    suggested_fix="Use one of the allowed workflow node types in the shared DAG contract.",
                )
            )

    dependency_pairs: list[tuple[str, str]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        relation = str(edge.get("relation", "")).strip()
        source = str(edge.get("from_node_id", "")).strip()
        target = str(edge.get("to_node_id", "")).strip()
        if relation not in ALLOWED_EDGE_RELATIONS:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="dag_edge_relation_valid",
                    artifact_refs=[artifact_ref],
                    summary=f"Edge '{edge.get('edge_id', '')}' uses unsupported relation '{relation}'.",
                    related_node_refs=[source, target],
                    suggested_fix="Use an allowed DAG edge relation from the shared contract model.",
                )
            )
        if relation == "depends_on" and source and target:
            dependency_pairs.append((source, target))

    if _dag_cycle(list(node_map), dependency_pairs):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="dag_dependency_cycle",
                artifact_refs=[artifact_ref],
                summary="The design-iteration DAG contains a dependency cycle.",
                related_node_refs=sorted(node_map),
                suggested_fix="Remove cyclic depends_on edges so the workflow remains acyclic.",
            )
        )

    for node_id, node in node_map.items():
        for packet in node.get("input_packet_refs", []):
            packet_name = str(packet).strip()
            if not packet_name:
                continue
            if packet_name not in producers and packet_name not in KNOWN_EXTERNAL_INPUT_PACKETS:
                findings.append(
                    _finding(
                        run_id=run_id,
                        check_index=check_index,
                        check_id="dag_unsatisfied_input_contract",
                        artifact_refs=[artifact_ref],
                        summary=f"Node '{node_id}' requires input '{packet_name}' with no producing predecessor.",
                        related_node_refs=[node_id],
                        suggested_fix="Add or connect a producer for the missing input packet, or register it as an allowed external workflow input.",
                    )
                )

    if governance_nodes:
        for node_id in governance_nodes:
            node = node_map[node_id]
            required_fields = {"required_inputs", "expected_outputs", "validation_targets", "blocking_dependencies"}
            if not required_fields.issubset(set(node)):
                findings.append(
                    _finding(
                        run_id=run_id,
                        check_index=check_index,
                        check_id="governance_gate_without_runnable_contract",
                        artifact_refs=[artifact_ref],
                        summary=f"Governance node '{node_id}' is missing runnable contract fields.",
                        related_node_refs=[node_id],
                        suggested_fix="Add explicit runnable contract fields to governance gate nodes.",
                    )
                )

    if dag.get("graph_kind") == "workflow_dag" and not dag.get("implementation_graph_ref"):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="workflow_to_implementation_link_missing",
                artifact_refs=[artifact_ref],
                summary="Workflow DAG does not declare a canonical implementation graph link.",
                suggested_fix="Add an implementation_graph_ref when the workflow is meant to project into implementation planning.",
            )
        )
    implementation_graph_ref = str(dag.get("implementation_graph_ref", "")).strip()
    if implementation_graph_ref:
        implementation_path = root / implementation_graph_ref
        if not implementation_path.exists():
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="linked_implementation_graph_missing",
                    artifact_refs=[artifact_ref],
                    summary=f"Workflow DAG links implementation graph '{implementation_graph_ref}' that does not exist.",
                    suggested_fix="Create the linked implementation graph artifact or update the workflow DAG reference.",
                )
            )
        else:
            findings.extend(
                _implementation_graph_findings(
                    root=root,
                    run_id=run_id,
                    implementation_graph_path=implementation_path,
                    check_index=check_index,
                )
            )

    return findings


def _implementation_graph_findings(
    *,
    root: Path,
    run_id: str,
    implementation_graph_path: Path,
    check_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    graph = _load_json(implementation_graph_path)
    artifact_ref = implementation_graph_path.relative_to(root).as_posix()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list):
        nodes = []
    if not isinstance(edges, list):
        edges = []

    node_map: dict[str, dict[str, Any]] = {}
    dependency_pairs: list[tuple[str, str]] = []

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id", "")).strip()
        node_type = str(node.get("node_type", "")).strip()
        title = str(node.get("title", "")).strip()
        status = str(node.get("status", "")).strip()
        blocking_dependencies = node.get("blocking_dependencies", [])
        changes = node.get("changes", [])
        if node_id:
            node_map[node_id] = node

        shape_errors: list[str] = []
        if not node_id:
            shape_errors.append("missing node_id")
        if node_type not in ALLOWED_IMPLEMENTATION_NODE_TYPES:
            shape_errors.append(f"invalid node_type '{node_type}'")
        if not title:
            shape_errors.append("missing title")
        if not status:
            shape_errors.append("missing status")
        if not isinstance(blocking_dependencies, list):
            shape_errors.append("blocking_dependencies must be a list")
        if node_type in {"task", "artifact", "handoff"}:
            if not isinstance(changes, list) or not [str(item).strip() for item in changes if str(item).strip()]:
                shape_errors.append("missing non-empty changes list")
        if shape_errors:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="implementation_node_shape_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Implementation node '{node_id or '<missing>'}' is invalid: {', '.join(shape_errors)}.",
                    related_node_refs=[node_id] if node_id else [],
                    suggested_fix="Emit bounded implementation nodes with explicit type, title, status, dependencies, and owned changes.",
                )
            )

    for node_id, node in node_map.items():
        for dependency in node.get("blocking_dependencies", []):
            dependency_id = str(dependency).strip()
            if not dependency_id:
                continue
            if dependency_id not in node_map:
                findings.append(
                    _finding(
                        run_id=run_id,
                        check_index=check_index,
                        check_id="implementation_dependency_missing_node",
                        artifact_refs=[artifact_ref],
                        summary=f"Implementation node '{node_id}' depends on missing node '{dependency_id}'.",
                        related_node_refs=[node_id, dependency_id],
                        suggested_fix="Remove stale dependency refs or add the missing implementation node.",
                    )
                )
            else:
                dependency_pairs.append((dependency_id, node_id))

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("from_node_id", "")).strip()
        target = str(edge.get("to_node_id", "")).strip()
        relation = str(edge.get("relation", "")).strip()
        if relation not in ALLOWED_IMPLEMENTATION_EDGE_RELATIONS:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="implementation_edge_relation_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Implementation edge '{edge.get('edge_id', '')}' uses unsupported relation '{relation}'.",
                    related_node_refs=[source, target],
                    suggested_fix="Use one of the allowed implementation graph relations.",
                )
            )
        missing_refs = [node_id for node_id in (source, target) if node_id and node_id not in node_map]
        if missing_refs:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="implementation_dependency_missing_node",
                    artifact_refs=[artifact_ref],
                    summary=f"Implementation edge '{edge.get('edge_id', '')}' references missing node(s): {', '.join(missing_refs)}.",
                    related_node_refs=[item for item in (source, target) if item],
                    suggested_fix="Repair implementation edge endpoints so they reference existing nodes.",
                )
            )
        if relation == "depends_on" and source and target and source in node_map and target in node_map:
            dependency_pairs.append((source, target))

    if node_map and _dag_cycle(list(node_map), dependency_pairs):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="implementation_dependency_cycle",
                artifact_refs=[artifact_ref],
                summary="The linked implementation graph contains a dependency cycle.",
                related_node_refs=sorted(node_map),
                suggested_fix="Remove cyclic implementation dependencies so the plan remains buildable.",
            )
        )

    return findings


def _candidate_planning_graph_paths(root: Path, primary_dag_path: Path, linked_implementation_path: Path | None) -> list[Path]:
    candidates: list[Path] = []
    for pattern in (
        "artifacts/planner/graphs/*.json",
        "artifacts/planner/research/*dag*.json",
        "artifacts/planner/research/remaining-work-graph.json",
    ):
        candidates.extend(root.glob(pattern))
    unique: list[Path] = []
    seen: set[Path] = set()
    excluded = {primary_dag_path.resolve()}
    if linked_implementation_path is not None:
        excluded.add(linked_implementation_path.resolve())
    for path in sorted(candidates):
        resolved = path.resolve()
        if resolved in seen or resolved in excluded:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _planning_graph_findings(
    *,
    root: Path,
    run_id: str,
    graph_path: Path,
    check_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    graph = _load_json(graph_path)
    artifact_ref = graph_path.relative_to(root).as_posix()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return [
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="planning_graph_shape_invalid",
                artifact_refs=[artifact_ref],
                summary=f"Planning graph '{artifact_ref}' must expose list-valued nodes and edges.",
                suggested_fix="Normalize the planning graph to expose machine-readable node and edge lists.",
            )
        ]

    node_ids: set[str] = set()
    dependency_pairs: list[tuple[str, str]] = []

    for node in nodes:
        if not isinstance(node, dict):
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="planning_graph_shape_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Planning graph '{artifact_ref}' contains a non-object node entry.",
                    suggested_fix="Ensure every planning graph node is a machine-readable object.",
                )
            )
            continue
        node_id = str(node.get("node_id", "") or node.get("id", "")).strip()
        if not node_id:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="planning_graph_shape_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Planning graph '{artifact_ref}' contains a node without a stable id.",
                    suggested_fix="Add a canonical id or node_id to each planning graph node.",
                )
            )
            continue
        node_ids.add(node_id)

    for edge in edges:
        if not isinstance(edge, dict):
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="planning_graph_shape_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Planning graph '{artifact_ref}' contains a non-object edge entry.",
                    suggested_fix="Ensure every planning graph edge is a machine-readable object.",
                )
            )
            continue
        source = str(edge.get("from_node_id", "") or edge.get("from", "")).strip()
        target = str(edge.get("to_node_id", "") or edge.get("to", "")).strip()
        relation = str(edge.get("relation", "")).strip()
        if relation not in ALLOWED_DISCOVERED_PLANNING_EDGE_RELATIONS:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="planning_edge_relation_invalid",
                    artifact_refs=[artifact_ref],
                    summary=f"Planning graph '{artifact_ref}' uses unsupported edge relation '{relation}'.",
                    related_node_refs=[source, target],
                    suggested_fix="Use one of the allowed planning graph relations.",
                )
            )
        missing_refs = [node_id for node_id in (source, target) if node_id and node_id not in node_ids]
        if missing_refs:
            findings.append(
                _finding(
                    run_id=run_id,
                    check_index=check_index,
                    check_id="planning_dependency_missing_node",
                    artifact_refs=[artifact_ref],
                    summary=f"Planning graph '{artifact_ref}' edge references missing node(s): {', '.join(missing_refs)}.",
                    related_node_refs=[item for item in (source, target) if item],
                    suggested_fix="Repair the planning graph edge endpoints so they reference existing nodes.",
                )
            )
        if relation == "depends_on" and source and target and source in node_ids and target in node_ids:
            dependency_pairs.append((target, source))

    if node_ids and _dag_cycle(sorted(node_ids), dependency_pairs):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="planning_dependency_cycle",
                artifact_refs=[artifact_ref],
                summary=f"Planning graph '{artifact_ref}' contains a dependency cycle.",
                related_node_refs=sorted(node_ids),
                suggested_fix="Remove cyclic planning dependencies so the graph remains executable.",
            )
        )

    return findings


def _boundary_findings(
    *,
    root: Path,
    run_id: str,
    check_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    design_text = _read_text(root, BOUNDARY_DOCS["design_iteration"]).lower()
    governance_text = _read_text(root, BOUNDARY_DOCS["governance"]).lower()
    orchestration_text = _read_text(root, BOUNDARY_DOCS["orchestration"]).lower()
    question_text = _read_text(root, BOUNDARY_DOCS["question"]).lower()
    design_review_automation_text = _read_text(root, BOUNDARY_DOCS["design_review_automation"]).lower()

    if "general execution orchestrator" in design_text or "owns execution orchestration" in design_text:
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="design_iteration_owns_execution_orchestration",
                artifact_refs=[BOUNDARY_DOCS["design_iteration"].as_posix()],
                summary="Design iteration documentation claims general execution orchestration authority.",
                suggested_fix="Keep design iteration focused on critique and next-problem framing, not general execution.",
            )
        )

    if "reconstruct missing planner semantics" in governance_text or "infer missing planner" in governance_text:
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="governance_reconstructs_plan_structure",
                artifact_refs=[BOUNDARY_DOCS["governance"].as_posix()],
                summary="Governance documentation suggests reconstructing planner structure instead of consuming explicit contracts.",
                suggested_fix="Move missing planning semantics into planner outputs and keep governance evaluative only.",
            )
        )

    if "domain logic" in orchestration_text and "runner owns" in orchestration_text:
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="runner_owns_domain_logic",
                artifact_refs=[BOUNDARY_DOCS["orchestration"].as_posix()],
                summary="Orchestration runner documentation suggests ownership of domain logic.",
                suggested_fix="Keep the runner as execution substrate and push domain logic back into bounded tools.",
            )
        )

    if "design critique" in question_text and "owns" in question_text:
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="question_tool_replaces_design_iteration",
                artifact_refs=[BOUNDARY_DOCS["question"].as_posix()],
                summary="Question tool documentation appears to absorb design-iteration critique authority.",
                suggested_fix="Let design iteration generate gaps and let question-tool refine them into research questions.",
            )
        )

    if (
        "design-iteration-tool is the general execution runner" in design_review_automation_text
        or "design-iteration-tool owns execution orchestration" in design_review_automation_text
    ):
        findings.append(
            _finding(
                run_id=run_id,
                check_index=check_index,
                check_id="design_iteration_owns_execution_orchestration",
                artifact_refs=[BOUNDARY_DOCS["design_review_automation"].as_posix()],
                summary="Design review automation documentation drifts into making design iteration the general execution runner.",
                suggested_fix="Keep design iteration responsible for review programs and keep execution of tool calls in the orchestration runner.",
            )
        )

    return findings


def _group_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for finding in findings:
        key = (
            str(finding.get("validator_family", "")).strip(),
            str(finding.get("violated_invariant", "")).strip(),
        )
        grouped.setdefault(key, []).append(finding)

    gap_packets: list[dict[str, Any]] = []
    for index, ((family, invariant), items) in enumerate(sorted(grouped.items()), start=1):
        sorted_items = sorted(
            items,
            key=lambda item: (
                0 if bool(item.get("blocking")) else 1,
                str(item.get("severity", "")).strip(),
                str(item.get("finding_id", "")).strip(),
            ),
        )
        gap_packets.append(
            {
                "packet_type": "design_gap_packet",
                "packet_version": "v1",
                "gap_id": f"gap-{index:03d}",
                "validator_family": family,
                "violated_invariant": invariant,
                "severity": sorted_items[0].get("severity", "medium"),
                "blocking": any(bool(item.get("blocking")) for item in sorted_items),
                "summary": sorted_items[0].get("summary", ""),
                "finding_refs": [str(item.get("finding_id", "")).strip() for item in sorted_items],
                "artifact_refs": sorted(
                    {
                        artifact
                        for item in sorted_items
                        for artifact in item.get("artifact_refs", [])
                        if str(artifact).strip()
                    }
                ),
            }
        )
    return gap_packets


def _question_candidates(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, gap in enumerate(gaps, start=1):
        gap_id = str(gap.get("gap_id", "")).strip()
        invariant = str(gap.get("violated_invariant", "")).strip().replace("_", " ")
        summary = str(gap.get("summary", "")).strip()
        candidates.append(
            {
                "packet_type": "next_question_candidate_packet",
                "packet_version": "v1",
                "question_candidate_id": f"nqc-{index:03d}",
                "source_gap_id": gap_id,
                "title": f"Resolve {gap_id}",
                "question": f"What is the minimal contract or workflow change needed to satisfy invariant '{invariant}'?",
                "decision_target": "shared-contract-and-workflow-design",
                "downstream_value": "unblock_implementation",
                "why_now": summary,
                "artifact_refs": gap.get("artifact_refs", []),
            }
        )
    return candidates


def run_design_iteration(
    *,
    root: str = ".",
    registry_path: str = DEFAULT_REGISTRY_PATH.as_posix(),
    checkset_path: str = DEFAULT_CHECKSET_PATH.as_posix(),
    dag_path: str = DEFAULT_DAG_PATH.as_posix(),
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    plan_quality_scoring_path: str = DEFAULT_PLAN_QUALITY_SCORING_PATH.as_posix(),
) -> tuple[int, dict[str, Any]]:
    base = Path(root).resolve()
    registry_file = (base / registry_path).resolve()
    checkset_file = (base / checkset_path).resolve()
    dag_file = (base / dag_path).resolve()
    output_base = (base / output_root).resolve()
    plan_quality_scoring_file = (base / plan_quality_scoring_path).resolve()
    blockers: list[str] = []

    for label, path in (
        ("registry_path_missing", registry_file),
        ("checkset_path_missing", checkset_file),
        ("dag_path_missing", dag_file),
    ):
        if not path.exists():
            blockers.append(label)
    if not plan_quality_scoring_file.exists():
        blockers.append("plan_quality_scoring_path_missing")

    run_id = _run_id()
    run_root = output_base / run_id
    findings_packet_path = run_root / "design-findings.packet.json"
    gaps_packet_path = run_root / "design-gaps.packet.json"
    questions_packet_path = run_root / "next-question-candidates.packet.json"
    findings_log_path = run_root / "findings.jsonl"

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "run_id": run_id,
                "root": base.as_posix(),
                "registry_path": registry_file.as_posix(),
                "checkset_path": checkset_file.as_posix(),
                "dag_path": dag_file.as_posix(),
                "output_root": run_root.as_posix(),
                "plan_quality_scoring_path": plan_quality_scoring_file.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    registry = _load_yaml(registry_file)
    checkset = _load_yaml(checkset_file)
    dag = _load_json(dag_file)
    check_index = _build_check_index(checkset)
    linked_implementation_path: Path | None = None
    implementation_graph_ref = str(dag.get("implementation_graph_ref", "")).strip()
    if implementation_graph_ref:
        linked_implementation_path = (base / implementation_graph_ref).resolve()

    contract_findings = _contract_findings(run_id=run_id, registry=registry, check_index=check_index)
    dag_findings = _dag_findings(root=base, run_id=run_id, dag=dag, check_index=check_index)
    discovered_planning_findings: list[dict[str, Any]] = []
    for graph_path in _candidate_planning_graph_paths(base, dag_file, linked_implementation_path):
        discovered_planning_findings.extend(
            _planning_graph_findings(root=base, run_id=run_id, graph_path=graph_path, check_index=check_index)
        )
    boundary_findings = _boundary_findings(root=base, run_id=run_id, check_index=check_index)
    findings = sorted(
        contract_findings + dag_findings + discovered_planning_findings + boundary_findings,
        key=lambda item: (
            0 if bool(item.get("blocking")) else 1,
            str(item.get("severity", "")).strip(),
            str(item.get("finding_id", "")).strip(),
        ),
    )
    gap_packets = _group_findings(findings)
    question_candidates = _question_candidates(gap_packets)

    findings_packet = {
        "packet_type": "design_findings_packet",
        "packet_version": "v1",
        "run_id": run_id,
        "generated_at": _utc_now(),
        "finding_count": len(findings),
        "blocking_finding_count": sum(1 for item in findings if bool(item.get("blocking"))),
        "findings": findings,
        "artifact_refs": [
            registry_file.relative_to(base).as_posix(),
            checkset_file.relative_to(base).as_posix(),
            dag_file.relative_to(base).as_posix(),
            plan_quality_scoring_file.relative_to(base).as_posix(),
        ]
        + [
            path.relative_to(base).as_posix()
            for path in _candidate_planning_graph_paths(base, dag_file, linked_implementation_path)
        ],
        "evidence_refs": [
            "https://arxiv.org/abs/2303.17651",
            "https://arxiv.org/abs/2303.11366",
            "https://arxiv.org/abs/2305.11738",
        ],
    }
    gap_packet_bundle = {
        "packet_type": "design_gap_packet_bundle",
        "packet_version": "v1",
        "run_id": run_id,
        "gap_count": len(gap_packets),
        "gaps": gap_packets,
    }
    question_packet_bundle = {
        "packet_type": "next_question_candidate_packet_bundle",
        "packet_version": "v1",
        "run_id": run_id,
        "candidate_count": len(question_candidates),
        "candidates": question_candidates,
    }

    write_json(findings_packet_path, findings_packet)
    write_json(gaps_packet_path, gap_packet_bundle)
    write_json(questions_packet_path, question_packet_bundle)
    _write_jsonl(findings_log_path, findings)

    blocking_findings = sum(1 for item in findings if bool(item.get("blocking")))
    status = "blocked" if blocking_findings else "ok"
    return (1 if blocking_findings else 0), envelope(
        command=COMMAND,
        status=status,
        ok=blocking_findings == 0,
        payload={
            "run_id": run_id,
            "root": base.as_posix(),
            "registry_path": registry_file.as_posix(),
            "checkset_path": checkset_file.as_posix(),
            "dag_path": dag_file.as_posix(),
            "output_root": run_root.as_posix(),
            "plan_quality_scoring_path": plan_quality_scoring_file.as_posix(),
            "findings_packet_path": findings_packet_path.as_posix(),
            "gaps_packet_path": gaps_packet_path.as_posix(),
            "question_candidates_path": questions_packet_path.as_posix(),
            "findings_log_path": findings_log_path.as_posix(),
            "finding_count": len(findings),
            "blocking_finding_count": blocking_findings,
            "gap_count": len(gap_packets),
            "question_candidate_count": len(question_candidates),
            "inspected_planning_graph_count": len(_candidate_planning_graph_paths(base, dag_file, linked_implementation_path)),
            "blockers": [item["finding_id"] for item in findings if bool(item.get("blocking"))],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry-path", default=DEFAULT_REGISTRY_PATH.as_posix())
    parser.add_argument("--checkset-path", default=DEFAULT_CHECKSET_PATH.as_posix())
    parser.add_argument("--dag-path", default=DEFAULT_DAG_PATH.as_posix())
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--plan-quality-scoring-path", default=DEFAULT_PLAN_QUALITY_SCORING_PATH.as_posix())
    args = parser.parse_args()
    code, report = run_design_iteration(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
