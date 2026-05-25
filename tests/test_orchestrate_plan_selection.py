from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrate_plan_selection import run_plan_selection_workflow


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


def _plan(*, scope_ref: str, plan_id: str, valid: bool, dense: bool) -> dict[str, object]:
    nodes = [
        {
            "node_id": "n1",
            "title": "Normalize inputs",
            "node_type": "task",
            "status": "ready",
            "goal": "Normalize inputs",
            "owned_changes": ["src/a.py"],
            "conflict_domains": ["planning"],
            "expected_outputs": ["normalized packet"],
            "validation_targets": [] if not valid else ["unit test"],
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
    ]
    edges = []
    if dense:
        edges.append(
            {
                "edge_id": "e1",
                "from_node_id": "n2",
                "to_node_id": "n1",
                "relation": "depends_on",
            }
        )
    return {
        "plan_id": plan_id,
        "selected_solution_scope_ref": scope_ref,
        "graph_id": f"{plan_id}-graph",
        "plan_type": "implementation_plan",
        "plan_readiness": "candidate",
        "status": "ready",
        "purpose": "Candidate plan",
        "assumptions": ["bounded scope"],
        "risks": ["dependency drift"],
        "nodes": nodes,
        "edges": edges,
    }


def test_run_plan_selection_workflow_emits_execution_ready_outputs(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_payload = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    scope_ref = str(scope_payload["packet_id"])
    _write_json(tmp_path / "plans" / "plan-a.json", _plan(scope_ref=scope_ref, plan_id="plan-a", valid=True, dense=True))
    _write_json(tmp_path / "plans" / "plan-b.json", _plan(scope_ref=scope_ref, plan_id="plan-b", valid=True, dense=False))

    code, report = run_plan_selection_workflow(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=["plans/plan-a.json", "plans/plan-b.json"],
        plan_quality_policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        execution_materialization_policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        evidence_refs=["evidence/ops.packet.json"],
        output_root="artifacts/orchestration-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["chosen_plan_ref"] in {"plans/plan-a.json", "plans/plan-b.json"}
    assert Path(report["execution_ready_plan_path"]).exists()
    assert len(report["execution_packet_paths"]) == 2
    assert len(report["step_reports"]) == 2


def test_run_plan_selection_workflow_blocks_when_no_plan_is_valid(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_payload = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    scope_ref = str(scope_payload["packet_id"])
    _write_json(tmp_path / "plans" / "plan-a.json", _plan(scope_ref=scope_ref, plan_id="plan-a", valid=False, dense=True))
    _write_json(tmp_path / "plans" / "plan-b.json", _plan(scope_ref=scope_ref, plan_id="plan-b", valid=False, dense=False))

    code, report = run_plan_selection_workflow(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=["plans/plan-a.json", "plans/plan-b.json"],
        plan_quality_policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        execution_materialization_policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        output_root="artifacts/orchestration-test",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "no_plans_passed_hard_gates" in report["blockers"]


def test_run_plan_selection_workflow_with_governance_intake(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_payload = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    scope_ref = str(scope_payload["packet_id"])
    _write_json(tmp_path / "plans" / "plan-a.json", _plan(scope_ref=scope_ref, plan_id="plan-a", valid=True, dense=True))
    _write_json(tmp_path / "plans" / "plan-b.json", _plan(scope_ref=scope_ref, plan_id="plan-b", valid=True, dense=False))

    code, report = run_plan_selection_workflow(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=["plans/plan-a.json", "plans/plan-b.json"],
        plan_quality_policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        execution_materialization_policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        governance_intake=True,
        output_root="artifacts/orchestration-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    governance_report = report["governance_report"]
    assert isinstance(governance_report, dict)
    assert governance_report["status"] == "ok"
    assert governance_report["warnings"] == []
    assert len(report["step_reports"]) == 3
