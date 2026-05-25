---
id: "20260521-question-research-handoff-review-v1-codex-01"
title: "Question Research Handoff Review V1"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/design-review-automation-v1.md
  - src/platform_tools/orchestrate_design_review.py
  - tests/test_orchestrate_design_review.py
  - artifacts/orchestration/examples/question-evidence-research-handoff-review-request.packet.json
  - .agent/execplans/20260521-question-research-handoff-review-v1-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/question-research-handoff-review-v1"
initiative_node_id: "initiative-question-research-handoff-review-v1"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "handoff-review-dispatch"
      command: "run focused pytest for design-review orchestration and ensure question_research_handoff_review nodes execute"
      expected_exit: 0
    - name: "real-handoff-request"
      command: "run the question-evidence-research handoff review request through orchestrate-design-review"
      expected_exit: 0

tasks:
  - title: "Add question_research_handoff_review mode to program materialization"
    priority: "P0"
  - title: "Implement bounded handoff review dispatcher"
    priority: "P0"
  - title: "Emit machine-readable handoff review report"
    priority: "P0"
  - title: "Exercise the real handoff review request"
    priority: "P1"

depends_on:
  - "20260521-design-review-automation-runner-v1-codex-01"
---

## Outcomes & Retrospective

This slice makes the upstream question-to-evidence-to-research ambiguity reviewable as a dedicated bounded mode instead of relying on the generic review loop.

## Plan of Work

Phase 1 adds a dedicated mode to the design-review program generator. Phase 2 implements a bounded dispatcher that checks the explicit upstream contracts and tool-boundary docs. Phase 3 exercises the real request and confirms the result is replayable.

## Validation and Acceptance

Acceptance means:

- the review request can ask for `question_research_handoff_review`
- the runner emits a dedicated handoff review result packet
- the output is explicit about missing contracts, weak transforms, or ambiguous boundaries
- the mode stays bounded to contract and doc inspection rather than trying to execute the research runtime
