# Game Scoring Model

## Purpose

This document defines how the planner and implementation games should be scored without pretending that the scoring system is mathematically inevitable. The scoring model is source-informed, not source-derived. The cited literature and standards justify the dimensions that matter; the exact weights remain platform design choices and must be treated as such.

## Design Principles

The scoring model is grounded in five ideas:

1. mechanism design
   The platform should reward legal, evidence-backed play and punish moves that create incentive problems or hide information.
2. bounded rationality
   The system should penalize unresolved ambiguity and unsupported commitment because agents and humans operate under limited information and attention.
3. provenance
   Scoring should value traceable state and attributable changes.
4. formal transition legality
   A move that violates the game’s transition rules should not score well simply because it appears productive.
5. inspection and verification
   Review and validation are not optional polish. They are core evidence of quality.

## Source Mapping

These dimensions are informed by the following sources:

- mechanism design and rule selection:
  - Eric Maskin, “Mechanism Design: How to Implement Social Goals”
  - Roger Myerson, “Perspectives on Mechanism Design in Economic Theory”
- strategic coordination:
  - John Nash, “Equilibrium Points in N-Person Games”
- bounded rationality:
  - Herbert Simon, “A Behavioral Model of Rational Choice”
- provenance:
  - W3C PROV-DM
  - Git `interpret-trailers` documentation
- formal transition systems:
  - David Harel, “Statecharts: a visual formalism for complex systems”
- inspection and verification:
  - Michael Fagan, “Advances in Software Inspections”
  - Glenford Myers, “A Controlled Experiment in Program Testing and Code Walkthroughs/Inspections”

## Planner Scoring

The planner game should emphasize clarity, legality, and readiness.

Primary planner dimensions:

- transition legality
  - are moves legal under `spec/game-transitions.yaml`
- provenance completeness
  - can state be traced to sessions, artifacts, and commits
- bounded readiness
  - is the work sufficiently bounded to justify commitment
- evidence coverage
  - are decisions, constraints, and validations supported by explicit evidence
- contradiction and blocker pressure
  - do unresolved blockers or contradictions remain high

Planner scoring should punish:

- unsupported readiness claims
- hidden state
- missing provenance
- unresolved blockers hidden behind optimistic summaries
- contract projection attempted before validated readiness

## Implementation Scoring

The implementation game should emphasize scoped execution, verification, and review.

Primary implementation dimensions:

- transition legality
  - are implementation moves legal on the shared board
- scope compliance
  - does implementation stay within selected graph or contract scope
- validation pass rate
  - do required checks pass
- review coverage
  - did hostile review happen and produce attributable results
- recovery discipline
  - are failed runs and partial repairs handled explicitly rather than buried
- provenance completeness
  - are commits, validations, and artifacts linked back to canonical state

Implementation scoring should punish:

- code changes without scope linkage
- skipped or failed validation
- unreviewed completion claims
- recovery-required work presented as done
- provenance gaps between commits, graph state, and contracts

## Weighting Policy

Weights in `spec/scoring.yaml` are policy choices. They should be:

- explicit
- reviewable
- versioned
- adjustable only through governed changes

The sources justify what to measure. They do not dictate exact numeric weights. Any paper or future public write-up should state that clearly.

## Evidence Requirement

No score should be treated as authoritative if it cannot be explained in terms of:

- the move-transition model
- local artifacts
- validation outputs
- review artifacts
- provenance records

If the platform cannot explain a score, the score is decorative and should not drive decisions.

## Citation and Inference Requirement

Every scoring dimension should be traceable to one of two categories:

- source-backed rationale
- explicit platform inference

The references belong in `docs/references.md`, and the inference boundary belongs in `docs/research-assumptions.md`.
