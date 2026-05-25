---
id: "20260522-execution-era-loop-apply-integration-v1-codex-01"
title: "Execution ERA Loop Apply Integration V1"
owner: "agent/codex"
created: "2026-05-22T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/execution-era-loop-apply-integration-research-v1.md
  - artifacts/planner/research/execution-era-loop-apply-integration-v1-dag.json
  - src/platform_tools/run_execution_era_loop_smoke.py
  - tests/test_run_execution_era_loop_smoke.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "execution-era-loop-smoke-tests"
      command: "uv run pytest tests/test_run_execution_era_loop_smoke.py"
      expected_exit: 0
    - name: "execution-era-regression"
      command: "uv run pytest tests/test_apply_solution_artifact.py tests/test_applied_solution_contracts.py tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_emit_solution_artifact.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Research optional apply integration"
    priority: "P0"
  - title: "Add --apply-solution flag"
    priority: "P0"
  - title: "Call apply_solution_artifact after solution emission"
    priority: "P0"
  - title: "Record applied_solution refs in smoke packet"
    priority: "P0"
  - title: "Block on failed optional apply"
    priority: "P0"
  - title: "Test compatibility and source immutability"
    priority: "P0"

depends_on:
  - "20260522-apply-solution-artifact-v1-codex-01"
source_artifacts:
  - docs/execution-era-loop-apply-integration-research-v1.md
  - docs/apply-solution-artifact-policy-v1.md
  - artifacts/planner/research/execution-era-loop-apply-integration-v1-dag.json
---

## Objective

Add an explicit optional apply phase to `run-execution-era-loop-smoke`.

The default smoke loop remains non-applying. When `--apply-solution` is provided, the runner calls `apply_solution_artifact` after solution emission and records the resulting `applied_solution`.

## Scope

In scope:

- add `--apply-solution`
- route to `apply_solution_artifact`
- include apply step in `step_reports`
- include `applied_solution_path` in command report
- include `applied_solution_ref` in smoke packet
- block on apply failure
- tests for default behavior, success, failure, and source immutability

Out of scope:

- current-worktree mutation
- applying by default
- retry loops
- patch generation changes

## Acceptance

- existing smoke tests pass without `--apply-solution`
- valid patch loop with `--apply-solution` emits `applied_solution`
- failed post-apply validation blocks the smoke loop
- source file remains unchanged in root after apply-integrated smoke
- design iteration reports no blockers
