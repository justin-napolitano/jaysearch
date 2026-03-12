# Planning Game

## Objective

The planning game reduces ambiguity and shapes intent into explicit, auditable state.

## Layer

The planning game is a work-domain game. It inherits global board law
and ExecPlan constraints, then narrows them to ambiguity reduction,
decomposition, and graph formation.

## Board

The planning board is the canonical graph plus planner session artifacts.

## Legal Moves

- propose
- challenge
- refine
- answer
- constrain
- decompose
- validate
- commit

## Local Rule Focus

- ambiguity reduction
- dependency declaration
- blocker visibility
- citation-backed design constraints

## Win Condition

The planning game succeeds when intent is bounded, blockers are explicit, and commitment state is justified.

## Child Proof Game

The planning game terminates in the planning merge-readiness game, which proves whether planning outputs are ready to become governed contract or downstream implementation inputs.
