---
id: "20260512-executable-research-gating-codex-01-execplan"
title: "Make research candidate gating executable in the control plane"
owner: "agent/codex-01"
created: "2026-05-12T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260512-executable-research-gating-codex-01-execplan.md"
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
  node_id: "rwg-068"
  queue_position: 68
  implementation_branch: "impl-execplan/20260512-executable-research-gating-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "capability-contracts"
    - "governance"
    - "orchestration"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260512-executable-research-gating-codex-01-execplan.md"
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
      command: "bin/execplan-validate .agent/execplans/20260512-executable-research-gating-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_prepare_research_followups.py"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260512-executable-research-gating-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Make promotion gates executable in prepare_research_followups"
    priority: "P1"
  - title: "Emit machine-readable gate evaluations and selection statuses per candidate"
    priority: "P1"
  - title: "Pin the new gating behavior with focused tests"
    priority: "P1"
depends_on:
  - "20260511-candidate-selection-contract-codex-01-execplan"
---

## Outcomes & Retrospective

The selection contract is documented, but the runtime still needs to apply it explicitly so later conflict-resolution and backlog slices have deterministic candidate state to build on.

## Context and Orientation

`prepare_research_followups` is the first control-plane step that turns raw research outputs into actionable follow-up material. This slice makes that step emit explicit gate-evaluation and selection-status data instead of silently treating all non-selected candidates the same.

## Plan of Work

Implement executable candidate gating in `prepare_research_followups`, attach machine-readable gate evaluations to each candidate, and expose a compact selection summary for downstream orchestration.

## Validation and Acceptance

This slice is accepted when the runtime emits stable gate-evaluation metadata, focused tests cover promotion-cap and gate-failure cases, and the governed graph registers the slice cleanly.

## Artifacts and Notes

This slice is intentionally narrow. Conflict detection and research backlog work come next, after the gate output is stable.
