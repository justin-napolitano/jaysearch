from __future__ import annotations

import argparse
import json
from typing import Any

from platform_tools.resolve_worker_contract import resolve_worker_contract
from platform_tools.run_worker_contract import run_worker_contract


COMMAND = "start-next-worker"


def start_next_worker(
    *,
    root: str = ".",
    repo_source: str | None = None,
    initiative_branch: str | None = None,
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
    resolve_code, resolve_report = resolve_worker_contract(
        root=root,
        initiative_branch=initiative_branch,
    )
    if resolve_code != 0:
        return resolve_code, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": initiative_branch or "",
            "resolution": resolve_report,
            "blockers": list(resolve_report.get("blockers", [])),
        }

    selected = resolve_report.get("selected", {})
    run_code, run_report = run_worker_contract(
        root=root,
        repo_source=repo_source,
        initiative_branch=resolve_report.get("initiative_branch"),
        contract_id=selected.get("contract_id"),
        branch=selected.get("branch"),
        worker_id=selected.get("worker_id"),
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
    return run_code, {
        "command": COMMAND,
        "status": "ok" if run_code == 0 else "blocked",
        "ok": run_code == 0,
        "initiative_branch": resolve_report.get("initiative_branch", ""),
        "resolution": resolve_report,
        "worker_run": run_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo-source", default=None)
    parser.add_argument("--initiative-branch", default=None)
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
    code, report = start_next_worker(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
