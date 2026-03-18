from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.anti_cheat_check import check_anti_cheat


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> None:
    command = ["git", *args]
    if args and args[0] == "commit":
        command = ["git", "commit", "--no-gpg-sign", *args[1:]]
    subprocess.run(command, cwd=root, check=True, capture_output=True, text=True)


def _seed_repo(tmp_path: Path, *, branch: str, execplan_id: str, goal_area: str, changes: list[str]) -> Path:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")

    execplan = tmp_path / ".agent" / "execplans" / f"{execplan_id}.md"
    _write(
        execplan,
        "\n".join(
            [
                "---",
                f'id: "{execplan_id}"',
                'title: "Anti-cheat test"',
                'owner: "agent/codex-01"',
                'created: "2026-03-16T00:00:00Z"',
                'status: "draft"',
                'base_branch: "main"',
                "changes:",
                *[f"  - {path}" for path in [execplan.as_posix().split(str(tmp_path) + "/")[1], *changes]],
                'approve_policy: "codeowners"',
                'reviewers: ["github:test"]',
                'draft_by: "agent/codex-01"',
                f'draft_branch: "{branch}"',
                'draft_created: "2026-03-16T00:00:00Z"',
                'finalized_by: ""',
                'finalized_at: ""',
                'finalized_in_pr: ""',
                "validation:",
                "  tests:",
                '    - name: "execplan-validate"',
                f'      command: "bin/execplan-validate {execplan.as_posix().split(str(tmp_path) + "/")[1]}"',
                '      expected_exit: 0',
                "---",
                "",
                "# Purpose / Big Picture",
            ]
        )
        + "\n",
    )

    _write(tmp_path / "spec/agent-capability-policy.yaml", Path("spec/agent-capability-policy.yaml").read_text(encoding="utf-8"))
    _write(tmp_path / "spec/protected-surfaces.schema.yaml", Path("spec/protected-surfaces.schema.yaml").read_text(encoding="utf-8"))
    _write(tmp_path / "spec/governance.yaml", "board_review_runtime:\n  authority_mode: projection_only\n")
    _write(tmp_path / "spec/board-action-api.yaml", "authority_model:\n  github_projects_authority: projection_only\n")
    _write(tmp_path / "spec/remaining-work-graph.schema.yaml", Path("spec/remaining-work-graph.schema.yaml").read_text(encoding="utf-8"))
    _write(tmp_path / ".agent/governance/exceptions.yaml", "version: v1\nexceptions: []\n")
    _write(
        tmp_path / "docs/queued-execplans.md",
        "\n".join(
            [
                "# Queued ExecPlans",
                "",
                "## Mirror Metadata",
                "",
                "- canonical_last_graph_action_id: `act-1`",
                f"- canonical_ready_order: `{execplan_id}`",
                "- projection_authority: `projection_only`",
            ]
        )
        + "\n",
    )
    _write_json(
        tmp_path / "artifacts/planner/research/remaining-work-graph.json",
        {
            "graph_id": "remaining-work-test",
            "created_at": "2026-03-16T00:00:00Z",
            "ordering_policy": {
                "ready_statuses": ["ready"],
                "ready_sort_fields": ["ready_order", "tie_breaker", "node_id"],
                "reorder_requires_explicit_action": True,
                "board_projection_authority": "projection_only",
            },
            "queue_projection": {
                "path": "docs/queued-execplans.md",
                "projection_authority": "projection_only",
                "last_reconciled_action_id": "act-1",
                "ready_execplan_ids": [execplan_id],
            },
            "graph_actions": [
                {
                    "action_id": "act-1",
                    "action": "promote_ready",
                    "node_id": "rwg-anti",
                    "rationale": "ready anti-cheat slice",
                }
            ],
            "nodes": [
                {
                    "node_id": "rwg-anti",
                    "title": "Anti-cheat test",
                    "status": "ready",
                    "status_reason": "",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["governance"],
                    "target_execplan_id": execplan_id,
                    "goal_area": goal_area,
                    "implementation_branch": branch,
                    "expected_artifacts": changes,
                    "ordering": {
                        "queue_position": 1,
                        "ready_order": 1,
                        "tie_breaker": execplan_id,
                        "source_action_id": "act-1",
                    },
                    "action_state": {
                        "last_action_id": "act-1",
                        "last_action": "promote_ready",
                        "action_required": False,
                        "reorder_requires_human": False,
                        "reorder_blockers": [],
                    },
                }
            ],
            "edges": [],
        },
    )

    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", branch)
    return execplan


def test_governance_impl_branch_allows_bounded_referee_surface_change(tmp_path: Path) -> None:
    branch = "impl-execplan/20260316-anti-cheat-capability-enforcement-codex-01-execplan-codex-01-20260316"
    execplan = _seed_repo(
        tmp_path,
        branch=branch,
        execplan_id="20260316-anti-cheat-capability-enforcement-codex-01-execplan",
        goal_area="governance",
        changes=["src/platform_tools/anti_cheat_check.py"],
    )
    _write(tmp_path / "src/platform_tools/anti_cheat_check.py", "ALLOWED = True\n")
    _git(tmp_path, "add", "src/platform_tools/anti_cheat_check.py")
    _git(tmp_path, "commit", "-m", "feat(governance): add anti-cheat runtime")

    code, report = check_anti_cheat(root=tmp_path.as_posix(), execplan_path=execplan.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["capability_rule_id"] == "agent_impl_governance"


def test_governance_draft_branch_allows_canonical_state_and_projection_changes(tmp_path: Path) -> None:
    branch = "draft-execplan/20260318-rule-authority-consolidation-codex-01-20260318"
    execplan = _seed_repo(
        tmp_path,
        branch=branch,
        execplan_id="20260318-rule-authority-consolidation-codex-01-execplan",
        goal_area="governance",
        changes=[
            "artifacts/planner/research/remaining-work-graph.json",
            "docs/queued-execplans.md",
        ],
    )
    _write_json(
        tmp_path / "artifacts/planner/research/remaining-work-graph.json",
        {
            "graph_id": "remaining-work-test",
            "created_at": "2026-03-18T00:00:00Z",
            "ordering_policy": {
                "ready_statuses": ["ready"],
                "ready_sort_fields": ["ready_order", "tie_breaker", "node_id"],
                "reorder_requires_explicit_action": True,
                "board_projection_authority": "projection_only",
            },
            "queue_projection": {
                "path": "docs/queued-execplans.md",
                "projection_authority": "projection_only",
                "last_reconciled_action_id": "act-2",
                "ready_execplan_ids": [],
            },
            "graph_actions": [
                {
                    "action_id": "act-2",
                    "action": "unblock",
                    "node_id": "rwg-anti",
                    "rationale": "draft review queued",
                }
            ],
            "nodes": [
                {
                    "node_id": "rwg-anti",
                    "title": "Anti-cheat test",
                    "status": "review_gated",
                    "status_reason": "draft under review",
                    "gating_class": "review_gated",
                    "conflict_domains": ["governance"],
                    "target_execplan_id": "20260318-rule-authority-consolidation-codex-01-execplan",
                    "goal_area": "governance",
                    "implementation_branch": "impl-execplan/20260318-rule-authority-consolidation-codex-01-execplan-codex-01-20260318",
                    "expected_artifacts": ["docs/queued-execplans.md"],
                    "ordering": {
                        "queue_position": 1,
                        "tie_breaker": "20260318-rule-authority-consolidation-codex-01-execplan",
                        "source_action_id": "act-2",
                    },
                    "action_state": {
                        "last_action_id": "act-2",
                        "last_action": "unblock",
                        "action_required": False,
                        "reorder_requires_human": False,
                        "reorder_blockers": [],
                    },
                }
            ],
            "edges": [],
        },
    )
    _write(
        tmp_path / "docs/queued-execplans.md",
        "# Queued ExecPlans\n\n## Mirror Metadata\n\n- canonical_last_graph_action_id: `act-2`\n- canonical_ready_order: ``\n- projection_authority: `projection_only`\n",
    )
    _git(tmp_path, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
    _git(tmp_path, "commit", "-m", "docs(governance): queue draft review")

    code, report = check_anti_cheat(root=tmp_path.as_posix(), execplan_path=execplan.as_posix())

    assert code == 0
    assert report["ok"] is True
    assert report["capability_rule_id"] == "agent_draft_governance"


def test_non_governance_impl_branch_blocks_referee_surface_change(tmp_path: Path) -> None:
    branch = "impl-execplan/20260316-provider-runtime-codex-01-execplan-codex-01-20260316"
    execplan = _seed_repo(
        tmp_path,
        branch=branch,
        execplan_id="20260316-provider-runtime-codex-01-execplan",
        goal_area="provider-sync",
        changes=["src/platform_tools/policy_compliance_check.py"],
    )
    _write(tmp_path / "src/platform_tools/policy_compliance_check.py", "CHANGED = True\n")
    _git(tmp_path, "add", "src/platform_tools/policy_compliance_check.py")
    _git(tmp_path, "commit", "-m", "feat(provider): illegal referee change")

    code, report = check_anti_cheat(root=tmp_path.as_posix(), execplan_path=execplan.as_posix())

    assert code == 1
    assert any("protected_surface_denied:src/platform_tools/policy_compliance_check.py:referee_surface" == blocker for blocker in report["blockers"])


def test_agent_cannot_write_exception_registry_even_on_governance_branch(tmp_path: Path) -> None:
    branch = "impl-execplan/20260316-anti-cheat-capability-enforcement-codex-01-execplan-codex-01-20260316"
    execplan = _seed_repo(
        tmp_path,
        branch=branch,
        execplan_id="20260316-anti-cheat-capability-enforcement-codex-01-execplan",
        goal_area="governance",
        changes=[".agent/governance/exceptions.yaml"],
    )
    _write(tmp_path / ".agent/governance/exceptions.yaml", "version: v1\nexceptions:\n  - id: bad\n")
    _git(tmp_path, "add", ".agent/governance/exceptions.yaml")
    _git(tmp_path, "commit", "-m", "feat(governance): illegal self exception")

    code, report = check_anti_cheat(root=tmp_path.as_posix(), execplan_path=execplan.as_posix())

    assert code == 1
    assert any("agent_exception_self_authorization_denied:.agent/governance/exceptions.yaml:exception_registry" == blocker for blocker in report["blockers"])
