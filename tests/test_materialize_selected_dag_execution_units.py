from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_selected_dag_execution_units import (  # noqa: E402
    materialize_selected_dag_execution_units,
)


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _node(node_id: str) -> dict[str, object]:
    return {
        "node_id": node_id,
        "title": node_id,
        "node_type": "runtime",
        "goal": f"Build {node_id}.",
        "owned_changes": [f"src/platform_tools/{node_id}.py"],
        "expected_outputs": [f"{node_id} implementation"],
        "validation_commands": [f"uv run pytest tests/test_{node_id}.py"],
        "evidence_refs": ["docs/selected-dag-execution-units-v1.md"],
    }


def _dag(*, nodes: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    return {
        "graph_id": "selected-test-dag",
        "graph_type": "implementation_dag",
        "version": "v1",
        "source_artifacts": ["docs/selected-dag-execution-units-v1.md"],
        "nodes": nodes,
        "edges": edges,
    }


def _selection(root: Path, dag_ref: str, *, blockers: list[str] | None = None) -> str:
    payload = {
        "packet_type": "candidate_dag_selection",
        "packet_version": "v1",
        "packet_id": "candidate-dag-selection:test",
        "created_at": "2026-05-26T00:00:00Z",
        "producer": "test",
        "selection_id": "selection:test",
        "source_manifest_ref": "manifest.packet.json",
        "selected_dag_ref": dag_ref,
        "selected_evaluation_ref": "evaluation.packet.json",
        "rejected_dag_refs": [],
        "rejected_evaluation_refs": [],
        "selection_policy": {"policy": "test"},
        "score_summary": {"total_score": 10},
        "evidence_refs": ["docs/selected-dag-execution-units-v1.md"],
        "blockers": blockers or [],
    }
    return _write_json(root / "artifacts" / "selection.packet.json", payload)


def test_materializes_execution_units_and_preserves_dependencies(tmp_path: Path) -> None:
    dag_ref = _write_json(
        tmp_path / "artifacts" / "selected-dag.json",
        _dag(
            nodes=[_node("define_contract"), _node("implement_runtime")],
            edges=[
                {
                    "edge_id": "e1",
                    "from_node_id": "implement_runtime",
                    "to_node_id": "define_contract",
                    "relation": "depends_on",
                }
            ],
        ),
    )
    selection_ref = _selection(tmp_path, dag_ref)

    code, report = materialize_selected_dag_execution_units(
        root=tmp_path.as_posix(),
        selection_path=selection_ref,
    )

    assert code == 0
    assert report["ok"] is True
    assert len(report["execution_unit_paths"]) == 2
    manifest = json.loads(
        Path(report["dag_execution_unit_manifest_path"]).read_text(encoding="utf-8")
    )
    assert manifest["packet_type"] == "dag_execution_unit_manifest"
    assert len(manifest["execution_dependencies"]) == 1
    assert manifest["topological_layers"] == [["define_contract"], ["implement_runtime"]]

    runtime_unit = [
        json.loads(Path(path).read_text(encoding="utf-8"))
        for path in report["execution_unit_paths"]
        if path.endswith("execution-unit-implement-runtime.packet.json")
    ][0]
    assert runtime_unit["dependency_refs"] == ["execution-unit:define-contract"]


def test_blocked_selection_does_not_emit_execution_units(tmp_path: Path) -> None:
    dag_ref = _write_json(tmp_path / "artifacts" / "selected-dag.json", _dag(nodes=[_node("a")], edges=[]))
    selection_ref = _selection(tmp_path, dag_ref, blockers=["no_eligible_candidate_dags"])

    code, report = materialize_selected_dag_execution_units(
        root=tmp_path.as_posix(),
        selection_path=selection_ref,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["execution_unit_paths"] == []
    assert "no_eligible_candidate_dags" in report["blockers"]


def test_cyclic_selected_dag_fails_closed(tmp_path: Path) -> None:
    dag_ref = _write_json(
        tmp_path / "artifacts" / "selected-dag.json",
        _dag(
            nodes=[_node("a"), _node("b")],
            edges=[
                {"from_node_id": "a", "to_node_id": "b", "relation": "depends_on"},
                {"from_node_id": "b", "to_node_id": "a", "relation": "depends_on"},
            ],
        ),
    )
    selection_ref = _selection(tmp_path, dag_ref)

    code, report = materialize_selected_dag_execution_units(
        root=tmp_path.as_posix(),
        selection_path=selection_ref,
    )

    assert code == 1
    assert "selected_dag_contains_cycle" in report["blockers"]
    assert report["execution_unit_paths"] == []


def test_buildable_node_missing_validation_blocks(tmp_path: Path) -> None:
    node = _node("underspecified")
    node.pop("validation_commands")
    dag_ref = _write_json(tmp_path / "artifacts" / "selected-dag.json", _dag(nodes=[node], edges=[]))
    selection_ref = _selection(tmp_path, dag_ref)

    code, report = materialize_selected_dag_execution_units(
        root=tmp_path.as_posix(),
        selection_path=selection_ref,
    )

    assert code == 1
    assert "node_missing_validation_targets:underspecified" in report["blockers"]
    assert report["execution_unit_paths"] == []
