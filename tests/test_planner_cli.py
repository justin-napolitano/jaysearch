from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools import planner_cli, planner_runtime
from platform_tools.planner_runtime import (
    apply_move,
    build_graph,
    create_session,
    draft_execplan,
    import_execplan,
    load_session,
    summarize_session,
    validate_all,
    validate_graph,
    validate_move,
)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_cli_report(captured: str) -> dict[str, Any]:
    lines = [line for line in captured.splitlines() if line.strip()]
    return json.loads("\n".join(lines))


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
    _write_text(root / "docs" / "references.md", "# References\n\nhttps://example.com/source\n")
    _write_text(
        root / "docs" / "research-assumptions.md",
        "source-backed\ndesign-inference\npolicy-choice\nopen-assumption\n",
    )
    _write_text(
        root / "spec" / "bibliography-graph.schema.yaml",
        "version: v1\ngraph:\n  required_fields:\n    - graph_id\n    - created_at\n    - nodes\n    - edges\n",
    )
    _write_text(
        root / "spec" / "planner-contract-import.yaml",
        "\n".join(
            [
                "version: v1",
                "report:",
                "  required_fields:",
                "    - report_id",
                "    - session_id",
                "    - graph_id",
                "    - execplan_id",
                "    - source_execplan_path",
                "    - original_projection_hash",
                "    - edited_execplan_hash",
                "    - created_at",
                "    - status",
                "    - accepted_changes",
                "    - rejected_changes",
                "    - unresolved_changes",
                "    - canonical_updates",
                "    - authority",
                "    - operator_notes",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "game-transitions.yaml",
        "\n".join(
            [
                "version: v1",
                "shared_statuses:",
                "  - draft",
                "  - ready",
                "  - blocked",
                "  - in_progress",
                "  - in_review",
                "  - validated",
                "  - recovery_required",
                "  - done",
                "  - rejected",
                "  - archived",
                "moves:",
                "  planner:",
                "    refine:",
                "      allowed_from:",
                "        - draft",
                "        - blocked",
                "      allowed_to:",
                "        - draft",
                "        - ready",
                "      referee_required: false",
                "      required_evidence:",
                "        - change_summary",
                "    commit:",
                "      allowed_from:",
                "        - validated",
                "      allowed_to:",
                "        - in_review",
                "      referee_required: true",
                "      required_evidence:",
                "        - readiness_report",
            ]
        )
        + "\n",
    )
    _write_text(
        root / "spec" / "task-graph.schema.yaml",
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
    )
    _write_text(root / "examples" / "execplan-template.md", "template\n")


def test_session_start_and_show(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="Planner Runtime", objective="Build it")
    session_id = started["session_id"]
    loaded = load_session(root=tmp_path.as_posix(), session_id=session_id)
    summary = summarize_session(root=tmp_path.as_posix(), session_id=session_id)
    assert loaded["session"]["title"] == "Planner Runtime"
    assert summary["session_id"] == session_id
    assert summary["counts"]["goals"] == 0


def test_graph_build_validate_and_move_apply(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="Graph Test")
    session_id = started["session_id"]
    session_dir = tmp_path / "artifacts" / "planner" / "sessions" / session_id
    extracted = {
        "goals": [{"title": "Build planner", "success_criteria": "Works", "scope": "runtime", "status": "validated"}],
        "constraints": [{"constraint": "No UI", "constraint_type": "platform", "title": "No UI"}],
        "assumptions": [],
        "decisions": [],
        "questions": [],
        "tasks": [
            {
                "title": "Add CLI",
                "description": "Add CLI",
                "ready_definition": "",
                "done_definition": "",
                "status": "draft",
                "changes": ["src/platform_tools/planner_cli.py"],
            }
        ],
        "risks": [],
        "evidence": [{"title": "CLI evidence", "artifact_type": "note", "path": "docs/references.md"}],
    }
    _write_json(session_dir / "extracted-state.json", extracted)
    built = build_graph(root=tmp_path.as_posix(), session_id=session_id)
    code, report = validate_graph(root=tmp_path.as_posix(), graph_id=built["graph_id"])
    assert code == 0
    move_code, move_report = validate_move(
        root=tmp_path.as_posix(),
        graph_id=built["graph_id"],
        node_id="task-1",
        phase="planner",
        move="refine",
        target_status="ready",
        evidence={"change_summary": "clarified task"},
    )
    assert move_code == 0
    apply_code, _ = apply_move(
        root=tmp_path.as_posix(),
        graph_id=built["graph_id"],
        node_id="task-1",
        phase="planner",
        move="refine",
        target_status="ready",
        evidence={"change_summary": "clarified task"},
    )
    assert apply_code == 0
    illegal_code, illegal_report = validate_move(
        root=tmp_path.as_posix(),
        graph_id=built["graph_id"],
        node_id="task-1",
        phase="planner",
        move="commit",
        target_status="in_review",
        evidence={},
    )
    assert illegal_code == 1
    assert illegal_report["errors"]


def test_contract_draft_and_import(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="Contract Test")
    session_id = started["session_id"]
    session_dir = tmp_path / "artifacts" / "planner" / "sessions" / session_id
    extracted = {
        "goals": [{"title": "Build contract", "success_criteria": "draft", "scope": "runtime", "status": "validated"}],
        "constraints": [],
        "assumptions": [],
        "decisions": [],
        "questions": [],
        "tasks": [
            {
                "title": "Generate plan",
                "description": "Generate plan",
                "ready_definition": "",
                "done_definition": "",
                "status": "ready",
                "changes": ["src/platform_tools/planner_runtime.py"],
            }
        ],
        "risks": [],
        "evidence": [{"title": "Artifact", "artifact_type": "file", "path": "src/platform_tools/planner_runtime.py"}],
    }
    _write_json(session_dir / "extracted-state.json", extracted)
    built = build_graph(root=tmp_path.as_posix(), session_id=session_id)
    planner_runtime.get_current_branch = lambda **kwargs: "initiative/example"
    draft_code, draft_report = draft_execplan(
        root=tmp_path.as_posix(), graph_id=built["graph_id"], title="Generated Contract"
    )
    assert draft_code == 0
    original = Path(draft_report["path"])
    generated = original.read_text(encoding="utf-8")
    assert "initiative_branch: initiative/example" in generated
    assert "base_branch: initiative/example" in generated
    assert "## Outcomes & Retrospective" in generated
    assert "# Purpose / Big Picture" not in generated
    assert "## Concrete Steps" not in generated
    assert "draft_branch:" not in generated
    edited = original.with_name("edited.md")
    edited.write_text(generated + "\nEdited\n", encoding="utf-8")
    import_code, import_report = import_execplan(
        root=tmp_path.as_posix(),
        session_id=session_id,
        graph_id=built["graph_id"],
        execplan_id=draft_report["execplan_id"],
        original_path=str(original.relative_to(tmp_path)),
        edited_path=str(edited.relative_to(tmp_path)),
        operator="operator/test",
        referee="referee/test",
    )
    assert import_code == 1
    assert Path(import_report["report_path"]).exists()


def test_validate_all_checks_research_artifacts(tmp_path: Path) -> None:
    _seed_runtime_specs(tmp_path)
    code, report = validate_all(root=tmp_path.as_posix())
    assert code == 0
    assert report["research"]["ok"] is True


def test_planner_cli_execplan_contract_command_projects_execplan(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="CLI ExecPlan")
    session_id = started["session_id"]
    session_dir = tmp_path / "artifacts" / "planner" / "sessions" / session_id
    _write_json(
        session_dir / "extracted-state.json",
        {
            "goals": [{"title": "Project execplan", "success_criteria": "created", "scope": "cli", "status": "validated"}],
            "constraints": [],
            "assumptions": [],
            "decisions": [],
            "questions": [],
            "tasks": [
                {
                    "title": "Generate plan",
                    "description": "Generate plan",
                    "ready_definition": "",
                    "done_definition": "",
                    "status": "ready",
                    "changes": ["src/platform_tools/planner_cli.py"],
                }
            ],
            "risks": [],
            "evidence": [{"title": "Planner CLI", "artifact_type": "file", "path": "src/platform_tools/planner_cli.py"}],
        },
    )
    built = build_graph(root=tmp_path.as_posix(), session_id=session_id)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(planner_runtime, "get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        sys,
        "argv",
        ["planner_cli.py", "contract", "execplan", "--graph-id", built["graph_id"], "--title", "Generated Contract"],
    )
    exit_code = planner_cli.main()
    report = _read_cli_report(capsys.readouterr().out)

    assert exit_code == 0
    assert report["operation"] == "contract.execplan"
    assert report["status"] == "ok"
    assert report["next_validations"] == [f"bin/execplan-validate {report['path']}"]
    assert report["ok"] is True


def test_planner_cli_wraps_graph_validation_in_orchestrator_contract(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _seed_runtime_specs(tmp_path)
    started = create_session(root=tmp_path.as_posix(), title="CLI Contract")
    session_id = started["session_id"]
    session_dir = tmp_path / "artifacts" / "planner" / "sessions" / session_id
    _write_json(
        session_dir / "extracted-state.json",
        {
            "goals": [{"title": "Validate graph", "success_criteria": "valid", "scope": "cli", "status": "validated"}],
            "constraints": [],
            "assumptions": [],
            "decisions": [],
            "questions": [],
            "tasks": [],
            "risks": [],
            "evidence": [],
        },
    )
    built = build_graph(root=tmp_path.as_posix(), session_id=session_id)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["planner_cli.py", "graph", "validate", "--graph-id", built["graph_id"]],
    )
    exit_code = planner_cli.main()
    report = _read_cli_report(capsys.readouterr().out)

    assert exit_code == 0
    assert report["command"] == "planner"
    assert report["operation"] == "graph.validate"
    assert report["status"] == "ok"
    assert report["blockers"] == []
    assert report["graph_id"] == built["graph_id"]
    assert report["next_validations"] == []
    assert report["ok"] is True


def test_planner_cli_reports_machine_readable_precondition_failures(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _seed_runtime_specs(tmp_path)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["planner_cli.py", "graph", "validate", "--graph-id", "missing-graph"],
    )
    exit_code = planner_cli.main()
    report = _read_cli_report(capsys.readouterr().out)

    assert exit_code == 1
    assert report["command"] == "planner"
    assert report["operation"] == "graph.validate"
    assert report["status"] == "blocked"
    assert report["blockers"]
    assert report["ok"] is False
