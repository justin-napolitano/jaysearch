from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.evaluate_implementation_attempt import evaluate_implementation_attempt


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
        "implementation_intent": {"summary": "Evaluate attempt."},
        "owned_changes": ["src/platform_tools/example.py", "tests/test_example.py"],
        "required_inputs": ["selected scope"],
        "expected_outputs": ["attempt evaluation"],
        "acceptance_checks": ["evaluation packet exists"],
        "validation_commands": ["uv run pytest tests/test_example.py"],
        "rollback_plan": "Remove changed files.",
        "non_goals": ["do not select"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "pytest",
        "completion_evidence_requirements": ["pytest output"],
    }


def _execution_unit_with_command(command: str) -> dict[str, object]:
    payload = _execution_unit()
    payload["validation_commands"] = [command]
    return payload


def _attempt(source_ref: str) -> dict[str, object]:
    return {
        "packet_type": "implementation_attempt",
        "packet_version": "v1",
        "packet_id": "attempt:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "attempt_id": "attempt-1",
        "source_execution_unit_ref": source_ref,
        "attempt_family": "baseline_reference",
        "implementation_summary": "Candidate patch.",
        "changed_artifact_refs": ["src/platform_tools/example.py", "tests/test_example.py"],
        "patch_ref": "",
        "validation_command_refs": ["uv run pytest tests/test_example.py"],
        "assumptions": [],
        "risks": [],
        "status": "draft",
        "created_by": "test",
    }


def _attempt_with_command(source_ref: str, command: str) -> dict[str, object]:
    payload = _attempt(source_ref)
    payload["validation_command_refs"] = [command]
    return payload


def _attempt_with_patch(source_ref: str, patch_ref: str) -> dict[str, object]:
    payload = _attempt(source_ref)
    payload["patch_ref"] = patch_ref
    return payload


def _write_example_source(root: Path) -> None:
    source_file = root / "src" / "platform_tools" / "example.py"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("VALUE = 1\n", encoding="utf-8")


def _write_valid_patch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "diff --git a/src/platform_tools/example.py b/src/platform_tools/example.py",
                "index 43b23da..5a2f16f 100644",
                "--- a/src/platform_tools/example.py",
                "+++ b/src/platform_tools/example.py",
                "@@ -1 +1 @@",
                "-VALUE = 1",
                "+VALUE = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_evaluate_implementation_attempt_promotes_valid_attempt_with_evidence(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt(source_ref),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        validation_result_ref="artifacts/pytest-output.txt",
    )

    assert code == 0
    assert report["status"] == "ok"
    evaluation = json.loads(Path(report["attempt_evaluation_path"]).read_text(encoding="utf-8"))
    assert evaluation["packet_type"] == "attempt_evaluation"
    assert evaluation["promotion_status"] == "promoted"
    assert evaluation["blockers"] == []
    assert evaluation["evidence_refs"] == ["artifacts/pytest-output.txt"]


def test_evaluate_implementation_attempt_blocks_outside_owned_changes(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt = _attempt(source_ref)
    attempt["changed_artifact_refs"] = ["src/platform_tools/example.py", "unowned.py"]
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        attempt,
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        validation_result_ref="artifacts/pytest-output.txt",
    )

    assert code == 1
    assert "changed_artifact_outside_owned_changes:unowned.py" in report["blockers"]
    evaluation = json.loads(Path(report["attempt_evaluation_path"]).read_text(encoding="utf-8"))
    assert evaluation["promotion_status"] == "blocked"


def test_evaluate_implementation_attempt_blocks_source_ref_mismatch(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt("/tmp/other/execution-unit.packet.json"),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
    )

    assert code == 1
    assert "attempt_source_execution_unit_ref_mismatch" in report["blockers"]


def test_evaluate_implementation_attempt_blocks_unknown_validation_command(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt = _attempt(source_ref)
    attempt["validation_command_refs"] = ["uv run pytest tests/test_other.py"]
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        attempt,
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
    )

    assert code == 1
    assert (
        "validation_command_not_in_execution_unit:uv run pytest tests/test_other.py"
        in report["blockers"]
    )


def test_evaluate_implementation_attempt_executes_declared_passing_command(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/execution-unit.packet.json"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_command(source_ref, command),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        execute_validation_commands=True,
    )

    assert code == 0
    assert report["promotion_status"] == "promoted"
    assert report["command_evidence_refs"]
    evaluation = json.loads(Path(report["attempt_evaluation_path"]).read_text(encoding="utf-8"))
    assert evaluation["evidence_refs"] == report["command_evidence_refs"]
    result = json.loads(Path(report["command_evidence_refs"][0]).read_text(encoding="utf-8"))
    assert result["status"] == "passed"
    assert result["exit_code"] == 0


def test_evaluate_implementation_attempt_blocks_failing_executed_command(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/missing.json"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_command(source_ref, command),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        execute_validation_commands=True,
    )

    assert code == 1
    assert f"validation_command_failed:{command}" in report["blockers"]


def test_evaluate_implementation_attempt_blocks_forbidden_shell_token(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/execution-unit.packet.json; echo nope"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_command(source_ref, command),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        execute_validation_commands=True,
    )

    assert code == 1
    assert any(
        blocker.startswith("validation_command_forbidden_token:;")
        for blocker in report["blockers"]
    )
    assert report["command_evidence_refs"] == []


def test_evaluate_implementation_attempt_does_not_execute_without_flag(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/execution-unit.packet.json"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_command(source_ref, command),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
    )

    assert code == 0
    assert report["command_evidence_refs"] == []
    assert report["warnings"] == ["validation_result_ref_missing_v1_records_command_refs_only"]


def test_evaluate_implementation_attempt_validates_patch_ref_when_requested(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    patch_ref = "artifacts/change.patch"
    _write_valid_patch(tmp_path / patch_ref)
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_patch(source_ref, patch_ref),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        validation_result_ref="artifacts/pytest-output.txt",
        validate_patch_ref=True,
    )

    assert code == 0
    assert report["promotion_status"] == "promoted"
    assert report["patch_validation_refs"]
    evaluation = json.loads(Path(report["attempt_evaluation_path"]).read_text(encoding="utf-8"))
    assert evaluation["evidence_refs"] == [
        "artifacts/pytest-output.txt",
        report["patch_validation_refs"][0],
    ]
    validation = json.loads(Path(report["patch_validation_refs"][0]).read_text(encoding="utf-8"))
    assert validation["status"] == "passed"


def test_evaluate_implementation_attempt_blocks_invalid_patch_ref(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    patch_ref = "artifacts/bad.patch"
    bad_patch_path = tmp_path / patch_ref
    bad_patch_path.parent.mkdir(parents=True, exist_ok=True)
    bad_patch_path.write_text("not a patch\n", encoding="utf-8")
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_patch(source_ref, patch_ref),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        validation_result_ref="artifacts/pytest-output.txt",
        validate_patch_ref=True,
    )

    assert code == 1
    assert f"patch_validation_failed:{patch_ref}" in report["blockers"]
    assert report["patch_validation_refs"]
    validation = json.loads(Path(report["patch_validation_refs"][0]).read_text(encoding="utf-8"))
    assert validation["status"] == "failed"


def test_evaluate_implementation_attempt_blocks_missing_patch_ref_file(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    source_ref = str((tmp_path / execution_unit_path).resolve())
    patch_ref = "artifacts/missing.patch"
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt_with_patch(source_ref, patch_ref),
    )

    code, report = evaluate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        validation_result_ref="artifacts/pytest-output.txt",
        validate_patch_ref=True,
    )

    assert code == 1
    assert f"patch_ref_missing:{patch_ref}" in report["blockers"]
    assert report["patch_validation_refs"] == []
