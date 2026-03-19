from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.managed_repo_status import get_managed_repo_status


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_managed_repo_status_resolves_lightweight_external_repo(tmp_path: Path) -> None:
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "allowed_branch_patterns:",
                "  - initiative/*",
                "  - draft-execplan/*",
                "  - impl-execplan/*",
                "forbidden_branches:",
                "  - main",
                "  - master",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / ".agent" / "execplans" / "20260319-example.md",
        "\n".join(
            [
                "---",
                'id: "20260319-example"',
                'title: "Example"',
                'draft_branch: "draft-execplan/example"',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "docs" / "queued-execplans.md",
        "\n".join(
            [
                "# Queued ExecPlans",
                "",
                "## Mirror Metadata",
                "",
                "- canonical_last_graph_action_id: `rwg-action-1`",
                "- canonical_ready_order: ``",
                "- projection_authority: `projection_only`",
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-jayrun-foundation",
                        "type": "initiative",
                        "status": "in_progress",
                        "initiative_branch": "initiative/jayrun-foundation",
                    },
                    {
                        "node_id": "rwg-002",
                        "type": "execplan",
                        "status": "decision_gated",
                        "target_execplan_id": "20260319-example",
                        "implementation_branch": "impl-execplan/example",
                        "initiative_branch": "initiative/jayrun-foundation",
                        "parent_initiative_node": "initiative-jayrun-foundation",
                        "integration_mode": "via_initiative",
                    },
                ]
            }
        )
        + "\n",
    )

    code, report = get_managed_repo_status(
        root=tmp_path.as_posix(),
        branch="impl-execplan/example",
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert report["active_execplan"]["id"] == "20260319-example"
    assert report["active_node"]["node_id"] == "rwg-002"

