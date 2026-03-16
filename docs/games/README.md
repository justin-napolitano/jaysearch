# Nested Game System

## Objective

The platform is a nested game system, not a single workflow. Each game has its own objective, legal moves, win conditions, and referees, while inheriting shared governance concepts from the larger platform.

## Shared Board Law

All moves on the platform board inherit the same global law before any
domain-specific game rules are considered:

- forbidden moves
- scope compliance
- no hidden state
- canonical state ownership
- determinism requirements
- human authority boundaries

These rules apply to every game and subgame unless a canonical artifact
explicitly narrows how a child game proves compliance. Child games do
not override the existence of this law.

## Hierarchy

The current executable hierarchy is:

1. platform game
2. ExecPlan game
3. planning game
4. implementation game
5. policy-compliance game
6. commit-structure game
7. planning merge-readiness game
8. implementation merge-readiness game
9. hostile-review game

The platform game owns the shared board and its inherited law. The
ExecPlan game acts as the current authority-domain contract game. The
planning and implementation games are work-domain games. Policy
compliance is the current assurance-layer legality game for implementation
branches, and commit structure is its narrower subgame. Each phase ends
in its own merge-readiness proof game under the assurance layer.

This means the platform is not a flat set of peer games. It is:

1. one shared board
2. inherited global board law
3. domain games with local move sets
4. proof/subgames that narrow local obligations further

Policy compliance is where the platform currently proves that a governed
slice cannot advance by assertion alone. Hostile review is the current
review-layer game that consumes that legality surface rather than
replacing it.

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

Games may add phase-specific referee pressure without redefining the
shared validator contract.

Referees should evaluate moves in this order:

1. inherited global board law
2. active domain-game rules
3. active subgame or proof-game rules

Failed moves should be kicked back at the narrowest game boundary that
explains the violation without suppressing any inherited board-law
breach.

## Design Consequence

Future runtime work should be game-aware:

- status surfaces should identify which game a result belongs to
- handoffs should move state between games explicitly
- merge-readiness should be treated as proof within a phase, not as a vague final step
