from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.apply_solution_artifact import apply_solution_artifact
from platform_tools.emit_solution_artifact import emit_solution_artifact
from platform_tools.evaluate_implementation_attempt import (
    DEFAULT_COMMAND_POLICY_PATH,
    evaluate_implementation_attempt,
)
from platform_tools.generate_implementation_attempt import generate_implementation_attempt
from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json
from platform_tools.select_implementation_attempt import select_implementation_attempt


COMMAND = "run-execution-era-loop-smoke"
DEFAULT_OUTPUT_ROOT = Path("artifacts/execution-era-loop-smoke/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("eels-%Y%m%dT%H%M%SZ")


def _step_record(step: str, code: int, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": step,
        "status": str(report.get("status", "blocked")),
        "ok": code == 0 and bool(report.get("ok", False)),
        "report": report,
    }


def _blocked(
    *,
    repo_root: Path,
    run_root: Path,
    run_id: str,
    execution_unit_path: str,
    step_reports: list[dict[str, Any]],
    blockers: list[str],
) -> tuple[int, dict[str, Any]]:
    report = envelope(
        command=COMMAND,
        status="blocked",
        ok=False,
        payload={
            "run_id": run_id,
            "execution_unit_path": str((repo_root / execution_unit_path).resolve()),
            "attempt_packet_path": "",
            "attempt_evaluation_path": "",
            "solution_artifact_path": "",
            "step_reports": step_reports,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "execution-era-loop-smoke.report.json", report)
    return 1, report


def _validation_mode(
    *,
    execute_validation_commands: bool,
    validate_patch_ref: bool,
    validation_result_ref: str,
) -> str:
    modes: list[str] = []
    if execute_validation_commands:
        modes.append("command_execution")
    if validate_patch_ref:
        modes.append("patch_check")
    if validation_result_ref:
        modes.append("evidence_ref")
    return "+".join(modes) if modes else "metadata_only"


def run_execution_era_loop_smoke(
    *,
    root: str = ".",
    execution_unit_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    validation_result_ref: str = "",
    execute_validation_commands: bool = False,
    command_policy_path: str = DEFAULT_COMMAND_POLICY_PATH,
    timeout_seconds: int | None = None,
    patch_source_path: str = "",
    validate_patch: bool = False,
    validate_patch_ref: bool = False,
    apply_solution: bool = False,
    max_attempts: int = 1,
    candidate_patch_manifest_path: str = "",
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    step_root = f"{output_root}/{run_id}/steps"
    step_reports: list[dict[str, Any]] = []

    attempt_code, attempt_report = generate_implementation_attempt(
        root=root,
        execution_unit_path=execution_unit_path,
        output_root=step_root,
        patch_source_path=patch_source_path,
        validate_patch=validate_patch,
        max_attempts=max_attempts,
        candidate_patch_manifest_path=candidate_patch_manifest_path,
    )
    step_reports.append(_step_record("generate_implementation_attempt", attempt_code, attempt_report))
    if attempt_code != 0:
        return _blocked(
            repo_root=repo_root,
            run_root=run_root,
            run_id=run_id,
            execution_unit_path=execution_unit_path,
            step_reports=step_reports,
            blockers=[
                f"generate_implementation_attempt:{item}"
                for item in attempt_report.get("blockers", [])
            ],
        )

    attempt_paths = attempt_report.get("attempt_packet_paths", [])
    if not isinstance(attempt_paths, list) or not attempt_paths:
        return _blocked(
            repo_root=repo_root,
            run_root=run_root,
            run_id=run_id,
            execution_unit_path=execution_unit_path,
            step_reports=step_reports,
            blockers=["generate_implementation_attempt:attempt_packet_paths_missing"],
        )
    multi_attempt = len(attempt_paths) > 1
    attempt_path = str(attempt_paths[0])
    evaluation_path = ""
    evaluation_paths: list[str] = []
    attempt_selection_path = ""
    rejected_attempt_refs: list[str] = []
    for index, candidate_attempt_path in enumerate(attempt_paths, start=1):
        evaluation_code, evaluation_report = evaluate_implementation_attempt(
            root=root,
            execution_unit_path=execution_unit_path,
            attempt_path=str(candidate_attempt_path),
            output_root=step_root if not multi_attempt else f"{step_root}/evaluation-{index:02d}",
            validation_result_ref=validation_result_ref,
            execute_validation_commands=execute_validation_commands,
            command_policy_path=command_policy_path,
            timeout_seconds=timeout_seconds,
            validate_patch_ref=validate_patch_ref,
        )
        step_reports.append(
            _step_record(
                "evaluate_implementation_attempt"
                if not multi_attempt
                else f"evaluate_implementation_attempt_{index:02d}",
                evaluation_code,
                evaluation_report,
            )
        )
        candidate_evaluation_path = str(evaluation_report.get("attempt_evaluation_path", "")).strip()
        if not candidate_evaluation_path:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=["evaluate_implementation_attempt:attempt_evaluation_path_missing"],
            )
        evaluation_paths.append(candidate_evaluation_path)
        if evaluation_code != 0 and not multi_attempt:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=[
                    f"evaluate_implementation_attempt:{item}"
                    for item in evaluation_report.get("blockers", [])
                ],
            )

    evaluation_path = evaluation_paths[0]
    if multi_attempt:
        selection_code, selection_report = select_implementation_attempt(
            root=root,
            execution_unit_path=execution_unit_path,
            attempt_paths=[str(path) for path in attempt_paths],
            evaluation_paths=evaluation_paths,
            output_root=step_root,
        )
        step_reports.append(
            _step_record("select_implementation_attempt", selection_code, selection_report)
        )
        if selection_code != 0:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=[
                    f"select_implementation_attempt:{item}"
                    for item in selection_report.get("blockers", [])
                ],
            )
        attempt_selection_path = str(selection_report.get("attempt_selection_path", "")).strip()
        attempt_path = str(selection_report.get("selected_attempt_ref", "")).strip()
        evaluation_path = str(selection_report.get("selected_evaluation_ref", "")).strip()
        rejected_attempt_refs = [
            str(item) for item in selection_report.get("rejected_attempt_refs", [])
        ]
        if not attempt_path or not evaluation_path:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=["select_implementation_attempt:selected_refs_missing"],
            )

    solution_code, solution_report = emit_solution_artifact(
        root=root,
        execution_unit_path=execution_unit_path,
        attempt_path=attempt_path,
        evaluation_path=evaluation_path,
        output_root=step_root,
        rejected_attempt_refs=rejected_attempt_refs,
    )
    step_reports.append(_step_record("emit_solution_artifact", solution_code, solution_report))
    if solution_code != 0:
        return _blocked(
            repo_root=repo_root,
            run_root=run_root,
            run_id=run_id,
            execution_unit_path=execution_unit_path,
            step_reports=step_reports,
            blockers=[f"emit_solution_artifact:{item}" for item in solution_report.get("blockers", [])],
        )

    solution_path = str(solution_report.get("solution_artifact_path", "")).strip()
    applied_solution_path = ""
    if apply_solution:
        apply_code, apply_report = apply_solution_artifact(
            root=root,
            execution_unit_path=execution_unit_path,
            attempt_path=attempt_path,
            evaluation_path=evaluation_path,
            solution_artifact_path=solution_path,
            output_root=step_root,
            timeout_seconds=timeout_seconds or 60,
        )
        step_reports.append(_step_record("apply_solution_artifact", apply_code, apply_report))
        if apply_code != 0:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=[
                    f"apply_solution_artifact:{item}" for item in apply_report.get("blockers", [])
                ],
            )
        applied_solution_path = str(apply_report.get("applied_solution_path", "")).strip()
        if not applied_solution_path:
            return _blocked(
                repo_root=repo_root,
                run_root=run_root,
                run_id=run_id,
                execution_unit_path=execution_unit_path,
                step_reports=step_reports,
                blockers=["apply_solution_artifact:applied_solution_path_missing"],
            )

    explicitly_not_validated = [
        "autonomous code editing",
        "project node completion",
    ]
    if not multi_attempt:
        explicitly_not_validated.append("multi-attempt ranking")
    if not execute_validation_commands:
        explicitly_not_validated.append("direct validation command execution")
    if not validate_patch_ref:
        explicitly_not_validated.append("patch applicability validation")
    if not apply_solution:
        explicitly_not_validated.append("isolated solution application")
    validation_mode = _validation_mode(
        execute_validation_commands=execute_validation_commands,
        validate_patch_ref=validate_patch_ref,
        validation_result_ref=validation_result_ref,
    )

    smoke_packet = {
        "packet_type": "execution_era_loop_smoke_report",
        "packet_version": "v1",
        "packet_id": f"{run_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "run_id": run_id,
        "source_execution_unit_ref": str((repo_root / execution_unit_path).resolve()),
        "attempt_packet_ref": attempt_path,
        "attempt_evaluation_ref": evaluation_path,
        "attempt_selection_ref": attempt_selection_path,
        "candidate_patch_manifest_ref": candidate_patch_manifest_path,
        "solution_artifact_ref": solution_path,
        "applied_solution_ref": applied_solution_path,
        "step_reports": step_reports,
        "validated_scope": "execution_era_packet_loop_only",
        "validation_mode": validation_mode,
        "explicitly_not_validated": explicitly_not_validated,
    }
    smoke_packet_path = write_json(run_root / "execution-era-loop-smoke.packet.json", smoke_packet)

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "execution_unit_path": str((repo_root / execution_unit_path).resolve()),
            "attempt_packet_path": attempt_path,
            "attempt_packet_paths": [str(path) for path in attempt_paths],
            "attempt_evaluation_path": evaluation_path,
            "attempt_evaluation_paths": evaluation_paths,
            "attempt_selection_path": attempt_selection_path,
            "candidate_patch_manifest_path": candidate_patch_manifest_path,
            "solution_artifact_path": solution_path,
            "applied_solution_path": applied_solution_path,
            "smoke_packet_path": smoke_packet_path.as_posix(),
            "validation_mode": validation_mode,
            "step_reports": step_reports,
            "blockers": [],
        },
    )
    write_json(run_root / "execution-era-loop-smoke.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--validation-result-ref", default="")
    parser.add_argument("--execute-validation-commands", action="store_true")
    parser.add_argument("--command-policy-path", default=DEFAULT_COMMAND_POLICY_PATH)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--patch-source-path", default="")
    parser.add_argument("--validate-patch", action="store_true")
    parser.add_argument("--validate-patch-ref", action="store_true")
    parser.add_argument("--apply-solution", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=1)
    parser.add_argument("--candidate-patch-manifest-path", default="")
    args = parser.parse_args()
    try:
        code, report = run_execution_era_loop_smoke(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            output_root=args.output_root,
            validation_result_ref=args.validation_result_ref,
            execute_validation_commands=args.execute_validation_commands,
            command_policy_path=args.command_policy_path,
            timeout_seconds=args.timeout_seconds,
            patch_source_path=args.patch_source_path,
            validate_patch=args.validate_patch,
            validate_patch_ref=args.validate_patch_ref,
            apply_solution=args.apply_solution,
            max_attempts=args.max_attempts,
            candidate_patch_manifest_path=args.candidate_patch_manifest_path,
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
