---
id: "20260316-board-action-api-contract-and-event-log-codex-01-execplan"
title: "Formalize a board-action API contract, capability-scoped mutations, and deterministic event log"
owner: "agent/codex-01"
created: "2026-03-16T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260316-board-action-api-contract-and-event-log-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/board-action-api.md
  - spec/board-action-api.yaml
  - spec/board-event-log.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260316-next-planning-codex-02"
draft_created: "2026-03-16T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260316-board-action-api-contract-and-event-log-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define authority-preserving board action API contract"
    priority: "P1"
  - title: "Define deterministic board event log and mutation audit surface"
    priority: "P1"
  - title: "Map canonical transitions to Git and GitHub evidence without promoting GitHub to authority"
    priority: "P1"
depends_on:
  - "20260313-game-hostile-review-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Turn board and game mutations into typed API actions so users and agents request legal state transitions through one contract instead of editing canonical artifacts ad hoc.

The local graph and other canonical local artifacts must remain authoritative. The API is a controlled mutation and projection surface, not a new authority source.

## Progress

- [ ] Draft the board-action API authority contract
- [ ] Define typed legal actions and mutation targets
- [ ] Define deterministic event-log and audit requirements
- [ ] Queue the implementation slice behind hostile-review completion

## Surprises & Discoveries

- The current system still lets governed agents mutate canonical files directly, which makes user and agent moves look similar even when they should be capability-distinct.
- A usable API contract must describe both write commands and read/projection semantics, otherwise consumers will accidentally treat projections as authority.

## Decision Log

- 2026-03-16 / agent-codex-01 / The API must not replace canonical local authority; it only mediates legal state transitions against it.
- 2026-03-16 / agent-codex-01 / “Users can update everything” is reframed as “users can submit any legal action through a typed, audited interface.”
- 2026-03-16 / agent-codex-01 / `git` and `gh` should act as the operator UI and evidence transport for the game, while local canonical artifacts remain the source of truth and local referees remain the primary judges.

## Outcomes & Retrospective

On completion, the repository should have:

- a canonical board-action API contract
- typed action families for graph, queue, review, and governance mutations
- a deterministic event-log schema for every applied action
- explicit rules for which surfaces are mutable through the API versus projection-only

## Context and Orientation

This slice is the foundation for the next governance phase. It should make board mutation explicit before we tighten anti-cheat enforcement or remove commit-order dependence from implementation branches.

The API contract needs to cover both machine and human callers without collapsing authority boundaries:

- canonical local artifacts remain the source of truth
- projection surfaces stay non-authoritative
- users and agents both act through typed actions
- validators/referees still decide whether a requested state transition is legal
- Git and GitHub may provide evidence for transitions, but neither may become the authority source for transition legality

## Plan of Work

1. Define the board-action API domain, storage authority model, and non-authoritative projections.
2. Define action families, required fields, deterministic outputs, rejection semantics, and idempotence rules.
3. Define the event-log schema for every accepted or rejected action.
4. Define how Git and GitHub events attach evidence to actions without becoming authority sources.
5. Bind the contract to existing canonical artifacts and queue/graph governance.

## Concrete Steps

1. Add `spec/board-action-api.yaml` for:
   - action envelopes
   - actor classes
   - governed object identifiers
   - source-state / target-state declarations
   - allowed mutation surfaces
   - authority/projection fields
   - deterministic success and rejection payloads
2. Add `spec/board-event-log.schema.yaml` for:
   - transition ids
   - requested / accepted / rejected action records
   - canonical artifact refs
   - git evidence refs
   - optional GitHub evidence refs
   - replay-safe timestamps and actor ids
3. Document the model in `docs/board-action-api.md`, including:
   - current canonical backend: local repo artifacts
   - future-compatible backend abstraction: external control-plane repo/service
   - non-goal: promoting GitHub Projects, PR state, or checks to authority
4. Define the minimum action families this slice must cover:
   - backlog graph actions
   - queue projection reconciliation
   - implementation branch publication
   - merge completion reconciliation
   - exception request / denial / approval records
5. Define the minimum Git/GitHub evidence mapping this slice must cover:
   - branch creation
   - commit / tree / merge-base evidence
   - PR open / review / merge evidence
   - check-run evidence as projection only
6. Reconcile the remaining-work graph and queue mirror so the API slice is queued canonically after hostile review.

## Validation and Acceptance

Acceptance criteria:

- the API contract makes canonical authority boundaries explicit
- typed actions are machine-readable and deterministic
- event-log records are structured enough for downstream referees to consume
- the contract distinguishes canonical authority, projection-only surfaces, and evidence-only surfaces
- each required transition type has a declared Git/GitHub evidence mapping
- the contract is strong enough that slice 2 can consume it without inventing new authority concepts
- the queue and graph reflect the slice without promoting it early

## Idempotence and Recovery

- identical action requests against unchanged state should produce deterministic results
- rejected actions should emit deterministic failure records rather than partial writes
- replay of event-log records should be sufficient to reconstruct mutation intent

## Artifacts and Notes

Expected artifacts:

- `docs/board-action-api.md`
- `spec/board-action-api.yaml`
- `spec/board-event-log.schema.yaml`

Non-goals for this slice:

- implementing the API runtime
- externalizing the canonical board to another repo or service
- redefining protected-surface policy
- replacing implementation-branch order rules

## Interfaces and Dependencies

Primary interfaces:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `docs/governance.md`
- `docs/games/README.md`
- `bin/remaining-work-graph-check`

Implementation expectations for the later implementation branch:

- add a local referee-facing contract validator for board actions
- add a deterministic event-log writer/validator
- expose transition types that later slices can enforce without schema churn

Planned implementation branch:

- `impl-execplan/20260316-board-action-api-contract-and-event-log-codex-01-execplan-codex-01-20260316`
