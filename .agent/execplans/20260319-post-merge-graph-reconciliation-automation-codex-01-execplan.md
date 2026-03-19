---
id: "20260319-post-merge-graph-reconciliation-automation-codex-01-execplan"
title: "Automatically reconcile merged implementation evidence into canonical graph completion state"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260319-post-merge-graph-reconciliation-automation-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - artifacts/governance/board-action-events.jsonl
  - docs/queued-execplans.md
  - docs/codex-orchestrator-contract.md
  - spec/workflow.yaml
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
  - bin/post-merge-graph-reconciliation-smoke-test
  - bin/reconcile-pending-merge-completions
  - src/platform_tools/orchestrate_governed_slice.py
  - src/platform_tools/reconcile_governed_graph_events.py
  - src/platform_tools/reconcile_pending_merge_completions.py
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/human_operations_runtime.py
  - src/platform_tools/merge_readiness.py
  - src/platform_tools/policy_compliance_check.py
  - tests/test_orchestrate_governed_slice.py
  - tests/test_reconcile_governed_graph_events.py
  - tests/test_reconcile_pending_merge_completions.py
  - tests/test_merge_readiness.py
  - tests/test_policy_compliance_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/graph-transition-automation"
initiative_node_id: "initiative-graph-transition-automation"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-post-merge-graph-reconciliation-automation-codex-01-20260319"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260319-post-merge-graph-reconciliation-automation-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260319-post-merge-graph-reconciliation-automation-codex-01-execplan.md"
      expected_exit: 0
    - name: "post-merge-graph-reconciliation-smoke-test"
      command: "bin/post-merge-graph-reconciliation-smoke-test"
      expected_exit: 0
tasks:
  - title: "Make the local orchestrator detect merged implementation evidence and reconcile graph completion automatically"
    priority: "P1"
  - title: "Fail closed when merged evidence exists but the graph remains stale"
    priority: "P1"
  - title: "Eliminate the normal need for a manual post-merge cleanup branch"
    priority: "P1"
depends_on:
  - "20260318-graph-transition-automation-and-merge-gating-codex-01-execplan"
---

# Purpose / Big Picture

Close the gap between deterministic merge reconciliation logic and actual automatic runtime behavior so a merged implementation PR produces canonical completion state without manual cleanup work.

## Progress

- [ ] define the post-merge automation contract
- [ ] teach the local runtime to consume merged implementation evidence automatically
- [ ] block governed progress when merge evidence exists but graph completion is stale

## Surprises & Discoveries

- the current system already knows how to reconcile completion, but nobody guarantees that reconciliation runs after a merge
- this leaves the repo in an avoidable stale state until a human or agent notices and performs cleanup

## Decision Log

- treat post-merge reconciliation automation as a distinct runtime slice, not as incidental cleanup inside unrelated feature work
- prefer local orchestrator invocation over GitHub workflow automation because the hosting environment cannot rely on GitHub Actions

## Outcomes & Retrospective

- expected outcome: merged implementation evidence becomes canonical graph completion with no routine follow-up branch
- expected retrospective question: whether the same runtime should also reconcile draft-plan finalization automatically

## Context and Orientation

- canonical graph state still lives in-repo
- GitHub merge history remains evidence, not authority
- the orchestrator should consume that evidence deterministically and update canonical state locally

## Plan of Work

1. define the exact post-merge evidence contract and stale-state blocker
2. wire the local orchestrator to run completion reconciliation automatically
3. surface unreconciled merged evidence as an explicit runtime blocker
4. add a dedicated post-merge reconciliation command so the automation path stays auditable and reusable

## Concrete Steps

1. update the orchestrator/runtime path that currently stops short of post-merge completion updates
2. teach status commands to detect merged-but-unreconciled slices
3. ensure graph and queue projection reconcile together when completion evidence is consumed
4. document the new automatic behavior in the orchestrator contract

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-post-merge-graph-reconciliation-automation-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- merged implementation evidence should produce deterministic local completion reconciliation without a manual cleanup branch

## Idempotence and Recovery

- repeated reconciliation runs should be no-ops once graph completion is already canonical
- if merge evidence is ambiguous, the runtime must fail closed without mutating graph state

## Artifacts and Notes

- motivating failure case: `rwg-027` merged in PR 91 but initially remained `ready` in the canonical graph until manual reconciliation

## Interfaces and Dependencies

- depends on `rwg-027` because it extends the merge reconciliation runtime
- likely touches orchestrator status, human operations status, and merge reconciliation entrypoints
