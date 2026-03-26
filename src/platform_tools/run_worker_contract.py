from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.next_worker_slice import get_next_worker_slice
from platform_tools.worker_contracts import contract_scope_findings, find_contract, load_registry, registry_contracts
from platform_tools.worker_session_coordinator import run_worker_session_coordinator


COMMAND = "run-worker-contract"
SUPPORTED_EXECUTORS = {
    "local_clone": "clone",
    "local_worktree": "worktree",
}
SUPPORTED_PUSH_MODES = {"none", "staging", "github", "staging_and_github"}


def _load_registries(root: Path) -> list[dict[str, Any]]:
    contracts_dir = root / "artifacts" / "governance" / "initiative-worker-contracts"
    if not contracts_dir.exists():
        return []
    registries: list[dict[str, Any]] = []
    for path in sorted(contracts_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            registries.append(payload)
    return registries


def _resolve_contract(
    *,
    root: Path,
    initiative_branch: str,
    contract_id: str | None,
    branch: str | None,
    worker_id: str | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    registry = load_registry(root=root, initiative_branch=initiative_branch)
    if registry is None:
        return None, ["worker_contract_registry_missing"]
    scope_findings: list[str] = []
    contract = find_contract(registry, contract_id=contract_id, branch=branch, worker_id=worker_id)
    if contract is None:
        return None, ["worker_contract_not_found"]
    scope_findings.extend(contract_scope_findings(contract))
    if str(contract.get("status", "")).strip() != "ready":
        scope_findings.append("worker_contract_not_ready")
    return contract, scope_findings


def _resolve_contract_without_branch(
    *,
    root: Path,
    contract_id: str | None,
    branch: str | None,
    worker_id: str | None,
) -> tuple[str, dict[str, Any] | None, list[str]]:
    registries = _load_registries(root)
    matches: list[tuple[str, dict[str, Any]]] = []
    for registry in registries:
        initiative_branch = str(registry.get("initiative_branch", "")).strip()
        contract = find_contract(registry, contract_id=contract_id, branch=branch, worker_id=worker_id)
        if initiative_branch and contract is not None:
            matches.append((initiative_branch, contract))
    if not matches:
        return "", None, ["worker_contract_not_found"]
    if len(matches) != 1:
        return "", None, ["worker_contract_not_deterministic"]
    initiative_branch, contract = matches[0]
    findings = contract_scope_findings(contract)
    if str(contract.get("status", "")).strip() != "ready":
        findings.append("worker_contract_not_ready")
    return initiative_branch, contract, findings


def _normalize_executor(executor: str) -> tuple[str, list[str]]:
    normalized = executor.strip().lower()
    backend = SUPPORTED_EXECUTORS.get(normalized)
    if backend is None:
        return "", ["unsupported_executor"]
    return backend, []


def _push_policy(
    *,
    push_mode: str,
    github_push_remote: str | None,
) -> tuple[dict[str, Any], list[str]]:
    normalized = push_mode.strip().lower()
    if normalized not in SUPPORTED_PUSH_MODES:
        return {}, ["unsupported_push_mode"]
    github_remote = (github_push_remote or "").strip()
    if normalized in {"github", "staging_and_github"} and not github_remote:
        return {}, ["github_push_remote_required"]
    if normalized == "none":
        return {"push": False, "github_push_remote": None}, []
    if normalized == "staging":
        return {"push": True, "github_push_remote": None}, []
    return {"push": True, "github_push_remote": github_remote}, []


def run_worker_contract(
    *,
    root: str = ".",
    repo_source: str | None = None,
    initiative_branch: str | None = None,
    contract_id: str | None = None,
    branch: str | None = None,
    worker_id: str | None = None,
    executor: str = "local_clone",
    push_mode: str = "staging",
    github_push_remote: str | None = None,
    task_command: str | None = None,
    commit_message: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    draft_pr: bool = False,
    commit: bool = False,
    create_pr: bool = False,
    cleanup: bool = False,
    actor_id: str = "orchestrator/default",
    workspace_root: str = ".tmp/governed-workers",
    stale_after_minutes: int = 60,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    repo_root = Path(repo_source).resolve() if repo_source else root_path

    backend, backend_findings = _normalize_executor(executor)
    if backend_findings:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "blockers": backend_findings,
            "executor": executor,
        }

    push_policy, push_findings = _push_policy(push_mode=push_mode, github_push_remote=github_push_remote)
    if push_findings:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "blockers": push_findings,
            "push_mode": push_mode,
        }

    resolved_initiative_branch = (initiative_branch or "").strip()
    resolved_contract: dict[str, Any] | None = None
    resolution_findings: list[str] = []

    if contract_id or branch or worker_id:
        if resolved_initiative_branch:
            resolved_contract, resolution_findings = _resolve_contract(
                root=repo_root,
                initiative_branch=resolved_initiative_branch,
                contract_id=contract_id,
                branch=branch,
                worker_id=worker_id,
            )
        else:
            resolved_initiative_branch, resolved_contract, resolution_findings = _resolve_contract_without_branch(
                root=repo_root,
                contract_id=contract_id,
                branch=branch,
                worker_id=worker_id,
            )
    else:
        resolved_initiative_branch = resolved_initiative_branch or get_current_branch(root=repo_root)
        next_code, next_report = get_next_worker_slice(root=repo_root.as_posix(), initiative_branch=resolved_initiative_branch)
        if next_code != 0:
            return next_code, {
                "command": COMMAND,
                "status": "blocked",
                "ok": False,
                "initiative_branch": resolved_initiative_branch,
                "blockers": list(next_report.get("blockers", [])),
                "resolution": next_report,
            }
        selected = next_report.get("selected", {})
        resolved_contract = {
            "contract_id": str(selected.get("contract_id", "")).strip(),
            "branch": str(selected.get("implementation_branch", "")).strip(),
            "worker_id": str(selected.get("worker_id", "")).strip(),
            "execplan_id": str(selected.get("execplan_id", "")).strip(),
            "initiative_branch": str(selected.get("initiative_branch", "")).strip() or resolved_initiative_branch,
            "title": str(selected.get("title", "")).strip(),
            "status": "ready",
        }

    if resolved_contract is None or resolution_findings:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": resolved_initiative_branch,
            "blockers": resolution_findings or ["worker_contract_not_resolved"],
        }

    resolved_branch = str(resolved_contract.get("branch", "")).strip()
    resolved_worker_id = str(resolved_contract.get("worker_id", "")).strip()
    if not resolved_branch or not resolved_worker_id:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": resolved_initiative_branch,
            "blockers": ["worker_contract_missing_branch_or_worker_id"],
            "selected": resolved_contract,
        }

    code, coordinator_report = run_worker_session_coordinator(
        repo_source=repo_root.as_posix(),
        worker_id=resolved_worker_id,
        branch=resolved_branch,
        backend=backend,
        workspace_root=workspace_root,
        task_command=task_command,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        github_push_remote=push_policy["github_push_remote"],
        draft_pr=draft_pr,
        commit=commit,
        push=bool(push_policy["push"]),
        create_pr=create_pr,
        cleanup=cleanup,
        actor_id=actor_id,
        stale_after_minutes=stale_after_minutes,
    )
    report = {
        "command": COMMAND,
        "status": "ok" if code == 0 else "blocked",
        "ok": code == 0,
        "executor": executor,
        "push_mode": push_mode,
        "initiative_branch": resolved_initiative_branch,
        "selected": {
            "contract_id": str(resolved_contract.get("contract_id", "")).strip(),
            "execplan_id": str(resolved_contract.get("execplan_id", "")).strip(),
            "implementation_branch": resolved_branch,
            "worker_id": resolved_worker_id,
            "title": str(resolved_contract.get("title", "")).strip(),
        },
        "worker_run": coordinator_report,
    }
    return code, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo-source", default=None)
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--contract-id", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--executor", default="local_clone")
    parser.add_argument("--push-mode", default="staging")
    parser.add_argument("--github-push-remote", default=None)
    parser.add_argument("--task-command", default=None)
    parser.add_argument("--commit-message", default=None)
    parser.add_argument("--pr-title", default=None)
    parser.add_argument("--pr-body", default=None)
    parser.add_argument("--draft-pr", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--create-pr", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--actor-id", default="orchestrator/default")
    parser.add_argument("--workspace-root", default=".tmp/governed-workers")
    parser.add_argument("--stale-after-minutes", type=int, default=60)
    args = parser.parse_args()
    code, report = run_worker_contract(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
