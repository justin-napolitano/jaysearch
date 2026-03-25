from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Any

from platform_tools.session_bootstrap import run_session_bootstrap_check, run_worker_session_lease
from platform_tools.worker_runtime_artifacts import (
    append_runtime_event,
    create_run_metadata,
    make_run_id,
    make_trace_id,
    utc_timestamp,
    update_run_metadata,
    write_problem_artifact,
)


COMMAND = "governed-worker"
DEFAULT_WORKSPACE_ROOT = ".tmp/governed-workers"
DEFAULT_LOCAL_PUSH_REMOTE_ROOT = "artifacts/governance/staging-remotes"
STAGING_REMOTE_NAME = "codex-staging"
LOCAL_BACKENDS = {"clone", "worktree"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "worker"


def _default_branch(worker_id: str, base_ref: str) -> str:
    return f"impl-execplan/{_slugify(worker_id)}-{_slugify(base_ref)}"


def _run_process(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"command_failed:{' '.join(args)}"
        raise RuntimeError(detail)
    return proc


def _git(root: Path, *args: str) -> str:
    return _run_process(["git", *args], cwd=root).stdout.strip()


def _git_config_get(root: Path, key: str) -> str:
    proc = subprocess.run(
        ["git", "config", "--get", key],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _inherit_commit_identity(*, source_repo: Path, workspace_path: Path) -> None:
    source_name = _git_config_get(source_repo, "user.name")
    source_email = _git_config_get(source_repo, "user.email")
    workspace_name = _git_config_get(workspace_path, "user.name")
    workspace_email = _git_config_get(workspace_path, "user.email")
    if source_name and not workspace_name:
        _git(workspace_path, "config", "user.name", source_name)
    if source_email and not workspace_email:
        _git(workspace_path, "config", "user.email", source_email)


def _configure_secondary_push_remote(*, source_repo: Path, workspace_path: Path, remote_name: str) -> dict[str, str]:
    if not remote_name:
        return {"name": "", "url": "", "configured": "false"}
    remote_url = _git_config_get(source_repo, f"remote.{remote_name}.url")
    if not remote_url:
        return {"name": remote_name, "url": "", "configured": "false"}
    existing_remotes = {line.strip() for line in _git(workspace_path, "remote").splitlines() if line.strip()}
    if remote_name in existing_remotes:
        _git(workspace_path, "remote", "set-url", remote_name, remote_url)
    else:
        _git(workspace_path, "remote", "add", remote_name, remote_url)
    return {"name": remote_name, "url": remote_url, "configured": "true"}


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _is_bare_repo(path: Path) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--is-bare-repository"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _default_local_push_remote_path(*, source_repo: Path, workspace_root: Path) -> Path:
    del workspace_root
    remote_root = source_repo / DEFAULT_LOCAL_PUSH_REMOTE_ROOT
    remote_root.mkdir(parents=True, exist_ok=True)
    return remote_root / f"{source_repo.name}.git"


def _configure_local_push_remote(
    *,
    source_repo: Path,
    workspace_path: Path,
    workspace_root: Path,
    base_ref: str,
    push_remote: str,
) -> dict[str, Any]:
    if push_remote != "origin":
        return {"mode": "passthrough", "staging_remote": "", "remote": push_remote, "url": ""}
    if not _is_git_repo(source_repo) or _is_bare_repo(source_repo):
        return {"mode": "passthrough", "staging_remote": "", "remote": push_remote, "url": ""}
    bare_remote = _default_local_push_remote_path(source_repo=source_repo, workspace_root=workspace_root)
    if not bare_remote.exists():
        _run_process(["git", "init", "--bare", bare_remote.as_posix()])
    _run_process(
        [
            "git",
            "push",
            "--force",
            bare_remote.as_posix(),
            f"refs/heads/{base_ref}:refs/heads/{base_ref}",
        ],
        cwd=source_repo,
    )
    existing_remotes = {line.strip() for line in _git(workspace_path, "remote").splitlines() if line.strip()}
    if STAGING_REMOTE_NAME in existing_remotes:
        _git(workspace_path, "remote", "set-url", STAGING_REMOTE_NAME, bare_remote.as_posix())
    else:
        _git(workspace_path, "remote", "add", STAGING_REMOTE_NAME, bare_remote.as_posix())
    return {
        "mode": "local_staging_remote",
        "staging_remote": STAGING_REMOTE_NAME,
        "remote": push_remote,
        "url": bare_remote.as_posix(),
    }


def _build_worker_spec(
    *,
    repo_source: str,
    worker_id: str,
    base_ref: str,
    branch: str | None,
    backend: str,
    task_command: str | None,
    workspace_root: str,
    commit_message: str | None,
    pr_title: str | None,
    pr_body: str | None,
    push_remote: str,
    github_push_remote: str | None,
    draft_pr: bool,
) -> dict[str, Any]:
    normalized_backend = backend.strip().lower()
    if normalized_backend not in LOCAL_BACKENDS:
        raise ValueError(f"unsupported_backend:{backend}")
    normalized_branch = branch.strip() if branch else _default_branch(worker_id, base_ref)
    normalized_commit_message = commit_message.strip() if commit_message else f"feat(worker): {worker_id}"
    normalized_pr_title = pr_title.strip() if pr_title else normalized_commit_message
    normalized_pr_body = pr_body.strip() if pr_body else f"Automated changes from worker `{worker_id}`."
    return {
        "command": COMMAND,
        "repo_source": repo_source,
        "worker_id": worker_id,
        "base_ref": base_ref,
        "branch": normalized_branch,
        "backend": normalized_backend,
        "task_command": task_command or "",
        "workspace_root": workspace_root,
        "workspace_name": _slugify(worker_id),
        "commit_message": normalized_commit_message,
        "pr_title": normalized_pr_title,
        "pr_body": normalized_pr_body,
        "push_remote": push_remote,
        "github_push_remote": github_push_remote.strip() if github_push_remote else "",
        "draft_pr": draft_pr,
    }


def _write_worker_metadata(workspace_path: Path, spec: dict[str, Any]) -> Path:
    metadata_dir = workspace_path / ".ephemeral-worker"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    spec_path = metadata_dir / "spec.json"
    spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return spec_path


def _bootstrap_gate(*, repo_root: Path, branch: str, base_ref: str) -> dict[str, Any]:
    code, report = run_session_bootstrap_check(
        root=repo_root.as_posix(),
        branch=branch,
        base_ref=base_ref,
        session_kind="worker",
        worker_id=branch.split("/", 1)[1] if branch.startswith("impl-execplan/") else branch,
    )
    if code != 0 or not report.get("ok", False):
        raise RuntimeError(f"worker_bootstrap_blocked:{json.dumps(report, sort_keys=True)}")
    return report


def _close_lease(*, repo_root: Path, branch: str, outcome: str) -> dict[str, Any]:
    worker_id = branch.split("/", 1)[1] if branch.startswith("impl-execplan/") else branch
    code, report = run_worker_session_lease(
        root=repo_root.as_posix(),
        branch=branch,
        worker_id=worker_id,
        action="close",
        outcome=outcome,
    )
    if code != 0 or not report.get("ok", False):
        raise RuntimeError(f"worker_lease_close_failed:{json.dumps(report, sort_keys=True)}")
    return report


def prepare_local_workspace(
    *,
    repo_source: str,
    worker_id: str,
    base_ref: str = "main",
    branch: str | None = None,
    backend: str = "worktree",
    workspace_root: str = DEFAULT_WORKSPACE_ROOT,
    task_command: str | None = None,
    commit_message: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    push_remote: str = "origin",
    github_push_remote: str | None = None,
    draft_pr: bool = False,
    configure_push_remote: bool = False,
) -> tuple[int, dict[str, Any]]:
    spec = _build_worker_spec(
        repo_source=repo_source,
        worker_id=worker_id,
        base_ref=base_ref,
        branch=branch,
        backend=backend,
        task_command=task_command,
        workspace_root=workspace_root,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        push_remote=push_remote,
        github_push_remote=github_push_remote,
        draft_pr=draft_pr,
    )
    repo_path = Path(repo_source).expanduser().resolve()
    workspace_root_path = Path(workspace_root).expanduser().resolve()
    workspace_path = workspace_root_path / spec["workspace_name"]
    if workspace_path.exists():
        raise RuntimeError(f"workspace_already_exists:{workspace_path.as_posix()}")
    bootstrap_report = _bootstrap_gate(repo_root=repo_path, branch=spec["branch"], base_ref=spec["base_ref"])
    workspace_root_path.mkdir(parents=True, exist_ok=True)
    if spec["backend"] == "worktree":
        _git(repo_path, "worktree", "add", "-b", spec["branch"], workspace_path.as_posix(), spec["base_ref"])
    else:
        _run_process(
            [
                "git",
                "clone",
                "--branch",
                spec["base_ref"],
                "--single-branch",
                repo_source,
                workspace_path.as_posix(),
            ]
        )
        _git(workspace_path, "checkout", "-b", spec["branch"])
    _inherit_commit_identity(source_repo=repo_path, workspace_path=workspace_path)
    secondary_remote_config = _configure_secondary_push_remote(
        source_repo=repo_path,
        workspace_path=workspace_path,
        remote_name=spec["github_push_remote"],
    )
    push_remote_config = {"mode": "not_configured", "staging_remote": "", "remote": spec["push_remote"], "url": ""}
    if configure_push_remote:
        push_remote_config = _configure_local_push_remote(
            source_repo=repo_path,
            workspace_path=workspace_path,
            workspace_root=workspace_root_path,
            base_ref=spec["base_ref"],
            push_remote=spec["push_remote"],
        )
    spec_path = _write_worker_metadata(workspace_path, spec)
    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "mode": "prepare-local",
        "backend": spec["backend"],
        "repo_source": repo_source,
        "branch": spec["branch"],
        "workspace_path": workspace_path.as_posix(),
        "spec_path": spec_path.as_posix(),
        "task_command": spec["task_command"],
        "push_remote_config": push_remote_config,
        "secondary_remote_config": secondary_remote_config,
        "bootstrap": bootstrap_report,
    }
    return 0, report


def _cleanup_workspace(*, backend: str, repo_source: str, workspace_path: Path) -> None:
    if backend == "worktree":
        repo_path = Path(repo_source).expanduser().resolve()
        _git(repo_path, "worktree", "remove", "--force", workspace_path.as_posix())
        return
    shutil.rmtree(workspace_path)


def _working_tree_changes(workspace_path: Path) -> list[str]:
    status_output = _git(workspace_path, "status", "--short")
    return [line for line in status_output.splitlines() if line.strip()]


def _run_task_command(task_command: str, *, workspace_path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    proc = subprocess.run(
        task_command,
        cwd=workspace_path,
        env=env,
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": task_command,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def _commit_if_needed(workspace_path: Path, commit_message: str, *, enable_commit: bool) -> dict[str, Any]:
    changes = _working_tree_changes(workspace_path)
    if not enable_commit:
        return {"requested": False, "created": False, "sha": "", "changes": changes}
    if not changes:
        return {"requested": True, "created": False, "sha": "", "changes": changes}
    _git(workspace_path, "add", "-A")
    _run_process(["git", "-c", "commit.gpgsign=false", "commit", "-m", commit_message], cwd=workspace_path)
    sha = _git(workspace_path, "rev-parse", "HEAD")
    return {"requested": True, "created": True, "sha": sha, "changes": changes}


def _push_if_requested(
    workspace_path: Path,
    remote: str,
    branch: str,
    *,
    enable_push: bool,
    staging_remote: str = "",
    github_push_remote: str = "",
) -> dict[str, Any]:
    if not enable_push:
        return {"requested": False, "pushed": False, "remote": remote, "branch": branch, "targets": []}
    targets: list[dict[str, Any]] = []
    if staging_remote:
        _git(workspace_path, "push", "-u", staging_remote, branch)
        targets.append({"remote": staging_remote, "branch": branch, "pushed": True, "role": "local_staging"})
    elif remote:
        _git(workspace_path, "push", "-u", remote, branch)
        targets.append({"remote": remote, "branch": branch, "pushed": True, "role": "primary"})
    if github_push_remote:
        _git(workspace_path, "push", "-u", github_push_remote, branch)
        targets.append({"remote": github_push_remote, "branch": branch, "pushed": True, "role": "github"})
    return {
        "requested": True,
        "pushed": bool(targets),
        "remote": remote,
        "branch": branch,
        "targets": targets,
        "push_policy": {
            "local_staging_required": bool(staging_remote),
            "github_push_remote": github_push_remote,
        },
    }


def _create_pr_if_requested(
    workspace_path: Path,
    *,
    title: str,
    body: str,
    draft: bool,
    enable_pr: bool,
) -> dict[str, Any]:
    if not enable_pr:
        return {"requested": False, "created": False, "url": ""}
    args = ["gh", "pr", "create", "--title", title, "--body", body]
    if draft:
        args.append("--draft")
    proc = _run_process(args, cwd=workspace_path)
    return {"requested": True, "created": True, "url": proc.stdout.strip()}


def _cleanup_safety_findings(
    *,
    commit_report: dict[str, Any],
    push_report: dict[str, Any],
    cleanup_requested: bool,
) -> list[str]:
    if not cleanup_requested:
        return []
    if commit_report.get("created", False) and not push_report.get("pushed", False):
        return ["cleanup_forbidden_with_unpushed_commit"]
    return []


def _runtime_context(
    *,
    repo_path: Path,
    prepared: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    bootstrap = prepared.get("bootstrap", {}) or {}
    active_node = bootstrap.get("active_node", {}) or {}
    active_contract = bootstrap.get("active_worker_contract", {}) or {}
    active_execplan = bootstrap.get("active_execplan", {}) or {}
    run_id = make_run_id(spec["worker_id"])
    trace_id = make_trace_id()
    push_targets = [
        {
            "remote": str((prepared.get("push_remote_config", {}) or {}).get("staging_remote", "")) or spec["push_remote"],
            "mode": str((prepared.get("push_remote_config", {}) or {}).get("mode", "not_configured")),
            "url": str((prepared.get("push_remote_config", {}) or {}).get("url", "")),
        }
    ]
    if spec.get("github_push_remote", ""):
        push_targets.append(
            {
                "remote": spec["github_push_remote"],
                "mode": "secondary_github",
                "url": "",
            }
        )
    metadata = create_run_metadata(
        root=repo_path,
        run_id=run_id,
        trace_id=trace_id,
        worker_id=spec["worker_id"],
        branch=spec["branch"],
        backend=spec["backend"],
        workspace_path=prepared["workspace_path"],
        initiative_id=str(active_node.get("node_id", "")).strip(),
        initiative_branch=str(active_node.get("initiative_branch", "")).strip(),
        contract_id=str(active_contract.get("contract_id", "")).strip(),
        execplan_id=str(active_execplan.get("id", "")).strip(),
        push_targets=push_targets,
        task_command=spec["task_command"],
    )
    append_runtime_event(
        root=repo_path,
        event_type="platform.worker.run.started",
        run_id=run_id,
        trace_id=trace_id,
        worker_id=spec["worker_id"],
        branch=spec["branch"],
        initiative_id=metadata["initiative_id"],
        contract_id=metadata["contract_id"],
        summary="worker run started",
        data={"executor_backend": spec["backend"]},
    )
    return metadata


def _problem_for_failure(
    *,
    repo_path: Path,
    metadata: dict[str, Any],
    error_code: str,
    title: str,
    detail: str,
    status: int,
    retryable: bool,
    what_you_should_do: str,
    artifact_refs: list[str] | None = None,
) -> dict[str, str]:
    problem_refs = write_problem_artifact(
        root=repo_path,
        run_id=metadata["run_id"],
        trace_id=metadata["trace_id"],
        initiative_id=metadata["initiative_id"],
        worker_id=metadata["worker_id"],
        contract_id=metadata["contract_id"],
        execplan_id=metadata["execplan_id"],
        branch=metadata["branch"],
        executor_backend=metadata["executor_backend"],
        error_code=error_code,
        title=title,
        detail=detail,
        status=status,
        retryable=retryable,
        what_you_should_do=what_you_should_do,
        artifact_refs=artifact_refs,
    )
    metadata["problem_ref"] = problem_refs["json"]
    update_run_metadata(root=repo_path, record=metadata)
    append_runtime_event(
        root=repo_path,
        event_type="platform.worker.run.problem_recorded",
        run_id=metadata["run_id"],
        trace_id=metadata["trace_id"],
        worker_id=metadata["worker_id"],
        branch=metadata["branch"],
        initiative_id=metadata["initiative_id"],
        contract_id=metadata["contract_id"],
        summary=title,
        data={"error_code": error_code, "problem_ref": problem_refs["json"]},
    )
    return problem_refs


def _finalize_runtime(
    *,
    repo_path: Path,
    metadata: dict[str, Any],
    status: str,
    outcome: str,
    commit_report: dict[str, Any],
    push_report: dict[str, Any],
    cleanup_performed: bool,
) -> dict[str, Any]:
    metadata["status"] = status
    metadata["outcome"] = outcome
    metadata["completed_at"] = metadata.get("completed_at") or utc_timestamp()
    metadata["commit"] = commit_report
    metadata["push"] = push_report
    metadata["cleanup_performed"] = cleanup_performed
    update_run_metadata(root=repo_path, record=metadata)
    append_runtime_event(
        root=repo_path,
        event_type="platform.worker.run.completed" if status == "completed" else "platform.worker.run.failed",
        run_id=metadata["run_id"],
        trace_id=metadata["trace_id"],
        worker_id=metadata["worker_id"],
        branch=metadata["branch"],
        initiative_id=metadata["initiative_id"],
        contract_id=metadata["contract_id"],
        summary=f"worker run {status}",
        data={"outcome": outcome, "run_path": metadata["run_path"]},
    )
    return metadata


def run_worker(
    *,
    repo_source: str,
    worker_id: str,
    base_ref: str = "main",
    branch: str | None = None,
    backend: str = "clone",
    workspace_root: str = DEFAULT_WORKSPACE_ROOT,
    task_command: str | None = None,
    commit_message: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    push_remote: str = "origin",
    github_push_remote: str | None = None,
    draft_pr: bool = False,
    commit: bool = False,
    push: bool = False,
    create_pr: bool = False,
    cleanup: bool = False,
) -> tuple[int, dict[str, Any]]:
    _, prepared = prepare_local_workspace(
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
        github_push_remote=github_push_remote,
        draft_pr=draft_pr,
        configure_push_remote=push or create_pr,
    )
    workspace_path = Path(prepared["workspace_path"])
    repo_path = Path(repo_source).expanduser().resolve()
    spec = json.loads((workspace_path / ".ephemeral-worker" / "spec.json").read_text(encoding="utf-8"))
    runtime = _runtime_context(repo_path=repo_path, prepared=prepared, spec=spec)
    task_report = {
        "command": spec["task_command"],
        "returncode": 0,
        "stdout": "",
        "stderr": "",
        "ok": True,
    }
    try:
        if spec["task_command"]:
            task_report = _run_task_command(spec["task_command"], workspace_path=workspace_path)
            append_runtime_event(
                root=repo_path,
                event_type="platform.worker.run.task_finished",
                run_id=runtime["run_id"],
                trace_id=runtime["trace_id"],
                worker_id=spec["worker_id"],
                branch=spec["branch"],
                initiative_id=runtime["initiative_id"],
                contract_id=runtime["contract_id"],
                summary="worker task finished",
                data={"ok": task_report["ok"], "returncode": task_report["returncode"]},
            )
            if task_report["returncode"] != 0:
                lease_report = _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="failed")
                problem_refs = _problem_for_failure(
                    repo_path=repo_path,
                    metadata=runtime,
                    error_code="WORKER_TASK_FAILED",
                    title="Worker task command failed",
                    detail=task_report["stderr"] or task_report["stdout"] or f"task exited with code {task_report['returncode']}",
                    status=422,
                    retryable=False,
                    what_you_should_do="Inspect the worker task output, repair the bounded task or contract, then rerun the worker.",
                    artifact_refs=[prepared["workspace_path"]],
                )
                runtime = _finalize_runtime(
                    repo_path=repo_path,
                    metadata=runtime,
                    status="failed",
                    outcome="failed",
                    commit_report={"requested": commit, "created": False, "sha": "", "changes": _working_tree_changes(workspace_path)},
                    push_report={"requested": push, "pushed": False, "remote": push_remote, "branch": spec["branch"], "targets": []},
                    cleanup_performed=False,
                )
                report = {
                    "command": COMMAND,
                    "status": "failed",
                    "ok": False,
                    "mode": "run",
                    "workspace_path": workspace_path.as_posix(),
                    "branch": spec["branch"],
                    "task": task_report,
                    "commit": {"requested": commit, "created": False, "sha": "", "changes": _working_tree_changes(workspace_path)},
                    "push": {"requested": push, "pushed": False, "remote": push_remote, "branch": spec["branch"], "targets": []},
                    "pull_request": {"requested": create_pr, "created": False, "url": ""},
                    "lease": lease_report,
                    "runtime": runtime,
                    "problem": problem_refs,
                    "cleanup_performed": False,
                }
                if cleanup:
                    _cleanup_workspace(backend=spec["backend"], repo_source=repo_source, workspace_path=workspace_path)
                    report["cleanup_performed"] = True
                return 1, report
        commit_report = _commit_if_needed(workspace_path, spec["commit_message"], enable_commit=commit)
        if create_pr and not push:
            raise RuntimeError("pull_request_requires_push")
        if create_pr and not spec.get("github_push_remote", ""):
            raise RuntimeError("pull_request_requires_github_push_remote")
        push_report = _push_if_requested(
            workspace_path,
            spec["push_remote"],
            spec["branch"],
            enable_push=push,
            staging_remote=str((prepared.get("push_remote_config", {}) or {}).get("staging_remote", "")),
            github_push_remote=str(spec.get("github_push_remote", "")),
        )
        cleanup_findings = _cleanup_safety_findings(
            commit_report=commit_report,
            push_report=push_report,
            cleanup_requested=cleanup,
        )
        if cleanup_findings:
            lease_report = _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="failed")
            problem_refs = _problem_for_failure(
                repo_path=repo_path,
                metadata=runtime,
                error_code="WORKER_CLEANUP_BLOCKED",
                title="Worker cleanup was blocked",
                detail="Cleanup would remove a workspace containing an unpushed commit.",
                status=409,
                retryable=False,
                what_you_should_do="Push the worker branch or rerun without cleanup so the commit stays recoverable.",
                artifact_refs=[prepared["workspace_path"]],
            )
            runtime = _finalize_runtime(
                repo_path=repo_path,
                metadata=runtime,
                status="failed",
                outcome="failed",
                commit_report=commit_report,
                push_report=push_report,
                cleanup_performed=False,
            )
            report = {
                "command": COMMAND,
                "status": "blocked",
                "ok": False,
                "mode": "run",
                "workspace_path": workspace_path.as_posix(),
                "branch": spec["branch"],
                "task": task_report,
                "commit": commit_report,
                "push": push_report,
                "pull_request": {"requested": create_pr, "created": False, "url": ""},
                "lease": lease_report,
                "runtime": runtime,
                "problem": problem_refs,
                "cleanup_performed": False,
                "blockers": cleanup_findings,
            }
            return 1, report
        pr_report = _create_pr_if_requested(
            workspace_path,
            title=spec["pr_title"],
            body=spec["pr_body"],
            draft=spec["draft_pr"],
            enable_pr=create_pr,
        )
        lease_report = _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="completed")
        cleaned = False
        if cleanup:
            _cleanup_workspace(backend=spec["backend"], repo_source=repo_source, workspace_path=workspace_path)
            cleaned = True
        if commit_report.get("created", False):
            append_runtime_event(
                root=repo_path,
                event_type="platform.worker.run.commit_created",
                run_id=runtime["run_id"],
                trace_id=runtime["trace_id"],
                worker_id=spec["worker_id"],
                branch=spec["branch"],
                initiative_id=runtime["initiative_id"],
                contract_id=runtime["contract_id"],
                summary="worker commit created",
                data={"sha": commit_report["sha"]},
            )
        if push_report.get("pushed", False):
            append_runtime_event(
                root=repo_path,
                event_type="platform.worker.run.push_succeeded",
                run_id=runtime["run_id"],
                trace_id=runtime["trace_id"],
                worker_id=spec["worker_id"],
                branch=spec["branch"],
                initiative_id=runtime["initiative_id"],
                contract_id=runtime["contract_id"],
                summary="worker push succeeded",
                data={"remote": push_report["remote"]},
            )
        runtime = _finalize_runtime(
            repo_path=repo_path,
            metadata=runtime,
            status="completed",
            outcome="completed",
            commit_report=commit_report,
            push_report=push_report,
            cleanup_performed=cleaned,
        )
        report = {
            "command": COMMAND,
            "status": "ok",
            "ok": True,
            "mode": "run",
            "workspace_path": workspace_path.as_posix(),
            "branch": spec["branch"],
            "task": task_report,
            "commit": commit_report,
            "push": push_report,
            "pull_request": pr_report,
            "lease": lease_report,
            "runtime": runtime,
            "cleanup_performed": cleaned,
        }
        return 0, report
    except Exception as exc:
        problem_refs = _problem_for_failure(
            repo_path=repo_path,
            metadata=runtime,
            error_code="WORKER_RUNTIME_EXCEPTION",
            title="Worker runtime raised an unexpected exception",
            detail=str(exc) or traceback.format_exc(),
            status=500,
            retryable=False,
            what_you_should_do="Inspect the runtime exception, repair the worker runtime or invocation, then rerun the worker.",
            artifact_refs=[prepared["workspace_path"]],
        )
        try:
            _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="abandoned")
        except Exception:
            pass
        _finalize_runtime(
            repo_path=repo_path,
            metadata=runtime,
            status="failed",
            outcome="abandoned",
            commit_report={"requested": commit, "created": False, "sha": "", "changes": []},
            push_report={"requested": push, "pushed": False, "remote": push_remote, "branch": spec["branch"], "targets": []},
            cleanup_performed=False,
        )
        if cleanup and workspace_path.exists():
            try:
                _cleanup_workspace(backend=spec["backend"], repo_source=repo_source, workspace_path=workspace_path)
            except Exception:
                pass
        raise RuntimeError(json.dumps({"error": str(exc), "problem": problem_refs}, sort_keys=True)) from exc


def render_azure_container_app_job(
    *,
    repo_source: str,
    worker_id: str,
    image: str,
    base_ref: str = "main",
    branch: str | None = None,
    backend: str = "clone",
    workspace_root: str = "/tmp/governed-workers",
    task_command: str | None = None,
    commit_message: str | None = None,
    pr_title: str | None = None,
    pr_body: str | None = None,
    push_remote: str = "origin",
    github_push_remote: str | None = None,
    draft_pr: bool = False,
    create_pr: bool = False,
    cpu: float = 2.0,
    memory: str = "4Gi",
) -> tuple[int, dict[str, Any]]:
    spec = _build_worker_spec(
        repo_source=repo_source,
        worker_id=worker_id,
        base_ref=base_ref,
        branch=branch,
        backend=backend,
        task_command=task_command,
        workspace_root=workspace_root,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        push_remote=push_remote,
        github_push_remote=github_push_remote,
        draft_pr=draft_pr,
    )
    container_command = [
        "python3",
        "-m",
        "platform_tools.governed_worker",
        "run",
        "--repo-source",
        spec["repo_source"],
        "--worker-id",
        spec["worker_id"],
        "--base-ref",
        spec["base_ref"],
        "--branch",
        spec["branch"],
        "--backend",
        "clone",
        "--workspace-root",
        "/tmp/governed-workers",
        "--commit",
        "--push",
        "--cleanup",
    ]
    if spec["task_command"]:
        container_command.extend(["--task-command", spec["task_command"]])
    if spec["commit_message"]:
        container_command.extend(["--commit-message", spec["commit_message"]])
    if spec["pr_title"]:
        container_command.extend(["--pr-title", spec["pr_title"]])
    if spec["pr_body"]:
        container_command.extend(["--pr-body", spec["pr_body"]])
    if spec["github_push_remote"]:
        container_command.extend(["--github-push-remote", spec["github_push_remote"]])
    if create_pr:
        container_command.append("--create-pr")
    if draft_pr:
        container_command.append("--draft-pr")
    job_name = f"gw-{_slugify(worker_id)}"
    job_payload = {
        "name": job_name[:32],
        "properties": {
            "configuration": {
                "triggerType": "Manual",
                "replicaRetryLimit": 0,
                "replicaTimeout": 1800,
                "manualTriggerConfig": {
                    "parallelism": 1,
                    "replicaCompletionCount": 1,
                },
            },
            "template": {
                "containers": [
                    {
                        "name": "worker",
                        "image": image,
                        "command": container_command,
                        "env": [
                            {"name": "GITHUB_TOKEN", "secretRef": "github-token"},
                        ],
                        "resources": {
                            "cpu": cpu,
                            "memory": memory,
                        },
                    }
                ]
            },
        },
    }
    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "mode": "render-azure-container-app-job",
        "platform": "azure-container-apps-jobs",
        "job_name": job_payload["name"],
        "image": image,
        "job_payload": job_payload,
        "required_secrets": ["github-token"],
        "required_tools_in_image": ["git", "gh", "python3"],
        "notes": [
            "Use a repo URL that the container can clone directly.",
            "The image must include this repository's code so python3 -m platform_tools.governed_worker is available.",
            "Azure Container Apps Jobs are intended for containerized tasks that run and then stop.",
        ],
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-source", required=True)
    common.add_argument("--worker-id", required=True)
    common.add_argument("--base-ref", default="main")
    common.add_argument("--branch", default=None)
    common.add_argument("--backend", default="worktree")
    common.add_argument("--workspace-root", default=DEFAULT_WORKSPACE_ROOT)
    common.add_argument("--task-command", default=None)
    common.add_argument("--commit-message", default=None)
    common.add_argument("--pr-title", default=None)
    common.add_argument("--pr-body", default=None)
    common.add_argument("--push-remote", default="origin")
    common.add_argument("--github-push-remote", default=None)
    common.add_argument("--draft-pr", action="store_true")

    subparsers.add_parser("prepare-local", parents=[common])

    run_parser = subparsers.add_parser("run", parents=[common])
    run_parser.add_argument("--commit", action="store_true")
    run_parser.add_argument("--push", action="store_true")
    run_parser.add_argument("--create-pr", action="store_true")
    run_parser.add_argument("--cleanup", action="store_true")
    run_parser.set_defaults(backend="clone")

    azure_parser = subparsers.add_parser("render-azure-container-app-job", parents=[common])
    azure_parser.add_argument("--image", required=True)
    azure_parser.add_argument("--create-pr", action="store_true")
    azure_parser.add_argument("--cpu", type=float, default=2.0)
    azure_parser.add_argument("--memory", default="4Gi")
    azure_parser.set_defaults(backend="clone", workspace_root="/tmp/governed-workers")

    args = parser.parse_args()
    kwargs = vars(args).copy()
    subcommand = kwargs.pop("subcommand")
    if subcommand == "prepare-local":
        code, report = prepare_local_workspace(**kwargs)
    elif subcommand == "run":
        code, report = run_worker(**kwargs)
    else:
        code, report = render_azure_container_app_job(**kwargs)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
