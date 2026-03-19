from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.auto_reconcile_main import run_auto_reconcile_main


def test_auto_reconcile_main_skips_ineligible_branch() -> None:
    code, report = run_auto_reconcile_main(branch="impl-execplan/test")

    assert code == 0
    assert report["status"] == "skipped"
    assert report["reason"] == "branch_not_eligible"


def test_auto_reconcile_main_runs_reconciliation_on_main(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.auto_reconcile_main.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 1},
    )
    monkeypatch.setattr(
        "platform_tools.auto_reconcile_main.check_remaining_work_graph",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "errors": []}),
    )

    code, report = run_auto_reconcile_main(root=tmp_path.as_posix(), branch="main", source_hook="post-merge")

    assert code == 0
    assert report["status"] == "ok"
    assert report["reconciliation"]["reconciled_count"] == 1


def test_auto_reconcile_main_skips_non_branch_checkout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.auto_reconcile_main.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0},
    )

    code, report = run_auto_reconcile_main(
        root=tmp_path.as_posix(),
        branch="main",
        source_hook="post-checkout",
        checkout_kind="file",
    )

    assert code == 0
    assert report["status"] == "skipped"
    assert report["reason"] == "non_branch_checkout"
