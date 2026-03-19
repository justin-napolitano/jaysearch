from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_remaining_work_merge import reconcile_pending_merge_completions


def test_reconcile_pending_merge_completions_runs_for_pending_candidates(monkeypatch, tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

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

    report = reconcile_pending_merge_completions(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["reconciled_count"] == 1
    assert report["results"][0]["completion_ref"] == "merged:pr-99"
