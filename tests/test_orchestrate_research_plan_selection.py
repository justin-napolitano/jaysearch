from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrate_research_plan_selection import run_research_plan_selection_workflow


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_recommendation(root: Path, *, invalid: bool = False) -> str:
    payload = {
        "packet_type": "research_recommendation_packet",
        "packet_version": "v1",
        "packet_id": "rec-001",
        "created_at": "2026-05-20T00:00:00Z",
        "producer": "test",
        "problem_id": "prob-1",
        "ranked_candidates": [
            {
                "candidate_id": "cand-1",
                "summary": "Best candidate",
                "strengths": ["strong validation"],
                "weaknesses": ["narrow scope"],
                "assumptions": ["local runtime"]
            }
        ],
        "recommended_candidate_id": "" if invalid else "cand-1",
        "recommendation_reason": "Best candidate for planning",
        "open_questions": ["one"],
        "artifact_refs": ["artifact/a.json"],
        "evidence_refs": ["docs/example.md"]
    }
    path = root / "artifacts" / "recommendation.packet.json"
    _write_json(path, payload)
    return "artifacts/recommendation.packet.json"


def _seed_plans(root: Path) -> list[str]:
    scope_ref = "selected-scope:prob-1:cand-1"
    for plan_id, dense in (("plan-a", True), ("plan-b", False)):
        _write_json(
            root / "plans" / f"{plan_id}.json",
            {
                "plan_id": plan_id,
                "selected_solution_scope_ref": scope_ref,
                "graph_id": f"{plan_id}-graph",
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
                        "completion_evidence_requirements": ["test report"]
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
                        "completion_evidence_requirements": ["contract report"]
                    }
                ],
                "edges": [
                    {
                        "edge_id": "e1",
                        "from_node_id": "n2",
                        "to_node_id": "n1",
                        "relation": "depends_on"
                    }
                ] if dense else []
            },
        )
    return ["plans/plan-a.json", "plans/plan-b.json"]


def test_run_research_plan_selection_workflow(tmp_path: Path) -> None:
    recommendation_path = _seed_recommendation(tmp_path)
    plan_paths = _seed_plans(tmp_path)
    code, report = run_research_plan_selection_workflow(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
        plan_paths=plan_paths,
        in_scope=["bridge research recommendation into planning"],
        out_of_scope=["question loop"],
        acceptance_checks=["governance-ready handoff"],
        plan_quality_policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        execution_materialization_policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        governance_intake=True,
        output_root="artifacts/research-plan-selection-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert Path(report["selected_solution_scope_path"]).exists()
    assert Path(report["execution_ready_plan_path"]).exists()
    assert len(report["step_reports"]) == 2


def test_run_research_plan_selection_workflow_blocks_bad_recommendation(tmp_path: Path) -> None:
    recommendation_path = _seed_recommendation(tmp_path, invalid=True)
    plan_paths = _seed_plans(tmp_path)
    code, report = run_research_plan_selection_workflow(
        root=tmp_path.as_posix(),
        recommendation_path=recommendation_path,
        plan_paths=plan_paths,
        plan_quality_policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        execution_materialization_policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        output_root="artifacts/research-plan-selection-test",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "recommended_candidate_missing" in report["blockers"]
