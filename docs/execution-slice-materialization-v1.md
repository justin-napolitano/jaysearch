# Execution Slice Materialization V1

## Objective

Define the planner-owned phase that converts a chosen structural plan into an execution-ready plan plus governed runnable execution packets.

This tool or planner phase is not:

- plan generation
- plan ranking
- governance
- code execution

Its purpose is to:

- take one chosen structural plan
- group nodes into runnable execution slices
- attach runnable preconditions
- attach completion evidence requirements
- emit execution-ready planning semantics for governance intake

## Role In The System

The intended split is:

- `planner-tool`
  generates candidate structural plans
- `plan-quality-score`
  compares valid structural plans and recommends one
- `execution-slice-materialization`
  converts the chosen structural plan into execution-ready form
- `governance-tool`
  decides whether execution-ready slices may run

## Hard Boundary

`execution-slice-materialization` must not:

- choose the winning plan
- repair invalid structural plans silently
- approve execution
- run code or mutate the repo

It may:

- group plan nodes into runnable slices
- define required inputs and expected outputs
- define runnable preconditions
- define completion evidence requirements
- emit execution-facing packet structure

## Inputs

Minimum inputs:

- `selected_solution_scope`
- chosen structural `implementation_plan`
- `execution_materialization_policy_ref`

Optional inputs:

- `plan_quality_score_packet[]`
- `ranked_plan_packet`
- evidence refs relevant to execution safety
- reuse context for known slice patterns

## Outputs

Primary outputs:

- `execution_ready_plan_packet`
- `execution_packet[]`

Secondary outputs:

- slice grouping explanation
- materialization warnings

## Core Rule

This phase happens after plan comparison.

The planning order is:

1. generate candidate structural plans
2. compare and choose one structural plan
3. materialize execution slices
4. hand execution-ready artifacts to governance

Candidate plans should not be forced to invent execution slices prematurely.

## Allowed Transformations

This phase may:

- group one or more existing structural plan nodes into a runnable slice
- carry forward existing dependency semantics into slice-level dependency semantics
- attach runnable preconditions and completion evidence requirements

This phase must not:

- change selected solution scope
- invent new structural work not present in the chosen plan
- reinterpret plan ranking authority
- silently rewrite node meaning in order to make slicing easier

## Materialization Rule

Execution slices should be created only when:

- node boundaries are clear enough to run
- dependencies are explicit enough to govern
- validation targets are clear enough to check
- completion evidence is clear enough to prove

Materialization should reject or warn on plans where runnable slicing would require hidden prose interpretation.

## V1 Scope

V1 should support:

- one chosen structural plan at a time
- simple deterministic slice grouping rules
- emission of execution-ready plan metadata
- emission of `execution_packet[]`
- machine-readable warnings when materialization is lossy or ambiguous

## Non-Goals

V1 should not:

- optimize for global scheduling
- rewrite the chosen plan structure
- merge governance policy into planner logic
- execute slices

## Key Question

This tool answers:

- how do we turn a chosen structural plan into governed runnable work without making governance reconstruct planning semantics?
