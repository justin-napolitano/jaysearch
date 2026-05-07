---
id: "20260507-platform-seed-draft-rendering-codex-01-execplan"
title: "Materialize follow-up packets and render platform draft ExecPlan artifacts"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260507-platform-seed-draft-rendering-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/materialize-research-followup-assets"
  - "bin/render-platform-execplan-drafts"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/platform-researcher-interface.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/materialize_research_followup_assets.py"
  - "src/platform_tools/render_platform_execplan_drafts.py"
  - "tests/test_materialize_research_followup_assets.py"
  - "tests/test_render_platform_execplan_drafts.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-064"
  queue_position: 64
  implementation_branch: "impl-execplan/20260507-platform-seed-draft-rendering-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-platform-seed-draft-rendering-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/materialize-research-followup-assets"
    - "bin/render-platform-execplan-drafts"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/materialize_research_followup_assets.py"
    - "src/platform_tools/render_platform_execplan_drafts.py"
    - "tests/test_materialize_research_followup_assets.py"
    - "tests/test_render_platform_execplan_drafts.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-platform-seed-draft-rendering-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-platform-seed-draft-rendering-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_materialize_research_followup_assets.py tests/test_render_platform_execplan_drafts.py"
      expected_exit: 0
tasks:
  - title: "Add a façade command that materializes projected follow-up packets into platform seed assets and external repo request packets"
    priority: "P1"
  - title: "Add a façade command that renders materialized platform seed assets into draft ExecPlan candidate files"
    priority: "P1"
  - title: "Extend the public command surface and focused tests for post-packet execution artifacts"
    priority: "P1"
depends_on:
  - "20260507-repo-followup-packet-projection-codex-01-execplan"
---

## Outcomes & Retrospective

Projected follow-up packets should become tangible handoff assets and draft ExecPlan candidate files so the next supervising session can move directly into reviewed execution rather than reinterpreting intermediate structures.

## Context and Orientation

The platform can already project repo-specific follow-up packets from ranked research results. This slice advances the execution chain by materializing those packets into real files and then rendering the platform-owned subset into draft ExecPlan candidate artifacts while keeping authoritative governed state unchanged.

## Plan of Work

Add façade commands that read projected follow-up packets, write materialized platform seed files and external repo request packets, then render the platform seed files into draft markdown and JSON ExecPlan candidate artifacts.

## Validation and Acceptance

This slice is accepted when `materialize-research-followup-assets` and `render-platform-execplan-drafts` both return `ok` envelopes for valid inputs, write stable asset artifacts, and the public command contracts plus focused tests cover both phases.

## Artifacts and Notes

This slice intentionally stops at non-authoritative asset generation. It does not create canonical `.agent/execplans/*` files or activate new governed work automatically.
