from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from platform_tools.human_operations_runtime import review_projection_for_node
from platform_tools.plan_utils import parse_plan
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def load_provider_contract(*, root: str = ".") -> dict[str, Any]:
    return _load_yaml(Path(root) / "spec" / "provider-adapter.schema.yaml")


def load_provider_mapping(*, root: str = ".", provider: str) -> dict[str, Any]:
    filename = {
        "github_projects": "github-projects.schema.yaml",
        "microsoft_lists": "microsoft-lists.schema.yaml",
    }.get(provider)
    if not filename:
        raise ValueError(f"unsupported_provider:{provider}")
    return _load_yaml(Path(root) / "spec" / "providers" / filename)


def _execplan_path_for_target(*, root: str, target_execplan_id: str) -> str:
    if not target_execplan_id:
        return ""
    candidate = Path(root) / ".agent" / "execplans" / f"{target_execplan_id}.md"
    return candidate.as_posix() if candidate.exists() else ""


def _provider_projection_blockers(
    *,
    contract: dict[str, Any],
    mapping: dict[str, Any],
    provider: str,
) -> list[str]:
    blockers: list[str] = []
    provider_contract = contract.get("provider_adapter", {}) if isinstance(contract.get("provider_adapter"), dict) else {}
    required_fields = provider_contract.get("required_fields", [])
    for field in required_fields:
        if field not in {
            "provider": provider,
            "projection_kind": mapping.get("projection_kind"),
            "authority_mode": "projection_only",
            "identity_field": mapping.get("board_model", {}).get("item_identity_field"),
            "supported_entities": ["remaining_work_node"],
            "exported_fields": sorted((mapping.get("required_board_fields") or mapping.get("required_list_fields") or [])),
            "conflict_policy": {
                "unresolved_conflict_resolution": "local_wins",
                "remote_authority": False,
            },
            "human_portable": True,
            "agent_portable": True,
        }:
            blockers.append(f"unsupported_required_field_contract:{field}")
    if mapping.get("projection_kind") not in provider_contract.get("projection_kind_allowed", []):
        blockers.append(f"projection_kind_not_allowed:{provider}:{mapping.get('projection_kind', '')}")
    if provider_contract.get("authority_mode_allowed", []) != ["projection_only"]:
        blockers.append("provider_contract_authority_mode_weakened")
    return blockers


def _project_item(node: dict[str, Any], *, provider: str, root: str, current_branch: str) -> dict[str, Any]:
    dependency_summary = ", ".join(
        f"{item['node_id']}={item['status']}" for item in node.get("dependency_states", [])
    )
    review_projection = review_projection_for_node(node, root=root, current_branch=current_branch)
    return {
        "provider": provider,
        "identity": str(node.get("node_id", "")).strip(),
        "fields": {
            "node_id": str(node.get("node_id", "")).strip(),
            "title": str(node.get("title", "")).strip(),
            "target_execplan_id": str(node.get("target_execplan_id", "")).strip(),
            "status": str(node.get("status", "")).strip(),
            "gating_class": str(node.get("gating_class", "")).strip(),
            "implementation_branch": str(node.get("implementation_branch", "")).strip(),
            "goal_area": str(node.get("goal_area", "")).strip(),
            "dependency_summary": dependency_summary,
            "human_review_state": review_projection["human_review_state"],
            "pr_url": review_projection["pr_url"],
            "validation_status": review_projection["validation_status"],
            "smoke_status": review_projection["smoke_status"],
            "merge_readiness": review_projection["merge_readiness"],
            "finalization_state": review_projection["finalization_state"],
        },
        "local_provenance": {
            "graph_node_id": str(node.get("node_id", "")).strip(),
            "target_execplan_id": str(node.get("target_execplan_id", "")).strip(),
            "completion_ref": str(node.get("completion_ref", "")).strip(),
            "execplan_path": _execplan_path_for_target(
                root=root,
                target_execplan_id=str(node.get("target_execplan_id", "")).strip(),
            ),
            "implementation_branch": str(node.get("implementation_branch", "")).strip(),
            "queue_position": node.get("ordering", {}).get("queue_position"),
            "ready_order": node.get("ordering", {}).get("ready_order"),
            "last_action": str(node.get("action_state", {}).get("last_action", "")).strip(),
            "action_required": bool(node.get("action_state", {}).get("action_required", False)),
        },
    }


def build_provider_projection(
    *,
    root: str = ".",
    provider: str,
    branch: str | None = None,
    execplan_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    contract = load_provider_contract(root=root)
    mapping = load_provider_mapping(root=root, provider=provider)
    remaining_work_code, remaining_work_report = check_remaining_work_graph(
        root=root,
        branch=branch,
        execplan_path=execplan_path,
    )
    blockers: list[str] = []
    blockers.extend(_provider_projection_blockers(contract=contract, mapping=mapping, provider=provider))
    if remaining_work_code != 0:
        blockers.extend(f"remaining_work_graph:{item}" for item in remaining_work_report.get("errors", []))

    items = []
    for collection_name in ("ready_nodes", "blocked_nodes", "completed_nodes"):
        for node in remaining_work_report.get(collection_name, []):
            if not isinstance(node, dict):
                continue
            items.append(_project_item(node, provider=provider, root=root, current_branch=str(remaining_work_report.get("branch", branch or "")).strip()))
    items = sorted(
        items,
        key=lambda item: (
            item.get("local_provenance", {}).get("queue_position")
            if isinstance(item.get("local_provenance", {}).get("queue_position"), int)
            else 999999,
            item["identity"],
        ),
    )

    execplan_id = ""
    if execplan_path:
        execplan_id = str(parse_plan(Path(execplan_path)).frontmatter.get("id", "")).strip()

    report = {
        "command": "provider-projection",
        "provider": provider,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "projection_kind": str(mapping.get("projection_kind", "")).strip(),
        "authority_mode": "projection_only",
        "branch": str(remaining_work_report.get("branch", branch or "")).strip(),
        "execplan_id": execplan_id,
        "ready_order": remaining_work_report.get("ordering", {}).get("ready_execplan_ids", []),
        "queue_projection": remaining_work_report.get("queue_projection", {}),
        "board_model": mapping.get("board_model", {}),
        "items": items,
        "item_count": len(items),
        "evidence_refs": sorted(
            {
                "artifacts/planner/research/remaining-work-graph.json",
                "spec/provider-adapter.schema.yaml",
                f"spec/providers/{'github-projects.schema.yaml' if provider == 'github_projects' else 'microsoft-lists.schema.yaml'}",
            }
        ),
    }
    return (1 if blockers else 0), report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--provider", required=True, choices=["github_projects", "microsoft_lists"])
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    args = parser.parse_args()
    code, report = build_provider_projection(
        root=args.root,
        provider=args.provider,
        branch=args.branch,
        execplan_path=args.execplan_path,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
