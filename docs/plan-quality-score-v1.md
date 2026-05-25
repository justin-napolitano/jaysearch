# Plan Quality Score V1

## Objective

Define a standalone tool that compares valid candidate plans for the same selected solution scope and ranks them.

This tool is not:

- the planner
- the design iteration tool
- the evidence search tool

Its purpose is:

- compare valid alternative plans
- explain why one plan is better than another
- apply plan-quality policy consistently

## Role In The System

The intended split is:

- `design-iteration-tool`
  invalidity and drift detection
- `planner-tool`
  candidate plan generation
- `plan-quality-score`
  valid-plan comparison and ranking
- `governance-tool`
  legality of execution

## Hard Boundary

`plan-quality-score` must not:

- repair invalid plans
- generate new plans from scratch
- perform open-ended research by itself
- replace governance

It may:

- consume plan-quality policy
- consume evidence packets
- compare alternative valid plans

## Inputs

Minimum inputs:

- `selected_solution_scope`
- `candidate_plan_refs`
- `plan_quality_policy_ref`

Optional inputs:

- `evidence_packet[]`
- `prior_execution_evidence`
- `memory_tool` reuse context

## Outputs

Primary outputs:

- `plan_quality_score_packet[]`
- `ranked_plan_packet`
- `recommended_plan_ref`

## Comparison Contracts

V1 should define explicit comparison packets:

- `candidate_plan_comparison_packet`
- `plan_quality_score_packet`
- `ranked_plan_packet`

These packets should be machine-readable and should prevent the tool from silently depending on raw planner internals.

## Comparison Rule

Use two stages:

1. reject plans failing hard validity gates
2. rank valid plans using plan-quality policy

See:

- [plan-model-v1.md](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/docs/plan-model-v1.md:1)
- [plan-quality-metrics-v1.md](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/docs/plan-quality-metrics-v1.md:1)
- [plan-quality-scoring.yaml](/mnt/c/Users/jna31a/advent-repos/jna31a_ait/platform-template-bootstrap/spec/plan-quality-scoring.yaml:1)

## V1 Scope

V1 should support:

- comparing 2-5 candidate implementation plans
- same selected solution scope across all candidates
- evidence-aware ranking when relevant
- explicit explanation of tradeoffs
- structural plan comparison before execution-slice materialization

Candidate plans in V1 may be `candidate` plans rather than `execution_ready` plans.

That means:

- nodes and edges must already be machine-readable
- hard-gate validity must already be testable
- execution slices may still be absent during comparison

The chosen plan must be promoted into `execution_ready` form by downstream execution-slice materialization before governance and governed execution.

## Execution Slice Boundary

`plan-quality-score` should compare structural plans, not require every candidate to already be execution-ready.

That means:

- planner or implementation-planner logic may generate several `candidate` structural plans
- `plan-quality-score` ranks those structural plans
- a later execution-slice materialization phase converts the chosen structural plan into an `execution_ready` plan

`plan-quality-score` must not be responsible for generating execution slices itself.

## Non-Goals

V1 should not:

- generate plans
- mutate contracts
- execute plan nodes

## Key Question

This tool answers:

- among valid plans for the same selected scope, which plan is best and why?
