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

    code, report = check_remaining_work_graph(
        root=tmp_path.as_posix(),
        branch="impl-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311",
        execplan_path=execplan.as_posix(),
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["active_node"]["node_id"] == "rwg-006"
    assert report["ready_nodes"][0]["node_id"] == "rwg-006"


def test_remaining_work_graph_check_rejects_stale_blocked_state(tmp_path: Path) -> None:
    _seed_schema(tmp_path)
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
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
                },
            ],
            "edges": [
                {"from": "rwg-004", "to": "rwg-001", "relation": "depends_on"},
            ],
        },
    )

    code, report = check_remaining_work_graph(root=tmp_path.as_posix())

    assert code == 1
    assert "blocked_node_without_open_dependency:rwg-004" in report["errors"]
