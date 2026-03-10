from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.planner_runtime import (
    build_graph,
    create_session,
    load_session,
    summarize_session,
    validate_all,
    validate_graph,
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seed_runtime_specs(root: Path) -> None:
    (root / "spec").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    _write_json(
        root / "artifacts" / "planner" / "research" / "bibliography-graph.json",
        {
            "graph_id": "g1",
            "created_at": "2026-03-10T00:00:00Z",
            "nodes": [
                {
                    "id": "src-1",
                    "type": "source",
                    "label": "Source",
                    "title": "Source",
                    "link": "https://example.com/source",
                }
            ],
            "edges": [],
        },
    )
    (root / "docs" / "references.md").write_text(
        "# References\n\nhttps://example.com/source\n", encoding="utf-8"
    )
    (root / "docs" / "research-assumptions.md").write_text(
        "source-backed\ndesign-inference\npolicy-choice\nopen-assumption\n",
        encoding="utf-8",
    )
    (root / "spec" / "bibliography-graph.schema.yaml").write_text(
        "version: v1\ngraph:\n  required_fields:\n    - graph_id\n    - created_at\n    - nodes\n    - edges\n",
        encoding="utf-8",
    )
    (root / "spec" / "game-transitions.yaml").write_text(
        "version: v1\nshared_statuses:\n  - draft\n  - ready\n  - blocked\n  - in_progress\n  - in_review\n  - validated\n  - recovery_required\n  - done\n  - rejected\n  - archived\n",
        encoding="utf-8",
    )
    (root / "spec" / "task-graph.schema.yaml").write_text(
        "\n".join(
            [
                "version: v1",
                "graph:",
                "  required_fields:",
                "    - graph_id",
                "    - session_id",
                "    - created_at",
                "    - updated_at",
                "    - nodes",
                "    - edges",
                "node:",
                "  required_fields:",
                "    - node_id",
                "    - node_type",
                "    - title",
                "    - summary",
                "    - status",
                "    - priority",
                "    - owner",
                "    - created_at",
                "    - updated_at",
                "    - provenance",
                "    - evidence_refs",
                "    - external_refs",
                "  node_type_allowed:",
                "    - goal",
                "    - decision",
                "    - question",
                "    - constraint",
                "    - task",
                "    - validation",
                "    - artifact",
                "    - risk",
                "    - tool_run",
                "    - handoff",
                "  status_allowed:",
                "    - draft",
                "    - ready",
                "    - blocked",
                "    - in_progress",
                "    - in_review",
                "    - validated",
                "    - recovery_required",
                "    - done",
                "    - rejected",
                "    - archived",
                "  priority_allowed:",
                "    - P0",
                "    - P1",
                "    - P2",
                "    - P3",
                "typed_node_requirements:",
                "  goal:",
                "    required_fields:",
                "      - success_criteria",
                "      - scope",
                "  constraint:",
                "    required_fields:",
                "      - constraint",
                "      - constraint_type",
                "  task:",
                "    required_fields:",
                "      - description",
                "      - ready_definition",
                "      - done_definition",
                "  question:",
                "    required_fields:",
                "      - question",
                "      - blocking",
                "  decision:",
                "    required_fields:",
                "      - decision",
                "      - rationale",
                "      - alternatives_considered",
                "  risk:",
                "    required_fields:",
                "      - risk",
                "      - impact",
                "      - mitigation",
                "  artifact:",
                "    required_fields:",
                "      - artifact_type",
                "      - path",
                "  validation:",
                "    required_fields:",
                "      - validation_type",
                "      - command",
                "      - expected_result",
                "  tool_run:",
                "    required_fields:",
                "      - tool_name",
                "      - inputs",
                "      - expected_outputs",
                "  handoff:",
                "    required_fields:",
                "      - handoff_to",
                "      - entry_criteria",
                "      - exit_criteria",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_session_start_and_show(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="Planner Runtime", objective="Build it")
    session_id = started["session_id"]
    loaded = load_session(root=tmp_path.as_posix(), session_id=session_id)
    summary = summarize_session(root=tmp_path.as_posix(), session_id=session_id)
    assert loaded["session"]["title"] == "Planner Runtime"
    assert summary["session_id"] == session_id
    assert summary["counts"]["goals"] == 0


def test_graph_build_and_validate(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="Graph Test")
    session_id = started["session_id"]
    session_dir = tmp_path / "artifacts" / "planner" / "sessions" / session_id
    extracted = {
        "goals": [{"title": "Build planner", "success_criteria": "Works", "scope": "runtime"}],
        "constraints": [{"constraint": "No UI", "constraint_type": "platform", "title": "No UI"}],
        "assumptions": [],
        "decisions": [],
        "questions": [{"title": "How strict?", "question": "How strict?", "blocking": True}],
        "tasks": [{"title": "Add CLI", "description": "Add CLI", "ready_definition": "", "done_definition": ""}],
        "risks": [],
        "evidence": [],
    }
    _write_json(session_dir / "extracted-state.json", extracted)
    built = build_graph(root=tmp_path.as_posix(), session_id=session_id)
    code, report = validate_graph(root=tmp_path.as_posix(), graph_id=built["graph_id"])
    assert code == 0
    assert report["ok"] is True
    assert built["node_count"] == 4


def test_validate_all_checks_research_artifacts(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    code, report = validate_all(root=tmp_path.as_posix())
    assert code == 0
    assert report["research"]["ok"] is True
