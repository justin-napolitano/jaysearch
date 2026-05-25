---
id: "20260521-question-research-handoff-review-v2-codex-01"
title: "Question Research Handoff Review V2"
owner: "agent/codex"
created: "2026-05-21T00:00:00Z"
status: draft
base_branch: main
changes:
  - docs/design-review-automation-v1.md
  - src/platform_tools/orchestrate_design_review.py
  - tests/test_orchestrate_design_review.py
  - artifacts/planner/research/question-research-handoff-review-v2-dag.json
  - .agent/execplans/20260521-question-research-handoff-review-v2-codex-01-execplan.md
approve_policy: codeowners
reviewers:
  - "github:jna31a"

initiative_branch: "initiative/question-research-handoff-review-v2"
initiative_node_id: "initiative-question-research-handoff-review-v2"

finalized_by: ""
finalized_at: ""
finalized_in_pr: ""

validation:
  tests:
    - name: "handoff-review-artifact-level"
      command: "run focused pytest for design-review orchestration and ensure artifact-level handoff review behavior is explicit"
      expected_exit: 0
    - name: "real-handoff-request-v2"
      command: "run the question-evidence-research handoff review request and expect explicit artifact-level signal"
      expected_exit: 0

tasks:
  - title: "Define stricter handoff review DAG"
    priority: "P0"
  - title: "Inspect packet example availability for research_question and research_problem"
    priority: "P0"
  - title: "Inspect transform artifact availability for question_to_research_problem_transform"
    priority: "P0"
  - title: "Emit explicit artifact-level blockers and artifact refs"
    priority: "P0"
  - title: "Rerun the real upstream handoff review"
    priority: "P1"

depends_on:
  - "20260521-question-research-handoff-review-v1-codex-01"
---

## Outcomes & Retrospective

V1 proved the handoff docs and shared registry are internally aligned. V2 hardens the review around runtime readiness by checking whether the repo actually contains example packet artifacts and transform surfaces for the upstream handoff.

## Plan of Work

Phase 1 defines the stricter handoff-review DAG. Phase 2 strengthens the bounded review node to inspect artifact-level readiness, not just docs. Phase 3 reruns the real handoff request and captures the resulting blockers as the next upstream problem set.

## Validation and Acceptance

Acceptance means:

- the handoff review mode checks artifact-level readiness
- missing packet examples or missing transform surfaces become explicit blockers
- the real question-evidence-research handoff request produces replayable signal when those artifacts are absent
