from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.human_operations_status import get_human_operations_status


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_plan(path: Path, *, plan_id: str, status: str, finalized_in_pr: str = "") -> None:
    _write_text(
        path,
        "\n".join(
            [
                "---",
                f'id: "{plan_id}"',
                f'status: "{status}"',
                f'finalized_in_pr: "{finalized_in_pr}"',
                'finalized_by: "github:jay.napolitano"' if status == "completed" else 'finalized_by: ""',
                'finalized_at: "2026-03-12T12:00:00Z"' if status == "completed" else 'finalized_at: ""',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )


def test_human_operations_status_reports_board_reuse_and_review_states(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260312-human-operations-review-runtime-codex-01-execplan-codex-01-20260312"
    _seed_plan(
        tmp_path / ".agent" / "execplans" / "20260312-execplan-finalization-completion-reconciliation-codex-01-execplan.md",
        plan_id="20260312-execplan-finalization-completion-reconciliation-codex-01-execplan",
        status="completed",
        finalized_in_pr="53",
    )
    _seed_plan(
        tmp_path / ".agent" / "execplans" / "20260312-human-operations-review-runtime-codex-01-execplan.md",
        plan_id="20260312-human-operations-review-runtime-codex-01-execplan",
        status="draft",
    )
    _write_json(
        tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json",
        {
            "project_id": "PVT_123",
            "fields": {"title": {"field_id": "builtin:title", "data_type": "title"}},
            "item_ids_by_node_id": {"rwg-009": "ITEM_9"},
        },
    )

    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "branch": branch,
                "execplan_id": "20260312-human-operations-review-runtime-codex-01-execplan",
                "active_node": {
                    "node_id": "rwg-010",
                    "title": "Human operations review runtime",
                    "status": "ready",
                    "target_execplan_id": "20260312-human-operations-review-runtime-codex-01-execplan",
                    "implementation_branch": branch,
                },
                "ready_nodes": [
                    {
                        "node_id": "rwg-010",
                        "title": "Human operations review runtime",
                        "status": "ready",
                        "target_execplan_id": "20260312-human-operations-review-runtime-codex-01-execplan",
                        "implementation_branch": branch,
                    }
                ],
                "blocked_nodes": [],
                "completed_nodes": [
                    {
                        "node_id": "rwg-009",
                        "title": "ExecPlan finalization completion reconciliation",
                        "status": "completed",
                        "target_execplan_id": "20260312-execplan-finalization-completion-reconciliation-codex-01-execplan",
                        "implementation_branch": "",
                    }
                ],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.build_github_projects_sync_plan",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "operation_count": 1,
                "create_count": 0,
                "update_count": 1,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_runtime.github_repo_http_url",
        lambda **kwargs: "https://github.com/JNA31A_AIT/codex_platform",
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_policy_compliance",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = get_human_operations_status(root=tmp_path.as_posix(), branch=branch)

    assert code == 0
    assert report["ok"] is True
    assert report["board_runtime"]["board_reuse_required"] is True
    assert report["board_runtime"]["prefer_update_when_item_id_known"] is True
    assert report["board_projection"]["update_count"] == 1
    assert report["review_summary"]["counts"]["merged"] == 1
    assert report["review_summary"]["counts"]["in_review"] == 1
    merged_node = next(item for item in report["review_nodes"] if item["node_id"] == "rwg-009")
    assert merged_node["pr_url"] == "https://github.com/JNA31A_AIT/codex_platform/pull/53"
    assert report["next_actions"][0]["action"] == "sync_review_board"


def test_human_operations_status_blocks_on_duplicate_item_ids(monkeypatch, tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json",
        {
            "project_id": "PVT_123",
            "fields": {"title": {"field_id": "builtin:title", "data_type": "title"}},
            "item_ids_by_node_id": {
                "rwg-001": "ITEM_DUP",
                "rwg-002": "ITEM_DUP",
            },
        },
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "branch": "main",
                "execplan_id": "",
                "active_node": None,
                "ready_nodes": [],
                "blocked_nodes": [],
                "completed_nodes": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.build_github_projects_sync_plan",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "operation_count": 0,
                "create_count": 0,
                "update_count": 0,
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_policy_compliance",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = get_human_operations_status(root=tmp_path.as_posix())

    assert code == 1
    assert report["status"] == "blocked"
    assert "board_runtime:duplicate_item_id:ITEM_DUP" in report["blockers"]


def test_human_operations_status_surfaces_graph_reconciliation_action(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260319-graph-transition-runtime"
    _seed_plan(
        tmp_path / ".agent" / "execplans" / "20260319-graph-transition-runtime-codex-01-execplan.md",
        plan_id="20260319-graph-transition-runtime-codex-01-execplan",
        status="draft",
        finalized_in_pr="91",
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "branch": branch,
                "execplan_id": "20260319-graph-transition-runtime-codex-01-execplan",
                "active_node": None,
                "ready_nodes": [],
                "blocked_nodes": [],
                "completed_nodes": [
                    {
                        "node_id": "rwg-027",
                        "title": "Graph transition runtime",
                        "status": "decision_gated",
                        "target_execplan_id": "20260319-graph-transition-runtime-codex-01-execplan",
                        "implementation_branch": branch,
                    }
                ],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.build_github_projects_sync_plan",
        lambda **kwargs: (
            0,
            {"status": "ok", "ok": True, "operation_count": 0, "create_count": 0, "update_count": 0, "blockers": []},
        ),
    )
    monkeypatch.setattr(
        "platform_tools.human_operations_status.check_policy_compliance",
        lambda **kwargs: (0, {"ok": True, "blockers": []}),
    )

    code, report = get_human_operations_status(root=tmp_path.as_posix(), branch=branch)

    assert code == 0
    assert report["ok"] is True
    assert report["next_actions"][0]["action"] == "reconcile_governed_graph_events"
