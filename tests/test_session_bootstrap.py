from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.session_bootstrap import run_session_bootstrap_check, run_worker_session_lease


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_common(tmp_path: Path) -> None:
    _write(tmp_path / ".agent" / "AGENTS.md", "# AGENTS\n")
    _write(tmp_path / ".agent" / "PLANS.md", "# PLANS\n")
    _write(
        tmp_path / "pyproject.toml",
        "\n".join(
            [
                "[project]",
                'name = "test-repo"',
                "",
                "[project.scripts]",
                'get-control-plane-status = "platform_tools.get_control_plane_status:main"',
                'local-task-router = "platform_tools.local_runtime.router:main"',
                'control-plane-api-check = "platform_tools.control_plane_api_check:main"',
                'public-orchestration-api-check = "platform_tools.public_orchestration_api_check:main"',
                'local-runtime-check = "platform_tools.local_runtime.runtime_check:main"',
            ]
        )
        + "\n",
    )
    for command in (
        "get-control-plane-status",
        "local-task-router",
        "control-plane-api-check",
        "public-orchestration-api-check",
        "local-runtime-check",
    ):
        _write(tmp_path / "bin" / command, "#!/usr/bin/env bash\n")
    _write(
        tmp_path / "spec" / "workflow.yaml",
        "\n".join(
            [
                "execution_requirements:",
                "  initiative_requirements:",
                "    fail_closed_on_missing_initiative_mapping: true",
                "    normal_governed_work_requires_initiative_branch: true",
            ]
        )
        + "\n",
    )
    _write(tmp_path / "spec" / "control-plane-api.schema.yaml", "$defs:\n  response_get_control_plane_status:\n    allOf:\n      - properties:\n          command:\n            const: get-control-plane-status\n        required: [command, api_version, status, ok]\n  response_get_next_orchestration_action:\n    allOf:\n      - properties:\n          command:\n            const: get-next-orchestration-action\n        required: [command, api_version, status, ok]\n")
    _write(
        tmp_path / "spec" / "public-orchestration-api.schema.yaml",
        "\n".join(
            [
                "properties:",
                "  api_version:",
                '    const: "public-orchestration.v1"',
                "$defs:",
                "  graph_node_projection:",
                "    required: [node_id]",
                "  worker_contract_projection:",
                "    required: [contract_id]",
                "  worker_contract_run_projection:",
                "    required: [contract_id]",
                "  response_get_graph_state:",
                "    allOf:",
                "      - properties:",
                "          command:",
                "            const: get-graph-state",
                "        required: [command, api_version, status, ok, counts]",
                "  response_resolve_worker_contract:",
                "    allOf:",
                "      - properties:",
                "          command:",
                "            const: resolve-worker-contract",
                "        required: [command, api_version, status, ok]",
                "  response_get_worker_status:",
                "    allOf:",
                "      - properties:",
                "          command:",
                "            const: get-worker-status",
                "        required: [command, api_version, status, ok]",
                "  response_run_worker_contract:",
                "    allOf:",
                "      - properties:",
                "          command:",
                "            const: run-worker-contract",
                "        required: [command, api_version, status, ok]",
                "  response_start_next_worker:",
                "    allOf:",
                "      - properties:",
                "          command:",
                "            const: start-next-worker",
                "        required: [command, api_version, status, ok, resolution]",
            ]
        )
        + "\n",
    )
    _write(tmp_path / "spec" / "local-orchestration.yaml", "runtime_profile:\n  default_backend: ollama\n")
    _write(tmp_path / "spec" / "local-orchestration-api.schema.yaml", "version: v1\n")
    _write(tmp_path / "spec" / "ruleset.yaml", "execution_constraints:\n  allowed_branch_patterns: [initiative/*, draft-execplan/*, impl-execplan/*, queue-execplan/*]\n")
    _write(tmp_path / "spec" / "governance.yaml", "required_checks: {}\n")
    _write(tmp_path / "project.rules.yaml", "overlay:\n  required_check_names_add: []\n  forbidden_branches_add: []\n  allowed_branch_patterns_remove: []\n")


def _seed_worker_contract(
    tmp_path: Path,
    *,
    branch: str = "impl-execplan/plan",
    worker_id: str = "worker-1",
    status: str = "ready",
    initiative_branch: str = "initiative/example",
    execplan_id: str = "plan-id",
) -> None:
    registry_name = initiative_branch.replace("/", "-")
    _write(
        tmp_path / "artifacts" / "governance" / "initiative-worker-contracts" / f"{registry_name}.json",
        json.dumps(
            {
                "initiative_branch": initiative_branch,
                "contracts": [
                    {
                        "contract_id": "contract-1",
                        "title": "Worker contract",
                        "status": status,
                        "execplan_id": execplan_id,
                        "initiative_branch": initiative_branch,
                        "branch": branch,
                        "worker_id": worker_id,
                        "queue_position": 1,
                        "scope": {
                            "owned_surfaces": ["src/platform_tools/session_bootstrap.py"],
                            "non_goals": ["Do not widen initiative scope"],
                            "validations": ["uv run pytest -q tests/test_session_bootstrap.py"],
                        },
                    }
                ],
            }
        )
        + "\n",
    )


def test_worker_session_requires_impl_branch(tmp_path: Path) -> None:
    _seed_common(tmp_path)
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(json.dumps({"nodes": []}) + "\n", encoding="utf-8")

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="initiative/example",
        session_kind="worker",
        worker_id="worker-1",
    )

    assert code == 1
    assert "bootstrap_violation:worker_session_requires_impl_branch" in report["blockers"]


def test_session_bootstrap_blocks_when_harness_surface_is_missing(tmp_path: Path) -> None:
    _seed_common(tmp_path)
    (tmp_path / "bin" / "local-task-router").unlink()
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(json.dumps({"nodes": []}) + "\n", encoding="utf-8")

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="initiative/example",
        session_kind="codex",
    )

    assert code == 1
    assert "bootstrap_violation:missing_harness_bin_wrapper:local-task-router" in report["blockers"]


def test_impl_branch_bootstrap_requires_parent_initiative_and_execplan(tmp_path: Path) -> None:
    _seed_common(tmp_path)
    _write(
        tmp_path / ".agent" / "execplans" / "plan.md",
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                'title: "Plan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-24T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - .agent/execplans/plan.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/plan"',
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
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-1",
                        "target_execplan_id": "plan-id",
                        "implementation_branch": "impl-execplan/plan",
                        "integration_mode": "via_initiative",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _seed_worker_contract(tmp_path, initiative_branch="main")

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        session_kind="worker",
        worker_id="worker-1",
    )

    assert code == 1
    assert report["role"] == "implementation_worker"
    assert report["active_worker_contract"] is None
    assert any(item.startswith("bootstrap_violation:worker_contract_registry_missing:") for item in report["blockers"])
    assert "bootstrap_violation:worker_lease_missing" in report["blockers"]

    _seed_worker_contract(tmp_path)

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        session_kind="worker",
        worker_id="worker-1",
    )

    assert code == 1
    assert report["active_worker_contract"]["contract_id"] == "contract-1"
    assert "bootstrap_violation:worker_lease_missing" in report["blockers"]

    lease_code, lease_report = run_worker_session_lease(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        worker_id="worker-1",
        action="issue",
    )

    assert lease_code == 0
    assert lease_report["lease"]["initiative_branch"] == "initiative/example"

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        session_kind="worker",
        worker_id="worker-1",
    )

    assert code == 0
    assert report["merge_target"] == "initiative/example"
    assert report["active_execplan"]["id"] == "plan-id"
    assert report["active_worker_contract"]["contract_id"] == "contract-1"
    assert report["active_worker_lease"]["status"] == "active"


def test_impl_branch_bootstrap_blocks_when_merge_target_is_main(tmp_path: Path) -> None:
    _seed_common(tmp_path)
    _write(
        tmp_path / ".agent" / "execplans" / "plan.md",
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                'title: "Plan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-24T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - .agent/execplans/plan.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/plan"',
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
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-1",
                        "target_execplan_id": "plan-id",
                        "implementation_branch": "impl-execplan/plan",
                        "integration_mode": "via_initiative",
                        "initiative_branch": "main",
                        "parent_initiative_node": "initiative-example",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _seed_worker_contract(tmp_path, initiative_branch="main")

    code, report = run_session_bootstrap_check(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        session_kind="worker",
        worker_id="worker-1",
    )

    assert code == 1
    assert "bootstrap_violation:implementation_merge_target_main" in report["blockers"]


def test_worker_session_lease_close_marks_lease_closed_and_audits(tmp_path: Path) -> None:
    _seed_common(tmp_path)
    _write(
        tmp_path / ".agent" / "execplans" / "plan.md",
        "\n".join(
            [
                "---",
                'id: "plan-id"',
                'title: "Plan"',
                'owner: "agent/codex-01"',
                'created: "2026-03-24T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                "  - .agent/execplans/plan.md",
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                'draft_branch: "draft-execplan/plan"',
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
    (tmp_path / "artifacts" / "planner" / "research").mkdir(parents=True, exist_ok=True)
    (tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "initiative-example",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                    {
                        "node_id": "rwg-1",
                        "target_execplan_id": "plan-id",
                        "implementation_branch": "impl-execplan/plan",
                        "integration_mode": "via_initiative",
                        "initiative_branch": "initiative/example",
                        "parent_initiative_node": "initiative-example",
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _seed_worker_contract(tmp_path)

    issue_code, _ = run_worker_session_lease(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        worker_id="worker-1",
        action="issue",
    )
    close_code, close_report = run_worker_session_lease(
        root=tmp_path.as_posix(),
        branch="impl-execplan/plan",
        worker_id="worker-1",
        action="close",
    )

    assert issue_code == 0
    assert close_code == 0
    assert close_report["lease"]["status"] == "closed"
    audit_lines = (tmp_path / "artifacts" / "governance" / "worker-session-events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2
