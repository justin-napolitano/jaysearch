from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.select_implementation_attempt import select_implementation_attempt


def _write_json(path: Path, data: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.relative_to(path.parents[1]).as_posix()


def _execution_unit() -> dict[str, object]:
    return {
        "packet_type": "execution_unit",
        "packet_version": "v1",
        "packet_id": "execution-unit:001",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "execution_unit_id": "execution-unit:test",
        "owned_changes": ["src/example.py"],
        "validation_commands": ["python3 -m py_compile src/example.py"],
    }


def _attempt(source_ref: str, attempt_id: str, changed: list[str] | None = None) -> dict[str, object]:
    return {
        "packet_type": "implementation_attempt",
        "packet_version": "v1",
        "packet_id": f"{attempt_id}:packet",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "attempt_id": attempt_id,
        "source_execution_unit_ref": source_ref,
        "attempt_family": "baseline",
        "implementation_summary": "Candidate.",
        "changed_artifact_refs": changed or ["src/example.py"],
        "patch_ref": "artifacts/change.patch",
        "validation_command_refs": ["python3 -m py_compile src/example.py"],
        "assumptions": [],
        "risks": [],
        "status": "draft",
        "created_by": "test",
    }


def _evaluation(
    source_ref: str,
    attempt_ref: str,
    evaluation_id: str,
    *,
    promoted: bool = True,
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "packet_type": "attempt_evaluation",
        "packet_version": "v1",
        "packet_id": f"{evaluation_id}:packet",
        "created_at": "2026-05-25T00:00:00Z",
        "producer": "test",
        "evaluation_id": evaluation_id,
        "source_attempt_ref": attempt_ref,
        "source_execution_unit_ref": source_ref,
        "evaluation_method": "selector-test",
        "validation_results": [{"status": "passed"}],
        "test_results": [{"status": "passed"}],
        "review_findings": [],
        "score_breakdown": {},
        "promotion_status": "promoted" if promoted else "blocked",
        "blockers": [] if promoted else ["failed"],
        "evidence_refs": evidence_refs or ["artifacts/evidence.txt"],
    }


def _write_candidate(
    tmp_path: Path,
    execution_ref: str,
    index: int,
    *,
    promoted: bool = True,
    evidence_refs: list[str] | None = None,
    changed: list[str] | None = None,
) -> tuple[str, str]:
    attempt_path = _write_json(
        tmp_path / "artifacts" / f"attempt-{index}.packet.json",
        _attempt(execution_ref, f"attempt-{index}", changed=changed),
    )
    attempt_ref = str((tmp_path / attempt_path).resolve())
    evaluation_path = _write_json(
        tmp_path / "artifacts" / f"evaluation-{index}.packet.json",
        _evaluation(
            execution_ref,
            attempt_ref,
            f"evaluation-{index}",
            promoted=promoted,
            evidence_refs=evidence_refs,
        ),
    )
    return attempt_path, evaluation_path


def test_select_implementation_attempt_prefers_tool_evidence(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_1, evaluation_1 = _write_candidate(
        tmp_path,
        execution_ref,
        1,
        evidence_refs=["artifacts/evidence.txt"],
    )
    attempt_2, evaluation_2 = _write_candidate(
        tmp_path,
        execution_ref,
        2,
        evidence_refs=[
            "artifacts/patch-validation.result.json",
            "artifacts/validation-command-01.result.json",
        ],
    )

    code, report = select_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_paths=[attempt_1, attempt_2],
        evaluation_paths=[evaluation_1, evaluation_2],
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["selected_attempt_ref"].endswith("attempt-2.packet.json")
    selection = json.loads(Path(report["attempt_selection_path"]).read_text(encoding="utf-8"))
    assert selection["selected_attempt_ref"] == report["selected_attempt_ref"]
    assert len(selection["rejected_attempt_refs"]) == 1


def test_select_implementation_attempt_rejects_blocked_evaluations(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_1, evaluation_1 = _write_candidate(
        tmp_path,
        execution_ref,
        1,
        promoted=False,
        evidence_refs=[
            "artifacts/patch-validation.result.json",
            "artifacts/validation-command-01.result.json",
        ],
    )
    attempt_2, evaluation_2 = _write_candidate(tmp_path, execution_ref, 2)

    code, report = select_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_paths=[attempt_1, attempt_2],
        evaluation_paths=[evaluation_1, evaluation_2],
    )

    assert code == 0
    assert report["selected_attempt_ref"].endswith("attempt-2.packet.json")


def test_select_implementation_attempt_uses_deterministic_tie_breaker(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_1, evaluation_1 = _write_candidate(tmp_path, execution_ref, 1)
    attempt_2, evaluation_2 = _write_candidate(tmp_path, execution_ref, 2)

    code, report = select_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_paths=[attempt_2, attempt_1],
        evaluation_paths=[evaluation_2, evaluation_1],
    )

    assert code == 0
    assert report["selected_attempt_ref"].endswith("attempt-1.packet.json")


def test_select_implementation_attempt_blocks_when_no_eligible_attempts(tmp_path: Path) -> None:
    execution_unit_path = _write_json(
        tmp_path / "artifacts" / "execution-unit.packet.json",
        _execution_unit(),
    )
    execution_ref = str((tmp_path / execution_unit_path).resolve())
    attempt_1, evaluation_1 = _write_candidate(tmp_path, execution_ref, 1, promoted=False)
    attempt_2, evaluation_2 = _write_candidate(tmp_path, execution_ref, 2, promoted=False)

    code, report = select_implementation_attempt(
        root=tmp_path.as_posix(),
        execution_unit_path=execution_unit_path,
        attempt_paths=[attempt_1, attempt_2],
        evaluation_paths=[evaluation_1, evaluation_2],
    )

    assert code == 1
    assert "no_eligible_attempts" in report["blockers"]
    assert report["attempt_selection_path"] == ""
