from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.emit_solution_artifact import emit_solution_artifact


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _execution_unit() -> dict[str, object]:
    return {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": "execution-unit:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "execution_unit_id": "execution-unit:test",
        "source_problem_node_ref": "problem-node.packet.json",
        "selected_option_ref": "node-option.packet.json",
        "implementation_intent": {"summary": "Emit solution."},
        "owned_changes": ["src/platform_tools/example.py"],
        "required_inputs": ["selected scope"],
        "expected_outputs": ["solution artifact"],
        "acceptance_checks": ["solution artifact exists"],
        "validation_commands": ["uv run pytest tests/test_example.py"],
        "rollback_plan": "Remove changed files.",
        "non_goals": ["do not close node"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "pytest",
        "completion_evidence_requirements": ["pytest output"],
    }


def _attempt(execution_ref: str) -> dict[str, object]:
    return {
        "packet_type": "implementation_attempt",
        "packet_version": "v1",
        "packet_id": "attempt:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "attempt_id": "attempt-1",
        "source_execution_unit_ref": execution_ref,
        "attempt_family": "baseline_reference",
        "implementation_summary": "Candidate patch.",
        "changed_artifact_refs": ["src/platform_tools/example.py"],
        "patch_ref": "artifacts/patches/attempt-1.patch",
        "validation_command_refs": ["uv run pytest tests/test_example.py"],
        "assumptions": [],
        "risks": [],
        "status": "validated",
        "created_by": "test",
    }


def _evaluation(execution_ref: str, attempt_ref: str, *, promoted: bool = True) -> dict[str, object]:
    return {
        "packet_type": "attempt_evaluation",
        "packet_version": "v1",
        "packet_id": "evaluation:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "evaluation_id": "evaluation-1",
        "source_attempt_ref": attempt_ref,
        "source_execution_unit_ref": execution_ref,
        "evaluation_method": "validation_ref_and_boundary_check_v1",
        "validation_results": [{"status": "passed"}],
        "test_results": [{"status": "passed"}],
        "review_findings": [],
        "score_breakdown": {"validation_evidence": 1.0},
        "promotion_status": "promoted" if promoted else "blocked",
        "blockers": [] if promoted else ["tests_failed"],
        "evidence_refs": ["artifacts/pytest-output.txt"],
    }


def _fixture_paths(tmp_path: Path, *, promoted: bool = True) -> tuple[str, str, str]:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt(execution_ref),
    )
    attempt_ref = str((tmp_path / attempt_path).resolve())
    evaluation_path = _write_json(
        tmp_path / "artifacts" / "attempt-evaluation.packet.json",
        _evaluation(execution_ref, attempt_ref, promoted=promoted),
    )
    return execution_unit_path, attempt_path, evaluation_path


def test_emit_solution_artifact_from_promoted_evaluation(tmp_path: Path) -> None:
    execution_unit_path, attempt_path, evaluation_path = _fixture_paths(tmp_path)

    code, report = emit_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        evaluation_path=evaluation_path,
    )

    assert code == 0
    assert report["status"] == "ok"
    solution = json.loads(Path(report["solution_artifact_path"]).read_text(encoding="utf-8"))
    assert solution["packet_type"] == "solution_artifact"
    assert solution["artifact_refs"] == ["src/platform_tools/example.py"]
    assert solution["patch_ref"] == "artifacts/patches/attempt-1.patch"
    assert solution["completion_evidence_refs"] == ["artifacts/pytest-output.txt"]


def test_emit_solution_artifact_blocks_nonpromoted_evaluation(tmp_path: Path) -> None:
    execution_unit_path, attempt_path, evaluation_path = _fixture_paths(tmp_path, promoted=False)

    code, report = emit_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        evaluation_path=evaluation_path,
    )

    assert code == 1
    assert report["solution_artifact_path"] == ""
    assert "attempt_evaluation_not_promoted" in report["blockers"]
    assert "evaluation_blocker:tests_failed" in report["blockers"]


def test_emit_solution_artifact_blocks_mismatched_refs(tmp_path: Path) -> None:
    execution_unit_path, attempt_path, evaluation_path = _fixture_paths(tmp_path)
    path = tmp_path / evaluation_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["source_attempt_ref"] = "/tmp/other-attempt.packet.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    code, report = emit_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        evaluation_path=evaluation_path,
    )

    assert code == 1
    assert "evaluation_source_attempt_ref_mismatch" in report["blockers"]


def test_emit_solution_artifact_requires_completion_evidence(tmp_path: Path) -> None:
    execution_unit_path, attempt_path, evaluation_path = _fixture_paths(tmp_path)
    path = tmp_path / evaluation_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["evidence_refs"] = []
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    code, report = emit_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        evaluation_path=evaluation_path,
    )

    assert code == 1
    assert "solution_missing_completion_evidence_refs" in report["blockers"]
