from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMMAND = "worker-session-status"
LEASE_DIR = Path("artifacts/governance/worker-sessions")
AUDIT_LOG = Path("artifacts/governance/worker-session-events.jsonl")
RUNTIME_EVENT_LOG = Path("artifacts/governance/worker-runtime-events.jsonl")
RUN_DIR = Path("artifacts/governance/worker-runs")
PROBLEM_DIR = Path("artifacts/governance/problems")


def _parse_timestamp(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _load_leases(root: Path) -> list[dict[str, Any]]:
    lease_dir = root / LEASE_DIR
    if not lease_dir.exists():
        return []
    leases: list[dict[str, Any]] = []
    for path in sorted(lease_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        item = dict(payload)
        item["lease_path"] = path.as_posix()
        leases.append(item)
    return leases


def _load_audit_events(root: Path) -> list[dict[str, Any]]:
    path = root / AUDIT_LOG
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _load_runtime_events(root: Path) -> list[dict[str, Any]]:
    path = root / RUNTIME_EVENT_LOG
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _load_runs(root: Path) -> list[dict[str, Any]]:
    run_dir = root / RUN_DIR
    if not run_dir.exists():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            runs.append(payload)
    return runs


def get_worker_session_status(
    *,
    root: str = ".",
    stale_after_minutes: int = 60,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    leases = _load_leases(root_path)
    events = _load_audit_events(root_path)
    runtime_events = _load_runtime_events(root_path)
    runs = _load_runs(root_path)
    now = datetime.now(timezone.utc)
    stale_threshold_seconds = stale_after_minutes * 60

    active: list[dict[str, Any]] = []
    closed: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    abandoned: list[dict[str, Any]] = []

    for lease in leases:
        issued_at = _parse_timestamp(str(lease.get("issued_at", "")).strip())
        age_seconds = int((now - issued_at).total_seconds()) if issued_at else None
        lease["age_seconds"] = age_seconds
        status = str(lease.get("status", "")).strip()
        outcome = str(lease.get("outcome", "")).strip()
        if status == "active":
            active.append(lease)
            if age_seconds is not None and age_seconds > stale_threshold_seconds:
                stale.append(lease)
        else:
            closed.append(lease)
            if outcome == "failed":
                failed.append(lease)
            elif outcome == "abandoned":
                abandoned.append(lease)

    blockers: list[str] = []
    if stale:
        blockers.extend(f"stale_worker_session:{item.get('worker_id', '')}" for item in stale)

    next_actions: list[dict[str, str]] = []
    if stale:
        next_actions.append({"action": "inspect_or_close_stale_workers", "reason": "stale_worker_sessions_detected"})
    elif active:
        next_actions.append({"action": "monitor_active_workers", "reason": "active_worker_sessions_present"})
    else:
        next_actions.append({"action": "issue_new_worker_lease", "reason": "no_active_worker_sessions"})

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "root": root_path.as_posix(),
        "lease_dir": (root_path / LEASE_DIR).as_posix(),
        "audit_log": (root_path / AUDIT_LOG).as_posix(),
        "runtime_event_log": (root_path / RUNTIME_EVENT_LOG).as_posix(),
        "counts": {
            "active": len(active),
            "closed": len(closed),
            "stale": len(stale),
            "failed": len(failed),
            "abandoned": len(abandoned),
            "audit_events": len(events),
            "runtime_events": len(runtime_events),
            "runs": len(runs),
            "problems": len(list((root_path / PROBLEM_DIR).glob("*.problem.json"))) if (root_path / PROBLEM_DIR).exists() else 0,
        },
        "active_workers": active,
        "stale_workers": stale,
        "failed_workers": failed,
        "abandoned_workers": abandoned,
        "recent_runs": runs[-5:],
        "blockers": sorted(set(blockers)),
        "next_actions": next_actions,
    }
    return (0 if not blockers else 1), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--stale-after-minutes", type=int, default=60)
    args = parser.parse_args()
    code, report = get_worker_session_status(root=args.root, stale_after_minutes=args.stale_after_minutes)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
