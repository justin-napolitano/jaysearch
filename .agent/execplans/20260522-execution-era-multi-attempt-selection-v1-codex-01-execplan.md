---
id: "20260522-execution-era-multi-attempt-selection-v1-codex-01"
title: "Execution ERA Multi Attempt Selection V1"
owner: "agent/codex"
created: "2026-05-22T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/execution-era-multi-attempt-selection-research-v1.md
  - artifacts/planner/research/execution-era-multi-attempt-selection-v1-dag.json
  - spec/contracts/attempt-selection.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/select_implementation_attempt.py
  - bin/select-implementation-attempt
  - src/platform_tools/run_execution_era_loop_smoke.py
  - tests/test_select_implementation_attempt.py
  - tests/test_attempt_selection_contracts.py
  - tests/test_run_execution_era_loop_smoke.py
approve_policy: codeowners
reviewers:
  - "github:jna31a"

validation:
  tests:
    - name: "attempt-selection-tests"
      command: "uv run pytest tests/test_select_implementation_attempt.py tests/test_attempt_selection_contracts.py"
      expected_exit: 0
    - name: "execution-era-regression"
      command: "uv run pytest tests/test_apply_solution_artifact.py tests/test_applied_solution_contracts.py tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_emit_solution_artifact.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Research deterministic attempt selection"
    priority: "P0"
  - title: "Define attempt_selection contract"
    priority: "P0"
  - title: "Implement deterministic selector"
    priority: "P0"
  - title: "Wire multi-attempt smoke runner"
    priority: "P0"
  - title: "Test selection and anti-cheat rules"
    priority: "P0"

depends_on:
  - "20260522-execution-era-loop-apply-integration-v1-codex-01"
source_artifacts:
  - docs/execution-era-multi-attempt-selection-research-v1.md
  - artifacts/planner/research/execution-era-multi-attempt-selection-v1-dag.json
---

## Objective

Add deterministic multi-attempt selection to the execution ERA loop.

The selector consumes evaluated attempts, rejects blocked attempts, scores eligible attempts, and emits an `attempt_selection` packet that identifies the selected attempt/evaluation pair and rejected candidates.

## Scope

In scope:

- add `attempt_selection` contract
- add deterministic scoring policy
- add selector CLI
- preserve selected and rejected attempt/evaluation refs
- wire optional multi-attempt selection into smoke runner
- tests for scoring, rejection, tie-breaking, and runner integration

Out of scope:

- LLM judge selection
- autonomous retries
- current-worktree apply
- candidate patch synthesis
- non-deterministic scoring

## Acceptance

- blocked evaluations are ineligible
- promoted evaluation with stronger evidence is selected
- tie-breaking is deterministic
- selector emits rejected refs
- smoke runner can emit solution artifact from selected attempt
- existing single-attempt path remains compatible
- design iteration reports no blockers
