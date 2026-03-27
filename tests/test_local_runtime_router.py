from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.local_runtime.router import route_local_task


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_local_task_router_blocks_internet_required_when_disabled(tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))

    code, report = route_local_task(
        root=tmp_path.as_posix(),
        task="Research the latest cloud pricing",
        internet_required=True,
    )

    assert code == 1
    assert report["route_target"] == "human_escalation"
    assert report["blockers"] == ["internet_access_is_required_but_not_approved"]
    assert report["next_action"] == "human_review_required"


def test_local_task_router_returns_model_decision(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))
    _write(tmp_path / "spec" / "workflow.yaml", "version: v1\n")
    _write(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", "{}\n")
    _write(tmp_path / "docs" / "queued-execplans.md", "# queue\n")
    (tmp_path / ".agent" / "execplans").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        "platform_tools.local_runtime.router.OllamaAdapter.runtime_probe",
        lambda self, required_models=None: {"backend": "ollama", "reachable": True, "models_checked": list(required_models or [])},
    )
    monkeypatch.setattr(
        "platform_tools.local_runtime.router.OllamaAdapter.generate_json",
        lambda self, model, prompt, temperature=0.0: {
            "route_target": "planning_worker",
            "reason_codes": ["task_requires_graph_or_contract_changes"],
        },
    )

    code, report = route_local_task(
        root=tmp_path.as_posix(),
        repo_root=tmp_path.as_posix(),
        task="Refine the work graph and plan dependencies",
        requires_graph_changes=True,
    )

    assert code == 0
    assert report["status"] == "ok"
    assert report["route_target"] == "planning_worker"
    assert report["next_action"] == "bin/get-graph-state"


def test_local_task_router_blocks_invalid_model_response(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))
    monkeypatch.setattr(
        "platform_tools.local_runtime.router.OllamaAdapter.runtime_probe",
        lambda self, required_models=None: {"backend": "ollama", "reachable": True, "models_checked": list(required_models or [])},
    )
    monkeypatch.setattr(
        "platform_tools.local_runtime.router.OllamaAdapter.generate_json",
        lambda self, model, prompt, temperature=0.0: {"route_target": "not-real", "reason_codes": ["bad"]},
    )

    code, report = route_local_task(
        root=tmp_path.as_posix(),
        task="Do something ambiguous",
    )

    assert code == 1
    assert report["blockers"] == ["governance_authority_is_ambiguous"]
    assert report["route_target"] == "human_escalation"
