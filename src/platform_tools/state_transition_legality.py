from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from platform_tools.anti_cheat_check import check_anti_cheat
from platform_tools.plan_utils import parse_plan
from platform_tools.remaining_work_graph_check import check_remaining_work_graph


COMMAND = "state-transition-legality-check"
BRANCH_CONTRACT_PATH = "spec/subgame-branch-contract.yaml"
SURFACES_PATH = "spec/protected-surfaces.schema.yaml"
GRAPH_PATH = "artifacts/planner/research/remaining-work-graph.json"


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git_command_failed:{' '.join(args)}")
    return proc.stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _merge_base(cwd: Path, base_ref: str) -> str:
    return _git(cwd, "merge-base", "HEAD", base_ref)


def _changed_files(cwd: Path, base_ref: str) -> list[str]:
    merge_base = _merge_base(cwd, base_ref)
    output = _git(cwd, "diff", "--name-only", f"{merge_base}..HEAD")
    return sorted(line.strip() for line in output.splitlines() if line.strip())


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


def _branch_role(branch: str, contract: dict[str, Any]) -> dict[str, Any] | None:
    for role in contract.get("branch_roles", []):
        if not isinstance(role, dict):
            continue
        for pattern in role.get("branch_patterns", []) if isinstance(role.get("branch_patterns"), list) else []:
            if fnmatch.fnmatch(branch, str(pattern).strip()):
                return role
    return None


def _graph_node_for_execplan(graph: dict[str, Any], execplan_id: str) -> dict[str, Any] | None:
    for node in graph.get("nodes", []):
        if isinstance(node, dict) and str(node.get("target_execplan_id", "")).strip() == execplan_id:
            return node
    return None


def _dependency_blockers(graph: dict[str, Any], node_id: str) -> list[str]:
    nodes = {
        str(node.get("node_id", "")).strip(): node
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and str(node.get("node_id", "")).strip()
    }
    blockers: list[str] = []
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        if str(edge.get("from", "")).strip() != node_id or str(edge.get("relation", "")).strip() != "depends_on":
            continue
        dep_id = str(edge.get("to", "")).strip()
        dep_node = nodes.get(dep_id, {})
        dep_status = str(dep_node.get("status", "")).strip()
        if dep_status != "completed":
            blockers.append(f"dependencies_incomplete:{dep_id}:{dep_status or 'missing'}")
    return blockers


def check_state_transition_legality(
    *,
    root: str = ".",
    execplan_path: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    cwd = Path(root)
    branch = _git(cwd, "branch", "--show-current")
    if execplan_path is None:
        raise RuntimeError("execplan_path_required")
    plan_path = Path(execplan_path)
    contract_path = cwd / BRANCH_CONTRACT_PATH
    surfaces_path = cwd / SURFACES_PATH
    graph_path = cwd / GRAPH_PATH
    if not contract_path.exists() or not surfaces_path.exists() or not graph_path.exists():
        report = {
            "command": COMMAND,
            "status": "deferred",
            "ok": True,
            "transition_id": "",
            "branch": branch,
            "branch_role": "unknown",
            "source_state": "unknown",
            "target_state": "state_transition_deferred",
            "active_node": {},
            "changed_files": _changed_files(cwd, base_ref),
            "declared_changes": [],
            "surface_matches": [],
            "decision": "accepted",
            "blockers": [],
            "warnings": ["state_transition_contract_not_installed"],
            "anti_cheat": {},
            "evidence_refs": [
                path.as_posix()
                for path in (contract_path, surfaces_path, graph_path)
                if path.exists()
            ],
        }
        return 0, report
    parsed = parse_plan(plan_path)
    execplan_id = str(parsed.frontmatter.get("id", "")).strip()
    declared_changes = sorted(
        str(item).strip()
        for item in parsed.frontmatter.get("changes", [])
        if str(item).strip()
    )

    contract = _load_yaml(contract_path)
    surfaces = _load_yaml(surfaces_path)
    graph = _load_json(graph_path)
    surface_entries = surfaces.get("surface_entries", [])
    if not isinstance(surface_entries, list):
        surface_entries = []

    changed_files = _changed_files(cwd, base_ref)
    _, remaining_report = check_remaining_work_graph(root=root, branch=branch, execplan_path=plan_path.as_posix())
    anti_cheat_code, anti_cheat_report = check_anti_cheat(
        root=root,
        execplan_path=plan_path.as_posix(),
        base_ref=base_ref,
    )

    active_node = remaining_report.get("active_node") or _graph_node_for_execplan(graph, execplan_id) or {}
    node_id = str(active_node.get("node_id", "")).strip()
    role = _branch_role(branch, contract)
    role_id = str(role.get("id", "")).strip() if role else "unknown"
    allowed_surface_classes = (
        {str(item).strip() for item in role.get("allowed_surface_classes", []) if str(item).strip()} if role else set()
    )
    handoff_paths = [str(item).strip() for item in role.get("handoff_paths", []) if str(item).strip()] if role else []
    requires_handoff = bool(role.get("requires_handoff", False)) if role else False

    blockers: list[str] = []
    warnings: list[str] = []
    if role is None:
        blockers.append(f"missing_branch_contract:{branch}")

    surface_matches: list[dict[str, str]] = []
    for path in changed_files:
        if path not in declared_changes:
            blockers.append(f"changed_file_not_declared:{path}")
        match = _match_surface(path, surface_entries)
        surface_matches.append({"path": path, **match})
        surface_class = match["surface_class"]
        if surface_class == "unclassified_surface":
            blockers.append(f"unknown_surface_class:{path}")
            continue
        if allowed_surface_classes and surface_class not in allowed_surface_classes:
            blockers.append(f"surface_outside_branch_scope:{path}:{surface_class}")

    if node_id:
        blockers.extend(_dependency_blockers(graph, node_id))
    else:
        warnings.append("active_node_not_resolved")

    if requires_handoff and not any(changed.startswith(prefix) for prefix in handoff_paths for changed in changed_files):
        blockers.append("missing_handoff_artifact")

    if anti_cheat_code != 0:
        blockers.extend(f"protected_surface_violation:{item}" for item in anti_cheat_report.get("blockers", []))

    head = _git(cwd, "rev-parse", "--short", "HEAD")
    source_state = str(active_node.get("status", "")).strip() or "unknown"
    decision = "accepted" if not blockers else "rejected"
    target_state = "state_transition_validated" if decision == "accepted" else "state_transition_blocked"
    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "transition_id": f"{execplan_id}:{branch}:{head}",
        "branch": branch,
        "branch_role": role_id,
        "source_state": source_state,
        "target_state": target_state,
        "active_node": active_node,
        "changed_files": changed_files,
        "declared_changes": declared_changes,
        "surface_matches": surface_matches,
        "decision": decision,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "anti_cheat": anti_cheat_report,
        "evidence_refs": sorted(
            {
                plan_path.as_posix(),
                BRANCH_CONTRACT_PATH,
                SURFACES_PATH,
                GRAPH_PATH,
                "spec/agent-capability-policy.yaml",
            }
        ),
    }
    return (0 if not blockers else 1), report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate branch state transitions for governed implementation work.")
    parser.add_argument("--execplan-path", required=True)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    code, report = check_state_transition_legality(
        root=args.root,
        execplan_path=args.execplan_path,
        base_ref=args.base_ref,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
