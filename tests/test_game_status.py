from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.game_status import get_game_status


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_branch_policy(root: Path) -> None:
    _write_text(
        root / "platform.engine.yaml",
        "\n".join(
            [
                "runtime:",
                "  mode: standalone",
                "  governance_source: ''",
                "  project_rules_source: project.rules.yaml",
            ]
        )
        + "\n",
    )
    _write_text(root / "spec" / "ruleset.yaml", "execution_constraints:\n  allowed_branch_patterns:\n    - draft-execplan/*\n")
    _write_text(
        root / "spec" / "workflow.yaml",
        "execution_requirements:\n  workflow_branch_patterns:\n    draft_execplan: draft-execplan/*\n  protected_branches_disallowed_for_execution:\n    - main\n",
    )
    _write_text(root / "spec" / "governance.yaml", "required_checks:\n  contract: []\n")
    _write_text(
        root / "spec" / "rule-layering.yaml",
        "project_overlay:\n  allowed_keys:\n    - required_check_names_add\n    - forbidden_branches_add\n    - allowed_branch_patterns_remove\n  forbidden_keys: []\n",
    )
    _write_text(root / "project.rules.yaml", "overlay: {}\n")


def _seed_game_graph(root: Path) -> None:
    _write_text(
        root / "spec" / "games.schema.yaml",
        "\n".join(
            [
                "version: v1",
                "graph:",
                "  required_fields:",
                "    - graph_id",
                "    - created_at",
                "    - nodes",
                "    - edges",
                "node:",
                "  required_fields:",
                "    - id",
                "    - type",
                "    - label",
                "    - title",
                "  type_allowed:",
                "    - game",
                "    - artifact",
                "edge:",
                "  required_fields:",
                "    - from",
                "    - to",
                "    - relation",
                "  relation_allowed:",
                "    - contains",
                "    - terminates_in",
                "    - hands_off_to",
                "    - links_to",
                "    - documented_in",
                "    - inherits",
                "game_node:",
                "  required_fields:",
                "    - layer",
                "    - scope",
                "    - spec_path",
                "  allowed_layers:",
                "    - platform",
                "    - authority",
                "    - work",
                "    - assurance",
                "  allowed_scopes:",
                "    - global_board_law",
                "    - domain_game",
                "    - proof_game",
                "game_graph:",
                "  required_game_ids:",
                "    - game-platform",
                "    - game-execplan",
                "    - game-planning",
                "    - game-implementation",
                "    - game-planning-proof",
                "    - game-implementation-proof",
                "  root_game_id: game-platform",
                "  required_edges:",
                "    - from: game-platform",
                "      to: game-execplan",
                "      relation: contains",
                "    - from: game-execplan",
                "      to: game-planning",
                "      relation: contains",
                "    - from: game-execplan",
                "      to: game-implementation",
                "      relation: contains",
                "    - from: game-planning",
                "      to: game-planning-proof",
                "      relation: terminates_in",
                "    - from: game-implementation",
                "      to: game-implementation-proof",
                "      relation: terminates_in",
                "    - from: game-planning",
                "      to: game-implementation",
                "      relation: hands_off_to",
            ]
        )
        + "\n",
    )
    for relative_path, body in {
        "spec/games/platform-game.yaml": "\n".join(
            [
                "game_id: game-platform",
                "type: platform",
                "title: Platform Game",
                "layer: platform",
                "rule_scope: global_board_law",
                "parent_game: null",
                "objective: root",
                "board: board",
                "players: [human_authority]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/execplan-game.yaml": "\n".join(
            [
                "game_id: game-execplan",
                "type: execplan",
                "title: ExecPlan Game",
                "layer: authority",
                "rule_scope: domain_game",
                "parent_game: game-platform",
                "objective: contract",
                "board: board",
                "players: [human_authority]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/planning-game.yaml": "\n".join(
            [
                "game_id: game-planning",
                "type: planning",
                "title: Planning Game",
                "layer: work",
                "rule_scope: domain_game",
                "parent_game: game-execplan",
                "objective: plan",
                "board: board",
                "players: [planner]",
                "referees: [bin/planner]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/implementation-game.yaml": "\n".join(
            [
                "game_id: game-implementation",
                "type: implementation",
                "title: Implementation Game",
                "layer: work",
                "rule_scope: domain_game",
                "parent_game: game-execplan",
                "objective: implement",
                "board: board",
                "players: [implementer]",
                "referees: [bin/run-local-ci]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [scoped_file_changes]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/planning-merge-readiness-game.yaml": "\n".join(
            [
                "game_id: game-planning-proof",
                "type: merge_readiness",
                "title: Planning Proof",
                "layer: assurance",
                "rule_scope: proof_game",
                "parent_game: game-planning",
                "objective: prove",
                "board: board",
                "players: [planner]",
                "referees: [bin/execplan-validate]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/implementation-merge-readiness-game.yaml": "\n".join(
            [
                "game_id: game-implementation-proof",
                "type: merge_readiness",
                "title: Implementation Proof",
                "layer: assurance",
                "rule_scope: proof_game",
                "parent_game: game-implementation",
                "objective: prove",
                "board: board",
                "players: [implementer]",
                "referees: [bin/run-local-ci]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
    }.items():
        _write_text(root / relative_path, body + "\n")
    _write_json(
        root / "artifacts" / "planner" / "research" / "game-graph.json",
        {
            "graph_id": "nested-game-system-test",
            "created_at": "2026-03-11T00:00:00Z",
            "nodes": [
                {"id": "game-platform", "type": "game", "label": "Platform Game", "title": "Platform Game", "layer": "platform", "scope": "global_board_law", "spec_path": "spec/games/platform-game.yaml"},
                {"id": "game-execplan", "type": "game", "label": "ExecPlan Game", "title": "ExecPlan Game", "layer": "authority", "scope": "domain_game", "spec_path": "spec/games/execplan-game.yaml"},
                {"id": "game-planning", "type": "game", "label": "Planning Game", "title": "Planning Game", "layer": "work", "scope": "domain_game", "spec_path": "spec/games/planning-game.yaml"},
                {"id": "game-implementation", "type": "game", "label": "Implementation Game", "title": "Implementation Game", "layer": "work", "scope": "domain_game", "spec_path": "spec/games/implementation-game.yaml"},
                {"id": "game-planning-proof", "type": "game", "label": "Planning Merge Readiness", "title": "Planning Merge Readiness", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/planning-merge-readiness-game.yaml"},
                {"id": "game-implementation-proof", "type": "game", "label": "Implementation Merge Readiness", "title": "Implementation Merge Readiness", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/implementation-merge-readiness-game.yaml"},
            ],
            "edges": [
                {"from": "game-platform", "to": "game-execplan", "relation": "contains"},
                {"from": "game-execplan", "to": "game-planning", "relation": "contains"},
                {"from": "game-execplan", "to": "game-implementation", "relation": "contains"},
                {"from": "game-planning", "to": "game-planning-proof", "relation": "terminates_in"},
                {"from": "game-implementation", "to": "game-implementation-proof", "relation": "terminates_in"},
                {"from": "game-planning", "to": "game-implementation", "relation": "hands_off_to"},
            ],
        },
    )


def _seed_execplan(root: Path, branch: str) -> Path:
    plan_path = root / ".agent" / "execplans" / "20260311-test-execplan.md"
    _write_text(
        plan_path,
        "\n".join(
            [
                "---",
                'id: "20260311-test-execplan"',
                'title: "Test ExecPlan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-11T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - src/platform_tools/game_status.py",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                f'draft_branch: "{branch}"',
                'draft_created: "2026-03-11T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    return plan_path


def test_game_status_reports_implementation_game_for_explicit_execplan(tmp_path: Path) -> None:
    branch = "draft-execplan/test-game-status"
    _seed_branch_policy(tmp_path)
    _seed_game_graph(tmp_path)
    plan_path = _seed_execplan(tmp_path, branch)
    code, report = get_game_status(
        root=tmp_path.as_posix(),
        branch=branch,
        execplan_path=plan_path.as_posix(),
    )
    assert code == 0
    assert report["ok"] is True
    assert report["active_game"]["id"] == "game-implementation"
    assert report["active_game"]["layer"] == "work"
    assert report["active_game"]["scope"] == "domain_game"
    assert report["active_game"]["lineage"] == [
        "game-platform",
        "game-execplan",
        "game-implementation",
    ]
    assert report["active_execplan"]["path"] == plan_path.as_posix()


def test_game_status_falls_back_to_execplan_game_on_draft_branch(tmp_path: Path) -> None:
    _seed_branch_policy(tmp_path)
    _seed_game_graph(tmp_path)
    code, report = get_game_status(
        root=tmp_path.as_posix(),
        branch="draft-execplan/no-explicit-plan",
    )
    assert code == 0
    assert report["ok"] is True
    assert report["active_game"]["id"] == "game-execplan"
    assert report["active_game"]["referee_order"] == [
        "global_board_law",
        "active_domain_game",
        "active_subgame",
    ]
    assert report["active_game"]["reason"] == "draft_execplan_branch_without_explicit_execplan"
