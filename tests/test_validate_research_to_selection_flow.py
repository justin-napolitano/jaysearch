from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.validate_research_to_selection_flow import validate_research_to_selection_flow


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_question(root: Path, *, invalid: bool = False) -> str:
    payload = {
        "packet_type": "research_question_packet",
        "packet_version": "v1",
        "packet_id": "rq-packet-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "question_id": "rq-001",
        "project_id": "proj-1",
        "question_text": "How should we validate the research-to-selection flow?",
        "question_type": "validation_strategy",
        "goal": "Produce a bounded validation report before planner buildout.",
        "constraints": ["local-first", "typed packets"],
        "evaluation_targets": ["contract completeness", "handoff traceability"],
        "artifact_targets": ["research_to_selection_validation_report"],
        "decision_target": "" if invalid else "validate research-to-selection before planner",
        "decision_consequence": "changes whether planner buildout can safely proceed",
        "blocked_work_if_unanswered": "cannot justify planner entry",
    }
    path = root / "artifacts" / "research-question.packet.json"
    _write_json(path, payload)
    return "artifacts/research-question.packet.json"


def _seed_evidence(root: Path) -> str:
    payload = {
        "packet_type": "evidence_packet",
        "packet_version": "v1",
        "packet_id": "ev-001",
        "created_at": "2026-05-21T00:00:00Z",
        "producer": "test",
        "problem_id": "rq-001",
        "source_refs": [
            "https://arxiv.org/abs/2305.11738",
            "https://arxiv.org/abs/2310.06770",
            "https://www.w3.org/TR/prov-overview/",
        ],
        "claim_refs": [
            "tool-grounded critique is stronger than unsupported introspection",
            "software candidates need task-grounded evaluation",
            "handoffs should preserve provenance",
        ],
        "method_refs": ["tool-assisted critique", "task-grounded evaluation"],
        "benchmark_refs": ["research-to-selection validation"],
        "evidence_summary": "Bounded evidence summary for validation runner.",
    }
    path = root / "artifacts" / "evidence.packet.json"
    _write_json(path, payload)
    return "artifacts/evidence.packet.json"


def test_validate_research_to_selection_flow_emits_validation_report(tmp_path: Path) -> None:
    question_path = _seed_question(tmp_path)
    evidence_path = _seed_evidence(tmp_path)

    code, report = validate_research_to_selection_flow(
        root=tmp_path.as_posix(),
        research_question_path=question_path,
        evidence_packet_path=evidence_path,
        output_root="artifacts/validation-test",
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["validated_scope"] == "research_to_selection_only"
    assert "planner DAG generation" in report["explicitly_not_validated"]
    assert Path(report["validation_report_path"]).exists()
    validation_packet = json.loads(Path(report["validation_report_path"]).read_text(encoding="utf-8"))
    assert validation_packet["packet_type"] == "research_to_selection_validation_report"
    assert validation_packet["artifact_refs"]["selected_solution_scope_path"]
    assert len(validation_packet["step_reports"]) == 6


def test_validate_research_to_selection_flow_blocks_invalid_question(tmp_path: Path) -> None:
    question_path = _seed_question(tmp_path, invalid=True)
    evidence_path = _seed_evidence(tmp_path)

    code, report = validate_research_to_selection_flow(
        root=tmp_path.as_posix(),
        research_question_path=question_path,
        evidence_packet_path=evidence_path,
        output_root="artifacts/validation-test",
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "materialize_research_problem:research_question_missing_decision_target" in report[
        "blockers"
    ]
    assert report["validated_scope"] == "research_to_selection_only"
