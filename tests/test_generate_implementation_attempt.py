from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.generate_implementation_attempt import generate_implementation_attempt


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
        "implementation_intent": {
            "summary": "Generate attempt.",
            "contract_changes": [],
            "runtime_changes": ["src/platform_tools/example.py"],
            "validation_changes": ["uv run pytest tests/test_example.py"],
            "docs_changes": [],
            "handoff_requirements": [],
        },
        "owned_changes": ["src/platform_tools/example.py", "tests/test_example.py"],
        "required_inputs": ["selected scope"],
        "expected_outputs": ["implementation attempt"],
        "acceptance_checks": ["attempt packet exists"],
        "validation_commands": ["uv run pytest tests/test_example.py"],
        "rollback_plan": "Remove changed files.",
        "non_goals": ["do not evaluate"],
        "dependency_refs": [],
        "evidence_refs": ["docs/current-research-bibliography.md"],
        "evaluation_method": "pytest",
        "completion_evidence_requirements": ["pytest output"],
    }


def test_generate_implementation_attempt_emits_attempt_packet(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["attempt_count"] == 1
    attempt = json.loads(Path(report["attempt_packet_paths"][0]).read_text(encoding="utf-8"))
    assert attempt["packet_type"] == "implementation_attempt"
    assert attempt["source_execution_unit_ref"].endswith("artifacts/execution-unit.packet.json")
    assert attempt["changed_artifact_refs"] == [
        "src/platform_tools/example.py",
        "tests/test_example.py",
    ]
    assert attempt["validation_command_refs"] == ["uv run pytest tests/test_example.py"]
    assert attempt["patch_ref"] == ""
    assert attempt["status"] == "draft"


def test_generate_implementation_attempt_respects_max_attempts(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        max_attempts=2,
        attempt_family="reuse_hybrid",
    )

    assert code == 0
    assert report["attempt_count"] == 2
    first = json.loads(Path(report["attempt_packet_paths"][0]).read_text(encoding="utf-8"))
    second = json.loads(Path(report["attempt_packet_paths"][1]).read_text(encoding="utf-8"))
    assert first["attempt_family"] == "reuse_hybrid"
    assert first["attempt_id"] != second["attempt_id"]


def test_generate_implementation_attempt_blocks_missing_validation_commands(
    tmp_path: Path,
) -> None:
    payload = _execution_unit()
    payload["validation_commands"] = []
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        payload,
    )

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "execution_unit_missing_field:validation_commands" in report["blockers"]
    assert "execution_unit_missing_validation_commands" in report["blockers"]


def test_generate_implementation_attempt_blocks_invalid_packet_type(tmp_path: Path) -> None:
    payload = _execution_unit()
    payload["packet_type"] = "selected_solution_scope"
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        payload,
    )

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
    )

    assert code == 1
    assert "execution_unit_packet_type_invalid" in report["blockers"]


def test_generate_implementation_attempt_accepts_valid_patch_source(tmp_path: Path) -> None:
    source_file = tmp_path / "src" / "platform_tools" / "example.py"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    patch_path = tmp_path / "artifacts" / "noop.patch"
    patch_path.write_text(
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

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path="artifacts/noop.patch",
        validate_patch=True,
    )

    assert code == 0
    assert report["patch_validation_refs"]
    attempt = json.loads(Path(report["attempt_packet_paths"][0]).read_text(encoding="utf-8"))
    assert attempt["patch_ref"].endswith("implementation-attempt-01.patch")
    validation = json.loads(Path(report["patch_validation_refs"][0]).read_text(encoding="utf-8"))
    assert validation["status"] == "passed"


def test_generate_implementation_attempt_blocks_invalid_patch_source(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    patch_path = tmp_path / "artifacts" / "bad.patch"
    patch_path.write_text("not a patch\n", encoding="utf-8")

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path="artifacts/bad.patch",
        validate_patch=True,
    )

    assert code == 1
    assert report["attempt_packet_paths"] == []
    assert "patch_validation_failed" in report["blockers"]
    assert report["patch_validation_refs"]


def test_generate_implementation_attempt_blocks_missing_patch_source(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )

    code, report = generate_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        patch_source_path="artifacts/missing.patch",
        validate_patch=True,
    )

    assert code == 1
    assert "patch_source_path_missing" in report["blockers"]
