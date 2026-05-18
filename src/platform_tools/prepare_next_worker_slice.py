from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch
from platform_tools.grouped_task_bundles import select_active_grouped_bundle
from platform_tools.plan_utils import parse_plan
from platform_tools.worker_contracts import (
    contract_scope_findings,
    find_contract,
    load_registry,
    registry_contracts,
    save_registry,
    slugify,
    worker_id_from_branch,
)


COMMAND = "prepare-next-worker-slice"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
PENDING_NODE_STATUSES = {"decision_gated", "review_gated", "ready"}
ACTIVE_CONTRACT_STATUSES = {"ready", "in_progress"}


def _load_graph(root: Path) -> dict[str, Any]:
    return json.loads((root / GRAPH_PATH).read_text(encoding="utf-8"))


def _save_graph(root: Path, graph: dict[str, Any]) -> Path:
    path = root / GRAPH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _queue_position(node: dict[str, Any]) -> int:
    ordering = node.get("ordering", {}) if isinstance(node.get("ordering"), dict) else {}
    queue_position = ordering.get("queue_position")
    return queue_position if isinstance(queue_position, int) else 10**9


def _initiative_node(nodes: list[dict[str, Any]], branch: str) -> dict[str, Any] | None:
    matches = [
        node
        for node in nodes
        if str(node.get("initiative_branch", "")).strip() == branch
        and (
            str(node.get("node_id", "")).strip() == str(node.get("parent_initiative_node", "")).strip()
            or str(node.get("node_id", "")).strip().startswith("initiative-")
        )
    ]
    return matches[0] if len(matches) == 1 else None


def _candidate_nodes(nodes: list[dict[str, Any]], initiative_node_id: str, branch: str) -> list[dict[str, Any]]:
    candidates = []
    for node in nodes:
        if str(node.get("initiative_branch", "")).strip() != branch:
            continue
        if str(node.get("parent_initiative_node", "")).strip() != initiative_node_id:
            continue
        if str(node.get("node_id", "")).strip() == initiative_node_id:
            continue
        if str(node.get("status", "")).strip() not in PENDING_NODE_STATUSES:
            continue
        if not str(node.get("target_execplan_id", "")).strip():
            continue
        candidates.append(node)
    return sorted(
        candidates,
        key=lambda node: (
            _queue_position(node),
            str(node.get("target_execplan_id", "")).strip(),
            str(node.get("node_id", "")).strip(),
        ),
    )


def _generated_branch(node: dict[str, Any]) -> str:
    source = str(node.get("target_execplan_id", "")).strip() or str(node.get("node_id", "")).strip()
    return f"impl-execplan/{slugify(source)}"


def _contract_candidates(registry: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        item
        for item in registry_contracts(registry)
        if str(item.get("status", "")).strip() in ACTIVE_CONTRACT_STATUSES
    ]


def _execplan_exists(root: Path, execplan_id: str) -> bool:
    execplan_dir = root / ".agent" / "execplans"
    if not execplan_dir.exists():
        return False
    for path in sorted(execplan_dir.glob("*.md")):
        parsed = parse_plan(path)
        if str(parsed.frontmatter.get("id", "")).strip() == execplan_id:
            return True
    return False


def prepare_next_worker_slice(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
    node_id: str | None = None,
    execplan_id: str | None = None,
    branch: str | None = None,
    worker_id: str | None = None,
    owned_surfaces: list[str] | None = None,
    non_goals: list[str] | None = None,
    validations: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    current_branch = initiative_branch or get_current_branch(root=root_path)
    if not current_branch.startswith("initiative/"):
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "blockers": ["initiative_branch_required"],
            "candidates": [],
            "next_actions": [{"action": "switch_to_initiative_branch", "reason": "prepare_requires_initiative_branch"}],
        }

    graph = _load_graph(root_path)
    nodes = [item for item in graph.get("nodes", []) if isinstance(item, dict)]
    initiative_node = _initiative_node(nodes, current_branch)
    if initiative_node is None:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "blockers": ["initiative_node_not_deterministic"],
            "candidates": [],
            "next_actions": [{"action": "resolve_initiative_mapping", "reason": "initiative_node_not_deterministic"}],
        }

    initiative_node_id = str(initiative_node.get("node_id", "")).strip()
    candidates = _candidate_nodes(nodes, initiative_node_id, current_branch)
    allowed_node_ids = {str(node.get("node_id", "")).strip() for node in nodes if str(node.get("node_id", "")).strip()}
    candidate_node_ids = {str(node.get("node_id", "")).strip() for node in candidates}
    active_bundle = select_active_grouped_bundle(
        root=root_path,
        initiative_branch=current_branch,
        allowed_node_ids=allowed_node_ids,
        candidate_node_ids=candidate_node_ids,
    )
    selected_candidates = candidates
    if node_id:
        selected_candidates = [node for node in selected_candidates if str(node.get("node_id", "")).strip() == node_id]
    if execplan_id:
        selected_candidates = [
            node for node in selected_candidates if str(node.get("target_execplan_id", "")).strip() == execplan_id
        ]
    candidate_projection = [
        {
            "node_id": str(node.get("node_id", "")).strip(),
            "title": str(node.get("title", "")).strip(),
            "status": str(node.get("status", "")).strip(),
            "execplan_id": str(node.get("target_execplan_id", "")).strip(),
            "implementation_branch": str(node.get("implementation_branch", "")).strip(),
            "queue_position": _queue_position(node),
        }
        for node in candidates
    ]
    if (
        active_bundle is not None
        and not node_id
        and not execplan_id
        and len(selected_candidates) > 1
    ):
        bundle_order = list(active_bundle.get("pending_node_ids", []))
        ordered = {node_id_value: index for index, node_id_value in enumerate(bundle_order)}
        selected_candidates = sorted(
            [node for node in selected_candidates if str(node.get("node_id", "")).strip() in ordered],
            key=lambda node: ordered[str(node.get("node_id", "")).strip()],
        )[:1] or selected_candidates
    if len(selected_candidates) != 1:
        blocker = "no_matching_worker_candidate" if not selected_candidates else "worker_candidate_ambiguous"
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "selectors": {
                "node_id": node_id or "",
                "execplan_id": execplan_id or "",
            },
            "active_grouped_bundle": (
                {
                    "bundle_id": str(active_bundle.get("bundle_id", "")).strip(),
                    "dag_id": str(active_bundle.get("dag_id", "")).strip(),
                    "exec_plan_id": str(active_bundle.get("exec_plan_id", "")).strip(),
                    "node_ids": list(active_bundle.get("pending_node_ids", [])),
                }
                if active_bundle is not None
                else None
            ),
            "blockers": [blocker],
            "candidates": candidate_projection,
            "next_actions": [{"action": "resolve_worker_candidate_selection", "reason": blocker}],
        }

    selected_node = selected_candidates[0]
    registry = load_registry(root=root_path, initiative_branch=current_branch) or {
        "initiative_branch": current_branch,
        "contracts": [],
    }
    active_contracts = _contract_candidates(registry)
    selected_execplan_id = str(selected_node.get("target_execplan_id", "")).strip()
    selected_node_id = str(selected_node.get("node_id", "")).strip()
    selected_branch = branch.strip() if branch else str(selected_node.get("implementation_branch", "")).strip() or _generated_branch(selected_node)
    selected_worker_id = worker_id.strip() if worker_id else worker_id_from_branch(selected_branch)
    if not _execplan_exists(root_path, selected_execplan_id):
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "selected": {
                "node_id": selected_node_id,
                "title": str(selected_node.get("title", "")).strip(),
                "execplan_id": selected_execplan_id,
                "implementation_branch": selected_branch,
                "worker_id": selected_worker_id,
            },
            "blockers": ["initiative_execplan_missing"],
            "next_actions": [{"action": "author_or_finalize_initiative_execplan", "reason": "initiative_execplan_missing"}],
        }

    existing_contract = find_contract(registry, branch=selected_branch) or find_contract(
        registry,
        worker_id=selected_worker_id,
    )
    if existing_contract is None:
        existing_contract = find_contract(registry, contract_id=f"{selected_node_id}:{selected_execplan_id}")

    existing_contract_id = str(existing_contract.get("contract_id", "")).strip() if existing_contract else ""
    conflicting_active = [
        contract
        for contract in active_contracts
        if str(contract.get("contract_id", "")).strip() != existing_contract_id
    ]
    if conflicting_active:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "blockers": ["active_worker_contract_exists"],
            "active_contracts": conflicting_active,
            "candidates": candidate_projection,
            "next_actions": [{"action": "close_or_run_active_worker_contract", "reason": "active_worker_contract_exists"}],
        }

    contract_id = (
        str(existing_contract.get("contract_id", "")).strip()
        if existing_contract
        else f"{selected_node_id}:{selected_execplan_id}"
    )
    existing_scope = existing_contract.get("scope", {}) if isinstance(existing_contract, dict) else {}
    if not isinstance(existing_scope, dict):
        existing_scope = {}
    contract = {
        "contract_id": contract_id,
        "title": str(selected_node.get("title", "")).strip(),
        "status": "ready",
        "node_id": selected_node_id,
        "execplan_id": selected_execplan_id,
        "initiative_branch": current_branch,
        "branch": selected_branch,
        "worker_id": selected_worker_id,
        "bundle_id": str(active_bundle.get("bundle_id", "")).strip() if active_bundle is not None else "",
        "bundle_dag_id": str(active_bundle.get("dag_id", "")).strip() if active_bundle is not None else "",
        "bundle_exec_plan_id": str(active_bundle.get("exec_plan_id", "")).strip() if active_bundle is not None else "",
        "queue_position": _queue_position(selected_node),
        "merge_target": current_branch,
        "scope": {
            "owned_surfaces": [
                str(item).strip()
                for item in (owned_surfaces if owned_surfaces is not None else existing_scope.get("owned_surfaces", []))
                if str(item).strip()
            ],
            "non_goals": [
                str(item).strip()
                for item in (non_goals if non_goals is not None else existing_scope.get("non_goals", []))
                if str(item).strip()
            ],
            "validations": [
                str(item).strip()
                for item in (validations if validations is not None else existing_scope.get("validations", []))
                if str(item).strip()
            ],
        },
    }
    scope_findings = contract_scope_findings(contract)
    if scope_findings:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "initiative_branch": current_branch,
            "initiative_node": {
                "node_id": initiative_node_id,
                "title": str(initiative_node.get("title", "")).strip(),
                "status": str(initiative_node.get("status", "")).strip(),
            },
            "selected": {
                "node_id": selected_node_id,
                "title": str(selected_node.get("title", "")).strip(),
                "execplan_id": selected_execplan_id,
                "implementation_branch": selected_branch,
                "worker_id": selected_worker_id,
            "contract_id": contract_id,
            "bundle_id": str(active_bundle.get("bundle_id", "")).strip() if active_bundle is not None else "",
            "bundle_dag_id": str(active_bundle.get("dag_id", "")).strip() if active_bundle is not None else "",
        },
        "active_grouped_bundle": (
            {
                "bundle_id": str(active_bundle.get("bundle_id", "")).strip(),
                "dag_id": str(active_bundle.get("dag_id", "")).strip(),
                "exec_plan_id": str(active_bundle.get("exec_plan_id", "")).strip(),
                "node_ids": list(active_bundle.get("pending_node_ids", [])),
            }
            if active_bundle is not None
            else None
        ),
        "blockers": scope_findings,
        "next_actions": [{"action": "add_worker_contract_scope", "reason": finding} for finding in scope_findings],
    }
    registry_contract_list = [
        item
        for item in registry_contracts(registry)
        if str(item.get("contract_id", "")).strip() != contract_id
    ]
    registry_contract_list.append(contract)
    registry["contracts"] = sorted(
        registry_contract_list,
        key=lambda item: (
            int(item.get("queue_position")) if isinstance(item.get("queue_position"), int) else 10**9,
            str(item.get("contract_id", "")).strip(),
        ),
    )
    registry_path = save_registry(root=root_path, initiative_branch=current_branch, registry=registry)

    for node in nodes:
        if str(node.get("node_id", "")).strip() != selected_node_id:
            continue
        node["implementation_branch"] = selected_branch
        break
    graph_path = _save_graph(root_path, graph)

    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "initiative_branch": current_branch,
        "initiative_node": {
            "node_id": initiative_node_id,
            "title": str(initiative_node.get("title", "")).strip(),
            "status": str(initiative_node.get("status", "")).strip(),
        },
        "selected": {
            "node_id": selected_node_id,
            "title": str(selected_node.get("title", "")).strip(),
            "execplan_id": selected_execplan_id,
            "implementation_branch": selected_branch,
            "worker_id": selected_worker_id,
            "contract_id": contract_id,
            "bundle_id": str(active_bundle.get("bundle_id", "")).strip() if active_bundle is not None else "",
            "bundle_dag_id": str(active_bundle.get("dag_id", "")).strip() if active_bundle is not None else "",
        },
        "contract_registry_path": registry_path.as_posix(),
        "graph_path": graph_path.as_posix(),
        "active_grouped_bundle": (
            {
                "bundle_id": str(active_bundle.get("bundle_id", "")).strip(),
                "dag_id": str(active_bundle.get("dag_id", "")).strip(),
                "exec_plan_id": str(active_bundle.get("exec_plan_id", "")).strip(),
                "node_ids": list(active_bundle.get("pending_node_ids", [])),
            }
            if active_bundle is not None
            else None
        ),
        "candidates": candidate_projection,
        "next_actions": [
            {
                "action": "bootstrap_worker_session",
                "reason": "worker_contract_prepared",
                "command": f"bin/bootstrap-session --session-kind worker --branch {selected_branch} --worker-id {selected_worker_id} --lease-action issue",
            },
            {
                "action": "run_worker_session",
                "reason": "worker_contract_prepared",
                "command": f"bin/worker-session-coordinator --repo-source {root_path.as_posix()} --worker-id {selected_worker_id} --branch {selected_branch}",
            },
        ],
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--execplan-id", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--worker-id", default=None)
    parser.add_argument("--owned-surface", action="append", dest="owned_surfaces", default=None)
    parser.add_argument("--non-goal", action="append", dest="non_goals", default=None)
    parser.add_argument("--validation", action="append", dest="validations", default=None)
    args = parser.parse_args()
    code, report = prepare_next_worker_slice(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
