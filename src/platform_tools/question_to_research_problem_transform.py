from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from platform_tools.public_orchestration_api import envelope
from platform_tools.research_questions import write_json


COMMAND = "question-to-research-problem-transform"
DEFAULT_OUTPUT_ROOT = Path("artifacts/research-problem-materialization/runs")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("qrpt-%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload_not_object:{path.as_posix()}")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def materialize_research_problem(
    *,
    root: str = ".",
    research_question_path: str,
    evidence_packet_path: str | None = None,
    output_root: str = DEFAULT_OUTPUT_ROOT.as_posix(),
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(root)
    question_payload = _load_json(repo_root / research_question_path)
    evidence_payload = _load_json(repo_root / evidence_packet_path) if evidence_packet_path else None
    run_id = _run_id()
    run_root = repo_root / output_root / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    if str(question_payload.get("packet_type", "")).strip() != "research_question_packet":
        blockers.append("research_question_packet_type_invalid")

    question_id = str(question_payload.get("question_id", "")).strip()
    project_id = str(question_payload.get("project_id", "")).strip()
    question_text = str(question_payload.get("question_text", "")).strip()
    goal = str(question_payload.get("goal", "")).strip()
    decision_target = str(question_payload.get("decision_target", "")).strip()
    decision_consequence = str(question_payload.get("decision_consequence", "")).strip()
    blocked_work = str(question_payload.get("blocked_work_if_unanswered", "")).strip()
    constraints = _string_list(question_payload.get("constraints", []))
    evaluation_targets = _string_list(question_payload.get("evaluation_targets", []))
    artifact_targets = _string_list(question_payload.get("artifact_targets", []))

    if not question_id:
        blockers.append("research_question_missing_question_id")
    if not project_id:
        blockers.append("research_question_missing_project_id")
    if not question_text:
        blockers.append("research_question_missing_question_text")
    if not goal:
        blockers.append("research_question_missing_goal")
    if not decision_target:
        blockers.append("research_question_missing_decision_target")
    if not decision_consequence:
        blockers.append("research_question_missing_decision_consequence")
    if not blocked_work:
        blockers.append("research_question_missing_blocked_work_if_unanswered")
    if not evaluation_targets:
        blockers.append("research_question_missing_evaluation_targets")
    if not artifact_targets:
        blockers.append("research_question_missing_artifact_targets")
    if evidence_payload is not None and str(evidence_payload.get("packet_type", "")).strip() != "evidence_packet":
        blockers.append("evidence_packet_type_invalid")

    if blockers:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={
                "research_question_path": str((repo_root / research_question_path).resolve()),
                "evidence_packet_path": str((repo_root / evidence_packet_path).resolve()) if evidence_packet_path else "",
                "blockers": sorted(set(blockers)),
            },
        )
        write_json(run_root / "question-to-research-problem-transform.report.json", report)
        return 1, report

    problem_id = f"research-problem:{project_id}:{question_id}"
    source_refs = _string_list(evidence_payload.get("source_refs", [])) if evidence_payload else []
    method_refs = _string_list(evidence_payload.get("method_refs", [])) if evidence_payload else []
    benchmark_refs = _string_list(evidence_payload.get("benchmark_refs", [])) if evidence_payload else []
    evidence_summary = str(evidence_payload.get("evidence_summary", "")).strip() if evidence_payload else ""

    research_problem_packet = {
        "packet_type": "research_problem_packet",
        "packet_version": "v1",
        "packet_id": f"{problem_id}:packet",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "problem_id": problem_id,
        "title": f"Research problem for {question_id}",
        "goal": goal,
        "problem_statement": question_text,
        "constraints": constraints,
        "repo_context": {
            "project_id": project_id,
            "decision_target": decision_target,
            "decision_consequence": decision_consequence,
            "blocked_work_if_unanswered": blocked_work,
        },
        "artifact_targets": artifact_targets,
        "evaluation_criteria": evaluation_targets,
        "search_budget": {
            "max_sources": max(len(source_refs), 5),
            "max_candidates": 3,
        },
        "output_requirements": [
            "research_candidate_packet[]",
            "research_evaluation_packet[]",
            "research_recommendation_packet",
        ],
        "evidence_packet_ref": str((repo_root / evidence_packet_path).resolve()) if evidence_packet_path else "",
        "reference_implementations": source_refs,
        "baseline_artifact_refs": benchmark_refs,
        "allowed_tools": ["evidence-search-tool", "memory-tool", "research-tool"],
        "runtime_environment": "repo-local",
        "language": "python",
        "research_context": {
            "method_refs": method_refs,
            "evidence_summary": evidence_summary,
        },
    }
    research_problem_path = write_json(run_root / "research-problem.packet.json", research_problem_packet)

    transform_packet = {
        "packet_type": "question_to_research_problem_transform",
        "packet_version": "v1",
        "packet_id": f"{problem_id}:transform",
        "created_at": _utc_now(),
        "producer": COMMAND,
        "research_question_ref": str((repo_root / research_question_path).resolve()),
        "evidence_packet_ref": str((repo_root / evidence_packet_path).resolve()) if evidence_packet_path else "",
        "research_problem_ref": research_problem_path.as_posix(),
        "traceability": {
            "question_id": question_id,
            "project_id": project_id,
            "decision_target": decision_target,
            "evaluation_targets": evaluation_targets,
            "mapped_evaluation_criteria": evaluation_targets,
        },
    }
    transform_path = write_json(run_root / "question-to-research-problem-transform.packet.json", transform_packet)

    report = envelope(
        command=COMMAND,
        status="ok",
        ok=True,
        payload={
            "run_id": run_id,
            "research_question_path": str((repo_root / research_question_path).resolve()),
            "evidence_packet_path": str((repo_root / evidence_packet_path).resolve()) if evidence_packet_path else "",
            "research_problem_path": research_problem_path.as_posix(),
            "transform_packet_path": transform_path.as_posix(),
            "blockers": [],
        },
    )
    write_json(run_root / "question-to-research-problem-transform.report.json", report)
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--research-question-path", required=True)
    parser.add_argument("--evidence-packet-path", default=None)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT.as_posix())
    args = parser.parse_args()
    try:
        code, report = materialize_research_problem(
            root=args.root,
            research_question_path=args.research_question_path,
            evidence_packet_path=args.evidence_packet_path,
            output_root=args.output_root,
        )
    except (FileNotFoundError, PermissionError, ValueError, json.JSONDecodeError) as exc:
        report = envelope(
            command=COMMAND,
            status="blocked",
            ok=False,
            payload={"blockers": [f"{exc.__class__.__name__}:{exc}"]},
        )
        code = 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
