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


def _manifest() -> dict[str, Any]:
    return {
        "packet_type": "candidate_patch_manifest",
        "packet_version": "v1",
        "packet_id": "candidate-patch-manifest:001",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "manifest_id": "manifest-1",
        "source_execution_unit_ref": "execution-unit.packet.json",
        "candidate_patches": [
            {
                "candidate_id": "candidate-1",
                "patch_ref": "artifacts/a.patch",
                "candidate_family": "manual_patch",
                "source_label": "a",
                "producer_ref": "test",
                "expected_changed_artifact_refs": ["src/example.py"],
                "validation_refs": [],
                "blockers": [],
            }
        ],
        "validation_policy": {"validate_patches": False},
        "evidence_refs": [],
        "blockers": [],
    }


def test_candidate_patch_manifest_contract_requires_candidates() -> None:
    schema = _load_schema("candidate-patch-manifest.schema.yaml")
    assert _missing_required(_manifest(), schema) == []

    invalid = _manifest()
    invalid.pop("candidate_patches")
    assert "candidate_patches" in _missing_required(invalid, schema)


def test_attempt_selection_is_not_candidate_patch_manifest() -> None:
    schema = _load_schema("candidate-patch-manifest.schema.yaml")
    invalid = _manifest()
    invalid["packet_type"] = "attempt_selection"

    assert "packet_type_const_mismatch" in _missing_required(invalid, schema)
