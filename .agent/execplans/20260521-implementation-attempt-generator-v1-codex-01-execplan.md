---
id: "20260521-implementation-attempt-generator-v1-codex-01"
title: "Implementation Attempt Generator V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/generate_implementation_attempt.py
  - bin/generate-implementation-attempt
  - tests/test_generate_implementation_attempt.py
  - docs/execution-era-runtime-research-v1.md
  - docs/execution-era-loop-v1.md
  - artifacts/planner/research/implementation-attempt-generator-v1-dag.json
  - .agent/execplans/20260521-implementation-attempt-generator-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/implementation-attempt-generator-v1"
initiative_node_id: "initiative-implementation-attempt-generator-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "attempt-generator-tests"
      command: "uv run pytest tests/test_generate_implementation_attempt.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Read execution_unit packet"
    priority: "P0"
  - title: "Generate bounded implementation_attempt packet"
    priority: "P0"
  - title: "Keep generation non-mutating"
    priority: "P0"
  - title: "Preserve owned changes and validation command refs"
    priority: "P0"
  - title: "Add fixtures and tests"
    priority: "P0"

depends_on:
  - "20260521-execution-unit-materializer-v1-codex-01"
source_artifacts:
  - docs/execution-era-runtime-research-v1.md
  - docs/execution-era-loop-v1.md
  - spec/contracts/implementation-attempt.schema.yaml
---

## Objective

Create the first runtime bridge from `execution_unit` to `implementation_attempt`.

V1 should generate attempt packets only. It must not edit source files or claim completion.

## Research Basis

- AlphaEvolve supports generate/evaluate/select candidate loops.
- SWE-agent supports explicit agent-computer interfaces for software work.
- Agentless warns that simple bounded software flows can outperform complex autonomous agents.
- W3C PROV-DM supports preserving derivation from execution unit to attempt.

## Scope

In scope:

- consume one `execution_unit`
- emit one or more `implementation_attempt` packets
- copy `owned_changes` into `changed_artifact_refs` as intended targets
- copy `validation_commands` into `validation_command_refs`
- record attempt family, assumptions, risks, and status
- emit a generation report

Out of scope:

- writing code
- applying patches
- running validation commands
- evaluating attempts
- selecting attempts

## CLI Contract

Command:

- `bin/generate-implementation-attempt`

Arguments:

- `--root`
- `--execution-unit-path`
- `--output-root`
- optional `--attempt-family`
- optional `--max-attempts`

Outputs:

- `implementation-attempt-XX.packet.json`
- `implementation-attempt-generation.report.json`

## Acceptance

- valid execution unit emits at least one attempt packet
- generated attempt references the source execution unit
- generated attempt does not mutate files
- generated attempt includes changed artifact refs from owned changes
- generated attempt includes validation command refs
- execution unit missing validation commands blocks

## Anti-Drift Rules

- generator does not evaluate
- generator does not select
- generator does not create solution artifacts
- generator must not invent files outside `owned_changes`
