from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.worker_session_status import get_worker_session_status


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_worker_session_status_reports_active_and_closed_workers(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-sessions" / "worker-1.json",
        {
            "worker_id": "worker-1",
            "status": "active",
            "issued_at": "2026-03-24T12:00:00Z",
            "branch": "impl-execplan/worker-1",
            "initiative_branch": "initiative/example",
        },
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-sessions" / "worker-2.json",
        {
            "worker_id": "worker-2",
            "status": "closed",
            "outcome": "failed",
            "issued_at": "2026-03-24T10:00:00Z",
            "closed_at": "2026-03-24T10:10:00Z",
            "branch": "impl-execplan/worker-2",
            "initiative_branch": "initiative/example",
        },
    )
    _write_jsonl(
        tmp_path / "artifacts" / "governance" / "worker-session-events.jsonl",
        [
            {"event": "worker_lease_issued", "worker_id": "worker-1"},
            {"event": "worker_lease_closed", "worker_id": "worker-2"},
        ],
    )
    _write_jsonl(
        tmp_path / "artifacts" / "governance" / "worker-runtime-events.jsonl",
        [
            {"type": "platform.worker.run.started", "data": {"run_id": "run-1"}},
            {"type": "platform.worker.run.completed", "data": {"run_id": "run-1"}},
        ],
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-runs" / "run-1.json",
        {
            "run_id": "run-1",
            "status": "completed",
            "worker_id": "worker-2",
        },
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "problems" / "run-2.problem.json",
        {
            "instance": "run-2",
            "title": "problem",
        },
    )

    code, report = get_worker_session_status(root=tmp_path.as_posix(), stale_after_minutes=10_000_000)

    assert code == 0
    assert report["counts"]["active"] == 1
    assert report["counts"]["failed"] == 1
    assert report["counts"]["audit_events"] == 2
    assert report["counts"]["runtime_events"] == 2
    assert report["counts"]["runs"] == 1
    assert report["counts"]["problems"] == 1
    assert report["recent_runs"][0]["run_id"] == "run-1"
    assert report["next_actions"][0]["action"] == "monitor_active_workers"


def test_worker_session_status_blocks_on_stale_active_workers(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-sessions" / "worker-1.json",
        {
            "worker_id": "worker-1",
            "status": "active",
            "issued_at": "2020-03-24T12:00:00Z",
            "branch": "impl-execplan/worker-1",
            "initiative_branch": "initiative/example",
        },
    )

    code, report = get_worker_session_status(root=tmp_path.as_posix(), stale_after_minutes=1)

    assert code == 1
    assert "stale_worker_session:worker-1" in report["blockers"]
    assert report["next_actions"][0]["action"] == "inspect_or_close_stale_workers"
