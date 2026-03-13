from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import get_current_branch
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.plan_utils import parse_plan
from platform_tools.policy_compliance_check import check_policy_compliance
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "hostile-review"
DEFAULT_REPORT_PATH = "artifacts/review/hostile-review-report.json"
DEFAULT_SUMMARY_PATH = "artifacts/review/hostile-review-summary.md"
DEFAULT_EVIDENCE_PATH = "artifacts/review/validation-evidence.json"
SPEC_PATH = "spec/games/hostile-review-game.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _validation_commands(plan_path: Path) -> list[str]:
    parsed = parse_plan(plan_path)
    validation = parsed.frontmatter.get("validation", {})
    tests = validation.get("tests", []) if isinstance(validation, dict) else []
    commands = []
    for item in tests:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command", "")).strip()
        if command:
            commands.append(command)
    return sorted(set(commands))


def _has_smoke_validation(commands: list[str]) -> bool:
    return any("smoke" in command for command in commands)


def _findings(
    *,
    branch: str,
    execplan_id: str,
    validation_commands: list[str],
    policy_report: dict[str, Any],
    remaining_report: dict[str, Any],
    merge_report: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    active_node = remaining_report.get("active_node") or {}
    ready_order = remaining_report.get("ordering", {}).get("ready_execplan_ids", [])
    queue_projection = remaining_report.get("queue_projection", {})

    if not policy_report.get("ok", False):
        findings.append(
            {
                "finding_id": "hostile-review-001-policy-compliance",
                "severity": "blocker",
                "title": "Policy compliance must pass before hostile review can attest clean state",
                "summary": "The implementation branch is not yet legal under policy compliance, so hostile review cannot advance beyond recovery guidance.",
                "details": sorted(str(item) for item in policy_report.get("blockers", [])),
                "evidence_refs": sorted(
                    {
                        ".agent/execplans/" + execplan_id + ".md",
                        "artifacts/planner/research/remaining-work-graph.json",
                        "docs/queued-execplans.md",
                    }
                ),
            }
        )

    if not active_node:
        findings.append(
            {
                "finding_id": "hostile-review-002-active-node-missing",
                "severity": "blocker",
                "title": "No active remaining-work node was selected for hostile review",
                "summary": "Hostile review requires an active node bound to the current ExecPlan or implementation branch.",
                "details": [],
                "evidence_refs": ["artifacts/planner/research/remaining-work-graph.json"],
            }
        )
    else:
        if str(active_node.get("target_execplan_id", "")).strip() != execplan_id:
            findings.append(
                {
                    "finding_id": "hostile-review-003-active-node-mismatch",
                    "severity": "blocker",
                    "title": "The active remaining-work node does not match the reviewed ExecPlan",
                    "summary": "Hostile review cannot claim findings for a different backlog node than the active ExecPlan.",
                    "details": [
                        f"branch={branch}",
                        f"active_node={active_node.get('node_id', '')}",
                        f"target_execplan_id={active_node.get('target_execplan_id', '')}",
                    ],
                    "evidence_refs": ["artifacts/planner/research/remaining-work-graph.json"],
                }
            )
        if str(active_node.get("status", "")).strip() != "ready":
            findings.append(
                {
                    "finding_id": "hostile-review-004-active-node-not-ready",
                    "severity": "blocker",
                    "title": "Hostile review was invoked before the active slice reached ready state",
                    "summary": "The review runtime only attests governed work that is canonically ready on the local graph.",
                    "details": [f"status={active_node.get('status', '')}"],
                    "evidence_refs": ["artifacts/planner/research/remaining-work-graph.json"],
                }
            )
        if str(active_node.get("implementation_branch", "")).strip() != branch:
            findings.append(
                {
                    "finding_id": "hostile-review-005-branch-mismatch",
                    "severity": "blocker",
                    "title": "The active node points at a different implementation branch",
                    "summary": "Review findings must stay attached to the canonical branch recorded on the local remaining-work graph.",
                    "details": [
                        f"expected_branch={active_node.get('implementation_branch', '')}",
                        f"current_branch={branch}",
                    ],
                    "evidence_refs": [
                        "artifacts/planner/research/remaining-work-graph.json",
                        "docs/queued-execplans.md",
                    ],
                }
            )

    if execplan_id not in ready_order:
        findings.append(
            {
                "finding_id": "hostile-review-006-ready-order-missing",
                "severity": "blocker",
                "title": "The reviewed ExecPlan is missing from canonical ready order",
                "summary": "Hostile review should only operate on work that has deterministic ready-order evidence in the local graph projection.",
                "details": [f"ready_order={','.join(str(item) for item in ready_order)}"],
                "evidence_refs": [
                    "artifacts/planner/research/remaining-work-graph.json",
                    "docs/queued-execplans.md",
                ],
            }
        )

    if str(queue_projection.get("projection_authority", "")).strip() != "projection_only":
        findings.append(
            {
                "finding_id": "hostile-review-007-projection-authority-drift",
                "severity": "blocker",
                "title": "A projection surface appears to have gained authority",
                "summary": "Hostile review must fail closed if queue or board projection authority drifts away from local canonical state.",
                "details": [f"projection_authority={queue_projection.get('projection_authority', '')}"],
                "evidence_refs": ["artifacts/planner/research/remaining-work-graph.json"],
            }
        )

    if not _has_smoke_validation(validation_commands):
        findings.append(
            {
                "finding_id": "hostile-review-008-smoke-missing",
                "severity": "blocker",
                "title": "The active ExecPlan does not define a dedicated smoke command",
                "summary": "Implementation slices must carry one-command smoke coverage before hostile review can attest merge-readiness evidence.",
                "details": validation_commands,
                "evidence_refs": [".agent/execplans/" + execplan_id + ".md"],
            }
        )

    if not merge_report.get("readiness", False):
        findings.append(
            {
                "finding_id": "hostile-review-009-merge-readiness-pending",
                "severity": "warning",
                "title": "Merge readiness is not yet satisfied",
                "summary": "Human finalization should remain blocked until the required validation commands have been run and the branch is merge-ready.",
                "details": sorted(str(item) for item in merge_report.get("failing_checks", [])),
                "evidence_refs": sorted({".agent/execplans/" + execplan_id + ".md", "docs/merge-readiness-contract.md"}),
            }
        )

    if not findings:
        findings.append(
            {
                "finding_id": "hostile-review-010-clean-attestation",
                "severity": "info",
                "title": "Hostile review found no recovery-triggering issues in current canonical state",
                "summary": "The branch is policy-compliant, canonically selected, and retains human final authority for the eventual merge decision.",
                "details": [],
                "evidence_refs": sorted(
                    {
                        ".agent/execplans/" + execplan_id + ".md",
                        "artifacts/planner/research/remaining-work-graph.json",
                        "docs/queued-execplans.md",
                    }
                ),
            }
        )

    return findings


def _summary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Hostile Review Summary",
        "",
        f"- execplan: `{report['execplan_id']}`",
        f"- branch: `{report['branch']}`",
        f"- review_state: `{report['review_state']}`",
        f"- blocker_count: `{report['finding_counts']['blocker']}`",
        f"- warning_count: `{report['finding_counts']['warning']}`",
        f"- info_count: `{report['finding_counts']['info']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in report["findings"]:
        lines.append(f"- `{finding['severity']}` `{finding['finding_id']}`: {finding['title']}")
        lines.append(f"  - {finding['summary']}")
    return "\n".join(lines) + "\n"


def load_hostile_review_state(
    *,
    root: str = ".",
    target_execplan_id: str,
    implementation_branch: str = "",
    current_branch: str = "",
    node_status: str = "",
) -> dict[str, Any]:
    report_path = Path(root) / DEFAULT_REPORT_PATH
    if report_path.exists():
        loaded = json.loads(report_path.read_text(encoding="utf-8"))
        if str(loaded.get("execplan_id", "")).strip() == target_execplan_id:
            return {
                "state": str(loaded.get("review_state", "")).strip() or "pending",
                "report_path": report_path.as_posix(),
                "blocker_count": int(loaded.get("finding_counts", {}).get("blocker", 0)),
                "warning_count": int(loaded.get("finding_counts", {}).get("warning", 0)),
                "ok": bool(loaded.get("ok", False)),
            }
    if node_status == "completed":
        state = "merged"
    elif implementation_branch and implementation_branch == current_branch:
        state = "pending"
    elif node_status in {"ready", "review_gated"}:
        state = "not_started"
    else:
        state = "not_applicable"
    return {
        "state": state,
        "report_path": report_path.as_posix() if report_path.exists() else "",
        "blocker_count": 0,
        "warning_count": 0,
        "ok": state in {"merged", "clean"},
    }


def run_hostile_review(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    write_artifacts: bool = True,
    report_path: str = DEFAULT_REPORT_PATH,
    summary_path: str = DEFAULT_SUMMARY_PATH,
    evidence_path: str = DEFAULT_EVIDENCE_PATH,
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    current_branch = branch or get_current_branch()
    if execplan_path is None:
        raise ValueError("execplan_path_required")
    plan_path = Path(execplan_path)
    parsed = parse_plan(plan_path)
    execplan_id = str(parsed.frontmatter.get("id", "")).strip()
    validation_commands = _validation_commands(plan_path)
    spec = _load_yaml(cwd / SPEC_PATH)

    _, remaining_report = check_remaining_work_graph(
        root=root,
        branch=current_branch,
        execplan_path=plan_path.as_posix(),
    )
    _, policy_report = check_policy_compliance(root=root, execplan_path=plan_path.as_posix())
    _, merge_report = check_merge_readiness(
        root=root,
        execplan_path=plan_path.as_posix(),
        include_validation_runs=False,
    )

    findings = _findings(
        branch=current_branch,
        execplan_id=execplan_id,
        validation_commands=validation_commands,
        policy_report=policy_report,
        remaining_report=remaining_report,
        merge_report=merge_report,
    )
    counts = {
        "blocker": sum(1 for item in findings if item["severity"] == "blocker"),
        "warning": sum(1 for item in findings if item["severity"] == "warning"),
        "info": sum(1 for item in findings if item["severity"] == "info"),
    }
    review_state = "recovery_required" if counts["blocker"] else "clean"
    ok = counts["blocker"] == 0

    report = {
        "command": COMMAND,
        "status": "ok" if ok else "blocked",
        "ok": ok,
        "branch": current_branch,
        "execplan_id": execplan_id,
        "execplan_path": plan_path.as_posix(),
        "review_game": {
          "game_id": str(spec.get("game_id", "")).strip(),
          "parent_game": str(spec.get("parent_game", "")).strip(),
          "layer": str(spec.get("layer", "")).strip(),
          "objective": str(spec.get("objective", "")).strip(),
        },
        "review_state": review_state,
        "finding_counts": counts,
        "findings": findings,
        "active_node": remaining_report.get("active_node"),
        "ready_order": remaining_report.get("ordering", {}).get("ready_execplan_ids", []),
        "validation_commands": validation_commands,
        "policy_compliance": {
            "status": policy_report.get("status", ""),
            "ok": bool(policy_report.get("ok", False)),
            "blockers": [str(item) for item in policy_report.get("blockers", [])],
        },
        "merge_readiness": {
            "readiness": bool(merge_report.get("readiness", False)),
            "failing_checks": [str(item) for item in merge_report.get("failing_checks", [])],
            "validation_commands": [
                str(item.get("command", "")).strip()
                for item in merge_report.get("checks", {}).get("validations", [])
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            ],
        },
        "artifacts": {
            "report_path": (cwd / report_path).as_posix(),
            "summary_path": (cwd / summary_path).as_posix(),
            "evidence_path": (cwd / evidence_path).as_posix(),
        },
        "evidence_refs": sorted(
            {
                plan_path.as_posix(),
                "artifacts/planner/research/remaining-work-graph.json",
                "docs/queued-execplans.md",
                "docs/merge-readiness-contract.md",
                SPEC_PATH,
            }
        ),
    }
    validation_evidence = {
        "command": "hostile-review-validation-evidence",
        "execplan_id": execplan_id,
        "branch": current_branch,
        "checks": [
            {
                "name": "policy-compliance-check",
                "status": policy_report.get("status", ""),
                "ok": bool(policy_report.get("ok", False)),
                "blockers": [str(item) for item in policy_report.get("blockers", [])],
            },
            {
                "name": "remaining-work-graph-check",
                "status": remaining_report.get("status", ""),
                "ok": bool(remaining_report.get("ok", False)),
                "blockers": [str(item) for item in remaining_report.get("errors", [])],
            },
            {
                "name": "merge-readiness-check",
                "status": "ok" if merge_report.get("readiness", False) else "blocked",
                "ok": bool(merge_report.get("readiness", False)),
                "blockers": [str(item) for item in merge_report.get("failing_checks", [])],
            },
        ],
        "evidence_refs": report["evidence_refs"],
    }

    if write_artifacts:
        _write_json(cwd / report_path, report)
        _write_json(cwd / evidence_path, validation_evidence)
        _write_text(cwd / summary_path, _summary_markdown(report))

    return (0 if ok else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", required=True)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    code, report = run_hostile_review(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        write_artifacts=not args.no_write,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
