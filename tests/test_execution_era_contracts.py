from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


ROOT = Path(__file__).resolve().parents[1]


def _load_schema(name: str) -> dict[str, Any]:
    payload = yaml.safe_load((ROOT / "spec" / "contracts" / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _missing_required(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    missing = [field for field in schema["required_fields"] if field not in payload]
    packet_const = schema.get("properties", {}).get("packet_type", {}).get("const")
    if packet_const and payload.get("packet_type") != packet_const:
        missing.append("packet_type_const_mismatch")
    return missing


def _base(packet_type: str) -> dict[str, Any]:
    return {
        "packet_type": packet_type,
        "packet_version": "v1",
        "packet_id": f"{packet_type}:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
    }


def _attempt() -> dict[str, Any]:
    return {
        **_base("implementation_attempt"),
        "attempt_id": "attempt-1",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "attempt_family": "baseline_reference",
        "implementation_summary": "Candidate patch.",
        "changed_artifact_refs": ["src/example.py"],
        "patch_ref": "artifacts/patches/attempt-1.patch",
        "validation_command_refs": ["uv run pytest tests/test_example.py"],
        "assumptions": [],
        "risks": [],
        "status": "validated",
        "created_by": "agent/codex",
    }


def _evaluation() -> dict[str, Any]:
    return {
        **_base("attempt_evaluation"),
        "evaluation_id": "evaluation-1",
        "source_attempt_ref": "implementation-attempt.packet.json",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "evaluation_method": "pytest_and_review",
        "validation_results": [{"command": "uv run pytest", "status": "passed"}],
        "test_results": [{"name": "pytest", "status": "passed"}],
        "review_findings": [],
        "score_breakdown": {"contract_fit": 1.0},
        "promotion_status": "promoted",
        "blockers": [],
        "evidence_refs": ["artifacts/test-output.txt"],
    }


def _solution() -> dict[str, Any]:
    return {
        **_base("solution_artifact"),
        "solution_artifact_id": "solution-1",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "selected_attempt_ref": "implementation-attempt.packet.json",
        "evaluation_ref": "attempt-evaluation.packet.json",
        "artifact_refs": ["src/example.py"],
        "patch_ref": "artifacts/patches/attempt-1.patch",
        "completion_evidence_refs": ["artifacts/test-output.txt"],
        "validation_summary": "Tests passed.",
        "known_limitations": [],
        "follow_up_problem_node_refs": [],
    }


def test_implementation_attempt_contract_requires_execution_unit_ref() -> None:
    schema = _load_schema("implementation-attempt.schema.yaml")
    assert _missing_required(_attempt(), schema) == []

    invalid = _attempt()
    invalid.pop("source_execution_unit_ref")
    assert "source_execution_unit_ref" in _missing_required(invalid, schema)


def test_attempt_evaluation_contract_requires_attempt_ref_and_blockers() -> None:
    schema = _load_schema("attempt-evaluation.schema.yaml")
    assert _missing_required(_evaluation(), schema) == []

    invalid = _evaluation()
    invalid.pop("blockers")
    assert "blockers" in _missing_required(invalid, schema)


def test_solution_artifact_contract_requires_selected_attempt_and_evaluation() -> None:
    schema = _load_schema("solution-artifact.schema.yaml")
    assert _missing_required(_solution(), schema) == []

    invalid = _solution()
    invalid.pop("evaluation_ref")
    assert "evaluation_ref" in _missing_required(invalid, schema)


def test_attempt_is_not_solution_artifact() -> None:
    schema = _load_schema("solution-artifact.schema.yaml")
    missing = _missing_required(_attempt(), schema)
    assert "packet_type_const_mismatch" in missing
    assert "solution_artifact_id" in missing
    assert "selected_attempt_ref" in missing
