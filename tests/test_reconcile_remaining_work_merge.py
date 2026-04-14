from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_remaining_work_merge import (
    reconcile_pending_merge_completions,
    reconcile_remaining_work_merge,
)


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
                "node_id": "initiative-remaining-work-ordering",
                "title": "Initiative / Remaining-work ordering",
                "status": "ready",
                "gating_class": "auto_runnable",
                "conflict_domains": ["remaining-work-graph"],
                "target_execplan_id": "initiative:remaining-work-ordering",
                "goal_area": "reference",
                "initiative_branch": "initiative/remaining-work-ordering",
                "parent_initiative_node": "initiative-remaining-work-ordering",
                "ordering": {},
            },
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
    assert report["transition_event"] == "impl_execplan_merge_to_initiative"
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

    def _fake_merge_candidates(
        repo_root: Path,
        ref: str,
        plan_id: str,
        draft_branch: str,
        extra_markers=None,
    ) -> list[dict[str, str]]:
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
    assert report["transition_event"] == "impl_execplan_merge_to_initiative"

def test_reconcile_requires_impl_merge_for_via_initiative(monkeypatch, tmp_path: Path) -> None:
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
            }
        ],
    )

    try:
        reconcile_remaining_work_merge(
            execplan_path=plan,
            repo_root=tmp_path,
        )
    except ValueError as exc:
        assert str(exc) == "missing_merge_commit"
    else:
        raise AssertionError("expected missing_merge_commit for draft-only merge history")


def test_reconcile_tracks_pending_mainline_activation_for_completed_via_initiative_node(tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text())
    graph = _graph_data()
    target = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    target["availability_target_ref"] = "main"
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", graph)
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
            "branch_ref": "impl-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312",
            "merge_role": "impl-execplan",
        },
    )

    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    rwg020 = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    assert report["completion_ref"] == "merged:pr-73"
    assert report["availability_status"] == "pending"
    assert report["availability_ref"] == ""
    assert rwg020["status"] == "completed"
    assert rwg020["availability_status"] == "pending"
    assert "availability_ref" not in rwg020


def test_pending_merge_reconciliation_activates_completed_node_when_initiative_reaches_main(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text())
    graph = _graph_data()
    target = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    target["status"] = "completed"
    target["completion_ref"] = "merged:pr-73"
    target["availability_target_ref"] = "main"
    target["availability_status"] = "pending"
    target["ordering"]["source_action_id"] = "rwg-action-20260312-005-complete-rwg-020"
    target["action_state"]["last_action_id"] = "rwg-action-20260312-005-complete-rwg-020"
    target["action_state"]["last_action"] = "complete"
    graph["queue_projection"]["last_reconciled_action_id"] = "rwg-action-20260312-005-complete-rwg-020"
    graph["queue_projection"]["ready_execplan_ids"] = []
    graph["graph_actions"].append(
        {
            "action_id": "rwg-action-20260312-005-complete-rwg-020",
            "action": "complete",
            "node_id": "rwg-020",
            "rationale": "ordering work completed on initiative branch",
            "evidence_ref": "merged:pr-73",
            "queue_reconciled": True,
        }
    )
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", graph)
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text().replace("   - status: `ready`", "   - status: `completed`", 1))
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _schema_text())
    _write(tmp_path / "docs" / "remaining-work-graph.md", "# Remaining Work Graph\n")

    def _fake_merge_candidates(repo_root: Path, ref: str, plan_id: str, draft_branch: str, extra_markers=None) -> list[dict[str, str]]:
        if ref == "main":
            return [
                {
                    "pull_request": "100",
                    "commit": "mainmerge",
                    "committed_at": "2026-03-19T19:00:00Z",
                    "branch_ref": "initiative/remaining-work-ordering",
                    "merge_role": "other",
                }
            ]
        return []

    monkeypatch.setattr("platform_tools.reconcile_remaining_work_merge._merge_candidates", _fake_merge_candidates)

    report = reconcile_pending_merge_completions(repo_root=tmp_path)

    assert report["activated_count"] == 1
    assert report["activation_results"][0]["availability_ref"] == "merged:pr-100"
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    rwg020 = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    assert rwg020["availability_status"] == "active"
    assert rwg020["availability_ref"] == "merged:pr-100"


def test_reconcile_pending_merge_completion_from_initiative_merge_to_main_without_impl_branch(
    monkeypatch, tmp_path: Path
) -> None:
    plan = tmp_path / ".agent" / "execplans" / "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
    _write(plan, _plan_text().replace("base_branch: main", "base_branch: initiative/remaining-work-ordering"))
    graph = _graph_data()
    target = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    target.pop("implementation_branch", None)
    target["status"] = "decision_gated"
    target["gating_class"] = "decision_gated"
    target["status_reason"] = "registered from ExecPlan metadata; authoritative ExecPlan required before execution"
    target["availability_target_ref"] = "main"
    target["action_state"]["last_action_id"] = "rwg-action-20260312-004-promote-rwg-020"
    target["action_state"]["last_action"] = "block"
    target["ordering"]["source_action_id"] = "rwg-action-20260312-004-promote-rwg-020"
    _write_json(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", graph)
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text().replace("   - status: `ready`", "   - status: `decision_gated`", 1))
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _schema_text())
    _write(tmp_path / "docs" / "remaining-work-graph.md", "# Remaining Work Graph\n")

    def _fake_merge_candidates(repo_root: Path, ref: str, plan_id: str, draft_branch: str, extra_markers=None) -> list[dict[str, str]]:
        if ref == "initiative/remaining-work-ordering":
            return []
        if ref == "main":
            return [
                {
                    "pull_request": "113",
                    "commit": "mainmerge",
                    "committed_at": "2026-03-26T14:00:00Z",
                    "branch_ref": "initiative/remaining-work-ordering",
                    "merge_role": "other",
                }
            ]
        return []

    monkeypatch.setattr("platform_tools.reconcile_remaining_work_merge._merge_candidates", _fake_merge_candidates)

    report = reconcile_pending_merge_completions(repo_root=tmp_path)

    assert report["reconciled_count"] == 1
    result = report["results"][0]
    assert result["completion_ref"] == "merged:pr-113"
    assert result["completion_target_ref"] == "main"
    assert result["transition_event"] == "initiative_merge_to_main"
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    rwg020 = next(node for node in graph["nodes"] if node["node_id"] == "rwg-020")
    assert rwg020["status"] == "completed"
    assert rwg020["completion_ref"] == "merged:pr-113"
