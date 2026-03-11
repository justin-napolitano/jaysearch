from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.integrations.github_projects_runtime import build_github_projects_sync_plan


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_specs(root: Path) -> None:
    _write_text(
        root / "spec" / "remaining-work-graph.schema.yaml",
        "\n".join(
            [
                "version: 1",
                "required:",
                "  - graph_id",
                "  - created_at",
                "  - nodes",
                "  - edges",
                "properties:",
                "  nodes:",
                "    items:",
                "      required:",
                "        - node_id",
                "        - title",
                "        - status",
                "        - gating_class",
                "        - conflict_domains",
                "        - target_execplan_id",
                "      properties:",
                "        status:",
                '          enum: ["ready", "blocked", "review_gated", "decision_gated", "completed"]',
                "        gating_class:",
                '          enum: ["auto_runnable", "review_gated", "decision_gated"]',
                "  edges:",
                "    items:",
                "      required:",
                "        - from",
                "        - to",
                "        - relation",
                "      properties:",
                "        relation:",
                '          enum: ["depends_on", "conflicts_with", "informed_by", "gated_by"]',
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "provider-adapter.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "provider_adapter:",
                "  required_fields:",
                "    - provider",
                "    - projection_kind",
                "    - authority_mode",
                "    - identity_field",
                "    - supported_entities",
                "    - exported_fields",
                "    - conflict_policy",
                "    - human_portable",
                "    - agent_portable",
                "  authority_mode_allowed:",
                "    - projection_only",
                "  projection_kind_allowed:",
                "    - remaining_work_board",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "providers" / "github-projects.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "provider: github_projects",
                "projection_kind: remaining_work_board",
                "board_model:",
                "  board_scope: remaining_work_graph",
                "  item_identity_field: node_id",
                "required_board_fields:",
                "  - node_id",
                "  - title",
                "  - target_execplan_id",
                "  - status",
                "  - gating_class",
                "  - implementation_branch",
                "  - goal_area",
                "  - dependency_summary",
                "  - human_review_state",
                "runtime_inputs:",
                "  required:",
                "    - project_id",
                "    - field_map_path",
                "field_map:",
                "  title: title",
                "  node_id: text",
                "  target_execplan_id: text",
                "  status: single_select",
                "  gating_class: single_select",
                "  implementation_branch: text",
                "  goal_area: single_select",
                "  dependency_summary: text",
                "  human_review_state: single_select",
                "  pr_url: text",
                "  validation_status: single_select",
                "  smoke_status: single_select",
                "  merge_readiness: single_select",
                "  finalization_state: single_select",
                "finalization_state_options:",
                "  - not_finalized",
                "  - merged_to_main",
            ]
        )
        + "\n",
    )


def _seed_graph(root: Path) -> Path:
    execplan = root / ".agent" / "execplans" / "provider.md"
    _write_text(execplan, "\n".join(["---", 'id: "20260311-provider-sync-scaffold-codex-01-execplan"', "---", "", "# Purpose / Big Picture"]) + "\n")
    _write_json(
        root / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "completed",
                    "completion_ref": "merged:implementation-orchestrator-runtime",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["orchestrator-status"],
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "goal_area": "implementation-orchestrator",
                },
                {
                    "node_id": "rwg-005",
                    "title": "Provider sync scaffolding",
                    "status": "review_gated",
                    "status_reason": "human_review_required_before_external_sync",
                    "gating_class": "review_gated",
                    "conflict_domains": ["provider-sync"],
                    "target_execplan_id": "20260311-provider-sync-scaffold-codex-01-execplan",
                    "goal_area": "provider-sync",
                },
            ],
            "edges": [],
        },
    )
    return execplan


def test_github_projects_sync_plan_builds_dry_run_operations(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    execplan = _seed_graph(tmp_path)
    field_map_path = tmp_path / "field-map.json"
    _write_json(
        field_map_path,
        {
            "project_id": "PVT_project",
            "item_ids_by_node_id": {"rwg-004": "PVT_item_004"},
            "fields": {
                "node_id": {"field_id": "F1", "data_type": "text"},
                "target_execplan_id": {"field_id": "F2", "data_type": "text"},
                "status": {"field_id": "F3", "data_type": "single_select", "options": {"completed": "O_completed", "review_gated": "O_review"}},
                "gating_class": {"field_id": "F4", "data_type": "single_select", "options": {"auto_runnable": "O_auto", "review_gated": "O_rg"}},
                "implementation_branch": {"field_id": "F5", "data_type": "text"},
                "goal_area": {"field_id": "F6", "data_type": "single_select", "options": {"implementation-orchestrator": "O_impl", "provider-sync": "O_ps"}},
                "dependency_summary": {"field_id": "F7", "data_type": "text"},
                "human_review_state": {"field_id": "F8", "data_type": "single_select", "options": {"merged": "O_merged", "not_requested": "O_nr"}},
                "pr_url": {"field_id": "F9", "data_type": "text"},
                "validation_status": {"field_id": "F10", "data_type": "single_select", "options": {"passed": "O_passed", "pending": "O_pending"}},
                "smoke_status": {"field_id": "F11", "data_type": "single_select", "options": {"passed": "O_sp", "pending": "O_pen"}},
                "merge_readiness": {"field_id": "F12", "data_type": "single_select", "options": {"local_only": "O_local"}},
                "finalization_state": {"field_id": "F13", "data_type": "single_select", "options": {"merged_to_main": "O_fin", "not_finalized": "O_not"}},
            },
        },
    )

    code, report = build_github_projects_sync_plan(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        branch="impl-execplan/20260311-provider-sync-scaffold-codex-01-execplan-codex-01-20260311",
        field_map_path=field_map_path.as_posix(),
        pr_url="https://github.com/example/repo/pull/123",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["dry_run"] is True
    assert report["operations"][0]["action"] == "update_item"
    assert report["operations"][1]["action"] == "create_draft_item"
    active_op = next(op for op in report["operations"] if op["node_id"] == "rwg-005")
    pr_update = next(update for update in active_op["field_updates"] if update["field_name"] == "pr_url")
    assert pr_update["value"] == "https://github.com/example/repo/pull/123"


def test_github_projects_sync_plan_requires_field_map(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    execplan = _seed_graph(tmp_path)

    code, report = build_github_projects_sync_plan(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        branch="impl-execplan/20260311-provider-sync-scaffold-codex-01-execplan-codex-01-20260311",
    )

    assert code == 1
    assert "field_map_path_required" in report["blockers"]
