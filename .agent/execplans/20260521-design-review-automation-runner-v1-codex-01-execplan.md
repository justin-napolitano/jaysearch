---
id: "20260521-design-review-automation-runner-v1-codex-01"
title: "Design Review Automation Runner V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/design-review-automation-v1.md
  - spec/design-review-program.schema.yaml
  - artifacts/planner/research/design-review-automation-v1-dag.json
  - src/platform_tools/orchestrate_design_review.py
  - src/platform_tools/review_evidence_adapter.py
  - tests/test_orchestrate_design_review.py
  - tests/test_review_evidence_adapter.py
  - artifacts/orchestration/examples/design-review-request.packet.json
  - .agent/execplans/20260521-design-review-automation-runner-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/design-review-automation-runner-v1"
initiative_node_id: "initiative-design-review-automation-runner-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "runner-review-flow"
      command: "run focused pytest for design-review orchestration, evidence adapter, design iteration, plan quality, governance intake, and execution materialization"
      expected_exit: 0
    - name: "design-review-request-shape"
      command: "exercise one real repo-level design_review_request_packet through materialize_review_program"
      expected_exit: 0

tasks:
  - title: "Add review-program request-to-runner workflow"
    priority: "P0"
  - title: "Wire bounded evidence adapter into review dispatch"
    priority: "P0"
  - title: "Emit replayable tool_call_request/result packets"
    priority: "P0"
  - title: "Create one real repo-level design_review_request_packet"
    priority: "P1"
  - title: "Keep unsupported review calls explicit instead of silent"
    priority: "P1"

depends_on:
  - "20260520-plan-quality-score-v1-codex-01"
  - "20260520-execution-slice-materialization-v1-codex-01"
---

## Outcomes & Retrospective

This slice should give the system a real front-door control loop for design review. It does not finish the whole evidence-search runtime; it only makes evidence-aware review operational through bounded, replayable calls.

## Context and Orientation

The repository already has:

- a validated design-iteration tool
- plan-quality scoring
- execution-slice materialization
- governance execution intake
- the first design-review runner surface

The remaining gap is runner-side automation that can consume a design review request, produce a review program, call bounded tools, and return machine-readable findings.

## Plan of Work

Phase 1 materializes a review program from a request packet and executes supported review nodes through the runner. Phase 2 adds a bounded evidence adapter so evidence-backed claim review is operational without pretending the full search runtime already exists. Phase 3 seeds a real repo-level request artifact and validates the workflow end to end.

## Validation and Acceptance

Acceptance means:

- one request packet can produce a review program
- the runner emits replayable request/result packets for each tool call
- planning-quality and governance-handoff review nodes execute successfully
- evidence-backed claim review has a bounded adapter path
- unsupported review nodes stay explicit and blocking

## Artifacts and Notes

The architectural DAG remains `artifacts/planner/research/design-review-automation-v1-dag.json`. The request example should live under `artifacts/orchestration/examples/`.
