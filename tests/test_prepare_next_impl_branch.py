from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.mergeback_orchestration import API_VERSION, prepare_next_impl_branch


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_prepare_next_impl_branch_returns_selected_branch(monkeypatch, tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "active_node": {"node_id": "rwg-47"},
            "nodes": [
                {
                    "node_id": "rwg-47",
                    "title": "Next runtime slice",
                    "target_execplan_id": "20260327-plan",
                    "implementation_branch": "impl-execplan/20260327-plan",
                    "initiative_branch": "initiative/example",
                    "parent_initiative_node": "initiative-example",
                    "status": "decision_gated",
                    "ordering": {"queue_position": 47},
                }
            ],
        },
    )
    monkeypatch.setattr("platform_tools.mergeback_orchestration.get_current_branch", lambda **kwargs: "initiative/example")
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._resolve_branch_ref",
        lambda *args, **kwargs: "HEAD",
    )
    monkeypatch.setattr(
        "platform_tools.mergeback_orchestration._prior_unmerged_impl_slices",
        lambda *args, **kwargs: [],
    )

    code, report = prepare_next_impl_branch(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "prepare-next-impl-branch"
    assert report["selected"]["implementation_branch"] == "impl-execplan/20260327-plan"
    assert report["next_action"] == "cut_impl_branch"


def test_prepare_next_impl_branch_blocks_when_not_on_initiative_branch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("platform_tools.mergeback_orchestration.get_current_branch", lambda **kwargs: "impl-execplan/example")

    code, report = prepare_next_impl_branch(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 1
    assert report["blockers"] == ["initiative_branch_not_current"]
    assert report["next_action"] == "refresh_initiative_branch"
