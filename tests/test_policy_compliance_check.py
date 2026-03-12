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
            }
        ],
        "edges": [],
    }


def _queue_text() -> str:
    return (
        "# Queued ExecPlans\n\n"
        f"1. `{EXECPLAN_ID}`\n"
        "   - status: `ready`\n"
        f"   - implementation branch: `{BRANCH}`\n"
    )


def _seed_repo(root: Path, *, graph_and_queue_on_main: bool) -> Path:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Tests")
    _git(root, "config", "user.email", "tests@example.com")
    _write(root / "README.md", "base\n")
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

    if not graph_and_queue_on_main:
        _write_json(root / "artifacts/planner/research/remaining-work-graph.json", _remaining_work_graph())
        _write(root / "docs/queued-execplans.md", _queue_text())
        _git(root, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
        _git(root, "commit", "-m", "docs(policy): reconcile graph and queue")

    return execplan


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
