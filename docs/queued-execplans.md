# Queued ExecPlans

## Objective

This document turns the remaining-work graph into an explicit near-term queue of planned slices.

## Initial Queue

1. `20260311-machine-readable-output-hardening-codex-01-execplan`
   - status: `completed`
   - goal: add stable JSON contracts across key orchestrator-facing commands

2. `20260311-composite-orchestrator-status-codex-01-execplan`
   - status: `completed`
   - goal: expose ready work, blockers, rule constraints, and required validations in one command
   - implementation branch: `impl-execplan/20260311-composite-orchestrator-status-codex-01-execplan-codex-01-20260311`

3. `20260311-game-graph-validator-and-status-codex-01-execplan`
   - status: `completed`
   - goal: validate the nested game graph and expose active game/subgame status for orchestration

4. `20260311-implementation-orchestrator-runtime-codex-01-execplan`
   - status: `completed`
   - goal: execute implementation-phase moves against the shared board and evidence model

5. `20260311-runtime-constraint-canonicalization-codex-01-execplan`
   - status: `completed`
   - goal: move remaining runtime-critical queue and readiness rules into validated canonical artifacts
   - implementation branch: `impl-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311`

6. `20260311-provider-sync-scaffold-codex-01-execplan`
   - status: `completed`
   - goal: scaffold provider adapters without granting external authority

7. `20260311-github-projects-bootstrap-runtime-codex-01-execplan`
   - status: `completed`
   - goal: bootstrap one governed GitHub Projects board from canonical provider schema

8. `20260311-github-projects-provider-sync-runtime-codex-01-execplan`
   - status: `completed`
   - goal: project canonical slice state into the governed GitHub Projects review board

9. `20260312-execplan-finalization-completion-reconciliation-codex-01-execplan`
   - status: `completed`
   - goal: reconcile merged ExecPlans to `status: completed` from signed merge history

10. `20260312-human-operations-review-runtime-codex-01-execplan`
   - status: `completed`
   - goal: formalize board review, takeover, and merge reconciliation as machine-readable runtime state
   - implementation branch: `impl-execplan/20260312-human-operations-review-runtime-codex-01-execplan-codex-01-20260312`

11. `20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan`
   - status: `completed`
   - goal: formalize global board law, game layers, and extension readiness for future subgames
   - implementation branch: `impl-execplan/20260312-game-rules-engine-audit-and-extensibility-codex-01-execplan-codex-01-20260312`

12. `20260312-game-policy-compliance-codex-01-execplan`
   - status: `ready`
   - goal: create `game-policy-compliance` and its `game-commit-structure` subgame so governed slices cannot advance by assertion alone
   - must also formalize graph-action-required and stale-queue blocking so merge/readiness cannot advance on stale backlog state
   - draft branch: `draft-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312`
   - implementation branch: `impl-execplan/20260312-game-policy-compliance-codex-01-execplan-codex-01-20260312`

13. `future:game-hostile-review`
   - status: `blocked`
   - goal: add machine hostile review before human approval gates
   - blocker: `20260312-game-policy-compliance-codex-01-execplan` must land first

14. `future:game-branching`
   - status: `decision_gated`
   - goal: formalize branch-cut legality and branch-choice policy as its own game

15. `future:game-citation`
   - status: `decision_gated`
   - goal: formalize citation-backed claim verification and anti-hallucination evidence rules

16. `future:game-documentation`
   - status: `decision_gated`
   - goal: formalize documentation completeness for code, games, and relationships

17. `future:game-board-integrity`
   - status: `decision_gated`
   - goal: formalize provider-board reuse, item identity reuse, and sync integrity

18. `graph-action-required-and-stale-queue-enforcement`
   - status: `blocked`
   - goal: require every governed work action to map to graph state and block advancement when queue reconciliation is stale
   - blocker: should be formalized inside `20260312-game-policy-compliance-codex-01-execplan`

19. `future:remaining-work-graph-actions-and-ordering`
   - status: `blocked`
   - goal: formalize deterministic graph actions, canonical ordering fields, and governed reorder/reconciliation behavior
   - blocker: `20260312-game-policy-compliance-codex-01-execplan` should land first

## Queue Discipline

Queued ExecPlans are not active merely because they are listed here. They become active only when:

- a branch is created for the slice
- the ExecPlan exists and validates
- all blocking dependencies are satisfied
- the slice is not held by review or decision gates

Under the current governance model, implementation execution should occur on a dedicated `impl-execplan/*` branch. `queue-execplan/*` branches may be used later for deliberate integration stacking only.

## Relationship to the Graph

This queue is a human-readable mirror of `artifacts/planner/research/remaining-work-graph.json` and `bin/remaining-work-graph-check`. If the two disagree, the canonical artifact and validator are authoritative.
