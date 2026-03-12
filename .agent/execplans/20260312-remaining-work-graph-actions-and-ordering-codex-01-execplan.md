---
id: "20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan"
title: "Canonicalize remaining-work graph actions, deterministic ordering, and governed reorder legality"
owner: "agent/codex-01"
created: "2026-03-12T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md
  - docs/queued-execplans.md
  - docs/remaining-work-graph.md
  - docs/governance.md
  - docs/agent-game-rules-v1.md
  - spec/remaining-work-graph.schema.yaml
  - spec/governance.yaml
  - spec/providers/github-projects.schema.yaml
  - artifacts/planner/research/remaining-work-graph.json
  - src/platform_tools/remaining_work_graph_check.py
  - src/platform_tools/policy_compliance_check.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/implementation_orchestrator.py
  - src/platform_tools/integrations/provider_adapter.py
  - src/platform_tools/integrations/github_projects_sync.py
  - bin/remaining-work-graph-check
  - bin/remaining-work-graph-ordering-smoke-test
  - tests/test_remaining_work_graph_check.py
  - tests/test_policy_compliance_check.py
  - tests/test_orchestrator_status.py
  - tests/test_implementation_orchestrator.py
  - tests/test_provider_adapter_contract.py
  - tests/test_github_projects_sync.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan-codex-01-20260312"
draft_created: "2026-03-12T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-ordering-smoke-test"
      command: "bin/remaining-work-graph-ordering-smoke-test"
      expected_exit: 0
tasks:
  - title: "Define canonical graph-action records and allowed transitions"
    priority: "P1"
  - title: "Define deterministic ready ordering and reorder constraints"
    priority: "P1"
  - title: "Encode stale-queue and action-required blockers in the graph validator"
    priority: "P1"
  - title: "Project graph-action status into runtime and provider surfaces without giving them authority"
    priority: "P1"
depends_on:
  - "20260311-runtime-constraint-canonicalization-codex-01-execplan"
  - "20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan"
  - "20260312-game-policy-compliance-codex-01-execplan"
---

# Purpose / Big Picture

Formalize the remaining-work graph as the canonical source for graph actions, legal reorder operations, and deterministic ready-slice ordering after policy compliance lands.

This slice is not a new domain game. It is a global board-law and runtime-governance follow-on that makes policy-compliant execution order machine-checkable so governed work cannot advance by agent assertion, stale queue prose, or board edits alone.

## Progress

- [x] Materialize the implementation ExecPlan on the canonical implementation branch
- [x] Define canonical graph-action records and allowed transitions
- [x] Define deterministic ready ordering and reorder constraints
- [x] Encode stale-queue and action-required blockers in the graph validator
- [x] Project graph-action status into runtime and provider surfaces without giving them authority
- [x] Validate the slice

## Surprises & Discoveries

- refreshed `main` already contains the merged policy-compliance runtime, but the remaining-work graph and queue mirror were not reconciled to that merged state
- the current graph distinguishes readiness and gating classes, but it does not yet expose canonical action records, deterministic order keys, or queue-projection freshness
- policy compliance can block stale graph and queue edits, but the canonical backlog still needs its own legality model for reorder moves and projection freshness
- GitHub Projects remains useful as a projection surface, but ordering and action-required state must still derive from the local graph rather than the board

## Decision Log

- 2026-03-12 / agent-codex-01 / Graph actions and ordering are global board-law/runtime concerns, not a new domain game.
- 2026-03-12 / agent-codex-01 / Policy compliance merged on `main` before this slice started, so backlog state must be canonically reconciled as part of this implementation branch.
- 2026-03-12 / agent-codex-01 / GitHub Projects may mirror graph order and action-required state, but it must not become the authority for either.
- 2026-03-12 / agent-codex-01 / Reorder operations should be explicit canonical moves with deterministic legality checks rather than silent file edits.
- 2026-03-12 / agent-codex-01 / Hostile review should now depend on the ordering slice so review-layer runtimes consume canonical graph-order evidence instead of reconstructing backlog order themselves.

## Outcomes & Retrospective

On completion, the repository should have:

- canonical graph-action records for promote, block, unblock, complete, and reorder-style moves
- deterministic ready-node ordering that can be reproduced from canonical artifact state
- explicit legality rules for when a reorder is allowed, forbidden, or requires a human decision
- validator output that reports stale queue state, missing graph actions, and illegal ordering mutations
- orchestrator and provider projections that consume graph-order state without becoming workflow authority

Expected implemented outcome:

- `bin/remaining-work-graph-check` emits deterministic action and ordering findings
- runtime surfaces consume canonical ready ordering instead of ad hoc list order or queue prose
- board projections can display ordering and action-required state while remaining non-authoritative
- downstream slices such as hostile review and branching can rely on canonical orderability semantics

## Context and Orientation

The current layered model already distinguishes:

- global board law
- domain games
- subgames
- decision-gated future games

What remains underspecified is how the canonical backlog itself changes shape once policy compliance has established that illegal moves cannot advance by narration alone. The graph needs a first-class concept of what action was taken, why the order changed, and whether that order change was legal.

This slice should preserve the existing authority boundaries:

- the local remaining-work graph remains canonical
- GitHub Projects is a projection surface
- policy-compliance results remain upstream legality evidence
- humans retain override authority where reorder decisions are explicitly decision-gated

## Plan of Work

1. Extend the remaining-work graph schema with canonical graph-action and ordering fields.
2. Define deterministic derivation rules for ready order, tie-breaks, and reorder legality.
3. Update the validator to reject stale queue state, missing action evidence, and illegal reorder mutations.
4. Thread validated ordering data into orchestrator and provider-sync projections without granting them authority.
5. Add focused tests and a one-command smoke path for ordering legality.

## Concrete Steps

1. Extend `spec/remaining-work-graph.schema.yaml` and `artifacts/planner/research/remaining-work-graph.json` with:
   - graph-action records
   - deterministic ordering keys
   - explicit reorder metadata
   - queue-projection freshness metadata
2. Update `docs/remaining-work-graph.md`, `docs/queued-execplans.md`, `docs/governance.md`, and `docs/agent-game-rules-v1.md` so ordering and action-required semantics are documented as projections of the canonical graph.
3. Extend `src/platform_tools/remaining_work_graph_check.py` and `bin/remaining-work-graph-check` to validate:
   - explicit action ownership
   - deterministic ready ordering
   - stale queue projection blockers
   - reorder legality and decision-gated cases
4. Update `src/platform_tools/policy_compliance_check.py`, `src/platform_tools/orchestrator_status.py`, `src/platform_tools/implementation_orchestrator.py`, `src/platform_tools/integrations/provider_adapter.py`, and `src/platform_tools/integrations/github_projects_sync.py` to consume validated ordering state.
5. Add focused tests and `bin/remaining-work-graph-ordering-smoke-test`.
6. Run:
   - `bin/execplan-validate .agent/execplans/20260312-remaining-work-graph-actions-and-ordering-codex-01-execplan.md`
   - `bin/remaining-work-graph-ordering-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- the remaining-work graph has explicit machine-readable action and ordering fields
- reorder operations are modeled as legal or illegal moves, not silent artifact edits
- stale queue or projection state blocks governed advancement deterministically
- orchestrator and provider surfaces consume validated ordering state without becoming authority sources
- downstream review layers can consume graph-order evidence rather than inventing it
- focused tests and smoke pass

## Idempotence and Recovery

- rerunning the validator on unchanged graph state should produce byte-equivalent results
- replaying the same legal graph action should be a no-op or explicit duplicate, never a silent mutation
- ambiguous reorder intent must fail with explicit blockers instead of inferred priority changes

## Artifacts and Notes

Expected artifacts:

- updated remaining-work graph schema and canonical graph artifact
- deterministic graph-action and ordering validator output
- smoke coverage for ready-order and reorder legality

Implemented evidence:

- `artifacts/planner/research/remaining-work-graph.json` now carries canonical `graph_actions`, `ordering_policy`, and `queue_projection` metadata
- `src/platform_tools/remaining_work_graph_check.py` validates queue freshness, ready-order determinism, and explicit promote/reorder legality
- provider and orchestrator surfaces now consume validated ordering metadata instead of inferring queue order from prose or board state
- focused pytest and `bin/remaining-work-graph-ordering-smoke-test` passed on the implementation branch

## Interfaces and Dependencies

Primary dependencies:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `docs/governance.md`
- `bin/remaining-work-graph-check`
- `bin/orchestrator-status`
- `bin/implementation-orchestrator`
