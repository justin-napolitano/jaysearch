from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import get_current_branch
from platform_tools.anti_cheat_check import check_anti_cheat
from platform_tools.plan_utils import parse_frontmatter, parse_plan
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "policy-compliance-check"
GRAPH_PATH = "artifacts/planner/research/remaining-work-graph.json"
QUEUE_PATH = "docs/queued-execplans.md"
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
BOUNDED_EXECPLAN_FRONTMATTER_FIELDS = {"changes", "validation"}
BOUNDED_EXECPLAN_MAX_LINES = 120
BOUNDED_POLICY_REPAIR_MAX_LINES = 260
BOUNDED_POLICY_REPAIR_MAX_FILES = 5
BOUNDED_BRANCH_RECONCILIATION_MAX_LINES = 120
BOUNDED_BRANCH_RECONCILIATION_SUBJECT_PREFIXES = (
    "docs(governance): promote ",
    "docs(governance): reconcile graph and queue",
)
EXCEPTION_REGISTRY_PATH = ".agent/governance/exceptions.yaml"
BOUNDED_POLICY_REPAIR_SUBJECT_PREFIXES = (
    "fix(governance):",
    "feat(governance):",
    "test(governance):",
    "docs(governance):",
)
BOUNDED_POLICY_REPAIR_ALLOWED_FILES = {
    GRAPH_PATH,
    EXCEPTION_REGISTRY_PATH,
    "docs/agent-game-rules-v1.md",
    "docs/governance.md",
    "docs/queued-execplans.md",
    "src/platform_tools/execplan_lint.py",
    "src/platform_tools/policy_compliance_check.py",
    "tests/test_execplan_lint.py",
    "tests/test_policy_compliance_check.py",
}


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _current_branch(cwd: Path) -> str:
    try:
        return _git(cwd, "branch", "--show-current")
    except RuntimeError:
        return get_current_branch()


def _parse_iso8601(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def _merge_base(cwd: Path, base_ref: str) -> str:
    return _git(cwd, "merge-base", "HEAD", base_ref)


def _changed_files(cwd: Path, base_ref: str) -> list[str]:
    merge_base = _merge_base(cwd, base_ref)
    output = _git(cwd, "diff", "--name-only", f"{merge_base}..HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def _discover_execplan(cwd: Path, base_ref: str) -> Path:
    candidates = [
        path
        for path in _changed_files(cwd, base_ref)
        if path.startswith(".agent/execplans/") and path.endswith(".md")
    ]
    if len(candidates) != 1:
        raise RuntimeError("active_execplan_not_deterministic")
    return cwd / candidates[0]


def _classify_commit(subject: str) -> str:
    if subject.startswith("docs(execplan):"):
        return "execplan"
    if subject.startswith("spec(") or subject.startswith("spec:"):
        return "spec"
    if subject.startswith("test(") or subject.startswith("test:"):
        return "test"
    if subject.startswith("docs(research):") or subject.startswith("research(") or subject.startswith("research:"):
        return "research"
    if subject.startswith("docs(governance):") or subject.startswith("governance("):
        return "governance"
    if subject.startswith("docs(") or subject.startswith("docs:"):
        return "docs"
    if subject.startswith(("feat(", "feat:", "fix(", "fix:", "refactor(", "refactor:")):
        return "runtime"
    return "unknown"


def _is_late_execplan_progress_commit(
    *,
    commit_class: str,
    commit_files: list[str],
    changed_lines: int,
    active_execplan_path: str,
) -> bool:
    if commit_class != "execplan":
        return False
    if not active_execplan_path:
        return False
    if commit_files != [active_execplan_path]:
        return False
    return changed_lines <= BOUNDED_EXECPLAN_MAX_LINES


def _git_show_text(cwd: Path, ref: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout


def _frontmatter_changed_keys(before_text: str, after_text: str) -> set[str]:
    before_frontmatter, _ = parse_frontmatter(before_text)
    after_frontmatter, _ = parse_frontmatter(after_text)
    keys = set(before_frontmatter) | set(after_frontmatter)
    return {key for key in keys if before_frontmatter.get(key) != after_frontmatter.get(key)}


def _changes_field_is_additive_or_stale_replacement(before_text: str, after_text: str, *, cwd: Path) -> bool:
    before_frontmatter, _ = parse_frontmatter(before_text)
    after_frontmatter, _ = parse_frontmatter(after_text)
    before_changes = before_frontmatter.get("changes", [])
    after_changes = after_frontmatter.get("changes", [])
    if not isinstance(before_changes, list) or not isinstance(after_changes, list):
        return False
    before_set = {str(item).strip() for item in before_changes if str(item).strip()}
    after_set = {str(item).strip() for item in after_changes if str(item).strip()}
    removed_paths = before_set - after_set
    return all(not (cwd / path).exists() for path in removed_paths)


def _is_bounded_execplan_reconciliation(
    *,
    cwd: Path,
    commit: str,
    commit_class: str,
    commit_files: list[str],
    changed_lines: int,
    active_execplan_path: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not _is_late_execplan_progress_commit(
        commit_class=commit_class,
        commit_files=commit_files,
        changed_lines=changed_lines,
        active_execplan_path=active_execplan_path,
    ):
        return False, reasons

    before_text = _git_show_text(cwd, f"{commit}^", active_execplan_path)
    after_text = _git_show_text(cwd, commit, active_execplan_path)
    if not before_text or not after_text:
        return False, ["missing_execplan_commit_context"]

    changed_keys = _frontmatter_changed_keys(before_text, after_text)
    disallowed_keys = sorted(changed_keys - BOUNDED_EXECPLAN_FRONTMATTER_FIELDS)
    if disallowed_keys:
        reasons.extend(f"disallowed_frontmatter_change:{key}" for key in disallowed_keys)
        return False, reasons
    if "changes" in changed_keys and not _changes_field_is_additive_or_stale_replacement(
        before_text,
        after_text,
        cwd=cwd,
    ):
        reasons.append("changes_field_not_additive")
        return False, reasons
    return True, reasons


def _is_bounded_policy_repair_commit(
    *,
    subject: str,
    commit_class: str,
    commit_files: list[str],
    changed_lines: int,
    active_execplan_path: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if commit_class not in {"runtime", "test", "governance"}:
        return False, reasons
    if not subject.startswith(BOUNDED_POLICY_REPAIR_SUBJECT_PREFIXES):
        return False, reasons
    if changed_lines > BOUNDED_POLICY_REPAIR_MAX_LINES:
        reasons.append(f"changed_lines_exceeded:{changed_lines}")
        return False, reasons
    if len(commit_files) > BOUNDED_POLICY_REPAIR_MAX_FILES:
        reasons.append(f"file_count_exceeded:{len(commit_files)}")
        return False, reasons
    allowed_files = set(BOUNDED_POLICY_REPAIR_ALLOWED_FILES)
    if active_execplan_path:
        allowed_files.add(active_execplan_path)
    disallowed_files = sorted(set(commit_files) - allowed_files)
    if disallowed_files:
        reasons.extend(f"disallowed_file:{path}" for path in disallowed_files)
        return False, reasons
    return True, reasons


def _is_bounded_branch_reconciliation_commit(
    *,
    subject: str,
    commit_class: str,
    commit_files: list[str],
    changed_lines: int,
    active_execplan_path: str,
) -> bool:
    if commit_class != "governance":
        return False
    if not subject.startswith(BOUNDED_BRANCH_RECONCILIATION_SUBJECT_PREFIXES):
        return False
    if changed_lines > BOUNDED_BRANCH_RECONCILIATION_MAX_LINES:
        return False
    allowed_files = {GRAPH_PATH, QUEUE_PATH}
    if active_execplan_path:
        allowed_files.add(active_execplan_path)
    commit_file_set = set(commit_files)
    return {GRAPH_PATH, QUEUE_PATH}.issubset(commit_file_set) and commit_file_set.issubset(allowed_files)


def _repo_relative_path(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


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
        if commit_class != "unknown" and class_order < max_seen:
            allowed_execplan_reconciliation, reconciliation_reasons = _is_bounded_execplan_reconciliation(
                cwd=cwd,
                commit=commit,
                commit_class=commit_class,
                commit_files=commit_files,
                changed_lines=changed_lines,
                active_execplan_path=active_execplan_path,
            )
            allowed_policy_repair, policy_repair_reasons = _is_bounded_policy_repair_commit(
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
                errors.extend(f"execplan_reconciliation_violation:{commit}:{reason}" for reason in reconciliation_reasons)
                errors.extend(f"policy_repair_violation:{commit}:{reason}" for reason in policy_repair_reasons)
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


def _graph_node_for_execplan(cwd: Path, execplan_id: str) -> dict[str, Any] | None:
    graph = _load_json(cwd / GRAPH_PATH)
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if str(node.get("target_execplan_id", "")).strip() == execplan_id:
            return node
    return None


def _queue_has_execplan(cwd: Path, execplan_id: str) -> bool:
    queue_path = cwd / QUEUE_PATH
    if not queue_path.exists():
        return False
    return execplan_id in queue_path.read_text(encoding="utf-8")


def _branch_is_aligned_with_base(cwd: Path, base_ref: str) -> tuple[bool, str, str]:
    merge_base = _merge_base(cwd, base_ref)
    base_head = _git(cwd, "rev-parse", base_ref)
    return merge_base == base_head, merge_base, base_head


def _ref_exists(cwd: Path, ref: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _is_ancestor(cwd: Path, ancestor_ref: str, descendant_ref: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_ref, descendant_ref],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def _active_branch_rewrite_exception(cwd: Path, branch: str) -> str | None:
    registry = _load_yaml(cwd / EXCEPTION_REGISTRY_PATH)
    exceptions = registry.get("exceptions", [])
    if not isinstance(exceptions, list):
        return None
    now = datetime.now(timezone.utc)
    allowed_scopes = {f"branch_rewrite:{branch}", f"history_rewrite:{branch}"}
    for item in exceptions:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        scope = str(item.get("scope", "")).strip()
        if status != "active" or scope not in allowed_scopes:
            continue
        expires = _parse_iso8601(str(item.get("expires_at", "")))
        if expires is not None and expires < now:
            continue
        return str(item.get("id", "")).strip() or scope
    return None


def _active_commit_hard_limit_exception(cwd: Path, branch: str, commit: str) -> str | None:
    registry = _load_yaml(cwd / EXCEPTION_REGISTRY_PATH)
    exceptions = registry.get("exceptions", [])
    if not isinstance(exceptions, list):
        return None
    now = datetime.now(timezone.utc)
    allowed_scopes = {
        f"commit_hard_limit:{branch}",
        f"commit_hard_limit:{branch}:{commit}",
    }
    for item in exceptions:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        scope = str(item.get("scope", "")).strip()
        if status != "active" or scope not in allowed_scopes:
            continue
        expires = _parse_iso8601(str(item.get("expires_at", "")))
        if expires is not None and expires < now:
            continue
        return str(item.get("id", "")).strip() or scope
    return None


def _published_branch_rewrite_status(cwd: Path, branch: str) -> dict[str, Any]:
    remote_ref = f"refs/remotes/origin/{branch}"
    if not branch or not _ref_exists(cwd, remote_ref):
        return {
            "published_ref_exists": False,
            "remote_ref": remote_ref,
            "remote_head": "",
            "local_head": _git(cwd, "rev-parse", "HEAD"),
            "ok": True,
            "non_fast_forward": False,
            "authorized_exception_id": "",
        }

    remote_head = _git(cwd, "rev-parse", remote_ref)
    local_head = _git(cwd, "rev-parse", "HEAD")
    non_fast_forward = not _is_ancestor(cwd, remote_ref, "HEAD")
    exception_id = _active_branch_rewrite_exception(cwd, branch) if non_fast_forward else None
    ok = not non_fast_forward or bool(exception_id)
    return {
        "published_ref_exists": True,
        "remote_ref": remote_ref,
        "remote_head": remote_head,
        "local_head": local_head,
        "ok": ok,
        "non_fast_forward": non_fast_forward,
        "authorized_exception_id": exception_id or "",
    }


def _requires_published_implementation_branch(branch: str) -> bool:
    return bool(branch) and branch.startswith("impl-execplan/")


def check_policy_compliance(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    branch = _current_branch(cwd)
    plan_path = Path(execplan_path) if execplan_path else _discover_execplan(cwd, base_ref)
    parsed = parse_plan(plan_path)
    execplan_id = str(parsed.frontmatter.get("id", "")).strip()
    changed_files = _changed_files(cwd, base_ref)
    commit_stack, commit_errors, commit_warnings = _commit_reports(
        cwd,
        base_ref,
        active_execplan_path=_repo_relative_path(plan_path, root=cwd),
    )
    dirty_artifacts = _dirty_generated_artifacts(cwd)
    branch_aligned, merge_base, base_head = _branch_is_aligned_with_base(cwd, base_ref)
    rewrite_guard = _published_branch_rewrite_status(cwd, branch)
    remaining_work_code, remaining_work_report = check_remaining_work_graph(
        root=root,
        branch=branch,
        execplan_path=plan_path.as_posix(),
    )
    anti_cheat_code, anti_cheat_report = check_anti_cheat(
        root=root,
        execplan_path=plan_path.as_posix(),
        base_ref=base_ref,
    )

    graph_node = _graph_node_for_execplan(cwd, execplan_id)
    queue_has_execplan = _queue_has_execplan(cwd, execplan_id)

    blockers: list[str] = []
    if not branch_aligned:
        blockers.append("latest_main_branching_violation")
    if _requires_published_implementation_branch(branch) and not rewrite_guard["published_ref_exists"]:
        blockers.append("implementation_branch_not_published")
    if not rewrite_guard["ok"]:
        blockers.append("published_branch_history_rewrite_violation")
    if dirty_artifacts:
        blockers.append("dirty_generated_artifacts")
    blockers.extend(commit_errors)
    if remaining_work_code != 0:
        blockers.extend(f"remaining_work_graph:{item}" for item in remaining_work_report.get("errors", []))
    if anti_cheat_code != 0:
        blockers.extend(f"anti_cheat:{item}" for item in anti_cheat_report.get("blockers", []))

    if graph_node is None:
        blockers.append(f"missing_remaining_work_node:{execplan_id}")
    else:
        node_status = str(graph_node.get("status", "")).strip()
        implementation_branch = str(graph_node.get("implementation_branch", "")).strip()
        if implementation_branch and implementation_branch != branch:
            blockers.append(f"implementation_branch_mismatch:{implementation_branch}")
        if node_status == "completed":
            blockers.append(f"remaining_work_node_already_completed:{execplan_id}")
        if node_status not in {"ready", "review_gated"}:
            blockers.append(f"remaining_work_node_not_advancable:{node_status}")
        active_node = remaining_work_report.get("active_node") or {}
        if active_node and bool(active_node.get("action_state", {}).get("action_required", False)):
            blockers.append("active_slice_requires_graph_action")

    if GRAPH_PATH not in changed_files:
        blockers.append("graph_action_required")
    if QUEUE_PATH not in changed_files:
        blockers.append("queued_execplans_update_required")
    if not queue_has_execplan:
        blockers.append(f"queue_missing_execplan:{execplan_id}")

    next_actions: list[dict[str, str]] = []
    if blockers:
        next_actions.append({"action": "resolve_policy_blockers", "reason": "policy_compliance_blocked"})
    else:
        next_actions.append({"action": "allow_downstream_referees", "reason": "policy_compliance_passed"})

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "branch": branch,
        "base_ref": base_ref,
        "execplan_id": execplan_id,
        "execplan_path": plan_path.as_posix(),
        "blockers": sorted(set(blockers)),
        "next_actions": next_actions,
        "checks": {
            "branch_alignment": {
                "ok": branch_aligned,
                "merge_base": merge_base,
                "base_head": base_head,
            },
            "branch_rewrite_guard": rewrite_guard,
            "graph_binding": {
                "ok": graph_node is not None and remaining_work_code == 0,
                "graph_path": GRAPH_PATH,
                "queue_path": QUEUE_PATH,
                "node": graph_node or {},
                "queue_has_execplan": queue_has_execplan,
                "changed_files_include_graph": GRAPH_PATH in changed_files,
                "changed_files_include_queue": QUEUE_PATH in changed_files,
                "remaining_work_status": remaining_work_report.get("status", ""),
                "ready_order": remaining_work_report.get("ordering", {}).get("ready_execplan_ids", []),
                "queue_projection": remaining_work_report.get("queue_projection", {}),
            },
            "anti_cheat": anti_cheat_report,
            "commit_structure": {
                "ok": not commit_errors,
                "commit_stack": commit_stack,
                "warnings": commit_warnings,
            },
            "clean_merge_state": {
                "ok": not dirty_artifacts,
                "dirty_generated_artifacts": dirty_artifacts,
            },
        },
        "warnings": sorted(set(commit_warnings)),
        "changed_files": changed_files,
        "evidence_refs": sorted(
            {
                plan_path.as_posix(),
                GRAPH_PATH,
                QUEUE_PATH,
                "docs/governance.md",
                "artifacts/planner/research/rule-graph.json",
            }
        ),
    }
    return (1 if blockers else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--execplan-path", default=None)
    parser.add_argument("--base-ref", default="main")
    args = parser.parse_args()
    code, report = check_policy_compliance(
        root=args.root,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
