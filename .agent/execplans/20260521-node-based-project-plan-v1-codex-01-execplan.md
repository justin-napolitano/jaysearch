---
id: "20260521-node-based-project-plan-v1-codex-01"
title: "Node-Based Project Plan V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/node-based-project-plan-v1.md
  - artifacts/planner/research/node-based-project-plan-v1-dag.json
  - docs/plan-model-v1.md
  - docs/planner-tool-v1.md
  - docs/incremental-toolchain-build-plan.md
  - .agent/execplans/20260521-node-based-project-plan-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/node-based-project-plan-v1"
initiative_node_id: "initiative-node-based-project-plan-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "dag-json"
      command: "python3 -m json.tool artifacts/planner/research/node-based-project-plan-v1-dag.json"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Formalize problem node and execution unit project model"
    priority: "P0"
  - title: "Define anti-drift rules"
    priority: "P0"
  - title: "Create project strategy DAG"
    priority: "P0"
  - title: "Update planner docs to route through nodes"
    priority: "P1"

depends_on:
  - "20260521-research-to-selection-validation-v1-codex-01"
---

## Outcomes & Retrospective

This slice makes the node-based project model the canonical project plan before planner and implementation work.

## Research Basis

The model is backed by tree-search/evolutionary coding ideas, SWE-bench task-grounding, CRITIC tool-grounded critique, Reflexion feedback retention, and W3C PROV provenance.

## Plan of Work

Phase 1 documents the model. Phase 2 adds the strategy DAG. Phase 3 updates planner-facing docs so future work routes through problem nodes and execution units.

## Validation and Acceptance

Acceptance means future planner/code scopes can be challenged if they try to execute generic selected scopes without problem nodes, selected options, implementation intent, and execution units.
