from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.governed_worker import prepare_local_workspace, render_azure_container_app_job, run_worker
from platform_tools.session_bootstrap import run_worker_session_lease


def _git(root: Path, *args: str) -> str:
    command = ["git", *args]
    if args and args[0] == "commit":
        command = ["git", "-c", "commit.gpgsign=false", *args]
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _seed_repo(tmp_path: Path, *, implementation_branch: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    (repo / ".agent").mkdir(parents=True, exist_ok=True)
    (repo / ".agent" / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (repo / ".agent" / "PLANS.md").write_text("# PLANS\n", encoding="utf-8")
    (repo / ".agent" / "execplans").mkdir(parents=True, exist_ok=True)
    (repo / ".agent" / "execplans" / "plan.md").write_text(
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                'title: "Plan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-24T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - .agent/execplans/plan.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/plan"',
                'draft_created: "2026-03-24T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "spec").mkdir(parents=True, exist_ok=True)
    (repo / "spec" / "workflow.yaml").write_text(
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
                "    normal_governed_work_requires_initiative_branch: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "spec" / "ruleset.yaml").write_text(
        "execution_constraints:\n  allowed_branch_patterns: [initiative/*, draft-execplan/*, impl-execplan/*, queue-execplan/*]\n",
        encoding="utf-8",
    )
    (repo / "spec" / "governance.yaml").write_text("required_checks: {}\n", encoding="utf-8")
    (repo / "project.rules.yaml").write_text(
        "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n",
        encoding="utf-8",
    )
    (repo / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (repo / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-1",
                        "target_execplan_id": "plan-id",
                        "implementation_branch": implementation_branch,
                        "integration_mode": "via_initiative",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "artifacts" / "governance" / "initiative-worker-contracts").mkdir(parents=True, exist_ok=True)
    (repo / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json").write_text(
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": f"contract-{implementation_branch.split('/', 1)[1]}",
                        "title": "Worker contract",
                        "status": "ready",
                        "execplan_id": "plan-id",
                        "initiative_branch": "initiative/example",
                        "branch": implementation_branch,
                        "worker_id": implementation_branch.split("/", 1)[1],
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["README.md"],
                            "non_goals": ["Do not modify unrelated repo policy"],
                            "validations": ["uv run pytest -q tests/test_governed_worker.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "README.md")
    _git(repo, "add", ".agent", "spec", "project.rules.yaml", "artifacts")
    _git(repo, "commit", "-m", "seed")
    return repo


def test_prepare_local_workspace_creates_worktree(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/alpha-worker-main")
    workspace_root = tmp_path / "workspaces"
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/alpha-worker-main",
        worker_id="alpha-worker-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = prepare_local_workspace(
        repo_source=repo.as_posix(),
        worker_id="alpha worker",
        base_ref="main",
        backend="worktree",
        workspace_root=workspace_root.as_posix(),
    )

    assert code == 0
    workspace_path = Path(report["workspace_path"])
    assert workspace_path.exists()
    assert (workspace_path / ".ephemeral-worker" / "spec.json").exists()
    assert _git(workspace_path, "branch", "--show-current") == "impl-execplan/alpha-worker-main"
    assert report["bootstrap"]["ok"] is True


def test_run_worker_commits_changes_in_clone_workspace(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/beta-main")
    workspace_root = tmp_path / "workspaces"
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/beta-main",
        worker_id="beta-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = run_worker(
        repo_source=repo.as_posix(),
        worker_id="beta",
        base_ref="main",
        backend="clone",
        workspace_root=workspace_root.as_posix(),
        task_command="printf 'hello\\n' > note.txt",
        commit=True,
    )

    assert code == 0
    assert report["commit"]["created"] is True
    assert report["lease"]["lease"]["status"] == "closed"
    assert report["lease"]["lease"]["outcome"] == "completed"
    assert report["runtime"]["status"] == "completed"
    assert Path(report["runtime"]["run_path"]).exists()
    workspace_path = Path(report["workspace_path"])
    assert (workspace_path / "note.txt").read_text(encoding="utf-8") == "hello\n"
    assert _git(workspace_path, "log", "-1", "--pretty=%s") == "feat(worker): beta"
    audit_lines = (repo / "artifacts" / "governance" / "worker-session-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2
    runtime_lines = (repo / "artifacts" / "governance" / "worker-runtime-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(runtime_lines) >= 2


def test_run_worker_closes_lease_with_failed_outcome(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/fail-main")
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/fail-main",
        worker_id="fail-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = run_worker(
        repo_source=repo.as_posix(),
        worker_id="fail",
        base_ref="main",
        branch="impl-execplan/fail-main",
        backend="clone",
        workspace_root=(tmp_path / "workspaces").as_posix(),
        task_command="exit 7",
        cleanup=True,
    )

    assert code == 1
    assert report["lease"]["lease"]["status"] == "closed"
    assert report["lease"]["lease"]["outcome"] == "failed"
    assert report["runtime"]["problem_ref"].endswith(".problem.json")
    assert Path(report["problem"]["json"]).exists()
    audit_lines = (repo / "artifacts" / "governance" / "worker-session-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2


def test_run_worker_blocks_cleanup_when_commit_is_unpushed(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/cleanup-main")
    workspace_root = tmp_path / "workspaces"
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/cleanup-main",
        worker_id="cleanup-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = run_worker(
        repo_source=repo.as_posix(),
        worker_id="cleanup",
        base_ref="main",
        branch="impl-execplan/cleanup-main",
        backend="clone",
        workspace_root=workspace_root.as_posix(),
        task_command="printf 'hello\\n' > note.txt",
        commit=True,
        cleanup=True,
    )

    assert code == 1
    assert "cleanup_forbidden_with_unpushed_commit" in report["blockers"]
    assert report["cleanup_performed"] is False
    assert report["lease"]["lease"]["status"] == "closed"
    assert report["lease"]["lease"]["outcome"] == "failed"
    assert Path(report["problem"]["markdown"]).exists()
    workspace_path = Path(report["workspace_path"])
    assert workspace_path.exists()
    assert _git(workspace_path, "log", "-1", "--pretty=%s") == "feat(worker): cleanup"


def test_run_worker_pushes_to_local_bare_remote_and_cleans_up(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/push-main")
    workspace_root = tmp_path / "workspaces"
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/push-main",
        worker_id="push-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = run_worker(
        repo_source=repo.as_posix(),
        worker_id="push",
        base_ref="main",
        branch="impl-execplan/push-main",
        backend="clone",
        workspace_root=workspace_root.as_posix(),
        task_command="printf 'hello\\n' > note.txt",
        commit=True,
        push=True,
        cleanup=True,
    )

    assert code == 0
    assert report["push"]["pushed"] is True
    assert report["cleanup_performed"] is True
    assert Path(report["workspace_path"]).exists() is False
    assert report["runtime"]["outcome"] == "completed"
    bare_remote = repo / "artifacts" / "governance" / "staging-remotes" / "repo.git"
    assert bare_remote.exists()
    pushed_sha = _git(bare_remote, "rev-parse", "refs/heads/impl-execplan/push-main")
    assert pushed_sha == report["commit"]["sha"]
    assert report["push"]["targets"][0]["role"] == "local_staging"


def test_run_worker_can_dual_push_to_staging_and_github_remote(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/dual-main")
    github_remote = tmp_path / "github-remote.git"
    _git(tmp_path, "init", "--bare", github_remote.as_posix())
    _git(repo, "remote", "add", "github", github_remote.as_posix())
    workspace_root = tmp_path / "workspaces"
    lease_code, _ = run_worker_session_lease(
        root=repo.as_posix(),
        branch="impl-execplan/dual-main",
        worker_id="dual-main",
        action="issue",
    )

    assert lease_code == 0
    code, report = run_worker(
        repo_source=repo.as_posix(),
        worker_id="dual",
        base_ref="main",
        branch="impl-execplan/dual-main",
        backend="clone",
        workspace_root=workspace_root.as_posix(),
        task_command="printf 'hello\\n' > note.txt",
        commit=True,
        push=True,
        github_push_remote="github",
        cleanup=True,
    )

    assert code == 0
    targets = {item["role"]: item["remote"] for item in report["push"]["targets"]}
    assert targets["local_staging"] == "codex-staging"
    assert targets["github"] == "github"
    staging_remote = repo / "artifacts" / "governance" / "staging-remotes" / "repo.git"
    assert _git(staging_remote, "rev-parse", "refs/heads/impl-execplan/dual-main") == report["commit"]["sha"]
    assert _git(github_remote, "rev-parse", "refs/heads/impl-execplan/dual-main") == report["commit"]["sha"]


def test_prepare_local_workspace_blocks_without_bootstrap_mapping(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "seed")

    try:
        prepare_local_workspace(
            repo_source=repo.as_posix(),
            worker_id="delta",
            base_ref="main",
            branch="impl-execplan/delta-main",
            backend="clone",
            workspace_root=(tmp_path / "workspaces").as_posix(),
        )
    except RuntimeError as exc:
        assert "worker_bootstrap_blocked:" in str(exc)
    else:
        raise AssertionError("expected worker bootstrap to block")


def test_render_azure_container_app_job_uses_clone_backend() -> None:
    code, report = render_azure_container_app_job(
        repo_source="https://github.com/example/repo.git",
        worker_id="gamma",
        image="example.azurecr.io/platform-worker:latest",
        task_command="python3 -m pytest",
        create_pr=True,
    )

    assert code == 0
    command = report["job_payload"]["properties"]["template"]["containers"][0]["command"]
    assert "--backend" in command
    assert "clone" in command
    assert "--create-pr" in command
