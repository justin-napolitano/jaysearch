from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.reconcile_worker_runtime_graph import reconcile_worker_runtime_graph


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def test_reconcile_worker_runtime_graph_updates_matching_node(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        {
            "queue_projection": {
                "last_reconciled_action_id": "act-0",
                "ready_execplan_ids": [],
            },
            "graph_actions": [],
            "nodes": [
                {
                    "node_id": "rwg-1",
                    "implementation_branch": "impl-execplan/example",
                    "target_execplan_id": "plan-id",
                }
            ]
        },
    )
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "queued-execplans.md").write_text(
        "# Queued ExecPlans\n\n## Mirror Metadata\n\n- canonical_last_graph_action_id: `act-0`\n- canonical_ready_order: ``\n- projection_authority: `projection_only`\n",
        encoding="utf-8",
    )
    _write_json(
        tmp_path / "artifacts" / "governance" / "worker-runs" / "run-1.json",
        {
            "run_id": "run-1",
            "trace_id": "trace-1",
            "branch": "impl-execplan/example",
            "contract_id": "contract-1",
            "problem_ref": "artifacts/governance/problems/run-1.problem.json",
            "executor_backend": "clone",
        },
    )

    report = reconcile_worker_runtime_graph(repo_root=tmp_path, run_id="run-1")

    assert report["ok"] is True
    graph = json.loads((tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8"))
    node = graph["nodes"][0]
    assert node["node_kind"] == "execplan_slice"
    assert node["active_worker_contract_id"] == "contract-1"
    assert node["last_run_id"] == "run-1"
    assert node["last_trace_id"] == "trace-1"
    assert node["last_problem_ref"] == "artifacts/governance/problems/run-1.problem.json"
    assert node["preferred_executor"] == "clone"
    assert node["allowed_executors"] == ["clone"]
    action = graph["graph_actions"][0]
    assert action["event_type"] == "worker_runtime_reconciled"
    assert action["trace_id"] == "trace-1"
    assert graph["queue_projection"]["last_reconciled_action_id"] == report["action_id"]
    queue_text = (tmp_path / "docs" / "queued-execplans.md").read_text(encoding="utf-8")
    assert report["action_id"] in queue_text
