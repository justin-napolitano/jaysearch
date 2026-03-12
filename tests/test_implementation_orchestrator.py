from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.implementation_orchestrator import run_implementation_orchestrator
from platform_tools.planner_runtime import load_graph


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_execplan(root: Path, branch: str) -> Path:
    path = root / ".agent" / "execplans" / "20260311-implementation-orchestrator-runtime-codex-01-execplan.md"
    _write_text(
        path,
        "\n".join(
            [
                "---",
                'id: "20260311-implementation-orchestrator-runtime-codex-01-execplan"',
                'title: "Implementation Orchestrator Runtime"',
                'owner: "agent/codex-01"',
                'created: "2026-03-11T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - src/platform_tools/implementation_orchestrator.py",
                "  - bin/implementation-orchestrator",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                f'draft_branch: "{branch}"',
                'draft_created: "2026-03-11T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "validation:",
                "  tests:",
                '    - name: "execplan-validate"',
                '      command: "bin/execplan-validate .agent/execplans/20260311-implementation-orchestrator-runtime-codex-01-execplan.md"',
                '      expected_exit: 0',
                '    - name: "implementation-orchestrator-smoke-test"',
                '      command: "bin/implementation-orchestrator-smoke-test"',
                '      expected_exit: 0',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    return path


def _seed_remaining_work(root: Path, branch: str) -> None:
    _write_json(
        root / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "graph_id": "remaining-work-graph-20260311",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {
                    "node_id": "rwg-002",
                    "title": "Composite orchestrator status command",
                    "status": "completed",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["orchestrator-status", "merge-readiness"],
                    "target_execplan_id": "20260311-composite-orchestrator-status-codex-01-execplan",
                    "goal_area": "orchestrator-status",
                    "implementation_branch": "impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311",
                },
                {
                    "node_id": "rwg-003",
                    "title": "Game graph validator",
                    "status": "completed",
                    "gating_class": "auto_runnable",
                    "target_execplan_id": "20260311-game-graph-validator-and-status-codex-01-execplan",
                    "goal_area": "game-graph",
                },
                {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "ready",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["planner-cli", "orchestrator-status", "merge-readiness"],
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "goal_area": "implementation-orchestrator",
                    "expected_artifacts": ["src/platform_tools/implementation_orchestrator.py", "bin/implementation-orchestrator"],
                    "implementation_branch": branch,
                },
            ],
            "edges": [
                {"from": "rwg-004", "to": "rwg-002", "relation": "depends_on"},
                {"from": "rwg-004", "to": "rwg-003", "relation": "depends_on"},
            ],
        },
    )


def _seed_graph(root: Path) -> str:
    graph_id = "impl-runtime-graph"
    _write_json(
        root / "artifacts" / "planner" / "graphs" / f"{graph_id}.json",
        {
            "graph_id": graph_id,
            "created_at": "2026-03-11T00:00:00Z",
            "updated_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {
                    "node_id": "task-1",
                    "node_type": "task",
                    "title": "Implement orchestrator runtime",
                    "summary": "Implement runtime",
                    "status": "ready",
                    "priority": "P1",
                    "owner": "agent/codex-01",
                    "created_at": "2026-03-11T00:00:00Z",
                    "updated_at": "2026-03-11T00:00:00Z",
                    "description": "Implement runtime",
                    "ready_definition": "Dependencies complete",
                    "done_definition": "Runtime merged",
                    "changes": ["src/platform_tools/implementation_orchestrator.py"],
                    "provenance": {"source_session": "ps-1", "source_artifact": "extracted-state.json", "recorded_at": "2026-03-11T00:00:00Z", "commit_refs": []},
                    "evidence_refs": [],
                    "external_refs": [],
                }
            ],
            "edges": [],
        },
    )
    return graph_id


def _seed_transition_spec(root: Path) -> None:
    _write_text(
        root / "spec" / "game-transitions.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-11",
                "phases:",
                "  - planner",
                "  - implementation",
                "shared_statuses:",
                "  - ready",
                "  - in_progress",
                "  - in_review",
                "moves:",
                "  implementation:",
                "    select:",
                "      allowed_from:",
                "        - ready",
                "      allowed_to:",
                "        - in_progress",
                "      referee_required: false",
                "      required_evidence:",
                "        - selection_ref",
                "    implement:",
                "      allowed_from:",
                "        - in_progress",
                "      allowed_to:",
                "        - in_progress",
                "        - in_review",
                "      referee_required: false",
                "      required_evidence:",
                "        - commit_ref",
            ]
        )
        + "\n",
    )


def _stub_governed_checks(monkeypatch, execplan_path: Path, branch: str) -> None:
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": branch,
                "blockers": [],
                "active_execplan": {
                    "id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "path": execplan_path.as_posix(),
                },
                "active_game": {"id": "game-implementation", "lineage": ["game-platform", "game-execplan", "game-implementation"]},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.check_merge_readiness",
        lambda **kwargs: (
            0,
            {
                "readiness": True,
                "failing_checks": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "errors": [],
                "active_node": {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "ready",
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "implementation_branch": branch,
                    "eligible_now": True,
                    "action_state": {"action_required": False},
                },
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_orchestrator_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "next_actions": [{"action": "continue_active_slice"}],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_human_operations_status",
        lambda **kwargs: (
            0,
            {
                "status": "ok",
                "next_actions": [],
            },
        ),
    )


def test_implementation_orchestrator_inspect_reports_next_move(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260311-implementation-orchestrator-runtime-codex-01-execplan-codex-01-20260311"
    execplan_path = _seed_execplan(tmp_path, branch)
    _seed_remaining_work(tmp_path, branch)
    graph_id = _seed_graph(tmp_path)
    _seed_transition_spec(tmp_path)
    _stub_governed_checks(monkeypatch, execplan_path, branch)

    code, report = run_implementation_orchestrator(
        root=tmp_path.as_posix(),
        action="inspect",
        graph_id=graph_id,
        execplan_path=execplan_path.as_posix(),
        branch=branch,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["active_slice"]["eligible_now"] is True
    assert report["selected_node"]["node_id"] == "task-1"
    assert report["next_actions"][0]["action"] == "select"


def test_implementation_orchestrator_select_and_implement_apply_moves(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260311-implementation-orchestrator-runtime-codex-01-execplan-codex-01-20260311"
    execplan_path = _seed_execplan(tmp_path, branch)
    _seed_remaining_work(tmp_path, branch)
    graph_id = _seed_graph(tmp_path)
    _seed_transition_spec(tmp_path)
    _stub_governed_checks(monkeypatch, execplan_path, branch)

    select_code, select_report = run_implementation_orchestrator(
        root=tmp_path.as_posix(),
        action="select",
        graph_id=graph_id,
        execplan_path=execplan_path.as_posix(),
        branch=branch,
    )

    assert select_code == 0
    assert select_report["graph_move_result"]["target_status"] == "in_progress"

    implement_code, implement_report = run_implementation_orchestrator(
        root=tmp_path.as_posix(),
        action="implement",
        graph_id=graph_id,
        node_id="task-1",
        execplan_path=execplan_path.as_posix(),
        branch=branch,
        commit_ref="abc1234",
    )

    assert implement_code == 0
    assert implement_report["graph_move_result"]["target_status"] == "in_review"
    graph = load_graph(root=tmp_path.as_posix(), graph_id=graph_id)
    assert graph["nodes"][0]["status"] == "in_review"
    assert graph["nodes"][0]["last_move"]["move"] == "implement"


def test_implementation_orchestrator_blocks_when_game_is_not_implementation(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260311-implementation-orchestrator-runtime-codex-01-execplan-codex-01-20260311"
    execplan_path = _seed_execplan(tmp_path, branch)
    _seed_remaining_work(tmp_path, branch)
    graph_id = _seed_graph(tmp_path)
    _seed_transition_spec(tmp_path)
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_game_status",
        lambda **kwargs: (
            0,
            {
                "branch": branch,
                "blockers": [],
                "active_execplan": {
                    "id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "path": execplan_path.as_posix(),
                },
                "active_game": {"id": "game-platform", "lineage": ["game-platform"]},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.check_merge_readiness",
        lambda **kwargs: (0, {"readiness": True, "failing_checks": []}),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "errors": [],
                "active_node": {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "ready",
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "implementation_branch": branch,
                    "eligible_now": True,
                    "action_state": {"action_required": False},
                },
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_orchestrator_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": []}),
    )
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.get_human_operations_status",
        lambda **kwargs: (0, {"status": "ok", "next_actions": []}),
    )

    code, report = run_implementation_orchestrator(
        root=tmp_path.as_posix(),
        action="inspect",
        graph_id=graph_id,
        execplan_path=execplan_path.as_posix(),
        branch=branch,
    )

    assert code == 1
    assert "active_game_mismatch:game-platform" in report["blockers"]


def test_implementation_orchestrator_blocks_when_active_slice_requires_graph_action(monkeypatch, tmp_path: Path) -> None:
    branch = "impl-execplan/20260311-implementation-orchestrator-runtime-codex-01-execplan-codex-01-20260311"
    execplan_path = _seed_execplan(tmp_path, branch)
    _seed_remaining_work(tmp_path, branch)
    graph_id = _seed_graph(tmp_path)
    _seed_transition_spec(tmp_path)
    _stub_governed_checks(monkeypatch, execplan_path, branch)
    monkeypatch.setattr(
        "platform_tools.implementation_orchestrator.check_remaining_work_graph",
        lambda **kwargs: (
            0,
            {
                "ok": True,
                "errors": [],
                "active_node": {
                    "node_id": "rwg-004",
                    "title": "Implementation orchestrator runtime",
                    "status": "ready",
                    "target_execplan_id": "20260311-implementation-orchestrator-runtime-codex-01-execplan",
                    "implementation_branch": branch,
                    "eligible_now": True,
                    "action_state": {"action_required": True},
                },
            },
        ),
    )

    code, report = run_implementation_orchestrator(
        root=tmp_path.as_posix(),
        action="inspect",
        graph_id=graph_id,
        execplan_path=execplan_path.as_posix(),
        branch=branch,
    )

    assert code == 1
    assert "active_slice_requires_graph_action:rwg-004" in report["blockers"]
