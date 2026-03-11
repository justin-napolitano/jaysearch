from __future__ import annotations

import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from platform_tools.merge_readiness import check_merge_readiness


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
