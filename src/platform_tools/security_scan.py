from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "api_key_assignment": re.compile(
        r"(?i)\bapi[_-]?key\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\/\+=]{8,}"
    ),
    "token_assignment": re.compile(r"(?i)\btoken\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\/\+=]{8,}"),
    "password_assignment": re.compile(
        r"(?i)\bpassword\b\s*[:=]\s*[\"']?[^\s\"']{6,}"
    ),
}

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".ruff_cache"}


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def scan_repository(path: str | Path = ".") -> dict[str, Any]:
    root = Path(path)
    findings: list[dict[str, Any]] = []
    for file_path in _iter_files(root):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(
                        {
                            "type": name,
                            "file": file_path.as_posix(),
                            "line": idx,
                        }
                    )
    findings.sort(key=lambda x: (x["file"], x["line"], x["type"]))
    return {
        "tool": "security_scan",
        "root": root.as_posix(),
        "finding_count": len(findings),
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    report = scan_repository(args.path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report["finding_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
