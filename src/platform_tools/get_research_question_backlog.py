from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import DEFAULT_BACKLOG_LOG, load_jsonl


COMMAND = "get-research-question-backlog"


def get_research_question_backlog(
    *,
    root: str = ".",
    question_origin: str | None = None,
    status: str | None = None,
    target_repo: str | None = None,
    limit: int = 10,
    backlog_log_path: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    log_path = Path(backlog_log_path).resolve() if backlog_log_path and str(backlog_log_path).strip() else root_path / DEFAULT_BACKLOG_LOG

    blockers: list[str] = []
    if limit < 1:
        blockers.append("limit_invalid")
    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "backlog_log_path": log_path.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    try:
        entries = load_jsonl(log_path)
    except (OSError, ValueError, TypeError):
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "backlog_log_path": log_path.as_posix(),
                "blockers": ["backlog_log_invalid"],
            },
        )

    selected_origin = (question_origin or "").strip()
    selected_status = (status or "").strip()
    selected_target_repo = (target_repo or "").strip()
    filtered = entries
    if selected_origin:
        filtered = [item for item in filtered if str(item.get("question_origin", "")).strip() == selected_origin]
    if selected_status:
        filtered = [item for item in filtered if str(item.get("status", "")).strip() == selected_status]
    if selected_target_repo:
        filtered = [
            item
            for item in filtered
            if selected_target_repo in [str(value).strip() for value in item.get("target_repos", []) if str(value).strip()]
        ]

    filtered.sort(
        key=lambda item: (
            str(item.get("recorded_at", "")).strip(),
            str(item.get("question_id", "")).strip(),
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
            "backlog_log_path": log_path.as_posix(),
            "question_origin_filter": selected_origin,
            "status_filter": selected_status,
            "target_repo_filter": selected_target_repo,
            "limit": limit,
            "count": len(limited),
            "counts_by_status": counts_by_status,
            "questions": limited,
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--question-origin", default=None)
    parser.add_argument("--status", default=None)
    parser.add_argument("--target-repo", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--backlog-log-path", default=None)
    args = parser.parse_args()
    code, report = get_research_question_backlog(**vars(args))
    import json

    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
