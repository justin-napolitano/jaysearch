---
id: "20260521-execution-era-loop-smoke-v1-codex-01"
title: "Execution ERA Loop Smoke V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/run_execution_era_loop_smoke.py
  - bin/run-execution-era-loop-smoke
  - tests/test_run_execution_era_loop_smoke.py
  - docs/execution-era-runtime-research-v1.md
  - docs/project-format-and-state-v1.md
  - artifacts/planner/research/execution-era-loop-smoke-v1-dag.json
  - .agent/execplans/20260521-execution-era-loop-smoke-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/execution-era-loop-smoke-v1"
initiative_node_id: "initiative-execution-era-loop-smoke-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execution-era-loop-smoke-tests"
      command: "uv run pytest tests/test_run_execution_era_loop_smoke.py tests/test_generate_implementation_attempt.py tests/test_evaluate_implementation_attempt.py tests/test_emit_solution_artifact.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Compose attempt generation"
    priority: "P0"
  - title: "Compose attempt evaluation"
    priority: "P0"
  - title: "Compose solution emission"
    priority: "P0"
  - title: "Emit loop report"
    priority: "P0"
  - title: "Add fixture end-to-end smoke"
    priority: "P0"

depends_on:
  - "20260521-solution-artifact-emitter-v1-codex-01"
source_artifacts:
  - docs/execution-era-runtime-research-v1.md
  - docs/project-format-and-state-v1.md
---

## Objective

Run the local execution ERA packet loop from one execution unit through solution artifact emission.

This is a smoke runner, not a general autonomous executor.

## Research Basis

- AlphaEvolve supports generate/evaluate/select loops.
- Agentless supports decomposing software repair into simple stages.
- SWE-agent supports explicit environment/tool interaction boundaries.
- PROV-DM supports retaining derivation through the full loop.

## Scope

In scope:

- consume one `execution_unit`
- call attempt generator
- call attempt evaluator
- call solution artifact emitter
- emit `execution-era-loop-smoke.report.json`
- surface blockers from any step

Out of scope:

- arbitrary code generation
- multi-attempt ranking
- autonomous retries
- live external research

## CLI Contract

Command:

- `bin/run-execution-era-loop-smoke`

Arguments:

- `--root`
- `--execution-unit-path`
- `--output-root`
- optional `--validation-result-ref`

Outputs:

- attempt packet refs
- evaluation packet ref
- solution artifact ref
- smoke report

## Acceptance

- valid fixture execution unit completes through solution artifact
- blocked attempt generation blocks the loop
- blocked evaluation blocks solution emission
- smoke report includes all child step reports and packet refs

## Anti-Drift Rules

- smoke runner orchestrates packet tools only
- smoke runner does not directly edit code
- smoke runner must preserve failed step reports
- smoke runner must not emit solution artifacts without promoted evaluation
