from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.materialize_grouped_bundle_projection import materialize_grouped_bundle_projection


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_materialize_grouped_bundle_projection_writes_remaining_work_graph(tmp_path: Path) -> None:
    _write(
        tmp_path / "artifacts" / "planner" / "graphs" / "registry-control-plane-foundation.json",
        json.dumps(
            {
                "graph_id": "registry-control-plane-foundation",
                "nodes": [
                    {"node_id": "fnd-001", "title": "Bootstrap neutral monorepo skeleton"},
                    {"node_id": "fnd-002", "title": "Implement core contract and registry module layout"},
                ]
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "grouped-bundles" / "foundation-bootstrap.json",
        json.dumps(
            {
                "bundle_id": "foundation-bootstrap",
                "project_id": "project-control-plane",
                "dag_id": "registry-control-plane-foundation",
                "exec_plan_id": "20260518-first-implementation-packet-codex-01-execplan",
                "initiative_branch": "initiative/project-control-plane",
                "title": "Foundation Bootstrap",
                "status": "ready",
                "node_ids": ["fnd-001", "fnd-002"],
                "selection_mode": "ordered",
                "lineage": {
                    "source_repo": "project-control-plane",
                    "source_artifact": "docs/operations/first-implementation-packet.md",
                    "recorded_at_utc": "2026-05-18T00:00:00Z",
                },
            }
        )
        + "\n",
    )

    code, report = materialize_grouped_bundle_projection(root=tmp_path.as_posix())

    assert code == 0
    graph = json.loads(
        (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8")
    )
    assert graph["source_bundle_id"] == "foundation-bootstrap"
    assert graph["nodes"][0]["node_id"] == "initiative-project-control-plane"
    assert graph["nodes"][1]["target_execplan_id"] == "20260518-first-implementation-packet-codex-01-execplan"
    assert report["projected_node_ids"] == ["fnd-001", "fnd-002"]
