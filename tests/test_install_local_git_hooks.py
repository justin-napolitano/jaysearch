from __future__ import annotations

from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.install_local_git_hooks import run_install_local_git_hooks


def test_install_local_git_hooks_configures_core_hooks_path(monkeypatch, tmp_path: Path) -> None:
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir()
    for name in ("post-merge", "post-checkout", "pre-push"):
        path = hooks_dir / name
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    recorded: list[tuple[str, ...]] = []

    def fake_git(root: Path, *args: str) -> str:
        recorded.append(args)
        if args == ("config", "--local", "--get", "core.hooksPath"):
            return ".githooks"
        return ""

    monkeypatch.setattr("platform_tools.install_local_git_hooks._git", fake_git)

    code, report = run_install_local_git_hooks(root=tmp_path.as_posix())

    assert code == 0
    assert report["configured_hooks_path"] == ".githooks"
    assert ("config", "--local", "core.hooksPath", ".githooks") in recorded


def test_install_local_git_hooks_blocks_when_required_hook_missing(tmp_path: Path) -> None:
    hooks_dir = tmp_path / ".githooks"
    hooks_dir.mkdir()
    (hooks_dir / "post-merge").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    code, report = run_install_local_git_hooks(root=tmp_path.as_posix())

    assert code == 1
    assert "post-checkout" in report["missing_hooks"]
