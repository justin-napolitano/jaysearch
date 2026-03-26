from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.execplan_discovery import discover_execplan
from platform_tools.execplan_lint import validate_execplan
from platform_tools.governance_check import check_governance
from platform_tools.orchestrate_governed_slice import _effective_base_ref
from platform_tools.policy_compliance_check import _published_branch_rewrite_status, check_policy_compliance
from platform_tools.public_orchestration_api_check import check_public_orchestration_api
from platform_tools.remaining_work_graph_check import check_remaining_work_graph
from platform_tools.worker_runtime_artifact_check import check_worker_runtime_artifacts


COMMAND = "run-governed-pre-push-checks"


def _governed_branch(branch: str) -> bool:
    return branch.startswith(("draft-execplan/", "impl-execplan/", "initiative/", "hotfix/", "queue-execplan/"))


def run_governed_pre_push_checks(
    *,
    root: str = ".",
    branch: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    current_branch = branch or get_current_branch(root=root_path)
    if not _governed_branch(current_branch):
        report = {
            "command": COMMAND,
            "status": "skipped",
            "ok": True,
            "root": root_path.as_posix(),
            "branch": current_branch,
            "reason": "branch_not_governed",
            "checks": [],
            "blockers": [],
        }
        return 0, report

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    branch_policy = evaluate_branch_policy(current_branch, root=root_path)
    checks.append({"name": "branch_policy", "ok": branch_policy.get("ok", False), "findings": branch_policy.get("findings", [])})
    if not branch_policy.get("ok", False):
        blockers.extend(f"branch_policy:{item}" for item in branch_policy.get("findings", []))

    governance_code, governance_report = check_governance()
    checks.append({"name": "governance_check", "ok": governance_code == 0, "findings": governance_report.get("findings", [])})
    if governance_code != 0:
        blockers.extend(f"governance:{item}" for item in governance_report.get("findings", []))

    graph_code, graph_report = check_remaining_work_graph(root=root_path.as_posix(), branch=current_branch)
    checks.append({"name": "remaining_work_graph_check", "ok": graph_code == 0, "errors": graph_report.get("errors", [])})
    if graph_code != 0:
        blockers.extend(f"remaining_work_graph:{item}" for item in graph_report.get("errors", []))

    runtime_code, runtime_report = check_worker_runtime_artifacts(root=root_path.as_posix())
    checks.append({"name": "worker_runtime_artifact_check", "ok": runtime_code == 0, "errors": runtime_report.get("errors", [])})
    if runtime_code != 0:
        blockers.extend(f"worker_runtime_artifacts:{item}" for item in runtime_report.get("errors", []))

    public_api_code, public_api_report = check_public_orchestration_api(root=root_path.as_posix())
    checks.append({"name": "public_orchestration_api_check", "ok": public_api_code == 0, "errors": public_api_report.get("errors", [])})
    if public_api_code != 0:
        blockers.extend(f"public_orchestration_api:{item}" for item in public_api_report.get("errors", []))

    execplan_path = ""
    execplan_strategy = ""
    if current_branch.startswith(("draft-execplan/", "impl-execplan/")):
        selected_execplan, candidates, strategy = discover_execplan(root_path, current_branch, base_ref)
        execplan_strategy = strategy
        if selected_execplan is None:
            blockers.append(f"execplan_discovery:{strategy}")
            checks.append({"name": "execplan_discovery", "ok": False, "strategy": strategy, "candidates": candidates})
        else:
            execplan_path = selected_execplan.as_posix()
            lint_report = validate_execplan(selected_execplan)
            lint_ok = not lint_report["errors"]
            checks.append({"name": "execplan_validate", "ok": lint_ok, "path": execplan_path, "errors": lint_report["errors"]})
            if not lint_ok:
                blockers.extend(f"execplan_validate:{item}" for item in lint_report["errors"])

    if current_branch.startswith("impl-execplan/") and execplan_path:
        effective_base_ref = _effective_base_ref(
            repo_root=root_path,
            branch=current_branch,
            execplan_path=execplan_path,
            default_base_ref=base_ref,
        )
        rewrite_guard = _published_branch_rewrite_status(root_path, current_branch)
        if not rewrite_guard.get("published_ref_exists", False):
            checks.append(
                {
                    "name": "policy_compliance_check",
                    "ok": True,
                    "base_ref": effective_base_ref,
                    "status": "deferred_initial_publish",
                    "blockers": [],
                }
            )
            report = {
                "command": COMMAND,
                "status": "ok" if not blockers else "blocked",
                "ok": not blockers,
                "root": root_path.as_posix(),
                "branch": current_branch,
                "base_ref": base_ref,
                "execplan_path": execplan_path,
                "execplan_strategy": execplan_strategy,
                "checks": checks,
                "blockers": sorted(set(blockers)),
            }
            return (0 if not blockers else 1), report
        try:
            compliance_code, compliance_report = check_policy_compliance(
                root=root_path.as_posix(),
                execplan_path=execplan_path,
                base_ref=effective_base_ref,
            )
            checks.append(
                {
                    "name": "policy_compliance_check",
                    "ok": compliance_code == 0,
                    "base_ref": effective_base_ref,
                    "blockers": compliance_report.get("blockers", []),
                }
            )
            if compliance_code != 0:
                blockers.extend(f"policy_compliance:{item}" for item in compliance_report.get("blockers", []))
        except RuntimeError as exc:
            message = str(exc).strip()
            checks.append(
                {
                    "name": "policy_compliance_check",
                    "ok": False,
                    "base_ref": effective_base_ref,
                    "blockers": [message],
                }
            )
            blockers.append(f"policy_compliance:{message}")

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "root": root_path.as_posix(),
        "branch": current_branch,
        "base_ref": base_ref,
        "execplan_path": execplan_path,
        "execplan_strategy": execplan_strategy,
        "checks": checks,
        "blockers": sorted(set(blockers)),
    }
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("hook_args", nargs="*")
    args = parser.parse_args()
    code, report = run_governed_pre_push_checks(root=args.root, branch=args.branch, base_ref=args.base_ref)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
