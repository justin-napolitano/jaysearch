# Queued ExecPlans

## Objective

This document turns the remaining-work graph into an explicit near-term queue of planned slices.

## Initial Queue

1. `20260311-machine-readable-output-hardening-codex-01-execplan`
   - status: `ready`
   - goal: add stable JSON contracts across key orchestrator-facing commands

2. `20260311-composite-orchestrator-status-codex-01-execplan`
   - status: `blocked`
   - blocked by: machine-readable output hardening
   - goal: expose ready work, blockers, rule constraints, and required validations in one command

3. `20260311-game-graph-validator-and-status-codex-01-execplan`
   - status: `ready`
   - goal: validate the nested game graph and expose active game/subgame status for orchestration

4. `20260311-implementation-orchestrator-runtime-codex-01-execplan`
   - status: `blocked`
   - blocked by: composite orchestrator status, game-graph validator and status
   - goal: execute implementation-phase moves against the shared board and evidence model

5. `20260311-provider-sync-scaffold-codex-01-execplan`
   - status: `review_gated`
   - goal: scaffold provider adapters without granting external authority

## Queue Discipline

Queued ExecPlans are not active merely because they are listed here. They become active only when:

- a branch is created for the slice
- the ExecPlan exists and validates
- all blocking dependencies are satisfied
- the slice is not held by review or decision gates

## Relationship to the Graph

This queue is a human-readable projection of `artifacts/planner/research/remaining-work-graph.json`. If the two disagree, the graph is authoritative.
