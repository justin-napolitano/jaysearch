from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.research_questions import write_json


COMMAND = "plan-quality-score"
DEFAULT_POLICY_PATH = Path("spec/plan-quality-scoring.yaml")
DEFAULT_OUTPUT_ROOT = Path("artifacts/plan-quality-score/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("pqs-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"yaml_not_object:{path.as_posix()}")
    return payload


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 4)


def _node_index(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node in plan.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id", "")).strip()
        if node_id:
            result[node_id] = node
    return result


def _edge_list(plan: dict[str, Any]) -> list[dict[str, Any]]:
    edges = plan.get("edges", [])
    return [edge for edge in edges if isinstance(edge, dict)]


def _trace_cycle(plan: dict[str, Any]) -> bool:
    nodes = _node_index(plan)
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in _edge_list(plan):
        relation = str(edge.get("relation", "")).strip()
        if relation not in {"depends_on", "gated_by"}:
            continue
        from_node = str(edge.get("from_node_id", "")).strip()
        to_node = str(edge.get("to_node_id", "")).strip()
        if from_node and to_node and from_node in adjacency and to_node in adjacency:
            adjacency[from_node].append(to_node)

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        for parent in adjacency.get(node_id, []):
            if dfs(parent):
                return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    return any(dfs(node_id) for node_id in adjacency)


def _critical_path_length(plan: dict[str, Any]) -> int:
    if _trace_cycle(plan):
        return len(_node_index(plan))
    nodes = _node_index(plan)
    parents: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in _edge_list(plan):
        relation = str(edge.get("relation", "")).strip()
        if relation not in {"depends_on", "gated_by"}:
            continue
        from_node = str(edge.get("from_node_id", "")).strip()
        to_node = str(edge.get("to_node_id", "")).strip()
        if from_node and to_node and from_node in parents and to_node in parents:
            parents[from_node].append(to_node)

    memo: dict[str, int] = {}

    def depth(node_id: str) -> int:
        if node_id in memo:
            return memo[node_id]
        upstream = parents.get(node_id, [])
        value = 1 if not upstream else 1 + max(depth(parent) for parent in upstream)
        memo[node_id] = value
        return value

    return max((depth(node_id) for node_id in nodes), default=0)


def _gate_results(
    plan: dict[str, Any],
    selected_scope: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes = _node_index(plan)
    edges = _edge_list(plan)
    selected_scope_ref = str(plan.get("selected_solution_scope_ref", "")).strip()
    selected_scope_packet_id = str(selected_scope.get("packet_id", "")).strip()
    plan_readiness = str(plan.get("plan_readiness", "candidate")).strip() or "candidate"

    def gate(gate_id: str, passed: bool, detail: str) -> dict[str, Any]:
        return {
            "gate_id": gate_id,
            "passed": bool(passed),
            "detail": detail,
        }

    has_cycle = _trace_cycle(plan)
    node_identity_complete = bool(nodes) and all(
        str(node.get("node_id", "")).strip() and str(node.get("title", "")).strip()
        for node in nodes.values()
    )
    edge_identity_complete = all(
        str(edge.get("edge_id", "")).strip()
        and str(edge.get("from_node_id", "")).strip() in nodes
        and str(edge.get("to_node_id", "")).strip() in nodes
        and str(edge.get("relation", "")).strip() in {"depends_on", "gated_by", "conflicts_with", "informed_by"}
        for edge in edges
    )
    runnable_contract_complete = all(
        isinstance(node.get("expected_outputs"), list)
        and node.get("expected_outputs")
        and isinstance(node.get("validation_targets"), list)
        and node.get("validation_targets")
        and isinstance(node.get("completion_evidence_requirements"), list)
        and node.get("completion_evidence_requirements")
        for node in nodes.values()
    )
    validation_targets_present = all(
        isinstance(node.get("validation_targets"), list) and node.get("validation_targets")
        for node in nodes.values()
    )
    scope_ownership_declared = all(
        (isinstance(node.get("owned_changes"), list) and node.get("owned_changes"))
        or (isinstance(node.get("conflict_domains"), list) and node.get("conflict_domains"))
        for node in nodes.values()
    )
    execution_ready_slices_present = not (
        plan_readiness == "execution_ready"
        and not (isinstance(plan.get("execution_slices"), list) and plan.get("execution_slices"))
    )

    return [
        gate(
            "acyclic_execution_graph",
            not has_cycle,
            "execution dependencies are acyclic" if not has_cycle else "cycle detected in dependency edges",
        ),
        gate(
            "selected_solution_scope_present",
            bool(selected_scope_ref and selected_scope_ref == selected_scope_packet_id),
            "plan references the selected solution scope"
            if selected_scope_ref == selected_scope_packet_id and selected_scope_ref
            else "plan selected_solution_scope_ref does not match selected scope packet",
        ),
        gate(
            "runnable_contract_complete",
            runnable_contract_complete and execution_ready_slices_present,
            "node-level runnable contract fields are present"
            if runnable_contract_complete and execution_ready_slices_present
            else "missing expected_outputs, validation_targets, completion_evidence_requirements, or execution_ready slices",
        ),
        gate(
            "node_and_edge_identity_complete",
            node_identity_complete and edge_identity_complete,
            "nodes and edges have stable machine-readable identity"
            if node_identity_complete and edge_identity_complete
            else "missing node/edge identity or invalid edge endpoints/relations",
        ),
        gate(
            "validation_targets_present",
            validation_targets_present,
            "validation targets are declared"
            if validation_targets_present
            else "one or more nodes are missing validation targets",
        ),
        gate(
            "scope_ownership_declared",
            scope_ownership_declared,
            "scope ownership is declared"
            if scope_ownership_declared
            else "one or more nodes are missing owned_changes and conflict_domains",
        ),
    ]


def _boundedness_score(plan: dict[str, Any]) -> float:
    nodes = list(_node_index(plan).values())
    if not nodes:
        return 0.0
    bounded = 0
    for node in nodes:
        goal = str(node.get("goal", "")).strip()
        outputs = node.get("expected_outputs", [])
        changes = node.get("owned_changes", [])
        if goal and isinstance(outputs, list) and outputs and isinstance(changes, list) and changes:
            bounded += 1
    return _safe_ratio(bounded, len(nodes))


def _dependency_efficiency_score(plan: dict[str, Any]) -> float:
    node_count = len(_node_index(plan))
    if node_count <= 1:
        return 1.0
    dep_edges = [
        edge for edge in _edge_list(plan) if str(edge.get("relation", "")).strip() in {"depends_on", "gated_by"}
    ]
    max_reasonable_edges = node_count * 2
    sparsity = 1.0 - min(len(dep_edges), max_reasonable_edges) / max_reasonable_edges
    cps_bonus = 1.0 - _safe_ratio(max(_critical_path_length(plan) - 1, 0), node_count)
    return _clamp((sparsity * 0.45) + (cps_bonus * 0.55))


def _validation_completeness_score(plan: dict[str, Any]) -> float:
    nodes = list(_node_index(plan).values())
    if not nodes:
        return 0.0
    complete = 0
    for node in nodes:
        if (
            isinstance(node.get("validation_targets"), list)
            and node.get("validation_targets")
            and isinstance(node.get("completion_evidence_requirements"), list)
            and node.get("completion_evidence_requirements")
        ):
            complete += 1
    return _safe_ratio(complete, len(nodes))


def _parallelism_safety_score(plan: dict[str, Any]) -> float:
    nodes = list(_node_index(plan).values())
    if not nodes:
        return 0.0
    conflict_aware = 0
    for node in nodes:
        conflicts = node.get("conflict_domains", [])
        changes = node.get("owned_changes", [])
        if (isinstance(conflicts, list) and conflicts) or (isinstance(changes, list) and changes):
            conflict_aware += 1
    return _safe_ratio(conflict_aware, len(nodes))


def _scope_isolation_score(plan: dict[str, Any]) -> float:
    nodes = list(_node_index(plan).values())
    if not nodes:
        return 0.0
    isolated = 0
    for node in nodes:
        changes = node.get("owned_changes", [])
        if isinstance(changes, list) and 0 < len(changes) <= 3:
            isolated += 1
    return _safe_ratio(isolated, len(nodes))


def _recovery_containment_score(plan: dict[str, Any]) -> float:
    nodes = list(_node_index(plan).values())
    if not nodes:
        return 0.0
    constrained = 0
    for node in nodes:
        changes = node.get("owned_changes", [])
        outputs = node.get("expected_outputs", [])
        if (
            isinstance(changes, list)
            and len(changes) <= 3
            and isinstance(outputs, list)
            and len(outputs) <= 3
        ):
            constrained += 1
    return _safe_ratio(constrained, len(nodes))


def _evidence_assumption_score(plan: dict[str, Any], evidence_refs: list[str]) -> float:
    assumptions = plan.get("assumptions", [])
    risks = plan.get("risks", [])
    plan_evidence = plan.get("evidence_refs", [])
    evidence_present = bool(evidence_refs or (isinstance(plan_evidence, list) and plan_evidence))
    assumption_present = isinstance(assumptions, list) and bool(assumptions)
    risk_present = isinstance(risks, list) and bool(risks)
    score = 0.0
    if evidence_present:
        score += 0.4
    if assumption_present:
        score += 0.3
    if risk_present:
        score += 0.3
    return round(score, 4)


def _critical_path_score(plan: dict[str, Any]) -> float:
    node_count = len(_node_index(plan))
    if node_count <= 1:
        return 1.0
    longest = _critical_path_length(plan)
    return _clamp(1.0 - _safe_ratio(max(longest - 1, 0), node_count))


def _metric_map(plan: dict[str, Any], evidence_refs: list[str]) -> dict[str, float]:
    return {
        "BDS": _boundedness_score(plan),
        "DES": _dependency_efficiency_score(plan),
        "VCS": _validation_completeness_score(plan),
        "PSS": _parallelism_safety_score(plan),
        "SIS": _scope_isolation_score(plan),
        "RCS": _recovery_containment_score(plan),
        "EAS": _evidence_assumption_score(plan, evidence_refs),
        "CPS": _critical_path_score(plan),
    }


def _aggregate_score(
    metrics: dict[str, float],
    policy: dict[str, Any],
) -> tuple[dict[str, float], dict[str, float], float]:
    primary_defs = policy.get("primary_metrics", [])
    secondary_defs = policy.get("secondary_metrics", [])
    primary_scores: dict[str, float] = {}
    secondary_scores: dict[str, float] = {}
    total = 0.0
    for item in primary_defs:
        if not isinstance(item, dict):
            continue
        metric_id = str(item.get("metric_id", "")).strip()
        weight = float(item.get("weight", 0.0))
        value = float(metrics.get(metric_id, 0.0))
        primary_scores[metric_id] = round(value, 4)
        total += value * weight
    for item in secondary_defs:
        if not isinstance(item, dict):
            continue
        metric_id = str(item.get("metric_id", "")).strip()
        weight = float(item.get("weight", 0.0))
        value = float(metrics.get(metric_id, 0.0))
        secondary_scores[metric_id] = round(value, 4)
        total += value * weight
    return primary_scores, secondary_scores, round(total * 100, 2)


def _anti_cheat_flags(plan: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    nodes = list(_node_index(plan).values())
    dep_edges = [
        edge for edge in _edge_list(plan) if str(edge.get("relation", "")).strip() in {"depends_on", "gated_by"}
    ]
    if len(nodes) >= 6 and len(dep_edges) == 0:
        flags.append("no_fake_parallelism")
    tiny_nodes = 0
    for node in nodes:
        outputs = node.get("expected_outputs", [])
        changes = node.get("owned_changes", [])
        if isinstance(outputs, list) and len(outputs) <= 1 and isinstance(changes, list) and len(changes) <= 1:
            tiny_nodes += 1
    if nodes and _safe_ratio(tiny_nodes, len(nodes)) > 0.75:
        flags.append("no_micro_node_spam")
    if any(not node.get("validation_targets") for node in nodes):
        flags.append("no_fake_validation")
    fragmented = 0
    for node in nodes:
        conflicts = node.get("conflict_domains", [])
        if isinstance(conflicts, list) and len(conflicts) > 3:
            fragmented += 1
    if nodes and _safe_ratio(fragmented, len(nodes)) > 0.4:
        flags.append("no_scope_fragmentation")
    return sorted(set(flags))


def _plan_ref(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def compare_plans(
    *,
    root: str = ".",
    selected_scope_path: str,
    plan_paths: list[str],
    policy_path: str = DEFAULT_POLICY_PATH.as_posix(),
    evidence_refs: list[str] | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> dict[str, Any]:
    repo_root = Path(root)
    selected_scope = _load_json(repo_root / selected_scope_path)
    policy = _load_yaml(repo_root / policy_path)
    plans = [_load_json(repo_root / path) for path in plan_paths]
    if len(plans) < 2:
        raise ValueError("minimum_two_candidate_plans_required")
    scope_packet_id = str(selected_scope.get("packet_id", "")).strip()
    if not scope_packet_id:
        raise ValueError("selected_scope_missing_packet_id")

    run_id = _run_id()
    comparison_id = f"{run_id}:cmp"
    output_dir = repo_root / output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_list = sorted({ref for ref in (evidence_refs or []) if ref})

    comparison_packet = {
        "packet_type": "candidate_plan_comparison_packet",
        "packet_version": "v1",
        "comparison_id": comparison_id,
        "selected_solution_scope_ref": scope_packet_id,
        "candidate_plan_refs": [_plan_ref(repo_root, repo_root / path) for path in plan_paths],
        "plan_quality_policy_ref": _plan_ref(repo_root, repo_root / policy_path),
        "evidence_packet_refs": evidence_list,
    }
    comparison_packet_path = write_json(output_dir / "candidate-plan-comparison.packet.json", comparison_packet)

    score_packets: list[dict[str, Any]] = []
    disqualified_plan_refs: list[str] = []
    qualified_packets: list[dict[str, Any]] = []

    for raw_path, plan in zip(plan_paths, plans, strict=True):
        plan_ref = _plan_ref(repo_root, repo_root / raw_path)
        gate_results = _gate_results(plan, selected_scope)
        qualified = all(bool(item.get("passed", False)) for item in gate_results)
        metric_values = _metric_map(plan, evidence_list)
        primary_scores, secondary_scores, aggregate_score = _aggregate_score(metric_values, policy)
        anti_cheat = _anti_cheat_flags(plan)
        explanation = [
            f"plan_readiness={str(plan.get('plan_readiness', 'candidate')).strip() or 'candidate'}",
            f"node_count={len(_node_index(plan))}",
            f"aggregate_score={aggregate_score}",
        ]
        packet = {
            "packet_type": "plan_quality_score_packet",
            "packet_version": "v1",
            "comparison_id": comparison_id,
            "candidate_plan_ref": plan_ref,
            "hard_gate_results": gate_results,
            "qualified_for_ranking": qualified,
            "primary_metric_scores": primary_scores,
            "secondary_metric_scores": secondary_scores,
            "aggregate_score": aggregate_score if qualified else 0.0,
            "evidence_adjustments": [{"source": ref, "applied": True} for ref in evidence_list],
            "anti_cheat_flags": anti_cheat,
            "explanation": explanation,
        }
        score_packets.append(packet)
        if qualified:
            qualified_packets.append(packet)
        else:
            disqualified_plan_refs.append(plan_ref)

    score_packets.sort(
        key=lambda item: (
            bool(item.get("qualified_for_ranking", False)),
            float(item.get("aggregate_score", 0.0)),
            str(item.get("candidate_plan_ref", "")),
        ),
        reverse=True,
    )
    for index, packet in enumerate(score_packets, start=1):
        write_json(output_dir / f"plan-quality-score-{index:02d}.packet.json", packet)

    qualified_packets.sort(
        key=lambda item: (
            float(item.get("aggregate_score", 0.0)),
            float(item.get("primary_metric_scores", {}).get("BDS", 0.0)),
            float(item.get("primary_metric_scores", {}).get("VCS", 0.0)),
            float(item.get("primary_metric_scores", {}).get("DES", 0.0)),
            str(item.get("candidate_plan_ref", "")),
        ),
        reverse=True,
    )
    recommended_plan_ref = str(qualified_packets[0]["candidate_plan_ref"]) if qualified_packets else ""
    ranked_packet = {
        "packet_type": "ranked_plan_packet",
        "packet_version": "v1",
        "comparison_id": comparison_id,
        "selected_solution_scope_ref": scope_packet_id,
        "ranked_plan_refs": [str(packet.get("candidate_plan_ref", "")) for packet in qualified_packets],
        "recommended_plan_ref": recommended_plan_ref,
        "recommendation_reason": (
            "highest aggregate score among plans passing hard gates" if recommended_plan_ref else "no plan passed hard gates"
        ),
        "tradeoff_summary": [
            "hard-gate failures disqualify plans before ranking",
            "aggregate score is policy-weighted and evidence-aware",
            "anti-cheat flags are advisory and should be reviewed explicitly",
        ],
        "disqualified_plan_refs": disqualified_plan_refs,
        "evidence_packet_refs": evidence_list,
    }
    ranked_packet_path = write_json(output_dir / "ranked-plan.packet.json", ranked_packet)

    report = {
        "command": COMMAND,
        "run_id": run_id,
        "comparison_id": comparison_id,
        "status": "ok" if qualified_packets else "blocked",
        "selected_solution_scope_ref": scope_packet_id,
        "candidate_plan_count": len(plans),
        "qualified_plan_count": len(qualified_packets),
        "disqualified_plan_count": len(disqualified_plan_refs),
        "recommended_plan_ref": recommended_plan_ref,
        "comparison_packet_path": comparison_packet_path.as_posix(),
        "ranked_packet_path": ranked_packet_path.as_posix(),
        "score_packet_paths": [
            (output_dir / f"plan-quality-score-{index:02d}.packet.json").as_posix()
            for index, _ in enumerate(score_packets, start=1)
        ],
        "output_root": output_dir.as_posix(),
        "policy_ref": _plan_ref(repo_root, repo_root / policy_path),
        "blockers": [] if qualified_packets else ["no_plans_passed_hard_gates"],
        "ok": bool(qualified_packets),
    }
    write_json(output_dir / "plan-quality-score.report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selected-scope", required=True)
    parser.add_argument("--plan", action="append", dest="plans", required=True)
    parser.add_argument("--policy", default=DEFAULT_POLICY_PATH.as_posix())
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        report = compare_plans(
            root=args.root,
            selected_scope_path=args.selected_scope,
            plan_paths=args.plans,
            policy_path=args.policy,
            evidence_refs=args.evidence_ref,
            output_root=args.output_root,
        )
        code = 0 if report.get("ok") else 1
    except (FileNotFoundError, PermissionError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        report = {
            "command": COMMAND,
            "status": "blocked",
            "blockers": [f"{exc.__class__.__name__}:{exc}"],
            "ok": False,
        }
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
