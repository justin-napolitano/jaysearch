---
id: "20260316-subgame-branch-state-transition-governance-codex-01-execplan"
title: "Replace implementation-branch commit-order legality with subgame branch and state-transition governance"
owner: "agent/codex-01"
created: "2026-03-16T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260316-subgame-branch-state-transition-governance-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/subgame-branch-governance.md
  - spec/subgame-branch-contract.yaml
  - spec/state-transition-legality.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260316-next-planning-codex-01"
draft_created: "2026-03-16T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260316-subgame-branch-state-transition-governance-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define subgame branch contracts and merge-back requirements"
    priority: "P1"
  - title: "Replace commit-order legality with state-transition legality"
    priority: "P1"
depends_on:
  - "20260313-game-hostile-review-runtime-codex-01-execplan"
  - "20260316-board-action-api-contract-and-event-log-codex-01-execplan"
  - "20260316-anti-cheat-capability-enforcement-codex-01-execplan"
---

# Purpose / Big Picture

Remove the assumption that an implementation branch must tell one linear procedural story in commit order. Replace that assumption with explicit legality for independently playable subgame branches and deterministic merge-back state transitions.

## Progress

- [ ] Define subgame branch model and merge contracts
- [ ] Define state-transition legality rules that replace commit-order dependence
- [ ] Define conflict and handoff semantics for independently played subgames
- [ ] Queue the implementation slice behind the API and anti-cheat slices

## Surprises & Discoveries

- Commit order worked as a review aid, but it is structurally hostile to independent subgame execution and branch fan-out.
- If branch-order rules are removed without a replacement legality model, the system will lose deterministic referee pressure rather than gaining flexibility.

## Decision Log

- 2026-03-16 / agent-codex-01 / The replacement for branch-order legality must be explicit state-transition legality, not “anything goes as long as the end state looks okay.”
- 2026-03-16 / agent-codex-01 / Independently played subgames need branch contracts, merge-back contracts, and conflict semantics before multiple agents can play them safely.

## Outcomes & Retrospective

On completion, the repository should have:

- a canonical contract for subgame branches
- deterministic state-transition legality rules
- merge-back and conflict semantics for independently played subgames
- a clear path to retire commit-order rules from implementation branches

## Context and Orientation

This slice intentionally comes last. The API contract defines how mutations are requested, and the anti-cheat slice defines who may perform them. Only then can implementation-branch order be removed safely.

The end state should support:

- subgame-specific branches
- independent agent or user execution inside those subgames
- deterministic merge-back validation
- legality based on scoped state transitions and dependencies, not commit chronology

## Plan of Work

1. Define subgame branch identities, scopes, and merge-back contracts.
2. Define state-transition legality rules and evidence requirements.
3. Define conflict and handoff semantics between subgames.
4. Queue the slice canonically behind the API and anti-cheat slices.

## Concrete Steps

1. Add `spec/subgame-branch-contract.yaml`.
2. Add `spec/state-transition-legality.schema.yaml`.
3. Document the model in `docs/subgame-branch-governance.md`.
4. Reconcile the remaining-work graph and queue mirror so the slice is canonically blocked behind the first two governance slices and hostile review.

## Validation and Acceptance

Acceptance criteria:

- state-transition legality is explicit enough to replace commit-order legality on implementation branches
- subgame branch scopes and merge-back semantics are machine-readable
- conflicts between independently played subgames are modeled explicitly
- the graph and queue preserve the dependency order without promoting the slice early

## Idempotence and Recovery

- repeated merge-back validation on unchanged state should be deterministic
- invalid subgame merges should fail closed with machine-readable blockers
- handoff artifacts should be sufficient for takeover by another agent or user

## Artifacts and Notes

Expected artifacts:

- `docs/subgame-branch-governance.md`
- `spec/subgame-branch-contract.yaml`
- `spec/state-transition-legality.schema.yaml`

## Interfaces and Dependencies

Primary interfaces:

- `docs/governance.md`
- `docs/agent-game-rules-v1.md`
- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`

Planned implementation branch:

- `impl-execplan/20260316-subgame-branch-state-transition-governance-codex-01-execplan-codex-01-20260316`
