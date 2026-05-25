---
id: "20260520-era-research-runtime-repo-bootstrap"
title: "Bootstrap ERA Research Runtime Repo"
owner: "agent/codex"
created: "2026-05-20T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/era-governed-research-repo-plan.md
  - artifacts/planner/research/era-research-runtime-bootstrap-dag.json
  - .agent/execplans/20260520-era-research-runtime-repo-bootstrap.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/era-research-runtime-bootstrap"
initiative_node_id: "initiative-era-research-runtime-bootstrap"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "plan-review"
      command: "review architecture plan and DAG for repo boundary, handoff contracts, and dependency order"
      expected_exit: 0

tasks:
  - title: "Lock system boundaries between governance, ERA runtime, and planner"
    priority: "P0"
  - title: "Define Phase 1 repo bootstrap scope and contracts"
    priority: "P0"
  - title: "Sequence bootstrap work in a machine-readable DAG"
    priority: "P0"
  - title: "Choose the first pilot problem class"
    priority: "P1"

depends_on: []
---

## Outcomes & Retrospective

The immediate planning outcome is a clean repo boundary and a bounded bootstrap sequence. The runtime should not own governance or planning authority.

## Context and Orientation

This plan bootstraps a new repo named `era-research-runtime` and keeps the current repository as the governance and planning control plane. The first release should prove one empirical search loop with structured evidence and a governed handoff.

## Plan of Work

Phase 1 should create the new repo scaffold, schemas, CLI skeleton, examples, and documentation. Later phases should add empirical search, evaluation, ranking, governance integration, and planner handoff in that order.

## Validation and Acceptance

Acceptance means:

- the repo boundary is explicit
- the phase ordering is defensible
- the pilot scope is narrow enough to execute
- the DAG does not mix research, governance, and planning authority

## Artifacts and Notes

The machine-readable bootstrap DAG is stored in `artifacts/planner/research/era-research-runtime-bootstrap-dag.json`.
