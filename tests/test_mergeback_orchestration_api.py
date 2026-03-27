from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.mergeback_orchestration import (
    API_VERSION,
    prepare_next_impl_branch,
    project_merge_readiness,
    project_pr_integration_contract,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_execplan(root: Path, execplan_id: str) -> Path:
    path = root / ".agent" / "execplans" / f"{execplan_id}.md"
    _write(
        path,
        f"""---
id: "{execplan_id}"
title: "Test mergeback plan"
owner: "agent/codex-01"
created: "2026-03-27T00:00:00Z"
status: draft
base_branch: initiative/example
changes:
  - .agent/execplans/{execplan_id}.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/test"
draft_created: "2026-03-27T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/{execplan_id}.md"
      expected_exit: 0
    - name: "smoke"
      command: "bin/smoke-pass"
      expected_exit: 0
---

# Purpose / Big Picture

Test.
""",
    )
    return path


def test_get_pr_integration_contract_resolves_initiative_target(tmp_path: Path) -> None:
    execplan_id = "20260327-test-plan"
    _seed_execplan(tmp_path, execplan_id)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "nodes": [
                {
                    "node_id": "rwg-1",
                    "target_execplan_id": execplan_id,
                    "implementation_branch": "impl-execplan/example",
                    "initiative_branch": "initiative/example",
                    "integration_mode": "via_initiative",
                }
            ]
        },
    )

    code, report = project_pr_integration_contract(
        root=tmp_path.as_posix(),
        source_branch="impl-execplan/example",
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["target_branch"] == "initiative/example"
    assert report["integration_mode"] == "via_initiative"
    assert "bin/merge-readiness-check" in report["required_validations"]
    assert report["next_action"] == "open_pr_to_initiative"


def test_get_merge_readiness_projects_existing_check(monkeypatch, tmp_path: Path) -> None:
    execplan_id = "20260327-test-plan"
    _seed_execplan(tmp_path, execplan_id)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "nodes": [
                {
                    "node_id": "rwg-1",
                    "target_execplan_id": execplan_id,
                    "implementation_branch": "impl-execplan/example",
                    "initiative_branch": "initiative/example",
                    "integration_mode": "via_initiative",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration.check_merge_readiness",
        lambda **kwargs: (
            0,
            {
                "failing_checks": [],
                "checks": {
                    "validations": [
                        {"command": "bin/execplan-validate", "ok": True},
                        {"command": "bin/policy-compliance-check", "ok": True},
                    ]
                },
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._stale_initiative_base",
        lambda *args, **kwargs: False,
    )

    code, report = project_merge_readiness(
        root=tmp_path.as_posix(),
        source_branch="impl-execplan/example",
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["target_branch"] == "initiative/example"
    assert report["blockers"] == []
    assert report["next_action"] == "open_pr_to_initiative"


def test_get_merge_readiness_blocks_on_ambiguous_mapping(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "nodes": [
                {"implementation_branch": "impl-execplan/example", "initiative_branch": "initiative/a"},
                {"implementation_branch": "impl-execplan/example", "initiative_branch": "initiative/b"},
            ]
        },
    )

    code, report = project_merge_readiness(
        root=tmp_path.as_posix(),
        source_branch="impl-execplan/example",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert report["blockers"] == ["ambiguous_initiative_mapping"]
    assert report["next_action"] == "resolve_initiative_target"


def test_get_merge_readiness_blocks_when_impl_is_stale_against_initiative(monkeypatch, tmp_path: Path) -> None:
    execplan_id = "20260327-test-plan"
    _seed_execplan(tmp_path, execplan_id)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "nodes": [
                {
                    "node_id": "rwg-1",
                    "target_execplan_id": execplan_id,
                    "implementation_branch": "impl-execplan/example",
                    "initiative_branch": "initiative/example",
                    "integration_mode": "via_initiative",
                }
            ]
        },
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration.check_merge_readiness",
        lambda **kwargs: (0, {"failing_checks": [], "checks": {"validations": []}}),
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._stale_initiative_base",
        lambda *args, **kwargs: True,
    )

    code, report = project_merge_readiness(
        root=tmp_path.as_posix(),
        source_branch="impl-execplan/example",
    )

    assert code == 1
    assert report["blockers"] == ["stale_initiative_base"]
    assert report["next_action"] == "restack_on_initiative"
    assert report["problem"]["type"].endswith("/stale-initiative-base")


def test_prepare_next_impl_branch_blocks_on_unmerged_prior_slice(monkeypatch, tmp_path: Path) -> None:
    execplan_id = "20260327-test-plan"
    _seed_execplan(tmp_path, execplan_id)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "active_node": {"node_id": "rwg-2"},
            "nodes": [
                {
                    "node_id": "rwg-1",
                    "title": "Older slice",
                    "target_execplan_id": "older-plan",
                    "implementation_branch": "impl-execplan/older",
                    "initiative_branch": "initiative/example",
                    "parent_initiative_node": "initiative-example",
                    "status": "decision_gated",
                    "ordering": {"queue_position": 1},
                },
                {
                    "node_id": "rwg-2",
                    "title": "New slice",
                    "target_execplan_id": execplan_id,
                    "implementation_branch": "impl-execplan/new",
                    "initiative_branch": "initiative/example",
                    "parent_initiative_node": "initiative-example",
                    "status": "decision_gated",
                    "ordering": {"queue_position": 2},
                },
            ],
        },
    )
    monkeypatch.setattr("platform_tools.mergeback_orchestration.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._resolve_branch_ref",
        lambda *args, **kwargs: "HEAD",
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._prior_unmerged_impl_slices",
        lambda *args, **kwargs: [
            {
                "blocker": "prior_impl_slice_unmerged",
                "node_id": "rwg-1",
                "implementation_branch": "impl-execplan/older",
                "reason": "branch_not_merged_into_initiative",
            }
        ],
    )

    code, report = prepare_next_impl_branch(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 1
    assert report["blockers"] == ["prior_impl_slice_unmerged"]
    assert report["next_action"] == "resolve_prior_impl_slice"
