from __future__ import annotations

import argparse
import json
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.worker_session_status import get_worker_session_status


COMMAND = "get-worker-status"


def get_worker_status(
    *,
    root: str = ".",
    worker_id: str | None = None,
    stale_after_minutes: int = 60,
) -> tuple[int, dict[str, Any]]:
    code, report = get_worker_session_status(root=root, stale_after_minutes=stale_after_minutes)
    selected_worker_id = (worker_id or "").strip()
    if not selected_worker_id:
        return code, envelope(
            command=COMMAND,
            status=report["status"],
            ok=report["ok"],
            payload={
                "counts": report["counts"],
                "active_workers": report["active_workers"],
                "failed_workers": report["failed_workers"],
                "abandoned_workers": report["abandoned_workers"],
                "recent_runs": report["recent_runs"],
                "blockers": report["blockers"],
            },
        )

    def _filter(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for item in items if str(item.get("worker_id", "")).strip() == selected_worker_id]

    active = _filter(report["active_workers"])
    failed = _filter(report["failed_workers"])
    abandoned = _filter(report["abandoned_workers"])
    recent_runs = [item for item in report["recent_runs"] if str(item.get("worker_id", "")).strip() == selected_worker_id]
    blockers = [item for item in report["blockers"] if selected_worker_id in item]
    selected_report = envelope(
        command=COMMAND,
        status="blocked" if blockers else "ok",
        ok=not blockers,
        payload={
            "worker_id": selected_worker_id,
            "active_workers": active,
            "failed_workers": failed,
            "abandoned_workers": abandoned,
            "recent_runs": recent_runs,
            "blockers": blockers,
        },
    )
    return (1 if blockers else 0), selected_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--stale-after-minutes", type=int, default=60)
    args = parser.parse_args()
    code, report = get_worker_status(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
