from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrate_governed_slice_api_check import check_orchestrate_governed_slice_api


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_orchestrate_governed_slice_api_check_passes(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "orchestrate-governed-slice-api.schema.yaml",
        Path("spec/orchestrate-governed-slice-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice_api_check.run_orchestrate_governed_slice",
        lambda **kwargs: (
            0,
            {
                "command": "orchestrate-governed-slice",
                "status": "ok",
                "ok": True,
                "branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["root"],
                "blockers": [],
                "control_plane_status": {
                    "api_version": "control-plane.v1",
                    "command": "get-control-plane-status",
                    "status": "ok",
                    "ok": True,
                },
                "next_orchestration_action": {
                    "api_version": "control-plane.v1",
                    "command": "get-next-orchestration-action",
                    "status": "ok",
                    "ok": True,
                    "recommended_action": "cut_impl_branch",
                    "command_ref": "bin/prepare-next-impl-branch",
                    "blockers": [],
                },
                "execution": {
                    "mode": "project_only",
                    "executed": False,
                    "status": "deferred",
                    "command": "",
                    "result": None,
                },
                "post_merge_reconciliation": {
                    "command": "reconcile-pending-merge-completions",
                    "status": "ok",
                    "ok": True,
                },
                "managed_repo": None,
                "next_actions": [{"action": "cut_impl_branch", "reason": "control_plane_projection"}],
            },
        ),
    )

    code, report = check_orchestrate_governed_slice_api(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["error_count"] == 0


def test_orchestrate_governed_slice_api_check_blocks_on_missing_field(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "orchestrate-governed-slice-api.schema.yaml",
        Path("spec/orchestrate-governed-slice-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice_api_check.run_orchestrate_governed_slice",
        lambda **kwargs: (
            0,
            {
                "command": "orchestrate-governed-slice",
                "status": "ok",
                "ok": True,
                "branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "blockers": [],
                "control_plane_status": {
                    "api_version": "control-plane.v1",
                    "command": "get-control-plane-status",
                    "status": "ok",
                    "ok": True,
                },
                "next_orchestration_action": {
                    "api_version": "control-plane.v1",
                    "command": "get-next-orchestration-action",
                    "status": "ok",
                    "ok": True,
                    "recommended_action": "cut_impl_branch",
                    "command_ref": "bin/prepare-next-impl-branch",
                    "blockers": [],
                },
                "execution": {
                    "mode": "project_only",
                    "executed": False,
                    "status": "deferred",
                    "command": "",
                    "result": None,
                },
                "post_merge_reconciliation": {
                    "command": "reconcile-pending-merge-completions",
                    "status": "ok",
                    "ok": True,
                },
                "managed_repo": None,
                "next_actions": [{"action": "cut_impl_branch", "reason": "control_plane_projection"}],
            },
        ),
    )

    code, report = check_orchestrate_governed_slice_api(root=tmp_path.as_posix())

    assert code == 1
    assert report["status"] == "blocked"
    assert "missing_field:repo_root" in report["errors"]
