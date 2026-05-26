from __future__ import annotations

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _load_yaml(path: str) -> dict[str, object]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_dag_execution_unit_manifest_contract_declares_required_fields() -> None:
    schema = _load_yaml("spec/contracts/dag-execution-unit-manifest.schema.yaml")

    assert schema["contract_name"] == "dag_execution_unit_manifest"
    assert schema["properties"]["packet_type"]["const"] == "dag_execution_unit_manifest"
    assert set(schema["required_fields"]) >= {
        "source_selection_ref",
        "selected_dag_ref",
        "execution_unit_refs",
        "execution_dependencies",
        "topological_layers",
        "blockers",
    }


def test_dag_execution_unit_manifest_is_registered() -> None:
    registry = _load_yaml("spec/contracts/packet-schema-registry.yaml")
    families = registry["contract_families"]
    match = [item for item in families if item["contract_name"] == "dag_execution_unit_manifest"]

    assert len(match) == 1
    assert match[0]["schema_ref"] == "spec/contracts/dag-execution-unit-manifest.schema.yaml"
    assert "implementation-orchestrator" in match[0]["downstream_consumers"]
