from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.get_research_question_backlog import get_research_question_backlog
from platform_tools.intake_research_question import intake_research_question
from platform_tools.materialize_research_request_from_question import materialize_research_request_from_question


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_intake_research_question_writes_canonical_artifacts(tmp_path: Path) -> None:
    question_path = tmp_path / "question.json"
    _write(
        question_path,
        json.dumps(
            {
                "question_id": "platform-options",
                "title": "Platform option decision",
                "topic": "Choose between Fabric and ADF + Functions.",
                "question_origin": "user",
                "target_repos": ["codex_platform", "researcher-harness"],
                "domain_plugins": ["cloud-architecture"],
            }
        ),
    )

    code, report = intake_research_question(root=tmp_path.as_posix(), question_path=question_path.as_posix())

    assert code == 0
    assert report["command"] == "intake-research-question"
    artifact_path = Path(report["artifact_path"])
    backlog_path = Path(report["backlog_log_path"])
    assert artifact_path.exists()
    assert backlog_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["question_id"] == "platform-options"
    assert artifact["status"] == "queued"


def test_get_research_question_backlog_filters_results(tmp_path: Path) -> None:
    question_one = tmp_path / "q1.json"
    question_two = tmp_path / "q2.json"
    _write(
        question_one,
        json.dumps(
            {
                "question_id": "q-1",
                "title": "One",
                "topic": "Question one",
                "question_origin": "user",
                "target_repos": ["codex_platform"],
            }
        ),
    )
    _write(
        question_two,
        json.dumps(
            {
                "question_id": "q-2",
                "title": "Two",
                "topic": "Question two",
                "question_origin": "researcher",
                "status": "deferred",
                "target_repos": ["researcher-harness"],
            }
        ),
    )
    intake_research_question(root=tmp_path.as_posix(), question_path=question_one.as_posix())
    intake_research_question(root=tmp_path.as_posix(), question_path=question_two.as_posix())

    code, report = get_research_question_backlog(
        root=tmp_path.as_posix(),
        question_origin="researcher",
        status="deferred",
        target_repo="researcher-harness",
    )

    assert code == 0
    assert report["count"] == 1
    assert report["questions"][0]["question_id"] == "q-2"


def test_materialize_research_request_from_question(tmp_path: Path) -> None:
    artifact_path = tmp_path / "artifacts" / "governance" / "research-questions" / "platform-options.json"
    _write(
        artifact_path,
        json.dumps(
            {
                "question_id": "platform-options",
                "title": "Platform option decision",
                "topic": "Choose between Fabric and ADF + Functions.",
                "question_origin": "user",
                "study_design_hint": "option-comparison",
                "domain_plugins": ["cloud-architecture"],
                "improvement_targets": ["researcher-harness", "platform-control-plane"],
                "options": [
                    {"option_id": "fabric", "summary": "Fabric", "strengths": ["one"], "risks": ["one"], "score": 3},
                    {"option_id": "adf-functions", "summary": "ADF + Functions", "strengths": ["two"], "risks": ["two"], "score": 5},
                ],
            }
        ),
    )

    code, report = materialize_research_request_from_question(
        root=tmp_path.as_posix(),
        question_path=artifact_path.as_posix(),
        output_root=(tmp_path / "out").as_posix(),
    )

    assert code == 0
    request_path = Path(report["request_path"])
    assert request_path.exists()
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert payload["question_id"] == "platform-options"
    assert payload["study_design"] == "option-comparison"
    assert len(payload["options"]) == 2
