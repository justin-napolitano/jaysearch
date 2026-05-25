from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.design_iteration import run_design_iteration
from platform_tools.governance_execution_intake import validate_execution_intake
from platform_tools.plan_quality_score import compare_plans
from platform_tools.public_orchestration_api import envelope
from platform_tools.review_evidence_adapter import assemble_review_evidence_packet
from platform_tools.research_questions import write_json


COMMAND = "orchestrate-design-review"
DEFAULT_OUTPUT_ROOT = Path("artifacts/orchestration/design-review-runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("odr-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _packet_ref(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _discover_paths(root: Path, patterns: list[str]) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()
    if not root.exists():
        return matches
    for pattern in patterns:
        for path in root.rglob(pattern):
            if not path.is_file():
                continue
            ref = path.as_posix()
            if ref in seen:
                continue
            seen.add(ref)
            matches.append(ref)
    return sorted(matches)


def _tool_call_request(
    *,
    run_id: str,
    call_id: str,
    requester: str,
    target_tool: str,
    operation_name: str,
    input_packet_refs: list[str],
    policy_ref: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "packet_type": "tool_call_request_packet",
        "packet_version": "v1",
        "packet_id": f"{run_id}:{call_id}:request",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "call_id": call_id,
        "run_id": run_id,
        "requester": requester,
        "target_tool": target_tool,
        "operation_name": operation_name,
        "input_packet_refs": input_packet_refs,
        "policy_ref": policy_ref,
        "reason": reason,
    }


def _tool_call_result(
    *,
    run_id: str,
    call_id: str,
    target_tool: str,
    operation_name: str,
    outcome: str,
    output_packet_refs: list[str],
    event_refs: list[str],
    warnings: list[str] | None = None,
    failure_ref: str = "",
) -> dict[str, Any]:
    payload = {
        "packet_type": "tool_call_result_packet",
        "packet_version": "v1",
        "packet_id": f"{run_id}:{call_id}:result",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "call_id": call_id,
        "run_id": run_id,
        "target_tool": target_tool,
        "operation_name": operation_name,
        "outcome": outcome,
        "output_packet_refs": output_packet_refs,
        "event_refs": event_refs,
        "warnings": sorted({item for item in (warnings or []) if item}),
    }
    if failure_ref:
        payload["failure_ref"] = failure_ref
    return payload


def _plan_quality_score_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    metadata = node.get("call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    selected_scope_path = str(metadata.get("selected_scope_path", "")).strip()
    plan_paths = [str(item).strip() for item in metadata.get("plan_paths", []) if str(item).strip()]
    policy_path = str(metadata.get("plan_quality_policy_path", "spec/plan-quality-scoring.yaml")).strip()
    evidence_refs = [str(item).strip() for item in metadata.get("evidence_refs", []) if str(item).strip()]
    if not selected_scope_path or len(plan_paths) < 2:
        return False, {"blockers": ["plan_quality_score_inputs_incomplete"]}, []
    report = compare_plans(
        root=repo_root.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=plan_paths,
        policy_path=policy_path,
        evidence_refs=evidence_refs,
        output_root=output_root,
    )
    output_packet_refs = [
        str(item).strip()
        for item in [
            report.get("comparison_packet_path", ""),
            report.get("ranked_plan_packet_path", ""),
            *report.get("score_packet_paths", []),
        ]
        if str(item).strip()
    ]
    return report.get("ok") is True, report, output_packet_refs


def _governance_intake_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    metadata = node.get("call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    execution_ready_plan_path = str(metadata.get("execution_ready_plan_path", "")).strip()
    execution_packet_paths = [
        str(item).strip() for item in metadata.get("execution_packet_paths", []) if str(item).strip()
    ]
    if not execution_ready_plan_path or not execution_packet_paths:
        return False, {"blockers": ["governance_intake_inputs_incomplete"]}, []
    code, report = validate_execution_intake(
        root=repo_root.as_posix(),
        execution_ready_plan_path=execution_ready_plan_path,
        execution_packet_paths=execution_packet_paths,
        output_root=output_root,
    )
    output_packet_refs = [str(report.get("decision_packet_path", "")).strip()] if str(report.get("decision_packet_path", "")).strip() else []
    return code == 0 and report.get("ok") is True, report, output_packet_refs


def _evidence_adapter_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    metadata = node.get("call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    request_path = str(metadata.get("request_path", "")).strip()
    if not request_path:
        return False, {"blockers": ["evidence_adapter_inputs_incomplete"]}, []
    code, report = assemble_review_evidence_packet(
        root=repo_root.as_posix(),
        request_path=request_path,
        output_root=output_root,
    )
    output_packet_refs = [str(report.get("evidence_packet_path", "")).strip()] if str(report.get("evidence_packet_path", "")).strip() else []
    return code == 0 and report.get("ok") is True, report, output_packet_refs


def _self_loop_review_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    metadata = node.get("call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    design_iteration_root = str(metadata.get("design_iteration_root", repo_root.as_posix())).strip() or repo_root.as_posix()
    dag_path = str(
        metadata.get("dag_path", "artifacts/planner/research/design-review-automation-v1-dag.json")
    ).strip() or "artifacts/planner/research/design-review-automation-v1-dag.json"
    registry_path = str(metadata.get("registry_path", "spec/contracts/packet-schema-registry.yaml")).strip() or "spec/contracts/packet-schema-registry.yaml"
    checkset_path = str(metadata.get("checkset_path", "spec/contracts/design-iteration-checks.yaml")).strip() or "spec/contracts/design-iteration-checks.yaml"
    plan_quality_scoring_path = str(metadata.get("plan_quality_scoring_path", "spec/plan-quality-scoring.yaml")).strip() or "spec/plan-quality-scoring.yaml"
    code, report = run_design_iteration(
        root=design_iteration_root,
        registry_path=registry_path,
        checkset_path=checkset_path,
        dag_path=dag_path,
        output_root=output_root,
        plan_quality_scoring_path=plan_quality_scoring_path,
    )
    output_packet_refs = [
        str(item).strip()
        for item in [
            report.get("findings_packet_path", ""),
            report.get("gaps_packet_path", ""),
            report.get("question_candidates_path", ""),
        ]
        if str(item).strip()
    ]
    return code == 0 and report.get("ok") is True, report, output_packet_refs


def _question_research_handoff_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    metadata = node.get("call_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    review_surface_root = Path(str(metadata.get("review_surface_root", repo_root.as_posix())).strip() or repo_root.as_posix())
    registry_path = review_surface_root / str(
        metadata.get("registry_path", "spec/contracts/packet-schema-registry.yaml")
    ).strip()
    question_doc_path = review_surface_root / str(metadata.get("question_doc_path", "docs/question-tool-v1.md")).strip()
    evidence_doc_path = review_surface_root / str(metadata.get("evidence_doc_path", "docs/evidence-search-tool-v1.md")).strip()
    research_doc_path = review_surface_root / str(metadata.get("research_doc_path", "docs/research-tool-v1.md")).strip()

    registry = _load_json(registry_path) if registry_path.suffix == ".json" else None
    if registry is None:
        import yaml
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    contract_families = registry.get("contract_families", [])
    if not isinstance(contract_families, list):
        contract_families = []
    available_contracts = {
        str(item.get("contract_name", "")).strip()
        for item in contract_families
        if isinstance(item, dict) and str(item.get("contract_name", "")).strip()
    }

    question_text = _read_text(question_doc_path).lower()
    evidence_text = _read_text(evidence_doc_path).lower()
    research_text = _read_text(research_doc_path).lower()

    blockers: list[str] = []
    warnings: list[str] = []

    required_contracts = {
        "research_question_packet",
        "evidence_packet",
        "research_problem_packet",
        "question_to_research_problem_transform",
    }
    for contract_name in sorted(required_contracts - available_contracts):
        blockers.append(f"missing_handoff_contract:{contract_name}")

    if "decision_target" not in question_text or "blocked_work_if_unanswered" not in question_text:
        blockers.append("question_packet_decision_contract_underspecified")
    if "assemble_evidence_packet" not in evidence_text or "evidence packet" not in evidence_text:
        blockers.append("evidence_packet_assembly_boundary_missing")
    if "question_to_research_problem_transform" not in research_text and "evidence-search-tool" not in research_text:
        blockers.append("research_handoff_boundary_underspecified")
    if "websites" in evidence_text:
        warnings.append("evidence_scope_includes_websites")

    packet_example_patterns = {
        "research_question_packet": ["*research-question*.json", "*research_question*.json"],
        "evidence_packet": ["*evidence*.json"],
        "research_problem_packet": ["*research-problem*.json", "*research_problem*.json"],
    }
    discovered_examples: dict[str, list[str]] = {}
    artifacts_root = review_surface_root / "artifacts"
    for contract_name, patterns in packet_example_patterns.items():
        discovered_examples[contract_name] = _discover_paths(artifacts_root, patterns)

    if not discovered_examples["research_question_packet"]:
        blockers.append("research_question_packet_example_missing")
    if not discovered_examples["evidence_packet"]:
        blockers.append("evidence_packet_example_missing")
    if not discovered_examples["research_problem_packet"]:
        blockers.append("research_problem_packet_example_missing")

    transform_surface_matches = [
        ref
        for ref in _discover_paths(
            review_surface_root,
            [
                "*question-to-research-problem*",
                "*question_to_research_problem*",
                "*research-problem-transform*",
            ],
        )
        if not ref.endswith("question-research-handoff-review.packet.json")
        and not ref.endswith("question-research-handoff-review.report.json")
    ]
    if not transform_surface_matches:
        blockers.append("question_to_research_problem_transform_surface_missing")

    run_id = _run_id().replace("odr-", "qrh-")
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    report_packet = {
        "packet_type": "question_research_handoff_review_packet",
        "packet_version": "v1",
        "packet_id": f"{run_id}:handoff-review",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "review_type": "question_research_handoff_review",
        "checked_contracts": sorted(required_contracts),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "discovered_packet_examples": discovered_examples,
        "discovered_transform_surfaces": transform_surface_matches,
        "artifact_refs": [
            _packet_ref(repo_root, question_doc_path),
            _packet_ref(repo_root, evidence_doc_path),
            _packet_ref(repo_root, research_doc_path),
            _packet_ref(repo_root, registry_path),
            *[ref for refs in discovered_examples.values() for ref in refs],
            *transform_surface_matches,
        ],
    }
    report_path = write_json(run_root / "question-research-handoff-review.packet.json", report_packet)
    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "report_packet_path": report_path.as_posix(),
            "blockers": sorted(set(blockers)),
            "warnings": sorted(set(warnings)),
        },
    )
    write_json(run_root / "question-research-handoff-review.report.json", report)
    return not blockers, report, [report_path.as_posix()]


def _dispatch_review_node(
    *,
    repo_root: Path,
    output_root: str,
    node: dict[str, Any],
) -> tuple[bool, dict[str, Any], list[str]]:
    target_tool = str(node.get("target_tool", "")).strip()
    operation_name = str(node.get("operation_name", "")).strip()
    if target_tool == "plan-quality-score" and operation_name == "compare_plans":
        return _plan_quality_score_node(repo_root=repo_root, output_root=output_root, node=node)
    if target_tool == "governance-tool" and operation_name == "validate_execution_intake":
        return _governance_intake_node(repo_root=repo_root, output_root=output_root, node=node)
    if target_tool == "evidence-search-tool" and operation_name == "assemble_evidence_packet":
        return _evidence_adapter_node(repo_root=repo_root, output_root=output_root, node=node)
    if target_tool == "design-iteration-tool" and operation_name == "run_design_iteration":
        return _self_loop_review_node(repo_root=repo_root, output_root=output_root, node=node)
    if target_tool == "design-iteration-tool" and operation_name == "review_question_research_handoff":
        return _question_research_handoff_node(repo_root=repo_root, output_root=output_root, node=node)
    return False, {"blockers": [f"unsupported_review_node:{target_tool}:{operation_name}"]}, []


def materialize_review_program(
    *,
    root: str = ".",
    request_path: str,
    design_iteration_root: str | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    request = _load_json(repo_root / request_path)
    run_id = _run_id().replace("odr-", "drp-")
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    review_id = str(request.get("review_id", "")).strip() or run_id
    requested_modes = _string_list(request.get("requested_review_modes", []))
    review_inputs = request.get("review_inputs", {})
    if not isinstance(review_inputs, dict):
        review_inputs = {}

    review_nodes: list[dict[str, Any]] = []
    blockers: list[str] = []

    if "planning_quality_review" in requested_modes:
        selected_scope_path = str(review_inputs.get("selected_scope_path", "")).strip()
        plan_paths = _string_list(review_inputs.get("plan_paths", []))
        if not selected_scope_path or len(plan_paths) < 2:
            blockers.append("planning_quality_review_inputs_incomplete")
        else:
            review_nodes.append(
                {
                    "node_id": "review-plan-quality",
                    "review_mode": "planning_quality_review",
                    "target_tool": "plan-quality-score",
                    "operation_name": "compare_plans",
                    "input_packet_refs": [selected_scope_path, *plan_paths],
                    "policy_ref": str(
                        review_inputs.get("plan_quality_policy_path", "spec/plan-quality-scoring.yaml")
                    ).strip()
                    or "spec/plan-quality-scoring.yaml",
                    "reason": "Compare candidate structural plans during design review.",
                    "call_metadata": {
                        "selected_scope_path": selected_scope_path,
                        "plan_paths": plan_paths,
                        "plan_quality_policy_path": str(
                            review_inputs.get("plan_quality_policy_path", "spec/plan-quality-scoring.yaml")
                        ).strip()
                        or "spec/plan-quality-scoring.yaml",
                        "evidence_refs": _string_list(review_inputs.get("evidence_refs", [])),
                    },
                }
            )

    if "evidence_backed_claim_review" in requested_modes:
        review_nodes.append(
            {
                "node_id": "review-evidence-basis",
                "review_mode": "evidence_backed_claim_review",
                "target_tool": "evidence-search-tool",
                "operation_name": "assemble_evidence_packet",
                "input_packet_refs": [request_path],
                "policy_ref": "bounded-review-evidence-policy-v1",
                "reason": "Assemble bounded evidence packet for explicit design-review claims.",
                "call_metadata": {
                    "request_path": request_path,
                },
            }
        )

    if "governance_handoff_review" in requested_modes:
        execution_ready_plan_path = str(review_inputs.get("execution_ready_plan_path", "")).strip()
        execution_packet_paths = _string_list(review_inputs.get("execution_packet_paths", []))
        if not execution_ready_plan_path or not execution_packet_paths:
            blockers.append("governance_handoff_review_inputs_incomplete")
        else:
            review_nodes.append(
                {
                    "node_id": "review-governance-handoff",
                    "review_mode": "governance_handoff_review",
                    "target_tool": "governance-tool",
                    "operation_name": "validate_execution_intake",
                    "input_packet_refs": [execution_ready_plan_path, *execution_packet_paths],
                    "policy_ref": "governance-intake-policy-v1",
                    "reason": "Verify governance intake compatibility during design review.",
                    "call_metadata": {
                        "execution_ready_plan_path": execution_ready_plan_path,
                        "execution_packet_paths": execution_packet_paths,
                    },
                }
            )

    if "self_loop_review" in requested_modes:
        review_nodes.append(
            {
                "node_id": "review-self-loop",
                "review_mode": "self_loop_review",
                "target_tool": "design-iteration-tool",
                "operation_name": "run_design_iteration",
                "input_packet_refs": [
                    "artifacts/planner/research/design-review-automation-v1-dag.json",
                    "spec/contracts/packet-schema-registry.yaml",
                    "spec/contracts/design-iteration-checks.yaml",
                ],
                    "policy_ref": "bounded-self-loop-review-policy-v1",
                    "reason": "Review the design-review automation loop artifacts with the design-iteration tool itself.",
                    "call_metadata": {
                        "design_iteration_root": design_iteration_root or root,
                        "dag_path": "artifacts/planner/research/design-review-automation-v1-dag.json",
                        "registry_path": "spec/contracts/packet-schema-registry.yaml",
                        "checkset_path": "spec/contracts/design-iteration-checks.yaml",
                        "plan_quality_scoring_path": "spec/plan-quality-scoring.yaml",
                    },
                }
            )

    if "question_research_handoff_review" in requested_modes:
        review_nodes.append(
            {
                "node_id": "review-question-research-handoff",
                "review_mode": "question_research_handoff_review",
                "target_tool": "design-iteration-tool",
                "operation_name": "review_question_research_handoff",
                "input_packet_refs": [
                    "docs/question-tool-v1.md",
                    "docs/evidence-search-tool-v1.md",
                    "docs/research-tool-v1.md",
                    "spec/contracts/packet-schema-registry.yaml",
                ],
                "policy_ref": "bounded-question-research-handoff-review-policy-v1",
                "reason": "Review whether the question-to-evidence-to-research handoff is sufficiently specified to build against.",
                "call_metadata": {
                    "registry_path": "spec/contracts/packet-schema-registry.yaml",
                    "question_doc_path": "docs/question-tool-v1.md",
                    "evidence_doc_path": "docs/evidence-search-tool-v1.md",
                    "research_doc_path": "docs/research-tool-v1.md",
                    "review_surface_root": design_iteration_root or root,
                },
            }
        )

    program_packet = {
        "packet_type": "design_review_program_packet",
        "packet_version": "v1",
        "packet_id": f"{review_id}:program",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "review_id": review_id,
        "review_request_ref": request_path,
        "review_nodes": review_nodes,
        "stop_conditions": {
            "max_tool_calls": max(len(review_nodes), 1),
            "max_blocking_findings": 5,
            "no_new_material_findings": True,
        },
    }
    program_path = write_json(run_root / "design-review-program.packet.json", program_packet)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "review_id": review_id,
            "request_path": str((repo_root / request_path).resolve()),
            "program_path": program_path.as_posix(),
            "review_node_count": len(review_nodes),
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "materialize-design-review-program.report.json", report)
    return (0 if not blockers else 1), report


def execute_review_program(
    *,
    root: str = ".",
    program_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    program = _load_json(repo_root / program_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    review_nodes = program.get("review_nodes", [])
    if not isinstance(review_nodes, list):
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": ["review_nodes_missing"], "program_path": str((repo_root / program_path).resolve())},
        )
        write_json(run_root / "orchestrate-design-review.report.json", report)
        return 1, report

    request_packets: list[str] = []
    result_packets: list[str] = []
    step_reports: list[dict[str, Any]] = []
    blockers: list[str] = []

    for index, raw_node in enumerate(review_nodes, start=1):
        if not isinstance(raw_node, dict):
            blockers.append(f"review_node_invalid:{index}")
            continue
        node_id = str(raw_node.get("node_id", "")).strip() or f"review-node-{index:03d}"
        target_tool = str(raw_node.get("target_tool", "")).strip()
        operation_name = str(raw_node.get("operation_name", "")).strip()
        call_id = f"{run_id}:{node_id}"
        request_packet = _tool_call_request(
            run_id=run_id,
            call_id=call_id,
            requester="design-iteration-tool",
            target_tool=target_tool,
            operation_name=operation_name,
            input_packet_refs=[str(item).strip() for item in raw_node.get("input_packet_refs", []) if str(item).strip()],
            policy_ref=str(raw_node.get("policy_ref", "bounded-review-policy")).strip() or "bounded-review-policy",
            reason=str(raw_node.get("reason", "design review requested bounded tool call")).strip()
            or "design review requested bounded tool call",
        )
        request_path = write_json(run_root / f"{node_id}.tool-call-request.packet.json", request_packet)
        request_packets.append(_packet_ref(repo_root, request_path))

        ok, tool_report, output_packet_refs = _dispatch_review_node(
            repo_root=repo_root,
            output_root=output_root,
            node=raw_node,
        )
        result_packet = _tool_call_result(
            run_id=run_id,
            call_id=call_id,
            target_tool=target_tool,
            operation_name=operation_name,
            outcome="ok" if ok else "blocked",
            output_packet_refs=output_packet_refs,
            event_refs=[],
            warnings=[
                str(item).strip()
                for item in tool_report.get("warnings", [])
                if str(item).strip()
            ],
            failure_ref="" if ok else ",".join(str(item).strip() for item in tool_report.get("blockers", []) if str(item).strip()),
        )
        result_path = write_json(run_root / f"{node_id}.tool-call-result.packet.json", result_packet)
        result_packets.append(_packet_ref(repo_root, result_path))

        step_reports.append(
            {
                "node_id": node_id,
                "target_tool": target_tool,
                "operation_name": operation_name,
                "status": "ok" if ok else "blocked",
                "ok": ok,
                "request_packet_path": _packet_ref(repo_root, request_path),
                "result_packet_path": _packet_ref(repo_root, result_path),
                "report": tool_report,
            }
        )
        if not ok:
            blockers.extend(str(item).strip() for item in tool_report.get("blockers", []) if str(item).strip())

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "program_path": str((repo_root / program_path).resolve()),
            "request_packet_paths": request_packets,
            "result_packet_paths": result_packets,
            "step_reports": step_reports,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "orchestrate-design-review.report.json", report)
    return (0 if not blockers else 1), report


def run_design_review_workflow(
    *,
    root: str = ".",
    request_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    design_iteration_root: str | None = None,
    design_iteration_output_root: str = "artifacts/design-iteration/runs",
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_root = repo_root / output_root
    run_root.mkdir(parents=True, exist_ok=True)
    step_reports: list[dict[str, Any]] = []

    program_code, program_report = materialize_review_program(
        root=root,
        request_path=request_path,
        design_iteration_root=design_iteration_root,
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "materialize_design_review_program",
            "status": str(program_report.get("status", "")).strip(),
            "ok": program_report.get("ok") is True,
            "report": program_report,
        }
    )
    if program_code != 0 or program_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "request_path": request_path,
                "step_reports": step_reports,
                "blockers": program_report.get("blockers", []),
            },
        )
        write_json(run_root / "design-review-workflow.report.json", report)
        return 1, report

    execute_code, execute_report = execute_review_program(
        root=root,
        program_path=_packet_ref(repo_root, Path(str(program_report.get("program_path", "")).strip())),
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "execute_review_program",
            "status": str(execute_report.get("status", "")).strip(),
            "ok": execute_report.get("ok") is True,
            "report": execute_report,
        }
    )
    if execute_code != 0 or execute_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "request_path": request_path,
                "program_path": program_report.get("program_path", ""),
                "step_reports": step_reports,
                "blockers": execute_report.get("blockers", []),
            },
        )
        write_json(run_root / "design-review-workflow.report.json", report)
        return 1, report

    review_code, review_report = run_design_iteration(
        root=design_iteration_root or root,
        output_root=design_iteration_output_root,
    )
    step_reports.append(
        {
            "step": "design_iteration_review",
            "status": str(review_report.get("status", "")).strip(),
            "ok": review_report.get("ok") is True,
            "report": review_report,
        }
    )

    blockers: list[str] = []
    if review_code != 0 or review_report.get("ok") is not True:
        blockers.extend(str(item).strip() for item in review_report.get("blockers", []) if str(item).strip())

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "request_path": request_path,
            "program_path": program_report.get("program_path", ""),
            "tool_call_result_paths": execute_report.get("result_packet_paths", []),
            "design_findings_packet_path": review_report.get("findings_packet_path", ""),
            "design_gaps_packet_path": review_report.get("gaps_packet_path", ""),
            "next_question_candidates_path": review_report.get("question_candidates_path", ""),
            "step_reports": step_reports,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "design-review-workflow.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--program")
    parser.add_argument("--request")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--design-iteration-root", default=None)
    parser.add_argument("--design-iteration-output-root", default="artifacts/design-iteration/runs")
    args = parser.parse_args()
    try:
        if bool(args.program) == bool(args.request):
            raise ValueError("exactly_one_of_program_or_request_required")
        if args.request:
            code, report = run_design_review_workflow(
                root=args.root,
                request_path=args.request,
                output_root=args.output_root,
                design_iteration_root=args.design_iteration_root,
                design_iteration_output_root=args.design_iteration_output_root,
            )
        else:
            code, report = execute_review_program(
                root=args.root,
                program_path=args.program,
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
