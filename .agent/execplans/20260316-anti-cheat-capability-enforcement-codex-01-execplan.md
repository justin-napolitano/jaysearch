---
id: "20260316-anti-cheat-capability-enforcement-codex-01-execplan"
title: "Enforce anti-cheat capability boundaries for governed agents, users, and referee surfaces"
owner: "agent/codex-01"
created: "2026-03-16T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260316-anti-cheat-capability-enforcement-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/agent-capability-boundaries.md
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
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
      command: "bin/execplan-validate .agent/execplans/20260316-anti-cheat-capability-enforcement-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy-compliance-check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260316-anti-cheat-capability-enforcement-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define protected rule and referee surfaces"
    priority: "P1"
  - title: "Define capability classes for users, agents, and branches"
    priority: "P1"
  - title: "Define enforcement boundaries so agents cannot self-authorize compliance"
    priority: "P1"
depends_on:
  - "20260313-game-hostile-review-runtime-codex-01-execplan"
  - "20260316-board-action-api-contract-and-event-log-codex-01-execplan"
---

# Purpose / Big Picture

Prevent Codex or any governed agent from “winning” by modifying the rules, validators, or protected code paths it is not supposed to control while still allowing humans to authorize exceptional governance moves explicitly.

## Progress

- [x] Cut and publish the canonical implementation branch
- [ ] Define protected surfaces and anti-cheat principles
- [ ] Define capability classes for users, agents, and branch types
- [ ] Define exception and escalation model
- [x] Queue the implementation slice behind the API contract

## Surprises & Discoveries

- The current governance model still permits fix-forward repair of the checkers that judge the active branch; that is auditable, but not yet a strong anti-cheat boundary.
- Anti-cheat enforcement has to distinguish legitimate governance work from implementation work or it will either overblock maintainers or underblock agents.
- Publishing the slice-2 implementation branch is not enough by itself; slice 1 completion and slice 2 promotion must be recorded as explicit graph actions before anti-cheat enforcement work can begin lawfully.

## Decision Log

- 2026-03-16 / agent-codex-01 / Anti-cheat work should treat rule surfaces, validator surfaces, and exception registries as separately governed capability domains.
- 2026-03-16 / agent-codex-01 / The system should allow explicit human-authorized exceptions without allowing agents to self-authorize them.
- 2026-03-16 / agent-codex-01 / Slice 2 must consume the transition/action model from slice 1 rather than inventing a second mutation model for protected surfaces.
- 2026-03-16 / agent-codex-01 / Slice 2 may only start after the merged slice-1 branch is canonically reconciled to `completed` and the published slice-2 branch is explicitly promoted to `ready`.

## Outcomes & Retrospective

On completion, the repository should have:

- a protected-surface registry
- a capability model by actor and branch/game type
- explicit rules for when an implementation branch may or may not change referee surfaces
- an exception/escalation model that keeps human authority explicit

## Context and Orientation

This slice depends on the board-action API contract. Without typed actions and scoped mutation surfaces, “anti-cheat” would degrade into ad hoc file deny-lists and subjective review.

The target model is:

- users may request legal actions
- agents may execute only within granted capabilities
- protected surfaces require stronger authority than normal implementation work
- exception records remain explicit, bounded, and human-authorized
- a branch that is seeking policy compliance may not redefine its own protected-surface allowances without stronger authority than that branch already has

## Plan of Work

1. Define capability classes and protected-surface categories.
2. Define which actor, branch, and game contexts may request which transition types from slice 1.
3. Define hard denials for self-authorization paths and policy-judge self-modification paths.
4. Define the exception path for protected-surface changes.
5. Queue the anti-cheat slice canonically after the API contract slice.

## Concrete Steps

1. Add `spec/agent-capability-policy.yaml` for:
   - actor classes
   - branch classes
   - game/slice classes
   - allowed transition families
   - forbidden transition families
   - escalation requirements
2. Add `spec/protected-surfaces.schema.yaml` for:
   - rules surfaces
   - referee surfaces
   - exception registries
   - canonical state surfaces
   - projection-only surfaces
3. Document capability boundaries in `docs/agent-capability-boundaries.md`, including:
   - what an implementation agent may change
   - what requires governance authority
   - what requires explicit human approval
   - how Git/GitHub evidence participates without granting new authority
4. Define the minimum denial cases this slice must settle:
   - agent changes rule surfaces on the branch it is trying to pass
   - agent changes referee logic that would legalize its own branch
   - agent writes exception records that authorize itself
   - agent treats GitHub state as authority rather than evidence
5. Define the minimum allowed exception cases this slice must preserve:
   - explicit human-authorized governance repair
   - separate governance branch changes
   - bounded exception records with expiry and evidence
6. Reconcile the remaining-work graph and queue mirror so the anti-cheat slice is canonically blocked behind the API contract and hostile review.

## Validation and Acceptance

Acceptance criteria:

- protected surfaces are machine-identifiable
- capability classes are explicit and actor-aware
- exception paths do not allow self-authorization by governed agents
- the plan identifies which current fix-forward repair patterns remain legal and which become illegal under stronger anti-cheat rules
- the slice is explicit about how local referees and Git/GitHub evidence interact
- the graph and queue reflect the dependency chain cleanly

## Idempotence and Recovery

- capability evaluation should be deterministic for the same branch/game/action tuple
- exception expiry should fail closed
- protected-surface violations should produce machine-readable denial evidence

## Artifacts and Notes

Expected artifacts:

- `docs/agent-capability-boundaries.md`
- `spec/agent-capability-policy.yaml`
- `spec/protected-surfaces.schema.yaml`

Non-goals for this slice:

- building the full API runtime
- externalizing board authority
- replacing branch-order legality
- preventing all governance changes everywhere; the goal is scoped capability control, not permanent freeze

## Interfaces and Dependencies

Primary interfaces:

- `docs/governance.md`
- `docs/agent-game-rules-v1.md`
- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`

Implementation expectations for the later implementation branch:

- capability evaluation must be machine-checkable from local repo state
- protected-surface denials must emit deterministic evidence
- exception handling must remain bounded, expiring, and human-authorized

Planned implementation branch:

- `impl-execplan/20260316-anti-cheat-capability-enforcement-codex-01-execplan-codex-01-20260316`
