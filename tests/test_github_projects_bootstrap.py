from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.integrations import github_projects_bootstrap as bootstrap


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_mapping(root: Path) -> None:
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
                '  default_title: "Platform Execution Board"',
                "field_map:",
                "  node_id: text",
                "  title: title",
                "  target_execplan_id: text",
                "  status: single_select",
                "  gating_class: single_select",
                "  implementation_branch: text",
                "  completion_pr: text",
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
                "  supports_project_creation: true",
                "  supports_field_creation: true",
                "  emits_field_map_contract: github_projects_sync_v1",
                "  default_field_map_output_path: artifacts/provider-sync/github-projects-field-map.json",
                "  provider_managed_fields:",
                "    - status",
            ]
        )
        + "\n",
    )


def test_build_bootstrap_plan_uses_schema_blueprint(tmp_path: Path) -> None:
    _seed_mapping(tmp_path)

    code, report = bootstrap.build_bootstrap_plan(
        root=tmp_path.as_posix(),
        owner="example-org",
        owner_type="organization",
        field_map_output_path=(tmp_path / "field-map.json").as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["title"] == "Platform Execution Board"
    assert report["project_create"]["owner"] == "example-org"
    assert report["field_map_preview"]["fields"]["title"]["field_id"] == "builtin:title"
    status_field = next(field for field in report["field_creates"] if field["field_name"] == "status")
    assert status_field["provider_managed"] is True
    assert status_field["options"] == ["ready", "blocked", "review_gated", "decision_gated", "completed"]
    assert report["field_map_preview"]["fields"]["status"]["options"]["ready"] == "pending:status:ready"
    assert report["field_map_preview"]["fields"]["status"]["provider_managed"] is True


def test_execute_bootstrap_writes_sync_compatible_field_map(tmp_path: Path, monkeypatch) -> None:
    _seed_mapping(tmp_path)
    output_path = tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json"

    monkeypatch.setattr(bootstrap, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        bootstrap,
        "resolve_owner_id",
        lambda **_: ("OWNER123", {"data": {"organization": {"id": "OWNER123"}}}),
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project",
        lambda **_: {"data": {"createProjectV2": {"projectV2": {"id": "PVT_123", "title": "Board"}}}},
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project_field",
        lambda **kwargs: {
            "data": {
                "createProjectV2Field": {
                    "projectV2Field": {
                        "id": f"FIELD_{kwargs['field_name']}",
                        "name": kwargs["field_name"],
                    }
                }
            }
        },
    )
    monkeypatch.setattr(
        bootstrap,
        "list_project_fields",
        lambda **_: {
            "data": {
                "node": {
                    "fields": {
                        "nodes": [
                            {"id": "FIELD_node_id", "name": "node_id", "dataType": "TEXT"},
                            {"id": "FIELD_target_execplan_id", "name": "target_execplan_id", "dataType": "TEXT"},
                            {"id": "FIELD_completion_pr", "name": "completion_pr", "dataType": "TEXT"},
                            {
                                "id": "FIELD_status",
                                "name": "status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_READY", "name": "ready"},
                                    {"id": "OPT_BLOCKED", "name": "blocked"},
                                ],
                            },
                            {
                                "id": "FIELD_finalization_state",
                                "name": "finalization_state",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_NOT_FINALIZED", "name": "not_finalized"},
                                    {"id": "OPT_MERGED", "name": "merged_to_main"},
                                ],
                            },
                        ]
                    }
                }
            }
        },
    )

    code, report = bootstrap.execute_bootstrap(
        root=tmp_path.as_posix(),
        owner="example-org",
        owner_type="organization",
        field_map_output_path=output_path.as_posix(),
        dry_run=False,
    )

    assert code == 0
    assert report["ok"] is True
    assert report["dry_run"] is False
    assert report["project_id"] == "PVT_123"
    field_map = json.loads(output_path.read_text(encoding="utf-8"))
    assert field_map["project_id"] == "PVT_123"
    assert field_map["fields"]["title"]["field_id"] == "builtin:title"
    assert field_map["fields"]["status"]["field_id"] == "FIELD_status"
    assert field_map["fields"]["completion_pr"]["field_id"] == "FIELD_completion_pr"
    assert field_map["fields"]["status"]["options"]["ready"] == "OPT_READY"
    assert field_map["fields"]["finalization_state"]["options"]["merged_to_main"] == "OPT_MERGED"


def test_execute_bootstrap_accepts_user_owner_lookup(tmp_path: Path, monkeypatch) -> None:
    _seed_mapping(tmp_path)
    output_path = tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json"

    monkeypatch.setattr(bootstrap, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        bootstrap,
        "resolve_owner_id",
        lambda **_: ("USER123", {"data": {"user": {"id": "USER123"}}}),
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project",
        lambda **_: {"data": {"createProjectV2": {"projectV2": {"id": "PVT_USER", "title": "Board"}}}},
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project_field",
        lambda **kwargs: {
            "data": {
                "createProjectV2Field": {
                    "projectV2Field": {
                        "id": f"FIELD_{kwargs['field_name']}",
                        "name": kwargs["field_name"],
                    }
                }
            }
        },
    )
    monkeypatch.setattr(
        bootstrap,
        "list_project_fields",
        lambda **_: {"data": {"node": {"fields": {"nodes": []}}}},
    )

    code, report = bootstrap.execute_bootstrap(
        root=tmp_path.as_posix(),
        owner="JNA31A_AIT",
        owner_type="user",
        field_map_output_path=output_path.as_posix(),
        dry_run=False,
    )

    assert code == 0
    assert report["ok"] is True
    assert report["project_id"] == "PVT_USER"


def test_execute_bootstrap_marks_live_mode_on_partial_failure(tmp_path: Path, monkeypatch) -> None:
    _seed_mapping(tmp_path)

    monkeypatch.setattr(bootstrap, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        bootstrap,
        "resolve_owner_id",
        lambda **_: ("USER123", {"data": {"user": {"id": "USER123"}}}),
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project",
        lambda **_: {"data": {"createProjectV2": {"projectV2": {"id": "PVT_FAIL", "title": "Board"}}}},
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project_field",
        lambda **kwargs: (
            {"errors": [{"message": "boom"}]}
            if kwargs["field_name"] == "gating_class"
            else {"data": {"createProjectV2Field": {"projectV2Field": {"id": f"FIELD_{kwargs['field_name']}"}}}}
        ),
    )

    code, report = bootstrap.execute_bootstrap(
        root=tmp_path.as_posix(),
        owner="JNA31A_AIT",
        owner_type="user",
        dry_run=False,
    )

    assert code == 1
    assert report["ok"] is False
    assert report["dry_run"] is False
    assert report["project_id"] == "PVT_FAIL"


def test_execute_bootstrap_discovers_provider_managed_status(tmp_path: Path, monkeypatch) -> None:
    _seed_mapping(tmp_path)
    output_path = tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json"
    created_fields: list[str] = []

    monkeypatch.setattr(bootstrap, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        bootstrap,
        "resolve_owner_id",
        lambda **_: ("USER123", {"data": {"user": {"id": "USER123"}}}),
    )
    monkeypatch.setattr(
        bootstrap,
        "create_project",
        lambda **_: {"data": {"createProjectV2": {"projectV2": {"id": "PVT_DISCOVER", "title": "Board"}}}},
    )

    def _create_field(**kwargs):
        created_fields.append(kwargs["field_name"])
        return {
            "data": {
                "createProjectV2Field": {
                    "projectV2Field": {
                        "id": f"FIELD_{kwargs['field_name']}",
                        "name": kwargs["field_name"],
                    }
                }
            }
        }

    monkeypatch.setattr(bootstrap, "create_project_field", _create_field)
    monkeypatch.setattr(
        bootstrap,
        "list_project_fields",
        lambda **_: {
            "data": {
                "node": {
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_BUILTIN",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_READY", "name": "ready"},
                                    {"id": "OPT_BLOCKED", "name": "blocked"},
                                ],
                            }
                        ]
                    }
                }
            }
        },
    )

    code, report = bootstrap.execute_bootstrap(
        root=tmp_path.as_posix(),
        owner="JNA31A_AIT",
        owner_type="user",
        field_map_output_path=output_path.as_posix(),
        dry_run=False,
    )

    assert code == 0
    assert report["ok"] is True
    assert "status" not in created_fields
    assert any(item["action"] == "discover_field" and item["field_name"] == "status" for item in report["execution_results"])
    field_map = json.loads(output_path.read_text(encoding="utf-8"))
    assert field_map["fields"]["status"]["field_id"] == "FIELD_STATUS_BUILTIN"
    assert field_map["fields"]["status"]["provider_managed"] is True


def test_execute_bootstrap_can_refresh_existing_project_field_map(tmp_path: Path, monkeypatch) -> None:
    _seed_mapping(tmp_path)
    output_path = tmp_path / "artifacts" / "provider-sync" / "github-projects-field-map.json"

    monkeypatch.setattr(bootstrap, "github_token_from_env", lambda: "token")
    monkeypatch.setattr(
        bootstrap,
        "resolve_owner_id",
        lambda **_: ("USER123", {"data": {"user": {"id": "USER123"}}}),
    )
    monkeypatch.setattr(
        bootstrap,
        "list_project_fields",
        lambda **_: {
            "data": {
                "node": {
                    "fields": {
                        "nodes": [
                            {
                                "id": "FIELD_STATUS_BUILTIN",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                                "options": [
                                    {"id": "OPT_READY", "name": "ready"},
                                ],
                            }
                        ]
                    }
                }
            }
        },
    )

    code, report = bootstrap.execute_bootstrap(
        root=tmp_path.as_posix(),
        owner="JNA31A_AIT",
        owner_type="user",
        field_map_output_path=output_path.as_posix(),
        existing_project_id="PVT_EXISTING",
        dry_run=False,
    )

    assert code == 0
    assert report["ok"] is True
    assert report["project_id"] == "PVT_EXISTING"
    assert any(item["action"] == "reuse_project" for item in report["execution_results"])
    field_map = json.loads(output_path.read_text(encoding="utf-8"))
    assert field_map["project_id"] == "PVT_EXISTING"
    assert field_map["fields"]["status"]["field_id"] == "FIELD_STATUS_BUILTIN"
