from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.run_jaysearch_question_dag_demo import (  # noqa: E402
    run_jaysearch_question_dag_demo,
)


def test_question_dag_demo_emits_lineage_and_execution_units(tmp_path: Path) -> None:
    code, report = run_jaysearch_question_dag_demo(
        root=tmp_path.as_posix(),
        question="How should we build the candidate generation boundary?",
        topic="candidate generation",
    )

    assert code == 0
    assert report["ok"] is True
    assert report["selected_candidate_id"] == "balanced_question_dag"
    assert set(report["rejected_candidate_ids"]) == {
        "over_split_question_dag",
        "cyclic_question_dag",
    }
    assert report["question_ref"].endswith("question.packet.json")
    assert report["evidence_ref"].endswith("evidence.packet.json")
    assert report["research_problem_ref"].endswith("research-problem.packet.json")
    assert report["question_research_transform_ref"].endswith(
        "question-to-research-problem-transform.packet.json"
    )
    assert report["candidate_dag_manifest_ref"]
    assert report["candidate_dag_selection_ref"]
    assert report["selected_dag_ref"]
    assert report["dag_execution_unit_manifest_ref"]
    assert len(report["execution_unit_refs"]) == 4
    assert [step["step"] for step in report["step_reports"]] == [
        "orchestrate_question_research_handoff",
        "select_candidate_dag",
        "materialize_selected_dag_execution_units",
    ]
    assert "Autonomous candidate generation" in report["implementation_boundary"]

    summary = Path(report["demo_summary_path"]).read_text(encoding="utf-8")
    assert "Question To DAG Demo Summary" in summary
    html = Path(report["demo_html_path"]).read_text(encoding="utf-8")
    assert "Jaysearch Question To DAG Demo" in html

    question_packet = json.loads(Path(report["question_ref"]).read_text(encoding="utf-8"))
    assert question_packet["packet_type"] == "research_question_packet"
    evidence_packet = json.loads(Path(report["evidence_ref"]).read_text(encoding="utf-8"))
    assert evidence_packet["packet_type"] == "evidence_packet"
    assert evidence_packet["evidence_mode"] == "curated_fixture"


def test_question_dag_demo_blocks_missing_question(tmp_path: Path) -> None:
    code, report = run_jaysearch_question_dag_demo(root=tmp_path.as_posix(), question=" ")

    assert code == 1
    assert report["status"] == "blocked"
    assert "question_missing" in report["blockers"]
    assert report["execution_unit_refs"] == []
