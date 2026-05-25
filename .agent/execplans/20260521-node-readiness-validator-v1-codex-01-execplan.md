---
id: "20260521-node-readiness-validator-v1-codex-01"
title: "Node Readiness Validator V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - src/platform_tools/validate_node_readiness.py
  - bin/validate-node-readiness
  - tests/test_validate_node_readiness.py
  - docs/node-based-project-plan-v1.md
  - spec/node-readiness-policy.yaml
  - .agent/execplans/20260521-node-readiness-validator-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/node-readiness-validator-v1"
initiative_node_id: "initiative-node-readiness-validator-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "readiness-validator-tests"
      command: "uv run pytest tests/test_validate_node_readiness.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define readiness policy"
    priority: "P0"
  - title: "Implement readiness validator"
    priority: "P0"
  - title: "Block generic selected scopes from implementation_ready"
    priority: "P0"
  - title: "Emit missing-field reports"
    priority: "P0"
  - title: "Add tests for readiness transitions"
    priority: "P0"

depends_on:
  - "20260521-problem-node-execution-unit-contract-v1-codex-01"
  - "20260521-implementation-intent-candidate-contract-v1-codex-01"
---

## Objective

Create the validator that tells us whether a node is research-ready, planning-ready, implementation-ready, or blocked.

## Scope

In scope:

- policy file defining required fields per readiness state
- CLI/runtime validator
- missing-field report
- blocking behavior for generic selected scopes and incomplete execution units

Out of scope:

- materializing execution units
- ranking nodes
- executing implementation attempts

## Acceptance

- Generic selected scopes are classified below `implementation_ready`.
- Problem nodes expose missing fields.
- Node options missing implementation intent fail `planning_ready`.
- Execution units missing owned changes, validation commands, or rollback plans fail `implementation_ready`.

## Readiness Policy Target

Create `spec/node-readiness-policy.yaml` with these state requirements.

`research_ready` requires:

- `goal`
- `problem_statement`
- `constraints`
- `evaluation_criteria`

`option_generation_ready` requires:

- all `research_ready` fields
- `evidence_refs` or `missing_fields` containing `evidence_refs`
- `option_generation_policy` or `missing_fields` containing `option_generation_policy`

`selection_ready` requires:

- `option_refs`
- `evaluation_criteria`
- `evidence_refs`

`planning_ready` requires:

- `selected_option_ref`
- selected option has `implementation_intent`
- selected option has `expected_changes`
- selected option has `non_goals`

`implementation_ready` requires:

- `execution_unit_id`
- `implementation_intent`
- `owned_changes`
- `validation_commands`
- `rollback_plan`
- `completion_evidence_requirements`

`evaluation_ready` requires:

- `solution_artifact_ref` or produced artifact refs
- validation output refs
- completion evidence refs

## CLI Contract

Command:

- `bin/validate-node-readiness`

Arguments:

- `--root`
- `--node-path`
- `--target-state`
- `--policy-path`

Output:

- public orchestration envelope
- `readiness_state`
- `target_state`
- `ready`
- `missing_fields`
- `blockers`

## Required Tests

- valid problem node passes `research_ready`
- problem node missing evaluation criteria fails `research_ready`
- node option missing implementation intent fails `planning_ready`
- selected-scope-shaped object fails `implementation_ready`
- execution unit missing validation commands fails `implementation_ready`
- valid execution unit passes `implementation_ready`

## A/B Expectations

Current A/B selected scopes should fail `implementation_ready`.

After implementation-intent propagation, they may pass `planning_ready`, but still must not pass `implementation_ready` until materialized into execution units.

## Source-Backed Claims

- W3C PROV-DM supports provenance-linked readiness evidence.
- SWE-bench supports requiring concrete task validation before implementation readiness.
- CRITIC supports tool-grounded readiness checks rather than self-declared readiness.
