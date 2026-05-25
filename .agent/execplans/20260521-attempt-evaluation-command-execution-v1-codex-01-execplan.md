---
id: "20260521-attempt-evaluation-command-execution-v1-codex-01"
title: "Attempt Evaluation Command Execution V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/evaluate_implementation_attempt.py
  - tests/test_evaluate_implementation_attempt.py
  - spec/attempt-evaluation-command-policy.yaml
  - docs/attempt-evaluation-command-execution-research-v1.md
  - docs/execution-era-runtime-research-v1.md
  - docs/project-format-and-state-v1.md
  - artifacts/planner/research/attempt-evaluation-command-execution-v1-dag.json
  - .agent/execplans/20260521-attempt-evaluation-command-execution-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/attempt-evaluation-command-execution-v1"
initiative_node_id: "initiative-attempt-evaluation-command-execution-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "attempt-evaluation-command-tests"
      command: "uv run pytest tests/test_evaluate_implementation_attempt.py tests/test_run_execution_era_loop_smoke.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define command execution policy"
    priority: "P0"
  - title: "Add optional command execution flag"
    priority: "P0"
  - title: "Validate command is declared and allowed"
    priority: "P0"
  - title: "Capture command output artifacts"
    priority: "P0"
  - title: "Promote only when executed commands pass"
    priority: "P0"

depends_on:
  - "20260521-execution-era-loop-smoke-v1-codex-01"
source_artifacts:
  - docs/attempt-evaluation-command-execution-research-v1.md
  - docs/execution-era-runtime-research-v1.md
  - spec/contracts/attempt-evaluation.schema.yaml
---

## Objective

Add optional execution-backed validation to `attempt-evaluation-runner-v1`.

The evaluator should be able to run declared validation commands and capture output evidence, while staying bounded and non-autonomous.

## Research Basis

- SWE-agent supports explicit command/test execution surfaces.
- Agentless supports simple validate-stage execution without autonomous future-action selection.
- SWE-bench supports task-grounded execution-backed evaluation.
- OpenHands supports sandboxed command execution and reproducible agent harnesses.

## Scope

In scope:

- add command execution policy file
- add `--execute-validation-commands`
- add timeout and output limits
- reject undeclared commands
- reject commands with forbidden shell tokens
- run allowed declared commands from repo root
- capture stdout/stderr/exit code/duration into artifact files
- include output artifact refs in `attempt_evaluation.evidence_refs`
- promote only when all executed commands exit `0` and no boundary blockers exist

Out of scope:

- autonomous retries
- test discovery
- code editing
- command execution outside declared validation refs
- broad shell access

## CLI Contract Changes

Existing command:

- `bin/evaluate-implementation-attempt`

New arguments:

- `--execute-validation-commands`
- `--command-policy-path`
- `--timeout-seconds`

Default behavior:

- command execution disabled unless `--execute-validation-commands` is passed

## Policy Contract

Add:

- `spec/attempt-evaluation-command-policy.yaml`

Required policy concepts:

- allowed command prefixes
- forbidden shell tokens
- default timeout seconds
- max output chars
- require declared command

## Acceptance

- passing declared command promotes attempt and records output artifact
- failing declared command blocks promotion
- undeclared command blocks
- forbidden shell token blocks
- command execution disabled by default
- existing non-command evaluation tests still pass

## Anti-Drift Rules

- evaluator does not mutate implementation files itself
- evaluator does not invent commands
- evaluator does not execute commands unless flag is passed
- evaluator does not accept commands outside execution unit validation commands
- evaluator captures command evidence before promotion
