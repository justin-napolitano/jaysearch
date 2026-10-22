from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.public_orchestration_api_check import check_public_orchestration_api


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_public_orchestration_api_check_passes_with_valid_outputs(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "public-orchestration-api.schema.yaml",
        Path("spec/public-orchestration-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.get_graph_state",
        lambda **kwargs: (
            0,
            {
                "api_version": API_VERSION,
                "command": "get-graph-state",
                "status": "ok",
                "ok": True,
                "initiative_branch": "initiative/example",
                "graph_id": "graph-1",
                "last_action_id": "action-1",
                "counts": {"nodes": 1, "completed": 0, "pending": 1},
                "initiative_nodes": [],
                "active_node": None,
                "queued_nodes": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.resolve_worker_contract",
        lambda **kwargs: (
            1,
            {
                "api_version": API_VERSION,
                "command": "resolve-worker-contract",
                "status": "blocked",
                "ok": False,
                "initiative_branch": "initiative/example",
                "blockers": ["no_runnable_worker_contract"],
                "candidates": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.get_worker_status",
        lambda **kwargs: (
            0,
            {
                "api_version": API_VERSION,
                "command": "get-worker-status",
                "status": "ok",
                "ok": True,
                "counts": {"active": 0},
                "active_workers": [],
                "failed_workers": [],
                "abandoned_workers": [],
                "recent_runs": [],
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.run_worker_contract",
        lambda **kwargs: (
            1,
            {
                "api_version": API_VERSION,
                "command": "run-worker-contract",
                "status": "blocked",
                "ok": False,
                "executor": "local_clone",
                "push_mode": "github",
                "initiative_branch": "initiative/example",
                "blockers": ["github_push_remote_required"],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.start_next_worker",
        lambda **kwargs: (
            1,
            {
                "api_version": API_VERSION,
                "command": "start-next-worker",
                "status": "blocked",
                "ok": False,
                "initiative_branch": "initiative/example",
                "resolution": {
                    "api_version": API_VERSION,
                    "command": "resolve-worker-contract",
                    "status": "blocked",
                    "ok": False,
                    "initiative_branch": "initiative/example",
                    "blockers": ["no_runnable_worker_contract"],
                    "candidates": [],
                },
                "worker_run": {
                    "api_version": API_VERSION,
                    "command": "run-worker-contract",
                    "status": "blocked",
                    "ok": False,
                },
            },
        ),
    )

    code, report = check_public_orchestration_api(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["error_count"] == 0


def test_public_orchestration_api_check_blocks_on_invalid_api_version(monkeypatch, tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "public-orchestration-api.schema.yaml",
        Path("spec/public-orchestration-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.get_graph_state",
        lambda **kwargs: (
            0,
            {
                "api_version": "public-orchestration.v0",
                "command": "get-graph-state",
                "status": "ok",
                "ok": True,
                "initiative_branch": "initiative/example",
                "graph_id": "graph-1",
                "last_action_id": "action-1",
                "counts": {"nodes": 1, "completed": 0, "pending": 1},
                "initiative_nodes": [],
                "active_node": None,
                "queued_nodes": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.resolve_worker_contract",
        lambda **kwargs: (1, {"api_version": API_VERSION, "command": "resolve-worker-contract", "status": "blocked", "ok": False, "initiative_branch": "initiative/example", "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.get_worker_status",
        lambda **kwargs: (0, {"api_version": API_VERSION, "command": "get-worker-status", "status": "ok", "ok": True, "counts": {}, "active_workers": [], "failed_workers": [], "abandoned_workers": [], "recent_runs": [], "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.run_worker_contract",
        lambda **kwargs: (1, {"api_version": API_VERSION, "command": "run-worker-contract", "status": "blocked", "ok": False, "executor": "local_clone", "push_mode": "github"}),
    )
    monkeypatch.setattr(
        "platform_tools.public_orchestration_api_check.start_next_worker",
        lambda **kwargs: (1, {"api_version": API_VERSION, "command": "start-next-worker", "status": "blocked", "ok": False, "initiative_branch": "initiative/example", "resolution": {}}),
    )

    code, report = check_public_orchestration_api(root=tmp_path.as_posix())

    assert code == 1
    assert report["status"] == "blocked"
    assert any(item.startswith("get_graph_state:invalid_api_version") for item in report["errors"])


def test_health_check_never_launches_ready_worker(monkeypatch, tmp_path: Path) -> None:
    """A ready contract must not make health/bootstrap recurse into execution."""
    from platform_tools.public_orchestration_api import envelope

    _write(
        tmp_path / "spec" / "public-orchestration-api.schema.yaml",
        Path("spec/public-orchestration-api.schema.yaml").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.get_graph_state", lambda **kwargs: (0, envelope(
        command="get-graph-state", status="ok", ok=True,
        payload={"initiative_branch": "initiative/example", "graph_id": "graph-1", "last_action_id": "action-1", "counts": {"nodes": 1, "completed": 0, "pending": 1}, "initiative_nodes": [], "active_node": None, "queued_nodes": []},
    )))
    ready = (0, envelope(command="resolve-worker-contract", status="ok", ok=True, payload={
        "initiative_branch": "initiative/example", "selected": {"contract_id": "ready", "branch": "impl-execplan/ready", "worker_id": "ready", "node_id": "ready", "execplan_id": "ready", "title": "Ready worker"}, "candidates": [], "blockers": [],
    }))
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.resolve_worker_contract", lambda **kwargs: ready)
    monkeypatch.setattr("platform_tools.start_next_worker.resolve_worker_contract", lambda **kwargs: ready)
    monkeypatch.setattr("platform_tools.public_orchestration_api_check.get_worker_status", lambda **kwargs: (0, envelope(
        command="get-worker-status", status="ok", ok=True,
        payload={"counts": {}, "active_workers": [], "failed_workers": [], "abandoned_workers": [], "recent_runs": [], "blockers": []},
    )))

    def forbidden_launch(**kwargs):
        raise AssertionError("Health check must not start a worker coordinator")

    monkeypatch.setattr("platform_tools.run_worker_contract.run_worker_session_coordinator", forbidden_launch)
    code, report = check_public_orchestration_api(root=tmp_path.as_posix())
    assert code == 0, report
    assert report["ok"] is True
    assert len(report["checks"]) == 5
    assert all(check["ok"] for check in report["checks"])
