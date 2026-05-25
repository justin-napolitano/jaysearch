from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_tools.materialize_selected_solution_scope import materialize_selected_solution_scope
from platform_tools.orchestrate_plan_selection import run_plan_selection_workflow
from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "orchestrate-research-plan-selection"
DEFAULT_OUTPUT_ROOT = Path("artifacts/orchestration/research-plan-selection-runs")


def run_research_plan_selection_workflow(
    *,
    root: str = ".",
    recommendation_path: str,
    plan_paths: list[str],
    selected_candidate_id: str | None = None,
    selection_reason: str | None = None,
    in_scope: list[str] | None = None,
    out_of_scope: list[str] | None = None,
    acceptance_checks: list[str] | None = None,
    plan_quality_policy_path: str = "spec/plan-quality-scoring.yaml",
    execution_materialization_policy_path: str = "spec/execution-materialization-policy.yaml",
    governance_intake: bool = False,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, object]]:
    repo_root = Path(root)
    run_root = repo_root / output_root
    run_root.mkdir(parents=True, exist_ok=True)
    step_reports: list[dict[str, object]] = []

    selection_code, selection_report = materialize_selected_solution_scope(
        root=root,
        recommendation_path=recommendation_path,
        output_root=output_root,
        selected_candidate_id=selected_candidate_id,
        selection_reason=selection_reason,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        acceptance_checks=acceptance_checks,
    )
    step_reports.append(
        {
            "step": "materialize_selected_solution_scope",
            "status": str(selection_report.get("status", "")).strip(),
            "ok": selection_report.get("ok") is True,
            "report": selection_report,
        }
    )
    if selection_code != 0 or selection_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "recommendation_path": recommendation_path,
                "candidate_plan_paths": plan_paths,
                "step_reports": step_reports,
                "blockers": selection_report.get("blockers", []),
            },
        )
        write_json(run_root / "research-plan-selection.report.json", report)
        return 1, report

    selected_scope_path = str(selection_report.get("selected_solution_scope_path", "")).strip()
    orchestration_code, orchestration_report = run_plan_selection_workflow(
        root=root,
        selected_scope_path=selected_scope_path,
        plan_paths=plan_paths,
        plan_quality_policy_path=plan_quality_policy_path,
        execution_materialization_policy_path=execution_materialization_policy_path,
        governance_intake=governance_intake,
        output_root=output_root,
    )
    step_reports.append(
        {
            "step": "orchestrate_plan_selection",
            "status": str(orchestration_report.get("status", "")).strip(),
            "ok": orchestration_report.get("ok") is True,
            "report": orchestration_report,
        }
    )
    if orchestration_code != 0 or orchestration_report.get("ok") is not True:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "recommendation_path": recommendation_path,
                "selected_solution_scope_path": selected_scope_path,
                "candidate_plan_paths": plan_paths,
                "step_reports": step_reports,
                "blockers": orchestration_report.get("blockers", []),
            },
        )
        write_json(run_root / "research-plan-selection.report.json", report)
        return 1, report

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "recommendation_path": recommendation_path,
            "selected_solution_scope_path": selected_scope_path,
            "candidate_plan_paths": plan_paths,
            "chosen_plan_ref": orchestration_report.get("chosen_plan_ref", ""),
            "execution_ready_plan_path": orchestration_report.get("execution_ready_plan_path", ""),
            "execution_packet_paths": orchestration_report.get("execution_packet_paths", []),
            "governance_report": orchestration_report.get("governance_report"),
            "step_reports": step_reports,
            "blockers": [],
        },
    )
    write_json(run_root / "research-plan-selection.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--recommendation-path", required=True)
    parser.add_argument("--plan", action="append", dest="plans", required=True)
    parser.add_argument("--selected-candidate-id", default=None)
    parser.add_argument("--selection-reason", default=None)
    parser.add_argument("--in-scope", action="append", default=[])
    parser.add_argument("--out-of-scope", action="append", default=[])
    parser.add_argument("--acceptance-check", action="append", default=[])
    parser.add_argument("--plan-quality-policy", default="spec/plan-quality-scoring.yaml")
    parser.add_argument("--execution-materialization-policy", default="spec/execution-materialization-policy.yaml")
    parser.add_argument("--governance-intake", action="store_true")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = run_research_plan_selection_workflow(
            root=args.root,
            recommendation_path=args.recommendation_path,
            plan_paths=args.plans,
            selected_candidate_id=args.selected_candidate_id,
            selection_reason=args.selection_reason,
            in_scope=args.in_scope,
            out_of_scope=args.out_of_scope,
            acceptance_checks=args.acceptance_check,
            plan_quality_policy_path=args.plan_quality_policy,
            execution_materialization_policy_path=args.execution_materialization_policy,
            governance_intake=args.governance_intake,
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
