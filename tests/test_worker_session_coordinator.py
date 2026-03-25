from __future__ import annotations

from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.worker_session_coordinator import run_worker_session_coordinator


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
        "---\nid: \"plan-id\"\ntitle: \"Plan\"\nowner: \"agent/codex-01\"\ncreated: \"2026-03-24T00:00:00Z\"\nstatus: \"draft\"\nbase_branch: \"main\"\nchanges:\n  - .agent/execplans/plan.md\napprove_policy: \"codeowners\"\nreviewers: [\"github:test\"]\ndraft_by: \"agent/codex-01\"\ndraft_branch: \"draft-execplan/plan\"\ndraft_created: \"2026-03-24T00:00:00Z\"\nfinalized_by: \"\"\nfinalized_at: \"\"\nfinalized_in_pr: \"\"\n---\n\n# Purpose / Big Picture\n",
        encoding="utf-8",
    )
    (repo / "spec").mkdir(parents=True, exist_ok=True)
    (repo / "spec" / "workflow.yaml").write_text(
        "execution_requirements:\n  initiative_requirements:\n    fail_closed_on_missing_initiative_mapping: true\n    normal_governed_work_requires_initiative_branch: true\n",
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
        f'{{"nodes":[{{"node_id":"initiative-example","initiative_branch":"initiative/example","parent_initiative_node":"initiative-example"}},{{"node_id":"rwg-1","target_execplan_id":"plan-id","implementation_branch":"{implementation_branch}","integration_mode":"via_initiative","initiative_branch":"initiative/example","parent_initiative_node":"initiative-example"}}]}}\n',
        encoding="utf-8",
    )
    (repo / "artifacts" / "governance" / "initiative-worker-contracts").mkdir(parents=True, exist_ok=True)
    (repo / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json").write_text(
        f'{{"initiative_branch":"initiative/example","contracts":[{{"contract_id":"contract-1","title":"Worker contract","status":"ready","execplan_id":"plan-id","initiative_branch":"initiative/example","branch":"{implementation_branch}","worker_id":"coord-main","queue_position":1,"scope":{{"owned_surfaces":["README.md"],"non_goals":["Do not widen scope"],"validations":["uv run pytest -q tests/test_worker_session_coordinator.py"]}}}}]}}\n',
        encoding="utf-8",
    )
    _git(repo, "add", "README.md", ".agent", "spec", "project.rules.yaml", "artifacts")
    _git(repo, "commit", "-m", "seed")
    return repo


def test_worker_session_coordinator_runs_full_flow(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, implementation_branch="impl-execplan/coord-main")

    code, report = run_worker_session_coordinator(
        repo_source=repo.as_posix(),
        worker_id="coord-main",
        branch="impl-execplan/coord-main",
        backend="clone",
        workspace_root=(tmp_path / "workspaces").as_posix(),
        task_command="printf 'hello\\n' > note.txt",
        commit=True,
        cleanup=False,
    )

    assert code == 0
    assert report["lease"]["ok"] is True
    assert report["worker_run"]["ok"] is True
    assert report["runtime_graph"]["ok"] is True
    assert report["runtime_graph"]["node_id"] == "rwg-1"
    assert report["worker_status"]["counts"]["closed"] == 1
    assert report["worker_status"]["counts"]["active"] == 0
