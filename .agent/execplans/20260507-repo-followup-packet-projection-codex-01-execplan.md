---
id: "20260507-repo-followup-packet-projection-codex-01-execplan"
title: "Project repo-specific follow-up packets from prepared research follow-ups"
owner: "agent/codex-01"
created: "2026-05-07T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260507-repo-followup-packet-projection-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/project-research-followup-packets"
  - "docs/commands.md"
  - "docs/public-orchestration-api.md"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/platform-researcher-interface.md"
  - "spec/public-orchestration-api.schema.yaml"
  - "src/platform_tools/project_research_followup_packets.py"
  - "tests/test_project_research_followup_packets.py"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-063"
  queue_position: 63
  implementation_branch: "impl-execplan/20260507-repo-followup-packet-projection-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "capability-contracts"
    - "research-runtime"
  expected_artifacts:
    - ".agent/execplans/20260507-repo-followup-packet-projection-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/project-research-followup-packets"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/project_research_followup_packets.py"
    - "tests/test_project_research_followup_packets.py"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260507-repo-followup-packet-projection-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260507-repo-followup-packet-projection-codex-01-execplan.md"
      expected_exit: 0
    - name: "pytest"
      command: "uv run pytest tests/test_project_research_followup_packets.py"
      expected_exit: 0
tasks:
  - title: "Add a facade command that converts prepared research follow-up inputs into repo-specific packet outputs"
    priority: "P1"
  - title: "Emit platform ExecPlan seed packets and external repo follow-up request packets from one deterministic artifact"
    priority: "P1"
  - title: "Extend public API docs, schema, and focused tests for repo packet projection"
    priority: "P1"
depends_on:
  - "20260507-ranked-candidate-followup-preparation-codex-01-execplan"
---

## Outcomes & Retrospective

Prepared research follow-ups should split cleanly into repo-specific packets so supervising Codex sessions can route platform-owned work into draft ExecPlan seed material and external repo work into bounded request packets.

## Context and Orientation

The platform can now produce a deterministic neutral follow-up package from promotable ranked candidates. The next control-plane step is to separate that package by target repo without recomputing the ranking gate or mutating any repo automatically.

## Plan of Work

Add a façade command that reads a prepared follow-ups artifact, emits platform ExecPlan seed packets for `codex_platform`, emits external repo follow-up request packets for non-platform targets, and returns the packet sets through the public orchestration envelope.

## Validation and Acceptance

This slice is accepted when `project-research-followup-packets` returns an `ok` envelope for valid prepared follow-up artifacts, writes a stable packets artifact, and the public contract plus focused tests cover both platform and external repo packet projections.

## Artifacts and Notes

This slice intentionally stops at packet projection. It does not create draft branches, open PRs, or auto-write ExecPlan markdown from the projected packets.
