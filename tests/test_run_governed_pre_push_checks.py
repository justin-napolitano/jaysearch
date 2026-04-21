from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.run_governed_pre_push_checks import run_governed_pre_push_checks


def test_pre_push_checks_skip_non_governed_branch() -> None:
    code, report = run_governed_pre_push_checks(branch="docs/example")

    assert code == 0
    assert report["status"] == "skipped"


def test_pre_push_checks_validate_draft_execplan(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.discover_execplan",
        lambda *args, **kwargs: (plan, [plan.as_posix()], "draft_branch"),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.validate_execplan",
        lambda path: {"errors": [], "warnings": [], "plan": str(path)},
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="draft-execplan/test")

    assert code == 0
    assert report["status"] == "ok"
    assert report["execplan_path"] == plan.as_posix()


def test_pre_push_checks_validate_initiative_execplan(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: \"plan-id\"\n---\n\n## Outcomes & Retrospective\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.discover_execplan",
        lambda *args, **kwargs: (plan, [plan.as_posix()], "initiative_branch"),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.validate_execplan",
        lambda path: {"errors": [], "warnings": [], "plan": str(path)},
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="initiative/example")

    assert code == 0
    assert report["status"] == "ok"
    assert report["execplan_path"] == plan.as_posix()
    assert report["execplan_strategy"] == "initiative_branch"


def test_pre_push_checks_run_policy_compliance_for_impl_branch(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.discover_execplan",
        lambda *args, **kwargs: (plan, [plan.as_posix()], "implementation_branch"),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.validate_execplan",
        lambda path: {"errors": [], "warnings": [], "plan": str(path)},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks._effective_base_ref",
        lambda **kwargs: "initiative/example",
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks._published_branch_rewrite_status",
        lambda *args, **kwargs: {"published_ref_exists": True},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_policy_compliance",
        lambda **kwargs: (0, {"blockers": []}),
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="impl-execplan/test")

    assert code == 0
    assert report["status"] == "ok"
    assert any(item["name"] == "policy_compliance_check" for item in report["checks"])


def test_pre_push_checks_allow_initial_impl_branch_publish(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / ".agent" / "execplans" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("---\nid: \"plan-id\"\n---\n\n# Purpose / Big Picture\n", encoding="utf-8")

    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.discover_execplan",
        lambda *args, **kwargs: (plan, [plan.as_posix()], "implementation_branch"),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.validate_execplan",
        lambda path: {"errors": [], "warnings": [], "plan": str(path)},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks._effective_base_ref",
        lambda **kwargs: "initiative/example",
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks._published_branch_rewrite_status",
        lambda *args, **kwargs: {"published_ref_exists": False},
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="impl-execplan/test")

    assert code == 0
    assert report["status"] == "ok"
    assert any(item.get("status") == "deferred_initial_publish" for item in report["checks"])


def test_pre_push_checks_block_on_runtime_artifact_errors(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (1, {"errors": ["problem_detail_too_long:run-1.problem.json"]}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (0, {"errors": []}),
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="initiative/example")

    assert code == 1
    assert report["status"] == "blocked"
    assert any(item["name"] == "worker_runtime_artifact_check" and item["ok"] is False for item in report["checks"])
    assert "worker_runtime_artifacts:problem_detail_too_long:run-1.problem.json" in report["blockers"]


def test_pre_push_checks_block_on_public_orchestration_api_errors(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.evaluate_branch_policy",
        lambda *args, **kwargs: {"ok": True, "findings": []},
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_governance",
        lambda: (0, {"findings": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_remaining_work_graph",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_worker_runtime_artifacts",
        lambda **kwargs: (0, {"errors": []}),
    )
    monkeypatch.setattr(
        "platform_tools.run_governed_pre_push_checks.check_public_orchestration_api",
        lambda **kwargs: (1, {"errors": ["get_graph_state:invalid_api_version:response_get_graph_state:public-orchestration.v0"]}),
    )

    code, report = run_governed_pre_push_checks(root=tmp_path.as_posix(), branch="initiative/example")

    assert code == 1
    assert report["status"] == "blocked"
    assert any(item["name"] == "public_orchestration_api_check" and item["ok"] is False for item in report["checks"])
    assert "public_orchestration_api:get_graph_state:invalid_api_version:response_get_graph_state:public-orchestration.v0" in report["blockers"]
