from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.reconcile_remaining_work_merge import _next_action_id, _update_queue_metadata


GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")
RUN_DIR = Path("artifacts/governance/worker-runs")
QUEUE_PATH = Path("docs/queued-execplans.md")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def reconcile_worker_runtime_graph(
    *,
    repo_root: Path,
    run_id: str,
) -> dict[str, Any]:
    graph_path = repo_root / GRAPH_PATH
    run_path = repo_root / RUN_DIR / f"{run_id}.json"
    if not graph_path.exists():
        return {"command": "reconcile-worker-runtime-graph", "status": "blocked", "ok": False, "blockers": ["missing_remaining_work_graph"]}
    if not run_path.exists():
        return {"command": "reconcile-worker-runtime-graph", "status": "blocked", "ok": False, "blockers": [f"missing_worker_run:{run_id}"]}

    graph = _load_json(graph_path)
    run = _load_json(run_path)
    nodes = graph.get("nodes", [])
    actions = graph.get("graph_actions", [])
    if not isinstance(nodes, list):
        return {"command": "reconcile-worker-runtime-graph", "status": "blocked", "ok": False, "blockers": ["invalid_remaining_work_graph_nodes"]}
    if not isinstance(actions, list):
        return {"command": "reconcile-worker-runtime-graph", "status": "blocked", "ok": False, "blockers": ["invalid_remaining_work_graph_actions"]}

    branch = str(run.get("branch", "")).strip()
    contract_id = str(run.get("contract_id", "")).strip()
    matched_node: dict[str, Any] | None = None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if branch and str(node.get("implementation_branch", "")).strip() == branch:
            matched_node = node
            break
    if matched_node is None:
        return {
            "command": "reconcile-worker-runtime-graph",
            "status": "blocked",
            "ok": False,
            "blockers": [f"runtime_graph_node_not_found:{branch or run_id}"],
        }

    matched_node["node_kind"] = matched_node.get("node_kind") or "execplan_slice"
    matched_node["active_worker_contract_id"] = contract_id
    matched_node["last_run_id"] = str(run.get("run_id", "")).strip()
    matched_node["last_trace_id"] = str(run.get("trace_id", "")).strip()
    matched_node["last_problem_ref"] = str(run.get("problem_ref", "")).strip()
    matched_node["preferred_executor"] = str(run.get("executor_backend", "")).strip()
    if matched_node["preferred_executor"]:
        matched_node["allowed_executors"] = sorted(
            set(
                [
                    str(item).strip()
                    for item in list(matched_node.get("allowed_executors", [])) + [matched_node["preferred_executor"]]
                    if str(item).strip()
                ]
            )
        )

    existing_action = next(
        (
            item
            for item in reversed(actions)
            if isinstance(item, dict)
            and str(item.get("node_id", "")).strip() == str(matched_node.get("node_id", "")).strip()
            and str(item.get("event_type", "")).strip() == "worker_runtime_reconciled"
            and str(item.get("evidence_ref", "")).strip() == run_path.as_posix()
        ),
        None,
    )
    if existing_action is None:
        occurred_at = str(run.get("completed_at", "")).strip() or str(run.get("started_at", "")).strip() or "2026-01-01T00:00:00Z"
        action_id = _next_action_id(
            actions,
            committed_at=occurred_at,
            action="activate",
            node_id=str(matched_node.get("node_id", "")).strip(),
        )
        actions.append(
            {
                "action_id": action_id,
                "action": "activate",
                "node_id": str(matched_node.get("node_id", "")).strip(),
                "rationale": "worker runtime evidence reconciled deterministically from governed run artifacts",
                "evidence_ref": run_path.as_posix(),
                "queue_reconciled": True,
                "occurred_at": occurred_at,
                "actor_id": "agent/codex-01",
                "event_id": f"runtime:{run_id}",
                "event_type": "worker_runtime_reconciled",
                "initiative_id": str(run.get("initiative_id", "")).strip(),
                "contract_id": contract_id,
                "worker_id": str(run.get("worker_id", "")).strip(),
                "trace_id": str(run.get("trace_id", "")).strip(),
                "artifact_refs": [run_path.as_posix(), str(run.get("problem_ref", "")).strip()],
            }
        )
        queue_projection = graph.get("queue_projection", {}) if isinstance(graph.get("queue_projection"), dict) else {}
        queue_projection["last_reconciled_action_id"] = action_id
        graph["queue_projection"] = queue_projection
        queue_path = repo_root / QUEUE_PATH
        if queue_path.exists():
            queue_text = queue_path.read_text(encoding="utf-8")
            queue_text = _update_queue_metadata(
                queue_text,
                last_action_id=action_id,
                ready_execplan_ids=[str(item).strip() for item in queue_projection.get("ready_execplan_ids", []) if str(item).strip()],
            )
            queue_path.write_text(queue_text, encoding="utf-8")
    else:
        action_id = str(existing_action.get("action_id", "")).strip()

    graph["graph_actions"] = actions
    _write_json(graph_path, graph)
    return {
        "command": "reconcile-worker-runtime-graph",
        "status": "ok",
        "ok": True,
        "run_id": run_id,
        "action_id": action_id,
        "node_id": str(matched_node.get("node_id", "")).strip(),
        "graph_path": graph_path.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    report = reconcile_worker_runtime_graph(repo_root=Path(args.repo_root), run_id=args.run_id)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
