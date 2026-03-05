from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def analyze_diff(base: str = "HEAD~1", head: str = "HEAD") -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "diff", "--numstat", base, head],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return {
            "tool": "diff_analyzer",
            "base": base,
            "head": head,
            "error": proc.stderr.strip(),
            "files": [],
            "summary": {"files_changed": 0, "lines_added": 0, "lines_removed": 0},
        }

    files: list[dict[str, Any]] = []
    total_add, total_remove = 0, 0
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_s, removed_s, file_path = parts
        try:
            added = int(added_s)
            removed = int(removed_s)
        except ValueError:
            added = 0
            removed = 0
        total_add += added
        total_remove += removed
        files.append({"file": Path(file_path).as_posix(), "added": added, "removed": removed})
    files.sort(key=lambda x: x["file"])
    return {
        "tool": "diff_analyzer",
        "base": base,
        "head": head,
        "files": files,
        "summary": {
            "files_changed": len(files),
            "lines_added": total_add,
            "lines_removed": total_remove,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD~1")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    report = analyze_diff(base=args.base, head=args.head)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
