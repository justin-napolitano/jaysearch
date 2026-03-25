from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.plan_utils import parse_plan
from platform_tools.worker_contracts import contract_scope_findings, load_registry, registry_contracts, worker_id_from_branch


COMMAND = "next-worker-slice"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
RUNNABLE_CONTRACT_STATUSES = {"ready"}


def _load_graph(root: Path) -> dict[str, Any]:
    return json.loads((root / GRAPH_PATH).read_text(encoding="utf-8"))


def _execplan_exists(root: Path, execplan_id: str) -> bool:
    execplan_dir = root / ".agent" / "execplans"
    if not execplan_dir.exists():
        return False
    for path in sorted(execplan_dir.glob("*.md")):
        parsed = parse_plan(path)
        if str(parsed.frontmatter.get("id", "")).strip() == execplan_id:
            return True
    return False


def _sort_key(node: dict[str, Any]) -> tuple[Any, ...]:
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    queue_position = ordering.get("queue_position")
    queue_sort = queue_position if isinstance(queue_position, int) else 10**9
    tie_breaker = str(ordering.get("tie_breaker", "")).strip()
    return (queue_sort, tie_breaker, str(node.get("node_id", "")).strip())

def get_next_worker_slice(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    branch = initiative_branch or get_current_branch(root=root_path)
    if not branch.startswith("initiative/"):
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": branch,
            "blockers": ["initiative_branch_required"],
            "candidates": [],
            "next_actions": [{"action": "switch_to_initiative_branch", "reason": "resolver_requires_initiative_branch"}],
        }
        return 1, report

    graph = _load_graph(root_path)
    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    initiative_nodes = [
        node
        for node in nodes
        if str(node.get("initiative_branch", "")).strip() == branch
        and (
            str(node.get("node_id", "")).strip() == str(node.get("parent_initiative_node", "")).strip()
            or str(node.get("node_id", "")).strip().startswith("initiative-")
        )
    ]
    if len(initiative_nodes) != 1:
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": branch,
            "blockers": ["initiative_node_not_deterministic"],
            "candidates": [],
            "next_actions": [{"action": "resolve_initiative_mapping", "reason": "initiative_node_not_deterministic"}],
        }
        return 1, report

    initiative_node = initiative_nodes[0]
    initiative_node_id = str(initiative_node.get("node_id", "")).strip()
    registry = load_registry(root=root_path, initiative_branch=branch)
    if registry is None:
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "blockers": ["worker_contract_registry_missing"],
            "candidates": [],
            "next_actions": [{"action": "author_worker_contracts", "reason": "worker_contract_registry_missing"}],
        }
        return 1, report
    contracts = sorted(
        registry_contracts(registry),
        key=lambda item: (
            int(item.get("queue_position")) if isinstance(item.get("queue_position"), int) else 10**9,
            str(item.get("contract_id", "")).strip(),
        ),
    )
    candidates = [
        {
            "contract_id": str(contract.get("contract_id", "")).strip(),
            "title": str(contract.get("title", "")).strip(),
            "status": str(contract.get("status", "")).strip(),
            "execplan_id": str(contract.get("execplan_id", "")).strip(),
            "implementation_branch": str(contract.get("branch", "")).strip(),
            "worker_id": str(contract.get("worker_id", "")).strip(),
            "initiative_branch": str(contract.get("initiative_branch", "")).strip() or branch,
            "queue_position": contract.get("queue_position"),
            "execplan_exists": _execplan_exists(root_path, str(contract.get("execplan_id", "")).strip()),
            "scope_findings": contract_scope_findings(contract),
        }
        for contract in contracts
    ]
    runnable = [
        contract
        for contract in contracts
        if str(contract.get("status", "")).strip() in RUNNABLE_CONTRACT_STATUSES
        and str(contract.get("branch", "")).strip()
        and _execplan_exists(root_path, str(contract.get("execplan_id", "")).strip())
        and not contract_scope_findings(contract)
    ]
    if len(runnable) != 1:
        blocker = "no_runnable_worker_contract" if not runnable else "runnable_worker_contract_ambiguous"
        report = {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "blockers": [blocker],
            "candidates": candidates,
            "next_actions": [{"action": "resolve_worker_contract_selection", "reason": blocker}],
        }
        return 1, report

    selected = runnable[0]
    implementation_branch = str(selected.get("branch", "")).strip()
    worker_id = str(selected.get("worker_id", "")).strip() or worker_id_from_branch(implementation_branch)
    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "initiative_branch": branch,
        "initiative_node": {
            "node_id": initiative_node_id,
            "title": str(initiative_node.get("title", "")).strip(),
            "status": str(initiative_node.get("status", "")).strip(),
        },
        "selected": {
            "contract_id": str(selected.get("contract_id", "")).strip(),
            "title": str(selected.get("title", "")).strip(),
            "status": str(selected.get("status", "")).strip(),
            "execplan_id": str(selected.get("execplan_id", "")).strip(),
            "implementation_branch": implementation_branch,
            "initiative_branch": str(selected.get("initiative_branch", "")).strip() or branch,
            "worker_id": worker_id,
        },
        "candidates": candidates,
        "next_actions": [
            {
                "action": "bootstrap_worker_session",
                "reason": "single_runnable_worker_contract",
                "command": f"bin/bootstrap-session --session-kind worker --branch {implementation_branch} --worker-id {worker_id} --lease-action issue",
            },
            {
                "action": "run_worker_session",
                "reason": "single_runnable_worker_contract",
                "command": f"bin/worker-session-coordinator --repo-source {root_path.as_posix()} --worker-id {worker_id} --branch {implementation_branch}",
            },
        ],
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    args = parser.parse_args()
    code, report = get_next_worker_slice(root=args.root, initiative_branch=args.initiative_branch)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
