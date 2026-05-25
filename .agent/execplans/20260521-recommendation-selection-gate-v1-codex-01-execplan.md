---
id: "20260521-recommendation-selection-gate-v1-codex-01"
title: "Recommendation Selection Gate V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/recommendation-selection-gate-v1.md
  - artifacts/planner/research/recommendation-selection-gate-v1-dag.json
  - src/platform_tools/materialize_selected_solution_scope.py
  - tests/test_materialize_selected_solution_scope.py
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - .agent/execplans/20260521-recommendation-selection-gate-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/recommendation-selection-gate-v1"
initiative_node_id: "initiative-recommendation-selection-gate-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "selected-solution-scope-runtime"
      command: "uv run pytest tests/test_materialize_selected_solution_scope.py tests/test_materialize_research_recommendation.py"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Define recommendation-to-selection gate"
    priority: "P0"
  - title: "Create selection gate DAG"
    priority: "P0"
  - title: "Harden selected scope materializer"
    priority: "P0"
  - title: "Add blocking tests for weak recommendations"
    priority: "P0"
  - title: "Run against real recommendation packet"
    priority: "P1"

depends_on:
  - "20260521-research-recommendation-v1-codex-01"
---

## Outcomes & Retrospective

This slice turns `selected_solution_scope` into an evaluation-backed gate rather than a loose projection from a recommendation packet.

## Research Basis

The plan uses `CRITIC`, `SWE-bench`, W3C PROV, and mechanism-design sources as summarized in `docs/current-research-bibliography.md`.

## Plan of Work

Phase 1 defines the gate policy and DAG. Phase 2 hardens the materializer. Phase 3 validates blocked cases and runs the gate against a real recommendation packet.

## Validation and Acceptance

Acceptance means:

- planner cannot receive scope from unevaluated recommendation
- selected candidate must be ranked, promoted, and evaluation-backed
- emitted selected scope records the gate policy
- real recommendation packet emits a selected scope
