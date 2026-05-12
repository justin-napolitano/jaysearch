from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import (
    DEFAULT_BACKLOG_LOG,
    DEFAULT_QUESTIONS_DIR,
    append_jsonl,
    canonicalize_question_payload,
    load_json_object,
    question_log_entry,
    validate_question_payload,
    write_json,
)


COMMAND = "intake-research-question"


def intake_research_question(
    *,
    root: str = ".",
    question_path: str,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    source_path = Path(question_path).resolve()
    blockers: list[str] = []
    if not source_path.exists():
        blockers.append("question_path_missing")
    payload: dict[str, Any] = {}
    if not blockers:
        try:
            payload = load_json_object(source_path)
        except (OSError, ValueError, TypeError):
            blockers.append("question_payload_invalid")
    if payload:
        blockers.extend(validate_question_payload(payload))

    question_id = str(payload.get("question_id", "")).strip() if payload else ""
    artifact_path = root_path / DEFAULT_QUESTIONS_DIR / f"{question_id}.json" if question_id else root_path / DEFAULT_QUESTIONS_DIR / "unknown.json"
    log_path = root_path / DEFAULT_BACKLOG_LOG
    if question_id and artifact_path.exists():
        blockers.append("question_id_exists")

    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "question_path": source_path.as_posix(),
                "artifact_path": artifact_path.as_posix(),
                "backlog_log_path": log_path.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    canonical = canonicalize_question_payload(payload=payload, source_path=source_path)
    write_json(artifact_path, canonical)
    append_jsonl(log_path, question_log_entry(canonical=canonical, artifact_path=artifact_path))
    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "question_path": source_path.as_posix(),
            "artifact_path": artifact_path.as_posix(),
            "backlog_log_path": log_path.as_posix(),
            "question_id": str(canonical.get("question_id", "")).strip(),
            "title": str(canonical.get("title", "")).strip(),
            "question_origin": str(canonical.get("question_origin", "")).strip(),
            "status_value": str(canonical.get("status", "")).strip(),
            "target_repos": canonical.get("target_repos", []),
            "target_systems": canonical.get("target_systems", []),
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--question-path", required=True)
    args = parser.parse_args()
    code, report = intake_research_question(**vars(args))
    import json

    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
