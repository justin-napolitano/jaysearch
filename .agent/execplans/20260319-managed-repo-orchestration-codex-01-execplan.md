---
id: "20260319-managed-repo-orchestration-codex-01-execplan"
title: "Allow platform runtime commands to orchestrate external canonical repos by explicit root targeting and scripted bootstrap"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/codex-orchestrator-contract.md
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
  - spec/workflow.yaml
  - bin/bootstrap-managed-repo
  - bin/github-projects-bootstrap
  - bin/managed-repo-status
  - src/platform_tools/bootstrap_managed_repo.py
  - src/platform_tools/branch_policy.py
  - src/platform_tools/execplan_discovery.py
  - src/platform_tools/game_status.py
  - src/platform_tools/governance_loader.py
  - src/platform_tools/integrations/github_projects_bootstrap.py
  - src/platform_tools/managed_repo_status.py
  - src/platform_tools/orchestrate_governed_slice.py
  - artifacts/provider-sync/
  - tests/test_bootstrap_managed_repo.py
  - tests/test_branch_policy.py
  - tests/test_managed_repo_status.py
  - tests/test_orchestrate_governed_slice.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/managed-repo-orchestration"
initiative_node_id: "initiative-managed-repo-orchestration"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-managed-repo-orchestration-bootstrap-codex-01-20260319"
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
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define the managed-repo bootstrap contract so canonical state stays in the target repo while runtime authority stays in platform-template-bootstrap"
    priority: "P1"
  - title: "Create a repo-owned bootstrap command that scaffolds required canonical artifacts in the target repo deterministically"
    priority: "P1"
  - title: "Create or reuse a per-repo GitHub Project through platform-owned runtime code and emit provider-sync artifacts"
    priority: "P1"
  - title: "Project canonical completion PR evidence into the managed-repo board so node completion is visible without reading raw graph files"
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
- [ ] define the machine-readable managed-repo bootstrap contract
- [ ] add a script-driven bootstrap path for canonical repo artifacts
- [ ] add script-driven GitHub Project bootstrap or reuse for managed repos
- [ ] expose completion PR evidence on the managed-repo board as a projection of canonical graph state
- [ ] add explicit root-targeting support where orchestration assumes the current repo is canonical
- [ ] document jayrun as the first managed external repo

## Surprises & Discoveries

- the current platform runtime already has most of the deterministic control-loop pieces needed for multi-repo use
- the missing work is mainly around explicit root targeting, artifact discovery, and fail-closed validation when a target repo is incomplete
- bootstrap needs to be platform-owned code, not hidden Codex behavior or ad hoc shell usage, or managed repos will invent inconsistent local procedures

## Decision Log

- choose external canonical ownership rather than copying the full runtime into `jayrun`
- keep `jayrun` authoritative for its own graph, ExecPlans, docs, and initiative state
- keep `platform-template-bootstrap` authoritative for orchestration runtime and scheduling behavior
- require managed-repo bootstrap to create or deterministically reuse a GitHub Project through versioned platform commands, not manual `gh` steps
- require managed-repo board projection to show canonical completion PR evidence for each completed node

## Outcomes & Retrospective

- expected outcome: the platform can orchestrate `jayrun` without absorbing `jayrun` into platform state
- expected retrospective question: whether the managed-repo contract is generic enough for multiple future repos, not only `jayrun`

## Context and Orientation

- target repos such as `jayrun` should own their own graph, ExecPlans, docs, and initiative state
- platform-template-bootstrap should own deterministic reconciliation, control-loop execution, and scheduling/runtime logic
- the design must fail closed when the target repo lacks required canonical artifacts
- bootstrap must be executable by a human developer without Codex; Codex should only call the same platform commands

## Plan of Work

1. define the managed-repo runtime boundary and required bootstrap artifact contract
2. add a platform-owned bootstrap command that can scaffold required canonical repo artifacts deterministically
3. integrate scripted GitHub Project creation or reuse into managed-repo bootstrap and emit provider-sync artifacts
4. extend provider projection so completion PR evidence is visible on the managed-repo board
5. identify the current platform commands that assume local-repo ownership and add explicit repo-root targeting
6. document the operator flow for using platform-template-bootstrap against `jayrun`

## Concrete Steps

1. extend the managed-repo contract with explicit bootstrap requirements for graph, queue, workflow, ExecPlans, and provider-sync artifacts
2. add `bin/bootstrap-managed-repo` so a developer can initialize a target repo without Codex-specific behavior
3. make bootstrap call platform-owned GitHub Project runtime code to create or reuse one board per managed repo and write local provider-sync artifacts
4. extend provider-sync mappings so the board exposes canonical completion PR evidence for completed nodes
5. update runtime discovery and orchestrator commands to accept explicit external repo roots
6. add fail-closed checks for missing graph, missing ExecPlans, missing workflow artifacts, and missing required board bootstrap state in managed repos
7. document the first supported workflow using `jayrun`

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-managed-repo-orchestration-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- the resulting implementation slice should be able to bootstrap a target repo deterministically from versioned platform commands and fail closed when required canonical or provider artifacts are missing
- GitHub Project creation or reuse for managed repos should run through versioned runtime code, not ad hoc shell commands
- the managed-repo board should show completion PR evidence derived from canonical graph completion refs

## Idempotence and Recovery

- discovery against an external repo root should be read-only unless an explicit orchestration command writes canonical state into that target repo
- if managed-repo targeting is ambiguous, the runtime should stop without mutating either repo
- bootstrap should be safe to rerun and should reuse existing project metadata when canonical local artifacts already point to a managed-repo board

## Artifacts and Notes

- first managed repo target: `/mnt/c/Users/jna31a/repos/jayrun`
- expected canonical state remains inside the target repo, not in platform-template-bootstrap
- expected bootstrap outputs include repo-local canonical artifacts plus repo-local provider-sync metadata for the managed board
- expected provider projection should include a visible completion-PR field or equivalent rendered evidence for completed nodes

## Interfaces and Dependencies

- depends on `rwg-027` because it extends the newly unified local orchestration path
- likely touches `execplan_discovery`, orchestrator status surfaces, root-aware runtime command entrypoints, and GitHub Project bootstrap runtime reuse
