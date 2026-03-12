from __future__ import annotations

import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.finalize_execplan import finalize_execplan


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _base_repo(root: Path) -> Path:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Tests")
    _git(root, "config", "user.email", "tests@example.com")
    _write(
        root / ".agent" / "AGENTS.md",
        """# AGENTS.md

Initial human maintainer:

github:justin-napolitano
""",
    )
    _write(root / "README.md", "base\n")
    _git(root, "add", ".")
    _git(root, "commit", "--no-gpg-sign", "-m", "docs: base")
    return root / ".agent" / "execplans" / "20260312-test-plan-codex-01-execplan.md"


def _plan_text(draft_branch: str) -> str:
    return f"""---
id: "20260312-test-plan-codex-01-execplan"
title: "Test plan"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-test-plan-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "{draft_branch}"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-test-plan-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Test"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Test.

## Progress

- [ ] Test

## Surprises & Discoveries

None.

## Decision Log

None.

## Outcomes & Retrospective

Test.

## Context and Orientation

Test.

## Plan of Work

Test.

## Concrete Steps

1. Test.

## Validation and Acceptance

Test.

## Idempotence and Recovery

Test.

## Artifacts and Notes

Test.

## Interfaces and Dependencies

Test.
"""


def _commit_plan_branch(root: Path, branch: str, message: str) -> Path:
    _git(root, "checkout", "-b", branch)
    plan = root / ".agent" / "execplans" / "20260312-test-plan-codex-01-execplan.md"
    _write(plan, _plan_text(branch))
    _git(root, "add", str(plan.relative_to(root)))
    _git(root, "commit", "--no-gpg-sign", "-m", message)
    return plan


def _merge_branch(root: Path, branch: str, pr_number: int) -> None:
    _git(root, "checkout", "main")
    _git(
        root,
        "merge",
        "--no-ff",
        "--no-gpg-sign",
        branch,
        "-m",
        f"Merge pull request #{pr_number} from JNA31A_AIT/{branch}",
    )


def test_finalize_execplan_derives_completed_state_from_impl_merge(tmp_path: Path) -> None:
    plan = _base_repo(tmp_path)
    branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    _commit_plan_branch(tmp_path, branch, "docs(execplan): add test plan")
    _merge_branch(tmp_path, branch, 77)

    result = finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")

    assert result["status"] == "completed"
    assert result["finalized_by"] == "github:justin-napolitano"
    assert result["finalized_in_pr"] == "77"
    assert result["merge_evidence"]["merge_role"] == "impl-execplan"
    assert result["changed"] is True
    text = plan.read_text(encoding="utf-8")
    assert 'status: completed' in text


def test_finalize_execplan_prefers_impl_merge_over_draft_merge(tmp_path: Path) -> None:
    plan = _base_repo(tmp_path)
    draft_branch = "draft-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    impl_branch = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"
    _commit_plan_branch(tmp_path, draft_branch, "docs(execplan): add test plan")
    _merge_branch(tmp_path, draft_branch, 70)

    _git(tmp_path, "checkout", "-b", impl_branch, "main")
    _write(tmp_path / "README.md", "base\nimpl\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "--no-gpg-sign", "-m", "feat: add impl evidence")
    _merge_branch(tmp_path, impl_branch, 71)

    result = finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")

    assert result["finalized_in_pr"] == "71"
    assert result["merge_evidence"]["merge_role"] == "impl-execplan"


def test_finalize_execplan_blocks_when_merge_history_is_ambiguous(tmp_path: Path) -> None:
    plan = _base_repo(tmp_path)
    branch_one = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312-a"
    branch_two = "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312-b"
    _commit_plan_branch(tmp_path, branch_one, "docs(execplan): add test plan")
    _merge_branch(tmp_path, branch_one, 80)

    _git(tmp_path, "checkout", "-b", branch_two, "main")
    _write(tmp_path / "README.md", "base\nagain\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "--no-gpg-sign", "-m", "feat: add second impl evidence")
    _merge_branch(tmp_path, branch_two, 81)

    try:
        finalize_execplan(path=plan, repo_root=tmp_path, derive_from_merge=True, main_ref="main")
    except ValueError as exc:
        assert str(exc) == "ambiguous_merge_commit"
    else:
        raise AssertionError("expected ambiguous merge history to block reconciliation")
