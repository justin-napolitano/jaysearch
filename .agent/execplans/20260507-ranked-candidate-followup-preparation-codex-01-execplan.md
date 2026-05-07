---
id: "20260507-ranked-candidate-followup-preparation-codex-01-execplan"
title: "Prepare ranked research follow-up inputs from promotable candidates"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260507-ranked-candidate-followup-preparation-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/prepare-research-followups"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/platform-researcher-interface.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/prepare_research_followups.py"
  - "tests/test_prepare_research_followups.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-062"
  queue_position: 62
  implementation_branch: "impl-execplan/20260507-ranked-candidate-followup-preparation-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-ranked-candidate-followup-preparation-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/prepare-research-followups"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/prepare_research_followups.py"
    - "tests/test_prepare_research_followups.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-ranked-candidate-followup-preparation-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-ranked-candidate-followup-preparation-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_prepare_research_followups.py"
      expected_exit: 0
tasks:
  - title: "Add a public orchestration command for preparing draft follow-up inputs from completed research reports"
    priority: "P1"
  - title: "Apply deterministic promotion gates and output stable draft follow-up seed artifacts"
    priority: "P1"
  - title: "Extend tests, docs, and the public orchestration schema for the new façade command"
    priority: "P1"
depends_on:
  - "20260507-ranked-candidate-promotion-codex-01-execplan"
---

## Outcomes & Retrospective

The platform should turn promotable ranked research candidates into deterministic draft follow-up inputs so human-reviewed governed work can start from evidence-backed seeds instead of raw research artifacts.

## Context and Orientation

The external researcher runtime now emits candidate ranking, promotion signals, and follow-up questions. The platform already projects those fields through `run-research-capability`, but it still does not convert them into bounded, reviewable follow-up inputs.

## Plan of Work

Add a public orchestration command that reads a completed `run-research-capability` report, applies the embedded promotion gate, selects promotable candidates, and emits a stable JSON package of draft follow-up inputs plus optional governed ExecPlan seed hints for platform-owned work.

## Validation and Acceptance

This slice is accepted when `prepare-research-followups` returns an `ok` public-orchestration envelope for valid research reports, emits a stable draft follow-up package, and the command is covered by focused tests and the versioned public API schema.

## Artifacts and Notes

This slice intentionally stops at deterministic draft follow-up generation. It does not auto-register new graph nodes or write full ExecPlan markdown from the selected candidates.
