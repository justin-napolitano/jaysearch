from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any


COMMAND = "install-local-git-hooks"
REQUIRED_HOOKS = ("post-merge", "post-checkout", "pre-push")


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _ensure_executable(path: Path) -> None:
    current_mode = path.stat().st_mode
    path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def run_install_local_git_hooks(
    *,
    root: str = ".",
    hook_path: str = ".githooks",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    hooks_dir = root_path / hook_path
    missing_hooks = [name for name in REQUIRED_HOOKS if not (hooks_dir / name).exists()]
    if missing_hooks:
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "root": root_path.as_posix(),
            "hook_path": hook_path,
            "missing_hooks": missing_hooks,
        }
        return 1, report

    for hook_name in REQUIRED_HOOKS:
        _ensure_executable(hooks_dir / hook_name)

    _git(root_path, "config", "--local", "core.hooksPath", hook_path)
    configured = _git(root_path, "config", "--local", "--get", "core.hooksPath")
    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "root": root_path.as_posix(),
        "hook_path": hook_path,
        "configured_hooks_path": configured,
        "installed_hooks": list(REQUIRED_HOOKS),
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--hook-path", default=".githooks")
    args = parser.parse_args()
    code, report = run_install_local_git_hooks(root=args.root, hook_path=args.hook_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
