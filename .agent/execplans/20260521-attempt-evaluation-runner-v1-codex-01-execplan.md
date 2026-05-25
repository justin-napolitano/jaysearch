---
id: "20260521-attempt-evaluation-runner-v1-codex-01"
title: "Attempt Evaluation Runner V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/evaluate_implementation_attempt.py
  - bin/evaluate-implementation-attempt
  - tests/test_evaluate_implementation_attempt.py
  - docs/execution-era-runtime-research-v1.md
  - docs/execution-era-loop-v1.md
  - artifacts/planner/research/attempt-evaluation-runner-v1-dag.json
  - .agent/execplans/20260521-attempt-evaluation-runner-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/attempt-evaluation-runner-v1"
initiative_node_id: "initiative-attempt-evaluation-runner-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "attempt-evaluation-tests"
      command: "uv run pytest tests/test_evaluate_implementation_attempt.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Read implementation_attempt and execution_unit"
    priority: "P0"
  - title: "Validate source refs"
    priority: "P0"
  - title: "Consume validation evidence refs"
    priority: "P0"
  - title: "Emit attempt_evaluation packet"
    priority: "P0"
  - title: "Block attempts outside owned changes"
    priority: "P0"

depends_on:
  - "20260521-implementation-attempt-generator-v1-codex-01"
source_artifacts:
  - docs/execution-era-runtime-research-v1.md
  - spec/contracts/attempt-evaluation.schema.yaml
---

## Objective

Evaluate one `implementation_attempt` against its source `execution_unit`.

V1 should be evidence-consuming and optionally command-running later. The first implementation may support fixture validation results before shell execution.

## Research Basis

- SWE-bench motivates task-grounded validation over plausibility.
- CRITIC motivates tool-grounded critique and correction.
- Agentless motivates simple validation as a core phase.
- PROV-DM motivates preserving evaluation derivation and evidence refs.

## Scope

In scope:

- validate attempt references the execution unit
- check changed artifacts are within execution unit owned changes
- consume validation result refs or command refs
- emit `attempt_evaluation`
- produce blockers for missing validation evidence

Out of scope:

- selecting attempts
- emitting solution artifacts
- autonomous repair
- broad test discovery

## CLI Contract

Command:

- `bin/evaluate-implementation-attempt`

Arguments:

- `--root`
- `--execution-unit-path`
- `--attempt-path`
- `--output-root`
- optional `--validation-result-ref`

Outputs:

- `attempt-evaluation.packet.json`
- `attempt-evaluation.report.json`

## Acceptance

- valid attempt with evidence emits promoted evaluation
- attempt with changed artifacts outside owned changes blocks
- attempt missing validation command refs blocks or needs revision
- evaluation packet includes validation results, review findings, score breakdown, blockers, evidence refs

## Anti-Drift Rules

- evaluator does not edit files
- evaluator does not select final solution
- evaluator must report blockers explicitly
- evaluator must not infer validation success without evidence
