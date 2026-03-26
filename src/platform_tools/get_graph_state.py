from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from platform_tools.branch_policy import get_current_branch


COMMAND = "get-graph-state"
GRAPH_PATH = Path("artifacts/planner/research/remaining-work-graph.json")


def _load_graph(root: Path) -> dict[str, Any]:
    return json.loads((root / GRAPH_PATH).read_text(encoding="utf-8"))


def _project_node(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": str(node.get("node_id", "")).strip(),
        "title": str(node.get("title", "")).strip(),
        "status": str(node.get("status", "")).strip(),
        "execplan_id": str(node.get("target_execplan_id", "")).strip(),
        "initiative_branch": str(node.get("initiative_branch", "")).strip(),
        "implementation_branch": str(node.get("implementation_branch", "")).strip(),
        "goal_area": str(node.get("goal_area", "")).strip(),
    }


def get_graph_state(
    *,
    root: str = ".",
    initiative_branch: str | None = None,
) -> tuple[int, dict[str, Any]]:
    root_path = Path(root).resolve()
    graph = _load_graph(root_path)
    nodes = [item for item in graph.get("nodes", []) if isinstance(item, dict)]
    branch = (initiative_branch or "").strip()
    if not branch:
        current_branch = get_current_branch(root=root_path)
        branch = current_branch if current_branch.startswith("initiative/") else ""

    filtered = [node for node in nodes if not branch or str(node.get("initiative_branch", "")).strip() == branch]
    active_node = next((node for node in filtered if str(node.get("status", "")).strip() == "ready"), None)
    completed_count = sum(1 for node in filtered if str(node.get("status", "")).strip() == "completed")
    pending_count = sum(1 for node in filtered if str(node.get("status", "")).strip() != "completed")
    initiative_nodes = [
        node
        for node in filtered
        if str(node.get("node_id", "")).strip().startswith("initiative-")
        or str(node.get("node_id", "")).strip() == str(node.get("parent_initiative_node", "")).strip()
    ]
    queued = sorted(
        [
            node
            for node in filtered
            if str(node.get("node_id", "")).strip() not in {str(item.get("node_id", "")).strip() for item in initiative_nodes}
        ],
        key=lambda node: (
            int(node.get("ordering", {}).get("queue_position", 10**9))
            if isinstance(node.get("ordering", {}).get("queue_position"), int)
            else 10**9,
            str(node.get("node_id", "")).strip(),
        ),
    )
    report = {
        "command": COMMAND,
        "status": "ok",
        "ok": True,
        "initiative_branch": branch,
        "graph_id": str(graph.get("graph_id", "")).strip(),
        "last_action_id": str(graph.get("queue_projection", {}).get("last_reconciled_action_id", "")).strip(),
        "counts": {
            "nodes": len(filtered),
            "completed": completed_count,
            "pending": pending_count,
        },
        "initiative_nodes": [_project_node(node) for node in initiative_nodes],
        "active_node": _project_node(active_node) if isinstance(active_node, dict) else None,
        "queued_nodes": [_project_node(node) for node in queued[:10]],
    }
    return 0, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--initiative-branch", default=None)
    args = parser.parse_args()
    code, report = get_graph_state(**vars(args))
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
