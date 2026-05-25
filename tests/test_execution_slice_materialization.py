from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.execution_slice_materialization import materialize_execution_slices


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_selected_scope(root: Path) -> str:
    packet = {
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
    }
    _write_json(root / "artifacts" / "selected-scope.packet.json", packet)
    return "artifacts/selected-scope.packet.json"


def _seed_structural_plan(root: Path, *, invalid: bool = False) -> str:
    packet = {
        "plan_id": "plan-001",
        "selected_solution_scope_ref": "selected-scope-001",
        "graph_id": "graph-001",
        "plan_type": "implementation_plan",
        "plan_readiness": "candidate",
        "status": "ready",
        "purpose": "Chosen structural plan",
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
                "validation_targets": [] if invalid else ["unit test"],
                "completion_evidence_requirements": ["test report"],
            },
            {
                "node_id": "n2",
                "title": "Emit packets",
                "node_type": "task",
                "status": "ready",
                "goal": "Emit execution packets",
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
    }
    _write_json(root / "plans" / "chosen-plan.json", packet)
    return "plans/chosen-plan.json"


def test_materialize_execution_slices_emits_execution_ready_outputs(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    chosen_plan_path = _seed_structural_plan(tmp_path)

    code, report = materialize_execution_slices(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        chosen_plan_path=chosen_plan_path,
        policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
        evidence_refs=["evidence/ops.packet.json"],
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["execution_slice_count"] == 2
    execution_ready = json.loads(Path(report["execution_ready_plan_path"]).read_text(encoding="utf-8"))
    assert execution_ready["packet_type"] == "execution_ready_plan_packet"
    assert execution_ready["plan_readiness"] == "execution_ready"
    assert len(execution_ready["execution_slices"]) == 2
    assert "required_approvals" in execution_ready["execution_slices"][0]
    first_packet = json.loads(Path(report["execution_packet_paths"][0]).read_text(encoding="utf-8"))
    assert first_packet["required_approvals"] == []


def test_materialize_execution_slices_blocks_on_invalid_structural_plan(tmp_path: Path) -> None:
    selected_scope_path = _seed_selected_scope(tmp_path)
    chosen_plan_path = _seed_structural_plan(tmp_path, invalid=True)

    code, report = materialize_execution_slices(
        root=tmp_path.as_posix(),
        selected_scope_path=selected_scope_path,
        chosen_plan_path=chosen_plan_path,
        policy_path=str(Path("spec/execution-materialization-policy.yaml").resolve()),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "node_missing_validation_targets:n1" in report["blockers"]
