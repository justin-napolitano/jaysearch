from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.orchestrate_governed_slice import _effective_base_ref, run_orchestrate_governed_slice


def test_orchestrate_governed_slice_uses_control_plane_status_and_action(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "impl-execplan/test",
                "branch_role": "implementation_execplan",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": [],
                "checks": {"managed_repo": None},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "recommended_action": "open_pr_to_initiative",
                "command_ref": "bin/get-pr-integration-contract",
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 0
    assert report["ok"] is True
    assert report["control_plane_status"]["branch_role"] == "implementation_execplan"
    assert report["next_orchestration_action"]["recommended_action"] == "open_pr_to_initiative"
    assert report["post_merge_reconciliation"]["reconciled_count"] == 0
    assert report["execution"]["mode"] == "project_only"
    assert report["execution"]["executed"] is False
    assert report["next_actions"][0]["action"] == "open_pr_to_initiative"


def test_orchestrate_governed_slice_targets_managed_repo_through_control_plane(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": [],
                "checks": {"managed_repo": {"status": "ok", "ok": True, "blockers": []}},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "recommended_action": "cut_impl_branch",
                "command_ref": "bin/prepare-next-impl-branch",
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=tmp_path.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["managed_repo"]["ok"] is True
    assert report["repo_root"] == tmp_path.resolve().as_posix()
    assert report["execution"]["mode"] == "project_only"
    assert report["next_actions"][0]["action"] == "cut_impl_branch"


def test_orchestrate_governed_slice_blocks_on_control_plane(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            1,
            {
                "current_branch": "impl-execplan/test",
                "branch_role": "implementation_execplan",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": ["stale_initiative_base"],
                "checks": {"managed_repo": None},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            1,
            {
                "recommended_action": "restack_on_initiative",
                "command_ref": "bin/get-merge-readiness",
                "blockers": ["stale_initiative_base"],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 1
    assert "stale_initiative_base" in report["blockers"]
    assert report["execution"]["executed"] is False
    assert report["next_actions"][0]["command_ref"] == "bin/get-merge-readiness"


def test_orchestrate_governed_slice_deduplicates_next_action_blockers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            1,
            {
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": ["missing_required_artifact:spec/workflow.yaml"],
                "checks": {
                    "managed_repo": {
                        "status": "blocked",
                        "ok": False,
                        "blockers": ["missing_required_artifact:spec/workflow.yaml"],
                    }
                },
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            1,
            {
                "recommended_action": "resolve_control_plane_blockers",
                "command_ref": "bin/managed-repo-status",
                "blockers": ["missing_required_artifact:spec/workflow.yaml"],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".")

    assert code == 1
    assert report["blockers"] == ["missing_required_artifact:spec/workflow.yaml"]
    assert report["next_actions"][0]["action"] == "resolve_control_plane_blockers"


def test_orchestrate_governed_slice_executes_recommended_action(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "impl-execplan/test",
                "branch_role": "implementation_execplan",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": [],
                "checks": {"managed_repo": None},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "recommended_action": "open_pr_to_initiative",
                "command_ref": "bin/get-pr-integration-contract",
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.project_pr_integration_contract",
        lambda **kwargs: (0, {"command": "get-pr-integration-contract", "status": "ok", "ok": True, "blockers": []}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".", execute=True)

    assert code == 0
    assert report["execution"]["mode"] == "execute_next_step"
    assert report["execution"]["executed"] is True
    assert report["execution"]["command"] == "bin/get-pr-integration-contract"


def test_orchestrate_governed_slice_executes_task_route_and_worker_dispatch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_control_plane_status",
        lambda **kwargs: (
            0,
            {
                "current_branch": "initiative/example",
                "branch_role": "initiative",
                "initiative_branch": "initiative/example",
                "repo_root": kwargs["repo_root"],
                "blockers": [],
                "checks": {"managed_repo": None},
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.get_next_orchestration_action",
        lambda **kwargs: (
            0,
            {
                "recommended_action": "cut_impl_branch",
                "command_ref": "bin/prepare-next-impl-branch",
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.route_local_task",
        lambda **kwargs: (
            0,
            {
                "command": "local-task-router",
                "status": "ok",
                "ok": True,
                "route_target": "local_execution_worker",
                "blockers": [],
            },
        ),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.start_next_worker",
        lambda **kwargs: (0, {"command": "start-next-worker", "status": "ok", "ok": True}),
    )
    monkeypatch.setattr(
        "platform_tools.orchestrate_governed_slice.reconcile_pending_merge_completions",
        lambda **kwargs: {"command": "reconcile-pending-merge-completions", "ok": True, "status": "ok", "reconciled_count": 0, "results": []},
    )

    code, report = run_orchestrate_governed_slice(root=".", execute=True, task="implement the next worker slice")

    assert code == 0
    assert report["execution"]["executed"] is True
    assert report["execution"]["command"] == "bin/start-next-worker"
    assert report["execution"]["result"]["route"]["route_target"] == "local_execution_worker"


def test_effective_base_ref_prefers_initiative_branch_for_impl_execplan(tmp_path: Path) -> None:
    execplan_path = tmp_path / ".agent" / "execplans" / "plan.md"
    execplan_path.parent.mkdir(parents=True, exist_ok=True)
    execplan_path.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")
    graph_path = tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        """
{
  "nodes": [
    {
      "target_execplan_id": "plan-id",
      "integration_mode": "via_initiative",
      "initiative_branch": "initiative/graph-transition-automation"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    base_ref = _effective_base_ref(
        repo_root=tmp_path,
        branch="impl-execplan/test",
        execplan_path=execplan_path.as_posix(),
        default_base_ref="main",
    )

    assert base_ref == "initiative/graph-transition-automation"
