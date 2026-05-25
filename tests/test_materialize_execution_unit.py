from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_execution_unit import materialize_execution_unit


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _intent(*, explicit: bool = False) -> dict[str, object]:
    if explicit:
        return {
            "summary": "Implement explicit execution unit.",
            "contract_changes": ["spec/contracts/example.schema.yaml"],
            "runtime_changes": ["src/platform_tools/example.py"],
            "validation_changes": ["uv run pytest tests/test_example.py"],
            "docs_changes": ["docs/example.md"],
            "handoff_requirements": ["selected scope packet"],
        }
    return {
        "summary": "Implement generic execution unit.",
        "contract_changes": ["add contract changes"],
        "runtime_changes": ["add runtime changes"],
        "validation_changes": ["add validation changes"],
        "docs_changes": ["document changes"],
        "handoff_requirements": ["selected scope packet"],
    }


def _selected_scope(*, with_intent: bool = True, explicit: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "packet_type": "selected_solution_scope",
        "packet_version": "v1",
        "packet_id": "selected-scope-1",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "selection_id": "selection-1",
        "problem_id": "problem-1",
        "selected_candidate_id": "candidate-1",
        "selection_reason": "Best evaluated candidate.",
        "selection_policy": {"source_recommendation_ref": "recommendation.packet.json"},
        "selected_solution_summary": "Build the selected candidate.",
        "in_scope": [],
        "out_of_scope": ["do not generate implementation attempts"],
        "scope_in": [],
        "scope_out": ["do not generate implementation attempts"],
        "assumptions": ["local repo"],
        "risks": ["incomplete scope"],
        "acceptance_checks": [],
        "acceptance_targets": [],
        "artifact_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
    }
    if with_intent:
        intent = _intent(explicit=explicit)
        payload["implementation_intent"] = intent
        payload["expected_changes"] = (
            list(intent["contract_changes"])
            + list(intent["runtime_changes"])
            + list(intent["validation_changes"])
            + list(intent["docs_changes"])
        )
        payload["contract_changes"] = intent["contract_changes"]
        payload["runtime_changes"] = intent["runtime_changes"]
        payload["validation_changes"] = intent["validation_changes"]
        payload["docs_changes"] = intent["docs_changes"]
        payload["handoff_requirements"] = intent["handoff_requirements"]
    return payload


def test_generic_selected_scope_emits_problem_node_but_blocks_execution_unit(
    tmp_path: Path,
) -> None:
    scope_path = _write_json(
        tmp_path / "artifacts" / "selected-scope.packet.json",
        _selected_scope(with_intent=False),
    )

    code, report = materialize_execution_unit(
        root=tmp_path.as_posix(),
        selected_scope_path=scope_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "problem_node_path" in report["emitted_packet_refs"]
    assert "execution_unit_path" not in report["emitted_packet_refs"]
    assert "selected_scope_missing_implementation_intent" in report["blockers"]


def test_scope_with_intent_without_paths_blocks_with_missing_owned_changes(
    tmp_path: Path,
) -> None:
    scope_path = _write_json(
        tmp_path / "artifacts" / "selected-scope.packet.json",
        _selected_scope(with_intent=True, explicit=False),
    )

    code, report = materialize_execution_unit(
        root=tmp_path.as_posix(),
        selected_scope_path=scope_path,
    )

    assert code == 1
    assert "node_option_path" in report["emitted_packet_refs"]
    assert "execution_unit_path" not in report["emitted_packet_refs"]
    assert "missing:owned_changes" in report["blockers"]


def test_scope_with_explicit_paths_and_commands_emits_execution_unit(
    tmp_path: Path,
) -> None:
    scope_path = _write_json(
        tmp_path / "artifacts" / "selected-scope.packet.json",
        _selected_scope(with_intent=True, explicit=True),
    )

    code, report = materialize_execution_unit(
        root=tmp_path.as_posix(),
        selected_scope_path=scope_path,
    )

    assert code == 0
    assert report["status"] == "ok"
    execution_unit = json.loads(
        Path(report["emitted_packet_refs"]["execution_unit_path"]).read_text(encoding="utf-8")
    )
    assert execution_unit["packet_type"] == "execution_unit"
    assert execution_unit["owned_changes"] == [
        "spec/contracts/example.schema.yaml",
        "src/platform_tools/example.py",
        "docs/example.md",
    ]
    assert execution_unit["validation_commands"] == ["uv run pytest tests/test_example.py"]
    assert report["readiness_report"]["ready"] is True


def test_materialization_report_includes_all_emitted_packet_refs(tmp_path: Path) -> None:
    scope_path = _write_json(
        tmp_path / "artifacts" / "selected-scope.packet.json",
        _selected_scope(with_intent=True, explicit=True),
    )

    code, report = materialize_execution_unit(
        root=tmp_path.as_posix(),
        selected_scope_path=scope_path,
    )

    assert code == 0
    refs = report["emitted_packet_refs"]
    assert set(refs) == {
        "problem_node_path",
        "node_option_path",
        "execution_unit_path",
    }
