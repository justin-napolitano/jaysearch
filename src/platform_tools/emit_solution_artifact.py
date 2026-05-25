from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "emit-solution-artifact"
DEFAULT_OUTPUT_ROOT = Path("artifacts/solution-artifacts/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("saf-%Y%m%dT%H%M%SZ")


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
        if field not in payload or value is None:
            missing.append(field)
    return missing


def emit_solution_artifact(
    *,
    root: str = ".",
    execution_unit_path: str,
    attempt_path: str,
    evaluation_path: str,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
    rejected_attempt_refs: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_unit = _load_json(repo_root / execution_unit_path)
    attempt = _load_json(repo_root / attempt_path)
    evaluation = _load_json(repo_root / evaluation_path)
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(execution_unit.get("packet_type", "")).strip() != "execution_unit":
        blockers.append("execution_unit_packet_type_invalid")
    if str(attempt.get("packet_type", "")).strip() != "implementation_attempt":
        blockers.append("implementation_attempt_packet_type_invalid")
    if str(evaluation.get("packet_type", "")).strip() != "attempt_evaluation":
        blockers.append("attempt_evaluation_packet_type_invalid")

    blockers.extend(
        f"execution_unit_missing_field:{field}"
        for field in _required_fields_present(
            execution_unit,
            ["execution_unit_id", "completion_evidence_requirements"],
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
            [
                "evaluation_id",
                "source_attempt_ref",
                "source_execution_unit_ref",
                "promotion_status",
                "blockers",
                "evidence_refs",
            ],
        )
    )

    execution_ref = str((repo_root / execution_unit_path).resolve())
    attempt_ref = str((repo_root / attempt_path).resolve())
    evaluation_ref = str((repo_root / evaluation_path).resolve())
    if str(attempt.get("source_execution_unit_ref", "")).strip() != execution_ref:
        blockers.append("attempt_source_execution_unit_ref_mismatch")
    if str(evaluation.get("source_execution_unit_ref", "")).strip() != execution_ref:
        blockers.append("evaluation_source_execution_unit_ref_mismatch")
    if str(evaluation.get("source_attempt_ref", "")).strip() != attempt_ref:
        blockers.append("evaluation_source_attempt_ref_mismatch")

    evaluation_blockers = _string_list(evaluation.get("blockers", []))
    blockers.extend(f"evaluation_blocker:{item}" for item in evaluation_blockers)
    if str(evaluation.get("promotion_status", "")).strip() != "promoted":
        blockers.append("attempt_evaluation_not_promoted")

    completion_evidence_refs = _string_list(evaluation.get("evidence_refs", []))
    if not completion_evidence_refs:
        blockers.append("solution_missing_completion_evidence_refs")

    emitted_path = ""
    if not blockers:
        solution_artifact_id = (
            f"solution-artifact:{str(execution_unit.get('execution_unit_id', 'execution')).replace(':', '-')}"
        )
        solution = {
            "packet_type": "solution_artifact",
            "packet_version": "v1",
            "packet_id": f"{solution_artifact_id}:packet",
            "created_at": _utc_now(),
            "producer": COMMAND,
            "solution_artifact_id": solution_artifact_id,
            "source_execution_unit_ref": execution_ref,
            "selected_attempt_ref": attempt_ref,
            "evaluation_ref": evaluation_ref,
            "artifact_refs": _string_list(attempt.get("changed_artifact_refs", [])),
            "patch_ref": str(attempt.get("patch_ref", "")).strip(),
            "completion_evidence_refs": completion_evidence_refs,
            "validation_summary": "Promoted attempt evaluation selected for solution artifact.",
            "known_limitations": _string_list(evaluation.get("review_findings", [])),
            "follow_up_problem_node_refs": [],
            "rejected_attempt_refs": rejected_attempt_refs or [],
        }
        emitted_path = write_json(run_root / "solution-artifact.packet.json", solution).as_posix()

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_unit_path": execution_ref,
            "attempt_path": attempt_ref,
            "evaluation_path": evaluation_ref,
            "solution_artifact_path": emitted_path,
            "blockers": sorted(set(blockers)),
        },
    )
    write_json(run_root / "solution-artifact.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-unit-path", required=True)
    parser.add_argument("--attempt-path", required=True)
    parser.add_argument("--evaluation-path", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    parser.add_argument("--rejected-attempt-ref", action="append", default=[])
    args = parser.parse_args()
    try:
        code, report = emit_solution_artifact(
            root=args.root,
            execution_unit_path=args.execution_unit_path,
            attempt_path=args.attempt_path,
            evaluation_path=args.evaluation_path,
            output_root=args.output_root,
            rejected_attempt_refs=args.rejected_attempt_ref,
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
