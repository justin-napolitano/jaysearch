from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.execution_slice_materialization import materialize_execution_slices
from platform_tools.governance_execution_intake import validate_execution_intake
from platform_tools.plan_quality_score import compare_plans
from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "orchestrate-plan-selection"
DEFAULT_OUTPUT_ROOT = Path("artifacts/orchestration/plan-selection-runs")


def run_plan_selection_workflow(
    *,
    root: str = ".",
    selected_scope_path: str,
    plan_paths: list[str],
    plan_quality_policy_path: str = "spec/plan-quality-scoring.yaml",
    execution_materialization_policy_path: str = "spec/execution-materialization-policy.yaml",
    governance_intake: bool = False,
    evidence_refs: list[str] | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    run_root = repo_root / output_root
    run_root.mkdir(parents=True, exist_ok=True)

    step_reports: list[dict[str, Any]] = []
    evidence_list = sorted({ref for ref in (evidence_refs or []) if ref})

    comparison_report = compare_plans(
        root=root,
        selected_scope_path=selected_scope_path,
        plan_paths=plan_paths,
        policy_path=plan_quality_policy_path,
        evidence_refs=evidence_list,
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "plan_quality_score",
            "status": str(comparison_report.get("status", "")).strip(),
            "ok": comparison_report.get("ok") is True,
            "report": comparison_report,
        }
    )
    if comparison_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "selected_scope_path": selected_scope_path,
                "candidate_plan_paths": plan_paths,
                "step_reports": step_reports,
                "blockers": comparison_report.get("blockers", []),
            },
        )
        write_json(run_root / "plan-selection-orchestration.report.json", report)
        return 1, report

    chosen_plan_ref = str(comparison_report.get("recommended_plan_ref", "")).strip()
    if not chosen_plan_ref:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "selected_scope_path": selected_scope_path,
                "candidate_plan_paths": plan_paths,
                "step_reports": step_reports,
                "blockers": ["recommended_plan_ref_missing"],
            },
        )
        write_json(run_root / "plan-selection-orchestration.report.json", report)
        return 1, report

    materialization_code, materialization_report = materialize_execution_slices(
        root=root,
        selected_scope_path=selected_scope_path,
        chosen_plan_path=chosen_plan_ref,
        policy_path=execution_materialization_policy_path,
        evidence_refs=evidence_list,
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "execution_slice_materialization",
            "status": str(materialization_report.get("status", "")).strip(),
            "ok": materialization_report.get("ok") is True,
            "report": materialization_report,
        }
    )
    if materialization_code != 0 or materialization_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "selected_scope_path": selected_scope_path,
                "candidate_plan_paths": plan_paths,
                "chosen_plan_ref": chosen_plan_ref,
                "step_reports": step_reports,
                "blockers": materialization_report.get("blockers", []),
            },
        )
        write_json(run_root / "plan-selection-orchestration.report.json", report)
        return 1, report

    governance_report: dict[str, Any] | None = None
    if governance_intake:
        governance_code, governance_report = validate_execution_intake(
            root=root,
            execution_ready_plan_path=str(materialization_report.get("execution_ready_plan_path", "")).strip(),
            execution_packet_paths=[
                str(item).strip()
                for item in materialization_report.get("execution_packet_paths", [])
                if str(item).strip()
            ],
            output_root=output_root,
        )
        step_reports.append(
            {
                "step": "governance_execution_intake",
                "status": str(governance_report.get("status", "")).strip(),
                "ok": governance_report.get("ok") is True,
                "report": governance_report,
            }
        )
        if governance_code != 0 or governance_report.get("ok") is not True:
            report = envelope(
                command=COMMAND,
                status="blocked",
                ok=False,
                payload={
                    "selected_scope_path": selected_scope_path,
                    "candidate_plan_paths": plan_paths,
                    "chosen_plan_ref": chosen_plan_ref,
                    "comparison_report": comparison_report,
                    "execution_ready_plan_path": materialization_report.get("execution_ready_plan_path", ""),
                    "execution_packet_paths": materialization_report.get("execution_packet_paths", []),
                    "step_reports": step_reports,
                    "blockers": governance_report.get("blockers", []),
                },
            )
            write_json(run_root / "plan-selection-orchestration.report.json", report)
            return 1, report

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "selected_scope_path": selected_scope_path,
            "candidate_plan_paths": plan_paths,
            "chosen_plan_ref": chosen_plan_ref,
            "comparison_report": comparison_report,
            "execution_ready_plan_path": materialization_report.get("execution_ready_plan_path", ""),
            "execution_packet_paths": materialization_report.get("execution_packet_paths", []),
            "governance_report": governance_report,
            "step_reports": step_reports,
            "blockers": [],
        },
    )
    write_json(run_root / "plan-selection-orchestration.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selected-scope", required=True)
    parser.add_argument("--plan", action="append", dest="plans", required=True)
    parser.add_argument("--plan-quality-policy", default="spec/plan-quality-scoring.yaml")
    parser.add_argument("--execution-materialization-policy", default="spec/execution-materialization-policy.yaml")
    parser.add_argument("--governance-intake", action="store_true")
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = run_plan_selection_workflow(
            root=args.root,
            selected_scope_path=args.selected_scope,
            plan_paths=args.plans,
            plan_quality_policy_path=args.plan_quality_policy,
            execution_materialization_policy_path=args.execution_materialization_policy,
            governance_intake=args.governance_intake,
            evidence_refs=args.evidence_ref,
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
