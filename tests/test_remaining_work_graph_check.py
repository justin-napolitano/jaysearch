from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.remaining_work_graph_check import check_remaining_work_graph


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_schema(root: Path) -> None:
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
                "  - ordering_policy",
                "  - queue_projection",
                "  - graph_actions",
                "  - nodes",
                "  - edges",
                "properties:",
                "  graph_id:",
                "    type: string",
                "  created_at:",
                "    type: string",
                "  ordering_policy:",
                "    type: object",
                "  queue_projection:",
                "    type: object",
                "  graph_actions:",
                "    type: array",
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
                "        expected_artifacts:",
                "          type: array",
                "          items:",
                "            type: string",
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


def test_remaining_work_graph_check_reports_active_ready_slice(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "ordering_policy": {
                "ready_statuses": ["ready"],
                "ready_sort_fields": ["ready_order", "tie_breaker", "node_id"],
                "reorder_requires_explicit_action": True,
                "board_projection_authority": "projection_only",
            },
            "queue_projection": {
                "path": "docs/queued-execplans.md",
                "projection_authority": "projection_only",
                "last_reconciled_action_id": "act-2",
                "ready_execplan_ids": ["20260311-runtime-constraint-canonicalization-codex-01-execplan"],
            },
            "graph_actions": [
                {
                    "action_id": "act-1",
                    "action": "complete",
                    "node_id": "rwg-001",
                    "rationale": "completed dependency",
                },
                {
                    "action_id": "act-2",
                    "action": "promote_ready",
                    "node_id": "rwg-006",
                    "rationale": "ready slice",
                },
            ],
            "nodes": [
                {
                    "node_id": "rwg-001",
                    "title": "Composite orchestrator status",
                    "status": "completed",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["orchestrator-status"],
                    "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                    "goal_area": "orchestrator-status",
                    "completion_ref": "merged:composite",
                    "ordering": {"queue_position": 1, "tie_breaker": "20260311-composite-orchestrator-status-codex-01-execplan"},
                    "action_state": {
                        "last_action_id": "act-1",
                        "last_action": "complete",
                        "action_required": False,
                        "reorder_requires_human": False,
                        "reorder_blockers": [],
                    },
                },
                {
                    "node_id": "rwg-006",
                    "title": "Runtime constraint canonicalization",
                    "status": "ready",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["remaining-work-graph"],
                    "target_execplan_id": "20260311-runtime-constraint-canonicalization-codex-01-execplan",
                    "goal_area": "runtime-governance",
                    "implementation_branch": "impl-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311",
                    "ordering": {
                        "queue_position": 2,
                        "ready_order": 1,
                        "tie_breaker": "20260311-runtime-constraint-canonicalization-codex-01-execplan",
                        "source_action_id": "act-2",
                    },
                    "action_state": {
                        "last_action_id": "act-2",
                        "last_action": "promote_ready",
                        "action_required": False,
                        "reorder_requires_human": False,
                        "reorder_blockers": [],
                    },
                },
            ],
            "edges": [
                {"from": "rwg-006", "to": "rwg-001", "relation": "depends_on"},
            ],
        },
    )
    execplan = tmp_path / ".agent" / "execplans" / "runtime.md"
    _write_text(
        execplan,
        "\n".join(
            [
                "---",
                'id: "20260311-runtime-constraint-canonicalization-codex-01-execplan"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    _write_text(
        tmp_path / "docs" / "queued-execplans.md",
        "\n".join(
            [
                "# Queued ExecPlans",
                "",
                "## Mirror Metadata",
                "",
                "- canonical_last_graph_action_id: `act-2`",
                "- canonical_ready_order: `20260311-runtime-constraint-canonicalization-codex-01-execplan`",
                "- projection_authority: `projection_only`",
            ]
        )
        + "\n",
    )

    code, report = check_remaining_work_graph(
        root=tmp_path.as_posix(),
        branch="impl-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311",
        execplan_path=execplan.as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["active_node"]["node_id"] == "rwg-006"
    assert report["ready_nodes"][0]["node_id"] == "rwg-006"
    assert report["ordering"]["ready_execplan_ids"] == ["20260311-runtime-constraint-canonicalization-codex-01-execplan"]


def test_remaining_work_graph_check_rejects_stale_blocked_state(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "ordering_policy": {
                "ready_statuses": ["ready"],
                "ready_sort_fields": ["ready_order", "tie_breaker", "node_id"],
                "reorder_requires_explicit_action": True,
                "board_projection_authority": "projection_only",
            },
            "queue_projection": {
                "path": "docs/queued-execplans.md",
                "projection_authority": "projection_only",
                "last_reconciled_action_id": "act-1",
                "ready_execplan_ids": [],
            },
            "graph_actions": [
                {
                    "action_id": "act-1",
                    "action": "complete",
                    "node_id": "rwg-001",
                    "rationale": "completed dependency",
                }
            ],
            "nodes": [
                {
                    "node_id": "rwg-001",
                    "title": "Composite orchestrator status",
                    "status": "completed",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["orchestrator-status"],
                    "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                    "goal_area": "orchestrator-status",
                    "completion_ref": "merged:composite",
                    "ordering": {"queue_position": 1, "tie_breaker": "20260311-composite-orchestrator-status-codex-01-execplan"},
                    "action_state": {
                        "last_action_id": "act-1",
                        "last_action": "complete",
                        "action_required": False,
                        "reorder_requires_human": False,
                        "reorder_blockers": [],
                    },
                },
                {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "blocked",
                    "status_reason": "dependency_incomplete",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["orchestrator-status"],
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "goal_area": "implementation-orchestrator",
                    "ordering": {
                        "queue_position": 2,
                        "tie_breaker": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    },
                },
            ],
            "edges": [
                {"from": "rwg-004", "to": "rwg-001", "relation": "depends_on"},
            ],
        },
    )
    _write_text(
        tmp_path / "docs" / "queued-execplans.md",
        "\n".join(
            [
                "# Queued ExecPlans",
                "",
                "## Mirror Metadata",
                "",
                "- canonical_last_graph_action_id: `act-1`",
                "- canonical_ready_order: ``",
                "- projection_authority: `projection_only`",
            ]
        )
        + "\n",
    )

    code, report = check_remaining_work_graph(root=tmp_path.as_posix())

    assert code == 1
    assert "blocked_node_without_open_dependency:rwg-004" in report["errors"]
