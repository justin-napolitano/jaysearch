from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.local_runtime.adapter import RuntimeUnavailableError
from platform_tools.local_runtime.runtime_check import check_local_runtime


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_local_runtime_check_blocks_when_runtime_unavailable(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))
    monkeypatch.setattr(
        "platform_tools.local_runtime.runtime_check.OllamaAdapter.runtime_probe",
        lambda self, required_models=None: (_ for _ in ()).throw(RuntimeUnavailableError("boom")),
    )

    code, report = check_local_runtime(root=tmp_path.as_posix(), required_models=["router"])

    assert code == 1
    assert report["status"] == "blocked"
    assert report["blockers"] == ["runtime_endpoint_unreachable"]


def test_local_runtime_check_blocks_for_missing_target_artifacts(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))
    target = tmp_path / "target"
    target.mkdir()

    code, report = check_local_runtime(
        root=tmp_path.as_posix(),
        repo_root=target.as_posix(),
        verify_managed_repo=True,
    )

    assert code == 1
    assert report["blockers"] == ["required_target_artifact_missing"]


def test_local_runtime_check_reports_missing_models(monkeypatch, tmp_path: Path) -> None:
    _write(tmp_path / "spec" / "local-orchestration.yaml", Path("spec/local-orchestration.yaml").read_text(encoding="utf-8"))
    monkeypatch.setattr(
        "platform_tools.local_runtime.runtime_check.OllamaAdapter.runtime_probe",
        lambda self, required_models=None: {
            "backend": "ollama",
            "reachable": True,
            "models_checked": list(required_models or []),
            "endpoint": "http://127.0.0.1:11434/api/tags",
            "latency_ms": 1,
            "available_models": ["router"],
            "missing_models": ["planner"],
        },
    )

    code, report = check_local_runtime(root=tmp_path.as_posix(), required_models=["planner"])

    assert code == 1
    assert report["blockers"] == ["configured_model_unavailable"]
