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
    _write_text(root / "docs" / "games" / "README.md", "# Games\n")
    edges = [
        {"from": "game-platform", "to": "game-execplan", "relation": "contains"},
        {"from": "game-execplan", "to": "game-planning", "relation": "contains"},
        {"from": "game-execplan", "to": "game-implementation", "relation": "contains"},
        {"from": "game-planning", "to": "game-planning-proof", "relation": "terminates_in"},
        {
            "from": "game-implementation",
            "to": "game-implementation-proof",
            "relation": "terminates_in",
        },
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
                {"id": "game-platform", "type": "game", "label": "Platform Game", "title": "Platform Game"},
                {"id": "game-execplan", "type": "game", "label": "ExecPlan Game", "title": "ExecPlan Game"},
                {"id": "game-planning", "type": "game", "label": "Planning Game", "title": "Planning Game"},
                {
                    "id": "game-implementation",
                    "type": "game",
                    "label": "Implementation Game",
                    "title": "Implementation Game",
                },
                {
                    "id": "game-planning-proof",
                    "type": "game",
                    "label": "Planning Merge Readiness",
                    "title": "Planning Merge Readiness",
                },
                {
                    "id": "game-implementation-proof",
                    "type": "game",
                    "label": "Implementation Merge Readiness",
                    "title": "Implementation Merge Readiness",
                },
                {
                    "id": "artifact-games-readme",
                    "type": "artifact",
                    "label": "Games README",
                    "title": "docs/games/README.md",
                },
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
