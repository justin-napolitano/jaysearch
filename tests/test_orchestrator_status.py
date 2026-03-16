from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrator_status import get_orchestrator_status


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_execplan(root: Path, branch: str) -> Path:
    path = root / ".agent" / "execplans" / "20260311-composite-orchestrator-status-codex-01-execplan.md"
    _write_text(
        path,
        "\n".join(
            [
                "---",
                'id: "20260311-composite-orchestrator-status-codex-01-execplan"',
                'title: "Composite Status"',
                'owner: "agent/codex-01"',
                'created: "2026-03-11T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - src/platform_tools/orchestrator_status.py",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                f'draft_branch: "{branch}"',
                'draft_created: "2026-03-11T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "validation:",
                "  tests:",
                '    - name: "execplan-validate"',
                '      command: "bin/execplan-validate .agent/execplans/20260311-composite-orchestrator-status-codex-01-execplan.md"',
                '      expected_exit: 0',
                '    - name: "orchestrator-status-smoke-test"',
                '      command: "bin/orchestrator-status-smoke-test"',
                '      expected_exit: 0',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    return path


def test_orchestrator_status_reports_active_ready_slice(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311"
    execplan_path = _seed_execplan(tmp_path, branch)

    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_rule_graph",
        lambda root=".": (0, {"ok": True, "blockers": [], "command": "rule-graph-check"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_citations",
        lambda root=".": (0, {"ok": True, "blockers": [], "command": "citation-check"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": branch,
                "blockers": [],
                "active_execplan": {
                    "id": "20260311-composite-orchestrator-status-codex-01-execplan",
                    "path": execplan_path.as_posix(),
                },
                "active_game": {"id": "game-implementation", "lineage": ["game-platform", "game-execplan", "game-implementation"]},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "errors": [],
                "active_node": {
                    "node_id": "rwg-002",
                    "title": "Composite orchestrator status command",
                    "status": "ready",
                    "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                    "implementation_branch": branch,
                },
                "ready_nodes": [
                    {
                        "node_id": "rwg-002",
                        "title": "Composite orchestrator status command",
                        "status": "ready",
                        "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                        "implementation_branch": branch,
                    }
                ],
                "blocked_nodes": [],
                "ordering": {"ready_execplan_ids": ["20260311-composite-orchestrator-status-codex-01-execplan"]},
                "queue_projection": {"projection_authority": "projection_only"},
                "action_required_nodes": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_merge_readiness",
        lambda **kwargs: (
            0,
            {
                "readiness": True,
                "failing_checks": [],
                "checks": {"validations": [], "validation_runs_included": False},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_policy_compliance",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_anti_cheat",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
                "status": "ok",
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_state_transition_legality",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
                "status": "ok",
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.get_human_operations_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.run_hostile_review",
        lambda **kwargs: (
            0,
            {
                "command": "hostile-review",
                "ok": True,
                "status": "ok",
                "findings": [],
                "review_state": "clean",
            },
        ),
    )

    code, report = get_orchestrator_status(
        root=tmp_path.as_posix(),
        branch=branch,
        execplan_path=execplan_path.as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["active_work"]["node_id"] == "rwg-002"
    assert report["next_actions"][0]["action"] == "continue_active_slice"
    assert report["ready_order"] == ["20260311-composite-orchestrator-status-codex-01-execplan"]
    assert report["checks"]["planner_score"]["status"] == "deferred"
    assert report["checks"]["remaining_work_graph"]["status"] == "ok"
    assert report["checks"]["anti_cheat"]["status"] == "ok"
    assert report["checks"]["state_transition"]["status"] == "ok"


def test_orchestrator_status_recommends_starting_ready_slice(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_rule_graph",
        lambda root=".": (0, {"ok": True, "blockers": [], "command": "rule-graph-check"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_citations",
        lambda root=".": (0, {"ok": True, "blockers": [], "command": "citation-check"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": "feature/no-active-slice",
                "blockers": [],
                "active_execplan": None,
                "active_game": {"id": "game-platform", "lineage": ["game-platform"]},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "errors": [],
                "active_node": None,
                "ready_nodes": [
                    {
                        "node_id": "rwg-002",
                        "title": "Composite orchestrator status command",
                        "status": "ready",
                        "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                        "implementation_branch": "impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311",
                    }
                ],
                "blocked_nodes": [
                    {
                        "node_id": "rwg-005",
                        "title": "Provider sync scaffolding",
                        "status": "review_gated",
                        "target_execplan_id": "20260311-provider-sync-scaffold-codex-01-execplan",
                        "implementation_branch": "",
                    }
                ],
                "ordering": {"ready_execplan_ids": ["20260311-composite-orchestrator-status-codex-01-execplan"]},
                "queue_projection": {"projection_authority": "projection_only"},
                "action_required_nodes": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_merge_readiness",
        lambda **kwargs: (
            0,
            {
                "readiness": True,
                "failing_checks": [],
                "checks": {"validations": [], "validation_runs_included": False},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_policy_compliance",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_anti_cheat",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
                "status": "ok",
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.check_state_transition_legality",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "blockers": [],
                "status": "ok",
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.get_human_operations_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrator_status.run_hostile_review",
        lambda **kwargs: (
            0,
            {
                "command": "hostile-review",
                "ok": True,
                "status": "ok",
                "findings": [],
                "review_state": "clean",
            },
        ),
    )

    code, report = get_orchestrator_status(root=tmp_path.as_posix(), branch="feature/no-active-slice")

    assert code == 0
    assert report["status"] == "ok"
    assert report["active_work"] is None
    assert report["next_actions"][0]["action"] == "start_ready_slice"
    assert report["next_actions"][0]["branch"] == "impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311"
