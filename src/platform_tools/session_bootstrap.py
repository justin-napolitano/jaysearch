from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import evaluate_branch_policy, get_current_branch
from platform_tools.execplan_discovery import discover_execplan
from platform_tools.plan_utils import parse_plan
from platform_tools.worker_contracts import contract_scope_findings, find_contract, load_registry, registry_path


COMMAND = "session-bootstrap-check"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
WORKER_LEASE_DIR = Path("artifacts/governance/worker-sessions")
WORKER_AUDIT_LOG = Path("artifacts/governance/worker-session-events.jsonl")
REQUIRED_BOOTSTRAP_ARTIFACTS = (
    ".agent/AGENTS.md",
    ".agent/PLANS.md",
    "spec/workflow.yaml",
)


def _required_artifact_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for rel in REQUIRED_BOOTSTRAP_ARTIFACTS:
        if not (root / rel).exists():
            findings.append(f"missing_bootstrap_artifact:{rel}")
    return findings


def _session_role(branch: str) -> str:
    if branch.startswith("initiative/"):
        return "initiative_coordinator"
    if branch.startswith("draft-execplan/"):
        return "draft_execplan_author"
    if branch.startswith("impl-execplan/"):
        return "implementation_worker"
    if branch.startswith("queue-execplan/"):
        return "queue_integration"
    return "unknown"


def _load_graph(root: Path) -> dict[str, Any]:
    return json.loads((root / GRAPH_PATH).read_text(encoding="utf-8"))


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _lease_path(*, root: Path, worker_id: str) -> Path:
    return root / WORKER_LEASE_DIR / f"{worker_id}.json"


def _load_worker_lease(*, root: Path, worker_id: str) -> dict[str, Any] | None:
    path = _lease_path(root=root, worker_id=worker_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _append_worker_audit_event(*, root: Path, record: dict[str, Any]) -> None:
    path = root / WORKER_AUDIT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(sorted(record.items())), sort_keys=True) + "\n")


def _matching_nodes(graph: dict[str, Any], *, branch: str, execplan_id: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        if branch and str(node.get("implementation_branch", "")).strip() == branch:
            matches.append(node)
            continue
        if execplan_id and str(node.get("target_execplan_id", "")).strip() == execplan_id:
            matches.append(node)
    deduped: dict[str, dict[str, Any]] = {}
    for node in matches:
        node_id = str(node.get("node_id", "")).strip() or json.dumps(node, sort_keys=True)
        deduped[node_id] = node
    return list(deduped.values())


def _initiative_mapping_findings(
    *,
    root: Path,
    branch: str,
    role: str,
    execplan_id: str,
) -> tuple[list[str], dict[str, Any] | None]:
    if not (root / GRAPH_PATH).exists():
        return ["missing_bootstrap_artifact:artifacts/planner/research/remaining-work-graph.json"], None
    graph = _load_graph(root)
    nodes = _matching_nodes(graph, branch=branch, execplan_id=execplan_id)
    if role == "implementation_worker":
        if not nodes:
            return ["bootstrap_violation:implementation_node_not_found"], None
        if len(nodes) > 1:
            return ["bootstrap_violation:implementation_node_ambiguous"], None
        node = nodes[0]
        findings: list[str] = []
        initiative_branch = str(node.get("initiative_branch", "")).strip()
        integration_mode = str(node.get("integration_mode", "")).strip()
        parent_node = str(node.get("parent_initiative_node", "")).strip()
        if integration_mode != "via_initiative":
            findings.append("bootstrap_violation:implementation_not_via_initiative")
        if not initiative_branch:
            findings.append("bootstrap_violation:initiative_branch_missing")
        if not parent_node:
            findings.append("bootstrap_violation:parent_initiative_missing")
        if initiative_branch and initiative_branch == "main":
            findings.append("bootstrap_violation:implementation_merge_target_main")
        return findings, node
    if role == "initiative_coordinator":
        initiative_nodes = [
            node for node in graph.get("nodes", []) if isinstance(node, dict) and str(node.get("initiative_branch", "")).strip() == branch
        ]
        if not initiative_nodes:
            return ["bootstrap_violation:initiative_node_not_found"], None
        parent_matches = [
            node
            for node in initiative_nodes
            if str(node.get("node_id", "")).strip() == str(node.get("parent_initiative_node", "")).strip()
            or str(node.get("node_id", "")).strip().startswith("initiative-")
        ]
        if len(parent_matches) != 1:
            return ["bootstrap_violation:initiative_node_ambiguous"], None
        return [], parent_matches[0]
    return [], None


def run_session_bootstrap_check(
    *,
    root: str = ".",
    branch: str | None = None,
    base_ref: str = "main",
    execplan_path: str | None = None,
    session_kind: str = "codex",
    worker_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    current_branch = branch or get_current_branch(root=root_path)
    role = _session_role(current_branch)
    blockers = _required_artifact_findings(root_path)

    branch_policy = evaluate_branch_policy(current_branch, root=root_path) if current_branch else {
        "ok": False,
        "current_branch": "",
        "allowed_branch_patterns": [],
        "forbidden_branches": [],
        "findings": ["branch_detection_failed"],
    }
    blockers.extend(str(item) for item in branch_policy.get("findings", []) if str(item).strip())

    selected_execplan_path = execplan_path
    discovery_strategy = "explicit" if execplan_path else "not_run"
    discovery_candidates: list[str] = []
    if selected_execplan_path is None and role in {"draft_execplan_author", "implementation_worker"}:
        selected, candidates, strategy = discover_execplan(root_path, current_branch, base_ref)
        discovery_strategy = strategy
        discovery_candidates = candidates
        if selected is None:
            blockers.append(f"active_execplan_not_deterministic:{strategy}")
        else:
            selected_execplan_path = selected.as_posix()

    execplan_summary: dict[str, Any] | None = None
    execplan_id = ""
    if selected_execplan_path:
        parsed = parse_plan(Path(selected_execplan_path))
        execplan_id = str(parsed.frontmatter.get("id", "")).strip()
        execplan_summary = {
            "id": execplan_id,
            "path": selected_execplan_path,
            "status": str(parsed.frontmatter.get("status", "")).strip(),
            "title": str(parsed.frontmatter.get("title", "")).strip(),
        }

    if role in {"draft_execplan_author", "implementation_worker"} and not execplan_summary:
        blockers.append("bootstrap_violation:active_execplan_required")

    initiative_findings, active_node = ([], None)
    if execplan_summary or role == "initiative_coordinator":
        initiative_findings, active_node = _initiative_mapping_findings(
            root=root_path,
            branch=current_branch,
            role=role,
            execplan_id=execplan_id,
        )
        blockers.extend(initiative_findings)

    if session_kind == "worker" and role != "implementation_worker":
        blockers.append("bootstrap_violation:worker_session_requires_impl_branch")
    active_lease: dict[str, Any] | None = None
    active_contract: dict[str, Any] | None = None
    if session_kind == "worker":
        if not worker_id:
            blockers.append("bootstrap_violation:worker_id_required")
        else:
            initiative_branch = str(active_node.get("initiative_branch", "")).strip() if isinstance(active_node, dict) else ""
            if not initiative_branch:
                blockers.append("bootstrap_violation:worker_contract_initiative_missing")
            else:
                registry = load_registry(root=root_path, initiative_branch=initiative_branch)
                if registry is None:
                    blockers.append(f"bootstrap_violation:worker_contract_registry_missing:{registry_path(root=root_path, initiative_branch=initiative_branch).as_posix()}")
                else:
                    active_contract = find_contract(registry, branch=current_branch, worker_id=worker_id)
                    if active_contract is None:
                        blockers.append("bootstrap_violation:worker_contract_missing")
                    else:
                        contract_status = str(active_contract.get("status", "")).strip()
                        if contract_status not in {"ready", "in_progress"}:
                            blockers.append("bootstrap_violation:worker_contract_not_runnable")
                        blockers.extend(
                            f"bootstrap_violation:{finding}" for finding in contract_scope_findings(active_contract)
                        )
                        if str(active_contract.get("initiative_branch", "")).strip() not in {"", initiative_branch}:
                            blockers.append("bootstrap_violation:worker_contract_initiative_mismatch")
                        if execplan_id and str(active_contract.get("execplan_id", "")).strip() not in {"", execplan_id}:
                            blockers.append("bootstrap_violation:worker_contract_execplan_mismatch")
            active_lease = _load_worker_lease(root=root_path, worker_id=worker_id)
            if active_lease is None:
                blockers.append("bootstrap_violation:worker_lease_missing")
            else:
                if str(active_lease.get("status", "")).strip() != "active":
                    blockers.append("bootstrap_violation:worker_lease_inactive")
                if str(active_lease.get("branch", "")).strip() != current_branch:
                    blockers.append("bootstrap_violation:worker_lease_branch_mismatch")
                if execplan_id and str(active_lease.get("execplan_id", "")).strip() != execplan_id:
                    blockers.append("bootstrap_violation:worker_lease_execplan_mismatch")
                if isinstance(active_node, dict):
                    initiative_branch = str(active_node.get("initiative_branch", "")).strip()
                    if initiative_branch and str(active_lease.get("initiative_branch", "")).strip() != initiative_branch:
                        blockers.append("bootstrap_violation:worker_lease_initiative_mismatch")
                if active_contract is not None:
                    contract_id = str(active_contract.get("contract_id", "")).strip()
                    if contract_id and str(active_lease.get("contract_id", "")).strip() != contract_id:
                        blockers.append("bootstrap_violation:worker_lease_contract_mismatch")

    report = {
        "command": COMMAND,
        "status": "ok" if not blockers else "blocked",
        "ok": not blockers,
        "root": root_path.as_posix(),
        "session_kind": session_kind,
        "branch": current_branch,
        "role": role,
        "required_bootstrap_artifacts": list(REQUIRED_BOOTSTRAP_ARTIFACTS),
        "branch_policy": branch_policy,
        "execplan_discovery": {
            "strategy": discovery_strategy,
            "candidates": discovery_candidates,
            "selected": selected_execplan_path or "",
        },
        "active_execplan": execplan_summary,
        "active_node": active_node,
        "active_worker_contract": active_contract,
        "active_worker_lease": active_lease,
        "merge_target": str(active_node.get("initiative_branch", "")).strip() if isinstance(active_node, dict) else "",
        "blockers": sorted(set(blockers)),
    }
    return (0 if not blockers else 1), report


def run_worker_session_lease(
    *,
    root: str = ".",
    branch: str | None = None,
    base_ref: str = "main",
    execplan_path: str | None = None,
    worker_id: str,
    actor_id: str = "agent/codex-01",
    action: str = "issue",
    outcome: str = "completed",
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    current_branch = branch or get_current_branch(root=root_path)
    if action == "issue":
        code, bootstrap = run_session_bootstrap_check(
            root=root,
            branch=current_branch,
            base_ref=base_ref,
            execplan_path=execplan_path,
            session_kind="codex",
        )
        if code != 0:
            return 1, {
                "command": COMMAND,
                "status": "blocked",
                "ok": False,
                "action": action,
                "worker_id": worker_id,
                "bootstrap": bootstrap,
                "blockers": bootstrap.get("blockers", []),
            }
        execplan = bootstrap.get("active_execplan") or {}
        node = bootstrap.get("active_node") or {}
        initiative_branch = str(node.get("initiative_branch", "")).strip()
        registry = load_registry(root=root_path, initiative_branch=initiative_branch) if initiative_branch else None
        contract = find_contract(registry, branch=current_branch, worker_id=worker_id) if registry else None
        if contract is None:
            return 1, {
                "command": COMMAND,
                "status": "blocked",
                "ok": False,
                "action": action,
                "worker_id": worker_id,
                "blockers": ["bootstrap_violation:worker_contract_missing"],
            }
        lease = {
            "version": "v1",
            "worker_id": worker_id,
            "status": "active",
            "issued_at": _timestamp(),
            "closed_at": "",
            "actor_id": actor_id,
            "branch": current_branch,
            "base_ref": base_ref,
            "execplan_id": str(execplan.get("id", "")).strip(),
            "execplan_path": str(execplan.get("path", "")).strip(),
            "initiative_branch": str(node.get("initiative_branch", "")).strip(),
            "parent_initiative_node": str(node.get("parent_initiative_node", "")).strip(),
            "node_id": str(node.get("node_id", "")).strip(),
            "merge_target": str(node.get("initiative_branch", "")).strip(),
            "contract_id": str(contract.get("contract_id", "")).strip(),
        }
        path = _lease_path(root=root_path, worker_id=worker_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lease, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _append_worker_audit_event(
            root=root_path,
            record={
                "event": "worker_lease_issued",
                "timestamp": lease["issued_at"],
                "worker_id": worker_id,
                "actor_id": actor_id,
                "branch": current_branch,
                "execplan_id": lease["execplan_id"],
                "initiative_branch": lease["initiative_branch"],
                "lease_path": path.as_posix(),
                "status": "active",
            },
        )
        return 0, {
            "command": COMMAND,
            "status": "ok",
            "ok": True,
            "action": action,
            "worker_id": worker_id,
            "lease_path": path.as_posix(),
            "lease": lease,
        }

    lease = _load_worker_lease(root=root_path, worker_id=worker_id)
    if lease is None:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "action": action,
            "worker_id": worker_id,
            "blockers": ["bootstrap_violation:worker_lease_missing"],
        }
    if action == "close":
        lease["status"] = "closed"
        lease["outcome"] = outcome
        lease["closed_at"] = _timestamp()
        path = _lease_path(root=root_path, worker_id=worker_id)
        path.write_text(json.dumps(lease, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _append_worker_audit_event(
            root=root_path,
            record={
                "event": "worker_lease_closed",
                "timestamp": lease["closed_at"],
                "worker_id": worker_id,
                "actor_id": actor_id,
                "branch": str(lease.get("branch", "")).strip(),
                "execplan_id": str(lease.get("execplan_id", "")).strip(),
                "initiative_branch": str(lease.get("initiative_branch", "")).strip(),
                "lease_path": path.as_posix(),
                "status": "closed",
                "outcome": outcome,
            },
        )
        return 0, {
            "command": COMMAND,
            "status": "ok",
            "ok": True,
            "action": action,
            "worker_id": worker_id,
            "lease_path": path.as_posix(),
            "lease": lease,
        }
    return 1, {
        "command": COMMAND,
        "status": "blocked",
        "ok": False,
        "action": action,
        "worker_id": worker_id,
        "blockers": [f"unsupported_lease_action:{action}"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--execplan", dest="execplan_path", default=None)
    parser.add_argument("--session-kind", choices=["codex", "worker"], default="codex")
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--actor-id", default="agent/codex-01")
    parser.add_argument("--lease-action", choices=["validate", "issue", "close"], default="validate")
    parser.add_argument("--outcome", choices=["completed", "failed", "abandoned"], default="completed")
    args = parser.parse_args()
    if args.lease_action == "validate":
        code, report = run_session_bootstrap_check(
            root=args.root,
            branch=args.branch,
            base_ref=args.base_ref,
            execplan_path=args.execplan_path,
            session_kind=args.session_kind,
            worker_id=args.worker_id,
        )
    else:
        if not args.worker_id:
            raise SystemExit("worker_id_required_for_lease_action")
        code, report = run_worker_session_lease(
            root=args.root,
            branch=args.branch,
            base_ref=args.base_ref,
            execplan_path=args.execplan_path,
            worker_id=args.worker_id,
            actor_id=args.actor_id,
            action=args.lease_action,
            outcome=args.outcome,
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
