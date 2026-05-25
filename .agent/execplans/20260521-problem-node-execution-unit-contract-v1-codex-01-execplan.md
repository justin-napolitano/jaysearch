---
id: "20260521-problem-node-execution-unit-contract-v1-codex-01"
title: "Problem Node And Execution Unit Contract V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - spec/contracts/problem-node.schema.yaml
  - spec/contracts/node-option.schema.yaml
  - spec/contracts/execution-unit.schema.yaml
  - spec/contracts/packet-schema-registry.yaml
  - docs/core-contract-spec-v1.md
  - docs/node-based-project-plan-v1.md
  - tests/test_problem_node_execution_unit_contracts.py
  - artifacts/planner/research/problem-node-execution-unit-contract-v1-dag.json
  - .agent/execplans/20260521-problem-node-execution-unit-contract-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/problem-node-execution-unit-contract-v1"
initiative_node_id: "initiative-problem-node-execution-unit-contract-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "contract-tests"
      command: "uv run pytest tests/test_problem_node_execution_unit_contracts.py"
      expected_exit: 0
    - name: "dag-json"
      command: "python3 -m json.tool artifacts/planner/research/problem-node-execution-unit-contract-v1-dag.json"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define problem_node schema"
    priority: "P0"
  - title: "Define node_option schema"
    priority: "P0"
  - title: "Define execution_unit schema"
    priority: "P0"
  - title: "Register contracts"
    priority: "P0"
  - title: "Add contract fixtures and tests"
    priority: "P0"

source_artifacts:
  - docs/single-workflow-node-era-prebuild-review-v1.md
  - artifacts/validation/single-workflow-node-era-prebuild-review-v1.json
---

## Objective

Create the canonical schemas and registry entries for `problem_node`, `node_option`, and `execution_unit`.

This is the foundation that prevents generic selected scopes from being treated as implementation-ready.

## Research Basis

Use the source-backed rationale in:

- `docs/single-workflow-node-era-prebuild-review-v1.md`
- `docs/current-research-bibliography.md`

Key sources:

- AlphaEvolve for generate/evaluate/select loops
- SWE-bench for task-grounded repository work
- CRITIC for tool-grounded critique
- Reflexion for feedback retention
- W3C PROV-DM for provenance links

## Scope

In scope:

- YAML schemas for the three packet types
- registry entries
- docs update
- tests that valid fixtures pass and incomplete fixtures fail

Out of scope:

- runtime materializer
- node ranking
- implementation attempt generation
- solution artifact contract

## Acceptance

- `problem_node` requires readiness state and missing fields.
- `node_option` requires implementation intent and expected changes.
- `execution_unit` requires owned changes, validation commands, rollback plan, and completion evidence requirements.
- Registry exposes all three contracts.
- Tests prove generic selected scopes are not execution units.

## Concrete Schema Targets

### `problem_node`

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `node_id`
- `node_version`
- `project_id`
- `title`
- `node_type`
- `goal`
- `problem_statement`
- `inputs`
- `expected_outputs`
- `constraints`
- `dependencies`
- `evidence_refs`
- `option_refs`
- `selected_option_ref`
- `readiness_state`
- `missing_fields`
- `evaluation_criteria`
- `feedback_refs`

Allowed `readiness_state` values:

- `draft`
- `research_ready`
- `option_generation_ready`
- `selection_ready`
- `planning_ready`
- `implementation_ready`
- `evaluation_ready`
- `complete`
- `blocked`

### `node_option`

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `option_id`
- `source_node_ref`
- `option_family`
- `approach_summary`
- `implementation_intent`
- `expected_changes`
- `non_goals`
- `assumptions`
- `risks`
- `evidence_refs`
- `evaluation_refs`

`implementation_intent` must be an object with:

- `summary`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `handoff_requirements`

### `execution_unit`

Required fields:

- `packet_type`
- `packet_version`
- `packet_id`
- `created_at`
- `producer`
- `execution_unit_id`
- `source_problem_node_ref`
- `selected_option_ref`
- `implementation_intent`
- `owned_changes`
- `required_inputs`
- `expected_outputs`
- `acceptance_checks`
- `validation_commands`
- `rollback_plan`
- `non_goals`
- `dependency_refs`
- `evidence_refs`
- `evaluation_method`
- `completion_evidence_requirements`

## Required Fixtures

Create fixtures inside the test file rather than permanent artifact files unless reuse becomes necessary:

- valid `problem_node`
- invalid `problem_node` missing `readiness_state`
- valid `node_option`
- invalid `node_option` missing `implementation_intent`
- valid `execution_unit`
- invalid `execution_unit` missing `validation_commands`
- invalid selected-scope-shaped object that must not validate as `execution_unit`

## Contract Compatibility

This slice is additive.

Do not remove existing contracts or fields.

Add new registry entries:

- `problem_node`
- `node_option`
- `execution_unit`

Do not make existing selected-scope validation depend on these contracts yet.

## Source-Backed Claims

- AlphaEvolve supports generate/evaluate/select loops over candidate code artifacts.
- SWE-bench supports task-grounded software evaluation over concrete repository tasks.
- W3C PROV-DM supports preserving derivation from selected scope to node, option, and execution unit.

If a claim extends beyond these sources, label it as a platform design inference in comments or docs.
