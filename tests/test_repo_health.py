from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import platform_tools.repo_health as repo_health


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_repo_health_treats_todo_as_non_blocking_projection(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / ".agent/AGENTS.md", "agents\n")
    _write(tmp_path / ".agent/PLANS.md", "plans\n")
    _write(tmp_path / ".agent/metrics.yml", "dq_weight: 0.25\n")
    _write(
        tmp_path / ".agent/execplans" / "20260318-sample-execplan.md",
        "\n".join(
            [
                "---",
                'id: "20260318-sample-execplan"',
                'title: "Sample"',
                'owner: "agent/codex-01"',
                'created: "2026-03-18T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - .agent/execplans/20260318-sample-execplan.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/20260318-sample-codex-01-20260318"',
                'draft_created: "2026-03-18T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "---",
                "",
                "# Purpose / Big Picture",
                "",
                "Test.",
                "",
                "## Progress",
                "",
                "- [ ] Test",
                "",
                "## Surprises & Discoveries",
                "",
                "None.",
                "",
                "## Decision Log",
                "",
                "None.",
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
                "## Concrete Steps",
                "",
                "1. Test.",
                "",
                "## Validation and Acceptance",
                "",
                "Test.",
                "",
                "## Idempotence and Recovery",
                "",
                "Test.",
                "",
                "## Artifacts and Notes",
                "",
                "Test.",
                "",
                "## Interfaces and Dependencies",
                "",
                "Test.",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "spec/governance.yaml",
        "\n".join(
            [
                "required_checks:",
                "  contract: []",
                "exception_lifecycle:",
                "  registry_path: .agent/governance/exceptions.yaml",
                "  required_fields: []",
                "  statuses: [active, expired, revoked]",
                "  renewal_window_days: 7",
                "  bypass_evidence_min_items: 1",
            ]
        )
        + "\n",
    )
    _write(tmp_path / "spec/ruleset.yaml", "execution_constraints:\n  allowed_branch_patterns: [draft-execplan/*]\n")
    _write(
        tmp_path / "spec/workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  protected_branches_disallowed_for_execution: [main, master]",
                "  workflow_branch_patterns:",
                "    draft_execplan: draft-execplan/*",
            ]
        )
        + "\n",
    )
    _write(tmp_path / ".agent/governance/exceptions.yaml", "exceptions: []\n")
    _write(tmp_path / "TODO.md", "# TODO list\n")

    monkeypatch.setattr(repo_health, "run_execplan_lint", lambda _paths: (0, {"error_count": 0, "results": [], "warning_count": 0}))
    monkeypatch.setattr(repo_health, "check_governance", lambda: (0, {"finding_count": 0, "findings": []}))
    monkeypatch.setattr(repo_health, "check_distribution", lambda: (0, {"finding_count": 0, "findings": []}))
    monkeypatch.setattr(repo_health, "check_adoption", lambda: (0, {"finding_count": 0, "findings": []}))
    monkeypatch.setattr(repo_health, "scan_repository", lambda _root: {"finding_count": 0})
    monkeypatch.setattr(repo_health, "_check_governance_files", lambda: (True, []))
    monkeypatch.setattr(repo_health, "evaluate_branch_policy", lambda _branch: {"ok": True})
    monkeypatch.setattr(repo_health, "get_current_branch", lambda: "draft-execplan/20260318-sample-codex-01-20260318")

    code, report = repo_health.check_repository_health(tmp_path.as_posix())

    assert code == 0
    assert report["checks"]["todo_projection"]["ok"] is True
    assert report["checks"]["todo_projection"]["deprecated"] is True
    assert report["checks"]["todo_projection"]["authoritative"] is False
