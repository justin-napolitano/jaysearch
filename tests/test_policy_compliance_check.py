from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.policy_compliance_check import check_policy_compliance


BRANCH = "impl-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312"
EXECPLAN_ID = "20260312-game-policy-compliance-codex-01-execplan"


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


def _execplan_text() -> str:
    return f"""---
id: "{EXECPLAN_ID}"
title: "Policy compliance"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/{EXECPLAN_ID}.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/test"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/{EXECPLAN_ID}.md"
      expected_exit: 0
tasks:
  - title: "Formalize policy compliance"
    priority: "P1"
depends_on: []
---

# Purpose / Big Picture

Test.

## Progress

- [ ] Test

## Surprises & Discoveries

None.

## Decision Log

None.

## Outcomes & Retrospective

Test.

## Context and Orientation

Test.

## Plan of Work

Test.

## Concrete Steps

1. Test.

## Validation and Acceptance

Test.

## Idempotence and Recovery

Test.

## Artifacts and Notes

Test.

## Interfaces and Dependencies

Test.
"""


def _remaining_work_graph() -> dict[str, object]:
    return {
        "graph_id": "remaining-work-test",
        "created_at": "2026-03-12T00:00:00Z",
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
            "ready_execplan_ids": [EXECPLAN_ID],
        },
        "graph_actions": [
            {
                "action_id": "act-1",
                "action": "promote_ready",
                "node_id": "rwg-012",
                "rationale": "ready implementation slice",
            }
        ],
        "nodes": [
            {
                "node_id": "rwg-012",
                "title": "Game policy-compliance runtime",
                "status": "ready",
                "status_reason": "active implementation slice",
                "gating_class": "auto_runnable",
                "conflict_domains": ["governance"],
                "target_execplan_id": EXECPLAN_ID,
                "goal_area": "governance",
                "expected_artifacts": ["bin/policy-compliance-check"],
                "implementation_branch": BRANCH,
                "ordering": {
                    "queue_position": 1,
                    "ready_order": 1,
                    "tie_breaker": EXECPLAN_ID,
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
    }


def _queue_text() -> str:
    return (
        "# Queued ExecPlans\n\n"
        "## Mirror Metadata\n\n"
        "- canonical_last_graph_action_id: `act-1`\n"
        f"- canonical_ready_order: `{EXECPLAN_ID}`\n"
        "- projection_authority: `projection_only`\n\n"
        f"1. `{EXECPLAN_ID}`\n"
        "   - status: `ready`\n"
        f"   - implementation branch: `{BRANCH}`\n"
    )


def _remaining_work_schema_text() -> str:
    return """version: 1
title: "Remaining Work Graph Schema"
type: object
required:
  - graph_id
  - created_at
  - ordering_policy
  - queue_projection
  - graph_actions
  - nodes
  - edges
properties:
  graph_id:
    type: string
  created_at:
    type: string
  ordering_policy:
    type: object
  queue_projection:
    type: object
  graph_actions:
    type: array
  nodes:
    type: array
    items:
      type: object
      required:
        - node_id
        - title
        - status
        - gating_class
        - conflict_domains
        - target_execplan_id
      properties:
        status:
          enum: ["ready", "blocked", "review_gated", "decision_gated", "completed"]
        gating_class:
          enum: ["auto_runnable", "review_gated", "decision_gated"]
  edges:
    type: array
    items:
      type: object
      required:
        - from
        - to
        - relation
      properties:
        relation:
          enum: ["depends_on", "conflicts_with", "informed_by", "gated_by"]
"""


def _seed_repo(root: Path, *, graph_and_queue_on_main: bool, split_test_phase: bool = False, publish_branch: bool = True) -> Path:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Tests")
    _git(root, "config", "user.email", "tests@example.com")
    _write(root / "README.md", "base\n")
    _write(root / "spec" / "remaining-work-graph.schema.yaml", _remaining_work_schema_text())
    if graph_and_queue_on_main:
        _write_json(root / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
        _write(root / "docs/queued-execplans.md", _queue_text())
    _git(root, "add", ".")
    _git(root, "commit", "-m", "docs: base")
    _git(root, "checkout", "-b", BRANCH)

    execplan = root / ".agent" / "execplans" / f"{EXECPLAN_ID}.md"
    _write(execplan, _execplan_text())
    _git(root, "add", execplan.as_posix())
    _git(root, "commit", "-m", "docs(execplan): add policy plan")

    _write(root / "spec" / "policy.yaml", "policy: true\n")
    _git(root, "add", "spec/policy.yaml")
    _git(root, "commit", "-m", "spec(policy): add policy spec")

    _write(root / "src" / "policy_runtime.py", "POLICY = True\n")
    _git(root, "add", "src/policy_runtime.py")
    _git(root, "commit", "-m", "feat(policy): add runtime")

    _write(root / "tests" / "policy_runtime.txt", "ok\n")
    _git(root, "add", "tests/policy_runtime.txt")
    _git(root, "commit", "-m", "test(policy): add coverage")
    if split_test_phase:
        _write(root / "tests" / "policy_runtime_extra.txt", "extra\n")
        _git(root, "add", "tests/policy_runtime_extra.txt")
        _git(root, "commit", "-m", "test(policy): add extra coverage")

    if not graph_and_queue_on_main:
        _write_json(root / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
        _write(root / "docs/queued-execplans.md", _queue_text())
        _git(root, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
        _git(root, "commit", "-m", "docs(policy): reconcile graph and queue")

    if publish_branch:
        _seed_remote(root)
        _git(root, "push", "-u", "origin", BRANCH)

    return execplan


def _seed_remote(root: Path) -> Path:
    remote = root.parent / f"{root.name}-remote.git"
    subprocess.run(["git", "init", "--bare", remote.as_posix()], check=True, capture_output=True, text=True)
    subprocess.run(["git", "remote", "add", "origin", remote.as_posix()], cwd=root, check=True, capture_output=True, text=True)
    return remote


def test_policy_compliance_passes_for_ordered_branch_with_graph_reconciliation(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)
    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )
    assert code == 0
    assert report["ok"] is True
    assert report["checks"]["graph_binding"]["changed_files_include_graph"] is True
    assert report["checks"]["graph_binding"]["changed_files_include_queue"] is True


def test_policy_compliance_blocks_when_graph_and_queue_are_stale(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=True)
    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )
    assert code == 1
    assert report["ok"] is False
    assert "graph_action_required" in report["blockers"]
    assert "queued_execplans_update_required" in report["blockers"]


def test_policy_compliance_allows_small_late_execplan_progress_update(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(
        execplan,
        _execplan_text().replace("- [ ] Test", "- [x] Test"),
    )
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): update policy progress")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])
    assert any("bounded_execplan_reconciliation" in warning for warning in report["warnings"])


def test_policy_compliance_allows_late_execplan_stale_path_replacement(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(
        execplan,
        _execplan_text().replace(
            "changes:\n  - .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md\n",
            "changes:\n"
            "  - .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md\n"
            "  - tests/test_missing_surface.py\n",
        ),
    )
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): add stale planned path")

    _write(
        execplan,
        _execplan_text().replace(
            "changes:\n  - .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md\n",
            "changes:\n"
            "  - .agent/execplans/20260312-game-policy-compliance-codex-01-execplan.md\n"
            "  - tests/test_real_surface.py\n",
        ).replace("- [ ] Test", "- [x] Test"),
    )
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): replace stale planned path")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("changes_field_not_additive" in blocker for blocker in report["blockers"])
    assert any("bounded_execplan_reconciliation" in warning for warning in report["warnings"])


def test_policy_compliance_allows_multiple_adjacent_test_commits(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False, split_test_phase=True)

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])


def test_policy_compliance_blocks_late_execplan_authority_change(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(
        execplan,
        _execplan_text().replace('approve_policy: codeowners', 'approve_policy: anyone'),
    )
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): update policy authority")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])
    assert any("execplan_reconciliation_violation" in blocker for blocker in report["blockers"])


def test_policy_compliance_allows_bounded_late_policy_repair_sequence(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(execplan, _execplan_text().replace("- [ ] Test", "- [x] Test"))
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): update policy progress")

    _write(tmp_path / "src" / "platform_tools" / "policy_compliance_check.py", "ALLOWED = True\n")
    _write(tmp_path / "tests" / "test_policy_compliance_check.py", "def test_allowed():\n    assert True\n")
    _git(tmp_path, "add", "src/platform_tools/policy_compliance_check.py", "tests/test_policy_compliance_check.py")
    _git(tmp_path, "commit", "-m", "fix(governance): allow bounded follow-up repairs")

    _write(tmp_path / "docs" / "governance.md", "split commits allowed\n")
    _write(tmp_path / "docs" / "agent-game-rules-v1.md", "split commits allowed\n")
    _write(tmp_path / "docs" / "queued-execplans.md", _queue_text() + "\n<!-- bounded follow-up repairs -->\n")
    _git(
        tmp_path,
        "add",
        "docs/governance.md",
        "docs/agent-game-rules-v1.md",
        "docs/queued-execplans.md",
    )
    _git(tmp_path, "commit", "-m", "docs(governance): document bounded follow-up repairs")

    _write(tmp_path / "tests" / "test_policy_compliance_check.py", "def test_allowed():\n    assert True\n\ndef test_more():\n    assert True\n")
    _git(tmp_path, "add", "tests/test_policy_compliance_check.py")
    _git(tmp_path, "commit", "-m", "test(governance): lock bounded follow-up repairs")

    _write(
        tmp_path / "src" / "platform_tools" / "policy_compliance_check.py",
        "ALLOWED = True\nBOUNDED = True\n",
    )
    _write(
        tmp_path / "tests" / "test_policy_compliance_check.py",
        "def test_allowed():\n    assert True\n\ndef test_more():\n    assert True\n\ndef test_bounded():\n    assert True\n",
    )
    _git(tmp_path, "add", "src/platform_tools/policy_compliance_check.py", "tests/test_policy_compliance_check.py")
    _git(tmp_path, "commit", "-m", "feat(governance): enforce bounded follow-up repairs")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])
    assert len([warning for warning in report["warnings"] if "bounded_policy_repair_commit" in warning]) == 3


def test_policy_compliance_allows_late_graph_queue_reconciliation_repair(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _remaining_work_schema_text())
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", BRANCH)

    execplan = tmp_path / ".agent" / "execplans" / f"{EXECPLAN_ID}.md"
    _write(execplan, _execplan_text())
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): add policy plan")

    _write_json(tmp_path / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
    _write(tmp_path / "docs/queued-execplans.md", _queue_text())
    _git(tmp_path, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
    _git(tmp_path, "commit", "-m", "docs(governance): reconcile graph and queue")

    _write(tmp_path / "spec" / "policy.yaml", "policy: true\n")
    _git(tmp_path, "add", "spec/policy.yaml")
    _git(tmp_path, "commit", "-m", "spec(policy): add policy spec")

    _seed_remote(tmp_path)
    _git(tmp_path, "push", "-u", "origin", BRANCH)

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])
    assert any("bounded_branch_reconciliation_commit" in warning for warning in report["warnings"])


def test_policy_compliance_allows_branch_reconciliation_with_active_execplan(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _remaining_work_schema_text())
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", BRANCH)

    execplan = tmp_path / ".agent" / "execplans" / f"{EXECPLAN_ID}.md"
    _write(execplan, _execplan_text())
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): add policy plan")

    _write_json(tmp_path / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
    _write(tmp_path / "docs/queued-execplans.md", _queue_text())
    _write(execplan, _execplan_text().replace("- [ ] Test", "- [x] Test"))
    _git(
        tmp_path,
        "add",
        "artifacts/planner/research/remaining-work-graph.json",
        "docs/queued-execplans.md",
        execplan.as_posix(),
    )
    _git(tmp_path, "commit", "-m", "docs(governance): promote board-action api slice ready")

    _write(tmp_path / "spec" / "policy.yaml", "policy: true\n")
    _git(tmp_path, "add", "spec/policy.yaml")
    _git(tmp_path, "commit", "-m", "spec(policy): add policy spec")

    _seed_remote(tmp_path)
    _git(tmp_path, "push", "-u", "origin", BRANCH)

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])
    assert any("bounded_branch_reconciliation_commit" in warning for warning in report["warnings"])


def test_policy_compliance_blocks_unbounded_late_runtime_follow_up(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(tmp_path / "src" / "policy_runtime_followup.py", "FOLLOW_UP = True\n")
    _git(tmp_path, "add", "src/policy_runtime_followup.py")
    _git(tmp_path, "commit", "-m", "fix(policy): add unrelated runtime follow-up")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert any("procedural_commit_order_violation" in blocker for blocker in report["blockers"])


def test_policy_compliance_surfaces_anti_cheat_blockers(monkeypatch, tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    monkeypatch.setattr(
        "platform_tools.policy_compliance_check.check_anti_cheat",
        lambda **kwargs: (
            1,
            {
                "ok": False,
                "blockers": ["protected_surface_denied:src/platform_tools/policy_compliance_check.py:referee_surface"],
            },
        ),
    )

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert "anti_cheat:protected_surface_denied:src/platform_tools/policy_compliance_check.py:referee_surface" in report["blockers"]
    assert report["checks"]["anti_cheat"]["ok"] is False


def test_policy_compliance_blocks_published_branch_history_rewrite_without_exception(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(tmp_path / "docs" / "governance.md", "rewrite after publish\n")
    _git(tmp_path, "add", "docs/governance.md")
    _git(tmp_path, "commit", "-m", "docs(governance): rewrite after publish")
    _git(tmp_path, "push", "origin", BRANCH)
    _git(tmp_path, "reset", "--hard", "HEAD^")

    _write(tmp_path / "docs" / "governance.md", "replacement history\n")
    _git(tmp_path, "add", "docs/governance.md")
    _git(tmp_path, "commit", "-m", "docs(governance): replacement history")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert "published_branch_history_rewrite_violation" in report["blockers"]
    assert report["checks"]["branch_rewrite_guard"]["published_ref_exists"] is True
    assert report["checks"]["branch_rewrite_guard"]["non_fast_forward"] is True
    assert report["checks"]["branch_rewrite_guard"]["authorized_exception_id"] == ""


def test_policy_compliance_allows_published_branch_history_rewrite_with_exception(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False)

    _write(tmp_path / "docs" / "governance.md", "rewrite after publish\n")
    _git(tmp_path, "add", "docs/governance.md")
    _git(tmp_path, "commit", "-m", "docs(governance): rewrite after publish")
    _git(tmp_path, "push", "origin", BRANCH)
    _git(tmp_path, "reset", "--hard", "HEAD^")

    _write(
        tmp_path / ".agent" / "governance" / "exceptions.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-12",
                "exceptions:",
                "  - id: branch-rewrite-001",
                f"    scope: branch_rewrite:{BRANCH}",
                "    owner: github:justin-napolitano",
                "    rationale: authorized history rewrite for branch repair",
                "    approved_by: github:justin-napolitano",
                "    created_at: 2026-03-12T00:00:00Z",
                "    expires_at: 2026-03-19T00:00:00Z",
                "    status: active",
                "    bypass_evidence:",
                "      - chat:explicit-human-authorization",
                "",
            ]
        ),
    )
    _write(tmp_path / "docs" / "governance.md", "replacement history\n")
    _git(tmp_path, "add", ".agent/governance/exceptions.yaml", "docs/governance.md")
    _git(tmp_path, "commit", "-m", "docs(governance): replacement history")

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert report["checks"]["branch_rewrite_guard"]["published_ref_exists"] is True
    assert report["checks"]["branch_rewrite_guard"]["non_fast_forward"] is True
    assert report["checks"]["branch_rewrite_guard"]["authorized_exception_id"] == "branch-rewrite-001"


def test_policy_compliance_blocks_unpublished_impl_branch(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path, graph_and_queue_on_main=False, publish_branch=False)

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 1
    assert "implementation_branch_not_published" in report["blockers"]
    assert report["checks"]["branch_rewrite_guard"]["published_ref_exists"] is False


def test_policy_compliance_allows_commit_hard_limit_with_active_exception(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _write(tmp_path / "spec" / "remaining-work-graph.schema.yaml", _remaining_work_schema_text())
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", BRANCH)

    execplan = tmp_path / ".agent" / "execplans" / f"{EXECPLAN_ID}.md"
    _write(execplan, _execplan_text())
    _git(tmp_path, "add", execplan.as_posix())
    _git(tmp_path, "commit", "-m", "docs(execplan): add policy plan")

    _write_json(tmp_path / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
    _write(tmp_path / "docs/queued-execplans.md", _queue_text())
    _git(tmp_path, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
    _git(tmp_path, "commit", "-m", "docs(governance): reconcile graph and queue")

    _write(tmp_path / "spec" / "policy.yaml", "policy: true\n")
    _git(tmp_path, "add", "spec/policy.yaml")
    _git(tmp_path, "commit", "-m", "spec(policy): add policy spec")

    large_text = "A = True\n" * 450
    _write(tmp_path / "src" / "policy_runtime.py", large_text)
    _git(tmp_path, "add", "src/policy_runtime.py")
    _git(tmp_path, "commit", "-m", "feat(policy): add oversized runtime")
    oversized_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    _write(
        tmp_path / ".agent" / "governance" / "exceptions.yaml",
        "\n".join(
            [
                "version: v1",
                "last_updated: 2026-03-13",
                "exceptions:",
                "  - id: commit-limit-001",
                f"    scope: commit_hard_limit:{BRANCH}:{oversized_commit}",
                "    owner: github:justin-napolitano",
                "    rationale: explicit human approval to tolerate one oversized runtime commit on the active branch",
                "    approved_by: github:justin-napolitano",
                "    created_at: 2026-03-13T00:00:00Z",
                "    expires_at: 2026-03-20T00:00:00Z",
                "    status: active",
                "    bypass_evidence:",
                "      - chat:explicit-human-authorization",
                "",
            ]
        ),
    )
    _git(tmp_path, "add", ".agent/governance/exceptions.yaml")
    _git(tmp_path, "commit", "-m", "docs(governance): allow active commit limit exception")
    _seed_remote(tmp_path)
    _git(tmp_path, "push", "-u", "origin", BRANCH)

    code, report = check_policy_compliance(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )

    assert code == 0
    assert report["ok"] is True
    assert not any("commit_hard_limit_exceeded" in blocker for blocker in report["blockers"])
    assert any("commit_hard_limit_exception" in warning for warning in report["warnings"])
