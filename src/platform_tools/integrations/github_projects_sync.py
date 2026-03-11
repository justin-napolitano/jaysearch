from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.integrations.github_projects_runtime import (
    add_project_draft_item,
    github_token_from_env,
    graphql_errors,
    load_field_map,
    load_github_projects_mapping,
    update_project_item_single_select_field,
    update_project_item_text_field,
    write_json,
)
from platform_tools.integrations.provider_adapter import build_provider_projection


def _provider_status_name(*, mapping: dict[str, Any], canonical_value: str) -> str:
    sync = mapping.get("sync", {}) if isinstance(mapping.get("sync"), dict) else {}
    provider_map = sync.get("provider_managed_value_map", {}) if isinstance(sync.get("provider_managed_value_map"), dict) else {}
    status_map = provider_map.get("status", {}) if isinstance(provider_map.get("status"), dict) else {}
    mapped = str(status_map.get(canonical_value, "")).strip()
    return mapped or canonical_value


def _field_entry(field_map: dict[str, Any], field_name: str) -> dict[str, Any]:
    fields = field_map.get("fields", {}) if isinstance(field_map.get("fields"), dict) else {}
    entry = fields.get(field_name, {})
    return entry if isinstance(entry, dict) else {}


def _resolve_single_select_value(
    *,
    mapping: dict[str, Any],
    field_map: dict[str, Any],
    field_name: str,
    canonical_value: str,
) -> tuple[str, str]:
    entry = _field_entry(field_map, field_name)
    options = entry.get("options", {}) if isinstance(entry.get("options"), dict) else {}
    provider_value = canonical_value
    if field_name == "status" and entry.get("provider_managed", False):
        provider_value = _provider_status_name(mapping=mapping, canonical_value=canonical_value)
    option_id = str(options.get(provider_value, "")).strip()
    return provider_value, option_id


def _field_updates_for_item(
    *,
    mapping: dict[str, Any],
    field_map: dict[str, Any],
    item: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    updates: list[dict[str, Any]] = []
    blockers: list[str] = []
    fields = item.get("fields", {}) if isinstance(item.get("fields"), dict) else {}
    for field_name, raw_value in fields.items():
        entry = _field_entry(field_map, field_name)
        data_type = str(entry.get("data_type", "")).strip()
        field_id = str(entry.get("field_id", "")).strip()
        if field_name == "title":
            continue
        if not field_id:
            blockers.append(f"missing_field_id:{field_name}")
            continue
        if data_type == "text":
            updates.append(
                {
                    "field_name": field_name,
                    "field_id": field_id,
                    "data_type": "text",
                    "value": str(raw_value),
                }
            )
            continue
        if data_type == "single_select":
            provider_value, option_id = _resolve_single_select_value(
                mapping=mapping,
                field_map=field_map,
                field_name=field_name,
                canonical_value=str(raw_value),
            )
            if not option_id:
                blockers.append(f"missing_option_id:{field_name}:{provider_value}")
                continue
            updates.append(
                {
                    "field_name": field_name,
                    "field_id": field_id,
                    "data_type": "single_select",
                    "value": str(raw_value),
                    "provider_value": provider_value,
                    "option_id": option_id,
                }
            )
            continue
        blockers.append(f"unsupported_field_type:{field_name}:{data_type}")
    return updates, blockers


def build_github_projects_sync_plan(
    *,
    root: str = ".",
    field_map_path: str,
    branch: str | None = None,
    execplan_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    mapping = load_github_projects_mapping(root=root)
    try:
        field_map = load_field_map(field_map_path)
    except FileNotFoundError:
        report = {
            "command": "github-projects-sync",
            "status": "blocked",
            "ok": False,
            "dry_run": True,
            "blockers": [f"field_map_not_found:{field_map_path}"],
            "project_id": "",
            "field_map_path": field_map_path,
            "operation_count": 0,
            "create_count": 0,
            "update_count": 0,
            "operations": [],
            "projection_summary": {"item_count": 0, "branch": str(branch or "").strip(), "execplan_id": ""},
            "evidence_refs": ["spec/providers/github-projects.schema.yaml"],
        }
        return 1, report
    projection_code, projection = build_provider_projection(
        root=root,
        provider="github_projects",
        branch=branch,
        execplan_path=execplan_path,
    )
    blockers = list(projection.get("blockers", [])) if isinstance(projection.get("blockers"), list) else []
    if projection_code != 0:
        blockers.append("projection_not_ready")

    project_id = str(field_map.get("project_id", "")).strip()
    if not project_id:
        blockers.append("missing_project_id")

    item_ids = field_map.get("item_ids_by_node_id", {}) if isinstance(field_map.get("item_ids_by_node_id"), dict) else {}
    operations: list[dict[str, Any]] = []
    for item in projection.get("items", []):
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("identity", "")).strip()
        item_id = str(item_ids.get(node_id, "")).strip()
        updates, update_blockers = _field_updates_for_item(mapping=mapping, field_map=field_map, item=item)
        blockers.extend(f"{node_id}:{value}" for value in update_blockers)
        operations.append(
            {
                "node_id": node_id,
                "item_id": item_id,
                "action": "update_item" if item_id else "create_draft_item",
                "title": str(item.get("fields", {}).get("title", "")).strip(),
                "local_provenance": item.get("local_provenance", {}),
                "field_updates": updates,
            }
        )

    report = {
        "command": "github-projects-sync",
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "dry_run": True,
        "blockers": sorted(set(blockers)),
        "project_id": project_id,
        "field_map_path": field_map_path,
        "operation_count": len(operations),
        "create_count": sum(1 for item in operations if item["action"] == "create_draft_item"),
        "update_count": sum(1 for item in operations if item["action"] == "update_item"),
        "operations": operations,
        "projection_summary": {
            "item_count": int(projection.get("item_count", 0)),
            "branch": str(projection.get("branch", branch or "")).strip(),
            "execplan_id": str(projection.get("execplan_id", "")).strip(),
        },
        "evidence_refs": sorted(
            {
                "artifacts/planner/research/remaining-work-graph.json",
                field_map_path,
                "spec/providers/github-projects.schema.yaml",
            }
        ),
    }
    return (1 if blockers else 0), report


def execute_github_projects_sync(
    *,
    root: str = ".",
    field_map_path: str,
    branch: str | None = None,
    execplan_path: str | None = None,
    dry_run: bool = True,
) -> tuple[int, dict[str, Any]]:
    code, plan = build_github_projects_sync_plan(
        root=root,
        field_map_path=field_map_path,
        branch=branch,
        execplan_path=execplan_path,
    )
    if code != 0 or dry_run:
        return code, plan

    token = github_token_from_env()
    if not token:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = ["github_token_required"]
        return 1, plan

    project_id = str(plan.get("project_id", "")).strip()
    field_map = load_field_map(field_map_path)
    item_ids = field_map.get("item_ids_by_node_id", {}) if isinstance(field_map.get("item_ids_by_node_id"), dict) else {}
    execution_results: list[dict[str, Any]] = []
    plan["dry_run"] = False
    for operation in plan.get("operations", []):
        if not isinstance(operation, dict):
            continue
        item_id = str(operation.get("item_id", "")).strip()
        if not item_id:
            body = json.dumps(operation.get("local_provenance", {}), indent=2, sort_keys=True)
            response = add_project_draft_item(
                token=token,
                project_id=project_id,
                title=str(operation.get("title", "")).strip(),
                body=body,
            )
            errors = graphql_errors(response)
            if errors:
                plan["status"] = "blocked"
                plan["ok"] = False
                plan["blockers"] = [f"github_graphql:{message}" for message in errors]
                plan["execution_results"] = execution_results + [
                    {"action": "create_draft_item", "node_id": operation.get("node_id", ""), "response": response}
                ]
                return 1, plan
            item_id = str(response.get("data", {}).get("addProjectV2DraftIssue", {}).get("projectItem", {}).get("id", "")).strip()
            item_ids[str(operation.get("node_id", "")).strip()] = item_id
            execution_results.append(
                {
                    "action": "create_draft_item",
                    "node_id": operation.get("node_id", ""),
                    "item_id": item_id,
                    "response": response,
                }
            )
        for update in operation.get("field_updates", []):
            if not isinstance(update, dict):
                continue
            if update.get("data_type") == "text":
                response = update_project_item_text_field(
                    token=token,
                    project_id=project_id,
                    item_id=item_id,
                    field_id=str(update.get("field_id", "")).strip(),
                    text=str(update.get("value", "")),
                )
            else:
                response = update_project_item_single_select_field(
                    token=token,
                    project_id=project_id,
                    item_id=item_id,
                    field_id=str(update.get("field_id", "")).strip(),
                    option_id=str(update.get("option_id", "")).strip(),
                )
            errors = graphql_errors(response)
            if errors:
                plan["status"] = "blocked"
                plan["ok"] = False
                plan["blockers"] = [f"github_graphql:{message}" for message in errors]
                plan["execution_results"] = execution_results + [
                    {
                        "action": "update_field",
                        "node_id": operation.get("node_id", ""),
                        "field_name": update.get("field_name", ""),
                        "response": response,
                    }
                ]
                return 1, plan
            execution_results.append(
                {
                    "action": "update_field",
                    "node_id": operation.get("node_id", ""),
                    "item_id": item_id,
                    "field_name": update.get("field_name", ""),
                    "response": response,
                }
            )

    field_map["item_ids_by_node_id"] = item_ids
    write_json(field_map_path, field_map)
    plan["field_map"] = field_map
    plan["execution_results"] = execution_results
    return 0, plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--field-map-path", required=True)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    code, report = execute_github_projects_sync(
        root=args.root,
        field_map_path=args.field_map_path,
        branch=args.branch,
        execplan_path=args.execplan_path,
        dry_run=not args.execute,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
