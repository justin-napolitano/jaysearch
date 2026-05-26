from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


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


def test_candidate_dag_manifest_contract_requires_candidate_refs() -> None:
    schema = _load_schema("candidate-dag-manifest.schema.yaml")
    payload = {
        "packet_type": "candidate_dag_manifest",
        "packet_version": "v1",
        "packet_id": "manifest:packet",
        "created_at": "2026-05-26T00:00:00Z",
        "producer": "test",
        "manifest_id": "manifest-1",
        "source_problem_ref": "problem-node.packet.json",
        "source_execplan_ref": "execplan.packet.json",
        "candidate_dag_refs": [],
        "selection_policy_ref": "docs/candidate-dag-selection-v1.md",
        "evidence_refs": [],
        "blockers": [],
    }

    assert _missing_required(payload, schema) == []
    payload.pop("candidate_dag_refs")
    assert "candidate_dag_refs" in _missing_required(payload, schema)


def test_candidate_dag_selection_contract_rejects_wrong_packet_type() -> None:
    schema = _load_schema("candidate-dag-selection.schema.yaml")
    payload = {
        "packet_type": "candidate_dag_manifest",
        "packet_version": "v1",
        "packet_id": "selection:packet",
        "created_at": "2026-05-26T00:00:00Z",
        "producer": "test",
        "selection_id": "selection-1",
        "source_manifest_ref": "manifest.packet.json",
        "selected_dag_ref": "dag.json",
        "selected_evaluation_ref": "evaluation.packet.json",
        "rejected_dag_refs": [],
        "rejected_evaluation_refs": [],
        "selection_policy": {},
        "score_summary": [],
        "evidence_refs": [],
        "blockers": [],
    }

    assert "packet_type_const_mismatch" in _missing_required(payload, schema)
