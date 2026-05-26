from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import networkx as nx

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "select-candidate-dag"
DEFAULT_OUTPUT_ROOT = Path("artifacts/candidate-dag-selections/runs")
SELECTION_POLICY_REF = "docs/candidate-dag-selection-v1.md#v1-runtime-shape"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("cds-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "").strip()


def _edge_endpoint(edge: dict[str, Any], *names: str) -> str:
    for name in names:
        value = str(edge.get(name, "")).strip()
        if value:
            return value
    return ""


def _node_list(dag: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(dag.get("nodes", []))


def _edge_list(dag: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(dag.get("edges", []))


def _validation_refs(node: dict[str, Any]) -> list[str]:
    refs = _string_list(node.get("validation_refs", []))
    refs.extend(_string_list(node.get("validation_targets", [])))
    refs.extend(_string_list(node.get("validation_commands", [])))
    refs.extend(_string_list(node.get("acceptance_checks", [])))
    refs.extend(_string_list(node.get("expected_outputs", [])))
    return refs


def _owned_refs(node: dict[str, Any]) -> list[str]:
    refs = _string_list(node.get("owned_changes", []))
    refs.extend(_string_list(node.get("owned_surfaces", [])))
    scope = node.get("scope")
    if isinstance(scope, dict):
        refs.extend(_string_list(scope.get("owned_surfaces", [])))
    return refs


def _evidence_refs(node: dict[str, Any]) -> list[str]:
    refs = _string_list(node.get("evidence_refs", []))
    refs.extend(_string_list(node.get("source_artifacts", [])))
    return refs


def _is_executable(node: dict[str, Any]) -> bool:
    node_type = str(node.get("node_type", "")).strip()
    return node_type in {"runtime", "validation", "contract", "documentation"} or bool(_owned_refs(node))


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
        blockers.append("dag_missing_nodes")
    return graph, blockers


def _critical_path_summary(graph: nx.DiGraph) -> dict[str, Any]:
    if graph.number_of_nodes() == 0 or not nx.is_directed_acyclic_graph(graph):
        return {"critical_path_length": 0, "critical_path_node_refs": []}
    path = nx.algorithms.dag.dag_longest_path(graph)
    return {"critical_path_length": len(path), "critical_path_node_refs": path}


def _parallel_layer_count(graph: nx.DiGraph) -> int:
    if graph.number_of_nodes() == 0 or not nx.is_directed_acyclic_graph(graph):
        return 0
    generations = list(nx.algorithms.dag.topological_generations(graph))
    return max((len(generation) for generation in generations), default=0)


def _hard_gate_blockers(dag: dict[str, Any], graph: nx.DiGraph, graph_blockers: list[str]) -> list[str]:
    blockers = list(graph_blockers)
    if str(dag.get("graph_type", "")).strip() not in {
        "implementation_dag",
        "candidate_dag",
        "execution_dag",
    }:
        blockers.append("graph_type_not_candidate_execution_dag")
    if graph.number_of_edges() == 0 and graph.number_of_nodes() > 1:
        blockers.append("dag_missing_dependency_edges")
    if graph.number_of_nodes() > 0 and not nx.is_directed_acyclic_graph(graph):
        blockers.append("dag_contains_cycle")
    for node_id, payload in graph.nodes(data="payload"):
        if not isinstance(payload, dict):
            blockers.append(f"node_payload_invalid:{node_id}")
            continue
        if _is_executable(payload) and not _validation_refs(payload):
            blockers.append(f"node_missing_validation_targets:{node_id}")
        if _is_executable(payload) and not _owned_refs(payload):
            blockers.append(f"node_missing_owned_surfaces:{node_id}")
        if str(payload.get("risk_level", "")).strip() in {"high", "critical"} and not _evidence_refs(payload):
            blockers.append(f"high_risk_node_missing_evidence_refs:{node_id}")
    return sorted(set(blockers))


def _score_dag(graph: nx.DiGraph, hard_gate_blockers: list[str]) -> dict[str, Any]:
    nodes = [payload for _node_id, payload in graph.nodes(data="payload") if isinstance(payload, dict)]
    node_count = len(nodes)
    edge_count = graph.number_of_edges()
    executable_nodes = [node for node in nodes if _is_executable(node)]
    executable_count = max(1, len(executable_nodes))
    validation_complete = sum(1 for node in executable_nodes if _validation_refs(node))
    owned_complete = sum(1 for node in executable_nodes if _owned_refs(node))
    evidence_nodes = sum(1 for node in nodes if _evidence_refs(node))
    critical_path = _critical_path_summary(graph)
    critical_path_length = int(critical_path["critical_path_length"])
    density = edge_count / max(1, node_count * max(1, node_count - 1))
    boundedness = max(0, 10 - max(0, node_count - 8))
    validation = round(10 * validation_complete / executable_count, 3)
    scope_isolation = round(10 * owned_complete / executable_count, 3)
    evidence = round(10 * evidence_nodes / max(1, node_count), 3)
    dependency_efficiency = round(max(0, 10 - (density * 20)), 3)
    parallelism = round(min(10, _parallel_layer_count(graph) * 2), 3)
    recovery = round(max(0, 10 - max(0, critical_path_length - 4)), 3)
    critical_path_score = round(max(0, 10 - max(0, critical_path_length - 3)), 3)
    if hard_gate_blockers:
        total = 0.0
    else:
        total = round(
            (
                boundedness * 2
                + validation * 2
                + dependency_efficiency * 1.5
                + scope_isolation * 1.5
                + parallelism
                + recovery
                + evidence
                + critical_path_score
            )
            / 11,
            3,
        )
    return {
        "boundedness": boundedness,
        "dependency_efficiency": dependency_efficiency,
        "parallelism_safety": parallelism,
        "validation_completeness": validation,
        "scope_isolation": scope_isolation,
        "recovery_containment": recovery,
        "evidence_and_assumption_clarity": evidence,
        "critical_path_score": critical_path_score,
        "total_score": total,
        "node_count": node_count,
        "edge_count": edge_count,
        "executable_node_count": len(executable_nodes),
        "scoring_notes": [
            "hard gates are applied before quality scoring",
            "V1 uses transparent heuristic MCDA-style scoring",
            "weights prioritize boundedness and validation completeness",
        ],
    }


def _candidate_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(manifest.get("candidate_dag_refs", []))


def _evaluation_packet(
    *,
    candidate: dict[str, Any],
    dag_ref: str,
    hard_gate_blockers: list[str],
    score_breakdown: dict[str, Any],
    critical_path_summary: dict[str, Any],
    evidence_refs: list[str],
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    eligible = not hard_gate_blockers
    return {
        "packet_type": "candidate_dag_evaluation",
        "packet_version": "v1",
        "packet_id": f"candidate-dag-evaluation:{candidate_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "evaluation_id": f"candidate-dag-evaluation:{candidate_id}",
        "candidate_id": candidate_id,
        "candidate_dag_ref": dag_ref,
        "hard_gate_status": "passed" if eligible else "failed",
        "hard_gate_blockers": hard_gate_blockers,
        "score_breakdown": score_breakdown,
        "critical_path_summary": critical_path_summary,
        "evidence_refs": sorted(set(evidence_refs)),
        "promotion_status": "promoted" if eligible else "blocked",
    }


def select_candidate_dag(
    *,
    root: str = ".",
    manifest_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    manifest_ref = str((repo_root / manifest_path).resolve())
    manifest = _load_json(repo_root / manifest_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    if str(manifest.get("packet_type", "")).strip() != "candidate_dag_manifest":
        blockers.append("candidate_dag_manifest_packet_type_invalid")
    candidates = _candidate_items(manifest)
    if not candidates:
        blockers.append("candidate_dag_refs_missing")

    evaluation_paths: list[str] = []
    evaluations: list[dict[str, Any]] = []
    if not blockers:
        for index, candidate in enumerate(candidates, start=1):
            candidate_id = str(candidate.get("candidate_id", "")).strip() or f"candidate-{index:02d}"
            dag_ref = str(candidate.get("dag_ref", "")).strip()
            evidence_refs = _string_list(manifest.get("evidence_refs", []))
            evidence_refs.extend(_string_list(candidate.get("evidence_refs", [])))
            graph = nx.DiGraph()
            graph_blockers: list[str] = []
            dag: dict[str, Any] = {}
            absolute_dag_ref = ""
            if not dag_ref:
                graph_blockers.append(f"candidate_missing_dag_ref:{candidate_id}")
            else:
                absolute_dag_ref = str((repo_root / dag_ref).resolve())
                try:
                    dag = _load_json(repo_root / dag_ref)
                    graph, graph_blockers = _build_graph(_node_list(dag), _edge_list(dag))
                except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
                    graph_blockers.append(f"{exc.__class__.__name__}:{dag_ref}:{exc}")
            candidate_blockers = _string_list(candidate.get("blockers", []))
            hard_gate_blockers = sorted(
                set(candidate_blockers + _hard_gate_blockers(dag, graph, graph_blockers))
            )
            critical_path = _critical_path_summary(graph)
            score_breakdown = _score_dag(graph, hard_gate_blockers)
            evaluation = _evaluation_packet(
                candidate={**candidate, "candidate_id": candidate_id},
                dag_ref=absolute_dag_ref,
                hard_gate_blockers=hard_gate_blockers,
                score_breakdown=score_breakdown,
                critical_path_summary=critical_path,
                evidence_refs=evidence_refs,
            )
            path = write_json(
                run_root / f"candidate-dag-evaluation-{index:02d}.packet.json",
                evaluation,
            ).as_posix()
            evaluations.append(evaluation)
            evaluation_paths.append(path)

    eligible = [
        (evaluation, path)
        for evaluation, path in zip(evaluations, evaluation_paths)
        if evaluation.get("promotion_status") == "promoted"
    ]
    if not blockers and not eligible:
        blockers.append("no_eligible_candidate_dags")

    selected_evaluation: dict[str, Any] | None = None
    selected_evaluation_path = ""
    if not blockers:
        selected_evaluation, selected_evaluation_path = sorted(
            eligible,
            key=lambda item: (
                -float(item[0]["score_breakdown"]["total_score"]),
                str(item[0]["candidate_id"]),
                str(item[0]["candidate_dag_ref"]),
            ),
        )[0]

    selected_dag_ref = str(selected_evaluation.get("candidate_dag_ref", "")) if selected_evaluation else ""
    rejected_dag_refs = [
        str(evaluation.get("candidate_dag_ref", ""))
        for evaluation in evaluations
        if str(evaluation.get("candidate_dag_ref", "")) != selected_dag_ref
    ]
    rejected_evaluation_refs = [
        path for path in evaluation_paths if path != selected_evaluation_path
    ]
    evidence_refs = _string_list(manifest.get("evidence_refs", []))
    for evaluation in evaluations:
        evidence_refs.extend(_string_list(evaluation.get("evidence_refs", [])))

    selection_path = ""
    if not blockers and selected_evaluation is not None:
        manifest_id = str(manifest.get("manifest_id", "manifest")).replace(":", "-")
        selection = {
            "packet_type": "candidate_dag_selection",
            "packet_version": "v1",
            "packet_id": f"candidate-dag-selection:{manifest_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "selection_id": f"candidate-dag-selection:{manifest_id}",
            "source_manifest_ref": manifest_ref,
            "selected_dag_ref": selected_dag_ref,
            "selected_evaluation_ref": selected_evaluation_path,
            "rejected_dag_refs": rejected_dag_refs,
            "rejected_evaluation_refs": rejected_evaluation_refs,
            "selection_policy": {
                "policy_ref": str(manifest.get("selection_policy_ref", "")).strip()
                or SELECTION_POLICY_REF,
                "method": "hard_gate_then_transparent_mcda_heuristic",
                "tie_breakers": ["highest_total_score", "candidate_id", "candidate_dag_ref"],
                "uses_networkx": True,
            },
            "score_summary": evaluations,
            "evidence_refs": sorted(set(evidence_refs)),
            "blockers": [],
        }
        selection_path = write_json(run_root / "candidate-dag-selection.packet.json", selection).as_posix()

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "manifest_path": manifest_ref,
            "candidate_dag_selection_path": selection_path,
            "selected_dag_ref": selected_dag_ref,
            "selected_evaluation_ref": selected_evaluation_path,
            "rejected_dag_refs": rejected_dag_refs,
            "rejected_evaluation_refs": rejected_evaluation_refs,
            "evaluation_packet_paths": evaluation_paths,
            "score_summary": evaluations,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "candidate-dag-selection.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = select_candidate_dag(
            root=args.root,
            manifest_path=args.manifest_path,
            output_root=args.output_root,
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
