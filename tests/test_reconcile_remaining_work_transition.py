from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_remaining_work_transition import reconcile_remaining_work_transition


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    command = ["git", *args]
    if args and args[0] == "commit":
        command = ["git", "commit", "--no-gpg-sign", *args[1:]]
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)


def _seed_specs(root: Path) -> None:
    _write(root / "spec/board-action-api.yaml", Path("spec/board-action-api.yaml").read_text(encoding="utf-8"))
    _write(root / "spec/board-event-log.schema.yaml", Path("spec/board-event-log.schema.yaml").read_text(encoding="utf-8"))
    _write(root / "spec/remaining-work-graph.schema.yaml", Path("spec/remaining-work-graph.schema.yaml").read_text(encoding="utf-8"))


def _plan_text(*, finalized_in_pr: str = "", finalized_at: str = "") -> str:
    return f"""---
id: "20260319-graph-transition-runtime-codex-01-execplan"
title: "Graph transition runtime"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: approved
base_branch: main
changes:
  - artifacts/planner/research/remaining-work-graph.json
approve_policy: codeowners
reviewers:
  - "github:test-owner"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-graph-transition-runtime"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: "github:test-owner"
finalized_at: "{finalized_at}"
finalized_in_pr: "{finalized_in_pr}"
---

# Purpose / Big Picture

Test.
"""


def _queue_text(status: str) -> str:
    return f"""# Queued ExecPlans

1. `20260319-graph-transition-runtime-codex-01-execplan`
   - status: `{status}`
   - goal: test graph transition reconciliation
   - implementation branch: `impl-execplan/20260319-graph-transition-runtime`

## Mirror Metadata

- canonical_last_graph_action_id: `act-001`
- canonical_ready_order: ``
- projection_authority: `projection_only`
"""


def _graph_data(status: str) -> dict[str, object]:
    return {
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
            "last_reconciled_action_id": "act-001",
            "ready_execplan_ids": [],
        },
        "graph_actions": [],
        "nodes": [
            {
                "node_id": "initiative-graph-transition-runtime",
                "title": "Initiative / Graph transition runtime",
                "status": "ready",
                "gating_class": "auto_runnable",
                "conflict_domains": ["governance"],
                "target_execplan_id": "initiative:graph-transition-runtime",
                "goal_area": "reference",
                "initiative_branch": "initiative/graph-transition-runtime",
                "parent_initiative_node": "initiative-graph-transition-runtime",
                "ordering": {},
            },
            {
                "node_id": "rwg-027",
                "title": "Graph transition runtime",
                "status": status,
                "status_reason": "waiting for canonical evidence" if status != "ready" else "",
                "gating_class": "review_gated" if status == "review_gated" else "decision_gated",
                "conflict_domains": ["governance"],
                "target_execplan_id": "20260319-graph-transition-runtime-codex-01-execplan",
                "goal_area": "governance",
                "implementation_branch": "impl-execplan/20260319-graph-transition-runtime",
                "initiative_branch": "initiative/graph-transition-runtime",
                "parent_initiative_node": "initiative-graph-transition-runtime",
                "integration_mode": "via_initiative",
                "expected_artifacts": ["artifacts/planner/research/remaining-work-graph.json"],
                "ordering": {
                    "queue_position": 27,
                    "tie_breaker": "20260319-graph-transition-runtime-codex-01-execplan",
                    "source_action_id": "act-001",
                },
                "action_state": {
                    "last_action_id": "act-001",
                    "last_action": "block",
                    "action_required": False,
                    "reorder_requires_human": False,
                    "reorder_blockers": [],
                },
            },
        ],
        "edges": [],
    }


def test_reconcile_transition_promotes_finalized_draft_to_review_gated(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    plan = tmp_path / ".agent" / "execplans" / "20260319-graph-transition-runtime-codex-01-execplan.md"
    _write(plan, _plan_text(finalized_in_pr="91", finalized_at="2026-03-19T12:00:00Z"))
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", _graph_data("decision_gated"))
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text("decision_gated"))

    report = reconcile_remaining_work_transition(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert report["transition_event"] == "draft_execplan_merge_to_main"
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    node = next(item for item in graph["nodes"] if item["node_id"] == "rwg-027")
    assert node["status"] == "review_gated"
    event_lines = (tmp_path / "artifacts" / "governance" / "board-action-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(event_lines) == 1
    assert json.loads(event_lines[0])["action_family"] == "backlog_graph_action"


def test_reconcile_transition_promotes_published_impl_branch_to_ready(tmp_path: Path) -> None:
    _seed_specs(tmp_path)
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", "impl-execplan/20260319-graph-transition-runtime")
    _write(tmp_path / "slice.txt", "ok\n")
    _git(tmp_path, "add", "slice.txt")
    _git(tmp_path, "commit", "-m", "feat: publish impl branch")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _git(tmp_path, "update-ref", "refs/remotes/origin/impl-execplan/20260319-graph-transition-runtime", head)

    plan = tmp_path / ".agent" / "execplans" / "20260319-graph-transition-runtime-codex-01-execplan.md"
    _write(plan, _plan_text())
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", _graph_data("review_gated"))
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text("review_gated"))

    report = reconcile_remaining_work_transition(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert report["transition_event"] == "implementation_branch_publish"
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    node = next(item for item in graph["nodes"] if item["node_id"] == "rwg-027")
    assert node["status"] == "ready"
    assert graph["queue_projection"]["ready_execplan_ids"] == ["20260319-graph-transition-runtime-codex-01-execplan"]
    event_lines = (tmp_path / "artifacts" / "governance" / "board-action-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(event_lines) == 1
    assert json.loads(event_lines[0])["action_family"] == "implementation_branch_publish"
