---
id: "20260507-researcher-repo-architecture-codex-01-execplan"
title: "Define the standalone researcher repo and platform integration surface"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - .agent/execplans/20260507-researcher-repo-architecture-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/system-architecture/README.md
  - docs/system-architecture/researcher-repo-architecture.md
  - docs/system-architecture/researcher-plugin-model.md
  - docs/system-architecture/platform-researcher-interface.md
  - docs/system-architecture/researcher-mvp-backlog.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-058"
  queue_position: 58
  implementation_branch: "impl-execplan/20260507-researcher-repo-architecture-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-researcher-repo-architecture-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/README.md"
    - "docs/system-architecture/researcher-repo-architecture.md"
    - "docs/system-architecture/researcher-plugin-model.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "docs/system-architecture/researcher-mvp-backlog.md"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-researcher-repo-architecture-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-researcher-repo-architecture-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define the standalone researcher repo architecture and ownership boundaries"
    priority: "P1"
  - title: "Define the study-design and domain plugin model"
    priority: "P1"
  - title: "Define the platform-to-researcher invocation contract and artifact flow"
    priority: "P1"
  - title: "Define an MVP build backlog for the external researcher engine"
    priority: "P1"
depends_on:
  - "20260507-research-control-plane-codex-01-execplan"
---

## Outcomes & Retrospective

The platform repo should specify what the separate researcher repo is, what it owns, how it exposes plugins, how the platform invokes it, and how to build the first useful MVP without collapsing the boundary between governance and execution.

## Context and Orientation

The previous slice defined the control plane, repo boundaries, and the first research capability contract. The next step is to define the actual external subsystem the platform will orchestrate. That subsystem should be reusable, self-contained, and contract-bound rather than implemented inside the platform repo.

## Plan of Work

Add a focused architecture package that specifies the standalone researcher repo, its plugin model, the platform integration surface, and the first implementation backlog needed to make it real.

## Validation and Acceptance

This slice is accepted when the platform repo contains a coherent, platform-facing definition of the external researcher repo and the first implementation path is explicit enough to start building the separate codebase against stable contracts.

## Artifacts and Notes

This slice intentionally stops at architecture and backlog definition. It does not yet create the separate researcher repo or the platform plugin runtime.
