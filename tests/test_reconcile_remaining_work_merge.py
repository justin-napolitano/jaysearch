from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_remaining_work_merge import reconcile_remaining_work_merge


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _plan_text() -> str:
    return """---
id: "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan"
title: "Remaining work ordering"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - artifacts/planner/research/remaining-work-graph.json
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
---

# Purpose / Big Picture

Test.

## Progress

- [x] Test

## Surprises & Discoveries

None.

## Decision Log

None.

## Outcomes & Retrospective

Test.

## Context and Orientation

Test.

## Plan of Work

Test.

## Concrete Steps

1. Test.

## Validation and Acceptance

Test.

## Idempotence and Recovery

Test.

## Artifacts and Notes

Test.

## Interfaces and Dependencies

Test.
"""


def _graph_data() -> dict[str, object]:
    return {
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
            "last_reconciled_action_id": "rwg-action-20260312-004-promote-rwg-020",
            "ready_execplan_ids": ["20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan"],
        },
        "graph_actions": [
            {
                "action_id": "rwg-action-20260312-004-promote-rwg-020",
                "action": "promote_ready",
                "node_id": "rwg-020",
                "rationale": "ordering work is ready",
                "evidence_ref": "docs/queued-execplans.md",
                "queue_reconciled": True,
            }
        ],
        "nodes": [
            {
                "node_id": "rwg-012",
                "title": "Policy compliance",
                "status": "completed",
                "completion_ref": "merged:pr-72",
                "gating_class": "auto_runnable",
                "conflict_domains": ["policy-compliance"],
                "target_execplan_id": "20260312-game-policy-compliance-codex-01-execplan",
                "goal_area": "governance",
                "expected_artifacts": ["bin/policy-compliance-check"],
                "ordering": {"queue_position": 12, "tie_breaker": "20260312-game-policy-compliance-codex-01-execplan"},
                "action_state": {"last_action_id": "", "last_action": "", "action_required": False, "reorder_requires_human": False, "reorder_blockers": []},
            },
            {
                "node_id": "rwg-013",
                "title": "Commit structure",
                "status": "completed",
                "completion_ref": "merged:pr-72",
                "gating_class": "auto_runnable",
                "conflict_domains": ["policy-compliance"],
                "target_execplan_id": "20260312-game-policy-compliance-codex-01-execplan",
                "goal_area": "governance",
                "expected_artifacts": ["docs/games/commit-structure-game.md"],
                "ordering": {"queue_position": 13, "tie_breaker": "20260312-game-policy-compliance-codex-01-execplan"},
                "action_state": {"last_action_id": "", "last_action": "", "action_required": False, "reorder_requires_human": False, "reorder_blockers": []},
            },
            {
                "node_id": "rwg-014",
                "title": "Game hostile-review runtime",
                "status": "blocked",
                "status_reason": "must follow remaining-work ordering",
                "gating_class": "auto_runnable",
                "conflict_domains": ["review-runtime"],
                "target_execplan_id": "future:game-hostile-review",
                "goal_area": "review-runtime",
                "expected_artifacts": ["bin/hostile-review"],
                "ordering": {"queue_position": 14, "tie_breaker": "future:game-hostile-review"},
                "action_state": {"last_action_id": "", "last_action": "", "action_required": False, "reorder_requires_human": False, "reorder_blockers": []},
            },
            {
                "node_id": "rwg-020",
                "title": "Remaining-work ordering",
                "status": "ready",
                "status_reason": "next canonical slice",
                "gating_class": "auto_runnable",
                "conflict_domains": ["remaining-work-graph"],
                "target_execplan_id": "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan",
                "goal_area": "governance",
                "expected_artifacts": ["bin/remaining-work-graph-check"],
                "implementation_branch": "impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312",
                "initiative_branch": "initiative/remaining-work-ordering",
                "parent_initiative_node": "initiative-remaining-work-ordering",
                "integration_mode": "via_initiative",
                "ordering": {
                    "queue_position": 20,
                    "ready_order": 1,
                    "tie_breaker": "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan",
                    "source_action_id": "rwg-action-20260312-004-promote-rwg-020",
                },
                "action_state": {
                    "last_action_id": "rwg-action-20260312-004-promote-rwg-020",
                    "last_action": "promote_ready",
                    "action_required": False,
                    "reorder_requires_human": False,
                    "reorder_blockers": [],
                },
            },
        ],
        "edges": [
            {"from": "rwg-014", "to": "rwg-012", "relation": "depends_on"},
            {"from": "rwg-014", "to": "rwg-013", "relation": "depends_on"},
            {"from": "rwg-014", "to": "rwg-020", "relation": "depends_on"},
            {"from": "rwg-020", "to": "rwg-012", "relation": "depends_on"},
        ],
    }


def _queue_text() -> str:
    return """# Queued ExecPlans

13. `future:game-hostile-review`
   - status: `blocked`
   - goal: add machine hostile review before human approval gates
   - blocker: `20260312-game-policy-compliance-codex-01-execplan` must land first

19. `20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan`
   - status: `ready`
   - goal: formalize deterministic graph actions, canonical ordering fields, and governed reorder/reconciliation behavior
   - implementation branch: `impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312`

## Mirror Metadata

- canonical_last_graph_action_id: `rwg-action-20260312-004-promote-rwg-020`
- canonical_ready_order: `20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan`
- projection_authority: `projection_only`
"""


def _schema_text() -> str:
    return Path("spec/remaining-work-graph.schema.yaml").read_text(encoding="utf-8")


def test_reconcile_remaining_work_merge_updates_graph_and_queue(tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text())
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", _graph_data())
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text())
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _schema_text())
    _write(tmp_path / "docs" / "remaining-work-graph.md", "# Remaining Work Graph\n")

    report = reconcile_remaining_work_merge(
        execplan_path=plan,
        repo_root=tmp_path,
        merge_evidence={
            "pull_request": "73",
            "commit": "abc123",
            "committed_at": "2026-03-12T12:00:00Z",
        },
    )

    assert report["ok"] is True
    assert report["completed_node_id"] == "rwg-020"
    assert report["next_node_id"] == "rwg-014"
    assert report["next_node_status"] == "review_gated"
    assert report["ready_execplan_ids"] == []

    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    rwg020 = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    rwg014 = next(node for node in graph["nodes"] if node["node_id"] == "rwg-014")
    assert rwg020["status"] == "completed"
    assert rwg020["completion_ref"] == "merged:pr-73"
    assert rwg020["action_state"]["last_action"] == "complete"
    assert rwg014["status"] == "review_gated"
    assert rwg014["gating_class"] == "review_gated"
    assert rwg014["action_state"]["last_action"] == "unblock"
    assert graph["queue_projection"]["ready_execplan_ids"] == []

    queue_text = (tmp_path / "docs" / "queued-execplans.md").read_text(encoding="utf-8")
    assert "- canonical_ready_order: ``" in queue_text
    assert "19. `20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan`" in queue_text
    assert "   - status: `completed`" in queue_text
    assert "   - completion ref: `merged:pr-73`" in queue_text
    assert "13. `future:game-hostile-review`" in queue_text
    assert "   - status: `review_gated`" in queue_text


def test_reconcile_prefers_matching_implementation_branch_merge(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text())
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", _graph_data())
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text())
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _schema_text())
    _write(tmp_path / "docs" / "remaining-work-graph.md", "# Remaining Work Graph\n")

    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge._merge_candidates",
        lambda *args, **kwargs: [
            {
                "pull_request": "82",
                "commit": "draftmerge",
                "committed_at": "2026-03-12T10:00:00Z",
                "branch_ref": "draft-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312",
                "merge_role": "draft-execplan",
            },
            {
                "pull_request": "83",
                "commit": "implmerge",
                "committed_at": "2026-03-12T09:00:00Z",
                "branch_ref": "impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312",
                "merge_role": "impl-execplan",
            },
        ],
    )

    report = reconcile_remaining_work_merge(
        execplan_path=plan,
        repo_root=tmp_path,
    )

    assert report["completion_ref"] == "merged:pr-83"


def test_reconcile_uses_initiative_branch_as_completion_target(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text())
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", _graph_data())
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text())
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _schema_text())
    _write(tmp_path / "docs" / "remaining-work-graph.md", "# Remaining Work Graph\n")

    seen: dict[str, str] = {}

    def _fake_merge_candidates(repo_root: Path, ref: str, plan_id: str, draft_branch: str) -> list[dict[str, str]]:
        seen["ref"] = ref
        return [
            {
                "pull_request": "91",
                "commit": "initiative-merge",
                "committed_at": "2026-03-19T12:00:00Z",
                "branch_ref": "impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312",
                "merge_role": "impl-execplan",
            }
        ]

    monkeypatch.setattr("platform_tools.reconcile_remaining_work_merge._merge_candidates", _fake_merge_candidates)

    report = reconcile_remaining_work_merge(
        execplan_path=plan,
        repo_root=tmp_path,
    )

    assert seen["ref"] == "initiative/remaining-work-ordering"
    assert report["ok"] is True
    assert report["completion_target_ref"] == "initiative/remaining-work-ordering"
