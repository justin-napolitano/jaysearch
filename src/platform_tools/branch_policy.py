from __future__ import annotations

import fnmatch
import subprocess
from typing import Any

from platform_tools.governance_loader import build_effective_policy


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


def _load_effective_branch_policy() -> tuple[list[str], list[str], list[str]]:
    _, report = build_effective_policy()
    findings = list(report.get("findings", []))
    effective = report.get("effective_policy", {}) if isinstance(report.get("effective_policy"), dict) else {}
    allowed = effective.get("allowed_branch_patterns", [])
    forbidden = effective.get("forbidden_branches", [])
    allowed_patterns = [str(p).strip() for p in allowed if str(p).strip()]
    forbidden_branches = [str(b).strip() for b in forbidden if str(b).strip() or b == ""]
    return allowed_patterns, sorted(set(forbidden_branches)), findings


def evaluate_branch_policy(branch: str) -> dict[str, Any]:
    # Universal governance requirement: all actions run on a dedicated non-protected branch.
    allowed_patterns, forbidden_branches, loader_findings = _load_effective_branch_policy()
    forbidden = set(forbidden_branches) if forbidden_branches else {"main", "master", ""}
    ok = branch not in forbidden and not loader_findings
    findings: list[str] = list(loader_findings)
    if branch in forbidden:
        findings.append("branch_policy_violation:execution_on_protected_branch")
    if branch and allowed_patterns:
        if not any(fnmatch.fnmatch(branch, pattern) for pattern in allowed_patterns):
            ok = False
            findings.append("branch_policy_violation:branch_pattern_mismatch")
    return {
        "ok": ok,
        "current_branch": branch,
        "forbidden_branches": sorted(forbidden),
        "allowed_branch_patterns": allowed_patterns,
        "findings": findings,
    }
