from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "generate-implementation-attempt"
DEFAULT_OUTPUT_ROOT = Path("artifacts/implementation-attempts/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("gia-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _slug(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in normalized.split("-") if part)[:80] or "attempt"


def _required_fields_present(payload: dict[str, Any], fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        value = payload.get(field)
        if field not in payload or value in ("", None) or (isinstance(value, list) and not value):
            missing.append(field)
    return missing


def _run_patch_check(*, repo_root: Path, patch_path: Path, run_root: Path) -> tuple[dict[str, Any], str]:
    started = time.monotonic()
    completed = subprocess.run(
        ["git", "apply", "--check", patch_path.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    result = {
        "command": f"git apply --check {patch_path.as_posix()}",
        "status": "passed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_tail": completed.stdout[-12000:],
        "stderr_tail": completed.stderr[-12000:],
        "patch_ref": patch_path.as_posix(),
    }
    result_path = write_json(run_root / "patch-validation.result.json", result)
    return result, result_path.as_posix()


def generate_implementation_attempt(
    *,
    root: str = ".",
    execution_unit_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    attempt_family: str = "baseline_reference",
    max_attempts: int = 1,
    patch_source_path: str = "",
    validate_patch: bool = False,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if max_attempts < 1:
        blockers.append("max_attempts_invalid")
    patch_source: Path | None = None
    if patch_source_path:
        patch_source = repo_root / patch_source_path
        if not patch_source.exists():
            blockers.append("patch_source_path_missing")
        elif not patch_source.is_file():
            blockers.append("patch_source_path_not_file")

    required = [
        "execution_unit_id",
        "implementation_intent",
        "owned_changes",
        "validation_commands",
        "rollback_plan",
        "completion_evidence_requirements",
    ]
    missing = _required_fields_present(execution_unit, required)
    blockers.extend(f"execution_unit_missing_field:{field}" for field in missing)

    owned_changes = _string_list(execution_unit.get("owned_changes", []))
    validation_commands = _string_list(execution_unit.get("validation_commands", []))
    if not owned_changes:
        blockers.append("execution_unit_missing_owned_changes")
    if not validation_commands:
        blockers.append("execution_unit_missing_validation_commands")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "run_id": run_id,
                "execution_unit_path": str((repo_root / execution_unit_path).resolve()),
                "attempt_packet_paths": [],
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "implementation-attempt-generation.report.json", report)
        return 1, report

    execution_unit_id = str(execution_unit["execution_unit_id"]).strip()
    source_ref = str((repo_root / execution_unit_path).resolve())
    attempt_paths: list[str] = []
    patch_validation_refs: list[str] = []
    for index in range(1, max_attempts + 1):
        attempt_id = f"attempt:{_slug(execution_unit_id)}:{index:03d}"
        patch_ref = ""
        if patch_source is not None:
            patch_target = run_root / f"implementation-attempt-{index:02d}.patch"
            shutil.copyfile(patch_source, patch_target)
            patch_ref = patch_target.as_posix()
            if validate_patch:
                patch_result, patch_validation_ref = _run_patch_check(
                    repo_root=repo_root,
                    patch_path=patch_target,
                    run_root=run_root,
                )
                patch_validation_refs.append(patch_validation_ref)
                if patch_result["status"] != "passed":
                    report = envelope(
                        command=COMMAND,
                        status="blocked",
                        ok=False,
                        payload={
                            "run_id": run_id,
                            "execution_unit_path": source_ref,
                            "attempt_packet_paths": [],
                            "patch_validation_refs": patch_validation_refs,
                            "blockers": ["patch_validation_failed"],
                        },
                    )
                    write_json(run_root / "implementation-attempt-generation.report.json", report)
                    return 1, report
        attempt = {
            "packet_type": "implementation_attempt",
            "packet_version": "v1",
            "packet_id": f"{attempt_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "attempt_id": attempt_id,
            "source_execution_unit_ref": source_ref,
            "attempt_family": attempt_family,
            "implementation_summary": (
                "Non-mutating implementation attempt scaffold generated from execution unit "
                f"{execution_unit_id}."
            ),
            "changed_artifact_refs": owned_changes,
            "patch_ref": patch_ref,
            "validation_command_refs": validation_commands,
            "assumptions": _string_list(execution_unit.get("required_inputs", [])),
            "risks": _string_list(execution_unit.get("non_goals", [])),
            "status": "draft",
            "created_by": COMMAND,
        }
        attempt_path = write_json(
            run_root / f"implementation-attempt-{index:02d}.packet.json",
            attempt,
        )
        attempt_paths.append(attempt_path.as_posix())

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "execution_unit_path": source_ref,
            "attempt_packet_paths": attempt_paths,
            "attempt_count": len(attempt_paths),
            "patch_validation_refs": patch_validation_refs,
            "blockers": [],
        },
    )
    write_json(run_root / "implementation-attempt-generation.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--attempt-family", default="baseline_reference")
    parser.add_argument("--max-attempts", type=int, default=1)
    parser.add_argument("--patch-source-path", default="")
    parser.add_argument("--validate-patch", action="store_true")
    args = parser.parse_args()
    try:
        code, report = generate_implementation_attempt(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            output_root=args.output_root,
            attempt_family=args.attempt_family,
            max_attempts=args.max_attempts,
            patch_source_path=args.patch_source_path,
            validate_patch=args.validate_patch,
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
