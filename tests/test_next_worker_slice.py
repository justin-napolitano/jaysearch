from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.next_worker_slice import get_next_worker_slice


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_execplan(tmp_path: Path, *, execplan_id: str) -> None:
    _write(
        tmp_path / ".agent" / "execplans" / f"{execplan_id}.md",
        "\n".join(
            [
                "---",
                f'id: "{execplan_id}"',
                'title: "Plan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-24T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                f"  - .agent/execplans/{execplan_id}.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                f'draft_branch: "draft-execplan/{execplan_id}"',
                'draft_created: "2026-03-24T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )


def test_next_worker_slice_selects_single_ready_child(tmp_path: Path) -> None:
    _seed_execplan(tmp_path, execplan_id="plan-id")
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "title": "Example",
                        "status": "in_progress",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json",
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": "contract-1",
                        "title": "Child",
                        "status": "ready",
                        "execplan_id": "plan-id",
                        "initiative_branch": "initiative/example",
                        "branch": "impl-execplan/child-main",
                        "worker_id": "child-main",
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q tests/test_next_worker_slice.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = get_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 0
    assert report["selected"]["implementation_branch"] == "impl-execplan/child-main"
    assert report["selected"]["worker_id"] == "child-main"
    assert report["selected"]["contract_id"] == "contract-1"


def test_next_worker_slice_blocks_when_no_ready_child_exists(tmp_path: Path) -> None:
    _seed_execplan(tmp_path, execplan_id="plan-id")
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "title": "Example",
                        "status": "in_progress",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json",
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": "contract-1",
                        "title": "Child",
                        "status": "decision_gated",
                        "execplan_id": "plan-id",
                        "initiative_branch": "initiative/example",
                        "branch": "",
                        "worker_id": "child-main",
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q tests/test_next_worker_slice.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = get_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 1
    assert "no_runnable_worker_contract" in report["blockers"]


def test_next_worker_slice_blocks_when_contract_execplan_missing(tmp_path: Path) -> None:
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "title": "Example",
                        "status": "in_progress",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    }
                ]
            }
        )
        + "\n",
    )
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json",
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": "contract-1",
                        "title": "Child",
                        "status": "ready",
                        "execplan_id": "missing-plan",
                        "initiative_branch": "initiative/example",
                        "branch": "impl-execplan/child-main",
                        "worker_id": "child-main",
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q tests/test_next_worker_slice.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = get_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 1
    assert "no_runnable_worker_contract" in report["blockers"]
    assert report["candidates"][0]["execplan_exists"] is False


def test_next_worker_slice_prefers_runnable_contract_inside_active_grouped_bundle(tmp_path: Path) -> None:
    _seed_execplan(tmp_path, execplan_id="plan-1")
    _seed_execplan(tmp_path, execplan_id="plan-2")
    _write(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "title": "Example",
                        "status": "in_progress",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-1",
                        "title": "Worker one",
                        "status": "ready",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-2",
                        "title": "Worker two",
                        "status": "ready",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
    )
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
                "node_ids": ["rwg-2"],
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
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json",
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": "contract-1",
                        "title": "Child one",
                        "status": "ready",
                        "node_id": "rwg-1",
                        "execplan_id": "plan-1",
                        "initiative_branch": "initiative/example",
                        "branch": "impl-execplan/child-one",
                        "worker_id": "child-one",
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q tests/test_next_worker_slice.py"],
                        },
                    },
                    {
                        "contract_id": "contract-2",
                        "title": "Child two",
                        "status": "ready",
                        "node_id": "rwg-2",
                        "execplan_id": "plan-2",
                        "initiative_branch": "initiative/example",
                        "branch": "impl-execplan/child-two",
                        "worker_id": "child-two",
                        "queue_position": 2,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q tests/test_next_worker_slice.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = get_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 0
    assert report["selected"]["contract_id"] == "contract-2"
    assert report["selected"]["bundle_id"] == "foundation-bootstrap"
