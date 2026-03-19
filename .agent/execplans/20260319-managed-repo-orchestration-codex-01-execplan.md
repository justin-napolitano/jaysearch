---
id: "20260319-managed-repo-orchestration-codex-01-execplan"
title: "Allow platform runtime commands to orchestrate external canonical repos by explicit root targeting"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - spec/workflow.yaml
  - docs/codex-orchestrator-contract.md
  - src/platform_tools/execplan_discovery.py
  - src/platform_tools/orchestrate_governed_slice.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-managed-repo-orchestration-codex-01-20260319"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define the managed-repo contract so canonical state stays in the target repo while runtime authority stays in platform-template-bootstrap"
    priority: "P1"
  - title: "Teach orchestrator commands to target an external repo root deterministically"
    priority: "P1"
  - title: "Document operator flow for using platform runtime against jayrun as the first managed repo"
    priority: "P1"
depends_on:
  - "20260318-graph-transition-automation-and-merge-gating-codex-01-execplan"
---

# Purpose / Big Picture

Make the platform act as a reusable governance and orchestration engine for external repos without taking ownership of those repos' canonical project state.

## Progress

- [ ] define the machine-readable managed-repo boundary
- [ ] add explicit root-targeting support where orchestration assumes the current repo is canonical
- [ ] document jayrun as the first managed external repo

## Surprises & Discoveries

- the current platform runtime already has most of the deterministic control-loop pieces needed for multi-repo use
- the missing work is mainly around explicit root targeting, artifact discovery, and fail-closed validation when a target repo is incomplete

## Decision Log

- choose external canonical ownership rather than copying the full runtime into `jayrun`
- keep `jayrun` authoritative for its own graph, ExecPlans, docs, and initiative state
- keep `platform-template-bootstrap` authoritative for orchestration runtime and scheduling behavior

## Outcomes & Retrospective

- expected outcome: the platform can orchestrate `jayrun` without absorbing `jayrun` into platform state
- expected retrospective question: whether the managed-repo contract is generic enough for multiple future repos, not only `jayrun`

## Context and Orientation

- target repos such as `jayrun` should own their own graph, ExecPlans, docs, and initiative state
- platform-template-bootstrap should own deterministic reconciliation, control-loop execution, and scheduling/runtime logic
- the design must fail closed when the target repo lacks required canonical artifacts

## Plan of Work

1. define the managed-repo runtime boundary and required canonical artifact contract
2. identify the current platform commands that assume local-repo ownership and add explicit repo-root targeting
3. document the operator flow for using platform-template-bootstrap against `jayrun`

## Concrete Steps

1. add a managed-repo contract artifact or equivalent machine-readable workflow extension
2. update runtime discovery and orchestrator commands to accept explicit external repo roots
3. add fail-closed checks for missing graph, missing ExecPlans, and missing workflow artifacts in managed repos
4. document the first supported workflow using `jayrun`

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- the resulting implementation slice should be able to target an external repo root deterministically and fail closed when canonical artifacts are missing

## Idempotence and Recovery

- discovery against an external repo root should be read-only unless an explicit orchestration command writes canonical state into that target repo
- if managed-repo targeting is ambiguous, the runtime should stop without mutating either repo

## Artifacts and Notes

- first managed repo target: `/mnt/c/Users/jna31a/repos/jayrun`
- expected canonical state remains inside the target repo, not in platform-template-bootstrap

## Interfaces and Dependencies

- depends on `rwg-027` because it extends the newly unified local orchestration path
- likely touches `execplan_discovery`, orchestrator status surfaces, and root-aware runtime command entrypoints
