from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.register_remaining_work_node import register_remaining_work_node


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _seed_specs(root: Path) -> None:
    _write(root / "spec/board-action-api.yaml", Path("spec/board-action-api.yaml").read_text(encoding="utf-8"))
    _write(root / "spec/board-event-log.schema.yaml", Path("spec/board-event-log.schema.yaml").read_text(encoding="utf-8"))
    _write(root / "spec/remaining-work-graph.schema.yaml", Path("spec/remaining-work-graph.schema.yaml").read_text(encoding="utf-8"))


def test_register_remaining_work_node_creates_decision_gated_node(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    plan = tmp_path / ".agent" / "execplans" / "20260319-test-register-node-codex-01-execplan.md"
    _write(
        plan,
        """---
id: "20260319-test-register-node-codex-01-execplan"
title: "Register node test"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - artifacts/planner/research/remaining-work-graph.json
approve_policy: codeowners
reviewers:
  - "github:test-owner"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-test-register-node"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
initiative_branch: "initiative/test-register-node"
initiative_node_id: "initiative-test-register-node"
graph_registration:
  node_id: "rwg-999"
  queue_position: 999
  goal_area: "governance"
  implementation_branch: "impl-execplan/20260319-test-register-node"
  integration_mode: "via_initiative"
  conflict_domains:
    - governance
    - workflow
  expected_artifacts:
    - artifacts/planner/research/remaining-work-graph.json
---

# Purpose / Big Picture

Test.
""",
    )
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260319",
            "created_at": "2026-03-19T00:00:00Z",
            "ordering_policy": {
                "ready_statuses": ["ready"],
                "ready_sort_fields": ["ready_order", "tie_breaker", "node_id"],
                "reorder_requires_explicit_action": True,
                "board_projection_authority": "projection_only",
            },
            "queue_projection": {
                "path": "docs/queued-execplans.md",
                "projection_authority": "projection_only",
                "last_reconciled_action_id": "",
                "ready_execplan_ids": [],
            },
            "graph_actions": [],
            "nodes": [],
            "edges": [],
        },
    )
    _write(
        tmp_path / "docs" / "queued-execplans.md",
        "# Queued ExecPlans\n\n## Mirror Metadata\n\n- canonical_last_graph_action_id: ``\n- canonical_ready_order: ``\n- projection_authority: `projection_only`\n",
    )

    report = register_remaining_work_node(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert report["action"] == "registered"
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    node = next(item for item in graph["nodes"] if item["node_id"] == "rwg-999")
    assert node["status"] == "decision_gated"
    assert node["parent_initiative_node"] == "initiative-test-register-node"
    assert any(item["node_id"] == "initiative-test-register-node" for item in graph["nodes"])
    queue_text = (tmp_path / "docs" / "queued-execplans.md").read_text(encoding="utf-8")
    assert "999. `20260319-test-register-node-codex-01-execplan`" in queue_text
    event_lines = (tmp_path / "artifacts" / "governance" / "board-action-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(event_lines) == 1
    assert json.loads(event_lines[0])["action_family"] == "backlog_graph_action"
