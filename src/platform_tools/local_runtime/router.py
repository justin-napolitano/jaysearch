from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.local_runtime.adapter import RuntimeUnavailableError
from platform_tools.local_runtime.config import load_local_orchestration_config, validate_repo_target
from platform_tools.local_runtime.ollama_adapter import OllamaAdapter
from platform_tools.local_runtime.types import API_VERSION, PROBLEM_TYPES, REASON_CODES, ROUTE_TARGETS


COMMAND = "local-task-router"
DEFAULT_MODEL = "router"


def _evidence(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def _problem(*, blocker: str, detail: str) -> dict[str, Any]:
    return {
        "type": PROBLEM_TYPES[blocker],
        "title": blocker.replace("_", " "),
        "status": 403 if blocker == "internet_access_is_required_but_not_approved" else 503,
        "detail": detail,
        "command": COMMAND,
        "api_version": API_VERSION,
        "blockers": [blocker],
    }


def _blocked_route(
    *,
    repo_root: str,
    initiative_branch: str | None,
    execplan_id: str | None,
    route_target: str,
    reason_codes: list[str],
    blocker: str,
    next_action: str,
    detail: str,
) -> tuple[int, dict[str, Any]]:
    report = {
        "api_version": API_VERSION,
        "command": COMMAND,
        "status": "blocked",
        "ok": False,
        "repo_root": repo_root,
        "initiative_branch": (initiative_branch or "").strip(),
        "execplan_id": (execplan_id or "").strip(),
        "route_target": route_target,
        "reason_codes": reason_codes,
        "policy_basis": ["local_orchestration.routing"],
        "next_action": next_action,
        "next_validations": ["bin/local-task-router"],
        "blockers": [blocker],
        "evidence_refs": [
            _evidence("spec", "spec/local-orchestration.yaml"),
            _evidence("spec", "spec/local-orchestration-api.schema.yaml"),
            _evidence("command", "bin/local-task-router"),
        ],
        "problem": _problem(blocker=blocker, detail=detail),
    }
    return 1, report


def _build_prompt(
    *,
    task: str,
    initiative_branch: str | None,
    execplan_id: str | None,
    internet_required: bool,
    requires_code_changes: bool,
    requires_graph_changes: bool,
    context_refs: list[str],
) -> str:
    return "\n".join(
        [
            "Return only a JSON object.",
            "Choose one route_target from: local_planner, planning_worker, local_execution_worker, remote_execution_worker, human_escalation.",
            f"Allowed reason_codes: {', '.join(REASON_CODES)}.",
            "Return reason_codes as an array with at least one item.",
            f"Task: {task}",
            f"initiative_branch: {(initiative_branch or '').strip()}",
            f"execplan_id: {(execplan_id or '').strip()}",
            f"internet_required: {str(internet_required).lower()}",
            f"requires_code_changes: {str(requires_code_changes).lower()}",
            f"requires_graph_changes: {str(requires_graph_changes).lower()}",
            f"context_refs: {json.dumps(context_refs)}",
        ]
    )


def _validate_model_decision(payload: dict[str, Any]) -> tuple[str, list[str]]:
    route_target = str(payload.get("route_target", "")).strip()
    reasons = payload.get("reason_codes", [])
    if route_target not in ROUTE_TARGETS:
        return "", []
    if not isinstance(reasons, list):
        return "", []
    normalized = [str(item).strip() for item in reasons if str(item).strip() in REASON_CODES]
    if not normalized:
        return "", []
    return route_target, normalized


def route_local_task(
    *,
    root: str = ".",
    task: str,
    repo_root: str | None = None,
    initiative_branch: str | None = None,
    execplan_id: str | None = None,
    internet_required: bool = False,
    requires_code_changes: bool = False,
    requires_graph_changes: bool = False,
    context_refs: list[str] | None = None,
    model: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    config = load_local_orchestration_config(root=root_path.as_posix())
    target_root = (repo_root or root_path.as_posix()).strip()
    target_blockers = validate_repo_target(config=config, repo_root=repo_root)
    if target_blockers:
        reason = "managed_repo_target_missing" if "target_repo_root_is_missing" in target_blockers else "managed_repo_target_ambiguous"
        return _blocked_route(
            repo_root=target_root,
            initiative_branch=initiative_branch,
            execplan_id=execplan_id,
            route_target="human_escalation",
            reason_codes=[reason],
            blocker=target_blockers[0],
            next_action="human_review_required",
            detail="repo target validation failed",
        )

    internet_mode = str(config.get("runtime_profile", {}).get("internet_mode", {}).get("default", "disabled")).strip()
    if internet_required and internet_mode != "enabled":
        return _blocked_route(
            repo_root=target_root,
            initiative_branch=initiative_branch,
            execplan_id=execplan_id,
            route_target="human_escalation",
            reason_codes=["task_requires_internet_access", "human_approval_required"],
            blocker="internet_access_is_required_but_not_approved",
            next_action="human_review_required",
            detail="internet-required work is not approved in the local runtime profile",
        )

    adapter = OllamaAdapter()
    try:
        adapter.runtime_probe(required_models=[model or DEFAULT_MODEL])
    except RuntimeUnavailableError as exc:
        return _blocked_route(
            repo_root=target_root,
            initiative_branch=initiative_branch,
            execplan_id=execplan_id,
            route_target="human_escalation",
            reason_codes=["local_runtime_unavailable"],
            blocker="runtime_endpoint_unreachable",
            next_action="bin/local-runtime-check",
            detail=str(exc),
        )

    prompt = _build_prompt(
        task=task,
        initiative_branch=initiative_branch,
        execplan_id=execplan_id,
        internet_required=internet_required,
        requires_code_changes=requires_code_changes,
        requires_graph_changes=requires_graph_changes,
        context_refs=context_refs or [],
    )
    try:
        model_payload = adapter.generate_json(model=model or DEFAULT_MODEL, prompt=prompt)
    except RuntimeUnavailableError as exc:
        return _blocked_route(
            repo_root=target_root,
            initiative_branch=initiative_branch,
            execplan_id=execplan_id,
            route_target="human_escalation",
            reason_codes=["local_runtime_unavailable"],
            blocker="runtime_endpoint_unreachable",
            next_action="bin/local-runtime-check",
            detail=str(exc),
        )

    route_target, reason_codes = _validate_model_decision(model_payload)
    if not route_target:
        return _blocked_route(
            repo_root=target_root,
            initiative_branch=initiative_branch,
            execplan_id=execplan_id,
            route_target="human_escalation",
            reason_codes=["governance_authority_ambiguous"],
            blocker="governance_authority_is_ambiguous",
            next_action="human_review_required",
            detail="local model did not return a valid bounded routing decision",
        )

    next_action = "none"
    if route_target == "planning_worker":
        next_action = "bin/get-graph-state"
    elif route_target in {"local_execution_worker", "remote_execution_worker"}:
        next_action = "bin/resolve-worker-contract"
    elif route_target == "human_escalation":
        next_action = "human_review_required"

    report = {
        "api_version": API_VERSION,
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "repo_root": target_root,
        "initiative_branch": (initiative_branch or "").strip(),
        "execplan_id": (execplan_id or "").strip(),
        "route_target": route_target,
        "reason_codes": reason_codes,
        "policy_basis": ["local_orchestration.routing", "public_orchestration_api.contract"],
        "next_action": next_action,
        "next_validations": ["bin/local-task-router"],
        "blockers": [],
        "evidence_refs": [
            _evidence("spec", "spec/local-orchestration.yaml"),
            _evidence("spec", "spec/local-orchestration-api.schema.yaml"),
            _evidence("command", "bin/local-task-router"),
        ],
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--execplan-id", default=None)
    parser.add_argument("--internet-required", action="store_true")
    parser.add_argument("--requires-code-changes", action="store_true")
    parser.add_argument("--requires-graph-changes", action="store_true")
    parser.add_argument("--context-ref", action="append", dest="context_refs")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    code, report = route_local_task(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
