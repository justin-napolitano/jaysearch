from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.run_research_capability import run_research_capability


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_researcher_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "researcher-harness"
    _write(repo / "pyproject.toml", "[project]\nname='researcher-harness'\n")
    _write(repo / "src" / "researcher_harness" / "cli.py", "print('placeholder')\n")
    return repo


def test_run_research_capability_blocks_on_missing_roots(tmp_path: Path) -> None:
    code, report = run_research_capability(
        root=tmp_path.as_posix(),
        researcher_root=(tmp_path / "missing").as_posix(),
        request_path=(tmp_path / "missing.json").as_posix(),
    )

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert report["command"] == "run-research-capability"
    assert report["status"] == "blocked"
    assert "researcher_root_missing" in report["blockers"]
    assert "request_path_missing" in report["blockers"]


def test_run_research_capability_blocks_on_invalid_request(tmp_path: Path) -> None:
    researcher_repo = _make_researcher_repo(tmp_path)
    request_path = tmp_path / "request.json"
    _write(request_path, json.dumps({"request_id": "req-1"}))

    code, report = run_research_capability(
        root=tmp_path.as_posix(),
        researcher_root=researcher_repo.as_posix(),
        request_path=request_path.as_posix(),
    )

    assert code == 1
    assert report["status"] == "blocked"
    assert "request_missing_question_id" in report["blockers"]
    assert "request_missing_study_design" in report["blockers"]


def test_run_research_capability_executes_and_projects_response(monkeypatch, tmp_path: Path) -> None:
    researcher_repo = _make_researcher_repo(tmp_path)
    request_path = tmp_path / "request.json"
    _write(
        request_path,
        json.dumps(
            {
                "request_id": "req-1",
                "question_id": "q-1",
                "topic": "Example topic",
                "study_design": "option-comparison",
                "artifact_contract": "v1",
                "output_root": str(tmp_path / "output"),
            }
        ),
    )

    class Completed:
        returncode = 0
        stdout = json.dumps(
            {
                "request_id": "req-1",
                "status": "completed",
                "output_root": str(tmp_path / "output"),
                "artifact_paths": {
                    "summary": str(tmp_path / "output" / "execution" / "summaries" / "req-1.json"),
                    "evidence": str(tmp_path / "output" / "evidence" / "req-1.md"),
                },
                "recommendation": "opt-1",
                "self_review_path": str(tmp_path / "output" / "execution" / "self_review" / "req-1.md"),
                "warnings": [],
            }
        )
        stderr = ""

    monkeypatch.setattr("platform_tools.run_research_capability.subprocess.run", lambda *args, **kwargs: Completed())

    code, report = run_research_capability(
        root=tmp_path.as_posix(),
        researcher_root=researcher_repo.as_posix(),
        request_path=request_path.as_posix(),
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["status"] == "ok"
    assert report["request_id"] == "req-1"
    assert report["research_status"] == "completed"
    assert report["recommendation"] == "opt-1"
    assert report["summary_path"].endswith("req-1.json")
