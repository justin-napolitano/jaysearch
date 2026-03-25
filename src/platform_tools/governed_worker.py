from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.session_bootstrap import run_session_bootstrap_check, run_worker_session_lease


COMMAND = "governed-worker"
DEFAULT_WORKSPACE_ROOT = ".tmp/governed-workers"
DEFAULT_LOCAL_PUSH_REMOTE_ROOT = ".tmp/governed-worker-remotes"
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
    remote_root = workspace_root / DEFAULT_LOCAL_PUSH_REMOTE_ROOT
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
        return {"mode": "passthrough", "remote": push_remote, "url": ""}
    if not _is_git_repo(source_repo) or _is_bare_repo(source_repo):
        return {"mode": "passthrough", "remote": push_remote, "url": ""}
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
    _git(workspace_path, "remote", "set-url", push_remote, bare_remote.as_posix())
    return {"mode": "local_bare_remote", "remote": push_remote, "url": bare_remote.as_posix()}


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
    push_remote_config = {"mode": "not_configured", "remote": spec["push_remote"], "url": ""}
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


def _push_if_requested(workspace_path: Path, remote: str, branch: str, *, enable_push: bool) -> dict[str, Any]:
    if not enable_push:
        return {"requested": False, "pushed": False, "remote": remote, "branch": branch}
    _git(workspace_path, "push", "-u", remote, branch)
    return {"requested": True, "pushed": True, "remote": remote, "branch": branch}


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
        draft_pr=draft_pr,
        configure_push_remote=push or create_pr,
    )
    workspace_path = Path(prepared["workspace_path"])
    repo_path = Path(repo_source).expanduser().resolve()
    spec = json.loads((workspace_path / ".ephemeral-worker" / "spec.json").read_text(encoding="utf-8"))
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
            if task_report["returncode"] != 0:
                lease_report = _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="failed")
                report = {
                    "command": COMMAND,
                    "status": "failed",
                    "ok": False,
                    "mode": "run",
                    "workspace_path": workspace_path.as_posix(),
                    "branch": spec["branch"],
                    "task": task_report,
                    "commit": {"requested": commit, "created": False, "sha": "", "changes": _working_tree_changes(workspace_path)},
                    "push": {"requested": push, "pushed": False, "remote": push_remote, "branch": spec["branch"]},
                    "pull_request": {"requested": create_pr, "created": False, "url": ""},
                    "lease": lease_report,
                    "cleanup_performed": False,
                }
                if cleanup:
                    _cleanup_workspace(backend=spec["backend"], repo_source=repo_source, workspace_path=workspace_path)
                    report["cleanup_performed"] = True
                return 1, report
        commit_report = _commit_if_needed(workspace_path, spec["commit_message"], enable_commit=commit)
        if create_pr and not push:
            raise RuntimeError("pull_request_requires_push")
        push_report = _push_if_requested(workspace_path, spec["push_remote"], spec["branch"], enable_push=push)
        cleanup_findings = _cleanup_safety_findings(
            commit_report=commit_report,
            push_report=push_report,
            cleanup_requested=cleanup,
        )
        if cleanup_findings:
            lease_report = _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="failed")
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
            "cleanup_performed": cleaned,
        }
        return 0, report
    except Exception:
        try:
            _close_lease(repo_root=repo_path, branch=spec["branch"], outcome="abandoned")
        except Exception:
            pass
        if cleanup and workspace_path.exists():
            try:
                _cleanup_workspace(backend=spec["backend"], repo_source=repo_source, workspace_path=workspace_path)
            except Exception:
                pass
        raise


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
