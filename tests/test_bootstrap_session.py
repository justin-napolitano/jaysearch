from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.session_bootstrap import run_session_bootstrap_check


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_bootstrap_session_reports_missing_governance_artifacts(tmp_path: Path) -> None:
    code, report = run_session_bootstrap_check(root=tmp_path.as_posix(), branch="impl-execplan/test", session_kind="codex")

    assert code == 1
    assert "missing_bootstrap_artifact:.agent/AGENTS.md" in report["blockers"]
