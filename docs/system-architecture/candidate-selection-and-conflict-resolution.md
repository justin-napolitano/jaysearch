# Candidate Selection And Conflict Resolution

## Objective

Define how research outputs become actionable governed work, and how conflicting candidate actions are resolved.

## Core Principle

Research outputs do not become work items just because they are interesting.

A candidate is worth promoting only when it is both:

- credible
- actionable

## Flow

The control-plane decision flow is:

1. question
2. hypothesis
3. evidence
4. candidate action
5. eligibility gate
6. ranked comparison
7. conflict resolution
8. disposition
9. draft ExecPlan promotion if approved

## Eligibility Gate

A candidate must satisfy all of the following before it is promotable:

- clear problem statement
- bounded proposed change
- explicit target repo or target surface
- at least one usable evidence reference
- expected benefit stated explicitly
- no obvious contract or governance violation
- reversibility understood well enough to review

Candidates that fail the gate must not be promoted directly into ExecPlan material.

They should instead be marked as one of:

- `research_more`
- `defer`
- `reject`

## Ranking Dimensions

Candidates that pass the gate should be ranked on these dimensions:

- `impact`
- `feasibility`
- `rigor`
- `time_to_value`
- `operational_cost`
- `reversibility`
- `dependency_load`
- `governance_fit`

## Default Weighting

The default weighted model is:

- `impact`: `0.20`
- `feasibility`: `0.20`
- `rigor`: `0.20`
- `governance_fit`: `0.15`
- `time_to_value`: `0.10`
- `reversibility`: `0.05`
- `operational_cost`: `0.05`
- `dependency_load`: `0.05`

These weights are meant to favor:

- well-supported actions
- shippable actions
- actions that fit the governed contract-first model

## Promotion Thresholds

Ranking alone is not enough.

A candidate should only be promoted when:

- the candidate disposition is `promote-to-execplan`
- rigor meets the minimum threshold
- feasibility meets the minimum threshold
- total score meets the minimum threshold
- the evidence set is non-empty
- the target repo or owning surface is explicit

The researcher runtime may emit the thresholds, but the platform control plane remains the final gatekeeper for promotion.

## Conflict Types

Conflicts must be classified before resolution.

Use these conflict types:

- `resource_conflict`
- `design_conflict`
- `sequencing_conflict`
- `assumption_conflict`

### Resource Conflict

Both candidates may be valid, but available bandwidth only supports one.

### Design Conflict

Both candidates modify the same surface in incompatible ways.

### Sequencing Conflict

Both candidates may be valid, but one should happen before the other.

### Assumption Conflict

The candidates depend on incompatible beliefs, so research is incomplete.

## Resolution Order

When candidates conflict, resolve them in this order:

1. higher rigor wins if one candidate is materially weaker
2. if rigor is close, higher impact wins
3. if impact is close, lower operational burden wins
4. if burden is close, the more reversible candidate wins
5. if still close, the candidate that unlocks more follow-on work wins

If a conflict remains unresolved after this sequence, the control plane should mark it as `research_more` rather than forcing an arbitrary promotion.

## Disposition States

Every candidate should end in one of these states:

- `promote_to_execplan`
- `defer`
- `research_more`
- `reject`
- `superseded_by_other_candidate`

These states should be explicit in both human-readable and machine-readable artifacts.

## Value Of Research

A research run is worthwhile if it produces at least one of the following:

- a promotable candidate
- a justified rejection of a weak direction
- a materially narrowed decision space
- a new high-value question that reduces uncertainty

Research is not only valuable when it recommends building something.

Preventing low-value or poorly supported work is also a successful output.

## Control Plane Responsibilities

The platform repo should:

- enforce the promotion gate
- emit machine-readable gate evaluations per candidate
- distinguish between gate failure, promotion-cap deferral, and final selection
- preserve candidate scores and evidence references
- emit machine-readable conflict groups and candidate-level conflict references
- resolve conflicts explicitly
- generate draft follow-up material only for eligible candidates
- avoid silently discarding lower-ranked or conflicting candidates

## Researcher Responsibilities

The researcher runtime should:

- emit structured candidates with evidence-backed scores
- mark conflict signals when they are visible
- emit a recommended disposition per candidate
- surface follow-up questions when evidence is incomplete

## Draft ExecPlan Promotion Rule

Draft ExecPlan material should only be produced for candidates that are:

- eligible
- ranked
- conflict-resolved
- still marked `promote_to_execplan`

This keeps research questions, hypotheses, and raw candidate ideas from turning directly into implementation work without governed review.
