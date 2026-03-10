# Planner Phase 2 Backlog

## Objective

This backlog turns the planner control-plane design package into implementation-sized work packages without reopening core architecture questions.

## Proposed Follow-On Work

1. Implement planner session persistence and transcript capture under `src/platform_tools/`.
2. Implement canonical graph persistence and validation from `spec/task-graph.schema.yaml`.
3. Add `bin/planner` wrapper commands that delegate to canonical implementation logic.
4. Write the implementation runtime plan for the planner and implementation orchestrators, including process model, persistence boundaries, and validator integration.
5. Expand the CLI/runtime contract into concrete command arguments, session-targeting rules, artifact paths, and machine-readable output formats.
6. Implement planner-to-ExecPlan draft generation.
7. Implement planner-specific validation aggregation.
8. Implement a validator that checks citation-versus-inference labeling and bibliography-graph coverage for governed design and implementation artifacts.
9. Scaffold GitHub Projects sync against the provider adapter contract.
10. Add placeholder adapter interfaces for Jira and Microsoft Lists without live integrations.
11. Add deterministic tests for session artifacts, graph validation, contract projection, and contract import reconciliation.
12. Add hostile-review coverage for planner artifacts and command outputs.
13. Design the implementation orchestrator as the next game phase using the same board, referee, and evidence model.
14. Implement bibliography graph generation and validation so research provenance remains machine-readable.
15. Enforce citation-or-inference labeling in future design and implementation artifacts.
16. Implement the coded scoring engine for planner-game and implementation-game metrics defined in `spec/scoring.yaml`.

## Sequencing

- session persistence and graph validation should precede contract drafting
- contract drafting should precede provider sync
- provider sync should precede any future execution authority discussion

## Out of Scope for Phase 2

- UI implementation
- external system authority
- autonomous code-writing from planner ideation
- full bidirectional provider sync
