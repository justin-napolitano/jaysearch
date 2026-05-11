from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.get_research_run_history import get_research_run_history


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_get_research_run_history_blocks_on_invalid_limit(tmp_path: Path) -> None:
    code, report = get_research_run_history(root=tmp_path.as_posix(), limit=0)

    assert code == 1
    assert report["command"] == "get-research-run-history"
    assert report["status"] == "blocked"
    assert "limit_invalid" in report["blockers"]


def test_get_research_run_history_reads_and_filters_entries(tmp_path: Path) -> None:
    log_path = tmp_path / "artifacts" / "governance" / "research-run-history.jsonl"
    _write(
        log_path,
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "req-1-20260511T120000Z",
                        "recorded_at": "2026-05-11T12:00:00Z",
                        "request_id": "req-1",
                        "status": "ok",
                        "history_entry_path": "/tmp/r1.json",
                    }
                ),
                json.dumps(
                    {
                        "run_id": "req-2-20260511T130000Z",
                        "recorded_at": "2026-05-11T13:00:00Z",
                        "request_id": "req-2",
                        "status": "ok",
                        "history_entry_path": "/tmp/r2.json",
                    }
                ),
            ]
        )
        + "\n",
    )

    code, report = get_research_run_history(root=tmp_path.as_posix(), request_id="req-1", limit=5)

    assert code == 0
    assert report["status"] == "ok"
    assert report["count"] == 1
    assert report["recent_runs"][0]["request_id"] == "req-1"
    assert report["counts_by_status"]["ok"] == 1
