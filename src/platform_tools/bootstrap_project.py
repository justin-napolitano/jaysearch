from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

TEMPLATE_PATHS = [
    ".agent",
    "bin",
    "docs",
    "examples",
    "policy",
    "prompts",
    "spec",
    "src",
    "Makefile",
    "README.md",
    "TODO.md",
    "main.py",
    "pyproject.toml",
]


def _copy_path(src: Path, dst: Path, force: bool) -> tuple[bool, str]:
    if src.is_dir():
        if dst.exists() and not force:
            return False, "exists"
        shutil.copytree(src, dst, dirs_exist_ok=force)
        return True, "copied"
    if src.is_file():
        if dst.exists() and not force:
            return False, "exists"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True, "copied"
    return False, "missing_source"


def bootstrap_project(
    destination: str,
    project_name: str | None = None,
    force: bool = False,
) -> tuple[int, dict[str, Any]]:
    repo_root = Path(".").resolve()
    target_root = Path(destination).resolve()
    project_dir = target_root / project_name if project_name else target_root

    if project_dir.exists() and any(project_dir.iterdir()) and not force:
        return 1, {
            "tool": "bootstrap_project",
            "ok": False,
            "reason": "destination_not_empty",
            "destination": project_dir.as_posix(),
            "created": [],
            "skipped": [],
        }

    project_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[dict[str, str]] = []

    for rel in TEMPLATE_PATHS:
        src = repo_root / rel
        dst = project_dir / rel
        did_copy, reason = _copy_path(src, dst, force=force)
        if did_copy:
            created.append(rel)
        else:
            skipped.append({"path": rel, "reason": reason})

    report = {
        "tool": "bootstrap_project",
        "ok": True,
        "destination": project_dir.as_posix(),
        "project_name": project_name or project_dir.name,
        "created_count": len(created),
        "created": sorted(created),
        "skipped": sorted(skipped, key=lambda item: item["path"]),
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    parser.add_argument("--name", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    code, report = bootstrap_project(
        destination=args.destination,
        project_name=args.name,
        force=args.force,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
