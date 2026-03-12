# Game Inheritance

## Objective

The nested game system only works if inheritance and override rules are explicit.

## Scope Levels

Rules exist at three scopes:

- global board law
- domain-game rules
- subgame-local or proof-game rules

Global board law applies to every move on the shared platform board.
Domain games inherit that law and add local move sets. Subgames and
proof games inherit both and may narrow local obligations further.

The current policy-compliance game is an assurance-layer domain game
under implementation. The current commit-structure game is a narrower
subgame under policy compliance.

## Inherited by Default

These concepts inherit from parent game to child game unless explicitly narrowed:

- global board law
- authority boundaries
- evidence requirements
- referee identities
- canonical board identity
- source-of-truth boundaries

## Locally Overridable

These concepts may be overridden locally if the override is explicit and does not contradict parent governance:

- legal move subsets
- scoring emphasis
- local win conditions
- local loss conditions
- local handoff criteria

## Forbidden Overrides

Child games may not override:

- forbidden-move boundaries
- scope-compliance boundaries
- human-only finalization authority
- canonical source-of-truth ownership
- validator authority to reject illegal moves
- no-hidden-state requirement

## Referee Order

Referees should review moves in deterministic order:

1. global board law
2. active domain-game rules
3. active subgame or proof-game rules

Child games may narrow local checks, but they must not skip inherited
global law.

## Merge-Readiness Rule

Merge-readiness games inherit authority and evidence rules by default, but they narrow legal moves and win conditions to proof obligations only.
