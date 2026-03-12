# Implementation Game

## Objective

The implementation game executes scoped work under contract and validator pressure.

## Layer

The implementation game is a work-domain game. It inherits global board
law and ExecPlan constraints, then narrows them to scoped execution,
verification, recovery, and review preparation.

## Board

The implementation board is the same canonical graph, but with stronger emphasis on:

- scoped file changes
- verification evidence
- hostile review state
- recovery state

## Legal Moves

- select
- implement
- verify
- review
- recover
- escalate

## Local Rule Focus

- scoped file changes
- verification evidence
- recovery state
- review readiness preparation

## Win Condition

The implementation game succeeds when scoped work is completed with evidence, validation, and review.

## Child Proof Game

The implementation game terminates in the implementation merge-readiness game, which proves whether the branch is legally ready for human review and merge handling.
