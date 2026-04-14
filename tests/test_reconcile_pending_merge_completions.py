from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_remaining_work_merge import (
    find_pending_merge_reconciliations,
    reconcile_pending_merge_completions,
)


PLAN_BODY = """
## Outcomes & Retrospective

Test.

## Context and Orientation

Test.

## Plan of Work

Test.

## Validation and Acceptance

Test.

## Artifacts and Notes

Test.
""".strip()


def test_reconcile_pending_merge_completions_runs_for_pending_candidates(monkeypatch, tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text(f"---\nid: \"plan-id\"\n---\n\n{PLAN_BODY}\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge.find_pending_merge_reconciliations",
        lambda **kwargs: [
            {
                "node_id": "rwg-100",
                "execplan_id": "plan-id",
                "execplan_path": execplan_path,
                "merge_evidence": {"pull_request": "99"},
            }
        ],
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge.reconcile_remaining_work_merge",
        lambda **kwargs: {"command": "reconcile-remaining-work-merge", "completion_ref": "merged:pr-99", "ok": True},
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge.reconcile_pending_mainline_activations",
        lambda **kwargs: [],
    )

    report = reconcile_pending_merge_completions(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["reconciled_count"] == 1
    assert report["results"][0]["completion_ref"] == "merged:pr-99"


def test_find_pending_merge_reconciliations_skips_unknown_merge_refs(monkeypatch, tmp_path: Path) -> None:
    graph_path = tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        """
{
  "nodes": [
    {
      "node_id": "rwg-101",
      "status": "ready",
      "target_execplan_id": "plan-id",
      "implementation_branch": "impl-execplan/test",
      "initiative_branch": "initiative/missing",
      "integration_mode": "via_initiative"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    execplan_path = tmp_path / ".agent" / "execplans" / "plan-id.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text(
        f"---\nid: \"plan-id\"\ninitiative_branch: \"initiative/test\"\n---\n\n{PLAN_BODY}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge._merge_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("fatal: ambiguous argument 'initiative/missing': unknown revision or path not in the working tree.")
        ),
    )

    pending = find_pending_merge_reconciliations(repo_root=tmp_path)

    assert pending == []


def test_find_pending_merge_reconciliations_skips_draft_only_history_for_via_initiative(monkeypatch, tmp_path: Path) -> None:
    graph_path = tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        """
{
  "nodes": [
    {
      "node_id": "rwg-102",
      "status": "ready",
      "target_execplan_id": "plan-id",
      "implementation_branch": "impl-execplan/test",
      "initiative_branch": "initiative/test",
      "integration_mode": "via_initiative"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    execplan_path = tmp_path / ".agent" / "execplans" / "plan-id.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text(
        f"---\nid: \"plan-id\"\ninitiative_branch: \"initiative/test\"\n---\n\n{PLAN_BODY}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "platform_tools.reconcile_remaining_work_merge._merge_candidates",
        lambda *args, **kwargs: [
            {
                "pull_request": "98",
                "commit": "draftmerge",
                "committed_at": "2026-03-19T12:00:00Z",
                "branch_ref": "draft-execplan/test",
                "merge_role": "draft-execplan",
            }
        ],
    )

    pending = find_pending_merge_reconciliations(repo_root=tmp_path)

    assert pending == []


def test_find_pending_merge_reconciliations_accepts_initiative_merge_to_main_without_impl_branch(
    monkeypatch, tmp_path: Path
) -> None:
    graph_path = tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        """
{
  "nodes": [
        {
          "node_id": "rwg-103",
          "status": "decision_gated",
          "target_execplan_id": "plan-id",
          "initiative_branch": "initiative/test",
          "integration_mode": "via_initiative"
        }
      ]
    }
""".strip()
        + "\n",
        encoding="utf-8",
    )

    execplan_path = tmp_path / ".agent" / "execplans" / "plan-id.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text(
        f"---\nid: \"plan-id\"\nbase_branch: \"initiative/test\"\ninitiative_branch: \"initiative/test\"\n---\n\n{PLAN_BODY}\n",
        encoding="utf-8",
    )

    def _fake_merge_candidates(repo_root: Path, ref: str, plan_id: str, branch_markers, extra_markers=None) -> list[dict[str, str]]:
        if ref == "initiative/test":
            return []
        if ref == "main":
            return [
                {
                    "pull_request": "113",
                    "commit": "mainmerge",
                    "committed_at": "2026-03-26T12:00:00Z",
                    "branch_ref": "initiative/test",
                    "merge_role": "other",
                }
            ]
        return []

    monkeypatch.setattr("platform_tools.reconcile_remaining_work_merge._merge_candidates", _fake_merge_candidates)

    pending = find_pending_merge_reconciliations(repo_root=tmp_path)

    assert len(pending) == 1
    assert pending[0]["merge_ref"] == "main"
    assert pending[0]["merge_evidence"]["pull_request"] == "113"
