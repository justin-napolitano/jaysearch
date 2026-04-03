from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.control_plane import API_VERSION, get_control_plane_status, get_next_orchestration_action


def test_control_plane_status_on_initiative_branch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("platform_tools.control_plane.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.control_plane.get_managed_repo_status",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": []}),
    )
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
    assert report["repo_root"] == tmp_path.resolve().as_posix()
    assert report["checks"]["managed_repo"]["ok"] is True
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
                "repo_root": tmp_path.resolve().as_posix(),
                "blockers": [],
                "checks": {
                    "managed_repo": {"blockers": [], "ok": True, "status": "ok"},
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
                "repo_root": tmp_path.resolve().as_posix(),
                "blockers": ["stale_initiative_base"],
                "checks": {
                    "managed_repo": {"blockers": [], "ok": True, "status": "ok"},
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
                "repo_root": tmp_path.resolve().as_posix(),
                "blockers": [],
                "checks": {
                    "managed_repo": {"blockers": [], "ok": True, "status": "ok"},
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


def test_control_plane_status_targets_managed_repo(monkeypatch, tmp_path: Path) -> None:
    target_repo = tmp_path / "managed"
    target_repo.mkdir()
    monkeypatch.setattr("platform_tools.control_plane.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.control_plane.get_managed_repo_status",
        lambda **kwargs: (
            0,
            {"status": "ok", "ok": True, "blockers": [], "root": kwargs["root"]},
        ),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.get_graph_state",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": [], "root": kwargs["root"]}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.check_local_runtime",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": [], "repo_root": kwargs["repo_root"]}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.get_worker_status",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": [], "root": kwargs["root"]}),
    )
    monkeypatch.setattr(
        "platform_tools.control_plane.prepare_next_impl_branch",
        lambda **kwargs: (0, {"status": "ok", "ok": True, "blockers": []}),
    )

    code, report = get_control_plane_status(
        root=tmp_path.as_posix(),
        repo_root=target_repo.as_posix(),
    )

    assert code == 0
    assert report["repo_root"] == target_repo.resolve().as_posix()
    assert report["checks"]["managed_repo"]["ok"] is True


def test_next_orchestration_action_blocks_on_managed_repo_target(monkeypatch, tmp_path: Path) -> None:
    target_repo = tmp_path / "managed"
    monkeypatch.setattr(
        "platform_tools.control_plane.get_control_plane_status",
        lambda **kwargs: (
            1,
            {
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "repo_root": target_repo.as_posix(),
                "blockers": ["missing_required_artifact:spec/workflow.yaml"],
                "checks": {
                    "managed_repo": {
                        "blockers": ["missing_required_artifact:spec/workflow.yaml"],
                        "ok": False,
                        "status": "blocked",
                    },
                    "worker_status": {"blockers": [], "ok": True, "status": "ok"},
                    "local_runtime": {"blockers": [], "ok": True, "status": "ok"},
                    "branch_preparation": {"blockers": [], "ok": True, "status": "ok"},
                },
            },
        ),
    )

    code, report = get_next_orchestration_action(root=tmp_path.as_posix(), repo_root=target_repo.as_posix())

    assert code == 1
    assert report["recommended_action"] == "resolve_control_plane_blockers"
    assert report["command_ref"] == "bin/managed-repo-status"
