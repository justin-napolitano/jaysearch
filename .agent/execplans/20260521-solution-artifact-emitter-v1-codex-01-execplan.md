---
id: "20260521-solution-artifact-emitter-v1-codex-01"
title: "Solution Artifact Emitter V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/emit_solution_artifact.py
  - bin/emit-solution-artifact
  - tests/test_emit_solution_artifact.py
  - docs/execution-era-runtime-research-v1.md
  - docs/execution-era-loop-v1.md
  - artifacts/planner/research/solution-artifact-emitter-v1-dag.json
  - .agent/execplans/20260521-solution-artifact-emitter-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/solution-artifact-emitter-v1"
initiative_node_id: "initiative-solution-artifact-emitter-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "solution-artifact-tests"
      command: "uv run pytest tests/test_emit_solution_artifact.py tests/test_execution_era_contracts.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Read execution_unit, attempt, and evaluation"
    priority: "P0"
  - title: "Require promoted nonblocking evaluation"
    priority: "P0"
  - title: "Emit solution_artifact packet"
    priority: "P0"
  - title: "Preserve rejected attempt refs when provided"
    priority: "P0"
  - title: "Add selection tests"
    priority: "P0"

depends_on:
  - "20260521-attempt-evaluation-runner-v1-codex-01"
source_artifacts:
  - docs/execution-era-runtime-research-v1.md
  - spec/contracts/solution-artifact.schema.yaml
---

## Objective

Emit a `solution_artifact` only after an implementation attempt has a promoted, nonblocking evaluation.

This is the first object that can complete or advance an execution unit.

## Research Basis

- AlphaEvolve supports selecting evaluated candidates rather than trusting first generation.
- Reflexion supports retaining feedback from rejected attempts.
- PROV-DM supports linking selected artifact to attempt, evaluation, evidence, and source execution unit.

## Scope

In scope:

- consume one execution unit
- consume one selected attempt
- consume one attempt evaluation
- require `promotion_status: promoted`
- require empty blockers
- emit `solution_artifact`
- preserve completion evidence refs

Out of scope:

- deciding which attempt is best among many
- running validation commands
- editing files
- closing project nodes automatically

## CLI Contract

Command:

- `bin/emit-solution-artifact`

Arguments:

- `--root`
- `--execution-unit-path`
- `--attempt-path`
- `--evaluation-path`
- `--output-root`
- optional repeated `--rejected-attempt-ref`

Outputs:

- `solution-artifact.packet.json`
- `solution-artifact.report.json`

## Acceptance

- promoted attempt evaluation emits solution artifact
- blocked evaluation does not emit solution artifact
- mismatched execution unit refs block
- solution artifact includes selected attempt, evaluation ref, patch ref, artifact refs, completion evidence refs, and limitations

## Anti-Drift Rules

- solution emitter does not evaluate
- solution emitter does not edit
- solution emitter does not hide rejected attempts
- solution emitter must not claim completion without evidence refs
