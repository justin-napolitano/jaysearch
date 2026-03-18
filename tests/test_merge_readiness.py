from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.merge_readiness import check_merge_readiness
from platform_tools.policy_compliance_check import EXCEPTION_REGISTRY_PATH


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


def _seed_repo(root: Path) -> Path:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.name", "Tests")
    _git(root, "config", "user.email", "tests@example.com")
    _write(root / "README.md", "base\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "docs: base")
    _git(root, "checkout", "-b", "feature/merge-readiness-test")

    execplan = root / ".agent" / "execplans" / "20260310-test-plan-codex-01-execplan.md"
    _write(
        execplan,
        """---
id: "20260310-test-plan-codex-01-execplan"
title: "Test plan"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-test-plan-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/test"
draft_created: "2026-03-10T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-test-plan-codex-01-execplan.md"
      expected_exit: 0
    - name: "smoke"
      command: "bin/smoke-pass"
      expected_exit: 0
tasks:
  - title: "Test"
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
""",
    )
    _write(root / "spec" / "slice.yaml", "slice: true\n")
    _write(root / "docs" / "note.md", "note\n")
    _write(root / "bin" / "execplan-validate", "#!/usr/bin/env bash\nexit 0\n")
    _write(root / "bin" / "smoke-pass", "#!/usr/bin/env bash\nexit 0\n")
    _write(root / "bin" / "rule-graph-check", "#!/usr/bin/env bash\nexit 0\n")
    _write(root / "bin" / "citation-check", "#!/usr/bin/env bash\nexit 0\n")
    for script in ["execplan-validate", "smoke-pass", "rule-graph-check", "citation-check"]:
        subprocess.run(["chmod", "+x", str(root / "bin" / script)], check=True)

    _git(root, "add", ".agent/execplans/20260310-test-plan-codex-01-execplan.md")
    _git(root, "commit", "-m", "docs(execplan): add test plan")
    _git(root, "add", "spec/slice.yaml")
    _git(root, "commit", "-m", "spec(test): add slice spec")
    _git(root, "add", "docs/note.md")
    _git(root, "commit", "-m", "docs(test): add note")
    return execplan


def test_merge_readiness_passes_for_clean_branch(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path)
    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )
    assert code == 0
    assert report["readiness"] is True
    assert report["dirty_artifacts"] == []


def test_merge_readiness_fails_for_dirty_generated_artifact(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path)
    _write(tmp_path / "artifacts" / "planner" / "graphs" / "pg-dirty.json", "{}\n")
    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )
    assert code == 1
    assert "dirty_generated_artifacts" in report["failing_checks"]


def test_merge_readiness_fails_for_wrong_commit_order(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", "feature/merge-readiness-test")

    execplan = tmp_path / ".agent" / "execplans" / "20260310-test-plan-codex-01-execplan.md"
    _write(
        execplan,
        """---
id: "20260310-test-plan-codex-01-execplan"
title: "Test plan"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-test-plan-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/test"
draft_created: "2026-03-10T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-test-plan-codex-01-execplan.md"
      expected_exit: 0
    - name: "smoke"
      command: "bin/smoke-pass"
      expected_exit: 0
tasks:
  - title: "Test"
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
""",
    )
    _write(tmp_path / "docs" / "note.md", "note\n")
    _write(tmp_path / "spec" / "slice.yaml", "slice: true\n")
    _write(tmp_path / "bin" / "execplan-validate", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "smoke-pass", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "rule-graph-check", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "citation-check", "#!/usr/bin/env bash\nexit 0\n")
    for script in ["execplan-validate", "smoke-pass", "rule-graph-check", "citation-check"]:
        subprocess.run(["chmod", "+x", str(tmp_path / "bin" / script)], check=True)

    _git(tmp_path, "add", "docs/note.md")
    _git(tmp_path, "commit", "-m", "docs(test): add note")
    _git(tmp_path, "add", ".agent/execplans/20260310-test-plan-codex-01-execplan.md")
    _git(tmp_path, "commit", "-m", "docs(execplan): add test plan")
    _git(tmp_path, "add", "spec/slice.yaml")
    _git(tmp_path, "commit", "-m", "spec(test): add slice spec")

    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
    )
    assert code == 1
    assert any("procedural_commit_order_violation:" in item for item in report["failing_checks"])


def test_merge_readiness_allows_bounded_branch_reconciliation_commit(tmp_path: Path) -> None:
    execplan = _seed_repo(tmp_path)
    _write(tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json", "{}\n")
    _write(tmp_path / "docs" / "queued-execplans.md", "queue\n")
    _git(tmp_path, "add", "artifacts/planner/research/remaining-work-graph.json", "docs/queued-execplans.md")
    _git(tmp_path, "commit", "-m", "docs(governance): promote hostile-review ready state")

    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
        include_validation_runs=False,
    )

    assert code == 0
    assert report["readiness"] is True
    assert not any("procedural_commit_order_violation" in item for item in report["failing_checks"])
    assert any("bounded_branch_reconciliation_commit" in item for item in report["warnings"])


def test_merge_readiness_allows_commit_hard_limit_with_active_exception(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "docs: base")
    _git(tmp_path, "checkout", "-b", "feature/merge-readiness-test")

    execplan = tmp_path / ".agent" / "execplans" / "20260310-test-plan-codex-01-execplan.md"
    _write(
        execplan,
        """---
id: "20260310-test-plan-codex-01-execplan"
title: "Test plan"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-test-plan-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/test"
draft_created: "2026-03-10T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-test-plan-codex-01-execplan.md"
      expected_exit: 0
    - name: "smoke"
      command: "bin/smoke-pass"
      expected_exit: 0
tasks:
  - title: "Test"
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
""",
    )
    _write(tmp_path / "spec" / "slice.yaml", "slice: true\n")
    _write(tmp_path / "bin" / "execplan-validate", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "smoke-pass", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "rule-graph-check", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "citation-check", "#!/usr/bin/env bash\nexit 0\n")
    for script in ["execplan-validate", "smoke-pass", "rule-graph-check", "citation-check"]:
        subprocess.run(["chmod", "+x", str(tmp_path / "bin" / script)], check=True)

    _git(tmp_path, "add", ".agent/execplans/20260310-test-plan-codex-01-execplan.md")
    _git(tmp_path, "commit", "-m", "docs(execplan): add test plan")
    _git(tmp_path, "add", "spec/slice.yaml")
    _git(tmp_path, "commit", "-m", "spec(test): add slice spec")
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    oversized_path = tmp_path / "src" / "big_runtime.py"
    _write(oversized_path, "".join(f"line_{index} = {index}\n" for index in range(410)))
    _git(tmp_path, "add", "src/big_runtime.py")
    _git(tmp_path, "commit", "-m", "feat(runtime): add oversized runtime")
    oversized_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _write(
        tmp_path / EXCEPTION_REGISTRY_PATH,
        "\n".join(
            [
                "exceptions:",
                "  - id: commit-limit-001",
                "    status: active",
                f"    scope: commit_hard_limit:{branch}:{oversized_commit}",
                '    owner: "github:test-owner"',
                '    approved_by: "github:test-owner"',
                '    rationale: "Allow one bounded oversized runtime commit during transition."',
                '    created_at: "2026-03-13T00:00:00Z"',
                '    expires_at: "2026-03-20T00:00:00Z"',
                "    bypass_evidence:",
                '      - "chat:explicit-human-authorization"',
                "",
            ]
        ),
    )
    _git(tmp_path, "add", EXCEPTION_REGISTRY_PATH)
    _git(tmp_path, "commit", "-m", "docs(governance): allow active commit limit exception")

    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        execplan_path=execplan.as_posix(),
        base_ref="main",
        include_validation_runs=False,
    )

    assert code == 0
    assert report["readiness"] is True
    assert not any("commit_hard_limit_exceeded" in item for item in report["failing_checks"])
    assert any("commit_hard_limit_exception" in item for item in report["warnings"])


def test_merge_readiness_discovers_execplan_from_implementation_branch_mapping(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.name", "Tests")
    _git(tmp_path, "config", "user.email", "tests@example.com")
    _write(tmp_path / "README.md", "base\n")

    execplan_rel = ".agent/execplans/20260318-test-ready-codex-01-execplan.md"
    execplan = tmp_path / execplan_rel
    _write(
        execplan,
        """---
id: "20260318-test-ready-codex-01-execplan"
title: "Ready implementation test"
owner: "agent/codex-01"
created: "2026-03-18T00:00:00Z"
status: approved
base_branch: main
changes:
  - spec/slice.yaml
approve_policy: codeowners
reviewers:
  - "github:test-owner"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260318-test-ready-codex-01"
draft_created: "2026-03-18T00:00:00Z"
finalized_by: "github:test-owner"
finalized_at: "2026-03-18T00:00:00Z"
finalized_in_pr: "82"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260318-test-ready-codex-01-execplan.md"
      expected_exit: 0
    - name: "smoke"
      command: "bin/smoke-pass"
      expected_exit: 0
tasks:
  - title: "Implement"
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
""",
    )
    _write_json(
        tmp_path / "artifacts" / "planner" / "research" / "remaining-work-graph.json",
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
                "last_reconciled_action_id": "rwg-action-20260318-002-promote-rwg-025",
                "ready_execplan_ids": ["20260318-test-ready-codex-01-execplan"],
            },
            "graph_actions": [],
            "nodes": [
                {
                    "node_id": "rwg-025",
                    "title": "Rule authority consolidation",
                    "status": "ready",
                    "gating_class": "auto_runnable",
                    "conflict_domains": ["governance"],
                    "target_execplan_id": "20260318-test-ready-codex-01-execplan",
                    "goal_area": "governance",
                    "implementation_branch": "impl-execplan/20260318-test-ready-codex-01-execplan-codex-01-20260318",
                    "expected_artifacts": ["spec/slice.yaml"],
                    "ordering": {
                        "queue_position": 1,
                        "ready_order": 1,
                        "tie_breaker": "20260318-test-ready-codex-01-execplan",
                    },
                    "action_state": {
                        "last_action_id": "rwg-action-20260318-002-promote-rwg-025",
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
    _write(tmp_path / "bin" / "execplan-validate", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "smoke-pass", "#!/usr/bin/env bash\nexit 0\n")
    _write(tmp_path / "bin" / "rule-graph-check", "#!/usr/bin/env bash\nexit 0\n")
    for script in ["execplan-validate", "smoke-pass", "rule-graph-check"]:
        subprocess.run(["chmod", "+x", str(tmp_path / "bin" / script)], check=True)
    _git(tmp_path, "add", "README.md", execplan_rel, "artifacts/planner/research/remaining-work-graph.json")
    _git(tmp_path, "commit", "-m", "docs: seed finalized execplan and graph")

    branch = "impl-execplan/20260318-test-ready-codex-01-execplan-codex-01-20260318"
    _git(tmp_path, "checkout", "-b", branch)
    _write(tmp_path / "spec" / "slice.yaml", "slice: true\n")
    _git(tmp_path, "add", "spec/slice.yaml")
    _git(tmp_path, "commit", "-m", "spec(test): add slice spec")

    code, report = check_merge_readiness(
        root=tmp_path.as_posix(),
        base_ref="main",
        include_validation_runs=False,
    )

    assert code == 0
    assert report["readiness"] is True
    assert report["execplan_id"] == "20260318-test-ready-codex-01-execplan"
    assert report["execplan_path"].endswith(execplan_rel)
