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


def _attempt_selection() -> dict[str, Any]:
    return {
        "packet_type": "attempt_selection",
        "packet_version": "v1",
        "packet_id": "attempt-selection:001",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "selection_id": "selection-1",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "selected_attempt_ref": "attempt-1.packet.json",
        "selected_evaluation_ref": "evaluation-1.packet.json",
        "rejected_attempt_refs": ["attempt-2.packet.json"],
        "rejected_evaluation_refs": ["evaluation-2.packet.json"],
        "candidate_score_breakdown": [],
        "selection_policy_ref": "docs/policy.md",
        "evidence_refs": ["artifacts/evidence.json"],
        "blockers": [],
    }


def test_attempt_selection_contract_requires_selected_and_rejected_refs() -> None:
    schema = _load_schema("attempt-selection.schema.yaml")
    assert _missing_required(_attempt_selection(), schema) == []

    invalid = _attempt_selection()
    invalid.pop("rejected_attempt_refs")
    assert "rejected_attempt_refs" in _missing_required(invalid, schema)


def test_attempt_evaluation_is_not_attempt_selection() -> None:
    schema = _load_schema("attempt-selection.schema.yaml")
    invalid = _attempt_selection()
    invalid["packet_type"] = "attempt_evaluation"

    assert "packet_type_const_mismatch" in _missing_required(invalid, schema)
