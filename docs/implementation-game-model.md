# Implementation Game Model

## Purpose

Implementation should follow the same game logic as planning rather than dropping into ungoverned execution. The implementation tool should therefore operate as a governed continuation of the planner game, with stronger referee pressure and tighter evidence requirements.

## Relationship to the Planner

The planner game produces bounded, auditable intent and contract state.

The implementation game consumes:

- canonical graph state
- approved or draft contract projections
- validation requirements
- explicit constraints and decisions

Implementation must not invent a second source of truth. It plays on the same board with additional move types and stricter consequences.

The authoritative move-transition rules also live in `spec/game-transitions.yaml`.

## Players

- human operator
  - approves direction, interprets findings, and retains final authority
- implementation orchestrator
  - executes scoped work against the contract and canonical graph
- hostile reviewer
  - attacks regressions, missing tests, drift, and unsafe shortcuts
- validator referee
  - enforces transition legality and quality gates

## Additional Moves

Legal implementation moves include:

- select
- implement
- verify
- review
- recover
- escalate
- finalize

Move intent:

- `select` chooses ready graph nodes or contract tasks
- `implement` makes scoped changes linked back to canonical provenance
- `verify` runs required validation commands
- `review` performs hostile inspection against the implementation result
- `recover` handles partial failure or rerun state explicitly
- `escalate` requests human attention when policy or safety boundaries are hit
- `finalize` prepares human-governed closure but does not bypass it

## Illegal Moves

Illegal implementation moves include:

- implementing from vague or blocked state
- mutating code outside the agreed scope without explicit contract update
- claiming success without validation evidence
- bypassing hostile review where required
- letting implementation commits drift from session, graph, or contract provenance

## Referee Model

Implementation requires stronger referee involvement than planning.

The referee layer should evaluate:

- branch legality
- scope compliance
- validation outcomes
- evidence completeness
- contract drift
- recovery correctness after partial failure

Implementation requires explicit board states that can represent:

- work selected but not yet complete
- work under hostile review
- work validated but not yet accepted as complete
- work requiring recovery before progress can continue

## Review Loop

Implementation should preserve adversarial review as a first-class step:

1. select ready work
2. implement
3. verify
4. hostile review
5. recover or refine if needed
6. prepare for human finalization

This keeps the implementation tool aligned with the planner’s anti-workslop goals.

The shared board should therefore support at least these implementation-relevant states:

- `in_progress`
- `in_review`
- `validated`
- `recovery_required`
- `done`

## Shared Scoring Signals

The implementation tool should eventually expose signals that align with the planner game:

- validation pass rate
- unreviewed change count
- drift count between implementation and contract
- recovery event count
- evidence coverage per completed task

The source-informed scoring rationale is defined in `docs/game-scoring-model.md` and implemented by policy in `spec/scoring.yaml`.

## Design Consequence

The platform should treat planning and implementation as two phases of one governed game:

- planning optimizes for clarity and valid commitment
- implementation optimizes for scoped execution and evidence-backed completion

That means the later implementation tool should reuse:

- canonical graph provenance
- contract projection semantics
- validator referee behavior
- hostile review patterns

rather than inventing a separate workflow language.

## Citation Requirement

Claims about implementation-game legality, review pressure, scoring, and evidence should be either:

- explicitly tied to cited sources listed in `docs/references.md`, or
- explicitly marked as platform design inferences in `docs/research-assumptions.md`

Implementation guidance should not present arbitrary orchestration choices as if they were literature-backed when they are actually policy decisions.
