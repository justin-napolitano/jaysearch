from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.next_worker_slice import get_next_worker_slice
from platform_tools.prepare_next_worker_slice import prepare_next_worker_slice


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_graph(tmp_path: Path) -> None:
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
                        "status": "decision_gated",
                        "target_execplan_id": "plan-1",
                        "implementation_branch": "",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                        "ordering": {"queue_position": 1},
                    },
                    {
                        "node_id": "rwg-2",
                        "title": "Worker two",
                        "status": "decision_gated",
                        "target_execplan_id": "plan-2",
                        "implementation_branch": "",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                        "ordering": {"queue_position": 2},
                    },
                ]
            }
        )
        + "\n",
    )


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


def test_prepare_next_worker_slice_requires_unambiguous_selection(tmp_path: Path) -> None:
    _seed_graph(tmp_path)

    code, report = prepare_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")

    assert code == 1
    assert "worker_candidate_ambiguous" in report["blockers"]


def test_prepare_next_worker_slice_writes_contract_and_graph_branch(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    _seed_execplan(tmp_path, execplan_id="plan-1")

    blocked_code, blocked_report = prepare_next_worker_slice(
        root=tmp_path.as_posix(),
        initiative_branch="initiative/example",
        node_id="rwg-1",
    )

    assert blocked_code == 1
    assert "worker_contract_owned_surfaces_missing" in blocked_report["blockers"]
    assert "worker_contract_non_goals_missing" in blocked_report["blockers"]
    assert "worker_contract_validations_missing" in blocked_report["blockers"]

    code, report = prepare_next_worker_slice(
        root=tmp_path.as_posix(),
        initiative_branch="initiative/example",
        node_id="rwg-1",
        owned_surfaces=["docs/commands.md"],
        non_goals=["Do not rename unrelated commands"],
        validations=["uv run pytest -q tests/test_prepare_next_worker_slice.py"],
    )

    assert code == 0
    assert report["selected"]["contract_id"] == "rwg-1:plan-1"
    assert report["selected"]["implementation_branch"] == "impl-execplan/plan-1"
    assert report["selected"]["worker_id"] == "plan-1"

    registry = json.loads(
        (
            tmp_path
            / "artifacts"
            / "governance"
            / "initiative-worker-contracts"
            / "initiative-example.json"
        ).read_text(encoding="utf-8")
    )
    assert registry["contracts"][0]["status"] == "ready"
    assert registry["contracts"][0]["branch"] == "impl-execplan/plan-1"

    graph = json.loads(
        (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").read_text(encoding="utf-8")
    )
    selected_node = next(node for node in graph["nodes"] if node.get("node_id") == "rwg-1")
    assert selected_node["implementation_branch"] == "impl-execplan/plan-1"

    next_code, next_report = get_next_worker_slice(root=tmp_path.as_posix(), initiative_branch="initiative/example")
    assert next_code == 0
    assert next_report["selected"]["contract_id"] == "rwg-1:plan-1"


def test_prepare_next_worker_slice_blocks_when_another_active_contract_exists(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    _seed_execplan(tmp_path, execplan_id="plan-1")
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / "initiative-example.json",
        json.dumps(
            {
                "initiative_branch": "initiative/example",
                "contracts": [
                    {
                        "contract_id": "existing",
                        "title": "Existing",
                        "status": "ready",
                        "node_id": "rwg-2",
                        "execplan_id": "plan-2",
                        "initiative_branch": "initiative/example",
                        "branch": "impl-execplan/plan-2",
                        "worker_id": "plan-2",
                        "queue_position": 2,
                        "scope": {
                            "owned_surfaces": ["docs/commands.md"],
                            "non_goals": ["Do not widen scope"],
                            "validations": ["uv run pytest -q"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )

    code, report = prepare_next_worker_slice(
        root=tmp_path.as_posix(),
        initiative_branch="initiative/example",
        node_id="rwg-1",
    )

    assert code == 1
    assert "active_worker_contract_exists" in report["blockers"]


def test_prepare_next_worker_slice_blocks_when_execplan_missing(tmp_path: Path) -> None:
    _seed_graph(tmp_path)

    code, report = prepare_next_worker_slice(
        root=tmp_path.as_posix(),
        initiative_branch="initiative/example",
        node_id="rwg-1",
        owned_surfaces=["docs/commands.md"],
        non_goals=["Do not widen scope"],
        validations=["uv run pytest -q tests/test_prepare_next_worker_slice.py"],
    )

    assert code == 1
    assert "initiative_execplan_missing" in report["blockers"]


def test_prepare_next_worker_slice_uses_grouped_bundle_to_resolve_ambiguity(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    _seed_execplan(tmp_path, execplan_id="plan-1")
    _seed_execplan(tmp_path, execplan_id="plan-2")
    _write(
        tmp_path / "artifacts" / "planner" / "grouped-bundles" / "bundle.json",
        json.dumps(
            {
                "bundle_id": "foundation-bootstrap",
                "project_id": "project-control-plane",
                "dag_id": "registry-control-plane-foundation",
                "initiative_branch": "initiative/example",
                "exec_plan_id": "bootstrap-execplan",
                "title": "Foundation Bootstrap",
                "status": "ready",
                "node_ids": ["rwg-2", "rwg-1"],
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

    code, report = prepare_next_worker_slice(
        root=tmp_path.as_posix(),
        initiative_branch="initiative/example",
        owned_surfaces=["docs/commands.md"],
        non_goals=["Do not widen scope"],
        validations=["uv run pytest -q tests/test_prepare_next_worker_slice.py"],
    )

    assert code == 0
    assert report["selected"]["node_id"] == "rwg-2"
    assert report["selected"]["bundle_id"] == "foundation-bootstrap"
    registry = json.loads(
        (
            tmp_path
            / "artifacts"
            / "governance"
            / "initiative-worker-contracts"
            / "initiative-example.json"
        ).read_text(encoding="utf-8")
    )
    assert registry["contracts"][0]["bundle_id"] == "foundation-bootstrap"
