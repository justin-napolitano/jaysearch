from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_governed_graph_events import reconcile_governed_graph_events


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_reconcile_governed_graph_events_runs_registration_and_transition(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    _write(
        plan,
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.register_remaining_work_node",
        lambda **kwargs: {"command": "register-remaining-work-node", "ok": True, "status": "ok", "action": "registered"},
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.reconcile_remaining_work_transition",
        lambda **kwargs: {"command": "reconcile-remaining-work-transition", "ok": True, "status": "ok", "target_state": "review_gated"},
    )

    report = reconcile_governed_graph_events(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert [step["command"] for step in report["steps"]] == [
        "register-remaining-work-node",
        "reconcile-remaining-work-transition",
    ]


def test_reconcile_governed_graph_events_attempts_merge_after_ready(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    _write(
        plan,
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.register_remaining_work_node",
        lambda **kwargs: {"command": "register-remaining-work-node", "ok": True, "status": "ok", "action": "noop"},
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.reconcile_remaining_work_transition",
        lambda **kwargs: {"command": "reconcile-remaining-work-transition", "ok": True, "status": "ok", "target_state": "ready"},
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.reconcile_remaining_work_merge",
        lambda **kwargs: {"command": "reconcile-remaining-work-merge", "ok": True, "status": "ok", "completion_ref": "merged:pr-91"},
    )

    report = reconcile_governed_graph_events(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert report["merge_completed"] is True
    assert [step["command"] for step in report["steps"]] == [
        "register-remaining-work-node",
        "reconcile-remaining-work-transition",
        "reconcile-remaining-work-merge",
    ]


def test_reconcile_governed_graph_events_treats_already_registered_plan_as_noop(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    _write(
        plan,
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json_text(
            {
                "nodes": [
                    {
                        "node_id": "rwg-101",
                        "target_execplan_id": "plan-id",
                    }
                ]
            }
        ),
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.register_remaining_work_node",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("missing_graph_registration")),
    )
    monkeypatch.setattr(
        "platform_tools.reconcile_governed_graph_events.reconcile_remaining_work_transition",
        lambda **kwargs: {"command": "reconcile-remaining-work-transition", "ok": True, "status": "ok", "target_state": "review_gated"},
    )

    report = reconcile_governed_graph_events(execplan_path=plan, repo_root=tmp_path)

    assert report["ok"] is True
    assert report["steps"][0]["action"] == "noop"
    assert report["steps"][0]["reason"] == "already_registered_in_graph"


def json_text(data: dict[str, object]) -> str:
    import json

    return json.dumps(data, indent=2) + "\n"
