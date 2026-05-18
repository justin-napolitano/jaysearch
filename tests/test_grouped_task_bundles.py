from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.grouped_task_bundles import bundle_validation_findings, select_active_grouped_bundle


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_select_active_grouped_bundle_returns_ready_matching_bundle(tmp_path: Path) -> None:
    _write(
        tmp_path / "artifacts" / "planner" / "grouped-bundles" / "bundle.json",
        json.dumps(
            {
                "bundle_id": "foundation-bootstrap",
                "project_id": "project-control-plane",
                "dag_id": "registry-control-plane-foundation",
                "initiative_branch": "initiative/example",
                "title": "Foundation Bootstrap",
                "status": "ready",
                "node_ids": ["fnd-001", "fnd-002"],
                "selection_mode": "ordered",
                "lineage": {
                    "source_repo": "project-control-plane",
                    "source_artifact": "bundle.json",
                    "recorded_at_utc": "2026-05-18T00:00:00Z",
                },
            }
        )
        + "\n",
    )

    bundle = select_active_grouped_bundle(
        root=tmp_path,
        initiative_branch="initiative/example",
        allowed_node_ids={"fnd-001", "fnd-002", "fnd-003"},
        candidate_node_ids={"fnd-002", "fnd-003"},
    )

    assert bundle is not None
    assert bundle["bundle_id"] == "foundation-bootstrap"
    assert bundle["pending_node_ids"] == ["fnd-002"]


def test_bundle_validation_fails_for_unknown_nodes() -> None:
    findings = bundle_validation_findings(
        bundle={
            "bundle_id": "foundation-bootstrap",
            "dag_id": "dag-1",
            "title": "Foundation Bootstrap",
            "status": "ready",
            "node_ids": ["missing-node"],
        },
        allowed_node_ids={"fnd-001"},
    )

    assert "bundle_references_unknown_node_ids" in findings
