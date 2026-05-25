---
id: "20260521-execution-unit-materializer-v1-codex-01"
title: "Execution Unit Materializer V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/materialize_execution_unit.py
  - bin/materialize-execution-unit
  - tests/test_materialize_execution_unit.py
  - docs/node-based-project-plan-v1.md
  - docs/execution-era-loop-v1.md
  - artifacts/planner/research/execution-unit-materializer-v1-dag.json
  - .agent/execplans/20260521-execution-unit-materializer-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/execution-unit-materializer-v1"
initiative_node_id: "initiative-execution-unit-materializer-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "execution-unit-materializer-tests"
      command: "uv run pytest tests/test_materialize_execution_unit.py tests/test_validate_node_readiness.py"
      expected_exit: 0
    - name: "a-b-materialization-smoke"
      command: "run materializer against A/B selected scopes after implementation-intent contract is active"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Materialize problem_node from selected_solution_scope"
    priority: "P0"
  - title: "Materialize node_option from implementation intent"
    priority: "P0"
  - title: "Materialize execution_unit from selected option"
    priority: "P0"
  - title: "Run readiness validation"
    priority: "P0"
  - title: "Emit materialization report"
    priority: "P0"

depends_on:
  - "20260521-node-readiness-validator-v1-codex-01"
---

## Objective

Turn selected scopes with implementation intent into problem nodes, node options, and execution units.

This is the first actual bridge from research/planning authority into buildable work contracts.

## Scope

In scope:

- consume selected solution scope
- emit `problem_node`
- emit one selected `node_option`
- emit `execution_unit` only when readiness requirements pass
- report missing fields instead of guessing

Out of scope:

- implementation attempt generation
- code execution
- solution artifact emission

## Acceptance

- A/B selected scopes materialize into problem nodes.
- A/B execution units materialize only if selected scopes carry implementation intent.
- Generic selected scopes block with missing fields.
- Output execution units include owned changes, validation commands, rollback plan, and completion evidence requirements.

## Runtime Contract

Command:

- `bin/materialize-execution-unit`

Arguments:

- `--root`
- `--selected-scope-path`
- `--output-root`
- optional `--target-state`

Default target state:

- `implementation_ready`

Outputs:

- `problem-node.packet.json`
- `node-option.packet.json`
- `execution-unit.packet.json` only when implementation-ready fields exist
- `execution-unit-materialization.report.json`

If materialization blocks, still emit the problem node and missing-field report when possible.

## Mapping Rules

From `selected_solution_scope` to `problem_node`:

- `problem_id` -> `project_id` or node project context
- `selected_solution_summary` -> `problem_statement` fallback
- `in_scope` -> expected outputs or constraints depending content
- `out_of_scope` -> constraints and non-goals
- `evidence_refs` -> evidence refs
- `selection_policy.source_recommendation_ref` -> input ref

From selected scope implementation intent to `node_option`:

- `implementation_intent.summary` -> approach summary
- `contract_changes`, `runtime_changes`, `validation_changes`, `docs_changes` -> expected changes
- selected candidate id -> option id suffix

From `node_option` to `execution_unit`:

- expected changes -> owned changes only when file/artifact paths are explicit
- validation changes -> validation commands only when commands are explicit
- handoff requirements -> required inputs and completion evidence requirements

Do not invent file paths or validation commands.

If paths/commands are absent, block and report missing fields.

## Required Tests

- generic selected scope emits problem node but blocks execution unit
- selected scope with implementation intent but no file paths blocks execution unit with missing `owned_changes`
- selected scope with implementation intent and explicit file paths/commands emits execution unit
- materializer calls readiness validator before returning ok
- materialization report includes all emitted packet refs

## A/B Expectations

Initial A/B scopes should become problem nodes and likely block before execution unit until implementation intent includes explicit owned changes and validation commands.

After `implementation-intent-candidate-contract-v1`, rerun A/B and expect:

- A has owned changes around evaluation contract/docs/tests
- B has owned changes around evidence-search contracts/docs/tests/runtime

## Source-Backed Claims

- SWE-bench requires task-like implementation targets and tests before code evaluation.
- AlphaEvolve-like execution can start only after a bounded evaluator exists.
- PROV-DM supports linking selected scope, problem node, selected option, and execution unit as derived entities.
