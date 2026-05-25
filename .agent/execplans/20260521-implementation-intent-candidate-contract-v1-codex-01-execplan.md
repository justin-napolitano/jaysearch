---
id: "20260521-implementation-intent-candidate-contract-v1-codex-01"
title: "Implementation Intent Candidate Contract V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/research-candidate-tree-search-v1.md
  - docs/research-recommendation-v1.md
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - src/platform_tools/materialize_research_candidate_tree.py
  - src/platform_tools/materialize_research_recommendation.py
  - src/platform_tools/materialize_selected_solution_scope.py
  - tests/test_materialize_research_candidate_tree.py
  - tests/test_materialize_research_recommendation.py
  - tests/test_materialize_selected_solution_scope.py
  - .agent/execplans/20260521-implementation-intent-candidate-contract-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/implementation-intent-candidate-contract-v1"
initiative_node_id: "initiative-implementation-intent-candidate-contract-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "candidate-intent-tests"
      command: "uv run pytest tests/test_materialize_research_candidate_tree.py tests/test_materialize_research_recommendation.py tests/test_materialize_selected_solution_scope.py"
      expected_exit: 0
    - name: "flow-validation"
      command: "bin/validate-research-to-selection-flow --root . --research-question-path artifacts/planner/examples/evaluation-strength-and-evidence-search/evaluation-strength-question.packet.json --evidence-packet-path artifacts/planner/examples/evaluation-strength-and-evidence-search/evaluation-strength-evidence.packet.json"
      expected_exit: 0

tasks:
  - title: "Extend research_candidate_packet with implementation_intent"
    priority: "P0"
  - title: "Generate problem-specific expected changes"
    priority: "P0"
  - title: "Carry implementation intent into ranked candidates"
    priority: "P0"
  - title: "Carry selected candidate intent into selected scope"
    priority: "P0"
  - title: "Update tests and A/B flow fixtures"
    priority: "P0"

depends_on:
  - "20260521-problem-node-execution-unit-contract-v1-codex-01"
---

## Objective

Make research candidates planner-usable by adding implementation-specific intent.

This fixes the current generic selected-scope issue.

## Scope

In scope:

- `research_candidate_packet` emits `implementation_intent`.
- Candidate packets include `contract_changes`, `runtime_changes`, `validation_changes`, `docs_changes`, `non_goals`, and `handoff_requirements`.
- Recommendation preserves those fields in ranked candidates.
- Selected solution scope can carry selected candidate intent forward.

Out of scope:

- execution unit materialization
- planner DAG generation
- implementation attempt generation

## Acceptance

- A/B candidates no longer say only "baseline/reuse/novel".
- Evaluation-strength candidate includes concrete expected changes for evaluation strength fields and gate propagation.
- Evidence-search candidate includes concrete expected changes for source records, ranking, rejected sources, and evidence packet emission.
- Selected scope exposes enough intent to create a problem node.

## Required Candidate Fields

Extend `research_candidate_packet` with:

- `implementation_intent`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `non_goals`
- `handoff_requirements`
- `planner_entry_notes`

`implementation_intent` should be an object:

- `summary`
- `contract_changes`
- `runtime_changes`
- `validation_changes`
- `docs_changes`
- `handoff_requirements`

The duplicated top-level lists are acceptable in V1 for easier downstream packet access.

## Problem-Specific Intent Rules

For `evaluation-strength-contract-001`, generated candidates must include expected changes equivalent to:

- add `evaluation_strength` to `research_evaluation_packet`
- add `evaluation_basis` or equivalent basis details
- distinguish `static_contract`, `artifact_backed`, and `execution_backed`
- propagate evaluation strength into recommendation ranking
- propagate evaluation strength into selection policy
- add tests that static-only evidence cannot be represented as execution-backed

For `evidence-search-runtime-001`, generated candidates must include expected changes equivalent to:

- add source search request/response packet shape
- add `source_record`
- add source ranking output with accepted and rejected sources
- add rejection reason codes
- emit `evidence_packet` from ranked source records
- preserve source provenance and rejected-source traceability

## Mapping Rules

`materialize_research_candidate_tree`:

- derive intent from `research_problem_packet.problem_statement`
- use `artifact_targets` to infer contract/runtime/docs targets
- use `evaluation_criteria` to infer validation changes
- use `constraints` as assumptions and non-goal boundaries

`materialize_research_recommendation`:

- copy selected candidate intent fields into each ranked candidate
- preserve intent for blocked candidates as well

`materialize_selected_solution_scope`:

- if selected ranked candidate has implementation intent, include it in selected scope
- default `in_scope` from intent expected changes if caller does not provide scope
- default `acceptance_checks` from intent validation changes if caller does not provide checks

## Required Tests

- candidate tree emits implementation intent for evaluation-strength question
- candidate tree emits implementation intent for evidence-search question
- recommendation preserves intent fields in ranked candidates
- selected solution scope includes selected candidate intent
- selected solution scope no longer falls back to only recommendation reason when intent exists

## Blocker Cases

- candidate missing implementation intent should receive evaluation warning
- selected scope should remain below implementation-ready if intent is absent

## Source-Backed Claims

- SWE-bench motivates concrete repository task and validation detail.
- AlphaEvolve motivates candidate option generation and selection.
- CRITIC motivates tool-grounded validation and explicit critique outputs.
