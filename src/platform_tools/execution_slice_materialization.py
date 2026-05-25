from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.research_questions import write_json


COMMAND = "execution-slice-materialization"
DEFAULT_POLICY_PATH = Path("spec/execution-materialization-policy.yaml")
DEFAULT_OUTPUT_ROOT = Path("artifacts/execution-slice-materialization/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("esm-%Y%m%dT%H%M%SZ")


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


def _repo_ref(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


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
    return [edge for edge in plan.get("edges", []) if isinstance(edge, dict)]


def _dependency_map(plan: dict[str, Any]) -> dict[str, list[str]]:
    nodes = _node_index(plan)
    dep_map: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in _edge_list(plan):
        relation = str(edge.get("relation", "")).strip()
        if relation not in {"depends_on", "gated_by"}:
            continue
        from_node = str(edge.get("from_node_id", "")).strip()
        to_node = str(edge.get("to_node_id", "")).strip()
        if from_node in dep_map and to_node in dep_map:
            dep_map[from_node].append(to_node)
    return dep_map


def _cycle_exists(plan: dict[str, Any]) -> bool:
    deps = _dependency_map(plan)
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        for parent in deps.get(node_id, []):
            if dfs(parent):
                return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    return any(dfs(node_id) for node_id in deps)


def _validate_inputs(
    *,
    selected_scope: dict[str, Any],
    structural_plan: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    scope_packet_id = str(selected_scope.get("packet_id", "")).strip()
    plan_scope_ref = str(structural_plan.get("selected_solution_scope_ref", "")).strip()
    plan_readiness = str(structural_plan.get("plan_readiness", "candidate")).strip() or "candidate"
    nodes = _node_index(structural_plan)

    if not scope_packet_id:
        blockers.append("selected_scope_missing_packet_id")
    if scope_packet_id != plan_scope_ref:
        blockers.append("selected_scope_ref_mismatch")
    if plan_readiness != "candidate":
        blockers.append("chosen_plan_not_structural_candidate")
    if not nodes:
        blockers.append("structural_plan_missing_nodes")
    if _cycle_exists(structural_plan):
        blockers.append("structural_plan_has_cycle")
    required_policy = {"policy_id", "grouping_rules", "warning_rules", "hard_fail_rules", "outputs"}
    if not required_policy.issubset(policy):
        blockers.append("materialization_policy_incomplete")
    for node_id, node in nodes.items():
        if not str(node.get("title", "")).strip():
            blockers.append(f"node_missing_title:{node_id}")
        if not isinstance(node.get("expected_outputs"), list) or not node.get("expected_outputs"):
            blockers.append(f"node_missing_expected_outputs:{node_id}")
        if not isinstance(node.get("validation_targets"), list) or not node.get("validation_targets"):
            blockers.append(f"node_missing_validation_targets:{node_id}")
        if not isinstance(node.get("completion_evidence_requirements"), list) or not node.get(
            "completion_evidence_requirements"
        ):
            blockers.append(f"node_missing_completion_evidence:{node_id}")
    return sorted(blockers)


def _materialize(
    *,
    selected_scope: dict[str, Any],
    structural_plan: dict[str, Any],
    policy: dict[str, Any],
    repo_root: Path,
    chosen_plan_ref: str,
    evidence_refs: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    plan_id = str(structural_plan.get("plan_id", "")).strip()
    scope_packet_id = str(selected_scope.get("packet_id", "")).strip()
    nodes = _node_index(structural_plan)
    deps = _dependency_map(structural_plan)
    warnings: list[str] = []
    execution_packets: list[dict[str, Any]] = []
    execution_slices: list[dict[str, Any]] = []
    approval_rules = policy.get("approval_rules", {})
    if not isinstance(approval_rules, dict):
        approval_rules = {}
    default_required_approvals = approval_rules.get("default_required_approvals", [])
    if not isinstance(default_required_approvals, list):
        default_required_approvals = []
    domain_required_approvals = approval_rules.get("domain_required_approvals", {})
    if not isinstance(domain_required_approvals, dict):
        domain_required_approvals = {}

    for node_id, node in nodes.items():
        source_node_refs = [node_id]
        expected_outputs = [str(item).strip() for item in node.get("expected_outputs", []) if str(item).strip()]
        validation_targets = [
            str(item).strip() for item in node.get("validation_targets", []) if str(item).strip()
        ]
        evidence_requirements = [
            str(item).strip()
            for item in node.get("completion_evidence_requirements", [])
            if str(item).strip()
        ]
        blocking_dependencies = [f"exec:{dep}" for dep in deps.get(node_id, [])]
        conflict_domains = [str(item).strip() for item in node.get("conflict_domains", []) if str(item).strip()]
        required_inputs = [f"output:{dep}" for dep in deps.get(node_id, [])]
        if not required_inputs:
            required_inputs = [f"scope:{scope_packet_id}"]
        runnable_preconditions = [f"selected_scope:{scope_packet_id}"]
        runnable_preconditions.extend(f"dependency_complete:{dep}" for dep in deps.get(node_id, []))

        if not conflict_domains:
            owned_changes = [str(item).strip() for item in node.get("owned_changes", []) if str(item).strip()]
            if owned_changes:
                conflict_domains = [f"owned:{item}" for item in owned_changes]
            else:
                warnings.append(f"slice_missing_conflict_domains:{node_id}")

        required_approvals: list[str] = [str(item).strip() for item in default_required_approvals if str(item).strip()]
        for domain in conflict_domains:
            domain_rules = domain_required_approvals.get(domain, [])
            if not isinstance(domain_rules, list):
                continue
            required_approvals.extend(str(item).strip() for item in domain_rules if str(item).strip())
        required_approvals = sorted(set(item for item in required_approvals if item))

        execution_id = f"exec:{node_id}"
        execution_slice = {
            "execution_id": execution_id,
            "source_plan_id": plan_id,
            "source_node_refs": source_node_refs,
            "required_inputs": required_inputs,
            "expected_outputs": expected_outputs,
            "validation_targets": validation_targets,
            "blocking_dependencies": blocking_dependencies,
            "conflict_domains": conflict_domains,
            "required_approvals": required_approvals,
            "runnable_preconditions": runnable_preconditions,
            "completion_evidence_requirements": evidence_requirements,
        }
        execution_slices.append(execution_slice)
        execution_packets.append(
            {
                "packet_type": "execution_packet",
                "packet_version": "v1",
                "packet_id": execution_id,
                "created_at": _utc_now(),
                "producer": COMMAND,
                "execution_id": execution_id,
                "node_id": node_id,
                "work_item_id": node_id,
                "graph_id": str(structural_plan.get("graph_id", "")).strip(),
                "task_summary": str(node.get("title", "")).strip(),
                "required_inputs": required_inputs,
                "expected_outputs": expected_outputs,
                "validation_targets": validation_targets,
                "blocking_dependencies": blocking_dependencies,
                "declared_ready_inputs": required_inputs,
                "conflict_domains": conflict_domains,
                "required_approvals": required_approvals,
                "completion_evidence_requirements": evidence_requirements,
                "runnable_preconditions": runnable_preconditions,
                "source_structural_plan_ref": chosen_plan_ref,
            }
        )

    execution_ready_plan = {
        "packet_type": "execution_ready_plan_packet",
        "packet_version": "v1",
        "packet_id": f"{plan_id}:execution-ready",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "plan_id": plan_id,
        "selected_solution_scope_ref": scope_packet_id,
        "source_structural_plan_ref": chosen_plan_ref,
        "plan_readiness": "execution_ready",
        "execution_slices": execution_slices,
        "materialization_policy_ref": _repo_ref(repo_root, repo_root / DEFAULT_POLICY_PATH),
        "materialization_warnings": sorted(set(warnings)),
        "evidence_refs": evidence_refs,
    }
    return execution_ready_plan, execution_packets, sorted(set(warnings))


def materialize_execution_slices(
    *,
    root: str = ".",
    selected_scope_path: str,
    chosen_plan_path: str,
    policy_path: str = DEFAULT_POLICY_PATH.as_posix(),
    evidence_refs: list[str] | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    selected_scope = _load_json(repo_root / selected_scope_path)
    structural_plan = _load_json(repo_root / chosen_plan_path)
    policy = _load_yaml(repo_root / policy_path)
    blockers = _validate_inputs(selected_scope=selected_scope, structural_plan=structural_plan, policy=policy)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    chosen_plan_ref = _repo_ref(repo_root, repo_root / chosen_plan_path)
    evidence_list = sorted({ref for ref in (evidence_refs or []) if ref})

    if blockers:
        report = {
            "command": COMMAND,
            "run_id": run_id,
            "status": "blocked",
            "blockers": blockers,
            "ok": False,
            "output_root": run_root.as_posix(),
        }
        write_json(run_root / "execution-slice-materialization.report.json", report)
        return 1, report

    execution_ready_plan, execution_packets, warnings = _materialize(
        selected_scope=selected_scope,
        structural_plan=structural_plan,
        policy=policy,
        repo_root=repo_root,
        chosen_plan_ref=chosen_plan_ref,
        evidence_refs=evidence_list,
    )

    plan_path = write_json(run_root / "execution-ready-plan.packet.json", execution_ready_plan)
    packet_paths: list[str] = []
    for index, packet in enumerate(execution_packets, start=1):
        packet_path = write_json(run_root / f"execution-packet-{index:02d}.packet.json", packet)
        packet_paths.append(packet_path.as_posix())

    report = {
        "command": COMMAND,
        "run_id": run_id,
        "status": "ok",
        "blockers": [],
        "ok": True,
        "selected_scope_ref": str(selected_scope.get("packet_id", "")).strip(),
        "chosen_structural_plan_ref": chosen_plan_ref,
        "execution_ready_plan_path": plan_path.as_posix(),
        "execution_packet_paths": packet_paths,
        "execution_slice_count": len(execution_packets),
        "materialization_warning_count": len(warnings),
        "materialization_warnings": warnings,
        "output_root": run_root.as_posix(),
    }
    write_json(run_root / "execution-slice-materialization.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selected-scope", required=True)
    parser.add_argument("--chosen-plan", required=True)
    parser.add_argument("--policy", default=DEFAULT_POLICY_PATH.as_posix())
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = materialize_execution_slices(
            root=args.root,
            selected_scope_path=args.selected_scope,
            chosen_plan_path=args.chosen_plan,
            policy_path=args.policy,
            evidence_refs=args.evidence_ref,
            output_root=args.output_root,
        )
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
