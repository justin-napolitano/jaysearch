---
id: "20260507-research-improvement-projection-codex-01-execplan"
title: "Project structured researcher improvement proposals through the platform capability command"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - .agent/execplans/20260507-research-improvement-projection-codex-01-execplan.md
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
  node_id: "rwg-060"
  queue_position: 60
  implementation_branch: "impl-execplan/20260507-research-improvement-projection-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-research-improvement-projection-codex-01-execplan.md"
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
      command: "bin/execplan-validate .agent/execplans/20260507-research-improvement-projection-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-research-improvement-projection-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_run_research_capability.py"
      expected_exit: 0
tasks:
  - title: "Read structured improvement proposal JSON from researcher outputs"
    priority: "P1"
  - title: "Project improvement targets and proposals through the public orchestration envelope"
    priority: "P1"
  - title: "Extend tests and docs for structured proposal projection"
    priority: "P1"
depends_on:
  - "20260507-platform-researcher-integration-codex-01-execplan"
---

## Outcomes & Retrospective

The platform command should return structured improvement-proposal data, not just opaque paths, so later orchestration layers can route follow-up work programmatically.

## Context and Orientation

The external researcher runtime now emits machine-readable improvement proposal artifacts. The platform already invokes the runtime, but it still treats those artifacts as opaque output paths. This slice projects the structured proposal content into the platform command response.

## Plan of Work

Extend `run-research-capability` to read the improvement proposal JSON when present, project its targets and proposals into the returned envelope, and update the versioned schema, docs, and tests accordingly.

## Validation and Acceptance

This slice is accepted when `run-research-capability` returns a stable machine-readable projection of structured improvement proposals and the response contract and tests cover that shape.

## Artifacts and Notes

This slice intentionally stops at response projection. It does not yet create automatic follow-up nodes or write new governed work items from the projected proposals.
