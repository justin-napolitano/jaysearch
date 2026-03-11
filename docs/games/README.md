# Nested Game System

## Objective

The platform is a nested game system, not a single workflow. Each game has its own objective, legal moves, win conditions, and referees, while inheriting shared governance concepts from the larger platform.

## Hierarchy

The hierarchy is:

1. platform game
2. ExecPlan game
3. planning game
4. implementation game
5. planning merge-readiness game
6. implementation merge-readiness game

The platform game contains the ExecPlan game. The ExecPlan game contains the planning and implementation games. Each phase ends in its own merge-readiness proof game.

## Shared Ontology

All games use the same core concepts:

- players
- board
- legal moves
- illegal moves
- referees
- evidence
- win conditions
- loss conditions

These concepts may be inherited, narrowed, or overridden only according to `docs/games/game-inheritance.md` and `spec/games/inheritance-rules.yaml`.

## Source-of-Truth Boundaries

The game graph is canonical only for:

- game hierarchy
- parent-child relations
- handoff edges
- inheritance edges

It is not canonical for:

- governance rules
- citation provenance
- artifact-level claim classification

Those remain governed by:

- `artifacts/planner/research/rule-graph.json`
- `artifacts/planner/research/bibliography-graph.json`
- `artifacts/planner/research/claim-registry.json`

## Referee Model

Validators may referee more than one game. Shared referees include:

- `bin/execplan-validate`
- `bin/rule-graph-check`
- `bin/citation-check`
- `bin/run-local-ci`

Games may add phase-specific referee pressure without redefining the shared validator contract.

## Design Consequence

Future runtime work should be game-aware:

- status surfaces should identify which game a result belongs to
- handoffs should move state between games explicitly
- merge-readiness should be treated as proof within a phase, not as a vague final step
