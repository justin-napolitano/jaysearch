from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.execution_slice_materialization import materialize_execution_slices
from platform_tools.orchestrate_design_review import execute_review_program
from platform_tools.orchestrate_design_review import run_design_review_workflow


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_selected_scope(root: Path) -> str:
    _write_json(
        root / "artifacts" / "selected-scope.packet.json",
        {
            "packet_type": "selected_solution_scope",
            "packet_version": "v1",
            "packet_id": "selected-scope-001",
            "created_at": "2026-05-20T00:00:00Z",
            "producer": "test",
            "problem_id": "prob-1",
            "selected_candidate_id": "cand-1",
            "selected_solution_summary": "Chosen solution",
            "scope_in": ["build tool"],
            "scope_out": ["rewrite governance"],
            "assumptions": ["local runtime"],
            "risks": ["scope drift"],
            "acceptance_targets": ["valid execution-ready plan"],
        },
    )
    return "artifacts/selected-scope.packet.json"


def _seed_plan(root: Path, *, scope_ref: str) -> str:
    _write_json(
        root / "plans" / "chosen-plan.json",
        {
            "plan_id": "plan-a",
            "selected_solution_scope_ref": scope_ref,
            "graph_id": "plan-a-graph",
            "plan_type": "implementation_plan",
            "plan_readiness": "candidate",
            "status": "ready",
            "purpose": "Candidate plan",
            "assumptions": ["bounded scope"],
            "risks": ["dependency drift"],
            "nodes": [
                {
                    "node_id": "n1",
                    "title": "Normalize inputs",
                    "node_type": "task",
                    "status": "ready",
                    "goal": "Normalize inputs",
                    "owned_changes": ["src/a.py"],
                    "conflict_domains": ["planning"],
                    "expected_outputs": ["normalized packet"],
                    "validation_targets": ["unit test"],
                    "completion_evidence_requirements": ["test report"],
                },
                {
                    "node_id": "n2",
                    "title": "Emit packets",
                    "node_type": "task",
                    "status": "ready",
                    "goal": "Emit packets",
                    "owned_changes": ["src/b.py"],
                    "conflict_domains": ["materialization"],
                    "expected_outputs": ["execution packet"],
                    "validation_targets": ["contract test"],
                    "completion_evidence_requirements": ["contract report"],
                },
            ],
            "edges": [
                {
                    "edge_id": "e1",
                    "from_node_id": "n2",
                    "to_node_id": "n1",
                    "relation": "depends_on",
                }
            ],
        },
    )
    return "plans/chosen-plan.json"


def _seed_program(root: Path, *, selected_scope_path: str, plan_path: str, execution_ready_plan_path: str, execution_packet_paths: list[str]) -> str:
    _write_json(
        root / "artifacts" / "design-review-program.packet.json",
        {
            "packet_type": "design_review_program_packet",
            "packet_version": "v1",
            "packet_id": "drp-001",
            "created_at": "2026-05-20T00:00:00Z",
            "producer": "test",
            "review_id": "review-001",
            "review_request_ref": "artifacts/design-review-request.packet.json",
            "review_nodes": [
                {
                    "node_id": "review-plan-quality",
                    "target_tool": "plan-quality-score",
                    "operation_name": "compare_plans",
                    "input_packet_refs": [selected_scope_path, plan_path, plan_path],
                    "policy_ref": str(Path("spec/plan-quality-scoring.yaml").resolve()),
                    "call_metadata": {
                        "selected_scope_path": selected_scope_path,
                        "plan_paths": [plan_path, plan_path],
                        "plan_quality_policy_path": str(Path("spec/plan-quality-scoring.yaml").resolve()),
                    },
                },
                {
                    "node_id": "review-governance",
                    "target_tool": "governance-tool",
                    "operation_name": "validate_execution_intake",
                    "input_packet_refs": [execution_ready_plan_path, *execution_packet_paths],
                    "policy_ref": "governance-intake-policy-v1",
                    "call_metadata": {
                        "execution_ready_plan_path": execution_ready_plan_path,
                        "execution_packet_paths": execution_packet_paths,
                    },
                },
            ],
            "stop_conditions": {
                "max_tool_calls": 4,
                "max_blocking_findings": 3,
            },
        },
    )
    return "artifacts/design-review-program.packet.json"


def _seed_request(root: Path, *, selected_scope_path: str, plan_path: str, execution_ready_plan_path: str, execution_packet_paths: list[str]) -> str:
    _write_json(
        root / "artifacts" / "design-review-request.packet.json",
        {
            "packet_type": "design_review_request_packet",
            "packet_version": "v1",
            "packet_id": "drr-001",
            "created_at": "2026-05-20T00:00:00Z",
            "producer": "test",
            "review_id": "review-001",
            "system_scope": "platform-template-bootstrap",
            "artifact_refs": [
                "docs/core-contract-spec-v1.md",
                "docs/design-review-automation-v1.md",
            ],
            "requested_review_modes": [
                "evidence_backed_claim_review",
                "planning_quality_review",
                "governance_handoff_review",
                "self_loop_review",
            ],
            "requested_outputs": [
                "design_findings_packet",
                "design_gap_packet[]",
                "next_question_candidate_packet[]",
            ],
            "review_inputs": {
                "evidence_problem_id": "design-review-claims",
                "source_records": [
                    {
                        "source_id": "critic-paper",
                        "title": "CRITIC",
                        "authors": ["Gou et al."],
                        "published_at": "2023-05-19",
                        "source_type": "paper",
                        "uri": "https://arxiv.org/abs/2305.11738",
                        "abstract": "Tool-interactive critique.",
                        "artifact_refs": ["https://arxiv.org/abs/2305.11738"],
                    }
                ],
                "claim_records": [
                    {
                        "claim_id": "claim-001",
                        "source_id": "critic-paper",
                        "claim_text": "Tool-interactive critique improves over unsupported introspection.",
                        "claim_type": "methodological",
                        "evidence_span_refs": ["abstract"],
                        "metric_refs": [],
                    }
                ],
                "method_refs": ["tool-assisted critique"],
                "benchmark_refs": ["design-review workflow"],
                "evidence_summary_text": "Bounded evidence packet for design review.",
                "selected_scope_path": selected_scope_path,
                "plan_paths": [plan_path, plan_path],
                "plan_quality_policy_path": str(Path("spec/plan-quality-scoring.yaml").resolve()),
                "execution_ready_plan_path": execution_ready_plan_path,
                "execution_packet_paths": execution_packet_paths,
            },
        },
    )
    return "artifacts/design-review-request.packet.json"


def test_execute_review_program_runs_bounded_tool_calls(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_payload = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    plan_path = _seed_plan(tmp_path, scope_ref=str(scope_payload["packet_id"]))
    materialization_code, materialization_report = materialize_execution_slices(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        chosen_plan_path=plan_path,
        policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        output_root="artifacts/materialization-test",
    )
    assert materialization_code == 0
    execution_ready_plan_path = str(materialization_report["execution_ready_plan_path"])
    execution_packet_paths = [str(item) for item in materialization_report["execution_packet_paths"]]
    program_path = _seed_program(
        tmp_path,
        selected_scope_path=selected_scope_path,
        plan_path=plan_path,
        execution_ready_plan_path=execution_ready_plan_path,
        execution_packet_paths=execution_packet_paths,
    )

    code, report = execute_review_program(
        root=tmp_path.as_posix(),
        program_path=program_path,
        output_root="artifacts/design-review-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert len(report["request_packet_paths"]) == 2
    assert len(report["result_packet_paths"]) == 2
    assert len(report["step_reports"]) == 2


def test_execute_review_program_blocks_unsupported_node(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "design-review-program.packet.json",
        {
            "packet_type": "design_review_program_packet",
            "packet_version": "v1",
            "packet_id": "drp-002",
            "created_at": "2026-05-20T00:00:00Z",
            "producer": "test",
            "review_id": "review-002",
            "review_request_ref": "artifacts/design-review-request.packet.json",
            "review_nodes": [
                {
                    "node_id": "review-evidence",
                    "target_tool": "evidence-search-tool",
                    "operation_name": "assemble_evidence_packet",
                    "input_packet_refs": [],
                    "policy_ref": "bounded-review-policy",
                }
            ],
            "stop_conditions": {"max_tool_calls": 1},
        },
    )

    code, report = execute_review_program(
        root=tmp_path.as_posix(),
        program_path="artifacts/design-review-program.packet.json",
        output_root="artifacts/design-review-test",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "evidence_adapter_inputs_incomplete" in report["blockers"]


def test_run_design_review_workflow_from_request(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_payload = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    plan_path = _seed_plan(tmp_path, scope_ref=str(scope_payload["packet_id"]))
    materialization_code, materialization_report = materialize_execution_slices(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        chosen_plan_path=plan_path,
        policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        output_root="artifacts/materialization-test",
    )
    assert materialization_code == 0
    request_path = _seed_request(
        tmp_path,
        selected_scope_path=selected_scope_path,
        plan_path=plan_path,
        execution_ready_plan_path=str(materialization_report["execution_ready_plan_path"]),
        execution_packet_paths=[str(item) for item in materialization_report["execution_packet_paths"]],
    )

    code, report = run_design_review_workflow(
        root=tmp_path.as_posix(),
        request_path=request_path,
        output_root="artifacts/design-review-test",
        design_iteration_root=Path(__file__).resolve().parents[1].as_posix(),
        design_iteration_output_root="artifacts/design-iteration-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert Path(str(report["design_findings_packet_path"])).exists()
    assert Path(str(report["design_gaps_packet_path"])).exists()
    assert Path(str(report["next_question_candidates_path"])).exists()
    assert len(report["tool_call_result_paths"]) == 4
    assert len(report["step_reports"]) == 3


def test_question_research_handoff_review_mode_runs(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "question-handoff-review.packet.json",
        {
            "packet_type": "design_review_request_packet",
            "packet_version": "v1",
            "packet_id": "drr-handoff-001",
            "created_at": "2026-05-21T00:00:00Z",
            "producer": "test",
            "review_id": "review-handoff-001",
            "system_scope": "platform-template-bootstrap",
            "artifact_refs": [
                "docs/question-tool-v1.md",
                "docs/evidence-search-tool-v1.md",
                "docs/research-tool-v1.md",
            ],
            "requested_review_modes": [
                "question_research_handoff_review"
            ],
            "requested_outputs": [
                "design_findings_packet"
            ],
            "review_inputs": {},
        },
    )

    code, report = run_design_review_workflow(
        root=tmp_path.as_posix(),
        request_path="artifacts/question-handoff-review.packet.json",
        output_root="artifacts/design-review-test",
        design_iteration_root=Path(__file__).resolve().parents[1].as_posix(),
        design_iteration_output_root="artifacts/design-iteration-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    execute_step = report["step_reports"][1]["report"]
    assert any("review-question-research-handoff" in path for path in execute_step["result_packet_paths"])
    assert execute_step["blockers"] == []
