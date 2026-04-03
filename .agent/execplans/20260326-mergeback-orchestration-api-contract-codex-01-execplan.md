---
id: "20260326-mergeback-orchestration-api-contract-codex-01-execplan"
title: "Define a machine-readable API contract for implementation merge-back into initiative branches"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260326-mergeback-orchestration-api-contract-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/mergeback-orchestration-api.md
  - docs/queued-execplans.md
  - spec/mergeback-orchestration-api.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-044"
  queue_position: 44
  goal_area: "orchestrator-runtime"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260326-mergeback-orchestration-api-contract-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/mergeback-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "spec/mergeback-orchestration-api.schema.yaml"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-mergeback-orchestration-api-contract-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260326-mergeback-orchestration-api-contract-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260326-mergeback-orchestration-api-contract-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define a compact merge-back readiness command for implementation slices targeting initiative integration"
    priority: "P1"
  - title: "Define a deterministic PR integration contract command that resolves the lawful parent initiative target"
    priority: "P1"
  - title: "Keep PR merge-back orchestration subordinate to existing workflow, merge-readiness, and initiative authority surfaces"
    priority: "P1"
depends_on:
  - "20260326-worker-orchestration-api-codex-01-execplan"
  - "20260326-initiative-branch-plan-authority-correction-codex-01-execplan"
---

# Purpose / Big Picture

Define the machine-readable API surface that lets a thin orchestrator determine whether an `impl-execplan/*` branch may merge back into its parent `initiative/*` branch and what PR target or integration contract should be used. The goal is to make implementation merge-back as deterministic and toolable as worker execution and graph inspection, rather than leaving those decisions in prose or operator memory.

## Progress

- [ ] define a request/response schema for merge readiness of implementation-to-initiative PR merge-back
- [ ] define a request/response schema for PR integration contract resolution
- [ ] define bounded blocker, next-action, and problem vocabularies for merge-back orchestration
- [ ] keep the new surface explicitly subordinate to existing merge-readiness and workflow contracts

## Surprises & Discoveries

- the current public orchestration facade stops at worker execution and status; it does not yet expose the next governed step of PR merge-back into the initiative branch
- now that PR merge-back is the normal integration path, the absence of a machine-readable integration contract is a real orchestration gap rather than a documentation preference
- this surface should resolve and project existing authority; it should not create a second merge-readiness or branch-policy engine

## Decision Log

- phase 1 should define two commands only: `get-merge-readiness` and `get-pr-integration-contract`
- `get-merge-readiness` should project whether a source implementation branch is ready to merge into its lawful initiative target and what checks still block it
- `get-pr-integration-contract` should resolve the lawful target branch, integration mode, required validations, and required evidence for the PR
- governance-critical routing, branch mapping, and readiness blockers must be expressible through deterministic schema fields rather than prose interpretation

## Outcomes & Retrospective

- expected outcome: one contract package that makes PR merge-back into the initiative branch machine-resolvable for thin orchestrators

## Context and Orientation

- the worker orchestration facade already exposes graph state, worker resolution, worker execution, and worker status
- the governance correction now makes PR merge-back into the initiative branch the normal integration path for implementation slices
- the next missing orchestration surface is the one that tells the orchestrator whether the slice is merge-ready and where it should open the PR

## Plan of Work

1. define the merge-back API command set and versioned schema
2. define bounded blocker, next-action, and problem vocabularies
3. define source-branch, target-branch, and initiative resolution semantics
4. define the relationship to existing workflow and merge-readiness contracts
5. register the slice in graph and queue state

## Concrete Steps

1. add `spec/mergeback-orchestration-api.schema.yaml`
2. add `docs/mergeback-orchestration-api.md`
3. register the ExecPlan in the remaining-work graph and queued ExecPlans mirror
4. keep later implementation out of scope for this planning slice

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260326-mergeback-orchestration-api-contract-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the contract must make it possible to determine the lawful initiative PR target and merge-back readiness without requiring prose interpretation
- the contract must remain subordinate to existing workflow and merge-readiness authority surfaces instead of duplicating them

## Idempotence and Recovery

- rerunning this planning slice is safe as long as the command set remains narrow and does not claim live runtime behavior before implementation exists
- if later implementation reveals missing fields, the contract should be widened in a follow-on slice rather than relying on undocumented output drift

## Artifacts and Notes

- this slice defines the contract for future merge-back orchestration commands; it does not implement them
- the new schema should use bounded vocabularies and fail-closed problem semantics consistent with the repo's recent orchestration contracts

## Interfaces and Dependencies

- depends on workflow branch-role and initiative-authority rules for lawful target resolution
- depends on merge-readiness checks for readiness evidence
- should align with the public orchestration facade style without pretending the commands are already live
