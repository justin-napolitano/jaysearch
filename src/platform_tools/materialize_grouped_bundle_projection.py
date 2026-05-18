from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.grouped_task_bundles import load_grouped_bundles, bundle_node_ids, bundle_validation_findings


COMMAND = "materialize-grouped-bundle-projection"
TASK_GRAPHS_DIR = Path("artifacts/planner/graphs")
REMAINING_WORK_GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")


def _load_task_graph(*, root: Path, dag_id: str) -> dict[str, Any]:
    path = root / TASK_GRAPHS_DIR / f"{dag_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("task_graph_not_object")
    return payload


def _save_remaining_work_graph(*, root: Path, graph: dict[str, Any]) -> Path:
    path = root / REMAINING_WORK_GRAPH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _select_bundle(*, root: Path, bundle_id: str | None) -> dict[str, Any]:
    bundles = load_grouped_bundles(root=root)
    if bundle_id:
        for bundle in bundles:
            if str(bundle.get("bundle_id", "")).strip() == bundle_id:
                return bundle
        raise ValueError("grouped_bundle_not_found")
    ready = [bundle for bundle in bundles if str(bundle.get("status", "")).strip() == "ready"]
    if len(ready) != 1:
        raise ValueError("grouped_bundle_not_deterministic")
    return ready[0]


def materialize_grouped_bundle_projection(
    *,
    root: str = ".",
    bundle_id: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    bundle = _select_bundle(root=root_path, bundle_id=bundle_id)
    dag_id = str(bundle.get("dag_id", "")).strip()
    task_graph = _load_task_graph(root=root_path, dag_id=dag_id)
    nodes = [node for node in task_graph.get("nodes", []) if isinstance(node, dict)]
    node_ids = {str(node.get("node_id", "")).strip() for node in nodes if str(node.get("node_id", "")).strip()}
    findings = bundle_validation_findings(bundle=bundle, allowed_node_ids=node_ids)
    if findings:
        return 1, {
            "command": COMMAND,
            "status": "blocked",
            "ok": False,
            "blockers": findings,
        }

    selected_node_ids = bundle_node_ids(bundle)
    node_index = {
        str(node.get("node_id", "")).strip(): node
        for node in nodes
        if str(node.get("node_id", "")).strip()
    }
    initiative_branch = str(bundle.get("initiative_branch", "")).strip() or "initiative/project-control-plane"
    initiative_node_id = f"initiative-{str(bundle.get('project_id', '')).strip() or 'project-control-plane'}"
    execplan_id = str(bundle.get("exec_plan_id", "")).strip()
    projection_nodes: list[dict[str, Any]] = [
        {
            "node_id": initiative_node_id,
            "title": str(bundle.get("title", "")).strip() or "Project Initiative",
            "status": "in_progress",
            "initiative_branch": initiative_branch,
            "parent_initiative_node": initiative_node_id,
        }
    ]
    for index, node_id in enumerate(selected_node_ids, start=1):
        source_node = node_index[node_id]
        projection_nodes.append(
            {
                "node_id": node_id,
                "title": str(source_node.get("title", "")).strip(),
                "status": "ready",
                "status_reason": "",
                "target_execplan_id": execplan_id,
                "implementation_branch": "",
                "initiative_branch": initiative_branch,
                "parent_initiative_node": initiative_node_id,
                "ordering": {
                    "queue_position": index,
                    "tie_breaker": node_id,
                },
            }
        )

    projection = {
        "graph_id": f"{dag_id}-projection",
        "source_dag_id": dag_id,
        "source_bundle_id": str(bundle.get("bundle_id", "")).strip(),
        "nodes": projection_nodes,
    }
    output_path = _save_remaining_work_graph(root=root_path, graph=projection)
    return 0, {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "bundle_id": str(bundle.get("bundle_id", "")).strip(),
        "dag_id": dag_id,
        "initiative_branch": initiative_branch,
        "output_path": output_path.as_posix(),
        "projected_node_ids": selected_node_ids,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--bundle-id", default=None)
    args = parser.parse_args()
    code, report = materialize_grouped_bundle_projection(root=args.root, bundle_id=args.bundle_id)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
