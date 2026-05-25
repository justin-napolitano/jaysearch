---
id: "20260520-plan-quality-score-v1-codex-01"
title: "Plan Quality Score V1"
owner: "agent/codex"
created: "2026-05-20T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/plan-quality-score-v1.md
  - docs/plan-model-v1.md
  - docs/plan-quality-metrics-v1.md
  - spec/plan-model.schema.yaml
  - spec/plan-quality-comparison.schema.yaml
  - spec/plan-quality-scoring.yaml
  - artifacts/planner/research/plan-quality-score-v1-dag.json
  - .agent/execplans/20260520-plan-quality-score-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/plan-quality-score-v1"
initiative_node_id: "initiative-plan-quality-score-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "design-review"
      command: "run design-iteration over the plan-quality-score architecture, contracts, and DAG"
      expected_exit: 0
    - name: "plan-coherence-review"
      command: "review plan-quality-score scope for hard-gate validity, alternative-plan comparison logic, and evidence-aware ranking boundaries"
      expected_exit: 0

tasks:
  - title: "Lock plan-quality-score contract and comparison boundary"
    priority: "P0"
  - title: "Define candidate-plan input and ranked-plan output packets"
    priority: "P0"
  - title: "Implement gated validity then quality comparison policy"
    priority: "P0"
  - title: "Emit explanation and tradeoff packet for chosen structural plan"
    priority: "P1"
  - title: "Integrate runner-facing selection handoff for chosen implementation plan"
    priority: "P1"

depends_on: []
---

## Outcomes & Retrospective

The immediate outcome is a bounded scoring tool that compares valid plans for the same selected solution scope. It should not generate plans, repair invalid plans, or replace governance.

## Context and Orientation

The repository now has:

- a validated design-iteration tool
- a formal plan model
- a formal plan-quality policy

The next step is to turn those definitions into a dedicated `plan-quality-score` tool that can compare competing plans and choose a winner after hard-gate validation.

## Plan of Work

Phase 1 should define the machine-readable comparison contract, candidate-plan input packet, ranked-plan output packet, and the distinction between `candidate` structural plans and `execution_ready` plans. Phase 2 should implement hard-gate filtering plus scoring over multiple candidate plans using quality metrics and evidence-aware tradeoff explanation. Phase 3 should connect the chosen structural plan output to downstream execution-slice materialization and then execution-packet emission.

## Validation and Acceptance

Acceptance means:

- invalid plans are disqualified before scoring
- only comparable plans for the same selected solution scope are ranked
- candidate plans and execution-ready plans are not silently conflated
- the chosen structural plan explanation is machine-readable
- the plan-quality-score role stays separate from planner generation and governance legality

## Artifacts and Notes

The machine-readable bootstrap DAG is stored in `artifacts/planner/research/plan-quality-score-v1-dag.json`.
