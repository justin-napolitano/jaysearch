from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.integrations import github_projects_sync as sync


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_execplan(root: Path) -> Path:
    execplan = root / ".agent" / "execplans" / "github-projects-sync.md"
    _write_text(
        execplan,
        "\n".join(
            [
                "---",
                'id: "20260311-github-projects-provider-sync-runtime-codex-01-execplan"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    return execplan


def _seed_specs(root: Path) -> None:
    _write_text(
        root / "spec" / "remaining-work-graph.schema.yaml",
        "\n".join(
            [
                "version: 1",
                'title: "Remaining Work Graph Schema"',
                "type: object",
                "required:",
                "  - graph_id",
                "  - created_at",
                "  - nodes",
                "  - edges",
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
                "  item_type: slice_node",
                "field_map:",
                "  node_id: text",
                "  title: title",
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
                "status_options:",
                "  - ready",
                "  - blocked",
                "  - review_gated",
                "  - decision_gated",
                "  - completed",
                "gating_class_options:",
                "  - auto_runnable",
                "  - review_gated",
                "  - decision_gated",
                "goal_area_options:",
                "  - provider-sync",
                "  - governance",
                "human_review_state_options:",
                "  - not_requested",
                "  - ready_for_review",
                "  - in_review",
                "  - merged",
                "validation_status_options:",
                "  - pending",
                "  - passed",
                "  - failed",
                "smoke_status_options:",
                "  - pending",
                "  - passed",
                "  - failed",
                "merge_readiness_options:",
                "  - local_only",
                "  - ready",
                "  - blocked",
                "finalization_state_options:",
                "  - not_finalized",
                "  - merged_to_main",
                "bootstrap:",
                "  provider_managed_fields:",
                "    - status",
                "sync:",
                "  provider_managed_value_map:",
                "    status:",
                "      ready: Todo",
                "      blocked: In Progress",
                "      review_gated: In Progress",
                "      decision_gated: In Progress",
                "      completed: Done",
            ]
        )
        + "\n",
    )


def _seed_remaining_work(root: Path) -> None:
    _write_json(
        root / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {
                    "node_id": "rwg-005",
                    "title": "Provider sync runtime",
                    "status": "ready",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["provider-sync"],
                    "target_execplan_id": "20260311-github-projects-provider-sync-runtime-codex-01-execplan",
                    "goal_area": "provider-sync",
                    "implementation_branch": "impl-execplan/provider-sync",
                },
                {
                    "node_id": "rwg-004",
                    "title": "Bootstrap runtime",
                    "status": "completed",
                    "completion_ref": "merged:bootstrap",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["provider-sync"],
                    "target_execplan_id": "20260311-github-projects-bootstrap-runtime-codex-01-execplan",
                    "goal_area": "provider-sync",
                    "implementation_branch": "impl-execplan/bootstrap",
                },
            ],
            "edges": [
                {"from": "rwg-005", "to": "rwg-004", "relation": "depends_on"},
            ],
        },
    )


def _seed_field_map(root: Path) -> Path:
    path = root / "artifacts" / "provider-sync" / "github-projects-field-map.json"
    _write_json(
        path,
        {
            "project_id": "PVT_123",
            "fields": {
                "title": {"field_id": "builtin:title", "data_type": "title"},
                "node_id": {"field_id": "FIELD_node_id", "data_type": "text"},
                "target_execplan_id": {"field_id": "FIELD_target_execplan_id", "data_type": "text"},
                "status": {
                    "field_id": "FIELD_status",
                    "data_type": "single_select",
                    "provider_managed": True,
                    "options": {"Todo": "OPT_TODO", "In Progress": "OPT_PROGRESS", "Done": "OPT_DONE"},
                },
                "gating_class": {
                    "field_id": "FIELD_gating_class",
                    "data_type": "single_select",
                    "options": {
                        "auto_runnable": "OPT_AUTO",
                        "review_gated": "OPT_REVIEW",
                        "decision_gated": "OPT_DECISION",
                    },
                },
                "implementation_branch": {"field_id": "FIELD_branch", "data_type": "text"},
                "goal_area": {
                    "field_id": "FIELD_goal_area",
                    "data_type": "single_select",
                    "options": {"provider-sync": "OPT_PROVIDER", "governance": "OPT_GOV"},
                },
                "dependency_summary": {"field_id": "FIELD_dep", "data_type": "text"},
                "human_review_state": {
                    "field_id": "FIELD_review",
                    "data_type": "single_select",
                    "options": {
                        "not_requested": "OPT_NR",
                        "ready_for_review": "OPT_RFR",
                        "merged": "OPT_MERGED",
                    },
                },
                "pr_url": {"field_id": "FIELD_pr", "data_type": "text"},
                "validation_status": {
                    "field_id": "FIELD_validation",
                    "data_type": "single_select",
                    "options": {"pending": "OPT_PENDING", "passed": "OPT_PASSED", "failed": "OPT_FAILED"},
                },
                "smoke_status": {
                    "field_id": "FIELD_smoke",
                    "data_type": "single_select",
                    "options": {"pending": "OPT_PENDING", "passed": "OPT_PASSED", "failed": "OPT_FAILED"},
                },
                "merge_readiness": {
                    "field_id": "FIELD_merge",
                    "data_type": "single_select",
                    "options": {"local_only": "OPT_LOCAL", "ready": "OPT_READY", "blocked": "OPT_BLOCKED"},
                },
                "finalization_state": {
                    "field_id": "FIELD_finalization",
                    "data_type": "single_select",
                    "options": {"not_finalized": "OPT_NOT_FINAL", "merged_to_main": "OPT_FINAL"},
                },
            },
            "item_ids_by_node_id": {},
        },
    )
    return path


def test_build_sync_plan_maps_canonical_status_to_provider_status(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    _seed_remaining_work(tmp_path)
    execplan = _seed_execplan(tmp_path)
    field_map_path = _seed_field_map(tmp_path)

    code, report = sync.build_github_projects_sync_plan(
        root=tmp_path.as_posix(),
        field_map_path=field_map_path.as_posix(),
        branch="impl-execplan/provider-sync",
        execplan_path=execplan.as_posix(),
    )

    assert code == 0
    assert report["ok"] is True
    assert report["create_count"] == 2
    ready_op = next(item for item in report["operations"] if item["node_id"] == "rwg-005")
    status_update = next(item for item in ready_op["field_updates"] if item["field_name"] == "status")
    assert status_update["provider_value"] == "Todo"
    assert status_update["option_id"] == "OPT_TODO"
    completed_op = next(item for item in report["operations"] if item["node_id"] == "rwg-004")
    completed_status = next(item for item in completed_op["field_updates"] if item["field_name"] == "status")
    assert completed_status["provider_value"] == "Done"
    assert completed_status["option_id"] == "OPT_DONE"


def test_execute_sync_updates_field_map_with_created_item_ids(tmp_path: Path, monkeypatch) -> None:
    _seed_specs(tmp_path)
    _seed_remaining_work(tmp_path)
    execplan = _seed_execplan(tmp_path)
    field_map_path = _seed_field_map(tmp_path)

    monkeypatch.setattr(sync, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        sync,
        "add_project_draft_item",
        lambda **kwargs: {
            "data": {
                "addProjectV2DraftIssue": {
                    "projectItem": {
                        "id": f"ITEM_{kwargs['title'].replace(' ', '_')}",
                    }
                }
            }
        },
    )
    monkeypatch.setattr(
        sync,
        "update_project_item_text_field",
        lambda **kwargs: {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": kwargs["item_id"]}}}},
    )
    monkeypatch.setattr(
        sync,
        "update_project_item_single_select_field",
        lambda **kwargs: {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": kwargs["item_id"]}}}},
    )

    code, report = sync.execute_github_projects_sync(
        root=tmp_path.as_posix(),
        field_map_path=field_map_path.as_posix(),
        branch="impl-execplan/provider-sync",
        execplan_path=execplan.as_posix(),
        dry_run=False,
    )

    assert code == 0
    assert report["ok"] is True
    updated_field_map = json.loads(field_map_path.read_text(encoding="utf-8"))
    assert updated_field_map["item_ids_by_node_id"]["rwg-005"] == "ITEM_Provider_sync_runtime"
    assert updated_field_map["item_ids_by_node_id"]["rwg-004"] == "ITEM_Bootstrap_runtime"
