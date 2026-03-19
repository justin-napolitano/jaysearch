from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.plan_utils import (
    REQUIRED_FRONTMATTER_FIELDS,
    REQUIRED_HEADINGS,
    VALID_STATUS_VALUES,
    list_execplans,
    parse_plan,
    timestamp_in_future,
)


def _heading_present(body: str, heading: str) -> bool:
    for line in body.splitlines():
        if line.strip().startswith("#") and line.strip("#").strip() == heading:
            return True
    return False


def _has_policy_compliance_validation(frontmatter: dict[str, Any], plan_path: Path) -> bool:
    validation = frontmatter.get("validation", {})
    if not isinstance(validation, dict):
        return False
    tests = validation.get("tests", [])
    if not isinstance(tests, list):
        return False
    expected_commands = {
        f"bin/policy-compliance-check --execplan-path {plan_path.as_posix()}",
    }
    try:
        relative_plan_path = plan_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        expected_commands.add(f"bin/policy-compliance-check --execplan-path {relative_plan_path}")
    except ValueError:
        pass
    for item in tests:
        if not isinstance(item, dict):
            continue
        command = str(item.get("command", "")).strip()
        if command in expected_commands:
            return True
    return False


def validate_execplan(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    parsed = parse_plan(p)
    errors: list[str] = []
    warnings: list[str] = []
    frontmatter = parsed.frontmatter
    body = parsed.body
    current_branch = get_current_branch()

    for heading in REQUIRED_HEADINGS:
        if not _heading_present(body, heading):
            errors.append(f"missing_heading:{heading}")

    if not frontmatter:
        errors.append("missing_frontmatter")
    else:
        for field in REQUIRED_FRONTMATTER_FIELDS:
            if field not in frontmatter:
                errors.append(f"missing_frontmatter_field:{field}")

        status = frontmatter.get("status")
        if status and status not in VALID_STATUS_VALUES:
            errors.append(f"invalid_status:{status}")

        if frontmatter.get("status") == "draft":
            branch = frontmatter.get("draft_branch", "")
            if not isinstance(branch, str) or not branch.startswith("draft-execplan/"):
                errors.append("invalid_draft_branch")

        initiative_branch = str(frontmatter.get("initiative_branch", "")).strip()
        initiative_node_id = str(frontmatter.get("initiative_node_id", "")).strip()
        if initiative_branch or initiative_node_id:
            if not initiative_branch.startswith("initiative/"):
                errors.append("invalid_initiative_branch")
            if not initiative_node_id:
                errors.append("missing_initiative_node_id")

        registration = frontmatter.get("graph_registration")
        if registration is not None:
            if not isinstance(registration, dict):
                errors.append("invalid_graph_registration")
            else:
                node_id = str(registration.get("node_id", "")).strip()
                goal_area = str(registration.get("goal_area", "")).strip()
                queue_position = registration.get("queue_position")
                conflict_domains = registration.get("conflict_domains")
                expected_artifacts = registration.get("expected_artifacts")
                implementation_branch = str(registration.get("implementation_branch", "")).strip()
                integration_mode = str(registration.get("integration_mode", "")).strip()
                if not node_id:
                    errors.append("missing_graph_registration_node_id")
                if not goal_area:
                    errors.append("missing_graph_registration_goal_area")
                if not isinstance(queue_position, int):
                    errors.append("missing_graph_registration_queue_position")
                if not isinstance(conflict_domains, list) or not conflict_domains:
                    errors.append("missing_graph_registration_conflict_domains")
                if not isinstance(expected_artifacts, list) or not expected_artifacts:
                    errors.append("missing_graph_registration_expected_artifacts")
                if implementation_branch and not implementation_branch.startswith("impl-execplan/"):
                    errors.append("invalid_graph_registration_implementation_branch")
                if integration_mode and integration_mode not in {"via_initiative", "direct_to_main_hotfix", "direct_to_main_patch"}:
                    errors.append("invalid_graph_registration_integration_mode")
                if implementation_branch and not integration_mode:
                    errors.append("missing_graph_registration_integration_mode")
                if integration_mode == "via_initiative":
                    if not initiative_branch:
                        errors.append("missing_initiative_branch")
                    if not initiative_node_id:
                        errors.append("missing_initiative_node_id")

        if (
            isinstance(current_branch, str)
            and current_branch.startswith("impl-execplan/")
            and not _has_policy_compliance_validation(frontmatter, p)
        ):
            errors.append("missing_policy_compliance_validation")

        changes = frontmatter.get("changes")
        if not isinstance(changes, list) or len(changes) == 0:
            errors.append("invalid_changes")

        tasks = frontmatter.get("tasks")
        if isinstance(tasks, list) and len(tasks) > 20:
            errors.append("task_limit_exceeded")

        for ts_field in ("created", "draft_created", "finalized_at"):
            value = frontmatter.get(ts_field)
            if isinstance(value, str) and value and timestamp_in_future(value):
                errors.append(f"timestamp_too_far_in_future:{ts_field}")

        plan_id = frontmatter.get("id")
        if isinstance(plan_id, str) and plan_id:
            if plan_id not in p.name:
                warnings.append("filename_not_aligned_with_id")

    return {
        "plan": p.as_posix(),
        "id": frontmatter.get("id") if isinstance(frontmatter, dict) else None,
        "errors": sorted(errors),
        "warnings": sorted(warnings),
    }


def run(paths: list[str]) -> tuple[int, dict[str, Any]]:
    file_paths: list[Path]
    if paths:
        file_paths = sorted(Path(p) for p in paths)
    else:
        file_paths = list_execplans()

    results = [validate_execplan(path) for path in file_paths]
    error_count = sum(len(item["errors"]) for item in results)
    warning_count = sum(len(item["warnings"]) for item in results)
    branch_policy = evaluate_branch_policy(get_current_branch())
    if not branch_policy["ok"]:
        error_count += 1

    report = {
        "tool": "execplan_lint",
        "files_checked": len(results),
        "error_count": error_count,
        "warning_count": warning_count,
        "branch_policy": branch_policy,
        "results": results,
    }
    return (1 if error_count else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    exit_code, report = run(args.paths)
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
