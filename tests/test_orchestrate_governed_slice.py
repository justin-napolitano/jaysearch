from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrate_governed_slice import _effective_base_ref, run_orchestrate_governed_slice


def test_orchestrate_governed_slice_runs_reconciliation_then_reports_status(monkeypatch, tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": "impl-execplan/test",
                "blockers": [],
                "active_execplan": {"path": execplan_path.as_posix()},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_governed_graph_events",
        lambda **kwargs: {"command": "reconcile-governed-graph-events", "ok": True, "status": "ok", "steps": []},
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.check_merge_readiness",
        lambda **kwargs: (0, {"readiness": True, "failing_checks": []}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.run_session_bootstrap_check",
        lambda **kwargs: (0, {"ok": True, "blockers": [], "status": "ok"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_orchestrator_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": [{"action": "continue_active_slice"}]}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_human_operations_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": [{"action": "monitor_board_runtime"}]}),
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 0
    assert report["ok"] is True
    assert report["session_bootstrap"]["ok"] is True
    assert report["reconciliation"]["status"] == "ok"
    assert report["post_merge_reconciliation"]["reconciled_count"] == 0
    assert report["next_actions"][0]["action"] == "continue_active_slice"


def test_orchestrate_governed_slice_uses_managed_repo_status_for_external_root(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_managed_repo_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "blockers": [],
                "branch": "impl-execplan/jayrun",
                "active_execplan": {"path": "/tmp/jayrun/.agent/execplans/plan.md"},
                "next_actions": [{"action": "start_managed_slice"}],
            },
        ),
    )

    code, report = run_orchestrate_governed_slice(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["managed_repo"]["ok"] is True
    assert report["next_actions"][0]["action"] == "start_managed_slice"


def test_orchestrate_governed_slice_blocks_on_session_bootstrap(monkeypatch, tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": "impl-execplan/test",
                "blockers": [],
                "active_execplan": {"path": execplan_path.as_posix()},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.run_session_bootstrap_check",
        lambda **kwargs: (1, {"ok": False, "blockers": ["bootstrap_violation:initiative_branch_missing"], "status": "blocked"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.check_merge_readiness",
        lambda **kwargs: (0, {"readiness": True, "failing_checks": []}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_orchestrator_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": [{"action": "continue_active_slice"}]}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_human_operations_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": [{"action": "monitor_board_runtime"}]}),
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 1
    assert "session_bootstrap:bootstrap_violation:initiative_branch_missing" in report["blockers"]


def test_orchestrate_governed_slice_blocks_cleanly_on_ambiguous_execplan(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_game_status",
        lambda **kwargs: (
            1,
            {
                "branch": "initiative/platform-surface-simplification",
                "blockers": ["active_execplan_not_deterministic:ambiguous_changed_files"],
                "active_execplan": {},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.run_session_bootstrap_check",
        lambda **kwargs: (0, {"ok": True, "blockers": [], "status": "ok"}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 1
    assert "game_status:active_execplan_not_deterministic:ambiguous_changed_files" in report["blockers"]
    assert report["merge_readiness"]["failing_checks"] == []


def test_effective_base_ref_prefers_initiative_branch_for_impl_execplan(tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")
    graph_path = tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        """
{
  "nodes": [
    {
      "target_execplan_id": "plan-id",
      "integration_mode": "via_initiative",
      "initiative_branch": "initiative/graph-transition-automation"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    base_ref = _effective_base_ref(
        repo_root=tmp_path,
        branch="impl-execplan/test",
        execplan_path=execplan_path.as_posix(),
        default_base_ref="main",
    )

    assert base_ref == "initiative/graph-transition-automation"
