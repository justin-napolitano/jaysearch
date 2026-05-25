from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.validate_node_readiness import validate_node_readiness


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _base(packet_type: str) -> dict[str, object]:
    return {
        "packet_type": packet_type,
        "packet_version": "v1",
        "packet_id": f"{packet_type}:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
    }


def _implementation_intent() -> dict[str, object]:
    return {
        "summary": "Build readiness validator.",
        "contract_changes": ["add readiness policy"],
        "runtime_changes": ["add readiness validator"],
        "validation_changes": ["add readiness tests"],
        "docs_changes": ["document readiness gates"],
        "handoff_requirements": ["emit missing fields"],
    }


def _problem_node() -> dict[str, object]:
    return {
        **_base("problem_node"),
        "node_id": "node-1",
        "node_version": "v1",
        "project_id": "project-1",
        "title": "Node",
        "node_type": "contract",
        "goal": "Validate readiness.",
        "problem_statement": "Need explicit gates.",
        "inputs": [],
        "expected_outputs": [],
        "constraints": ["bounded"],
        "dependencies": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "option_refs": ["node-option.packet.json"],
        "selected_option_ref": "node-option.packet.json",
        "readiness_state": "research_ready",
        "missing_fields": [],
        "evaluation_criteria": ["all required fields present"],
        "feedback_refs": [],
    }


def _node_option() -> dict[str, object]:
    return {
        **_base("node_option"),
        "option_id": "option-1",
        "source_node_ref": "problem-node.packet.json",
        "option_family": "baseline_reference",
        "approach_summary": "Add validator.",
        "implementation_intent": _implementation_intent(),
        "expected_changes": ["src/platform_tools/validate_node_readiness.py"],
        "non_goals": ["execution-unit materializer"],
        "assumptions": ["policy is local"],
        "risks": ["too permissive"],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_refs": [],
    }


def _execution_unit() -> dict[str, object]:
    return {
        **_base("execution_unit"),
        "execution_unit_id": "exec-1",
        "source_problem_node_ref": "problem-node.packet.json",
        "selected_option_ref": "node-option.packet.json",
        "implementation_intent": _implementation_intent(),
        "owned_changes": ["src/platform_tools/validate_node_readiness.py"],
        "required_inputs": ["problem node"],
        "expected_outputs": ["readiness report"],
        "acceptance_checks": ["tests pass"],
        "validation_commands": ["uv run pytest tests/test_validate_node_readiness.py"],
        "rollback_plan": "Remove validator files.",
        "non_goals": ["executor"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "contract_gate",
        "completion_evidence_requirements": ["pytest output"],
    }


def test_valid_problem_node_passes_research_ready(tmp_path: Path) -> None:
    node_path = _write_json(tmp_path / "artifacts" / "problem-node.packet.json", _problem_node())

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="research_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 0
    assert report["ready"] is True
    assert report["missing_fields"] == []


def test_problem_node_missing_evaluation_criteria_fails_research_ready(tmp_path: Path) -> None:
    payload = _problem_node()
    payload["evaluation_criteria"] = []
    node_path = _write_json(tmp_path / "artifacts" / "problem-node.packet.json", payload)

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="research_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 1
    assert report["ready"] is False
    assert "evaluation_criteria" in report["missing_fields"]


def test_node_option_missing_implementation_intent_fails_planning_ready(tmp_path: Path) -> None:
    payload = _node_option()
    payload.pop("implementation_intent")
    node_path = _write_json(tmp_path / "artifacts" / "node-option.packet.json", payload)

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="planning_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 1
    assert "implementation_intent" in report["missing_fields"]


def test_selected_scope_shape_fails_implementation_ready(tmp_path: Path) -> None:
    payload = {
        **_base("selected_solution_scope"),
        "selection_id": "selection-1",
        "problem_id": "problem-1",
        "selected_candidate_id": "candidate-1",
        "implementation_intent": _implementation_intent(),
        "expected_changes": ["change"],
    }
    node_path = _write_json(tmp_path / "artifacts" / "selected-scope.packet.json", payload)

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="implementation_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 1
    assert "selected_solution_scope_is_not_execution_unit" in report["blockers"]
    assert "validation_commands" in report["missing_fields"]


def test_execution_unit_missing_validation_commands_fails_implementation_ready(
    tmp_path: Path,
) -> None:
    payload = _execution_unit()
    payload.pop("validation_commands")
    node_path = _write_json(tmp_path / "artifacts" / "execution-unit.packet.json", payload)

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="implementation_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 1
    assert report["blockers"] == []
    assert "validation_commands" in report["missing_fields"]


def test_valid_execution_unit_passes_implementation_ready(tmp_path: Path) -> None:
    node_path = _write_json(tmp_path / "artifacts" / "execution-unit.packet.json", _execution_unit())

    code, report = validate_node_readiness(
        root=tmp_path.as_posix(),
        node_path=node_path,
        target_state="implementation_ready",
        policy_path=Path.cwd().joinpath("spec/node-readiness-policy.yaml").as_posix(),
    )

    assert code == 0
    assert report["ready"] is True
    assert report["missing_fields"] == []
