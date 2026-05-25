from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.apply_solution_artifact import apply_solution_artifact


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _write_source(root: Path) -> None:
    source = root / "src" / "platform_tools" / "example.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")


def _write_patch(path: Path, *, target: str = "src/platform_tools/example.py") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"diff --git a/{target} b/{target}",
                "index 43b23da..5a2f16f 100644",
                f"--- a/{target}",
                f"+++ b/{target}",
                "@@ -1 +1 @@",
                "-VALUE = 1",
                "+VALUE = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _execution_unit(command: str = "python3 -m py_compile src/platform_tools/example.py") -> dict[str, object]:
    return {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": "execution-unit:001",
        "created_at": "2026-05-22T00:00:00Z",
        "producer": "test",
        "execution_unit_id": "execution-unit:test",
        "source_problem_node_ref": "problem-node.packet.json",
        "selected_option_ref": "node-option.packet.json",
        "implementation_intent": {"summary": "Apply solution."},
        "owned_changes": ["src/platform_tools/example.py"],
        "required_inputs": [],
        "expected_outputs": [],
        "acceptance_checks": [],
        "validation_commands": [command],
        "rollback_plan": "Discard isolated target.",
        "non_goals": [],
        "dependency_refs": [],
        "evidence_refs": [],
        "evaluation_method": "pytest",
        "completion_evidence_requirements": ["post apply validation"],
    }


def _attempt(execution_ref: str, patch_ref: str) -> dict[str, object]:
    return {
        "packet_type": "implementation_attempt",
        "packet_version": "v1",
        "packet_id": "attempt:001",
        "created_at": "2026-05-22T00:00:00Z",
        "producer": "test",
        "attempt_id": "attempt-1",
        "source_execution_unit_ref": execution_ref,
        "attempt_family": "baseline",
        "implementation_summary": "Patch attempt.",
        "changed_artifact_refs": ["src/platform_tools/example.py"],
        "patch_ref": patch_ref,
        "validation_command_refs": ["python3 -m py_compile src/platform_tools/example.py"],
        "assumptions": [],
        "risks": [],
        "status": "draft",
        "created_by": "test",
    }


def _evaluation(execution_ref: str, attempt_ref: str, *, promoted: bool = True) -> dict[str, object]:
    return {
        "packet_type": "attempt_evaluation",
        "packet_version": "v1",
        "packet_id": "evaluation:001",
        "created_at": "2026-05-22T00:00:00Z",
        "producer": "test",
        "evaluation_id": "evaluation-1",
        "source_attempt_ref": attempt_ref,
        "source_execution_unit_ref": execution_ref,
        "evaluation_method": "patch_check",
        "validation_results": [{"status": "passed"}],
        "test_results": [{"status": "passed"}],
        "review_findings": [],
        "score_breakdown": {},
        "promotion_status": "promoted" if promoted else "blocked",
        "blockers": [] if promoted else ["test_blocker"],
        "evidence_refs": ["artifacts/patch-validation.result.json"],
    }


def _solution(execution_ref: str, attempt_ref: str, evaluation_ref: str, patch_ref: str) -> dict[str, object]:
    return {
        "packet_type": "solution_artifact",
        "packet_version": "v1",
        "packet_id": "solution:001",
        "created_at": "2026-05-22T00:00:00Z",
        "producer": "test",
        "solution_artifact_id": "solution-1",
        "source_execution_unit_ref": execution_ref,
        "selected_attempt_ref": attempt_ref,
        "evaluation_ref": evaluation_ref,
        "artifact_refs": ["src/platform_tools/example.py"],
        "patch_ref": patch_ref,
        "completion_evidence_refs": ["artifacts/patch-validation.result.json"],
        "validation_summary": "Patch validation passed.",
        "known_limitations": [],
        "follow_up_problem_node_refs": [],
    }


def _write_packets(tmp_path: Path, *, command: str = "python3 -m py_compile src/platform_tools/example.py", patch_target: str = "src/platform_tools/example.py", promoted: bool = True) -> dict[str, str]:
    _write_source(tmp_path)
    patch_ref = "artifacts/change.patch"
    _write_patch(tmp_path / patch_ref, target=patch_target)
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(command),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_path = _write_json(
        tmp_path / "artifacts" / "implementation-attempt.packet.json",
        _attempt(execution_ref, patch_ref),
    )
    attempt_ref = str((tmp_path / attempt_path).resolve())
    evaluation_path = _write_json(
        tmp_path / "artifacts" / "attempt-evaluation.packet.json",
        _evaluation(execution_ref, attempt_ref, promoted=promoted),
    )
    evaluation_ref = str((tmp_path / evaluation_path).resolve())
    solution_path = _write_json(
        tmp_path / "artifacts" / "solution-artifact.packet.json",
        _solution(execution_ref, attempt_ref, evaluation_ref, patch_ref),
    )
    return {
        "execution_unit_path": execution_unit_path,
        "attempt_path": attempt_path,
        "evaluation_path": evaluation_path,
        "solution_path": solution_path,
    }


def test_apply_solution_artifact_applies_patch_in_isolated_target(tmp_path: Path) -> None:
    paths = _write_packets(tmp_path)

    code, report = apply_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=paths["execution_unit_path"],
        attempt_path=paths["attempt_path"],
        evaluation_path=paths["evaluation_path"],
        solution_artifact_path=paths["solution_path"],
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["applied_solution_path"]
    assert (tmp_path / "src" / "platform_tools" / "example.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    applied = json.loads(Path(report["applied_solution_path"]).read_text(encoding="utf-8"))
    assert applied["packet_type"] == "applied_solution"
    assert applied["status"] == "applied"
    assert applied["applied_artifact_refs"] == ["src/platform_tools/example.py"]
    assert applied["validation_result_refs"] == report["validation_result_refs"]
    isolated_source = Path(applied["apply_target_ref"]) / "src" / "platform_tools" / "example.py"
    assert isolated_source.read_text(encoding="utf-8") == "VALUE = 2\n"


def test_apply_solution_artifact_blocks_non_promoted_evaluation(tmp_path: Path) -> None:
    paths = _write_packets(tmp_path, promoted=False)

    code, report = apply_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=paths["execution_unit_path"],
        attempt_path=paths["attempt_path"],
        evaluation_path=paths["evaluation_path"],
        solution_artifact_path=paths["solution_path"],
    )

    assert code == 1
    assert "attempt_evaluation_not_promoted" in report["blockers"]
    assert report["applied_solution_path"] == ""


def test_apply_solution_artifact_blocks_patch_outside_owned_changes(tmp_path: Path) -> None:
    paths = _write_packets(tmp_path, patch_target="src/platform_tools/other.py")

    code, report = apply_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=paths["execution_unit_path"],
        attempt_path=paths["attempt_path"],
        evaluation_path=paths["evaluation_path"],
        solution_artifact_path=paths["solution_path"],
    )

    assert code == 1
    assert "patch_changed_path_outside_owned_changes:src/platform_tools/other.py" in report["blockers"]


def test_apply_solution_artifact_blocks_invalid_patch_before_apply(tmp_path: Path) -> None:
    paths = _write_packets(tmp_path)
    (tmp_path / "artifacts" / "change.patch").write_text("not a patch\n", encoding="utf-8")

    code, report = apply_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=paths["execution_unit_path"],
        attempt_path=paths["attempt_path"],
        evaluation_path=paths["evaluation_path"],
        solution_artifact_path=paths["solution_path"],
    )

    assert code == 1
    assert "patch_apply_check_failed" in report["blockers"]
    assert report["applied_solution_path"] == ""


def test_apply_solution_artifact_blocks_failed_post_apply_validation(tmp_path: Path) -> None:
    paths = _write_packets(tmp_path, command="python3 -m py_compile missing.py")

    code, report = apply_solution_artifact(
        root=tmp_path.as_posix(),
        execution_unit_path=paths["execution_unit_path"],
        attempt_path=paths["attempt_path"],
        evaluation_path=paths["evaluation_path"],
        solution_artifact_path=paths["solution_path"],
    )

    assert code == 1
    assert "post_apply_validation_failed:python3 -m py_compile missing.py" in report["blockers"]
    assert report["validation_result_refs"]
