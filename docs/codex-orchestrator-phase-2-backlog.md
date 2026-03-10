# Codex Orchestrator Phase 2 Backlog

## Objective

This backlog turns the orchestrator contract into concrete runtime work without reopening the authority model or merge-readiness rules.

## Proposed Follow-On Work

1. Add machine-readable JSON output modes to `bin/planner`, `bin/citation-check`, `bin/planner-score`, and `bin/rule-graph-check`.
2. Implement a composite orchestrator status command that reports ready work, blockers, required validations, and active authority constraints.
3. Implement a machine-readable merge-readiness command that aggregates validations, smoke tests, artifact hygiene, and approval requirements.
4. Implement explicit stop-condition reporting for blocked orchestration states.
5. Implement orchestrator-facing task selection against the canonical graph and scoring model.
6. Implement implementation-phase orchestration using the same board, move rules, and evidence model as the planner phase.
7. Add deterministic branch hygiene checks for generated artifacts and commit-size compliance.
8. Add hostile-review report generation as a machine-readable orchestration step.
9. Add richer provenance links between canonical graph state, implementation changes, and merge-readiness outputs.

## Sequencing

- machine-readable output hardening should precede the composite orchestrator status command
- merge-readiness aggregation should precede implementation-phase orchestration
- implementation-phase orchestration should precede any provider-sync work that depends on execution state

## Out of Scope for This Backlog

- richer human-facing CLI presentation
- external system authority
- autonomous exception approval
- replacing human finalization requirements
