from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.plan_quality_score import compare_plans


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_selected_scope(root: Path) -> str:
    packet_id = "selected-scope-001"
    _write_json(
        root / "artifacts" / "selected-scope.packet.json",
        {
            "packet_type": "selected_solution_scope",
            "packet_version": "v1",
            "packet_id": packet_id,
            "created_at": "2026-05-20T00:00:00Z",
            "producer": "test",
            "problem_id": "prob-1",
            "selected_candidate_id": "cand-1",
            "selected_solution_summary": "Chosen solution",
            "scope_in": ["build tool"],
            "scope_out": ["rewrite governance"],
            "assumptions": ["local runtime"],
            "risks": ["scope drift"],
            "acceptance_targets": ["valid plan"],
        },
    )
    return "artifacts/selected-scope.packet.json"


def _plan_payload(*, plan_id: str, scope_ref: str, edge_count: int, invalid: bool = False) -> dict[str, object]:
    nodes = [
        {
            "node_id": "n1",
            "title": "Normalize inputs",
            "node_type": "task",
            "status": "ready",
            "goal": "Normalize planning inputs",
            "owned_changes": ["src/a.py"],
            "conflict_domains": ["planning"],
            "expected_outputs": ["normalized packet"],
            "validation_targets": [] if invalid else ["unit test"],
            "completion_evidence_requirements": ["test report"],
        },
        {
            "node_id": "n2",
            "title": "Score plans",
            "node_type": "task",
            "status": "ready",
            "goal": "Rank candidate plans",
            "owned_changes": ["src/b.py"],
            "conflict_domains": ["scoring"],
            "expected_outputs": ["score packet"],
            "validation_targets": ["contract test"],
            "completion_evidence_requirements": ["contract report"],
        },
    ]
    edges: list[dict[str, str]] = []
    if edge_count >= 1:
        edges.append(
            {
                "edge_id": "e1",
                "from_node_id": "n2",
                "to_node_id": "n1",
                "relation": "depends_on",
            }
        )
    if edge_count >= 2:
        edges.append(
            {
                "edge_id": "e2",
                "from_node_id": "n1",
                "to_node_id": "n2",
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
        "purpose": "Compare planning alternatives",
        "assumptions": ["bounded scope"],
        "risks": ["dependency drift"],
        "nodes": nodes,
        "edges": edges,
    }


def test_compare_plans_ranks_valid_candidates(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_packet = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    scope_ref = str(scope_packet["packet_id"])
    _write_json(tmp_path / "plans" / "plan-a.json", _plan_payload(plan_id="plan-a", scope_ref=scope_ref, edge_count=1))
    _write_json(tmp_path / "plans" / "plan-b.json", _plan_payload(plan_id="plan-b", scope_ref=scope_ref, edge_count=0))

    report = compare_plans(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=["plans/plan-a.json", "plans/plan-b.json"],
        policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
        evidence_refs=["evidence/plan-study.packet.json"],
    )

    assert report["command"] == "plan-quality-score"
    assert report["status"] == "ok"
    assert report["qualified_plan_count"] == 2
    assert report["recommended_plan_ref"] in {"plans/plan-a.json", "plans/plan-b.json"}
    ranked = json.loads(Path(report["ranked_packet_path"]).read_text(encoding="utf-8"))
    assert ranked["packet_type"] == "ranked_plan_packet"
    assert len(ranked["ranked_plan_refs"]) == 2


def test_compare_plans_disqualifies_invalid_candidate(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    scope_packet = json.loads((tmp_path / selected_scope_path).read_text(encoding="utf-8"))
    scope_ref = str(scope_packet["packet_id"])
    _write_json(tmp_path / "plans" / "plan-valid.json", _plan_payload(plan_id="plan-valid", scope_ref=scope_ref, edge_count=1))
    _write_json(tmp_path / "plans" / "plan-invalid.json", _plan_payload(plan_id="plan-invalid", scope_ref=scope_ref, edge_count=2, invalid=True))

    report = compare_plans(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        plan_paths=["plans/plan-valid.json", "plans/plan-invalid.json"],
        policy_path=str(Path("spec/plan-quality-scoring.yaml").resolve()),
    )

    assert report["status"] == "ok"
    assert report["qualified_plan_count"] == 1
    assert report["disqualified_plan_count"] == 1
    ranked = json.loads(Path(report["ranked_packet_path"]).read_text(encoding="utf-8"))
    assert ranked["recommended_plan_ref"] == "plans/plan-valid.json"
    assert "plans/plan-invalid.json" in ranked["disqualified_plan_refs"]
