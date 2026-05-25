from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.governance_execution_intake import validate_execution_intake


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_execution_ready_inputs(root: Path, *, invalid: bool = False) -> tuple[str, list[str]]:
    execution_ready = {
        "packet_type": "execution_ready_plan_packet",
        "packet_version": "v1",
        "packet_id": "plan-001:execution-ready",
        "created_at": "2026-05-20T00:00:00Z",
        "producer": "test",
        "plan_id": "plan-001",
        "selected_solution_scope_ref": "selected-scope-001",
        "source_structural_plan_ref": "plans/chosen-plan.json",
        "plan_readiness": "execution_ready",
        "execution_slices": [
            {
                "execution_id": "exec:n1",
                "source_plan_id": "plan-001",
                "source_node_refs": ["n1"],
                "required_inputs": ["scope:selected-scope-001"],
                "expected_outputs": ["normalized packet"],
                "validation_targets": ["unit test"],
                "blocking_dependencies": [],
                "conflict_domains": ["planning"],
                "required_approvals": [],
                "runnable_preconditions": ["selected_scope:selected-scope-001"],
                "completion_evidence_requirements": ["test report"],
            }
        ],
        "materialization_policy_ref": "spec/execution-materialization-policy.yaml",
        "materialization_warnings": [],
    }
    plan_path = root / "artifacts" / "execution-ready-plan.packet.json"
    _write_json(plan_path, execution_ready)
    packet = {
        "packet_type": "execution_packet",
        "packet_version": "v1",
        "packet_id": "exec:n1",
        "created_at": "2026-05-20T00:00:00Z",
        "producer": "test",
        "execution_id": "exec:n1",
        "node_id": "n1",
        "work_item_id": "n1",
        "graph_id": "graph-001",
        "task_summary": "Normalize inputs",
        "required_inputs": ["scope:selected-scope-001"],
        "expected_outputs": ["normalized packet"],
        "validation_targets": [] if invalid else ["unit test"],
        "blocking_dependencies": [],
        "declared_ready_inputs": ["scope:selected-scope-001"],
        "conflict_domains": ["planning"],
        "required_approvals": [],
        "completion_evidence_requirements": ["test report"],
        "runnable_preconditions": ["selected_scope:selected-scope-001"],
    }
    packet_path = root / "artifacts" / "execution-packet-01.packet.json"
    _write_json(packet_path, packet)
    return "artifacts/execution-ready-plan.packet.json", ["artifacts/execution-packet-01.packet.json"]


def test_validate_execution_intake_approves_valid_handoff(tmp_path: Path) -> None:
    plan_path, packet_paths = _seed_execution_ready_inputs(tmp_path)
    code, report = validate_execution_intake(
        root=tmp_path.as_posix(),
        execution_ready_plan_path=plan_path,
        execution_packet_paths=packet_paths,
        output_root="artifacts/governance-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["blockers"] == []
    assert report["warnings"] == []
    decision = json.loads(Path(report["decision_packet_path"]).read_text(encoding="utf-8"))
    assert decision["packet_type"] == "governance_decision_packet"
    assert decision["decision_status"] == "approved"


def test_validate_execution_intake_blocks_invalid_packet(tmp_path: Path) -> None:
    plan_path, packet_paths = _seed_execution_ready_inputs(tmp_path, invalid=True)
    code, report = validate_execution_intake(
        root=tmp_path.as_posix(),
        execution_ready_plan_path=plan_path,
        execution_packet_paths=packet_paths,
        output_root="artifacts/governance-test",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert any("execution_packet_1_missing_validation_targets" in blocker for blocker in report["blockers"])
