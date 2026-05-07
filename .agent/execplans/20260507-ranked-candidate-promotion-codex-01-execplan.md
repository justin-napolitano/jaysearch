---
id: "20260507-ranked-candidate-promotion-codex-01-execplan"
title: "Project ranked research candidates and promotable follow-ups through the platform capability command"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - .agent/execplans/20260507-ranked-candidate-promotion-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/public-orchestration-api.md
  - docs/queued-execplans.md
  - docs/system-architecture/platform-researcher-interface.md
  - spec/public-orchestration-api.schema.yaml
  - src/platform_tools/run_research_capability.py
  - tests/test_run_research_capability.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-061"
  queue_position: 61
  implementation_branch: "impl-execplan/20260507-ranked-candidate-promotion-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-ranked-candidate-promotion-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/run_research_capability.py"
    - "tests/test_run_research_capability.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-ranked-candidate-promotion-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-ranked-candidate-promotion-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_run_research_capability.py"
      expected_exit: 0
tasks:
  - title: "Read structured improvement candidate JSON from researcher outputs"
    priority: "P1"
  - title: "Project ranked candidates, promotable candidates, and follow-up questions through the platform envelope"
    priority: "P1"
  - title: "Extend tests and docs for ranked candidate projection"
    priority: "P1"
depends_on:
  - "20260507-research-improvement-projection-codex-01-execplan"
---

## Outcomes & Retrospective

The platform command should return ranked improvement candidates and promotable follow-up inputs, not just raw research artifacts, so later orchestration layers can turn the best candidates into governed work.

## Context and Orientation

The external researcher runtime now emits machine-readable ranked candidates and follow-up questions. The platform already projects structured improvement proposals, but it still does not surface candidate ranking or promotion signals.

## Plan of Work

Extend `run-research-capability` to read the ranked candidate artifact, project candidate ranking and promotable subsets into the returned envelope, and update the response contract, docs, and tests accordingly.

## Validation and Acceptance

This slice is accepted when `run-research-capability` returns stable machine-readable ranked candidate projections, including the promotable subset and follow-up question records.

## Artifacts and Notes

This slice intentionally stops at projection. It does not yet write draft ExecPlans or mutate governed work queues automatically from the projected candidates.
