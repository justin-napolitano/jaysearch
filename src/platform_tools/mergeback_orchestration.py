from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.plan_utils import parse_plan


API_VERSION = "mergeback-orchestration.v1"
ALLOWED_VALIDATIONS = {
    "bin/merge-readiness-check",
    "bin/execplan-validate",
    "bin/remaining-work-graph-check",
    "bin/policy-compliance-check",
}


def envelope(*, command: str, status: str, ok: bool, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "api_version": API_VERSION,
        "command": command,
        "status": status,
        "ok": ok,
    }
    if payload:
        body.update(payload)
    return body


def _load_graph(root: Path) -> dict[str, Any]:
    graph_path = root / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    return json.loads(graph_path.read_text(encoding="utf-8"))


def _execplan_path_from_id(root: Path, execplan_id: str) -> Path | None:
    if not execplan_id:
        return None
    execplan_dir = root / ".agent" / "execplans"
    if not execplan_dir.exists():
        return None
    for path in sorted(execplan_dir.glob("*.md")):
        try:
            parsed = parse_plan(path)
        except Exception:
            continue
        if str(parsed.frontmatter.get("id", "")).strip() == execplan_id:
            return path
    return None


def resolve_mergeback_context(
    *,
    root: str = ".",
    source_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    root_path = Path(root).resolve()
    resolved_source = (source_branch or "").strip() or get_current_branch(root=root_path)
    resolved_initiative = (initiative_branch or "").strip()
    resolved_execplan_id = (execplan_id or "").strip()

    if not resolved_source.startswith("impl-execplan/"):
        return ["source_branch_role_invalid"], {
            "source_branch": resolved_source,
            "source_branch_role": "unknown",
        }

    graph = _load_graph(root_path)
    nodes = graph.get("nodes", [])
    matches = [
        node
        for node in nodes
        if isinstance(node, dict) and str(node.get("implementation_branch", "")).strip() == resolved_source
    ]
    if len(matches) != 1:
        return ["ambiguous_initiative_mapping"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
        }

    node = matches[0]
    target_branch = str(node.get("initiative_branch", "")).strip()
    if not target_branch:
        return ["target_branch_resolution_failed"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "node_id": str(node.get("node_id", "")).strip(),
        }
    if resolved_initiative and resolved_initiative != target_branch:
        return ["target_branch_resolution_failed"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "node_id": str(node.get("node_id", "")).strip(),
            "target_branch": target_branch,
            "initiative_branch": resolved_initiative,
        }

    resolved_execplan_id = resolved_execplan_id or str(node.get("target_execplan_id", "")).strip()
    execplan_path = _execplan_path_from_id(root_path, resolved_execplan_id)
    if execplan_path is None:
        return ["missing_active_execplan"], {
            "source_branch": resolved_source,
            "source_branch_role": "implementation_execplan",
            "target_branch": target_branch,
            "target_branch_role": "initiative",
            "node_id": str(node.get("node_id", "")).strip(),
            "execplan_id": resolved_execplan_id,
        }

    return [], {
        "source_branch": resolved_source,
        "source_branch_role": "implementation_execplan",
        "target_branch": target_branch,
        "target_branch_role": "initiative",
        "initiative_branch": target_branch,
        "integration_mode": str(node.get("integration_mode", "")).strip() or "via_initiative",
        "node_id": str(node.get("node_id", "")).strip(),
        "execplan_id": resolved_execplan_id,
        "execplan_path": execplan_path.as_posix(),
    }


def blockers_from_merge_readiness(report: dict[str, Any]) -> list[str]:
    failing_checks = [str(item).strip() for item in report.get("failing_checks", []) if str(item).strip()]
    blockers: list[str] = []
    if any(
        item.startswith("missing_base_ref:")
        or item.startswith("merge_target_mismatch:")
        or item == "missing_merge_target_contract"
        for item in failing_checks
    ):
        blockers.append("target_branch_resolution_failed")
    if any(item.startswith("validation_failed:") or item == "missing_smoke_test_validation" for item in failing_checks):
        blockers.append("required_validation_failed")
    if "dirty_generated_artifacts" in failing_checks:
        blockers.append("working_tree_hygiene_failed")
    if failing_checks and not blockers:
        blockers.append("merge_readiness_failed")
    seen: set[str] = set()
    ordered: list[str] = []
    for blocker in blockers:
        if blocker not in seen:
            seen.add(blocker)
            ordered.append(blocker)
    return ordered


def next_validations_from_merge_readiness(report: dict[str, Any]) -> list[str]:
    validations = report.get("checks", {}).get("validations", [])
    next_validations = ["bin/merge-readiness-check"]
    for result in validations:
        if not isinstance(result, dict):
            continue
        command = str(result.get("command", "")).strip()
        if command in ALLOWED_VALIDATIONS and not result.get("ok", False) and command not in next_validations:
            next_validations.append(command)
    return next_validations


def project_merge_readiness(
    *,
    root: str = ".",
    source_branch: str | None = None,
    target_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    blockers, context = resolve_mergeback_context(
        root=root,
        source_branch=source_branch,
        initiative_branch=initiative_branch or target_branch,
        execplan_id=execplan_id,
    )
    resolved_target = (target_branch or "").strip() or str(context.get("target_branch", "")).strip()
    if blockers:
        return 1, envelope(
            command="get-merge-readiness",
            status="blocked",
            ok=False,
            payload={
                "source_branch": str(context.get("source_branch", "")).strip(),
                "target_branch": resolved_target,
                "source_branch_role": str(context.get("source_branch_role", "")).strip(),
                "target_branch_role": "initiative",
                "initiative_branch": str(context.get("initiative_branch", "")).strip(),
                "readiness_checks": [],
                "blockers": blockers,
                "next_validations": ["bin/merge-readiness-check"],
                "next_action": "resolve_initiative_target",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/target-resolution-failed",
                    "title": "Merge-back target resolution failed",
                    "status": 409,
                    "detail": "The implementation branch could not be mapped to one lawful initiative merge target.",
                },
            },
        )

    code, report = check_merge_readiness(
        root=root,
        execplan_path=str(context.get("execplan_path", "")).strip() or None,
        base_ref=resolved_target,
    )
    readiness_checks = []
    for result in report.get("checks", {}).get("validations", []):
        if not isinstance(result, dict):
            continue
        command = str(result.get("command", "")).strip()
        if command in ALLOWED_VALIDATIONS:
            readiness_checks.append(
                {
                    "check_id": command,
                    "status": "passed" if result.get("ok", False) else "failed",
                }
            )
    blockers = blockers_from_merge_readiness(report)
    readiness = not blockers and code == 0
    payload = {
        "source_branch": str(context.get("source_branch", "")).strip(),
        "target_branch": resolved_target,
        "source_branch_role": "implementation_execplan",
        "target_branch_role": "initiative",
        "initiative_branch": str(context.get("initiative_branch", "")).strip(),
        "execplan_id": str(context.get("execplan_id", "")).strip(),
        "readiness_checks": readiness_checks,
        "blockers": blockers,
        "next_validations": [] if readiness else next_validations_from_merge_readiness(report),
        "next_action": "open_pr_to_initiative" if readiness else "run_merge_readiness_check",
    }
    if blockers:
        payload["problem"] = {
            "type": "https://platform-template-bootstrap/problems/merge-readiness-failed",
            "title": "Merge readiness failed",
            "status": 409,
            "detail": "One or more merge-readiness checks are still failing for the implementation branch.",
        }
    return (0 if readiness else 1), envelope(
        command="get-merge-readiness",
        status="ok" if readiness else "blocked",
        ok=readiness,
        payload=payload,
    )


def project_pr_integration_contract(
    *,
    root: str = ".",
    source_branch: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    blockers, context = resolve_mergeback_context(
        root=root,
        source_branch=source_branch,
        initiative_branch=initiative_branch,
        execplan_id=execplan_id,
    )
    if blockers:
        return 1, envelope(
            command="get-pr-integration-contract",
            status="blocked",
            ok=False,
            payload={
                "source_branch": str(context.get("source_branch", "")).strip(),
                "target_branch": str(context.get("target_branch", "")).strip(),
                "source_branch_role": str(context.get("source_branch_role", "")).strip(),
                "target_branch_role": "initiative",
                "integration_mode": "via_initiative",
                "required_validations": [],
                "required_human_actions": [],
                "blockers": blockers,
                "next_action": "resolve_initiative_target",
                "problem": {
                    "type": "https://platform-template-bootstrap/problems/target-resolution-failed",
                    "title": "PR integration target resolution failed",
                    "status": 409,
                    "detail": "The lawful initiative merge target could not be resolved for this implementation branch.",
                },
            },
        )

    return 0, envelope(
        command="get-pr-integration-contract",
        status="ok",
        ok=True,
        payload={
            "source_branch": str(context.get("source_branch", "")).strip(),
            "target_branch": str(context.get("target_branch", "")).strip(),
            "source_branch_role": "implementation_execplan",
            "target_branch_role": "initiative",
            "initiative_branch": str(context.get("initiative_branch", "")).strip(),
            "execplan_id": str(context.get("execplan_id", "")).strip(),
            "integration_mode": "via_initiative",
            "required_validations": [
                "bin/merge-readiness-check",
                "bin/execplan-validate",
                "bin/remaining-work-graph-check",
                "bin/policy-compliance-check",
            ],
            "required_human_actions": [
                "review_pr",
                "approve_pr",
                "merge_pr",
            ],
            "blockers": [],
            "next_action": "open_pr_to_initiative",
        },
    )
