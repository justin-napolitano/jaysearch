---
id: "20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan"
title: "Remove remaining downstream assumptions about the legacy verbose ExecPlan shape"
owner: "agent/codex-01"
created: "2026-04-14T00:00:00Z"
status: draft
base_branch: "initiative/contract-first-planning"
changes:
  - .agent/execplans/20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/governance.md
  - docs/agent-game-rules-v1.md
  - docs/planner-execplan-projection.md
  - src/platform_tools/finalize_execplan.py
  - src/platform_tools/game_status.py
  - src/platform_tools/implementation_orchestrator.py
  - src/platform_tools/merge_readiness.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/reconcile_pending_merge_completions.py
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/reconcile_governed_graph_events.py
  - tests/test_finalize_execplan.py
  - tests/test_game_status.py
  - tests/test_implementation_orchestrator.py
  - tests/test_merge_readiness.py
  - tests/test_orchestrator_status.py
  - tests/test_reconcile_pending_merge_completions.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_reconcile_governed_graph_events.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/contract-first-planning"
initiative_node_id: "initiative-contract-first-planning"
graph_registration:
  node_id: "rwg-055"
  queue_position: 55
  goal_area: "governance"
  implementation_branch: "impl-execplan/contract-first-execplan-consumer-cleanup"
  integration_mode: "via_initiative"
  conflict_domains:
    - governance
    - workflow
    - planner-runtime
    - orchestration
  expected_artifacts:
    - .agent/execplans/20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan.md
    - artifacts/planner/research/remaining-work-graph.json
    - docs/queued-execplans.md
    - src/platform_tools/finalize_execplan.py
    - src/platform_tools/merge_readiness.py
    - src/platform_tools/reconcile_remaining_work_merge.py
    - tests/test_finalize_execplan.py
    - tests/test_merge_readiness.py
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260414-contract-first-execplan-consumer-cleanup-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Update downstream consumers that still assume legacy headings or draft-first merge semantics"
    priority: "P1"
  - title: "Replace stale language in runtime and reviewer surfaces that still treat verbose sections as canonical"
    priority: "P1"
  - title: "Keep old-shape support only through the explicit port-execplan migration path rather than scattered fixture logic"
    priority: "P1"
depends_on:
  - "20260413-contract-first-execplan-runtime-codex-01-execplan"
---

## Outcomes & Retrospective

This slice removes the next wave of drift after the runtime hard-cut: downstream consumers, reconciliation paths, and reviewer surfaces should stop assuming the old verbose ExecPlan shape and instead rely on the thinner contract-first model plus the explicit migration command.

## Context and Orientation

The previous slice fixed the primary generators and bootstrap surfaces, but several downstream readers still hard-code old headings, draft-merge wording, or draft-branch-first assumptions. Those consumers now need to either read the contract-first shape directly or rely on `bin/port-execplan` when old plans are encountered.

## Plan of Work

1. Update downstream runtime consumers and review/referee paths that still expect legacy headings or draft-first merge semantics.
2. Align active docs and reviewer-facing language with the contract-first model.
3. Keep the migration strategy explicit: old prose-heavy plans are ported through the repo-owned command instead of being silently treated as the canonical shape forever.

## Validation and Acceptance

- The touched downstream consumers must work with the five-section contract-first plan shape.
- Stale draft-first wording in active runtime and reviewer paths should be removed where this slice touches behavior.
- Focused tests for finalize/merge-readiness/orchestrator/reconciliation consumers must pass.

## Artifacts and Notes

- This slice is consumer cleanup, not a historical migration of every archived example in the repo.
- Historical queue lines may still contain old wording until a later projection-wide cleanup slice rewrites them deterministically.
