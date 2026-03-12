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
   - status: `ready`
   - goal: formalize board review, takeover, and merge reconciliation as machine-readable runtime state
   - implementation branch: `impl-execplan/20260312-human-operations-review-runtime-codex-01-execplan-codex-01-20260312`

## Queue Discipline

Queued ExecPlans are not active merely because they are listed here. They become active only when:

- a branch is created for the slice
- the ExecPlan exists and validates
- all blocking dependencies are satisfied
- the slice is not held by review or decision gates

Under the current governance model, implementation execution should occur on a dedicated `impl-execplan/*` branch. `queue-execplan/*` branches may be used later for deliberate integration stacking only.

## Relationship to the Graph

This queue is a human-readable mirror of `artifacts/planner/research/remaining-work-graph.json` and `bin/remaining-work-graph-check`. If the two disagree, the canonical artifact and validator are authoritative.
