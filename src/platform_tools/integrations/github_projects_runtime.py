from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import request

from platform_tools.integrations.provider_adapter import load_provider_mapping


GRAPHQL_URL = "https://api.github.com/graphql"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_github_projects_mapping(*, root: str = ".") -> dict[str, Any]:
    return load_provider_mapping(root=root, provider="github_projects")


def load_field_map(path: str | Path) -> dict[str, Any]:
    loaded = _load_json(Path(path))
    if not isinstance(loaded, dict):
        raise ValueError("field_map_json_must_be_object")
    return loaded


def github_graphql_request(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "platform-template-bootstrap/github-projects",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def github_token_from_env() -> str:
    return os.environ.get("GITHUB_TOKEN", "").strip()


def graphql_errors(response: dict[str, Any]) -> list[str]:
    errors = response.get("errors", [])
    if not isinstance(errors, list):
        return []
    messages: list[str] = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        message = str(error.get("message", "")).strip()
        if message:
            messages.append(message)
    return messages


def add_project_draft_item(*, token: str, project_id: str, title: str, body: str = "") -> dict[str, Any]:
    mutation = """
    mutation($projectId: ID!, $title: String!, $body: String!) {
      addProjectV2DraftIssue(input: {projectId: $projectId, title: $title, body: $body}) {
        projectItem {
          id
        }
      }
    }
    """
    return github_graphql_request(token, mutation, {"projectId": project_id, "title": title, "body": body})


def update_project_item_text_field(
    *,
    token: str,
    project_id: str,
    item_id: str,
    field_id: str,
    text: str,
) -> dict[str, Any]:
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { text: $text }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
    """
    return github_graphql_request(
        token,
        mutation,
        {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "text": text},
    )


def update_project_item_single_select_field(
    *,
    token: str,
    project_id: str,
    item_id: str,
    field_id: str,
    option_id: str,
) -> dict[str, Any]:
    mutation = """
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $singleSelectOptionId: String!) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { singleSelectOptionId: $singleSelectOptionId }
        }
      ) {
        projectV2Item {
          id
        }
      }
    }
    """
    return github_graphql_request(
        token,
        mutation,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "singleSelectOptionId": option_id,
        },
    )
