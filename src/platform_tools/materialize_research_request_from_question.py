from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import load_json_object, write_json


COMMAND = "materialize-research-request-from-question"


def materialize_research_request_from_question(
    *,
    root: str = ".",
    question_path: str,
    output_root: str,
    study_design: str | None = None,
    artifact_contract: str = "v1",
    request_id: str | None = None,
    researcher_output_root: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    source_path = Path(question_path).resolve()
    destination_root = Path(output_root).resolve()

    blockers: list[str] = []
    if not source_path.exists():
        blockers.append("question_path_missing")
    if not str(output_root).strip():
        blockers.append("output_root_missing")

    question: dict[str, Any] = {}
    if not blockers:
        try:
            question = load_json_object(source_path)
        except (OSError, ValueError, TypeError):
            blockers.append("question_payload_invalid")

    question_id = str(question.get("question_id", "")).strip()
    selected_study_design = (study_design or str(question.get("study_design_hint", "")).strip()).strip()
    selected_artifact_contract = (artifact_contract or str(question.get("artifact_contract_hint", "v1")).strip()).strip() or "v1"
    selected_request_id = (request_id or f"{question_id}-request").strip() if question_id else (request_id or "").strip()
    selected_question_origin = str(question.get("question_origin", "")).strip()
    selected_topic = str(question.get("topic", "")).strip()
    request_output_root = (
        Path(researcher_output_root).resolve()
        if researcher_output_root and str(researcher_output_root).strip()
        else destination_root / "researcher_runs" / question_id
    )

    if question and not question_id:
        blockers.append("question_missing_question_id")
    if question and not selected_topic:
        blockers.append("question_missing_topic")
    if not selected_study_design:
        blockers.append("study_design_missing")
    if not selected_request_id:
        blockers.append("request_id_missing")

    materialized_path = destination_root / "execution" / "materialized_research_requests" / f"{selected_request_id or 'unknown'}.json"
    if blockers:
        return 1, envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "root": root_path.as_posix(),
                "question_path": source_path.as_posix(),
                "output_root": destination_root.as_posix(),
                "request_path": materialized_path.as_posix(),
                "blockers": sorted(set(blockers)),
            },
        )

    payload = {
        "request_id": selected_request_id,
        "question_id": question_id,
        "question_origin": selected_question_origin,
        "topic": selected_topic,
        "study_design": selected_study_design,
        "artifact_contract": selected_artifact_contract,
        "output_root": request_output_root.as_posix(),
        "domain_plugins": question.get("domain_plugins", []) if isinstance(question.get("domain_plugins"), list) else [],
        "improvement_targets": question.get("improvement_targets", []) if isinstance(question.get("improvement_targets"), list) else [],
        "hypotheses": question.get("hypotheses", []) if isinstance(question.get("hypotheses"), list) else [],
        "required_sources": question.get("required_sources", []) if isinstance(question.get("required_sources"), list) else [],
        "options": question.get("options", []) if isinstance(question.get("options"), list) else [],
        "self_review_focus": str(question.get("self_review_focus", "")).strip(),
    }
    write_json(materialized_path, payload)
    return 0, envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "root": root_path.as_posix(),
            "question_path": source_path.as_posix(),
            "output_root": destination_root.as_posix(),
            "request_path": materialized_path.as_posix(),
            "request_id": selected_request_id,
            "question_id": question_id,
            "question_origin": selected_question_origin,
            "study_design": selected_study_design,
            "researcher_output_root": request_output_root.as_posix(),
            "blockers": [],
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--question-path", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--study-design", default=None)
    parser.add_argument("--artifact-contract", default="v1")
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--researcher-output-root", default=None)
    args = parser.parse_args()
    code, report = materialize_research_request_from_question(**vars(args))
    import json

    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
