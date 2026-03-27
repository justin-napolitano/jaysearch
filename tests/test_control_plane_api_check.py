from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.control_plane import API_VERSION
from platform_tools.control_plane_api_check import check_control_plane_api


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_control_plane_api_check_passes_with_valid_outputs(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "control-plane-api.schema.yaml",
        Path("spec/control-plane-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane_api_check.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "api_version": API_VERSION,
                "command": "get-control-plane-status",
                "status": "ok",
                "ok": True,
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "blockers": [],
                "checks": {},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane_api_check.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "api_version": API_VERSION,
                "command": "get-next-orchestration-action",
                "status": "ok",
                "ok": True,
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "recommended_action": "cut_impl_branch",
                "command_ref": "bin/prepare-next-impl-branch",
                "blockers": [],
            },
        ),
    )

    code, report = check_control_plane_api(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["error_count"] == 0


def test_control_plane_api_check_blocks_on_invalid_api_version(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "control-plane-api.schema.yaml",
        Path("spec/control-plane-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane_api_check.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "api_version": "control-plane.v0",
                "command": "get-control-plane-status",
                "status": "ok",
                "ok": True,
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "blockers": [],
                "checks": {},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane_api_check.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "api_version": API_VERSION,
                "command": "get-next-orchestration-action",
                "status": "ok",
                "ok": True,
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "recommended_action": "cut_impl_branch",
                "command_ref": "bin/prepare-next-impl-branch",
                "blockers": [],
            },
        ),
    )

    code, report = check_control_plane_api(root=tmp_path.as_posix())

    assert code == 1
    assert report["status"] == "blocked"
    assert any(item.startswith("get_control_plane_status:invalid_api_version") for item in report["errors"])
