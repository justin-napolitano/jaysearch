from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.game_graph_check import check_game_graph


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_repo(root: Path, *, include_handoff: bool = True) -> None:
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
                "    - subgame_local",
                "game_graph:",
                "  required_game_ids:",
                "    - game-platform",
                "    - game-execplan",
                "    - game-planning",
                "    - game-implementation",
                "    - game-policy-compliance",
                "    - game-commit-structure",
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
                "    - from: game-implementation",
                "      to: game-policy-compliance",
                "      relation: contains",
                "    - from: game-policy-compliance",
                "      to: game-commit-structure",
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
    _write_text(root / "docs" / "games" / "README.md", "# Games\n")
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
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/policy-compliance-game.yaml": "\n".join(
            [
                "game_id: game-policy-compliance",
                "type: policy_compliance",
                "title: Policy Compliance Game",
                "layer: assurance",
                "rule_scope: domain_game",
                "parent_game: game-implementation",
                "objective: prove legality",
                "board: board",
                "players: [implementer]",
                "referees: [bin/policy-compliance-check]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [latest_main_branching, clean_merge_state]",
                "win_condition: ok",
                "loss_condition: bad",
            ]
        ),
        "spec/games/commit-structure-game.yaml": "\n".join(
            [
                "game_id: game-commit-structure",
                "type: policy_compliance",
                "title: Commit Structure Game",
                "layer: assurance",
                "rule_scope: subgame_local",
                "parent_game: game-policy-compliance",
                "objective: prove commit legality",
                "board: board",
                "players: [implementer]",
                "referees: [bin/policy-compliance-check]",
                "referee_order: [global_board_law, active_domain_game, active_subgame]",
                "local_rule_focus: [procedural_commit_order, human_sized_commits]",
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
    edges = [
        {"from": "game-platform", "to": "game-execplan", "relation": "contains"},
        {"from": "game-execplan", "to": "game-planning", "relation": "contains"},
        {"from": "game-execplan", "to": "game-implementation", "relation": "contains"},
        {"from": "game-implementation", "to": "game-policy-compliance", "relation": "contains"},
        {"from": "game-policy-compliance", "to": "game-commit-structure", "relation": "contains"},
        {"from": "game-planning", "to": "game-planning-proof", "relation": "terminates_in"},
        {"from": "game-implementation", "to": "game-implementation-proof", "relation": "terminates_in"},
        {"from": "game-platform", "to": "artifact-games-readme", "relation": "documented_in"},
    ]
    if include_handoff:
        edges.append({"from": "game-planning", "to": "game-implementation", "relation": "hands_off_to"})
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
                {"id": "game-policy-compliance", "type": "game", "label": "Policy Compliance Game", "title": "Policy Compliance Game", "layer": "assurance", "scope": "domain_game", "spec_path": "spec/games/policy-compliance-game.yaml"},
                {"id": "game-commit-structure", "type": "game", "label": "Commit Structure Game", "title": "Commit Structure Game", "layer": "assurance", "scope": "subgame_local", "spec_path": "spec/games/commit-structure-game.yaml"},
                {"id": "game-planning-proof", "type": "game", "label": "Planning Merge Readiness", "title": "Planning Merge Readiness", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/planning-merge-readiness-game.yaml"},
                {"id": "game-implementation-proof", "type": "game", "label": "Implementation Merge Readiness", "title": "Implementation Merge Readiness", "layer": "assurance", "scope": "proof_game", "spec_path": "spec/games/implementation-merge-readiness-game.yaml"},
                {"id": "artifact-games-readme", "type": "artifact", "label": "Games README", "title": "docs/games/README.md"},
            ],
            "edges": edges,
        },
    )


def test_game_graph_check_passes_for_valid_graph(tmp_path: Path) -> None:
    _seed_repo(tmp_path)
    code, report = check_game_graph(tmp_path.as_posix())
    assert code == 0
    assert report["ok"] is True
    assert report["error_count"] == 0


def test_game_graph_check_fails_when_required_handoff_edge_is_missing(tmp_path: Path) -> None:
    _seed_repo(tmp_path, include_handoff=False)
    code, report = check_game_graph(tmp_path.as_posix())
    assert code == 1
    assert report["ok"] is False
    assert "missing_required_edge:game-planning:game-implementation:hands_off_to" in report["errors"]
