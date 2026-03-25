from __future__ import annotations

import argparse
import json
from typing import Any

from platform_tools.governed_worker import run_worker
from platform_tools.session_bootstrap import run_worker_session_lease
from platform_tools.worker_session_status import get_worker_session_status


COMMAND = "worker-session-coordinator"


def run_worker_session_coordinator(
    *,
    repo_source: str,
    worker_id: str,
    branch: str,
    base_ref: str = "main",
    backend: str = "clone",
    workspace_root: str = ".tmp/governed-workers",
    task_command: str | None = None,
    commit_message: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    push_remote: str = "origin",
    draft_pr: bool = False,
    commit: bool = False,
    push: bool = False,
    create_pr: bool = False,
    cleanup: bool = False,
    actor_id: str = "agent/codex-01",
    stale_after_minutes: int = 60,
) -> tuple[int, dict[str, Any]]:
    lease_code, lease_report = run_worker_session_lease(
        root=repo_source,
        branch=branch,
        base_ref=base_ref,
        worker_id=worker_id,
        actor_id=actor_id,
        action="issue",
    )
    if lease_code != 0:
        status_code, status_report = get_worker_session_status(root=repo_source, stale_after_minutes=stale_after_minutes)
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "lease": lease_report,
            "worker_run": None,
            "worker_status": status_report,
        }
        return 1 if status_code == 0 else status_code, report

    worker_code, worker_report = run_worker(
        repo_source=repo_source,
        worker_id=worker_id,
        base_ref=base_ref,
        branch=branch,
        backend=backend,
        workspace_root=workspace_root,
        task_command=task_command,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        push_remote=push_remote,
        draft_pr=draft_pr,
        commit=commit,
        push=push,
        create_pr=create_pr,
        cleanup=cleanup,
    )
    status_code, status_report = get_worker_session_status(root=repo_source, stale_after_minutes=stale_after_minutes)
    report = {
        "command": COMMAND,
        "status": "ok" if worker_code == 0 and status_code == 0 else "blocked",
        "ok": worker_code == 0 and status_code == 0,
        "lease": lease_report,
        "worker_run": worker_report,
        "worker_status": status_report,
    }
    return (0 if report["ok"] else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-source", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--backend", default="clone")
    parser.add_argument("--workspace-root", default=".tmp/governed-workers")
    parser.add_argument("--task-command", default=None)
    parser.add_argument("--commit-message", default=None)
    parser.add_argument("--pr-title", default=None)
    parser.add_argument("--pr-body", default=None)
    parser.add_argument("--push-remote", default="origin")
    parser.add_argument("--draft-pr", action="store_true")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--create-pr", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--actor-id", default="agent/codex-01")
    parser.add_argument("--stale-after-minutes", type=int, default=60)
    args = parser.parse_args()
    code, report = run_worker_session_coordinator(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
