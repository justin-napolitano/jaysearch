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


def resolve_owner_id(*, token: str, owner: str, owner_type: str) -> tuple[str, dict[str, Any]]:
    owner_type_upper = owner_type.upper()
    if owner_type_upper not in {"USER", "ORGANIZATION"}:
        raise ValueError(f"unsupported_owner_type:{owner_type}")

    query = """
    query($login: String!) {
      user(login: $login) { id }
      organization(login: $login) { id }
    }
    """
    response = github_graphql_request(token, query, {"login": owner})
    node_key = "organization" if owner_type_upper == "ORGANIZATION" else "user"
    owner_id = str(response.get("data", {}).get(node_key, {}).get("id", "")).strip()
    return owner_id, response


def create_project(*, token: str, owner_id: str, title: str) -> dict[str, Any]:
    mutation = """
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 { id title }
      }
    }
    """
    return github_graphql_request(token, mutation, {"ownerId": owner_id, "title": title})


def create_project_field(
    *,
    token: str,
    project_id: str,
    field_name: str,
    data_type: str,
    single_select_options: list[str] | None = None,
) -> dict[str, Any]:
    mutation = """
    mutation(
      $projectId: ID!,
      $name: String!,
      $dataType: ProjectV2CustomFieldType!,
      $singleSelectOptions: [ProjectV2SingleSelectFieldOptionInput!]
    ) {
      createProjectV2Field(
        input: {
          projectId: $projectId,
          name: $name,
          dataType: $dataType,
          singleSelectOptions: $singleSelectOptions
        }
      ) {
        projectV2Field {
          ... on ProjectV2FieldCommon { id name }
        }
      }
    }
    """
    options = [{"name": option, "color": "GRAY"} for option in (single_select_options or [])]
    return github_graphql_request(
        token,
        mutation,
        {
            "projectId": project_id,
            "name": field_name,
            "dataType": data_type,
            "singleSelectOptions": options or None,
        },
    )


def list_project_fields(*, token: str, project_id: str) -> dict[str, Any]:
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          id
          fields(first: 100) {
            nodes {
              __typename
              ... on ProjectV2Field {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                dataType
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    return github_graphql_request(token, query, {"projectId": project_id})

