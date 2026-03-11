from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib import request

from platform_tools.integrations.provider_adapter import build_provider_projection, load_provider_mapping


GRAPHQL_URL = "https://api.github.com/graphql"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_finalization_state(item: dict[str, Any]) -> str:
    review_state = str(item.get("fields", {}).get("human_review_state", "")).strip()
    if review_state == "merged":
        return "merged_to_main"
    return "not_finalized"


def _augment_item(item: dict[str, Any], *, active_execplan_id: str, pr_url: str) -> dict[str, Any]:
    augmented = json.loads(json.dumps(item))
    if str(augmented.get("local_provenance", {}).get("target_execplan_id", "")).strip() == active_execplan_id:
        augmented["fields"]["pr_url"] = pr_url
    else:
        augmented["fields"]["pr_url"] = ""
    augmented["fields"]["finalization_state"] = _derive_finalization_state(augmented)
    return augmented


def _load_field_map(path: Path) -> dict[str, Any]:
    loaded = _load_json(path)
    if not isinstance(loaded, dict):
        raise ValueError("field_map_json_must_be_object")
    return loaded


def _field_update_specs(item: dict[str, Any], field_map: dict[str, Any]) -> list[dict[str, Any]]:
    fields_config = field_map.get("fields", {})
    if not isinstance(fields_config, dict):
        raise ValueError("field_map_missing_fields")
    updates: list[dict[str, Any]] = []
    for field_name, value in item.get("fields", {}).items():
        config = fields_config.get(field_name)
        if not isinstance(config, dict):
            continue
        data_type = str(config.get("data_type", "")).strip()
        field_id = str(config.get("field_id", "")).strip()
        if data_type == "title":
            continue
        if not field_id:
            raise ValueError(f"missing_field_id:{field_name}")
        update: dict[str, Any] = {
            "field_name": field_name,
            "field_id": field_id,
            "data_type": data_type,
        }
        if data_type == "text":
            update["value"] = str(value)
        elif data_type == "single_select":
            options = config.get("options", {})
            option_id = str(options.get(str(value), "")).strip() if isinstance(options, dict) else ""
            if not option_id:
                raise ValueError(f"missing_option_id:{field_name}:{value}")
            update["value"] = option_id
        else:
            raise ValueError(f"unsupported_field_data_type:{field_name}:{data_type}")
        updates.append(update)
    return updates


def _draft_issue_body(item: dict[str, Any]) -> str:
    provenance = item.get("local_provenance", {})
    lines = [
        f"node_id: {provenance.get('graph_node_id', '')}",
        f"target_execplan_id: {provenance.get('target_execplan_id', '')}",
        f"status: {item.get('fields', {}).get('status', '')}",
        f"gating_class: {item.get('fields', {}).get('gating_class', '')}",
        f"implementation_branch: {item.get('fields', {}).get('implementation_branch', '')}",
    ]
    return "\n".join(lines)


def build_github_projects_sync_plan(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    branch: str | None = None,
    project_id: str = "",
    field_map_path: str = "",
    dry_run: bool = True,
    pr_url: str = "",
) -> tuple[int, dict[str, Any]]:
    mapping = load_provider_mapping(root=root, provider="github_projects")
    projection_code, projection_report = build_provider_projection(
        root=root,
        provider="github_projects",
        branch=branch,
        execplan_path=execplan_path,
    )
    blockers: list[str] = []
    if projection_code != 0:
        blockers.extend(str(item) for item in projection_report.get("blockers", []))

    runtime_required = mapping.get("runtime_inputs", {}).get("required", [])
    config: dict[str, Any] = {}
    if field_map_path:
        config = _load_field_map(Path(field_map_path))
    elif "field_map_path" in runtime_required:
        blockers.append("field_map_path_required")

    effective_project_id = project_id or str(config.get("project_id", "")).strip()
    if not effective_project_id and "project_id" in runtime_required:
        blockers.append("project_id_required")

    active_execplan_id = str(projection_report.get("execplan_id", "")).strip()
    augmented_items = [_augment_item(item, active_execplan_id=active_execplan_id, pr_url=pr_url) for item in projection_report.get("items", [])]

    operations: list[dict[str, Any]] = []
    item_ids = config.get("item_ids_by_node_id", {}) if isinstance(config.get("item_ids_by_node_id"), dict) else {}
    for item in augmented_items:
        identity = str(item.get("identity", "")).strip()
        existing_item_id = str(item_ids.get(identity, "")).strip()
        op: dict[str, Any] = {
            "node_id": identity,
            "project_id": effective_project_id,
            "title": str(item.get("fields", {}).get("title", "")).strip(),
            "local_provenance": item.get("local_provenance", {}),
        }
        if existing_item_id:
            op["action"] = "update_item"
            op["item_id"] = existing_item_id
        else:
            op["action"] = "create_draft_item"
            op["draft_issue_body"] = _draft_issue_body(item)
        try:
            op["field_updates"] = _field_update_specs(item, config)
        except ValueError as exc:
            blockers.append(str(exc))
        operations.append(op)

    report = {
        "command": "github-projects-sync",
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "dry_run": dry_run,
        "provider_projection": projection_report,
        "project_id": effective_project_id,
        "field_map_path": field_map_path,
        "operation_count": len(operations),
        "operations": operations,
        "evidence_refs": sorted(
            {
                "artifacts/planner/research/remaining-work-graph.json",
                "spec/providers/github-projects.schema.yaml",
                "spec/provider-adapter.schema.yaml",
            }
        ),
    }
    return (1 if blockers else 0), report


def _graphql_request(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "platform-template-bootstrap/github-projects-sync",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def execute_github_projects_sync(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    branch: str | None = None,
    project_id: str = "",
    field_map_path: str = "",
    dry_run: bool = True,
    pr_url: str = "",
) -> tuple[int, dict[str, Any]]:
    code, plan = build_github_projects_sync_plan(
        root=root,
        execplan_path=execplan_path,
        branch=branch,
        project_id=project_id,
        field_map_path=field_map_path,
        dry_run=dry_run,
        pr_url=pr_url,
    )
    if code != 0 or dry_run:
        return code, plan

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        plan["status"] = "blocked"
        plan["ok"] = False
        plan["blockers"] = sorted(set(plan.get("blockers", []) + ["github_token_required"]))
        return 1, plan

    execution_results: list[dict[str, Any]] = []
    for op in plan.get("operations", []):
        item_id = str(op.get("item_id", "")).strip()
        if op.get("action") == "create_draft_item":
            mutation = """
            mutation($projectId: ID!, $title: String!, $body: String!) {
              addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
                projectItem { id }
              }
            }
            """
            response = _graphql_request(
                token,
                mutation,
                {
                    "projectId": op["project_id"],
                    "title": op["title"],
                    "body": op["draft_issue_body"],
                },
            )
            item_id = (
                response.get("data", {})
                .get("addProjectV2DraftIssue", {})
                .get("projectItem", {})
                .get("id", "")
            )
            execution_results.append({"action": "create_draft_item", "node_id": op["node_id"], "item_id": item_id, "response": response})

        for update in op.get("field_updates", []):
            if not item_id:
                execution_results.append({"action": "skip_field_update", "node_id": op["node_id"], "reason": "missing_item_id", "field_name": update["field_name"]})
                continue
            if update["data_type"] == "text":
                value_fragment = {"text": update["value"]}
            else:
                value_fragment = {"singleSelectOptionId": update["value"]}
            mutation = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
              updateProjectV2ItemFieldValue(
                input: {projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: $value}
              ) {
                projectV2Item { id }
              }
            }
            """
            response = _graphql_request(
                token,
                mutation,
                {
                    "projectId": op["project_id"],
                    "itemId": item_id,
                    "fieldId": update["field_id"],
                    "value": value_fragment,
                },
            )
            execution_results.append(
                {
                    "action": "update_field",
                    "node_id": op["node_id"],
                    "item_id": item_id,
                    "field_name": update["field_name"],
                    "response": response,
                }
            )

    plan["execution_results"] = execution_results
    return 0, plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--project-id", default="")
    parser.add_argument("--field-map-path", default="")
    parser.add_argument("--pr-url", default="")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    code, report = execute_github_projects_sync(
        root=args.root,
        execplan_path=args.execplan_path,
        branch=args.branch,
        project_id=args.project_id,
        field_map_path=args.field_map_path,
        dry_run=not args.execute,
        pr_url=args.pr_url,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
