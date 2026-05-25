---
id: "20260521-research-candidate-tree-search-v1-codex-01"
title: "Research Candidate Tree Search V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/research-candidate-tree-search-v1.md
  - docs/research-tool-v1.md
  - docs/research-tool-v1-ranking-and-search.md
  - docs/core-contract-spec-v1.md
  - spec/contracts/packet-schema-registry.yaml
  - artifacts/planner/research/research-candidate-tree-search-v1-dag.json
  - .agent/execplans/20260521-research-candidate-tree-search-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/research-candidate-tree-search-v1"
initiative_node_id: "initiative-research-candidate-tree-search-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "design-review"
      command: "run design-iteration after adding candidate tree-search contracts and DAG"
      expected_exit: 0

tasks:
  - title: "Define candidate tree-search contract"
    priority: "P0"
  - title: "Define expansion decision packet"
    priority: "P0"
  - title: "Define bounded tree-search DAG"
    priority: "P0"
  - title: "Prepare implementation slice for candidate generation"
    priority: "P1"

depends_on:
  - "20260521-research-hypothesis-branching-v1-codex-01"
---

## Outcomes & Retrospective

This slice defines bounded candidate tree search as the next research-system improvement after hypothesis branching.

## Plan of Work

Phase 1 defines the tree and expansion-decision contracts. Phase 2 updates the research tool docs so candidate generation consumes hypotheses and emits a search tree. Phase 3 creates the implementation DAG for a later runtime build.

## Validation and Acceptance

Acceptance means:

- the candidate tree-search shape is explicit
- candidate expansion decisions are machine-readable
- the design is bounded enough to implement without becoming full research evaluation
