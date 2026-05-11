---
id: "20260511-candidate-selection-contract-codex-01-execplan"
title: "Formalize candidate selection and conflict resolution rules"
owner: "agent/codex-01"
created: "2026-05-11T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260511-candidate-selection-contract-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/README.md"
  - "docs/system-architecture/candidate-selection-and-conflict-resolution.md"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-067"
  queue_position: 67
  implementation_branch: "impl-execplan/20260511-candidate-selection-contract-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "research-runtime"
    - "capability-contracts"
  expected_artifacts:
    - ".agent/execplans/20260511-candidate-selection-contract-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/README.md"
    - "docs/system-architecture/candidate-selection-and-conflict-resolution.md"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260511-candidate-selection-contract-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260511-candidate-selection-contract-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Add a formal control-plane contract for evaluating candidate worth and resolving conflicting actions"
    priority: "P1"
  - title: "Define default ranking weights, promotion gates, and candidate dispositions"
    priority: "P1"
  - title: "Link the new contract into the system architecture package"
    priority: "P1"
depends_on:
  - "20260507-research-control-plane-codex-01-execplan"
---

## Outcomes & Retrospective

The platform needs a formal rule for deciding when research outputs are worth acting on and how to choose among conflicting candidate actions.

## Context and Orientation

The researcher and platform can already emit, rank, and project candidate actions. This slice establishes the constitutional decision contract that governs eligibility, ranking, conflict classification, and disposition before draft ExecPlan promotion.

## Plan of Work

Add a system-architecture contract that defines candidate worth, ranking dimensions, promotion thresholds, conflict types, and conflict-resolution ordering.

## Validation and Acceptance

This slice is accepted when the contract is documented under the system-architecture package, linked from the package index, and registered as a governed slice in the remaining-work graph.

## Artifacts and Notes

This slice is documentation-governance only. It does not change runtime code paths.
