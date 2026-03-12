from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.game_graph_check import check_game_graph
from platform_tools.plan_utils import parse_plan


def _git(cwd: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    output = proc.stdout.strip() if proc.stdout else proc.stderr.strip()
    return proc.returncode, output


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return loaded if isinstance(loaded, dict) else {}


def _evaluate_branch_policy_at_root(root: Path, branch: str) -> dict[str, Any]:
    previous = Path.cwd()
    os.chdir(root)
    try:
        return evaluate_branch_policy(branch)
    finally:
        os.chdir(previous)


def _graph_nodes_by_id(root: Path) -> dict[str, dict[str, Any]]:
    graph_path = root / "artifacts" / "planner" / "research" / "game-graph.json"
    graph = _load_json(graph_path)
    nodes = graph.get("nodes", [])
    return {
        str(node.get("id")): node
        for node in nodes
        if isinstance(node, dict) and str(node.get("id", "")).strip()
    }


def _contains_parents(root: Path) -> dict[str, str]:
    graph_path = root / "artifacts" / "planner" / "research" / "game-graph.json"
    graph = _load_json(graph_path)
    parents: dict[str, str] = {}
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        if edge.get("relation") == "contains":
            parents[str(edge.get("to", ""))] = str(edge.get("from", ""))
    return parents


def _game_spec_for_id(root: Path, game_id: str) -> dict[str, Any]:
    graph_path = root / "artifacts" / "planner" / "research" / "game-graph.json"
    graph = _load_json(graph_path)
    for node in graph.get("nodes", []):
        if not isinstance(node, dict) or str(node.get("id", "")).strip() != game_id:
            continue
        spec_path = str(node.get("spec_path", "")).strip()
        if not spec_path:
            return {}
        path = root / spec_path
        if not path.exists():
            return {}
        return _load_json(path) if path.suffix == ".json" else parse_plan(path).frontmatter if path.suffix == ".md" else _load_yaml(path)
    return {}


def _lineage(game_id: str, parents: dict[str, str]) -> list[str]:
    lineage: list[str] = []
    current = game_id
    while current:
        lineage.append(current)
        current = parents.get(current, "")
    return list(reversed(lineage))


def _discover_execplan(root: Path, branch: str, base_ref: str) -> tuple[str | None, list[str], str]:
    execplan_dir = root / ".agent" / "execplans"
    matches_by_branch: list[str] = []
    if execplan_dir.exists():
        for path in sorted(execplan_dir.glob("*.md")):
            parsed = parse_plan(path)
            draft_branch = str(parsed.frontmatter.get("draft_branch", "")).strip()
            if draft_branch and draft_branch == branch:
                matches_by_branch.append(path.as_posix())
    if len(matches_by_branch) == 1:
        return matches_by_branch[0], matches_by_branch, "draft_branch"
    if len(matches_by_branch) > 1:
        return None, matches_by_branch, "ambiguous_draft_branch"

    code, output = _git(root, "diff", "--name-only", base_ref + "...HEAD", "--", ".agent/execplans")
    if code != 0:
        return None, [], "git_diff_failed"
    changed = sorted(line.strip() for line in output.splitlines() if line.strip())
    if len(changed) == 1:
        return (root / changed[0]).as_posix(), changed, "changed_files"
    if len(changed) > 1:
        return None, changed, "ambiguous_changed_files"
    return None, [], "not_found"


def get_game_status(
    *,
    root: str = ".",
    branch: str | None = None,
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    current_branch = branch or get_current_branch()
    graph_code, graph_report = check_game_graph(root)
    nodes = _graph_nodes_by_id(cwd) if graph_report.get("ok") else {}
    parents = _contains_parents(cwd) if graph_report.get("ok") else {}
    branch_report = _evaluate_branch_policy_at_root(cwd, current_branch)

    blockers: list[str] = []
    blockers.extend(str(item) for item in graph_report.get("errors", []) if str(item).strip())
    blockers.extend(str(item) for item in branch_report.get("findings", []) if str(item).strip())

    discovery_strategy = "explicit"
    discovery_candidates: list[str] = []
    selected_execplan_path = execplan_path
    if selected_execplan_path is None:
        selected_execplan_path, discovery_candidates, discovery_strategy = _discover_execplan(
            cwd, current_branch, base_ref
        )
        if discovery_strategy.startswith("ambiguous_"):
            blockers.append(f"active_execplan_not_deterministic:{discovery_strategy}")

    active_execplan: dict[str, Any] | None = None
    active_game_id = "game-platform"
    active_game_reason = "fallback_platform_scope"
    if selected_execplan_path:
        plan_path = Path(selected_execplan_path)
        parsed = parse_plan(plan_path)
        active_execplan = {
            "id": str(parsed.frontmatter.get("id", "")).strip(),
            "path": plan_path.as_posix(),
            "status": str(parsed.frontmatter.get("status", "")).strip(),
            "title": str(parsed.frontmatter.get("title", "")).strip(),
        }
        active_game_id = "game-implementation"
        active_game_reason = "active_execplan_detected"
    elif current_branch.startswith("draft-execplan/"):
        active_game_id = "game-execplan"
        active_game_reason = "draft_execplan_branch_without_explicit_execplan"
    elif not branch_report.get("ok", False):
        active_game_reason = "branch_policy_blocked"

    active_node = nodes.get(active_game_id, {})
    active_spec = _game_spec_for_id(cwd, active_game_id) if active_node else {}
    lineage = _lineage(active_game_id, parents) if active_node else [active_game_id]

    if graph_code != 0 or not branch_report.get("ok", False):
        ok = False
    else:
        ok = True

    report = {
        "tool": "game_status",
        "ok": ok,
        "branch": current_branch,
        "base_ref": base_ref,
        "graph": {
            "graph_id": graph_report.get("graph_id", ""),
            "ok": bool(graph_report.get("ok", False)),
        },
        "branch_policy": {
            "ok": bool(branch_report.get("ok", False)),
            "allowed_branch_patterns": branch_report.get("allowed_branch_patterns", []),
            "forbidden_branches": branch_report.get("forbidden_branches", []),
            "findings": sorted(set(str(item) for item in branch_report.get("findings", []) if str(item).strip())),
        },
        "execplan_discovery": {
            "strategy": discovery_strategy,
            "candidates": discovery_candidates,
            "selected": selected_execplan_path or "",
        },
        "active_execplan": active_execplan,
        "active_game": {
            "id": active_game_id,
            "label": str(active_node.get("label", "")).strip(),
            "title": str(active_node.get("title", "")).strip(),
            "layer": str(active_node.get("layer", "")).strip(),
            "scope": str(active_node.get("scope", "")).strip(),
            "referee_order": active_spec.get("referee_order", []),
            "local_rule_focus": active_spec.get("local_rule_focus", []),
            "reason": active_game_reason,
            "lineage": lineage,
        },
        "blocker_count": len(sorted(set(blockers))),
        "blockers": sorted(set(blockers)),
    }
    return (1 if not ok else 0), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--base-ref", default="main")
    args = parser.parse_args()
    code, report = get_game_status(
        root=args.root,
        branch=args.branch,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
