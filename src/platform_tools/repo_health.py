from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.execplan_lint import run as run_execplan_lint
from platform_tools.generate_todos import collect_tasks
from platform_tools.security_scan import scan_repository

GOVERNANCE_FILES = [
    ".agent/AGENTS.md",
    ".agent/PLANS.md",
    ".agent/metrics.yml",
]


def _check_governance_files() -> tuple[bool, list[str]]:
    missing = [p for p in GOVERNANCE_FILES if not Path(p).exists()]
    return len(missing) == 0, missing


def _tracked_execplan_paths() -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", ".agent/execplans/*.md"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return sorted(Path(line.strip()) for line in proc.stdout.splitlines() if line.strip())


def _check_todo_integrity(todo_path: str = "TODO.md") -> tuple[bool, dict[str, Any]]:
    tracked_paths = _tracked_execplan_paths()
    expected_tasks, warnings = collect_tasks(paths=tracked_paths if tracked_paths else None)
    todo = Path(todo_path)
    text = todo.read_text(encoding="utf-8") if todo.exists() else ""
    key_count = text.count("  key: ")
    ok = key_count == len(expected_tasks) and len(warnings) == 0
    details = {
        "todo_exists": todo.exists(),
        "expected_task_count": len(expected_tasks),
        "todo_key_count": key_count,
        "warnings": warnings,
        "tracked_execplans": len(tracked_paths),
    }
    return ok, details


def _calc_score(
    execplan_ok: bool,
    todo_ok: bool,
    security_ok: bool,
    governance_ok: bool,
    branch_ok: bool,
) -> tuple[int, int]:
    checks = [execplan_ok, todo_ok, security_ok, governance_ok, branch_ok]
    passed = sum(1 for c in checks if c)
    score = passed * 20
    level = 1
    if score >= 50:
        level = 2
    if score >= 75:
        level = 3
    if score == 100:
        level = 4
    return score, level


def check_repository_health(root: str = ".") -> tuple[int, dict[str, Any]]:
    lint_code, lint_report = run_execplan_lint([])
    execplan_ok = lint_code == 0

    todo_ok, todo_details = _check_todo_integrity()
    security_report = scan_repository(root)
    security_ok = security_report["finding_count"] == 0

    governance_ok, missing_gov = _check_governance_files()
    branch_policy = evaluate_branch_policy(get_current_branch())
    branch_ok = branch_policy["ok"]
    score, level = _calc_score(execplan_ok, todo_ok, security_ok, governance_ok, branch_ok)

    report = {
        "tool": "repo_health",
        "checks": {
            "execplan_structure": {
                "ok": execplan_ok,
                "error_count": lint_report["error_count"],
            },
            "todo_integrity": {
                "ok": todo_ok,
                **todo_details,
            },
            "security": {
                "ok": security_ok,
                "finding_count": security_report["finding_count"],
            },
            "governance_files": {
                "ok": governance_ok,
                "missing": missing_gov,
            },
            "branch_compliance": branch_policy,
        },
        "maturity": {"level": level, "score": score},
    }

    if not security_ok:
        return 2, report
    if not (execplan_ok and todo_ok and governance_ok and branch_ok):
        return 1, report
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    code, report = check_repository_health(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
