from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from platform_tools.plan_utils import parse_plan
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "anti-cheat-check"
POLICY_PATH = "spec/agent-capability-policy.yaml"
SURFACES_PATH = "spec/protected-surfaces.schema.yaml"
EXCEPTION_REGISTRY_PATH = ".agent/governance/exceptions.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


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
    return sorted(line.strip() for line in output.splitlines() if line.strip())


def _branch_class(branch: str) -> str:
    if branch.startswith("impl-execplan/"):
        return "impl_execplan"
    if branch.startswith("draft-execplan/"):
        return "draft_execplan"
    if branch.startswith("queue-execplan/"):
        return "queue_execplan"
    return "other"


def _goal_area_class(goal_area: str) -> str:
    return "governance" if goal_area == "governance" else "non_governance"


def _match_surface(path: str, entries: list[dict[str, Any]]) -> dict[str, str]:
    best: dict[str, str] | None = None
    best_score = -1
    for entry in entries:
        entry_id = str(entry.get("id", "")).strip()
        surface_class = str(entry.get("surface_class", "")).strip()
        for exact in entry.get("path_exact", []) if isinstance(entry.get("path_exact"), list) else []:
            exact_path = str(exact).strip()
            if path == exact_path and len(exact_path) > best_score:
                best = {"surface_id": entry_id, "surface_class": surface_class, "match_type": "exact"}
                best_score = len(exact_path)
        for prefix in entry.get("path_prefixes", []) if isinstance(entry.get("path_prefixes"), list) else []:
            prefix_path = str(prefix).strip()
            if prefix_path and path.startswith(prefix_path) and len(prefix_path) > best_score:
                best = {"surface_id": entry_id, "surface_class": surface_class, "match_type": "prefix"}
                best_score = len(prefix_path)
    if best is None:
        return {"surface_id": "unclassified", "surface_class": "unclassified_surface", "match_type": "none"}
    return best


def _extract_value(data: dict[str, Any], dotted_path: str) -> str:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
    return str(current).strip() if current is not None else ""


def _projection_authority_blockers(cwd: Path, policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for rule in policy.get("denial_rules", []):
        if not isinstance(rule, dict) or str(rule.get("id", "")).strip() != "github_authority_promotion":
            continue
        for raw in rule.get("required_projection_only_fields", []):
            if not isinstance(raw, str) or ":" not in raw:
                continue
            path_text, dotted = raw.split(":", 1)
            path = cwd / path_text
            if not path.exists():
                continue
            value = _extract_value(_load_yaml(path), dotted)
            if value != "projection_only":
                blockers.append(str(rule.get("blocker", "github_authority_promotion_denied")))
    return blockers


def _active_rule(policy: dict[str, Any], *, actor_class: str, branch_class: str, goal_area_class: str) -> dict[str, Any] | None:
    for rule in policy.get("capability_rules", []):
        if not isinstance(rule, dict):
            continue
        if (
            str(rule.get("actor_class", "")).strip() == actor_class
            and str(rule.get("branch_class", "")).strip() == branch_class
            and str(rule.get("goal_area_class", "")).strip() == goal_area_class
        ):
            return rule
    return None


def check_anti_cheat(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    base_ref: str = "main",
    actor_class: str = "agent",
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    policy_path = cwd / POLICY_PATH
    surfaces_path = cwd / SURFACES_PATH
    if not policy_path.exists() or not surfaces_path.exists():
        report = {
            "command": COMMAND,
            "status": "deferred",
            "ok": True,
            "blockers": [],
            "warnings": ["anti_cheat_contract_not_installed"],
            "evidence_refs": [path.as_posix() for path in (policy_path, surfaces_path) if path.exists()],
        }
        return 0, report

    try:
        branch = _git(cwd, "branch", "--show-current")
    except RuntimeError:
        branch = ""
    parsed = parse_plan(Path(execplan_path)) if execplan_path else None
    execplan_changes = set()
    if parsed is not None:
        changes = parsed.frontmatter.get("changes", [])
        if isinstance(changes, list):
            execplan_changes = {str(item).strip() for item in changes if str(item).strip()}

    _, remaining_report = check_remaining_work_graph(root=root, branch=branch, execplan_path=execplan_path)
    active_node = remaining_report.get("active_node") or {}
    goal_area = str(active_node.get("goal_area", "")).strip()

    policy = _load_yaml(policy_path)
    surfaces = _load_yaml(surfaces_path)
    surface_entries = surfaces.get("surface_entries", [])
    if not isinstance(surface_entries, list):
        surface_entries = []

    branch_class = _branch_class(branch)
    goal_class = _goal_area_class(goal_area)
    rule = _active_rule(policy, actor_class=actor_class, branch_class=branch_class, goal_area_class=goal_class)
    changed_files = _changed_files(cwd, base_ref)

    blockers: list[str] = []
    warnings: list[str] = []
    if rule is None:
        blockers.append(f"missing_capability_rule:{actor_class}:{branch_class}:{goal_class}")
        rule = {}

    allowed_surface_classes = {
        str(item).strip() for item in rule.get("allowed_surface_classes", []) if str(item).strip()
    }
    forbidden_surface_classes = {
        str(item).strip() for item in rule.get("forbidden_surface_classes", []) if str(item).strip()
    }
    allowed_referee_paths = {
        str(item).strip() for item in rule.get("allowed_referee_paths", []) if str(item).strip()
    }
    require_declared = bool(rule.get("requires_execplan_declaration_for_protected_surfaces", False))

    surface_matches: list[dict[str, str]] = []
    for path in changed_files:
        match = _match_surface(path, surface_entries)
        surface_matches.append({"path": path, **match})
        surface_class = match["surface_class"]
        if surface_class == "unclassified_surface":
            warnings.append(f"unclassified_surface:{path}")
            continue
        if surface_class in forbidden_surface_classes:
            blocker = "protected_surface_denied"
            if surface_class == "exception_registry":
                blocker = "agent_exception_self_authorization_denied"
            blockers.append(f"{blocker}:{path}:{surface_class}")
        if surface_class == "referee_surface" and allowed_referee_paths and path not in allowed_referee_paths:
            blockers.append(f"referee_surface_outside_allowlist:{path}")
        if require_declared and surface_class in {
            "rule_surface",
            "referee_surface",
            "capability_policy_surface",
            "exception_registry",
        } and path not in execplan_changes:
            blockers.append(f"protected_surface_not_declared:{path}")
        if surface_class not in allowed_surface_classes and surface_class not in forbidden_surface_classes:
            warnings.append(f"surface_class_not_explicitly_ruled:{path}:{surface_class}")

    blockers.extend(_projection_authority_blockers(cwd, policy))

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "branch": branch,
        "actor_class": actor_class,
        "branch_class": branch_class,
        "goal_area_class": goal_class,
        "goal_area": goal_area,
        "active_node": active_node,
        "changed_files": changed_files,
        "capability_rule_id": str(rule.get("id", "")).strip(),
        "surface_matches": surface_matches,
        "evidence_refs": [
            policy_path.as_posix(),
            surfaces_path.as_posix(),
            EXCEPTION_REGISTRY_PATH,
            "spec/board-action-api.yaml",
            "spec/governance.yaml",
        ],
    }
    return (0 if not blockers else 1), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check anti-cheat capability boundaries for the active slice.")
    parser.add_argument("--execplan-path")
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--actor-class", default="agent")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    code, report = check_anti_cheat(
        root=args.root,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
        actor_class=args.actor_class,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
