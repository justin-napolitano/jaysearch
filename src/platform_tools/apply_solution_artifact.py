from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "apply-solution-artifact"
DEFAULT_OUTPUT_ROOT = Path("artifacts/apply-solution/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("asa-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _required_fields_present(payload: dict[str, Any], fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        value = payload.get(field)
        if field not in payload or value in ("", None):
            missing.append(field)
    return missing


def _resolve_ref(repo_root: Path, ref: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute():
        return candidate
    return repo_root / ref


def _truncate(value: str, max_chars: int = 12000) -> str:
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def _copy_ignore(output_root_parts: tuple[str, ...]):
    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache"}
        current = Path(directory).parts
        if current[-len(output_root_parts) :] == output_root_parts:
            ignored.update(names)
        if Path(directory).name == "artifacts" and "apply-solution" in names:
            ignored.add("apply-solution")
        return ignored.intersection(names)

    return ignore


def _parse_patch_changed_paths(patch_path: Path) -> list[str]:
    changed: list[str] = []
    for line in patch_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("+++ "):
            continue
        target = line[4:].strip()
        if target == "/dev/null":
            continue
        if target.startswith("b/"):
            target = target[2:]
        changed.append(target)
    return sorted(set(changed))


def _run_command(
    *,
    command: list[str],
    cwd: Path,
    timeout_seconds: int,
    artifact_path: Path,
) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        result = {
            "command": " ".join(command),
            "status": "passed" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(completed.stdout),
            "stderr_tail": _truncate(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = {
            "command": " ".join(command),
            "status": "timeout",
            "exit_code": None,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(str(exc.stdout or "")),
            "stderr_tail": _truncate(str(exc.stderr or "")),
        }
    return result, write_json(artifact_path, result).as_posix()


def _run_validation_command(
    *,
    command: str,
    cwd: Path,
    timeout_seconds: int,
    artifact_path: Path,
) -> tuple[dict[str, Any], str]:
    return _run_command(
        command=command.split(),
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        artifact_path=artifact_path,
    )


def apply_solution_artifact(
    *,
    root: str = ".",
    execution_unit_path: str,
    attempt_path: str,
    evaluation_path: str,
    solution_artifact_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    timeout_seconds: int = 60,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    attempt = _load_json(repo_root / attempt_path)
    evaluation = _load_json(repo_root / evaluation_path)
    solution = _load_json(repo_root / solution_artifact_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    apply_target = run_root / "worktree"

    blockers: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if str(attempt.get("packet_type", "")).strip() != "implementation_attempt":
        blockers.append("implementation_attempt_packet_type_invalid")
    if str(evaluation.get("packet_type", "")).strip() != "attempt_evaluation":
        blockers.append("attempt_evaluation_packet_type_invalid")
    if str(solution.get("packet_type", "")).strip() != "solution_artifact":
        blockers.append("solution_artifact_packet_type_invalid")

    blockers.extend(
        f"execution_unit_missing_field:{field}"
        for field in _required_fields_present(
            execution_unit,
            ["execution_unit_id", "owned_changes", "validation_commands"],
        )
    )
    blockers.extend(
        f"implementation_attempt_missing_field:{field}"
        for field in _required_fields_present(
            attempt,
            ["attempt_id", "source_execution_unit_ref", "changed_artifact_refs", "patch_ref"],
        )
    )
    blockers.extend(
        f"attempt_evaluation_missing_field:{field}"
        for field in _required_fields_present(
            evaluation,
            ["source_attempt_ref", "source_execution_unit_ref", "promotion_status", "blockers"],
        )
    )
    blockers.extend(
        f"solution_artifact_missing_field:{field}"
        for field in _required_fields_present(
            solution,
            [
                "solution_artifact_id",
                "source_execution_unit_ref",
                "selected_attempt_ref",
                "evaluation_ref",
                "patch_ref",
                "completion_evidence_refs",
            ],
        )
    )

    execution_ref = str((repo_root / execution_unit_path).resolve())
    attempt_ref = str((repo_root / attempt_path).resolve())
    evaluation_ref = str((repo_root / evaluation_path).resolve())
    solution_ref = str((repo_root / solution_artifact_path).resolve())
    if str(attempt.get("source_execution_unit_ref", "")).strip() != execution_ref:
        blockers.append("attempt_source_execution_unit_ref_mismatch")
    if str(evaluation.get("source_execution_unit_ref", "")).strip() != execution_ref:
        blockers.append("evaluation_source_execution_unit_ref_mismatch")
    if str(evaluation.get("source_attempt_ref", "")).strip() != attempt_ref:
        blockers.append("evaluation_source_attempt_ref_mismatch")
    if str(solution.get("source_execution_unit_ref", "")).strip() != execution_ref:
        blockers.append("solution_source_execution_unit_ref_mismatch")
    if str(solution.get("selected_attempt_ref", "")).strip() != attempt_ref:
        blockers.append("solution_selected_attempt_ref_mismatch")
    if str(solution.get("evaluation_ref", "")).strip() != evaluation_ref:
        blockers.append("solution_evaluation_ref_mismatch")
    if str(evaluation.get("promotion_status", "")).strip() != "promoted":
        blockers.append("attempt_evaluation_not_promoted")

    evaluation_blockers = _string_list(evaluation.get("blockers", []))
    blockers.extend(f"evaluation_blocker:{item}" for item in evaluation_blockers)
    patch_ref = str(solution.get("patch_ref", "")).strip()
    patch_path = _resolve_ref(repo_root, patch_ref) if patch_ref else repo_root / "__missing.patch"
    if not patch_ref:
        blockers.append("solution_patch_ref_missing")
    elif not patch_path.exists():
        blockers.append(f"patch_ref_missing:{patch_ref}")

    owned_changes = set(_string_list(execution_unit.get("owned_changes", [])))
    patch_changed_paths: list[str] = []
    if patch_ref and patch_path.exists():
        patch_changed_paths = _parse_patch_changed_paths(patch_path)
        outside_owned = sorted(set(patch_changed_paths) - owned_changes)
        blockers.extend(f"patch_changed_path_outside_owned_changes:{item}" for item in outside_owned)

    apply_result_ref = ""
    validation_result_refs: list[str] = []
    if not blockers:
        output_parts = tuple(Path(output_root).parts)
        shutil.copytree(repo_root, apply_target, ignore=_copy_ignore(output_parts))
        check_result, apply_result_ref = _run_command(
            command=["git", "apply", "--check", patch_path.as_posix()],
            cwd=apply_target,
            timeout_seconds=timeout_seconds,
            artifact_path=run_root / "apply-check.result.json",
        )
        if check_result["status"] != "passed":
            blockers.append("patch_apply_check_failed")
        else:
            apply_result, apply_result_ref = _run_command(
                command=["git", "apply", patch_path.as_posix()],
                cwd=apply_target,
                timeout_seconds=timeout_seconds,
                artifact_path=run_root / "apply.result.json",
            )
            if apply_result["status"] != "passed":
                blockers.append("patch_apply_failed")

    if not blockers:
        for index, command in enumerate(_string_list(execution_unit.get("validation_commands", [])), start=1):
            result, ref = _run_validation_command(
                command=command,
                cwd=apply_target,
                timeout_seconds=timeout_seconds,
                artifact_path=run_root / f"post-apply-validation-{index:02d}.result.json",
            )
            validation_result_refs.append(ref)
            if result["status"] != "passed":
                blockers.append(f"post_apply_validation_failed:{command}")

    applied_solution_path = ""
    if not blockers:
        applied_solution_id = (
            f"applied-solution:{str(solution.get('solution_artifact_id', 'solution')).replace(':', '-')}"
        )
        applied_solution = {
            "packet_type": "applied_solution",
            "packet_version": "v1",
            "packet_id": f"{applied_solution_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "applied_solution_id": applied_solution_id,
            "source_solution_artifact_ref": solution_ref,
            "source_execution_unit_ref": execution_ref,
            "selected_attempt_ref": attempt_ref,
            "evaluation_ref": evaluation_ref,
            "patch_ref": patch_ref,
            "apply_target_ref": apply_target.as_posix(),
            "apply_result_ref": apply_result_ref,
            "validation_result_refs": validation_result_refs,
            "applied_artifact_refs": patch_changed_paths,
            "status": "applied",
            "blockers": [],
        }
        applied_solution_path = write_json(run_root / "applied-solution.packet.json", applied_solution).as_posix()

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_unit_path": execution_ref,
            "attempt_path": attempt_ref,
            "evaluation_path": evaluation_ref,
            "solution_artifact_path": solution_ref,
            "apply_target_ref": apply_target.as_posix(),
            "apply_result_ref": apply_result_ref,
            "validation_result_refs": validation_result_refs,
            "applied_solution_path": applied_solution_path,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "apply-solution-artifact.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--attempt-path", required=True)
    parser.add_argument("--evaluation-path", required=True)
    parser.add_argument("--solution-artifact-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()
    try:
        code, report = apply_solution_artifact(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            attempt_path=args.attempt_path,
            evaluation_path=args.evaluation_path,
            solution_artifact_path=args.solution_artifact_path,
            output_root=args.output_root,
            timeout_seconds=args.timeout_seconds,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
