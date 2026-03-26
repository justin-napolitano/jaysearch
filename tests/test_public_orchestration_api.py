from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.get_graph_state import get_graph_state
from platform_tools.get_worker_status import get_worker_status
from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.resolve_worker_contract import resolve_worker_contract
from platform_tools.start_next_worker import start_next_worker


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_worker_contract_uses_next_slice_projection(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.resolve_worker_contract.get_current_branch",
        lambda **kwargs: "initiative/example",
    )
    monkeypatch.setattr(
        "platform_tools.resolve_worker_contract.get_next_worker_slice",
        lambda **kwargs: (
            0,
            {
                "selected": {
                    "contract_id": "contract-1",
                    "execplan_id": "plan-id",
                    "implementation_branch": "impl-execplan/example-worker",
                    "worker_id": "example-worker",
                    "title": "Example worker",
                    "status": "ready",
                }
            },
        ),
    )

    code, report = resolve_worker_contract(root=tmp_path.as_posix())

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["selected"]["contract_id"] == "contract-1"
    assert report["selected"]["branch"] == "impl-execplan/example-worker"


def test_get_graph_state_returns_compact_projection(tmp_path: Path) -> None:
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "graph_id": "graph-1",
                "queue_projection": {"last_reconciled_action_id": "action-1"},
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "title": "Example",
                        "status": "ready",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-100",
                        "title": "Worker api",
                        "status": "decision_gated",
                        "target_execplan_id": "plan-id",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                        "ordering": {"queue_position": 1},
                    },
                ],
            }
        )
        + "\n",
    )

    code, report = get_graph_state(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["graph_id"] == "graph-1"
    assert report["counts"]["nodes"] == 2
    assert report["initiative_nodes"][0]["node_id"] == "initiative-example"
    assert report["queued_nodes"][0]["node_id"] == "rwg-100"


def test_get_worker_status_filters_to_requested_worker(monkeypatch) -> None:
    monkeypatch.setattr(
        "platform_tools.get_worker_status.get_worker_session_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "ok": True,
                "counts": {"active": 1},
                "active_workers": [{"worker_id": "worker-1"}],
                "failed_workers": [{"worker_id": "worker-2"}],
                "abandoned_workers": [],
                "recent_runs": [{"worker_id": "worker-1", "run_id": "run-1"}],
                "blockers": [],
            },
        ),
    )

    code, report = get_worker_status(worker_id="worker-1")

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["worker_id"] == "worker-1"
    assert report["active_workers"] == [{"worker_id": "worker-1"}]
    assert report["recent_runs"] == [{"worker_id": "worker-1", "run_id": "run-1"}]


def test_start_next_worker_composes_resolve_and_run(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.start_next_worker.resolve_worker_contract",
        lambda **kwargs: (
            0,
            {
                "initiative_branch": "initiative/example",
                "selected": {
                    "contract_id": "contract-1",
                    "branch": "impl-execplan/example-worker",
                    "worker_id": "example-worker",
                },
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.start_next_worker.run_worker_contract",
        lambda **kwargs: (0, {"ok": True, "status": "ok", "selected": kwargs["contract_id"]}),
    )

    code, report = start_next_worker(root=tmp_path.as_posix(), commit=True, push_mode="staging")

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["resolution"]["selected"]["contract_id"] == "contract-1"
    assert report["worker_run"]["ok"] is True
