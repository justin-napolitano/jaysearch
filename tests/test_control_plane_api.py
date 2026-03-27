from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.control_plane import API_VERSION, get_control_plane_status, get_next_orchestration_action


def test_control_plane_status_on_initiative_branch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("platform_tools.control_plane.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.control_plane.get_graph_state",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.check_local_runtime",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.get_worker_status",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.prepare_next_impl_branch",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "blockers": [],
                "selected": {"implementation_branch": "impl-execplan/example"},
            },
        ),
    )

    code, report = get_control_plane_status(root=tmp_path.as_posix())

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["branch_role"] == "initiative"
    assert report["checks"]["branch_preparation"]["ok"] is True


def test_next_orchestration_action_prefers_cut_impl_branch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.control_plane.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "blockers": [],
                "checks": {
                    "worker_status": {"blockers": [], "ok": True, "status": "ok"},
                    "local_runtime": {"blockers": [], "ok": True, "status": "ok"},
                    "branch_preparation": {"blockers": [], "ok": True, "status": "ok"},
                },
            },
        ),
    )

    code, report = get_next_orchestration_action(root=tmp_path.as_posix())

    assert code == 0
    assert report["recommended_action"] == "cut_impl_branch"
    assert report["command_ref"] == "bin/prepare-next-impl-branch"


def test_next_orchestration_action_blocks_for_stale_impl(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.control_plane.get_control_plane_status",
        lambda **kwargs: (
            1,
            {
                "current_branch": "impl-execplan/example",
                "branch_role": "implementation_execplan",
                "initiative_branch": "initiative/example",
                "blockers": ["stale_initiative_base"],
                "checks": {
                    "worker_status": {"blockers": [], "ok": True, "status": "ok"},
                    "local_runtime": {"blockers": [], "ok": True, "status": "ok"},
                    "merge_readiness": {
                        "blockers": ["stale_initiative_base"],
                        "ok": False,
                        "status": "blocked",
                    },
                },
            },
        ),
    )

    code, report = get_next_orchestration_action(root=tmp_path.as_posix())

    assert code == 0
    assert report["recommended_action"] == "restack_on_initiative"
    assert report["command_ref"] == "bin/get-merge-readiness"


def test_next_orchestration_action_opens_pr_when_impl_is_ready(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.control_plane.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "impl-execplan/example",
                "branch_role": "implementation_execplan",
                "initiative_branch": "initiative/example",
                "blockers": [],
                "checks": {
                    "worker_status": {"blockers": [], "ok": True, "status": "ok"},
                    "local_runtime": {"blockers": [], "ok": True, "status": "ok"},
                    "merge_readiness": {"blockers": [], "ok": True, "status": "ok"},
                },
            },
        ),
    )

    code, report = get_next_orchestration_action(root=tmp_path.as_posix())

    assert code == 0
    assert report["recommended_action"] == "open_pr_to_initiative"
    assert report["command_ref"] == "bin/get-pr-integration-contract"
