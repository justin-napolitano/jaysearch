from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUNTIME_RUN_DIR = Path("artifacts/governance/worker-runs")
RUNTIME_EVENT_LOG = Path("artifacts/governance/worker-runtime-events.jsonl")
PROBLEM_DIR = Path("artifacts/governance/problems")
PROBLEM_DETAIL_MAX_CHARS = 280
EVENT_SUMMARY_MAX_CHARS = 160
TOKEN_ECONOMY_POLICY = {
    "mode": "compact_structured",
    "max_problem_detail_chars": PROBLEM_DETAIL_MAX_CHARS,
    "max_event_summary_chars": EVENT_SUMMARY_MAX_CHARS,
    "prefer_refs_over_restatement": True,
    "prefer_code_over_verbose_context_when_safe": True,
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_trace_id() -> str:
    return secrets.token_hex(16)


def make_run_id(worker_id: str) -> str:
    compact = "".join(char if char.isalnum() else "-" for char in worker_id.lower()).strip("-") or "worker"
    return f"run-{utc_timestamp().replace(':', '').replace('-', '')}-{compact}"


def _compact_text(value: str, *, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path.as_posix()


def append_runtime_event(
    *,
    root: Path,
    event_type: str,
    run_id: str,
    trace_id: str,
    worker_id: str,
    branch: str,
    initiative_id: str,
    contract_id: str,
    summary: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "specversion": "1.0",
        "id": f"{run_id}:{event_type}:{secrets.token_hex(4)}",
        "type": event_type,
        "source": "platform_tools/governed_worker",
        "subject": run_id,
        "time": utc_timestamp(),
        "datacontenttype": "application/json",
        "data": {
            "run_id": run_id,
            "trace_id": trace_id,
            "worker_id": worker_id,
            "branch": branch,
            "initiative_id": initiative_id,
            "contract_id": contract_id,
            "summary": _compact_text(summary, max_chars=EVENT_SUMMARY_MAX_CHARS),
            **(data or {}),
        },
    }
    path = root / RUNTIME_EVENT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def create_run_metadata(
    *,
    root: Path,
    run_id: str,
    trace_id: str,
    worker_id: str,
    branch: str,
    backend: str,
    workspace_path: str,
    initiative_id: str,
    initiative_branch: str,
    contract_id: str,
    execplan_id: str,
    push_targets: list[dict[str, Any]],
    task_command: str,
) -> dict[str, Any]:
    record = {
        "version": "v1",
        "run_id": run_id,
        "trace_id": trace_id,
        "worker_id": worker_id,
        "branch": branch,
        "executor_backend": backend,
        "workspace_path": workspace_path,
        "initiative_id": initiative_id,
        "initiative_branch": initiative_branch,
        "contract_id": contract_id,
        "execplan_id": execplan_id,
        "status": "running",
        "outcome": "",
        "started_at": utc_timestamp(),
        "completed_at": "",
        "task_command": task_command,
        "push_targets": push_targets,
        "event_log_path": (root / RUNTIME_EVENT_LOG).as_posix(),
        "problem_ref": "",
        "token_economy_policy": TOKEN_ECONOMY_POLICY,
    }
    record["run_path"] = _write_json(root / RUNTIME_RUN_DIR / f"{run_id}.json", record)
    return record


def update_run_metadata(*, root: Path, record: dict[str, Any]) -> dict[str, Any]:
    _write_json(root / RUNTIME_RUN_DIR / f"{record['run_id']}.json", record)
    record["run_path"] = (root / RUNTIME_RUN_DIR / f"{record['run_id']}.json").as_posix()
    return record


def write_problem_artifact(
    *,
    root: Path,
    run_id: str,
    trace_id: str,
    initiative_id: str,
    worker_id: str,
    contract_id: str,
    execplan_id: str,
    branch: str,
    executor_backend: str,
    error_code: str,
    title: str,
    detail: str,
    status: int,
    retryable: bool,
    what_you_should_do: str,
    artifact_refs: list[str] | None = None,
) -> dict[str, str]:
    problem = {
        "type": f"https://platform.local/problems/{error_code.lower().replace('_', '-')}",
        "title": title,
        "status": status,
        "detail": _compact_text(detail, max_chars=PROBLEM_DETAIL_MAX_CHARS),
        "instance": run_id,
        "error_code": error_code,
        "error_category": "worker_runtime",
        "retryable": retryable,
        "retry_after": None,
        "owner_action_required": not retryable,
        "initiative_id": initiative_id,
        "worker_id": worker_id,
        "contract_id": contract_id,
        "execplan_id": execplan_id,
        "branch": branch,
        "executor_backend": executor_backend,
        "trace_id": trace_id,
        "artifact_refs": artifact_refs or [],
        "what_you_should_do": _compact_text(what_you_should_do, max_chars=PROBLEM_DETAIL_MAX_CHARS),
    }
    json_path = root / PROBLEM_DIR / f"{run_id}.problem.json"
    markdown_path = root / PROBLEM_DIR / f"{run_id}.problem.md"
    _write_json(json_path, problem)
    markdown = "\n".join(
        [
            "---",
            f"error_code: {problem['error_code']}",
            f"status: {problem['status']}",
            f"retryable: {str(problem['retryable']).lower()}",
            f"initiative_id: {problem['initiative_id']}",
            f"worker_id: {problem['worker_id']}",
            f"trace_id: {problem['trace_id']}",
            "---",
            "",
            f"# {problem['title']}",
            "",
            "## What Happened",
            "",
            problem["detail"],
            "",
            "## What You Should Do",
            "",
            problem["what_you_should_do"],
            "",
        ]
    )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    return {"json": json_path.as_posix(), "markdown": markdown_path.as_posix()}
