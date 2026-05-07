---
id: "20260507-research-control-plane-codex-01-execplan"
title: "Formalize cross-repo research orchestration in the platform control plane"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - .agent/execplans/20260507-research-control-plane-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/system-architecture/README.md
  - docs/system-architecture/control-plane-principles.md
  - docs/system-architecture/cross-repo-boundaries.md
  - docs/system-architecture/orchestration-model.md
  - docs/system-architecture/research-capability-contract.md
  - docs/system-architecture/researcher-self-improvement-loop.md
  - docs/adr/ADR-0002-cross-repo-integration-is-contract-first.md
  - docs/adr/ADR-0003-researcher-capability-is-external-and-self-critical.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-057"
  queue_position: 57
  implementation_branch: "impl-execplan/20260507-research-control-plane-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-research-control-plane-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/README.md"
    - "docs/system-architecture/control-plane-principles.md"
    - "docs/system-architecture/cross-repo-boundaries.md"
    - "docs/system-architecture/orchestration-model.md"
    - "docs/system-architecture/research-capability-contract.md"
    - "docs/system-architecture/researcher-self-improvement-loop.md"
    - "docs/adr/ADR-0002-cross-repo-integration-is-contract-first.md"
    - "docs/adr/ADR-0003-researcher-capability-is-external-and-self-critical.md"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-research-control-plane-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-research-control-plane-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define control-plane principles for orchestrating external capabilities"
    priority: "P1"
  - title: "Define cross-repo boundary and output destination contracts"
    priority: "P1"
  - title: "Define researcher capability and self-improvement loop"
    priority: "P1"
depends_on: []
---

## Outcomes & Retrospective

The platform repo should become the constitutional layer for orchestrating external capabilities such as a researcher engine without absorbing their implementation.

## Context and Orientation

The current platform already governs plans, branches, runtime surfaces, and repo-local execution rules. The next step is to formalize how that control plane routes work to a separate researcher repo and how that researcher can critique the harness without self-authorizing architectural drift.

## Plan of Work

Add a concise architecture package that defines control-plane principles, cross-repo boundaries, orchestration flow, researcher capability contracts, and the self-improvement loop. Record the key boundary decisions as ADRs.

## Validation and Acceptance

This slice is accepted when the platform repo contains a coherent architecture package that explains how governance, orchestration, external researcher execution, and target-repo outputs relate to each other without requiring undocumented cross-repo coupling.

## Artifacts and Notes

This slice intentionally defines contracts and architecture only. It does not implement the separate researcher repo or plugin runtime yet.
