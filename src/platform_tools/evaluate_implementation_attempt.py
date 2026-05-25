from __future__ import annotations

import argparse
import subprocess
import time
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "evaluate-implementation-attempt"
DEFAULT_OUTPUT_ROOT = Path("artifacts/attempt-evaluations/runs")
DEFAULT_COMMAND_POLICY_PATH = "spec/attempt-evaluation-command-policy.yaml"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("aie-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"policy_not_object:{path.as_posix()}")
    return payload


def _policy_path(repo_root: Path, policy_path: str) -> Path:
    candidate = Path(policy_path)
    if candidate.is_absolute():
        return candidate
    root_policy = repo_root / policy_path
    if root_policy.exists():
        return root_policy
    return Path(__file__).resolve().parents[2] / policy_path


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _required_fields_present(payload: dict[str, Any], fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        value = payload.get(field)
        if field not in payload or value in ("", None) or (isinstance(value, list) and not value):
            missing.append(field)
    return missing


def _validation_result(ref: str) -> dict[str, Any]:
    if not ref:
        return {
            "source_ref": "",
            "status": "not_provided",
            "summary": "No external validation result ref was provided.",
        }
    return {
        "source_ref": ref,
        "status": "passed",
        "summary": "External validation result ref provided; V1 records the ref without re-running commands.",
    }


def _command_allowed(command: str, policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    forbidden_tokens = _string_list(policy.get("forbidden_shell_tokens", []))
    for token in forbidden_tokens:
        if token in command:
            blockers.append(f"validation_command_forbidden_token:{token}:{command}")
    allowed_prefixes = _string_list(policy.get("allowed_command_prefixes", []))
    if allowed_prefixes and not any(command.startswith(prefix) for prefix in allowed_prefixes):
        blockers.append(f"validation_command_prefix_not_allowed:{command}")
    return blockers


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]


def _run_validation_command(
    *,
    repo_root: Path,
    run_root: Path,
    command: str,
    timeout_seconds: int,
    max_output_chars: int,
    index: int,
) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command.split(),
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        status = "passed" if completed.returncode == 0 else "failed"
        result = {
            "command": command,
            "status": status,
            "exit_code": completed.returncode,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(completed.stdout, max_output_chars),
            "stderr_tail": _truncate(completed.stderr, max_output_chars),
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = {
            "command": command,
            "status": "timeout",
            "exit_code": None,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(str(exc.stdout or ""), max_output_chars),
            "stderr_tail": _truncate(str(exc.stderr or ""), max_output_chars),
        }
    artifact_path = write_json(run_root / f"validation-command-{index:02d}.result.json", result)
    return result, artifact_path.as_posix()


def _resolve_ref(repo_root: Path, ref: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute():
        return candidate
    return repo_root / ref


def _run_patch_check(
    *,
    repo_root: Path,
    run_root: Path,
    patch_ref: str,
    patch_path: Path,
    max_output_chars: int,
) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["git", "apply", "--check", patch_path.as_posix()],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        status = "passed" if completed.returncode == 0 else "failed"
        result = {
            "patch_ref": patch_ref,
            "patch_path": patch_path.as_posix(),
            "command": f"git apply --check {patch_path.as_posix()}",
            "status": status,
            "exit_code": completed.returncode,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(completed.stdout, max_output_chars),
            "stderr_tail": _truncate(completed.stderr, max_output_chars),
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = {
            "patch_ref": patch_ref,
            "patch_path": patch_path.as_posix(),
            "command": f"git apply --check {patch_path.as_posix()}",
            "status": "timeout",
            "exit_code": None,
            "duration_ms": duration_ms,
            "stdout_tail": _truncate(str(exc.stdout or ""), max_output_chars),
            "stderr_tail": _truncate(str(exc.stderr or ""), max_output_chars),
        }
    artifact_path = write_json(run_root / "patch-validation.result.json", result)
    return result, artifact_path.as_posix()


def evaluate_implementation_attempt(
    *,
    root: str = ".",
    execution_unit_path: str,
    attempt_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    validation_result_ref: str = "",
    execute_validation_commands: bool = False,
    command_policy_path: str = DEFAULT_COMMAND_POLICY_PATH,
    timeout_seconds: int | None = None,
    validate_patch_ref: bool = False,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    attempt = _load_json(repo_root / attempt_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    command_policy = _load_yaml(_policy_path(repo_root, command_policy_path))
    effective_timeout = int(
        timeout_seconds
        if timeout_seconds is not None
        else command_policy.get("default_timeout_seconds", 60)
    )
    max_output_chars = int(command_policy.get("max_output_chars", 12000))

    blockers: list[str] = []
    warnings: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if str(attempt.get("packet_type", "")).strip() != "implementation_attempt":
        blockers.append("implementation_attempt_packet_type_invalid")

    execution_missing = _required_fields_present(
        execution_unit,
        ["execution_unit_id", "owned_changes", "validation_commands"],
    )
    blockers.extend(f"execution_unit_missing_field:{field}" for field in execution_missing)
    attempt_missing = _required_fields_present(
        attempt,
        [
            "attempt_id",
            "source_execution_unit_ref",
            "changed_artifact_refs",
            "validation_command_refs",
        ],
    )
    blockers.extend(f"implementation_attempt_missing_field:{field}" for field in attempt_missing)

    expected_execution_ref = str((repo_root / execution_unit_path).resolve())
    if str(attempt.get("source_execution_unit_ref", "")).strip() != expected_execution_ref:
        blockers.append("attempt_source_execution_unit_ref_mismatch")

    owned_changes = set(_string_list(execution_unit.get("owned_changes", [])))
    changed_artifacts = set(_string_list(attempt.get("changed_artifact_refs", [])))
    outside_owned_changes = sorted(changed_artifacts - owned_changes)
    blockers.extend(f"changed_artifact_outside_owned_changes:{item}" for item in outside_owned_changes)

    execution_commands = set(_string_list(execution_unit.get("validation_commands", [])))
    attempt_commands = set(_string_list(attempt.get("validation_command_refs", [])))
    if not attempt_commands:
        blockers.append("attempt_missing_validation_command_refs")
    unknown_commands = sorted(attempt_commands - execution_commands)
    blockers.extend(f"validation_command_not_in_execution_unit:{item}" for item in unknown_commands)

    patch_validation_results: list[dict[str, Any]] = []
    patch_validation_refs: list[str] = []
    patch_ref = str(attempt.get("patch_ref", "")).strip()
    if patch_ref:
        patch_path = _resolve_ref(repo_root, patch_ref)
        if not patch_path.exists():
            blockers.append(f"patch_ref_missing:{patch_ref}")
        elif validate_patch_ref:
            result, artifact_ref = _run_patch_check(
                repo_root=repo_root,
                run_root=run_root,
                patch_ref=patch_ref,
                patch_path=patch_path,
                max_output_chars=max_output_chars,
            )
            patch_validation_results.append(result)
            patch_validation_refs.append(artifact_ref)
            if result["status"] != "passed":
                blockers.append(f"patch_validation_failed:{patch_ref}")

    command_results: list[dict[str, Any]] = []
    command_evidence_refs: list[str] = []
    if execute_validation_commands:
        for command in sorted(attempt_commands):
            blockers.extend(_command_allowed(command, command_policy))
        if not blockers:
            for index, command in enumerate(sorted(attempt_commands), start=1):
                result, artifact_ref = _run_validation_command(
                    repo_root=repo_root,
                    run_root=run_root,
                    command=command,
                    timeout_seconds=effective_timeout,
                    max_output_chars=max_output_chars,
                    index=index,
                )
                command_results.append(result)
                command_evidence_refs.append(artifact_ref)
                if result["status"] != "passed":
                    blockers.append(f"validation_command_failed:{command}")

    if not validation_result_ref and attempt_commands and not execute_validation_commands:
        warnings.append("validation_result_ref_missing_v1_records_command_refs_only")
    if patch_ref and not validate_patch_ref:
        warnings.append("patch_ref_present_but_patch_validation_not_requested")

    promotion_status = "promoted" if not blockers else "blocked"
    validation_results = patch_validation_results + (
        command_results or [_validation_result(validation_result_ref)]
    )
    if attempt_commands:
        validation_results.extend(
            {
                "command": command,
                "status": "executed" if execute_validation_commands else "not_run",
                "summary": (
                    "Command executed under attempt-evaluation command policy."
                    if execute_validation_commands
                    else "Command ref preserved; command execution was not requested."
                ),
            }
            for command in sorted(attempt_commands)
        )

    evaluation_id = f"attempt-evaluation:{str(attempt.get('attempt_id', 'attempt')).replace(':', '-')}"
    evaluation = {
        "packet_type": "attempt_evaluation",
        "packet_version": "v1",
        "packet_id": f"{evaluation_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "evaluation_id": evaluation_id,
        "source_attempt_ref": str((repo_root / attempt_path).resolve()),
        "source_execution_unit_ref": expected_execution_ref,
        "evaluation_method": "validation_ref_and_boundary_check_v1",
        "validation_results": validation_results,
        "test_results": [
            {
                "status": (
                    "passed"
                    if validation_result_ref or (execute_validation_commands and not blockers)
                    else "not_run"
                ),
                "validation_result_ref": validation_result_ref,
                "command_evidence_refs": command_evidence_refs,
                "patch_validation_refs": patch_validation_refs,
            }
        ],
        "review_findings": warnings,
        "score_breakdown": {
            "source_ref_match": 0.0 if "attempt_source_execution_unit_ref_mismatch" in blockers else 1.0,
            "owned_change_boundary": 0.0 if outside_owned_changes else 1.0,
            "validation_evidence": (
                1.0
                if validation_result_ref or (execute_validation_commands and command_results and not blockers)
                else 0.5
                if attempt_commands
                else 0.0
            ),
        },
        "promotion_status": promotion_status,
        "blockers": sorted(set(blockers)),
        "evidence_refs": (
            ([validation_result_ref] if validation_result_ref else [])
            + patch_validation_refs
            + command_evidence_refs
        ),
    }
    evaluation_path = write_json(run_root / "attempt-evaluation.packet.json", evaluation)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_unit_path": expected_execution_ref,
            "attempt_path": str((repo_root / attempt_path).resolve()),
            "attempt_evaluation_path": evaluation_path.as_posix(),
            "promotion_status": promotion_status,
            "blockers": sorted(set(blockers)),
            "warnings": sorted(set(warnings)),
            "patch_validation_refs": patch_validation_refs,
            "command_evidence_refs": command_evidence_refs,
        },
    )
    write_json(run_root / "attempt-evaluation.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--attempt-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--validation-result-ref", default="")
    parser.add_argument("--execute-validation-commands", action="store_true")
    parser.add_argument("--command-policy-path", default=DEFAULT_COMMAND_POLICY_PATH)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--validate-patch-ref", action="store_true")
    args = parser.parse_args()
    try:
        code, report = evaluate_implementation_attempt(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            attempt_path=args.attempt_path,
            output_root=args.output_root,
            validation_result_ref=args.validation_result_ref,
            execute_validation_commands=args.execute_validation_commands,
            command_policy_path=args.command_policy_path,
            timeout_seconds=args.timeout_seconds,
            validate_patch_ref=args.validate_patch_ref,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
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
