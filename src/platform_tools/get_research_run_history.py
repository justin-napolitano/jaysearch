from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope


COMMAND = "get-research-run-history"
DEFAULT_HISTORY_LOG = "artifacts/governance/research-run-history.jsonl"


def _load_history_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def get_research_run_history(
    *,
    root: str = ".",
    request_id: str | None = None,
    status: str | None = None,
    limit: int = 10,
    history_log_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    log_path = (
        Path(history_log_path).resolve()
        if history_log_path and str(history_log_path).strip()
        else root_path / DEFAULT_HISTORY_LOG
    )

    blockers: list[str] = []
    if limit < 1:
        blockers.append("limit_invalid")

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "history_log_path": log_path.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    try:
        entries = _load_history_entries(log_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "history_log_path": log_path.as_posix(),
                "blockers": ["history_log_invalid"],
            },
        )

    selected_request_id = (request_id or "").strip()
    selected_status = (status or "").strip()
    filtered = entries
    if selected_request_id:
        filtered = [item for item in filtered if str(item.get("request_id", "")).strip() == selected_request_id]
    if selected_status:
        filtered = [item for item in filtered if str(item.get("status", "")).strip() == selected_status]

    filtered.sort(
        key=lambda item: (
            str(item.get("recorded_at", "")).strip(),
            str(item.get("run_id", "")).strip(),
        ),
        reverse=True,
    )
    limited = filtered[:limit]
    counts_by_status: dict[str, int] = {}
    for item in filtered:
        key = str(item.get("status", "")).strip() or "unknown"
        counts_by_status[key] = counts_by_status.get(key, 0) + 1

    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "history_log_path": log_path.as_posix(),
            "request_id": selected_request_id,
            "status_filter": selected_status,
            "limit": limit,
            "count": len(limited),
            "counts_by_status": counts_by_status,
            "recent_runs": limited,
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--history-log-path", default=None)
    args = parser.parse_args()
    code, report = get_research_run_history(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
