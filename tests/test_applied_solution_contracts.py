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


def _applied_solution() -> dict[str, Any]:
    return {
        "packet_type": "applied_solution",
        "packet_version": "v1",
        "packet_id": "applied-solution:001",
        "created_at": "2026-05-22T00:00:00Z",
        "producer": "test",
        "applied_solution_id": "applied-solution-1",
        "source_solution_artifact_ref": "solution-artifact.packet.json",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "selected_attempt_ref": "implementation-attempt.packet.json",
        "evaluation_ref": "attempt-evaluation.packet.json",
        "patch_ref": "artifacts/patches/attempt.patch",
        "apply_target_ref": "artifacts/apply-solution/runs/run/worktree",
        "apply_result_ref": "artifacts/apply-solution/runs/run/apply.result.json",
        "validation_result_refs": ["artifacts/apply-solution/runs/run/validation.result.json"],
        "applied_artifact_refs": ["src/example.py"],
        "status": "applied",
        "blockers": [],
    }


def test_applied_solution_contract_requires_provenance_and_validation_refs() -> None:
    schema = _load_schema("applied-solution.schema.yaml")
    assert _missing_required(_applied_solution(), schema) == []

    invalid = _applied_solution()
    invalid.pop("validation_result_refs")
    assert "validation_result_refs" in _missing_required(invalid, schema)


def test_solution_artifact_is_not_applied_solution() -> None:
    schema = _load_schema("applied-solution.schema.yaml")
    payload = _applied_solution()
    payload["packet_type"] = "solution_artifact"

    assert "packet_type_const_mismatch" in _missing_required(payload, schema)
