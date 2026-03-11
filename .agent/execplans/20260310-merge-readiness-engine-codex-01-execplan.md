---
id: "20260310-merge-readiness-engine-codex-01-execplan"
title: "Implement merge-readiness engine for Codex orchestration"
owner: "agent/codex-01"
created: "2026-03-10T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260310-merge-readiness-engine-codex-01-execplan.md
  - bin/merge-readiness-check
  - bin/merge-readiness-smoke-test
  - pyproject.toml
  - src/platform_tools/merge_readiness.py
  - tests/test_merge_readiness.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"

draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260310-merge-readiness-engine-codex-01-execplan-codex-01-20260310"
draft_created: "2026-03-10T00:00:00Z"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260310-merge-readiness-engine-codex-01-execplan.md"
      expected_exit: 0
    - name: "merge-readiness-smoke-test"
      command: "bin/merge-readiness-smoke-test"
      expected_exit: 0
    - name: "merge-readiness-pytest"
      command: "uv run pytest tests/test_merge_readiness.py"
      expected_exit: 0

tasks:
  - title: "Implement merge-readiness checker runtime"
    priority: "P1"
  - title: "Aggregate ExecPlan validations and governance checks into one report"
    priority: "P1"
  - title: "Enforce generated-artifact hygiene and commit-shape checks"
    priority: "P1"
  - title: "Add merge-readiness CLI wrapper and smoke test"
    priority: "P1"
  - title: "Add focused tests for pass and fail paths"
    priority: "P1"

depends_on:
  - "20260310-codex-orchestrator-contract-codex-01-execplan"
  - "20260310-rule-graph-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first merge-readiness engine for Codex orchestration. This engine must aggregate the existing referee commands, the active ExecPlan validation contract, generated-artifact hygiene, and branch commit-shape rules into one deterministic machine-readable readiness report.

This slice implements the enforcement hub described by the orchestrator contract. It does not implement the full implementation-phase orchestrator.

## Progress

- [ ] Add merge-readiness runtime
- [ ] Add wrapper command
- [ ] Add smoke test
- [ ] Add focused tests
- [ ] Run validation

## Surprises & Discoveries

- Scope-blocker graph enforcement may remain deferred when no graph id is available on the branch.
- The merge-readiness engine should prefer explicit deferral over false claims of certainty.

## Decision Log

- 2026-03-10 / agent-codex-01 / The engine will use the active ExecPlan validation list as the primary contract for required checks.
- 2026-03-10 / agent-codex-01 / The engine will add governance checks for rule-graph validation, generated-artifact hygiene, and commit-shape enforcement.
- 2026-03-10 / agent-codex-01 / Checks the engine cannot yet prove will be reported as deferred rather than silently treated as pass.

## Outcomes & Retrospective

Expected outcomes:

- machine-readable merge-readiness report
- deterministic branch hygiene checks
- commit-size and procedural-order checks
- dedicated smoke test and focused tests

## Context and Orientation

The repository already has validator components and an orchestrator contract, but it lacks a single enforcement surface that answers whether a branch is merge-ready and why.

This slice fills that gap.

## Plan of Work

1. Implement the runtime checker.
2. Reuse the active ExecPlan validation list.
3. Add branch hygiene and commit-shape checks.
4. Add wrapper, tests, and smoke coverage.
5. Validate the slice.

## Concrete Steps

1. Add `src/platform_tools/merge_readiness.py`.
2. Add `bin/merge-readiness-check`.
3. Add `bin/merge-readiness-smoke-test`.
4. Register the CLI in `pyproject.toml`.
5. Add `tests/test_merge_readiness.py`.
6. Run `bin/execplan-validate`, `bin/merge-readiness-smoke-test`, and `uv run pytest tests/test_merge_readiness.py`.

## Validation and Acceptance

Acceptance criteria:

- the checker emits a deterministic machine-readable readiness report
- the checker fails when required validations fail
- the checker fails when generated artifacts are left dirty
- the checker fails when procedural commit order is violated
- the smoke test passes
- focused tests pass

## Idempotence and Recovery

- the checker is read-only with respect to repository state
- the smoke test may create disposable temp artifacts but must clean them up
- repeated runs against the same branch state should produce the same readiness result

## Artifacts and Notes

- `src/platform_tools/merge_readiness.py`
- `bin/merge-readiness-check`
- `bin/merge-readiness-smoke-test`
- `tests/test_merge_readiness.py`

## Interfaces and Dependencies

- `docs/merge-readiness-contract.md`
- `spec/codex-orchestrator.yaml`
- `src/platform_tools/execplan_lint.py`
- `src/platform_tools/rule_graph_check.py`
- `src/platform_tools/citation_check.py`
