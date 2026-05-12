from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


DEFAULT_BACKLOG_LOG = Path("artifacts/governance/research-question-backlog.jsonl")
DEFAULT_QUESTIONS_DIR = Path("artifacts/governance/research-questions")
SUPPORTED_QUESTION_ORIGINS = {"user", "platform", "researcher"}
SUPPORTED_QUESTION_STATUSES = {"queued", "active", "answered", "deferred"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload_not_object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def append_jsonl(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def normalize_string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def validate_question_payload(payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    question_id = str(payload.get("question_id", "")).strip()
    title = str(payload.get("title", "")).strip()
    topic = str(payload.get("topic", "")).strip()
    question_origin = str(payload.get("question_origin", "user")).strip() or "user"
    status = str(payload.get("status", "queued")).strip() or "queued"

    if not question_id:
        blockers.append("question_missing_question_id")
    if not title:
        blockers.append("question_missing_title")
    if not topic:
        blockers.append("question_missing_topic")
    if question_origin not in SUPPORTED_QUESTION_ORIGINS:
        blockers.append("question_origin_invalid")
    if status not in SUPPORTED_QUESTION_STATUSES:
        blockers.append("question_status_invalid")
    return blockers


def canonicalize_question_payload(
    *,
    payload: dict[str, Any],
    source_path: Path,
    existing_created_at: str = "",
) -> dict[str, Any]:
    created_at = existing_created_at or utc_now()
    status = str(payload.get("status", "queued")).strip() or "queued"
    return {
        "question_id": str(payload.get("question_id", "")).strip(),
        "title": str(payload.get("title", "")).strip(),
        "topic": str(payload.get("topic", "")).strip(),
        "question": str(payload.get("question", "")).strip(),
        "question_origin": str(payload.get("question_origin", "user")).strip() or "user",
        "status": status,
        "priority": str(payload.get("priority", "normal")).strip() or "normal",
        "requested_by": str(payload.get("requested_by", "")).strip(),
        "decision_deadline": str(payload.get("decision_deadline", "")).strip(),
        "success_condition": str(payload.get("success_condition", "")).strip(),
        "study_design_hint": str(payload.get("study_design_hint", "")).strip(),
        "artifact_contract_hint": str(payload.get("artifact_contract_hint", "")).strip(),
        "self_review_focus": str(payload.get("self_review_focus", "")).strip(),
        "target_repos": normalize_string_list(payload.get("target_repos", [])),
        "target_systems": normalize_string_list(payload.get("target_systems", [])),
        "constraints": normalize_string_list(payload.get("constraints", [])),
        "domain_plugins": normalize_string_list(payload.get("domain_plugins", [])),
        "improvement_targets": normalize_string_list(payload.get("improvement_targets", [])),
        "hypotheses": payload.get("hypotheses", []) if isinstance(payload.get("hypotheses"), list) else [],
        "required_sources": payload.get("required_sources", []) if isinstance(payload.get("required_sources"), list) else [],
        "options": payload.get("options", []) if isinstance(payload.get("options"), list) else [],
        "created_at": created_at,
        "updated_at": utc_now(),
        "source_path": source_path.as_posix(),
    }


def question_log_entry(*, canonical: dict[str, Any], artifact_path: Path) -> dict[str, Any]:
    return {
        "question_id": str(canonical.get("question_id", "")).strip(),
        "title": str(canonical.get("title", "")).strip(),
        "topic": str(canonical.get("topic", "")).strip(),
        "question_origin": str(canonical.get("question_origin", "")).strip(),
        "status": str(canonical.get("status", "")).strip(),
        "priority": str(canonical.get("priority", "")).strip(),
        "target_repos": canonical.get("target_repos", []) if isinstance(canonical.get("target_repos"), list) else [],
        "target_systems": canonical.get("target_systems", []) if isinstance(canonical.get("target_systems"), list) else [],
        "recorded_at": utc_now(),
        "artifact_path": artifact_path.as_posix(),
    }

