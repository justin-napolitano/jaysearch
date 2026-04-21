from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.execplan_lint import run


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan_text(*, include_policy_check: bool) -> str:
    validation_block = [
        '    - name: "execplan-validate"',
        '      command: "bin/execplan-validate .agent/execplans/20260312-test-plan-codex-01-execplan.md"',
        "      expected_exit: 0",
    ]
    if include_policy_check:
        validation_block.extend(
            [
                '    - name: "policy-compliance-check"',
                '      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260312-test-plan-codex-01-execplan.md"',
                "      expected_exit: 0",
            ]
        )
    validation_text = "\n".join(validation_block)
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
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
{validation_text}
---

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

## Artifacts and Notes

Test.
"""


def _init_repo(root: Path) -> Path:
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Tests"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=root, check=True, capture_output=True, text=True)
    _write(root / "README.md", "base\n")
    _write(
        root / "project.rules.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-12",
                "overlay:",
                "  required_check_names_add: []",
                "  forbidden_branches_add: []",
                "  allowed_branch_patterns_remove: []",
                "",
            ]
        ),
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "--no-gpg-sign", "-m", "docs: base"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "checkout", "-b", "impl-execplan/20260312-test-plan-codex-01-execplan-codex-01-20260312"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    plan = root / ".agent" / "execplans" / "20260312-test-plan-codex-01-execplan.md"
    return plan


def test_execplan_lint_requires_policy_compliance_validation_on_impl_branch(tmp_path: Path, monkeypatch) -> None:
    plan = _init_repo(tmp_path)
    _write(plan, _plan_text(include_policy_check=False))
    monkeypatch.chdir(tmp_path)

    code, report = run([plan.as_posix()])

    assert code == 1
    assert "missing_policy_compliance_validation" in report["results"][0]["errors"]


def test_execplan_lint_accepts_policy_compliance_validation_on_impl_branch(tmp_path: Path, monkeypatch) -> None:
    plan = _init_repo(tmp_path)
    _write(plan, _plan_text(include_policy_check=True))
    monkeypatch.chdir(tmp_path)

    code, report = run([plan.as_posix()])

    assert code == 0
    assert report["results"][0]["errors"] == []


def test_execplan_lint_allows_draft_plan_on_initiative_branch_without_draft_branch(tmp_path: Path, monkeypatch) -> None:
    plan = _init_repo(tmp_path)
    subprocess.run(
        ["git", "checkout", "-b", "initiative/contract-first-planning"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    _write(plan, _plan_text(include_policy_check=False))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "platform_tools.execplan_lint.evaluate_branch_policy",
        lambda branch: {
            "ok": True,
            "current_branch": branch,
            "forbidden_branches": [],
            "allowed_branch_patterns": [],
            "findings": [],
        },
    )

    code, report = run([plan.as_posix()])

    assert code == 0
    assert report["results"][0]["errors"] == []
