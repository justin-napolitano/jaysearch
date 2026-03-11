from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.integrations.provider_adapter import (
    build_provider_projection,
    load_provider_contract,
    load_provider_mapping,
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_provider_specs(root: Path) -> None:
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
                "properties:",
                "  graph_id:",
                "    type: string",
                "  created_at:",
                "    type: string",
                "  nodes:",
                "    type: array",
                "    items:",
                "      type: object",
                "      required:",
                "        - node_id",
                "        - title",
                "        - status",
                "        - gating_class",
                "        - conflict_domains",
                "        - target_execplan_id",
                "      properties:",
                "        node_id:",
                "          type: string",
                "        title:",
                "          type: string",
                "        status:",
                '          enum: ["ready", "blocked", "review_gated", "decision_gated", "completed"]',
                "        status_reason:",
                "          type: string",
                "        gating_class:",
                '          enum: ["auto_runnable", "review_gated", "decision_gated"]',
                "        conflict_domains:",
                "          type: array",
                "          items:",
                "            type: string",
                "        target_execplan_id:",
                "          type: string",
                "        goal_area:",
                "          type: string",
                "        implementation_branch:",
                "          type: string",
                "        completion_ref:",
                "          type: string",
                "  edges:",
                "    type: array",
                "    items:",
                "      type: object",
                "      required:",
                "        - from",
                "        - to",
                "        - relation",
                "      properties:",
                "        from:",
                "          type: string",
                "        to:",
                "          type: string",
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
                "last_updated: 2026-03-11",
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
                "  supported_entities_allowed:",
                "    - remaining_work_node",
                "  required_exported_fields:",
                "    - node_id",
                "    - title",
                "    - target_execplan_id",
                "    - status",
                "    - gating_class",
                "    - implementation_branch",
                "  conflict_policy:",
                "    required_fields:",
                "      - unresolved_conflict_resolution",
                "      - remote_authority",
                "    unresolved_conflict_resolution_allowed:",
                "      - local_wins",
                "invariants:",
                "  - local_graph_is_canonical",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "providers" / "github-projects.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-11",
                "provider: github_projects",
                "projection_kind: remaining_work_board",
                "board_model:",
                "  board_scope: remaining_work_graph",
                "  item_identity_field: node_id",
                "  item_type: slice_node",
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
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "providers" / "microsoft-lists.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-11",
                "provider: microsoft_lists",
                "projection_kind: remaining_work_board",
                "status: placeholder",
                "board_model:",
                "  board_scope: remaining_work_graph",
                "  item_identity_field: node_id",
                "required_list_fields:",
                "  - node_id",
                "  - title",
                "  - target_execplan_id",
                "  - status",
                "  - gating_class",
                "  - implementation_branch",
                "  - goal_area",
            ]
        )
        + "\n",
    )


def _seed_remaining_work(root: Path) -> Path:
    execplan = root / ".agent" / "execplans" / "provider-sync.md"
    _write_text(
        execplan,
        "\n".join(
            [
                "---",
                'id: "20260311-provider-sync-scaffold-codex-01-execplan"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    _write_json(
        root / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {
                    "node_id": "rwg-006",
                    "title": "Runtime constraint canonicalization",
                    "status": "completed",
                    "completion_ref": "merged:runtime-constraints",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["remaining-work-graph"],
                    "target_execplan_id": "20260311-runtime-constraint-canonicalization-codex-01-execplan",
                    "goal_area": "runtime-governance",
                    "implementation_branch": "impl-execplan/runtime-constraints",
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
            "edges": [
                {"from": "rwg-005", "to": "rwg-006", "relation": "gated_by"},
            ],
        },
    )
    return execplan


def test_provider_projection_builds_github_projects_board(tmp_path: Path) -> None:
    _seed_provider_specs(tmp_path)
    execplan = _seed_remaining_work(tmp_path)

    code, report = build_provider_projection(
        root=tmp_path.as_posix(),
        provider="github_projects",
        branch="impl-execplan/20260311-provider-sync-scaffold-codex-01-execplan-codex-01-20260311",
        execplan_path=execplan.as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["provider"] == "github_projects"
    assert report["board_model"]["board_scope"] == "remaining_work_graph"
    assert report["item_count"] == 2
    assert report["items"][0]["fields"]["node_id"] == "rwg-005"
    assert report["items"][0]["fields"]["human_review_state"] == "not_requested"


def test_provider_projection_supports_microsoft_placeholder_mapping(tmp_path: Path) -> None:
    _seed_provider_specs(tmp_path)
    _seed_remaining_work(tmp_path)

    contract = load_provider_contract(root=tmp_path.as_posix())
    mapping = load_provider_mapping(root=tmp_path.as_posix(), provider="microsoft_lists")

    assert contract["provider_adapter"]["authority_mode_allowed"] == ["projection_only"]
    assert mapping["provider"] == "microsoft_lists"
    assert mapping["status"] == "placeholder"
