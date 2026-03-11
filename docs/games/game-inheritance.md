# Game Inheritance

## Objective

The nested game system only works if inheritance and override rules are explicit.

## Inherited by Default

These concepts inherit from parent game to child game unless explicitly narrowed:

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

- human-only finalization authority
- canonical source-of-truth ownership
- validator authority to reject illegal moves
- no-hidden-state requirement

## Merge-Readiness Rule

Merge-readiness games inherit authority and evidence rules by default, but they narrow legal moves and win conditions to proof obligations only.
