from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.control_plane import get_control_plane_status, get_next_orchestration_action
from platform_tools.get_worker_status import get_worker_status
from platform_tools.local_runtime.router import route_local_task
from platform_tools.local_runtime.runtime_check import check_local_runtime
from platform_tools.managed_repo_status import get_managed_repo_status
from platform_tools.mergeback_orchestration import (
    prepare_next_impl_branch,
    project_merge_readiness,
    project_pr_integration_contract,
)
from platform_tools.plan_utils import parse_plan
from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions
from platform_tools.start_next_worker import start_next_worker


COMMAND = "orchestrate-governed-slice"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")


def _effective_base_ref(
    *,
    repo_root: Path,
    branch: str,
    execplan_path: str,
    default_base_ref: str,
) -> str:
    if not branch.startswith("impl-execplan/") or not execplan_path:
        return default_base_ref
    graph_path = repo_root / GRAPH_PATH
    if not graph_path.exists():
        return default_base_ref
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_base_ref
    nodes = graph.get("nodes", [])
    if not isinstance(nodes, list):
        return default_base_ref
    try:
        execplan_id = str(parse_plan(Path(execplan_path)).frontmatter.get("id", "")).strip()
    except Exception:
        return default_base_ref
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if str(node.get("target_execplan_id", "")).strip() != execplan_id:
            continue
        initiative_branch = str(node.get("initiative_branch", "")).strip()
        integration_mode = str(node.get("integration_mode", "")).strip()
        if integration_mode == "via_initiative" and initiative_branch:
            return initiative_branch
        break
    return default_base_ref


def _execution_projection(
    *,
    mode: str,
    executed: bool,
    status: str,
    command: str,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "mode": mode,
        "executed": executed,
        "status": status,
        "command": command,
        "result": result,
    }


def _execute_task_route(
    *,
    local_root: Path,
    target_root: Path,
    initiative_branch: str,
    task: str,
    model: str | None,
    executor: str,
    push_mode: str,
    github_push_remote: str | None,
    task_command: str | None,
    commit_message: str | None,
    pr_title: str | None,
    pr_body: str | None,
    draft_pr: bool,
    commit: bool,
    create_pr: bool,
    cleanup: bool,
    actor_id: str,
    workspace_root: str,
    stale_after_minutes: int,
) -> tuple[int, dict[str, Any]]:
    route_code, route_report = route_local_task(
        root=local_root.as_posix(),
        task=task,
        repo_root=target_root.as_posix(),
        initiative_branch=initiative_branch or None,
        model=model,
    )
    route_target = str(route_report.get("route_target", "")).strip()
    if route_code != 0 or route_target not in {"local_execution_worker", "remote_execution_worker"}:
        return (
            route_code,
            _execution_projection(
                mode="execute_next_step",
                executed=True,
                status="ok" if route_code == 0 else "blocked",
                command="bin/local-task-router",
                result=route_report,
            ),
        )

    run_code, run_report = start_next_worker(
        root=target_root.as_posix(),
        repo_source=target_root.as_posix(),
        initiative_branch=initiative_branch or None,
        executor=executor,
        push_mode=push_mode,
        github_push_remote=github_push_remote,
        task_command=task_command,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        draft_pr=draft_pr,
        commit=commit,
        create_pr=create_pr,
        cleanup=cleanup,
        actor_id=actor_id,
        workspace_root=workspace_root,
        stale_after_minutes=stale_after_minutes,
    )
    return (
        run_code,
        _execution_projection(
            mode="execute_next_step",
            executed=True,
            status="ok" if run_code == 0 else "blocked",
            command="bin/start-next-worker",
            result={
                "route": route_report,
                "worker_start": run_report,
            },
        ),
    )


def _execute_recommended_action(
    *,
    local_root: Path,
    target_root: Path,
    branch: str,
    initiative_branch: str,
    recommended_action: str,
    command_ref: str,
) -> tuple[int, dict[str, Any]]:
    if recommended_action == "cut_impl_branch":
        code, report = prepare_next_impl_branch(
            root=local_root.as_posix(),
            initiative_branch=initiative_branch or None,
        )
    elif recommended_action == "open_pr_to_initiative":
        code, report = project_pr_integration_contract(
            root=local_root.as_posix(),
            source_branch=branch or None,
            initiative_branch=initiative_branch or None,
        )
    elif recommended_action in {"restack_on_initiative", "resolve_mergeback_blockers"}:
        code, report = project_merge_readiness(
            root=local_root.as_posix(),
            source_branch=branch or None,
            initiative_branch=initiative_branch or None,
        )
    elif recommended_action == "run_local_runtime_check":
        code, report = check_local_runtime(
            root=local_root.as_posix(),
            repo_root=target_root.as_posix(),
            verify_managed_repo=True,
        )
    elif recommended_action == "inspect_worker_sessions":
        code, report = get_worker_status(root=target_root.as_posix())
    elif recommended_action == "resolve_control_plane_blockers":
        code, report = get_managed_repo_status(root=target_root.as_posix())
    else:
        return (
            1,
            _execution_projection(
                mode="execute_next_step",
                executed=False,
                status="blocked",
                command=command_ref,
                result={
                    "blockers": ["recommended_action_not_executable"],
                    "recommended_action": recommended_action,
                },
            ),
        )
    return (
        code,
        _execution_projection(
            mode="execute_next_step",
            executed=True,
            status="ok" if code == 0 else "blocked",
            command=command_ref,
            result=report,
        ),
    )


def run_orchestrate_governed_slice(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
    execute: bool = False,
    task: str | None = None,
    model: str | None = None,
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
    local_repo_path = Path(".").resolve()
    target_repo_root = root_path if root_path != local_repo_path else local_repo_path
    post_merge_reconciliation = reconcile_pending_merge_completions(
        repo_root=local_repo_path,
        main_ref=base_ref,
    )

    status_code, control_plane_status = get_control_plane_status(
        root=local_repo_path.as_posix(),
        repo_root=target_repo_root.as_posix(),
    )
    action_code, next_action_report = get_next_orchestration_action(
        root=local_repo_path.as_posix(),
        repo_root=target_repo_root.as_posix(),
    )

    blockers = [
        str(item).strip()
        for item in control_plane_status.get("blockers", [])
        if str(item).strip()
    ]
    if action_code != 0:
        blockers.extend(
            str(item).strip()
            for item in next_action_report.get("blockers", [])
            if str(item).strip()
        )

    next_actions: list[dict[str, Any]] = []
    recommended_action = str(next_action_report.get("recommended_action", "")).strip()
    command_ref = str(next_action_report.get("command_ref", "")).strip()
    if recommended_action and recommended_action != "none":
        next_actions.append(
            {
                "action": recommended_action,
                "command_ref": command_ref,
                "reason": "control_plane_projection",
            }
        )

    execution = _execution_projection(
        mode="execute_next_step" if execute else "project_only",
        executed=False,
        status="deferred",
        command="",
        result=None,
    )
    execution_code = 0
    if execute and not blockers:
        initiative_branch = str(control_plane_status.get("initiative_branch", "")).strip()
        current_branch = str(control_plane_status.get("current_branch", branch or "")).strip()
        if task:
            execution_code, execution = _execute_task_route(
                local_root=local_repo_path,
                target_root=target_repo_root,
                initiative_branch=initiative_branch,
                task=task,
                model=model,
                executor=executor,
                push_mode=push_mode,
                github_push_remote=github_push_remote,
                task_command=task_command,
                commit_message=commit_message,
                pr_title=pr_title,
                pr_body=pr_body,
                draft_pr=draft_pr,
                commit=commit,
                create_pr=create_pr,
                cleanup=cleanup,
                actor_id=actor_id,
                workspace_root=workspace_root,
                stale_after_minutes=stale_after_minutes,
            )
        elif recommended_action and command_ref:
            execution_code, execution = _execute_recommended_action(
                local_root=local_repo_path,
                target_root=target_repo_root,
                branch=current_branch,
                initiative_branch=initiative_branch,
                recommended_action=recommended_action,
                command_ref=command_ref,
            )

    ok = status_code == 0 and action_code == 0 and execution_code == 0 and not blockers
    report = {
        "command": COMMAND,
        "status": "ok" if ok else "blocked",
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "branch": str(control_plane_status.get("current_branch", branch or "")).strip(),
        "branch_role": str(control_plane_status.get("branch_role", "")).strip(),
        "initiative_branch": str(control_plane_status.get("initiative_branch", "")).strip(),
        "repo_root": target_repo_root.as_posix(),
        "base_ref": base_ref,
        "execplan_path": execplan_path or "",
        "control_plane_status": control_plane_status,
        "next_orchestration_action": next_action_report,
        "post_merge_reconciliation": post_merge_reconciliation,
        "managed_repo": (control_plane_status.get("checks", {}) or {}).get("managed_repo"),
        "execution": execution,
        "next_actions": next_actions,
    }
    return (0 if ok else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--task", default=None)
    parser.add_argument("--model", default=None)
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
    code, report = run_orchestrate_governed_slice(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
