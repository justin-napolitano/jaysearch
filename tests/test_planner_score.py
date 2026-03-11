from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.planner_score import score_graph


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path) -> str:
    _write_text(root / "spec" / "scoring.yaml", Path("spec/scoring.yaml").read_text(encoding="utf-8"))
    graph_id = "pg-test"
    _write_json(
        root / "artifacts" / "planner" / "graphs" / f"{graph_id}.json",
        {
            "graph_id": graph_id,
            "session_id": "ps-test",
            "created_at": "2026-03-10T00:00:00Z",
            "updated_at": "2026-03-10T00:00:00Z",
            "nodes": [
                {
                    "node_id": "goal-1",
                    "node_type": "goal",
                    "title": "Goal",
                    "summary": "Goal",
                    "status": "validated",
                    "priority": "P1",
                    "owner": "agent/codex-01",
                    "created_at": "2026-03-10T00:00:00Z",
                    "updated_at": "2026-03-10T00:00:00Z",
                    "provenance": {
                        "source_session": "ps-test",
                        "source_artifact": "extracted-state.json",
                        "recorded_at": "2026-03-10T00:00:00Z",
                    },
                    "evidence_refs": [{"kind": "note"}],
                    "external_refs": [],
                    "success_criteria": "done",
                    "scope": "score",
                },
                {
                    "node_id": "task-1",
                    "node_type": "task",
                    "title": "Task",
                    "summary": "Task",
                    "status": "ready",
                    "priority": "P1",
                    "owner": "agent/codex-01",
                    "created_at": "2026-03-10T00:00:00Z",
                    "updated_at": "2026-03-10T00:00:00Z",
                    "provenance": {
                        "source_session": "ps-test",
                        "source_artifact": "extracted-state.json",
                        "recorded_at": "2026-03-10T00:00:00Z",
                    },
                    "evidence_refs": [{"kind": "note"}],
                    "external_refs": [],
                    "description": "Task",
                    "ready_definition": "",
                    "done_definition": "",
                    "changes": ["src/platform_tools/planner_score.py"],
                },
                {
                    "node_id": "validation-1",
                    "node_type": "validation",
                    "title": "Validation",
                    "summary": "Validation",
                    "status": "validated",
                    "priority": "P2",
                    "owner": "agent/codex-01",
                    "created_at": "2026-03-10T00:00:00Z",
                    "updated_at": "2026-03-10T00:00:00Z",
                    "provenance": {
                        "source_session": "ps-test",
                        "source_artifact": "extracted-state.json",
                        "recorded_at": "2026-03-10T00:00:00Z",
                    },
                    "evidence_refs": [{"kind": "note"}],
                    "external_refs": [],
                    "validation_type": "check",
                    "command": "echo ok",
                    "expected_result": "ok",
                },
            ],
            "edges": [],
        },
    )
    return graph_id


def test_score_graph_emits_bounded_scores(tmp_path: Path) -> None:
    graph_id = _seed_repo(tmp_path)
    report = score_graph(root=tmp_path.as_posix(), graph_id=graph_id)
    assert report["command"] == "planner-score"
    assert report["status"] == "ok"
    assert report["blockers"] == []
    assert report["next_validations"] == []
    assert 0 <= report["planner_game"]["score"] <= 100
    assert 0 <= report["implementation_game"]["score"] <= 100
    assert "TLS" in report["planner_game"]["metrics"]
    assert "VPR" in report["implementation_game"]["metrics"]
