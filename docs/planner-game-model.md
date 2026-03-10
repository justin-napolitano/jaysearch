# Planner Game Model

## Purpose

The planner is not a generic chat tool. It is a governed game for converting uncertain intent into auditable, commitment-ready state. The game exists to reward explicit structure, evidence, and coordination while punishing ambiguity, hidden state, and fake readiness.

## Game Type

The planner is best modeled as a mechanism-designed sequential coordination game with adversarial review and explicit commitment stages.

That means:

- work proceeds in turns
- different actors have distinct roles
- the rules are designed to make good behavior easier than sloppy behavior
- critique is part of the game rather than a failure mode
- commitment requires stronger evidence than exploration

## Players

- human operator
  - sets intent, evaluates tradeoffs, and retains final authority
- planner facilitator
  - structures intent into explicit artifacts and graph state
- planner critic
  - attacks weak assumptions, vague scope, and unsupported readiness claims
- validator referee
  - determines whether state transitions are legal
- project-manager observers
  - consume downstream projections without becoming game authorities

## Board

The game board is the canonical local task graph plus linked planner session artifacts.

Board state includes:

- goals
- decisions
- questions
- constraints
- tasks
- validations
- risks
- artifacts
- dependencies
- evidence
- contract projections

## Moves

Legal planner moves include:

- propose
- challenge
- refine
- answer
- constrain
- decompose
- validate
- commit
- import
- project

Move intent:

- `propose` creates candidate structure
- `challenge` attacks weak assumptions or unsupported claims
- `refine` tightens previously vague state
- `answer` resolves blocking questions
- `constrain` makes boundaries explicit
- `decompose` turns larger intent into graph-ready work
- `validate` requests referee judgment
- `commit` projects canonical state into an ExecPlan contract
- `import` reconciles approved contract edits back into canonical state
- `project` syncs selected state outward to observer systems

## Move Legality

Move names alone are not sufficient. Legal play requires explicit transition rules.

The authoritative move-transition model lives in `spec/game-transitions.yaml`.

That spec defines, per move:

- allowed source states
- allowed target states
- whether referee approval is required
- minimum evidence required to make the move legal

If a proposed move does not satisfy the transition contract, it is illegal even if it sounds reasonable in chat.

## Illegal Moves

Illegal moves include:

- hidden state mutation
- implicit current-session authority outside explicit local artifacts
- direct code-writing from ideation mode
- provider-controlled canonical state
- contract edits treated as canonical without explicit import
- readiness claims without supporting graph state or evidence
- validation bypass without governed exception handling

## Commitment Stages

The planner game has three commitment levels:

1. Exploration
   Ideas are allowed to be incomplete, but they must remain explicitly marked as uncertain.
2. Structured readiness
   Graph state becomes specific enough to support blocked and ready views.
3. Contract commitment
   State is strong enough to become a governed ExecPlan draft.

The burden of proof increases at each stage.

Planner commitment stages map onto board states:

- exploration work primarily lives in `draft`
- structured readiness uses `ready` and `blocked`
- referee-confirmed planning uses `validated`
- contract commitment uses `in_review` until contract state is accepted or imported

## Win Conditions

A planner round succeeds when:

- the objective is bounded
- key constraints are explicit
- important decisions have rationale
- unresolved questions are visible
- graph state is valid
- contract projection, if attempted, is justified by readiness and evidence

## Loss Conditions

The planner round fails when:

- state becomes ambiguous or contradictory
- hidden assumptions remain necessary for progress
- canonical state and contract state drift without reconciliation
- provider projections distort local semantics
- critique identifies unresolved blockers that were ignored

## Scoring Signals

The planner may later expose scoring signals such as:

- readiness score
- contradiction count
- unresolved blocker count
- evidence coverage
- validation pass rate
- contract drift count

These are signals for review, not autonomous authority.

The source-informed scoring rationale is defined in `docs/game-scoring-model.md` and implemented by policy in `spec/scoring.yaml`.

## Mapping to Existing Artifacts

- planner session artifacts record moves and extracted state
- the canonical task graph represents the board
- prompt families represent governed player roles
- validators act as referees
- ExecPlans are commitment artifacts
- sync adapters publish observer views

## Citation Requirement

Claims about why the planner game is structured this way should be either:

- explicitly tied to cited sources listed in `docs/references.md`, or
- explicitly marked as platform design inferences in `docs/research-assumptions.md`

This prevents the framework from laundering arbitrary design choices as if they were established by literature.
