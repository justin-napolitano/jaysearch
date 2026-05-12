---
id: "20260512-candidate-conflict-detection-codex-01-execplan"
title: "Detect structured conflicts between ranked research candidates"
owner: "agent/codex-01"
created: "2026-05-12T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260512-candidate-conflict-detection-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/candidate-selection-and-conflict-resolution.md"
  - "src/platform_tools/prepare_research_followups.py"
  - "tests/test_prepare_research_followups.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-069"
  queue_position: 69
  implementation_branch: "impl-execplan/20260512-candidate-conflict-detection-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "capability-contracts"
    - "governance"
    - "orchestration"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260512-candidate-conflict-detection-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/candidate-selection-and-conflict-resolution.md"
    - "src/platform_tools/prepare_research_followups.py"
    - "tests/test_prepare_research_followups.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260512-candidate-conflict-detection-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_prepare_research_followups.py"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260512-candidate-conflict-detection-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Emit structured conflict groups from ranked candidates"
    priority: "P1"
  - title: "Attach candidate-level conflict references to follow-up artifacts"
    priority: "P1"
  - title: "Cover promotion-cap and sequencing conflict cases with focused tests"
    priority: "P1"
depends_on:
  - "20260511-candidate-selection-contract-codex-01-execplan"
---

## Outcomes & Retrospective

The research loop now needs a deterministic way to represent competing candidate actions instead of treating all deferred items as equivalent.

## Context and Orientation

`prepare_research_followups` is the natural place to attach conflict metadata because it already applies promotion gating and caps the number of selected candidates.

## Plan of Work

Add executable conflict detection for resource, design, sequencing, and assumption conflicts, and emit both top-level conflict groups and candidate-level conflict references in the follow-up artifact.

## Validation and Acceptance

This slice is accepted when prepared follow-up artifacts include structured conflicts, focused tests cover at least promotion-cap and sequencing cases, and the governed graph registers the slice cleanly.

## Artifacts and Notes

This slice intentionally stays at the conflict-detection layer. Conflict resolution ranking remains governed by the selection contract and can be automated further in a later slice.
