---
id: "20260319-local-git-hook-mainline-followup-codex-01-execplan"
title: "Fix local git-hook automation mainline activation and completion semantics"
owner: "agent/codex-01"
created: "2026-03-19T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260319-local-git-hook-mainline-followup-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - spec/workflow.yaml
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/orchestrate_governed_slice.py
  - src/platform_tools/reconcile_pending_merge_completions.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_orchestrate_governed_slice.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-git-hook-automation"
initiative_node_id: "initiative-local-git-hook-automation"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260319-local-git-hook-mainline-followup-codex-01-20260319"
draft_created: "2026-03-19T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260319-local-git-hook-mainline-followup-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Pin down why via-initiative completion can mark a slice complete while the expected runtime artifacts are absent from main"
    priority: "P1"
  - title: "Make completion evidence selection prefer the correct merge topology and avoid misleading draft-merge or pre-main evidence"
    priority: "P1"
  - title: "Define whether mainline availability needs its own machine-readable state separate from child-slice completion"
    priority: "P1"
  - title: "Ensure the local hook automation path activates deterministically on the default branch after the intended integration path completes"
    priority: "P1"
depends_on:
  - "20260319-local-git-hook-automation-codex-01-execplan"
---

# Purpose / Big Picture

Repair the gap between graph completion semantics and actual runtime availability for local git-hook automation.

## Progress

- [ ] reproduce the current mismatch between `rwg-031` completion and default-branch hook availability
- [ ] decide whether completion semantics, mainline availability semantics, or both are wrong
- [ ] patch merge reconciliation and orchestration logic to reflect the intended topology
- [ ] add coverage for initiative-to-main follow-through

## Surprises & Discoveries

- `rwg-031` can be reconciled to `completed` from initiative-side evidence even while `.githooks/` and repo-owned auto-reconcile commands are absent from `main`
- that makes the graph technically consistent with current child-node completion rules, but misleading for operators expecting working hook/runtime behavior on the default branch

## Decision Log

- treat this as a focused follow-up to `rwg-031`, not as a scheduler or managed-repo feature
- keep the work under the existing `initiative/local-git-hook-automation` parent

## Outcomes & Retrospective

- expected outcome: completion evidence, mainline availability, and hook activation semantics line up
- expected retrospective question: whether child-node completion and mainline integration need separate graph-visible states

## Context and Orientation

- the current policy says normal work completes into an initiative branch before the initiative merges to `main`
- local hook automation is uniquely sensitive because developers expect the default branch to become operational once the feature family is actually integrated
- the current state suggests the graph and runtime are not yet expressing that distinction cleanly

## Plan of Work

1. reproduce the current `rwg-031` mismatch from canonical branch and merge evidence
2. audit completion evidence selection for `via_initiative` slices and initiative-to-main transitions
3. decide whether completion should stay child-scoped with an added mainline-availability signal, or whether child completion itself needs tighter conditions
4. implement the smallest fail-closed fix that makes operator-facing runtime behavior trustworthy
5. add regression tests for the exact topology that failed here

## Concrete Steps

1. identify why `reconcile-pending-merge-completions` selected `merged:pr-98` and whether that is legal under the intended topology
2. inspect how initiative merges to `main` should influence child node and initiative node state
3. patch merge reconciliation and orchestration status so the default branch does not claim working hook automation until the relevant runtime artifacts are actually available there
4. validate the corrected behavior with focused tests and graph checks

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260319-local-git-hook-mainline-followup-codex-01-execplan.md` passes
- `bin/remaining-work-graph-check` passes
- targeted reconciliation/orchestrator tests pass
- the resulting system no longer leaves operators believing hook automation is active on `main` when the required artifacts are not present there

## Idempotence and Recovery

- investigation and tests should be safe to rerun against current graph state
- if the intended semantics are still ambiguous, the runtime should fail closed rather than silently claiming completion

## Artifacts and Notes

- current observed mismatch: `rwg-031` reconciles to `completed`, but `.githooks/` and `bin/auto-reconcile-main` are absent from `main`
- the fix should preserve deterministic evidence handling and avoid returning to manual cleanup branches for routine merges

## Interfaces and Dependencies

- depends on the existing post-merge reconciliation path from `rwg-030`
- touches local orchestration, merge evidence selection, and workflow semantics around `via_initiative` integration
