---
id: "20260507-external-handoff-and-loop-runner-codex-01-execplan"
title: "Render external researcher handoffs and run the supervised research improvement loop"
owner: "agent/codex-01"
created: "2026-05-08T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260507-external-handoff-and-loop-runner-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/render-researcher-followup-handoffs"
  - "bin/run-research-improvement-loop"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/platform-researcher-interface.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/render_researcher_followup_handoffs.py"
  - "src/platform_tools/run_research_improvement_loop.py"
  - "tests/test_render_researcher_followup_handoffs.py"
  - "tests/test_run_research_improvement_loop.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-065"
  queue_position: 65
  implementation_branch: "impl-execplan/20260507-external-handoff-and-loop-runner-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-external-handoff-and-loop-runner-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/render-researcher-followup-handoffs"
    - "bin/run-research-improvement-loop"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/render_researcher_followup_handoffs.py"
    - "src/platform_tools/run_research_improvement_loop.py"
    - "tests/test_render_researcher_followup_handoffs.py"
    - "tests/test_run_research_improvement_loop.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-external-handoff-and-loop-runner-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-external-handoff-and-loop-runner-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_render_researcher_followup_handoffs.py tests/test_run_research_improvement_loop.py"
      expected_exit: 0
tasks:
  - title: "Render researcher-harness request packets from materialized external follow-up assets"
    priority: "P1"
  - title: "Add a composite façade command that runs the supervised research loop end to end"
    priority: "P1"
  - title: "Extend the public command contract and focused tests for the first full loop runner"
    priority: "P1"
depends_on:
  - "20260507-platform-seed-draft-rendering-codex-01-execplan"
---

## Outcomes & Retrospective

Projected external repo packets should become execution-ready researcher requests, and the platform should be able to run the whole supervised loop in one bounded command.

## Context and Orientation

The platform can already run research, rank candidates, prepare follow-ups, split them into repo packets, materialize tangible assets, and render platform draft ExecPlan candidates. This slice closes the next practical gap by turning researcher-harness packets into runnable handoff requests and composing the full chain into one supervised loop command.

## Plan of Work

Add a researcher-harness handoff renderer and a composite command that runs the full research-improvement loop through draft platform assets and external handoff requests.

## Validation and Acceptance

This slice is accepted when the new renderer and composite runner both return `ok` envelopes for valid bounded inputs, write stable artifacts, and focused tests plus public contract documentation cover the new surfaces.

## Artifacts and Notes

This slice still stops short of mutating external repos automatically. It produces supervised, reviewable handoff assets and one end-to-end loop manifest.
