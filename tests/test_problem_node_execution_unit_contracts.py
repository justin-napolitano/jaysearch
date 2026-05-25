from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


ROOT = Path(__file__).resolve().parents[1]


def _load_schema(name: str) -> dict[str, Any]:
    path = ROOT / "spec" / "contracts" / name
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _missing_required(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    return [field for field in schema["required_fields"] if field not in payload]


def _validate_minimal(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    missing = _missing_required(payload, schema)
    packet_const = schema.get("properties", {}).get("packet_type", {}).get("const")
    if packet_const and payload.get("packet_type") != packet_const:
        missing.append("packet_type_const_mismatch")
    intent_required = (
        schema.get("properties", {})
        .get("implementation_intent", {})
        .get("required_fields", [])
    )
    if intent_required:
        intent = payload.get("implementation_intent", {})
        if not isinstance(intent, dict):
            missing.append("implementation_intent")
        else:
            for field in intent_required:
                if field not in intent or intent[field] in ("", None):
                    missing.append(f"implementation_intent.{field}")
    return missing


def _base(packet_type: str) -> dict[str, Any]:
    return {
        "packet_type": packet_type,
        "packet_version": "v1",
        "packet_id": f"{packet_type}:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
    }


def _implementation_intent() -> dict[str, Any]:
    return {
        "summary": "Add node contracts.",
        "contract_changes": ["add schema"],
        "runtime_changes": [],
        "validation_changes": ["add tests"],
        "docs_changes": ["update core contract docs"],
        "handoff_requirements": ["registry entry"],
    }


def _valid_problem_node() -> dict[str, Any]:
    return {
        **_base("problem_node"),
        "node_id": "node-1",
        "node_version": "v1",
        "project_id": "project-1",
        "title": "Define node contracts",
        "node_type": "contract",
        "goal": "Create node contracts.",
        "problem_statement": "The planner needs manageable problem nodes.",
        "inputs": ["selected_solution_scope"],
        "expected_outputs": ["problem_node"],
        "constraints": ["local-first"],
        "dependencies": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "option_refs": [],
        "selected_option_ref": "",
        "readiness_state": "research_ready",
        "missing_fields": ["option_refs"],
        "evaluation_criteria": ["contract completeness"],
        "feedback_refs": [],
    }


def _valid_node_option() -> dict[str, Any]:
    return {
        **_base("node_option"),
        "option_id": "option-1",
        "source_node_ref": "problem-node.packet.json",
        "option_family": "baseline_reference",
        "approach_summary": "Define minimal contracts first.",
        "implementation_intent": _implementation_intent(),
        "expected_changes": ["spec/contracts/problem-node.schema.yaml"],
        "non_goals": ["runtime materializer"],
        "assumptions": ["schemas are additive"],
        "risks": ["schema drift"],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_refs": [],
    }


def _valid_execution_unit() -> dict[str, Any]:
    return {
        **_base("execution_unit"),
        "execution_unit_id": "exec-1",
        "source_problem_node_ref": "problem-node.packet.json",
        "selected_option_ref": "node-option.packet.json",
        "implementation_intent": _implementation_intent(),
        "owned_changes": ["spec/contracts/problem-node.schema.yaml"],
        "required_inputs": ["selected node option"],
        "expected_outputs": ["schema file"],
        "acceptance_checks": ["contract test passes"],
        "validation_commands": [
            "uv run pytest tests/test_problem_node_execution_unit_contracts.py"
        ],
        "rollback_plan": "Remove added schema and registry entries.",
        "non_goals": ["executor attempts"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "contract_schema_validation_v1",
        "completion_evidence_requirements": ["pytest output"],
    }


def test_problem_node_contract_validates_required_fields() -> None:
    schema = _load_schema("problem-node.schema.yaml")
    assert _validate_minimal(_valid_problem_node(), schema) == []

    invalid = _valid_problem_node()
    invalid.pop("readiness_state")
    assert "readiness_state" in _validate_minimal(invalid, schema)


def test_node_option_contract_requires_implementation_intent() -> None:
    schema = _load_schema("node-option.schema.yaml")
    assert _validate_minimal(_valid_node_option(), schema) == []

    invalid = _valid_node_option()
    invalid["implementation_intent"] = {"summary": "too shallow"}
    missing = _validate_minimal(invalid, schema)
    assert "implementation_intent.contract_changes" in missing
    assert "implementation_intent.validation_changes" in missing


def test_execution_unit_contract_requires_buildable_fields() -> None:
    schema = _load_schema("execution-unit.schema.yaml")
    assert _validate_minimal(_valid_execution_unit(), schema) == []

    invalid = _valid_execution_unit()
    invalid.pop("validation_commands")
    assert "validation_commands" in _validate_minimal(invalid, schema)


def test_selected_scope_shape_is_not_execution_unit() -> None:
    schema = _load_schema("execution-unit.schema.yaml")
    selected_scope_like = {
        **_base("selected_solution_scope"),
        "selection_id": "selection-1",
        "problem_id": "problem-1",
        "selected_candidate_id": "candidate-1",
        "selected_solution_summary": "A selected direction.",
    }
    missing = _validate_minimal(selected_scope_like, schema)
    assert "packet_type_const_mismatch" in missing
    assert "execution_unit_id" in missing
    assert "validation_commands" in missing
