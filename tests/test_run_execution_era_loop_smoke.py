from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.run_execution_era_loop_smoke import run_execution_era_loop_smoke


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _execution_unit(*, valid: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": "execution-unit:001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "execution_unit_id": "execution-unit:test",
        "source_problem_node_ref": "problem-node.packet.json",
        "selected_option_ref": "node-option.packet.json",
        "implementation_intent": {"summary": "Run smoke loop."},
        "owned_changes": ["src/platform_tools/example.py"],
        "required_inputs": ["selected scope"],
        "expected_outputs": ["solution artifact"],
        "acceptance_checks": ["solution artifact exists"],
        "validation_commands": ["uv run pytest tests/test_example.py"],
        "rollback_plan": "Remove changed files.",
        "non_goals": ["do not autonomously edit"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "pytest",
        "completion_evidence_requirements": ["pytest output"],
    }
    if not valid:
        payload["validation_commands"] = []
    return payload


def _execution_unit_with_command(command: str) -> dict[str, object]:
    payload = _execution_unit()
    payload["validation_commands"] = [command]
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


def test_run_execution_era_loop_smoke_reaches_solution_artifact(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        validation_result_ref="artifacts/pytest-output.txt",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["attempt_packet_path"]
    assert report["attempt_evaluation_path"]
    assert report["solution_artifact_path"]
    assert len(report["step_reports"]) == 3
    smoke_packet = json.loads(Path(report["smoke_packet_path"]).read_text(encoding="utf-8"))
    assert smoke_packet["packet_type"] == "execution_era_loop_smoke_report"
    assert smoke_packet["validated_scope"] == "execution_era_packet_loop_only"
    assert smoke_packet["applied_solution_ref"] == ""
    assert report["applied_solution_path"] == ""


def test_run_execution_era_loop_smoke_blocks_on_attempt_generation_failure(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(valid=False),
    )

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        validation_result_ref="artifacts/pytest-output.txt",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["solution_artifact_path"] == ""
    assert any(
        blocker.startswith("generate_implementation_attempt:")
        for blocker in report["blockers"]
    )


def test_run_execution_era_loop_smoke_blocks_without_validation_evidence(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert any(
        blocker == "emit_solution_artifact:solution_missing_completion_evidence_refs"
        for blocker in report["blockers"]
    )


def test_run_execution_era_loop_smoke_can_use_command_backed_validation(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/execution-unit.packet.json"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        execute_validation_commands=True,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["validation_mode"] == "command_execution"
    evaluation_report = report["step_reports"][1]["report"]
    assert evaluation_report["command_evidence_refs"]
    smoke_packet = json.loads(Path(report["smoke_packet_path"]).read_text(encoding="utf-8"))
    assert smoke_packet["validation_mode"] == "command_execution"
    assert "direct validation command execution" not in smoke_packet["explicitly_not_validated"]


def test_run_execution_era_loop_smoke_blocks_failing_command_backed_validation(
    tmp_path: Path,
) -> None:
    command = "python3 -m json.tool artifacts/missing.json"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        execute_validation_commands=True,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert any(
        blocker == f"evaluate_implementation_attempt:validation_command_failed:{command}"
        for blocker in report["blockers"]
    )


def test_run_execution_era_loop_smoke_promotes_patch_validated_attempt(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    patch_source_path = "artifacts/change.patch"
    _write_valid_patch(tmp_path / patch_source_path)

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path=patch_source_path,
        validate_patch=True,
        validate_patch_ref=True,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["validation_mode"] == "patch_check"
    generation_report = report["step_reports"][0]["report"]
    evaluation_report = report["step_reports"][1]["report"]
    assert generation_report["patch_validation_refs"]
    assert evaluation_report["patch_validation_refs"]
    smoke_packet = json.loads(Path(report["smoke_packet_path"]).read_text(encoding="utf-8"))
    assert smoke_packet["validation_mode"] == "patch_check"
    assert "patch applicability validation" not in smoke_packet["explicitly_not_validated"]
    solution = json.loads(Path(report["solution_artifact_path"]).read_text(encoding="utf-8"))
    assert solution["patch_ref"]
    assert solution["completion_evidence_refs"] == evaluation_report["patch_validation_refs"]


def test_run_execution_era_loop_smoke_blocks_invalid_patch_at_evaluation(
    tmp_path: Path,
) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    patch_source_path = "artifacts/bad.patch"
    bad_patch_path = tmp_path / patch_source_path
    bad_patch_path.parent.mkdir(parents=True, exist_ok=True)
    bad_patch_path.write_text("not a patch\n", encoding="utf-8")

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path=patch_source_path,
        validate_patch_ref=True,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["solution_artifact_path"] == ""
    assert any(
        blocker.startswith("evaluate_implementation_attempt:patch_validation_failed:")
        for blocker in report["blockers"]
    )


def test_run_execution_era_loop_smoke_can_apply_solution_in_isolated_target(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    command = "python3 -m py_compile src/platform_tools/example.py"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    patch_source_path = "artifacts/change.patch"
    _write_valid_patch(tmp_path / patch_source_path)

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path=patch_source_path,
        validate_patch=True,
        validate_patch_ref=True,
        apply_solution=True,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["applied_solution_path"]
    assert len(report["step_reports"]) == 4
    assert report["step_reports"][3]["step"] == "apply_solution_artifact"
    assert (tmp_path / "src" / "platform_tools" / "example.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    smoke_packet = json.loads(Path(report["smoke_packet_path"]).read_text(encoding="utf-8"))
    assert smoke_packet["applied_solution_ref"] == report["applied_solution_path"]
    assert "isolated solution application" not in smoke_packet["explicitly_not_validated"]
    applied = json.loads(Path(report["applied_solution_path"]).read_text(encoding="utf-8"))
    assert applied["packet_type"] == "applied_solution"
    isolated_source = Path(applied["apply_target_ref"]) / "src" / "platform_tools" / "example.py"
    assert isolated_source.read_text(encoding="utf-8") == "VALUE = 2\n"


def test_run_execution_era_loop_smoke_blocks_failed_optional_apply(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    command = "python3 -m py_compile missing.py"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit_with_command(command),
    )
    patch_source_path = "artifacts/change.patch"
    _write_valid_patch(tmp_path / patch_source_path)

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path=patch_source_path,
        validate_patch=True,
        validate_patch_ref=True,
        apply_solution=True,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["solution_artifact_path"] == ""
    assert any(
        blocker == f"apply_solution_artifact:post_apply_validation_failed:{command}"
        for blocker in report["blockers"]
    )


def test_run_execution_era_loop_smoke_selects_from_multiple_attempts(
    tmp_path: Path,
) -> None:
    _write_example_source(tmp_path)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    patch_source_path = "artifacts/change.patch"
    _write_valid_patch(tmp_path / patch_source_path)

    code, report = run_execution_era_loop_smoke(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path=patch_source_path,
        validate_patch=True,
        validate_patch_ref=True,
        max_attempts=2,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert len(report["attempt_packet_paths"]) == 2
    assert len(report["attempt_evaluation_paths"]) == 2
    assert report["attempt_selection_path"]
    assert any(step["step"] == "select_implementation_attempt" for step in report["step_reports"])
    selection = json.loads(Path(report["attempt_selection_path"]).read_text(encoding="utf-8"))
    assert selection["packet_type"] == "attempt_selection"
    assert selection["selected_attempt_ref"] == report["attempt_packet_path"]
    assert len(selection["rejected_attempt_refs"]) == 1
    solution = json.loads(Path(report["solution_artifact_path"]).read_text(encoding="utf-8"))
    assert solution["selected_attempt_ref"] == selection["selected_attempt_ref"]
    assert solution["rejected_attempt_refs"] == selection["rejected_attempt_refs"]
    smoke_packet = json.loads(Path(report["smoke_packet_path"]).read_text(encoding="utf-8"))
    assert smoke_packet["attempt_selection_ref"] == report["attempt_selection_path"]
