from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.integrations.github_projects_runtime import (
    create_project,
    create_project_field,
    github_token_from_env,
    graphql_errors,
    list_project_fields,
    load_github_projects_mapping,
    resolve_owner_id,
    write_json,
)


def _single_select_options(mapping: dict[str, Any], field_name: str) -> list[str]:
    options = mapping.get(f"{field_name}_options", [])
    if not isinstance(options, list):
        return []
    return [str(item).strip() for item in options if str(item).strip()]


def _bootstrap_contract_blockers(mapping: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    bootstrap = mapping.get("bootstrap", {}) if isinstance(mapping.get("bootstrap"), dict) else {}
    if not bootstrap.get("supports_project_creation", False):
        blockers.append("project_creation_not_supported")
    if not bootstrap.get("supports_field_creation", False):
        blockers.append("field_creation_not_supported")
    if not isinstance(mapping.get("field_map"), dict) or not mapping.get("field_map"):
        blockers.append("field_map_missing")
    return blockers


def _provider_managed_fields(mapping: dict[str, Any]) -> set[str]:
    bootstrap = mapping.get("bootstrap", {}) if isinstance(mapping.get("bootstrap"), dict) else {}
    fields = bootstrap.get("provider_managed_fields", [])
    if not isinstance(fields, list):
        return set()
    return {str(item).strip() for item in fields if str(item).strip()}


def _normalize_field_name(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_")


def _field_name_candidates(field_name: str) -> list[str]:
    normalized = _normalize_field_name(field_name)
    aliases = {
        "status": ["status", "Status"],
    }.get(normalized, [field_name])
    candidates = {normalized}
    for alias in aliases:
        alias_str = str(alias).strip()
        if alias_str:
            candidates.add(alias_str)
            candidates.add(_normalize_field_name(alias_str))
    return list(candidates)


def _build_field_blueprints(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    field_types = mapping.get("field_map", {}) if isinstance(mapping.get("field_map"), dict) else {}
    provider_managed = _provider_managed_fields(mapping)
    fields: list[dict[str, Any]] = []
    for field_name, field_type_value in field_types.items():
        field_type = str(field_type_value).strip()
        if field_type == "title":
            continue
        field_entry = {
            "field_name": str(field_name).strip(),
            "data_type": field_type,
            "provider_managed": str(field_name).strip() in provider_managed,
        }
        if field_type == "single_select":
            field_entry["options"] = _single_select_options(mapping, field_entry["field_name"])
        fields.append(field_entry)
    return fields


def _field_map_preview(fields: list[dict[str, Any]], output_path: str) -> dict[str, Any]:
    preview_fields: dict[str, Any] = {
        "title": {
            "field_id": "builtin:title",
            "data_type": "title",
        }
    }
    for field in fields:
        field_entry = {
            "field_id": f"pending:{field['field_name']}",
            "data_type": field["data_type"],
        }
        if field.get("provider_managed", False):
            field_entry["provider_managed"] = True
        if field["data_type"] == "single_select":
            field_entry["options"] = {name: f"pending:{field['field_name']}:{name}" for name in field.get("options", [])}
        preview_fields[field["field_name"]] = field_entry
    return {
        "project_id": "pending:project_id",
        "fields": preview_fields,
        "item_ids_by_node_id": {},
        "output_path": output_path,
    }


def build_bootstrap_plan(
    *,
    root: str = ".",
    owner: str,
    owner_type: str,
    title: str | None = None,
    field_map_output_path: str | None = None,
    existing_project_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    mapping = load_github_projects_mapping(root=root)
    blockers = _bootstrap_contract_blockers(mapping)
    board_model = mapping.get("board_model", {}) if isinstance(mapping.get("board_model"), dict) else {}
    board_title = title or str(board_model.get("default_title", "")).strip() or "Platform Execution Board"
    output_path = field_map_output_path or "artifacts/provider-sync/github-projects-field-map.json"
    fields = _build_field_blueprints(mapping)

    plan = {
        "command": "github-projects-bootstrap",
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "dry_run": True,
        "blockers": sorted(set(blockers)),
        "owner": owner,
        "owner_type": owner_type,
        "title": board_title,
        "field_map_output_path": output_path,
        "existing_project_id": str(existing_project_id or "").strip(),
        "project_create": {
            "owner": owner,
            "owner_type": owner_type,
            "title": board_title,
        },
        "field_creates": fields,
        "field_map_preview": _field_map_preview(fields, output_path),
        "evidence_refs": sorted(
            {
                "spec/providers/github-projects.schema.yaml",
                "spec/provider-adapter.schema.yaml",
            }
        ),
    }
    return (1 if blockers else 0), plan


def _graphql_field_type(data_type: str) -> str:
    return {
        "text": "TEXT",
        "single_select": "SINGLE_SELECT",
    }.get(data_type, "")


def _build_field_map_from_listing(
    *,
    mapping: dict[str, Any],
    project_id: str,
    field_listing: dict[str, Any],
) -> dict[str, Any]:
    field_nodes = (
        field_listing.get("data", {})
        .get("node", {})
        .get("fields", {})
        .get("nodes", [])
    )
    field_nodes = field_nodes if isinstance(field_nodes, list) else []
    field_lookup: dict[str, dict[str, Any]] = {}
    for field in field_nodes:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name", "")).strip()
        if not name:
            continue
        field_lookup[name] = field
        field_lookup[_normalize_field_name(name)] = field
    field_map = {
        "project_id": project_id,
        "fields": {
            "title": {
                "field_id": "builtin:title",
                "data_type": "title",
            }
        },
        "item_ids_by_node_id": {},
    }

    field_types = mapping.get("field_map", {}) if isinstance(mapping.get("field_map"), dict) else {}
    for field_name, data_type_value in field_types.items():
        field_name = str(field_name).strip()
        data_type = str(data_type_value).strip()
        if data_type == "title":
            continue
        listed = {}
        for candidate in _field_name_candidates(field_name):
            listed = field_lookup.get(candidate, {})
            if listed:
                break
        field_entry = {
            "field_id": str(listed.get("id", "")).strip(),
            "data_type": data_type,
        }
        if field_name in _provider_managed_fields(mapping):
            field_entry["provider_managed"] = True
        if data_type == "single_select":
            options = listed.get("options", [])
            option_map = {}
            if isinstance(options, list):
                for option in options:
                    if not isinstance(option, dict):
                        continue
                    name = str(option.get("name", "")).strip()
                    option_id = str(option.get("id", "")).strip()
                    if name and option_id:
                        option_map[name] = option_id
            field_entry["options"] = option_map
        field_map["fields"][field_name] = field_entry
    return field_map


def execute_bootstrap(
    *,
    root: str = ".",
    owner: str,
    owner_type: str,
    title: str | None = None,
    field_map_output_path: str | None = None,
    existing_project_id: str | None = None,
    dry_run: bool = True,
) -> tuple[int, dict[str, Any]]:
    code, plan = build_bootstrap_plan(
        root=root,
        owner=owner,
        owner_type=owner_type,
        title=title,
        field_map_output_path=field_map_output_path,
        existing_project_id=existing_project_id,
    )
    if code != 0 or dry_run:
        return code, plan

    token = github_token_from_env()
    if not token:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = ["github_token_required"]
        return 1, plan

    mapping = load_github_projects_mapping(root=root)
    owner_id, owner_response = resolve_owner_id(token=token, owner=owner, owner_type=owner_type)
    owner_errors = graphql_errors(owner_response)
    if owner_errors:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = [f"github_graphql:{message}" for message in owner_errors]
        plan["owner_lookup_response"] = owner_response
        return 1, plan
    if not owner_id:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = [f"owner_not_found:{owner_type}:{owner}"]
        plan["owner_lookup_response"] = owner_response
        return 1, plan

    plan["dry_run"] = False
    existing_id = str(existing_project_id or "").strip()
    execution_results: list[dict[str, Any]] = []
    if existing_id:
        project_id = existing_id
        execution_results.append(
            {
                "action": "reuse_project",
                "project_id": project_id,
            }
        )
    else:
        project_response = create_project(token=token, owner_id=owner_id, title=plan["title"])
        project_errors = graphql_errors(project_response)
        project_id = str(
            project_response.get("data", {}).get("createProjectV2", {}).get("projectV2", {}).get("id", "")
        ).strip()
        if project_errors or not project_id:
            plan["status"] = "blocked"
            plan["ok"] = False
            plan["blockers"] = (
                [f"github_graphql:{message}" for message in project_errors] if project_errors else ["project_creation_failed"]
            )
            plan["project_response"] = project_response
            return 1, plan
        execution_results.append(
            {
                "action": "create_project",
                "project_id": project_id,
                "response": project_response,
            }
        )
        for field in plan["field_creates"]:
            if field.get("provider_managed", False):
                execution_results.append(
                    {
                        "action": "discover_field",
                        "field_name": field["field_name"],
                        "provider_managed": True,
                    }
                )
                continue
            graphql_type = _graphql_field_type(str(field["data_type"]).strip())
            if not graphql_type:
                plan["status"] = "blocked"
                plan["ok"] = False
                plan["blockers"] = [f"unsupported_field_type:{field['field_name']}:{field['data_type']}"]
                return 1, plan
            response = create_project_field(
                token=token,
                project_id=project_id,
                field_name=str(field["field_name"]).strip(),
                data_type=graphql_type,
                single_select_options=list(field.get("options", [])),
            )
            field_errors = graphql_errors(response)
            if field_errors:
                plan["status"] = "blocked"
                plan["ok"] = False
                plan["blockers"] = [f"github_graphql:{message}" for message in field_errors]
                plan["project_id"] = project_id
                plan["execution_results"] = execution_results + [
                    {
                        "action": "create_field",
                        "field_name": field["field_name"],
                        "response": response,
                    }
                ]
                return 1, plan
            execution_results.append(
                {
                    "action": "create_field",
                    "field_name": field["field_name"],
                    "response": response,
                }
            )

    field_listing = list_project_fields(token=token, project_id=project_id)
    listing_errors = graphql_errors(field_listing)
    if listing_errors:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = [f"github_graphql:{message}" for message in listing_errors]
        plan["project_id"] = project_id
        plan["execution_results"] = execution_results
        plan["field_listing_response"] = field_listing
        return 1, plan

    field_map = _build_field_map_from_listing(mapping=mapping, project_id=project_id, field_listing=field_listing)
    output_path = Path(plan["field_map_output_path"])
    write_json(output_path, field_map)

    plan["project_id"] = project_id
    plan["field_map"] = field_map
    plan["execution_results"] = execution_results
    return 0, plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--owner-type", required=True, choices=["user", "organization"])
    parser.add_argument("--title", default=None)
    parser.add_argument("--field-map-output-path", default=None)
    parser.add_argument("--existing-project-id", default=None)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    code, report = execute_bootstrap(
        root=args.root,
        owner=args.owner,
        owner_type=args.owner_type,
        title=args.title,
        field_map_output_path=args.field_map_output_path,
        existing_project_id=args.existing_project_id,
        dry_run=not args.execute,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
