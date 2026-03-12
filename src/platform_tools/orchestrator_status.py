from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.citation_check import check_citations
from platform_tools.game_status import get_game_status
from platform_tools.human_operations_status import get_human_operations_status
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.plan_utils import parse_plan
from platform_tools.planner_score import score_graph
from platform_tools.policy_compliance_check import check_policy_compliance
from platform_tools.remaining_work_graph_check import check_remaining_work_graph
from platform_tools.rule_graph_check import check_rule_graph


COMMAND = "orchestrator-status"


def _adapt_contract(
    *,
    command: str,
    ok: bool,
    blockers: list[str],
    payload: dict[str, Any],
    next_validations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "command": command,
        "status": "ok" if ok else "blocked",
        "blockers": sorted(set(blockers)),
        "next_validations": sorted(set(next_validations or [])),
        "ok": ok,
        "payload": payload,
    }


def _planner_score_surface(root: Path, graph_id: str | None) -> dict[str, Any]:
    if not graph_id:
        return {
            "command": "planner-score",
            "status": "deferred",
            "blockers": ["planner_graph_id_required"],
            "next_validations": [],
            "ok": False,
            "payload": {},
        }
    try:
        report = score_graph(root=root.as_posix(), graph_id=graph_id)
        return {
            "command": report["command"],
            "status": report["status"],
            "blockers": report["blockers"],
            "next_validations": report["next_validations"],
            "ok": bool(report["ok"]),
            "payload": report,
        }
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        return {
            "command": "planner-score",
            "status": "blocked",
            "blockers": [f"{exc.__class__.__name__}:{exc}"],
            "next_validations": [],
            "ok": False,
            "payload": {},
        }


def get_orchestrator_status(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
    planner_graph_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    current_branch = branch or ""
    game_code, game_report = get_game_status(
        root=root,
        branch=current_branch or None,
        execplan_path=execplan_path,
        base_ref=base_ref,
    )
    current_branch = str(game_report.get("branch", current_branch)).strip()
    remaining_work_code, remaining_work_report = check_remaining_work_graph(
        root=root,
        branch=current_branch or None,
        execplan_path=execplan_path,
    )
    active_work = remaining_work_report.get("active_node")
    ready_work = remaining_work_report.get("ready_nodes", [])
    blocked_work = remaining_work_report.get("blocked_nodes", [])

    _, rule_report = check_rule_graph(root)
    _, citation_report = check_citations(root)
    _, policy_report = check_policy_compliance(
        root=root,
        execplan_path=execplan_path,
        base_ref=base_ref,
    )
    _, merge_report = check_merge_readiness(
        root=root,
        execplan_path=execplan_path,
        base_ref=base_ref,
        include_validation_runs=False,
    )
    _, human_operations_report = get_human_operations_status(
        root=root,
        branch=current_branch or None,
        execplan_path=execplan_path,
    )
    score_surface = _planner_score_surface(cwd, planner_graph_id)

    checks = {
        "remaining_work_graph": _adapt_contract(
            command="remaining-work-graph-check",
            ok=remaining_work_code == 0,
            blockers=[str(item) for item in remaining_work_report.get("errors", [])],
            payload=remaining_work_report,
        ),
        "rule_graph": _adapt_contract(
            command="rule-graph-check",
            ok=bool(rule_report.get("ok", False)),
            blockers=[str(item) for item in rule_report.get("blockers", [])],
            payload=rule_report,
        ),
        "citation": _adapt_contract(
            command="citation-check",
            ok=bool(citation_report.get("ok", False)),
            blockers=[str(item) for item in citation_report.get("blockers", [])],
            payload=citation_report,
        ),
        "policy_compliance": _adapt_contract(
            command="policy-compliance-check",
            ok=bool(policy_report.get("ok", False)),
            blockers=[str(item) for item in policy_report.get("blockers", [])],
            payload=policy_report,
        ),
        "game_status": _adapt_contract(
            command="game-status",
            ok=game_code == 0,
            blockers=[str(item) for item in game_report.get("blockers", [])],
            payload=game_report,
        ),
        "merge_readiness": _adapt_contract(
            command="merge-readiness-check",
            ok=bool(merge_report.get("readiness", False)),
            blockers=[str(item) for item in merge_report.get("failing_checks", [])],
            payload=merge_report,
            next_validations=[
                str(item.get("command", "")).strip()
                for item in merge_report.get("checks", {}).get("validations", [])
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            ],
        ),
        "human_operations": _adapt_contract(
            command="human-operations-status",
            ok=bool(human_operations_report.get("ok", False)),
            blockers=[str(item) for item in human_operations_report.get("blockers", [])],
            payload=human_operations_report,
        ),
        "planner_score": score_surface,
    }

    blockers: list[str] = []
    for check_name, check_report in checks.items():
        if check_report["status"] == "blocked":
            blockers.extend(f"{check_name}:{item}" for item in check_report["blockers"])
    if active_work and str(active_work.get("status", "")).strip() != "ready":
        blockers.append(f"active_work_not_ready:{active_work['node_id']}:{active_work['status']}")
    if active_work and bool(active_work.get("action_state", {}).get("action_required", False)):
        blockers.append(f"active_work_requires_graph_action:{active_work['node_id']}")

    next_validations = [
        "bin/execplan-validate .agent/execplans/20260311-composite-orchestrator-status-codex-01-execplan.md"
    ]
    if execplan_path:
        parsed = parse_plan(Path(execplan_path))
        validation = parsed.frontmatter.get("validation", {})
        tests = validation.get("tests", []) if isinstance(validation, dict) else []
        next_validations = sorted(
            set(
                str(item.get("command", "")).strip()
                for item in tests
                if isinstance(item, dict) and str(item.get("command", "")).strip()
            )
        )

    next_actions: list[dict[str, str]] = []
    if blockers:
        next_actions.append({"action": "resolve_blockers", "reason": "status_blocked"})
    elif active_work:
        next_actions.append(
            {
                "action": "continue_active_slice",
                "execplan_id": active_work["target_execplan_id"],
                "branch": active_work["implementation_branch"] or current_branch,
                "reason": "active_ready_slice_detected",
            }
        )
    elif ready_work:
        first_ready = ready_work[0]
        next_actions.append(
            {
                "action": "start_ready_slice",
                "execplan_id": first_ready["target_execplan_id"],
                "branch": first_ready["implementation_branch"],
                "reason": "ready_remaining_work",
            }
        )
    else:
        next_actions.append({"action": "wait_for_ready_work", "reason": "no_ready_nodes"})

    authority_constraints = sorted(
        {
            "human_review_required",
            "execplan_finalization_required",
            "signed_merge_commit_required",
            "board_review_projection_only",
            "takeover_state_must_be_machine_readable",
        }
    )
    evidence_refs = sorted(
        {
            "artifacts/planner/research/remaining-work-graph.json",
            "artifacts/planner/research/rule-graph.json",
            "artifacts/planner/research/bibliography-graph.json",
            "artifacts/planner/research/claim-registry.json",
            "artifacts/planner/research/game-graph.json",
            "artifacts/provider-sync/github-projects-field-map.json",
            "docs/codex-orchestrator-contract.md",
            "docs/merge-readiness-contract.md",
        }
    )

    ok = not blockers
    report = {
        "command": COMMAND,
        "status": "ok" if ok else "blocked",
        "blockers": sorted(set(blockers)),
        "next_validations": next_validations,
        "ok": ok,
        "branch": current_branch,
        "active_execplan": game_report.get("active_execplan"),
        "active_game": game_report.get("active_game"),
        "active_work": active_work,
        "ready_work": ready_work,
        "blocked_work": blocked_work,
        "ready_order": remaining_work_report.get("ordering", {}).get("ready_execplan_ids", []),
        "queue_projection": remaining_work_report.get("queue_projection", {}),
        "action_required_nodes": remaining_work_report.get("action_required_nodes", []),
        "authority_constraints": authority_constraints,
        "next_actions": next_actions,
        "checks": checks,
        "evidence_refs": evidence_refs,
    }
    return (1 if not ok else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--planner-graph-id", default=None)
    args = parser.parse_args()
    code, report = get_orchestrator_status(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
        planner_graph_id=args.planner_graph_id,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
