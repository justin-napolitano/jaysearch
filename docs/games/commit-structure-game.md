# Commit-Structure Game

## Objective

The commit-structure game ensures that Codex-authored slices remain reviewable, procedurally ordered, and small enough for adversarial inspection.

## Layer

The commit-structure game is a subgame-local assurance game under policy compliance.

## Board

The commit-structure board emphasizes:

- branch commit stack
- artifact-class ordering
- commit size
- commit-to-task mapping

## Legal Moves

- stage
- commit
- split
- reorder
- recover

## Local Rule Focus

- human-sized commits
- procedural commit order
- single-class commit grouping

## Win Condition

The commit-structure game succeeds when the branch history remains reviewable in procedural order without collapsing unrelated artifact classes together.

## Loss Condition

The commit-structure game fails when the branch history obscures scope, hides evidence, or forces reviewers to reconstruct the intended order of work from mixed commits.
