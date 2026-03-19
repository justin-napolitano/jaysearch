---
id: "20260318-graph-transition-automation-and-merge-gating-codex-01-execplan"
title: "Deterministically derive routine graph transitions from branch, PR, merge, and check evidence"
owner: "agent/codex-01"
created: "2026-03-18T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260318-graph-transition-automation-and-merge-gating-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - bin/register-remaining-work-node
  - bin/reconcile-governed-graph-events
  - bin/reconcile-remaining-work-transition
  - docs/queued-execplans.md
  - spec/agent-capability-policy.yaml
  - spec/board-action-api.yaml
  - spec/governance.yaml
  - spec/protected-surfaces.schema.yaml
  - spec/remaining-work-graph.schema.yaml
  - spec/ruleset.yaml
  - spec/workflow.yaml
  - src/platform_tools/branch_policy.py
  - src/platform_tools/board_action_api.py
  - src/platform_tools/execplan_lint.py
  - src/platform_tools/integrations/github_projects_sync.py
  - src/platform_tools/integrations/provider_adapter.py
  - src/platform_tools/human_operations_runtime.py
  - src/platform_tools/human_operations_status.py
  - src/platform_tools/merge_readiness.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/register_remaining_work_node.py
  - src/platform_tools/reconcile_governed_graph_events.py
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/reconcile_remaining_work_transition.py
  - src/platform_tools/remaining_work_graph_check.py
  - tests/test_branch_policy.py
  - tests/test_board_action_api.py
  - tests/test_human_operations_status.py
  - tests/test_merge_readiness.py
  - tests/test_register_remaining_work_node.py
  - tests/test_policy_compliance_check.py
  - tests/test_reconcile_governed_graph_events.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_reconcile_remaining_work_transition.py
  - tests/test_remaining_work_graph_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260318-graph-transition-automation-and-merge-gating-codex-01-20260318"
draft_created: "2026-03-18T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260318-graph-transition-automation-and-merge-gating-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260318-graph-transition-automation-and-merge-gating-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define machine-readable graph transition rules for routine lifecycle events"
    priority: "P1"
  - title: "Implement deterministic reconciliation from branch, PR, merge, and check evidence"
    priority: "P1"
  - title: "Fail closed when merges would leave graph reconciliation missing or illegal"
    priority: "P1"
depends_on:
  - "20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan"
---

# Purpose / Big Picture

Move routine graph state out of manual bookkeeping and into deterministic reconciliation from branch, PR, merge, and check evidence, while keeping graph topology and prioritization as governed human decisions.

## Progress

- [ ] Define the machine-readable transition contract for routine graph state changes
- [ ] Implement deterministic reconciliation from GitHub and branch evidence
- [ ] Add fail-closed merge gating for unreconciled or illegal graph transitions

## Surprises & Discoveries

- The graph is now canonical enough that manual status maintenance is the main remaining ergonomics gap.
- Provider sync is downstream of reconciliation, so this slice should make board updates follow canonical graph state rather than compensate for missing graph state.

## Decision Log

- 2026-03-18 / agent-codex-01 / Keep this slice focused on routine operational state transitions. Node creation, dependency changes, and reprioritization remain explicit governed actions.

## Outcomes & Retrospective

On completion, developers should be able to follow branch and PR rules without manually editing routine graph lifecycle state, because the platform will derive those transitions deterministically and block merges when reconciliation is missing or invalid.

## Context and Orientation

The current platform has a strong canonical graph, but a weak operational-state loop:

- branch and PR events happen in GitHub
- graph state is still often updated manually afterward
- provider sync then mirrors whatever graph state exists

That is backwards for routine lifecycle changes. The desired split is:

- graph topology and planning decisions are governed and explicit
- routine lifecycle state is machine-derived from evidence

## Plan of Work

1. Define machine-readable event-to-transition rules for draft PR open/merge, implementation PR open/merge, and required-check completion.
2. Extend reconciliation runtime so branch, PR, merge, and check evidence map deterministically to exactly one graph node or fail closed.
3. Add merge/readiness enforcement so unreconciled required transitions block rather than silently deferring to manual follow-up.

## Concrete Steps

1. Add or refine spec surfaces that define legal routine transition sources and required evidence.
2. Implement reconciliation logic that can derive canonical lifecycle transitions from GitHub and local branch evidence.
3. Update merge/readiness/provider-sync behavior so graph reconciliation is a prerequisite rather than an optional cleanup step.

## Validation and Acceptance

Acceptance criteria:

- routine lifecycle transitions are machine-readable and deterministic
- ambiguous node mapping or unreconciled required transitions fail closed
- provider-sync and merge-readiness consume reconciled graph state rather than requiring manual graph edits for normal workflow

## Idempotence and Recovery

- repeated reconciliation with unchanged evidence should be idempotent
- if GitHub evidence is incomplete or ambiguous, the system should block with explicit reasons rather than guessing

## Artifacts and Notes

Expected artifacts:

- `spec/governance.yaml`
- `spec/workflow.yaml`
- `src/platform_tools/reconcile_remaining_work_merge.py`
- `src/platform_tools/integrations/github_projects_sync.py`

## Interfaces and Dependencies

Primary interfaces:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `spec/governance.yaml`
- `spec/workflow.yaml`
- `src/platform_tools/reconcile_remaining_work_merge.py`
- `src/platform_tools/integrations/github_projects_sync.py`
