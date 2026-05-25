from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "governance-execution-intake"
DEFAULT_OUTPUT_ROOT = Path("artifacts/governance/execution-intake-runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("gei-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _required_fields_present(payload: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if field not in payload or payload.get(field) in ("", None)]


def validate_execution_intake(
    *,
    root: str = ".",
    execution_ready_plan_path: str,
    execution_packet_paths: list[str],
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    execution_ready_plan = _load_json(repo_root / execution_ready_plan_path)
    execution_packets = [_load_json(repo_root / path) for path in execution_packet_paths]
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    warnings: list[str] = []
    required_plan_fields = [
        "packet_type",
        "packet_version",
        "packet_id",
        "created_at",
        "producer",
        "plan_id",
        "selected_solution_scope_ref",
        "source_structural_plan_ref",
        "plan_readiness",
        "execution_slices",
        "materialization_policy_ref",
        "materialization_warnings",
    ]
    missing_plan_fields = _required_fields_present(execution_ready_plan, required_plan_fields)
    blockers.extend(f"execution_ready_plan_missing_field:{field}" for field in missing_plan_fields)

    if str(execution_ready_plan.get("packet_type", "")).strip() != "execution_ready_plan_packet":
        blockers.append("execution_ready_plan_packet_type_invalid")
    if str(execution_ready_plan.get("plan_readiness", "")).strip() != "execution_ready":
        blockers.append("execution_ready_plan_readiness_invalid")

    slices = execution_ready_plan.get("execution_slices", [])
    if not isinstance(slices, list) or not slices:
        blockers.append("execution_ready_plan_missing_execution_slices")
        slices = []
    slice_ids = {
        str(item.get("execution_id", "")).strip()
        for item in slices
        if isinstance(item, dict) and str(item.get("execution_id", "")).strip()
    }

    if not execution_packets:
        blockers.append("execution_packets_missing")

    packet_ids: set[str] = set()
    for index, packet in enumerate(execution_packets, start=1):
        missing = _required_fields_present(
            packet,
            [
                "packet_type",
                "packet_version",
                "packet_id",
                "created_at",
                "producer",
                "execution_id",
                "node_id",
                "required_inputs",
                "expected_outputs",
                "validation_targets",
                "blocking_dependencies",
                "declared_ready_inputs",
                "conflict_domains",
                "completion_evidence_requirements",
                "runnable_preconditions",
            ],
        )
        blockers.extend(f"execution_packet_{index}_missing_field:{field}" for field in missing)
        if str(packet.get("packet_type", "")).strip() != "execution_packet":
            blockers.append(f"execution_packet_{index}_packet_type_invalid")
        execution_id = str(packet.get("execution_id", "")).strip()
        if execution_id:
            packet_ids.add(execution_id)
            if slice_ids and execution_id not in slice_ids:
                blockers.append(f"execution_packet_not_in_execution_ready_plan:{execution_id}")
        deps = packet.get("blocking_dependencies", [])
        if not isinstance(deps, list):
            blockers.append(f"execution_packet_{index}_blocking_dependencies_invalid")
            deps = []
        for dep in deps:
            dep_value = str(dep).strip()
            if dep_value and dep_value not in slice_ids:
                blockers.append(f"execution_packet_dependency_unknown:{execution_id}:{dep_value}")
        preconditions = packet.get("runnable_preconditions", [])
        if not isinstance(preconditions, list) or not preconditions:
            blockers.append(f"execution_packet_{index}_missing_runnable_preconditions")
        validation_targets = packet.get("validation_targets", [])
        if not isinstance(validation_targets, list) or not validation_targets:
            blockers.append(f"execution_packet_{index}_missing_validation_targets")
        evidence_requirements = packet.get("completion_evidence_requirements", [])
        if not isinstance(evidence_requirements, list) or not evidence_requirements:
            blockers.append(f"execution_packet_{index}_missing_completion_evidence_requirements")
        approvals = packet.get("required_approvals")
        if approvals is None:
            warnings.append(f"execution_packet_{index}_required_approvals_unspecified")

    if slice_ids and packet_ids != slice_ids:
        missing_packets = sorted(slice_ids - packet_ids)
        extra_packets = sorted(packet_ids - slice_ids)
        blockers.extend(f"missing_execution_packet_for_slice:{item}" for item in missing_packets)
        warnings.extend(f"extra_execution_packet_without_slice:{item}" for item in extra_packets)

    status = "approved" if not blockers else "blocked"
    decision_packet = {
        "packet_type": "governance_decision_packet",
        "packet_version": "v1",
        "packet_id": f"{run_id}:decision",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "decision_id": f"{run_id}:decision",
        "subject_ref": str((repo_root / execution_ready_plan_path).resolve()),
        "decision_type": "execution_intake_validation",
        "decision_status": status,
        "rationale": (
            "execution-ready plan and execution packets satisfy governance intake contract"
            if not blockers
            else "execution-ready handoff is incomplete or inconsistent"
        ),
        "blocker_refs": sorted(set(blockers)),
    }
    decision_path = write_json(run_root / "governance-decision.packet.json", decision_packet)

    report = envelope(
        command=COMMAND,
        status="ok" if not blockers else "blocked",
        ok=not blockers,
        payload={
            "run_id": run_id,
            "execution_ready_plan_path": str((repo_root / execution_ready_plan_path).resolve()),
            "execution_packet_paths": [str((repo_root / path).resolve()) for path in execution_packet_paths],
            "decision_packet_path": decision_path.as_posix(),
            "blockers": sorted(set(blockers)),
            "warnings": sorted(set(warnings)),
        },
    )
    write_json(run_root / "governance-execution-intake.report.json", report)
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-ready-plan", required=True)
    parser.add_argument("--execution-packet", action="append", dest="execution_packets", required=True)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = validate_execution_intake(
            root=args.root,
            execution_ready_plan_path=args.execution_ready_plan,
            execution_packet_paths=args.execution_packets,
            output_root=args.output_root,
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
