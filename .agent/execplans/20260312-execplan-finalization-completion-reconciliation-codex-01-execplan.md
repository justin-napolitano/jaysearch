---
id: "20260312-execplan-finalization-completion-reconciliation-codex-01-execplan"
title: "Reconcile ExecPlan finalization and completion from signed merge history"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-execplan-finalization-completion-reconciliation-codex-01-execplan.md
  - .agent/AGENTS.md
  - .agent/PLANS.md
  - docs/governance.md
  - docs/agent-game-rules-v1.md
  - spec/governance.yaml
  - bin/finalize-execplan
  - bin/finalize-execplan-smoke-test
  - src/platform_tools/finalize_execplan.py
  - tests/test_finalize_execplan.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-execplan-finalization-completion-reconciliation-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-execplan-finalization-completion-reconciliation-codex-01-execplan.md"
      expected_exit: 0
    - name: "finalize-execplan-smoke-test"
      command: "bin/finalize-execplan-smoke-test"
      expected_exit: 0
tasks:
  - title: "Define canonical completion transition after signed merge on main"
    priority: "P1"
  - title: "Teach finalize-execplan to derive merge-backed finalization metadata deterministically"
    priority: "P1"
  - title: "Add focused tests for merged, unmerged, and ambiguous-history paths"
    priority: "P1"
  - title: "Add smoke coverage for one-command human finalization preparation"
    priority: "P1"
depends_on:
  - "20260311-implementation-branch-split-governance-codex-01-execplan"
---

# Purpose / Big Picture

Close the governance gap between merge-backed human finalization and canonical ExecPlan lifecycle state. Today the repository says the signed merge commit on `main` is the authority event for finalization, but it does not yet provide a deterministic governed path for reconciling `finalized_by`, `finalized_at`, `finalized_in_pr`, and `status: completed` from that merge history.

This slice should make merged ExecPlans machine-reconcilable without weakening the human signing boundary.

## Progress

- [ ] Define canonical completion-on-merge policy
- [ ] Implement deterministic finalization reconciliation runtime
- [ ] Add focused tests for pass and fail paths
- [ ] Add smoke coverage
- [ ] Validate the slice

## Surprises & Discoveries

- several merged ExecPlans appear to have landed on `main` without corresponding completion metadata, which proves the lifecycle rule is underspecified operationally
- the repository already has a `src/platform_tools/finalize_execplan.py` helper, but it currently stops at `proposed` and `approved` rather than handling merge-backed completion reconciliation
- a safe solution needs to distinguish preparation of finalization metadata from the human-signed merge authority event itself

## Decision Log

- 2026-03-12 / agent-codex-01 / The signed merge commit on `main` should remain the canonical authority event for governed ExecPlan completion.
- 2026-03-12 / agent-codex-01 / The repository needs one deterministic command path that derives merge-backed finalization metadata instead of relying on manual markdown edits after merge.
- 2026-03-12 / agent-codex-01 / Ambiguous or missing merge history should produce explicit machine-readable blockers rather than inferred completion claims.

## Outcomes & Retrospective

On completion, the repository should have one governed way to reconcile merged ExecPlans into a completed canonical state with machine-checkable evidence derived from signed merge history.

Expected outcome:

- merged ExecPlans can be updated to `status: completed` through a deterministic governed flow
- finalization metadata is derived from merge history where feasible
- ambiguous history produces explicit blockers
- a smoke path proves the one-command reconciliation workflow

## Context and Orientation

The current governance docs consistently describe the signed merge commit on `main` as the authority event for finalization metadata, but the operational lifecycle remains incomplete. In practice, merged implementation slices can validate and land while their ExecPlan frontmatter still looks like an unfinished draft artifact.

That mismatch weakens machine-readable board state, makes backlog inspection less trustworthy, and forces humans to infer whether a slice is truly complete.

## Plan of Work

1. Clarify the completion-on-merge lifecycle in the canonical governance docs and spec.
2. Extend the finalization runtime so it can reconcile merge-backed completion metadata deterministically.
3. Add focused tests for clean merge, missing merge, and ambiguous merge cases.
4. Add one smoke script that proves the intended human-facing reconciliation flow.
5. Validate the slice with deterministic outputs.

## Concrete Steps

1. Update `.agent/AGENTS.md`, `.agent/PLANS.md`, `docs/governance.md`, `docs/agent-game-rules-v1.md`, and `spec/governance.yaml` to define:
   - when `status: completed` is legal
   - how `finalized_by`, `finalized_at`, and `finalized_in_pr` are derived
   - what happens when merge evidence is missing or ambiguous
2. Extend `src/platform_tools/finalize_execplan.py` and add `bin/finalize-execplan`.
3. Add `tests/test_finalize_execplan.py`.
4. Add `bin/finalize-execplan-smoke-test`.
5. Run:
   - `bin/execplan-validate .agent/execplans/20260312-execplan-finalization-completion-reconciliation-codex-01-execplan.md`
   - `bin/finalize-execplan-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- governance docs and spec agree on completion-on-merge behavior
- the finalization command emits deterministic machine-readable output
- merged ExecPlans can be reconciled to `status: completed`
- unmerged or ambiguous plans are blocked with explicit machine-readable reasons
- focused tests pass
- the smoke script passes

## Idempotence and Recovery

- rerunning reconciliation against an already completed ExecPlan should be a no-op or produce an explicit already-finalized result
- the reconciliation path must not invent merge metadata when signed merge evidence is absent
- smoke fixtures must clean up any temporary repositories or artifacts they create

## Artifacts and Notes

Expected artifacts:

- updated governance language for completion-on-merge
- deterministic finalization reconciliation runtime
- focused tests
- `bin/finalize-execplan-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `.agent/AGENTS.md`
- `.agent/PLANS.md`
- `docs/governance.md`
- `docs/agent-game-rules-v1.md`
- `spec/governance.yaml`
- `src/platform_tools/finalize_execplan.py`
