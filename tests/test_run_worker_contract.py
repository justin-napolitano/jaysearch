from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.public_orchestration_api import API_VERSION
from platform_tools.run_worker_contract import run_worker_contract


def test_run_worker_contract_uses_next_ready_contract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "platform_tools.run_worker_contract.get_current_branch",
        lambda **kwargs: "initiative/example",
    )
    monkeypatch.setattr(
        "platform_tools.run_worker_contract.get_next_worker_slice",
        lambda **kwargs: (
            0,
            {
                "selected": {
                    "contract_id": "contract-1",
                    "execplan_id": "plan-id",
                    "implementation_branch": "impl-execplan/example-worker",
                    "initiative_branch": "initiative/example",
                    "worker_id": "example-worker",
                    "title": "Example worker",
                }
            },
        ),
    )

    captured: dict[str, object] = {}

    def _fake_coordinator(**kwargs):
        captured.update(kwargs)
        return 0, {"ok": True, "status": "ok"}

    monkeypatch.setattr("platform_tools.run_worker_contract.run_worker_session_coordinator", _fake_coordinator)

    code, report = run_worker_contract(
        root=tmp_path.as_posix(),
        executor="local_clone",
        push_mode="staging_and_github",
        github_push_remote="github",
        commit=True,
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["command"] == "run-worker-contract"
    assert report["selected"]["contract_id"] == "contract-1"
    assert captured["repo_source"] == tmp_path.resolve().as_posix()
    assert captured["branch"] == "impl-execplan/example-worker"
    assert captured["worker_id"] == "example-worker"
    assert captured["backend"] == "clone"
    assert captured["push"] is True
    assert captured["github_push_remote"] == "github"
    assert captured["actor_id"] == "orchestrator/default"


def test_run_worker_contract_resolves_explicit_contract_without_initiative(monkeypatch, tmp_path: Path) -> None:
    contracts_dir = tmp_path / "artifacts" / "governance" / "initiative-worker-contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "initiative-example.json").write_text(
        """
{
  "initiative_branch": "initiative/example",
  "contracts": [
    {
      "contract_id": "contract-1",
      "title": "Example worker",
      "status": "ready",
      "execplan_id": "plan-id",
      "initiative_branch": "initiative/example",
      "branch": "impl-execplan/example-worker",
      "worker_id": "example-worker",
      "scope": {
        "owned_surfaces": ["README.md"],
        "non_goals": ["Do not widen scope"],
        "validations": ["uv run pytest -q tests/test_run_worker_contract.py"]
      }
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "platform_tools.run_worker_contract.run_worker_session_coordinator",
        lambda **kwargs: (0, {"ok": True, "status": "ok", "branch": kwargs["branch"]}),
    )

    code, report = run_worker_contract(
        root=tmp_path.as_posix(),
        contract_id="contract-1",
        executor="local_worktree",
        push_mode="none",
    )

    assert code == 0
    assert report["api_version"] == API_VERSION
    assert report["initiative_branch"] == "initiative/example"
    assert report["selected"]["implementation_branch"] == "impl-execplan/example-worker"
    assert report["executor"] == "local_worktree"


def test_run_worker_contract_blocks_for_unsupported_executor(tmp_path: Path) -> None:
    code, report = run_worker_contract(root=tmp_path.as_posix(), executor="cloud_job")

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert "unsupported_executor" in report["blockers"]


def test_run_worker_contract_blocks_for_missing_github_remote(tmp_path: Path) -> None:
    code, report = run_worker_contract(root=tmp_path.as_posix(), push_mode="github")

    assert code == 1
    assert report["api_version"] == API_VERSION
    assert "github_push_remote_required" in report["blockers"]
