from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.prepare_research_followups import prepare_research_followups
from platform_tools.public_orchestration_api import API_VERSION


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_prepare_research_followups_blocks_on_missing_report(tmp_path: Path) -> None:
    code, report = prepare_research_followups(
        root=tmp_path.as_posix(),
        report_path=(tmp_path / "missing.json").as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "prepare-research-followups"
    assert report["status"] == "blocked"
    assert "report_path_missing" in report["blockers"]


def test_prepare_research_followups_blocks_on_invalid_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    _write(report_path, json.dumps({"command": "not-run-research-capability", "ok": True, "status": "ok"}))

    code, report = prepare_research_followups(
        root=tmp_path.as_posix(),
        report_path=report_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "report_command_invalid" in report["blockers"]
    assert "report_missing_improvement_candidates_path" in report["blockers"]


def test_prepare_research_followups_emits_draft_followups(tmp_path: Path) -> None:
    candidates_path = tmp_path / "research" / "execution" / "improvement_candidates" / "req-1.json"
    _write(
        candidates_path,
        json.dumps(
            {
                "request_id": "req-1",
                "question_id": "q-1",
                "question_origin": "user",
                "ranking_rubric": {
                    "promotion_gate": {
                        "minimum_rigor": 3.0,
                        "minimum_feasibility": 3.0,
                        "minimum_total_score": 4.0,
                    }
                },
                "candidates": [
                    {
                        "candidate_id": "cand-01",
                        "target": "platform-control-plane",
                        "target_repo_hint": "codex_platform",
                        "proposed_change": "Prepare governed draft follow-up seeds from ranked candidates.",
                        "expected_benefit": "Turns research into actionable work.",
                        "disposition": "promote-to-execplan",
                        "total_score": 4.5,
                        "scores": {"rigor": 4.2, "feasibility": 4.1},
                        "source_hypothesis_ids": ["hyp-1"],
                        "evidence_refs": ["https://example.com/source-a"],
                    },
                    {
                        "candidate_id": "cand-03",
                        "target": "platform-control-plane",
                        "target_repo_hint": "codex_platform",
                        "proposed_change": "Add persistent candidate backlog views.",
                        "expected_benefit": "Improves portfolio visibility.",
                        "disposition": "promote_to_execplan",
                        "total_score": 4.4,
                        "scores": {"rigor": 4.0, "feasibility": 3.9},
                        "source_hypothesis_ids": ["hyp-3"],
                        "evidence_refs": ["https://example.com/source-c"],
                    },
                    {
                        "candidate_id": "cand-02",
                        "target": "researcher-harness",
                        "target_repo_hint": "researcher-harness",
                        "proposed_change": "Add another study-design plugin.",
                        "expected_benefit": "Broader harness coverage.",
                        "disposition": "research-more",
                        "total_score": 3.6,
                        "scores": {"rigor": 3.4, "feasibility": 3.8},
                        "source_hypothesis_ids": ["hyp-2"],
                        "evidence_refs": ["https://example.com/source-b"],
                    },
                ],
                "follow_up_questions": [
                    {
                        "question_id": "followup-01",
                        "origin": "researcher",
                        "topic": "What is the smallest governed slice to land next?",
                        "linked_candidate_ids": ["cand-01"],
                    }
                ],
            }
        ),
    )
    report_path = tmp_path / "platform-report.json"
    _write(
        report_path,
        json.dumps(
            {
                "api_version": API_VERSION,
                "command": "run-research-capability",
                "status": "ok",
                "ok": True,
                "request_id": "req-1",
                "improvement_candidates_path": candidates_path.as_posix(),
            }
        ),
    )

    code, report = prepare_research_followups(
        root=tmp_path.as_posix(),
        report_path=report_path.as_posix(),
        output_root=(tmp_path / "prepared").as_posix(),
        max_promotions=1,
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "prepare-research-followups"
    assert report["status"] == "ok"
    assert report["source_request_id"] == "req-1"
    assert report["source_question_id"] == "q-1"
    assert report["source_question_origin"] == "user"
    assert len(report["selected_candidates"]) == 1
    assert report["selected_candidates"][0]["candidate_id"] == "cand-01"
    assert report["selected_candidates"][0]["selection_status"] == "selected_for_followup"
    assert report["selected_candidates"][0]["gate_evaluation"]["promotable"] is True
    assert len(report["deferred_candidates"]) == 2
    assert report["selection_summary"]["selected_count"] == 1
    assert report["selection_summary"]["deferred_count"] == 2
    assert report["selection_summary"]["selection_status_counts"]["deferred_promotion_cap"] == 1
    assert report["selection_summary"]["selection_status_counts"]["failed_gate"] == 1
    assert report["follow_up_questions"][0]["origin"] == "researcher"

    artifact_path = Path(report["draft_followups_path"])
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["source_request_id"] == "req-1"
    assert payload["selection_summary"]["selection_status_counts"]["selected_for_followup"] == 1
    assert payload["draft_followup_inputs"][0]["source_candidate_id"] == "cand-01"
    assert payload["draft_followup_inputs"][0]["delivery_mode"] == "governed_execplan"
    assert payload["draft_followup_inputs"][0]["suggested_execplan_seed"]["initiative_branch"] == "initiative/research-control-plane"

    deferred_by_id = {item["candidate_id"]: item for item in payload["deferred_candidates"]}
    assert deferred_by_id["cand-03"]["selection_status"] == "deferred_promotion_cap"
    assert deferred_by_id["cand-03"]["gate_evaluation"]["promotable"] is True
    assert deferred_by_id["cand-02"]["selection_status"] == "failed_gate"
    assert "disposition_ok" in deferred_by_id["cand-02"]["gate_evaluation"]["failure_reasons"]
