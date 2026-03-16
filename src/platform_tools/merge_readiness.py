from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.plan_utils import parse_plan
from platform_tools.policy_compliance_check import (
    EXCEPTION_REGISTRY_PATH,
    _active_commit_hard_limit_exception,
    _current_branch,
    _is_bounded_execplan_reconciliation,
    _is_bounded_branch_reconciliation_commit,
    _is_bounded_policy_repair_commit,
    _repo_relative_path,
)


GENERATED_ARTIFACT_PREFIXES = (
    "artifacts/planner/graphs/",
    "artifacts/planner/sessions/",
    "artifacts/planner/imports/",
)
GENERATED_ARTIFACT_EXACT = {
    ".agent/execplans/20260310-smoke-draft-contract-codex-01-execplan.md",
}

CLASS_ORDER = {
    "execplan": 1,
    "spec": 2,
    "runtime": 3,
    "test": 4,
    "docs": 5,
    "research": 6,
    "governance": 7,
    "unknown": 99,
}


def _run(
    command: str,
    *,
    cwd: Path,
) -> dict[str, Any]:
    proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _merge_base(cwd: Path, base_ref: str) -> str:
    return _git(cwd, "merge-base", "HEAD", base_ref)


def _changed_files(cwd: Path, base_ref: str) -> list[str]:
    merge_base = _merge_base(cwd, base_ref)
    output = _git(cwd, "diff", "--name-only", f"{merge_base}..HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _discover_execplan(cwd: Path, base_ref: str) -> Path:
    candidates = [path for path in _changed_files(cwd, base_ref) if path.startswith(".agent/execplans/") and path.endswith(".md")]
    if len(candidates) != 1:
        raise RuntimeError("active_execplan_not_deterministic")
    return cwd / candidates[0]


def _validation_entries(execplan_path: Path) -> list[dict[str, str]]:
    parsed = parse_plan(execplan_path)
    frontmatter = parsed.frontmatter
    validation = frontmatter.get("validation", {}) if isinstance(frontmatter, dict) else {}
    tests = validation.get("tests", []) if isinstance(validation, dict) else []
    entries: list[dict[str, str]] = []
    for item in tests:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command", "")).strip()
        name = str(item.get("name", "")).strip() or command
        if command:
            entries.append({"name": name, "command": command})
    return entries


def _requires_citation_check(changed_files: list[str]) -> bool:
    return any(
        path.startswith("docs/")
        or path.startswith("spec/")
        or path.startswith("artifacts/planner/research/")
        for path in changed_files
    )


def _has_policy_compliance_runtime(cwd: Path) -> bool:
    return (cwd / "bin" / "policy-compliance-check").exists()


def _dirty_generated_artifacts(cwd: Path) -> list[str]:
    output = _git(cwd, "status", "--porcelain", "--untracked-files=all")
    dirty: list[str] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if path in GENERATED_ARTIFACT_EXACT or any(path.startswith(prefix) for prefix in GENERATED_ARTIFACT_PREFIXES):
            dirty.append(path)
    return sorted(dirty)


def _classify_commit(subject: str) -> str:
    if subject.startswith("docs(execplan):"):
        return "execplan"
    if subject.startswith("spec(") or subject.startswith("spec:"):
        return "spec"
    if subject.startswith("test(") or subject.startswith("test:"):
        return "test"
    if subject.startswith("docs(research):"):
        return "research"
    if subject.startswith("docs(governance):"):
        return "governance"
    if subject.startswith("docs(") or subject.startswith("docs:"):
        return "docs"
    if subject.startswith(("feat(", "feat:", "fix(", "fix:", "refactor(", "refactor:")):
        return "runtime"
    return "unknown"


def _commit_reports(
    cwd: Path,
    base_ref: str,
    *,
    active_execplan_path: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    merge_base = _merge_base(cwd, base_ref)
    output = _git(cwd, "rev-list", "--reverse", f"{merge_base}..HEAD")
    commits = [line.strip() for line in output.splitlines() if line.strip()]
    reports: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    max_seen = 0

    for commit in commits:
        subject = _git(cwd, "show", "-s", "--format=%s", commit)
        body = _git(cwd, "show", "-s", "--format=%b", commit)
        numstat = _git(cwd, "show", "--numstat", "--format=", commit)
        name_only = _git(cwd, "show", "--name-only", "--format=", commit)
        commit_files = [line.strip() for line in name_only.splitlines() if line.strip()]
        file_count = 0
        changed_lines = 0
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            file_count += 1
            added = 0 if parts[0] == "-" else int(parts[0])
            deleted = 0 if parts[1] == "-" else int(parts[1])
            changed_lines += added + deleted

        commit_class = _classify_commit(subject)
        class_order = CLASS_ORDER[commit_class]
        branch_reconciliation = _is_bounded_branch_reconciliation_commit(
            subject=subject,
            commit_class=commit_class,
            commit_files=commit_files,
            changed_lines=changed_lines,
            active_execplan_path=active_execplan_path,
        )
        if branch_reconciliation:
            warnings.append(f"bounded_branch_reconciliation_commit:{commit}")
        if commit_class != "unknown" and class_order < max_seen and not branch_reconciliation:
            allowed_execplan_reconciliation, _ = _is_bounded_execplan_reconciliation(
                cwd=cwd,
                commit=commit,
                commit_class=commit_class,
                commit_files=commit_files,
                changed_lines=changed_lines,
                active_execplan_path=active_execplan_path,
            )
            allowed_policy_repair, _ = _is_bounded_policy_repair_commit(
                subject=subject,
                commit_class=commit_class,
                commit_files=commit_files,
                changed_lines=changed_lines,
                active_execplan_path=active_execplan_path,
            )
            if allowed_execplan_reconciliation:
                warnings.append(f"bounded_execplan_reconciliation:{commit}")
            elif allowed_policy_repair:
                warnings.append(f"bounded_policy_repair_commit:{commit}")
            else:
                errors.append(f"procedural_commit_order_violation:{commit}:{subject}")
        if not branch_reconciliation:
            max_seen = max(max_seen, class_order)

        if changed_lines > 400 and "commit-size-justification" not in body:
            exception_id = _active_commit_hard_limit_exception(cwd, _current_branch(cwd), commit)
            if exception_id:
                warnings.append(f"commit_hard_limit_exception:{commit}:{exception_id}")
            else:
                errors.append(f"commit_hard_limit_exceeded:{commit}:{changed_lines}")
        elif changed_lines > 250 and commit_class not in {"execplan"}:
            warnings.append(f"commit_soft_limit_exceeded:{commit}:{changed_lines}")
        if file_count > 5:
            warnings.append(f"commit_file_target_exceeded:{commit}:{file_count}")

        reports.append(
            {
                "commit": commit,
                "subject": subject,
                "class": commit_class,
                "file_count": file_count,
                "changed_lines": changed_lines,
                "files": commit_files,
            }
        )
    return reports, errors, warnings


def _scope_blocker_report(cwd: Path, graph_id: str | None) -> dict[str, Any]:
    if not graph_id:
        return {
            "status": "deferred",
            "blockers": ["graph_scope_check_deferred:no_graph_id"],
        }
    graph_path = cwd / "artifacts" / "planner" / "graphs" / f"{graph_id}.json"
    if not graph_path.exists():
        return {
            "status": "fail",
            "blockers": [f"missing_graph:{graph_id}"],
        }
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    blockers: list[str] = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if node.get("status") in {"blocked", "recovery_required"}:
            blockers.append(f"graph_blocker:{node.get('node_id', '?')}")
        if node.get("node_type") == "question" and node.get("blocking") is True:
            blockers.append(f"graph_blocking_question:{node.get('node_id', '?')}")
    return {
        "status": "pass" if not blockers else "fail",
        "blockers": blockers,
    }


def check_merge_readiness(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    base_ref: str = "main",
    graph_id: str | None = None,
    include_validation_runs: bool = True,
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    branch = get_current_branch()
    plan_path = Path(execplan_path) if execplan_path else _discover_execplan(cwd, base_ref)
    parsed = parse_plan(plan_path)
    execplan_id = str(parsed.frontmatter.get("id", "")).strip()

    changed_files = _changed_files(cwd, base_ref)
    validation_entries = _validation_entries(plan_path)
    commands: list[dict[str, str]] = list(validation_entries)
    seen_commands = {entry["command"] for entry in commands}

    for name, command in (
        ("rule_graph_check", "bin/rule-graph-check"),
        ("citation_check", "bin/citation-check" if _requires_citation_check(changed_files) else ""),
        ("policy_compliance_check", "bin/policy-compliance-check" if _has_policy_compliance_runtime(cwd) else ""),
    ):
        if command and command not in seen_commands:
            commands.append({"name": name, "command": command})
            seen_commands.add(command)

    validation_results = []
    failing_checks: list[str] = []
    if include_validation_runs:
        for entry in commands:
            result = _run(entry["command"], cwd=cwd)
            result["name"] = entry["name"]
            validation_results.append(result)
            if not result["ok"]:
                failing_checks.append(f"validation_failed:{entry['name']}")

    smoke_present = any("smoke" in entry["name"].lower() or "smoke" in entry["command"].lower() for entry in commands)
    if not smoke_present:
        failing_checks.append("missing_smoke_test_validation")

    dirty_artifacts = _dirty_generated_artifacts(cwd)
    if dirty_artifacts:
        failing_checks.append("dirty_generated_artifacts")

    commit_reports, commit_errors, commit_warnings = _commit_reports(
        cwd,
        base_ref,
        active_execplan_path=_repo_relative_path(plan_path, root=cwd),
    )
    failing_checks.extend(commit_errors)
    scope_report = _scope_blocker_report(cwd, graph_id)
    if scope_report["status"] == "fail":
        failing_checks.extend(scope_report["blockers"])

    readiness = not failing_checks
    next_action = "ready_for_review" if readiness else "resolve_blockers"

    report = {
        "tool": "merge_readiness_check",
        "branch": branch,
        "execplan_id": execplan_id,
        "execplan_path": plan_path.as_posix(),
        "readiness": readiness,
        "failing_checks": failing_checks,
        "blockers": scope_report["blockers"],
        "dirty_artifacts": dirty_artifacts,
        "human_approvals": [
            "human_review_required",
            "execplan_finalization_required",
        ],
        "next_action": next_action,
        "checks": {
            "validations": validation_results,
            "validation_runs_included": include_validation_runs,
            "smoke_test_present": smoke_present,
            "commit_stack": commit_reports,
            "scope_blockers": scope_report,
        },
        "warnings": commit_warnings,
        "changed_files": changed_files,
    }
    return (1 if not readiness else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execplan-path", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--graph-id", default=None)
    args = parser.parse_args()
    code, report = check_merge_readiness(
        root=args.root,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
        graph_id=args.graph_id,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
