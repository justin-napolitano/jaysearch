from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 4)


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _load_graph(root: str, graph_id: str) -> dict[str, Any]:
    return _read_json(Path(root) / "artifacts" / "planner" / "graphs" / f"{graph_id}.json")


def _load_scoring(root: str) -> dict[str, Any]:
    return _read_yaml(Path(root) / "spec" / "scoring.yaml")


def _planner_scores(graph: dict[str, Any]) -> dict[str, float]:
    nodes = graph.get("nodes", [])
    total_nodes = len(nodes)
    legal_statuses = {"draft", "ready", "blocked", "in_progress", "in_review", "validated", "recovery_required", "done", "rejected", "archived"}
    legal_nodes = sum(1 for node in nodes if node.get("status") in legal_statuses)
    provenance_complete = sum(
        1
        for node in nodes
        if isinstance(node.get("provenance"), dict)
        and node["provenance"].get("source_session")
        and node["provenance"].get("source_artifact")
        and node["provenance"].get("recorded_at")
    )
    commitment_candidates = [node for node in nodes if node.get("node_type") in {"goal", "task", "decision", "validation"}]
    ready_nodes = [node for node in commitment_candidates if node.get("status") in {"ready", "validated", "in_review"}]
    evidence_required = [node for node in nodes if node.get("status") not in {"draft", "archived"}]
    evidence_complete = [node for node in evidence_required if node.get("evidence_refs")]
    blockers = sum(
        1
        for node in nodes
        if node.get("status") == "blocked"
        or (node.get("node_type") == "question" and node.get("blocking") is True)
    )
    return {
        "TLS": _safe_ratio(legal_nodes, total_nodes),
        "PCS": _safe_ratio(provenance_complete, total_nodes),
        "BRS": _safe_ratio(len(ready_nodes), len(commitment_candidates)),
        "ECS": _safe_ratio(len(evidence_complete), len(evidence_required)),
        "BPS": _clamp(1.0 - _safe_ratio(blockers, total_nodes)),
    }


def _implementation_scores(graph: dict[str, Any]) -> dict[str, float]:
    nodes = graph.get("nodes", [])
    total_nodes = len(nodes)
    legal_statuses = {"draft", "ready", "blocked", "in_progress", "in_review", "validated", "recovery_required", "done", "rejected", "archived"}
    legal_nodes = sum(1 for node in nodes if node.get("status") in legal_statuses)
    implementation_nodes = [node for node in nodes if node.get("node_type") in {"task", "validation", "tool_run", "handoff"}]
    scoped_nodes = [
        node
        for node in implementation_nodes
        if node.get("changes")
        or node.get("path")
        or node.get("node_type") in {"validation", "tool_run", "handoff"}
    ]
    validation_nodes = [node for node in nodes if node.get("node_type") == "validation"]
    passed_validation = [node for node in validation_nodes if node.get("status") in {"validated", "done"}]
    review_required = [node for node in implementation_nodes if node.get("status") in {"validated", "done", "recovery_required"}]
    reviewed = [node for node in review_required if node.get("status") in {"done", "recovery_required"}]
    recovery_nodes = [node for node in nodes if node.get("status") == "recovery_required"]
    provenance_complete = sum(
        1
        for node in implementation_nodes
        if isinstance(node.get("provenance"), dict)
        and node["provenance"].get("source_session")
        and node["provenance"].get("source_artifact")
        and node["provenance"].get("recorded_at")
    )
    return {
        "TLS": _safe_ratio(legal_nodes, total_nodes),
        "SCS": _safe_ratio(len(scoped_nodes), len(implementation_nodes)),
        "VPR": _safe_ratio(len(passed_validation), len(validation_nodes)),
        "RCS": _safe_ratio(len(reviewed), len(review_required)),
        "RDS": _clamp(1.0 if not recovery_nodes else 0.5),
        "PCS": _safe_ratio(provenance_complete, len(implementation_nodes)),
    }


def _weighted_score(metric_values: dict[str, float], weights: dict[str, float]) -> float:
    total = 0.0
    for key, value in metric_values.items():
        weight_key = f"{key.lower()}_weight"
        total += value * float(weights.get(weight_key, 0.0))
    return round(total * 100, 2)


def score_graph(root: str = ".", graph_id: str = "") -> dict[str, Any]:
    if not graph_id:
        raise ValueError("graph_id_required")
    graph = _load_graph(root, graph_id)
    scoring = _load_scoring(root)
    planner_metrics = _planner_scores(graph)
    implementation_metrics = _implementation_scores(graph)
    planner_score = _weighted_score(planner_metrics, scoring.get("planner_game", {}).get("weights", {}))
    implementation_score = _weighted_score(
        implementation_metrics, scoring.get("implementation_game", {}).get("weights", {})
    )
    return {
        "tool": "planner_score",
        "graph_id": graph_id,
        "planner_game": {
            "score": planner_score,
            "metrics": planner_metrics,
        },
        "implementation_game": {
            "score": implementation_score,
            "metrics": implementation_metrics,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--graph-id", required=True)
    args = parser.parse_args()
    report = score_graph(root=args.root, graph_id=args.graph_id)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
