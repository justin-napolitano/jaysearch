---
id: "20260521-execution-era-loop-v1-codex-01"
title: "Execution ERA Loop V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/execution-era-loop-v1.md
  - artifacts/planner/research/execution-era-loop-v1-dag.json
  - docs/node-based-project-plan-v1.md
  - docs/implementation-game-model.md
  - .agent/execplans/20260521-execution-era-loop-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/execution-era-loop-v1"
initiative_node_id: "initiative-execution-era-loop-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "dag-json"
      command: "python3 -m json.tool artifacts/planner/research/execution-era-loop-v1-dag.json"
      expected_exit: 0
    - name: "design-review"
      command: "bin/design-iteration --root ."
      expected_exit: 0

tasks:
  - title: "Formalize execution-level generate/evaluate/select loop"
    priority: "P0"
  - title: "Define implementation attempt, attempt evaluation, and solution artifact"
    priority: "P0"
  - title: "Create execution ERA DAG"
    priority: "P0"
  - title: "Link execution loop into node-based project model"
    priority: "P1"

depends_on:
  - "20260521-node-based-project-plan-v1-codex-01"
---

## Outcomes & Retrospective

This slice formalizes how an executor explores multiple implementations within an execution unit boundary and attaches the selected result back to the graph.

## Research Basis

The model is backed by tree-search/evolutionary coding ideas, SWE-bench task-grounded evaluation, CRITIC tool-grounded critique, Reflexion feedback retention, and W3C PROV provenance.

## Plan of Work

Phase 1 documents the execution-level objects. Phase 2 defines the generate/evaluate/select DAG. Phase 3 links the model into the existing implementation game.

## Validation and Acceptance

Acceptance means the system distinguishes execution units from implementation attempts and solution artifacts, preventing selected results from overwriting the work contract.
