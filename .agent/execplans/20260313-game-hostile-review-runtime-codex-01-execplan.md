---
id: "20260313-game-hostile-review-runtime-codex-01-execplan"
title: "Formalize hostile-review as a governed review-layer runtime with deterministic artifacts and branch-safe planning"
owner: "agent/codex-01"
created: "2026-03-13T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260313-game-hostile-review-runtime-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/games/hostile-review-game.md
  - spec/games/hostile-review-game.yaml
  - bin/hostile-review
  - bin/hostile-review-smoke-test
  - src/platform_tools/hostile_review.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/human_operations_runtime.py
  - src/platform_tools/integrations/provider_adapter.py
  - tests/test_hostile_review.py
  - tests/test_orchestrator_status.py
  - tests/test_human_operations_runtime.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313"
draft_created: "2026-03-13T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260313-game-hostile-review-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260313-game-hostile-review-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "hostile-review-smoke-test"
      command: "bin/hostile-review-smoke-test"
      expected_exit: 0
tasks:
  - title: "Define hostile-review game contract and inherited legality boundaries"
    priority: "P1"
  - title: "Implement deterministic hostile-review runtime and report artifacts"
    priority: "P1"
  - title: "Project hostile-review gating and findings into runtime status surfaces"
    priority: "P1"
  - title: "Preserve branch-safe planning and canonical graph projection rules"
    priority: "P1"
depends_on:
  - "20260312-game-policy-compliance-codex-01-execplan"
  - "20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan"
  - "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan"
---

# Purpose / Big Picture

Turn hostile review from a queued idea into a governed review-layer runtime that emits deterministic machine-readable findings before human approval gates.

This slice should not replace policy compliance. It should consume policy-compliance legality, game hierarchy, and canonical remaining-work state so hostile review becomes a stricter review-layer game on top of existing board law.

## Progress

- [x] Materialize the hostile-review ExecPlan on a dedicated draft branch
- [x] Reconcile the review-gated backlog node to a canonical ExecPlan id on a non-`main` planning branch
- [x] Cut and publish the canonical hostile-review implementation branch
- [ ] Define hostile-review game contract and artifacts
- [ ] Implement deterministic hostile-review runtime and smoke path
- [ ] Project hostile-review state into runtime status surfaces
- [ ] Validate the slice end to end

## Surprises & Discoveries

- `rwg-014` was review-gated after the remaining-work ordering slice merged, but it still pointed at the placeholder id `future:game-hostile-review` rather than a canonical ExecPlan id.
- The repository already has an older hostile-review sweep ExecPlan and a runbook, but not a governed review-layer runtime wired into the current game, graph, and branch-governance surfaces.
- Planning and graph reconciliation should now occur on dedicated planning or implementation branches, not by direct edits on `main`.
- Publishing the `impl-execplan/*` branch is not sufficient by itself; the active remaining-work node and queue mirror still need an explicit canonical graph action before policy compliance allows execution to proceed.

## Decision Log

- 2026-03-13 / agent-codex-01 / Hostile review remains a review-layer game that depends on policy-compliance and inherited global board law rather than replacing either one.
- 2026-03-13 / agent-codex-01 / Planning-state and remaining-work graph updates for this slice should be committed from dedicated branches and merged into `main`, not edited directly on `main`.
- 2026-03-13 / agent-codex-01 / The hostile-review slice should promote findings and gating state into machine-readable runtime surfaces without granting projection boards any authority.
- 2026-03-13 / agent-codex-01 / Once the canonical hostile-review implementation branch is published, the next lawful move is an explicit backlog graph action that promotes `rwg-014` from `review_gated` to `ready`; execution should not proceed on branch publication alone.

## Outcomes & Retrospective

On completion, the repository should have:

- a canonical hostile-review game contract and runtime
- deterministic hostile-review artifacts and a one-command smoke path
- runtime surfaces that expose hostile-review gating and findings
- branch-safe planning discipline encoded in the slice’s execution and reconciliation flow

## Context and Orientation

The canonical remaining-work graph now marks hostile review as the next review-gated slice after the ordering work merged on March 12, 2026. It is not yet executable because it lacks a canonical ExecPlan-backed implementation slice and published implementation branch.

The new hostile-review runtime should fit the existing layered model:

- global board law remains inherited
- policy compliance continues to prove branch legality
- hostile review adds stricter adversarial review findings before human approval gates
- queue and graph updates remain canonical local artifacts, projected outward only after validation

## Plan of Work

1. Replace the placeholder hostile-review backlog identity with a canonical ExecPlan id and draft branch metadata.
2. Define the hostile-review game contract, branch behavior, required artifacts, and referee surfaces.
3. Implement a deterministic runtime and smoke path that emits hostile-review findings and evidence artifacts.
4. Thread hostile-review status into the existing orchestration and human-operations surfaces.
5. Validate the runtime, then promote the slice to a published implementation branch for execution.

## Concrete Steps

1. Reconcile `rwg-014` and `docs/queued-execplans.md` to point at `20260313-game-hostile-review-runtime-codex-01-execplan`.
2. Add `docs/games/hostile-review-game.md` and `spec/games/hostile-review-game.yaml` with inherited-law, illegal-move, referee, and evidence contracts.
3. Implement `bin/hostile-review`, `src/platform_tools/hostile_review.py`, and `bin/hostile-review-smoke-test`.
4. Update runtime surfaces that need hostile-review awareness:
   - `src/platform_tools/orchestrator_status.py`
   - `src/platform_tools/human_operations_runtime.py`
   - provider projections only where needed for review-state display
5. Add focused tests and deterministic hostile-review artifacts under `artifacts/review/`.
6. Before implementation begins, cut and publish:
   - `impl-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313`
7. Reconcile `rwg-014` and the queue mirror on the implementation branch so policy compliance sees the published branch as a canonical ready-state transition rather than stale gated state.

## Validation and Acceptance

Acceptance criteria:

- hostile review is defined as a canonical game/runtime, not only a prompt or prose runbook
- findings are deterministic and machine-readable
- hostile-review status is visible in runtime surfaces without bypassing human review authority
- planning and remaining-work updates for this slice land from a dedicated branch, not direct `main` edits
- focused tests and a hostile-review smoke command pass

## Idempotence and Recovery

- rerunning hostile review on unchanged inputs should produce byte-equivalent machine-readable artifacts
- rerunning planning/graph reconciliation should be idempotent and not duplicate graph actions
- hostile-review findings should fail closed when evidence is missing or ambiguous rather than inventing advisory state

## Artifacts and Notes

Expected artifacts:

- `docs/games/hostile-review-game.md`
- `spec/games/hostile-review-game.yaml`
- `bin/hostile-review`
- `bin/hostile-review-smoke-test`
- `artifacts/review/hostile-review-report.json`
- `artifacts/review/hostile-review-summary.md`
- `artifacts/review/validation-evidence.json`

## Interfaces and Dependencies

Primary interfaces:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `docs/games/README.md`
- `docs/games/game-inheritance.md`
- `docs/agent-game-rules-v1.md`
- `docs/governance.md`
- `bin/policy-compliance-check`
- `bin/remaining-work-graph-check`

Branching interfaces:

- draft planning branch: `draft-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313`
- planned implementation branch: `impl-execplan/20260313-game-hostile-review-runtime-codex-01-execplan-codex-01-20260313`
