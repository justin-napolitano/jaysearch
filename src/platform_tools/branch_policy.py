from __future__ import annotations

import subprocess
from typing import Any


def get_current_branch() -> str:
    proc = subprocess.run(
        ["git", "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def evaluate_branch_policy(branch: str) -> dict[str, Any]:
    # Universal governance requirement: all actions run on a dedicated branch, never main/master.
    forbidden = {"main", "master", ""}
    ok = branch not in forbidden
    findings: list[str] = []
    if branch in forbidden:
        findings.append("branch_policy_violation:execution_on_protected_branch")
    return {
        "ok": ok,
        "current_branch": branch,
        "forbidden_branches": sorted(forbidden),
        "findings": findings,
    }
