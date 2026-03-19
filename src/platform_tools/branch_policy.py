from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

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


def _initiative_findings(branch: str) -> list[str]:
    if not branch.startswith("initiative/"):
        return []

    workflow_path = Path("spec/workflow.yaml")
    graph_path = Path("artifacts/planner/research/remaining-work-graph.json")
    if not workflow_path.exists():
        return ["branch_policy_violation:initiative_policy_missing"]
    if not graph_path.exists():
        return ["branch_policy_violation:initiative_graph_missing"]

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
    if not isinstance(workflow, dict):
        return ["branch_policy_violation:initiative_policy_invalid"]
    requirements = (
        workflow.get("execution_requirements", {}).get("initiative_requirements", {})
        if isinstance(workflow.get("execution_requirements", {}), dict)
        else {}
    )
    if not isinstance(requirements, dict) or not requirements.get("fail_closed_on_missing_initiative_mapping", False):
        return []

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", []) if isinstance(graph.get("nodes", []), list) else []
    matches = [
        node for node in nodes if isinstance(node, dict) and str(node.get("initiative_branch", "")).strip() == branch
    ]
    if not matches:
        return ["branch_policy_violation:initiative_parent_graph_node_missing"]
    parent_matches = [
        node
        for node in matches
        if str(node.get("node_id", "")).strip() == str(node.get("parent_initiative_node", "")).strip()
        or str(node.get("node_id", "")).strip().startswith("initiative-")
    ]
    if len(parent_matches) != 1:
        return ["branch_policy_violation:initiative_parent_graph_node_ambiguous"]
    return []


def _implementation_findings(branch: str) -> list[str]:
    if not branch.startswith("impl-execplan/"):
        return []

    workflow_path = Path("spec/workflow.yaml")
    graph_path = Path("artifacts/planner/research/remaining-work-graph.json")
    if not workflow_path.exists() or not graph_path.exists():
        return []

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
    if not isinstance(workflow, dict):
        return []
    requirements = (
        workflow.get("execution_requirements", {}).get("initiative_requirements", {})
        if isinstance(workflow.get("execution_requirements", {}), dict)
        else {}
    )
    if not isinstance(requirements, dict) or not requirements.get("normal_governed_work_requires_initiative_branch", False):
        return []

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", []) if isinstance(graph.get("nodes", []), list) else []
    matches = [
        node for node in nodes if isinstance(node, dict) and str(node.get("implementation_branch", "")).strip() == branch
    ]
    if not matches:
        return ["branch_policy_violation:implementation_graph_node_missing"]
    if len(matches) > 1:
        return ["branch_policy_violation:implementation_graph_node_ambiguous"]

    node = matches[0]
    integration_mode = str(node.get("integration_mode", "")).strip()
    if integration_mode != "via_initiative":
        if integration_mode in {"direct_to_main_hotfix", "direct_to_main_patch"}:
            return ["branch_policy_violation:direct_to_main_mode_not_allowed_on_impl_branch"]
        return ["branch_policy_violation:implementation_integration_mode_missing"]
    findings: list[str] = []
    if not str(node.get("initiative_branch", "")).strip():
        findings.append("branch_policy_violation:implementation_initiative_branch_missing")
    parent_initiative_node = str(node.get("parent_initiative_node", "")).strip()
    if not parent_initiative_node:
        findings.append("branch_policy_violation:implementation_parent_initiative_missing")
    else:
        parent_matches = [
            item
            for item in nodes
            if isinstance(item, dict) and str(item.get("node_id", "")).strip() == parent_initiative_node
        ]
        if len(parent_matches) != 1:
            findings.append("branch_policy_violation:implementation_parent_initiative_not_found")
        else:
            parent_branch = str(parent_matches[0].get("initiative_branch", "")).strip()
            if parent_branch != str(node.get("initiative_branch", "")).strip():
                findings.append("branch_policy_violation:implementation_parent_initiative_branch_mismatch")
    return findings


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
    initiative_findings = _initiative_findings(branch)
    if initiative_findings:
        ok = False
        findings.extend(initiative_findings)
    implementation_findings = _implementation_findings(branch)
    if implementation_findings:
        ok = False
        findings.extend(implementation_findings)
    return {
        "ok": ok,
        "current_branch": branch,
        "forbidden_branches": sorted(forbidden),
        "allowed_branch_patterns": allowed_patterns,
        "findings": findings,
    }
