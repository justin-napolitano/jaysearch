from __future__ import annotations

from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.execplan_discovery import discover_execplan


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    command = ["git", *args]
    if args and args[0] == "commit":
        command = ["git", "commit", "--no-gpg-sign", *args[1:]]
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)


def _plan(execplan_id: str, initiative_branch: str) -> str:
    return "\n".join(
        [
            "---",
            f'id: "{execplan_id}"',
            'title: "Plan"',
            'owner: "agent/codex-01"',
            'created: "2026-04-14T00:00:00Z"',
            'status: "draft"',
            'base_branch: "main"',
            "changes:",
            f"  - .agent/execplans/{execplan_id}.md",
            'approve_policy: "codeowners"',
            'reviewers: ["github:test"]',
            f'initiative_branch: "{initiative_branch}"',
            'finalized_by: ""',
            'finalized_at: ""',
            'finalized_in_pr: ""',
            "---",
            "",
            "## Outcomes & Retrospective",
            "",
            "Test.",
            "",
            "## Context and Orientation",
            "",
            "Test.",
            "",
            "## Plan of Work",
            "",
            "Test.",
            "",
            "## Validation and Acceptance",
            "",
            "Test.",
            "",
            "## Artifacts and Notes",
            "",
            "Test.",
            "",
        ]
    )


def test_discover_execplan_prefers_single_changed_plan_on_initiative_branch(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")

    first = tmp_path / ".agent" / "execplans" / "plan-a.md"
    second = tmp_path / ".agent" / "execplans" / "plan-b.md"
    _write(first, _plan("plan-a", "initiative/example"))
    _write(second, _plan("plan-b", "initiative/example"))
    _git(tmp_path, "add", ".agent/execplans/plan-a.md", ".agent/execplans/plan-b.md")
    _git(tmp_path, "commit", "-m", "docs(execplan): seed initiative plans")

    _git(tmp_path, "checkout", "-b", "initiative/example")
    _write(second, _plan("plan-b", "initiative/example").replace("Test.", "Updated.", 1))
    _git(tmp_path, "add", ".agent/execplans/plan-b.md")
    _git(tmp_path, "commit", "-m", "docs(execplan): update active initiative plan")

    selected, candidates, strategy = discover_execplan(tmp_path, "initiative/example", "main")

    assert selected == second
    assert candidates == [second.as_posix()]
    assert strategy == "initiative_branch_changed_files"
