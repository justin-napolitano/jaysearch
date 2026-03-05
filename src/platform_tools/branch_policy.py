from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path
from typing import Any

import yaml


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


def _load_allowed_patterns() -> list[str]:
    patterns: list[str] = []
    ruleset_path = Path("spec/ruleset.yaml")
    workflow_path = Path("spec/workflow.yaml")

    if ruleset_path.exists():
        data = yaml.safe_load(ruleset_path.read_text(encoding="utf-8")) or {}
        exec_constraints = data.get("execution_constraints", {})
        for p in exec_constraints.get("allowed_branch_patterns", []) or []:
            if isinstance(p, str) and p.strip():
                patterns.append(p.strip())

    if workflow_path.exists():
        data = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
        exec_requirements = data.get("execution_requirements", {})
        workflow_patterns = exec_requirements.get("workflow_branch_patterns", {}) or {}
        if isinstance(workflow_patterns, dict):
            for value in workflow_patterns.values():
                if isinstance(value, str) and value.strip():
                    patterns.append(value.strip())

    dedup: list[str] = []
    seen = set()
    for p in patterns:
        if p not in seen:
            dedup.append(p)
            seen.add(p)
    return dedup


def evaluate_branch_policy(branch: str) -> dict[str, Any]:
    # Universal governance requirement: all actions run on a dedicated non-protected branch.
    forbidden = {"main", "master", ""}
    allowed_patterns = _load_allowed_patterns()
    ok = branch not in forbidden
    findings: list[str] = []
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
