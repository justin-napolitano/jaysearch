---
id: "20260511-supervised-loop-smoke-run-codex-01-execplan"
title: "Add a live supervised research loop smoke test"
owner: "agent/codex-01"
created: "2026-05-11T00:00:00Z"
status: draft
base_branch: "main"
initiative_branch: "initiative/research-control-plane"
initiative_node_id: "initiative-research-control-plane"
changes:
  - ".agent/execplans/20260511-supervised-loop-smoke-run-codex-01-execplan.md"
  - "artifacts/governance/board-action-events.jsonl"
  - "artifacts/planner/research/remaining-work-graph.json"
  - "bin/run-research-improvement-loop-smoke-test"
  - "docs/commands.md"
  - "docs/queued-execplans.md"
  - "docs/system-architecture/platform-researcher-interface.md"
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
graph_registration:
  node_id: "rwg-066"
  queue_position: 66
  implementation_branch: "impl-execplan/20260511-supervised-loop-smoke-run-codex-01"
  goal_area: "governance"
  conflict_domains:
    - "governance"
    - "orchestration"
    - "research-runtime"
    - "smoke-test"
  expected_artifacts:
    - ".agent/execplans/20260511-supervised-loop-smoke-run-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "bin/run-research-improvement-loop-smoke-test"
    - "docs/commands.md"
    - "docs/queued-execplans.md"
    - "docs/system-architecture/platform-researcher-interface.md"
  integration_mode: "via_initiative"
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260511-supervised-loop-smoke-run-codex-01-execplan.md"
      expected_exit: 0
    - name: "policy-compliance"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260511-supervised-loop-smoke-run-codex-01-execplan.md"
      expected_exit: 0
    - name: "supervised-loop-smoke-test"
      command: "bin/run-research-improvement-loop-smoke-test"
      expected_exit: 0
tasks:
  - title: "Add a live smoke test that runs the platform research loop against the real researcher-harness repo"
    priority: "P1"
  - title: "Validate the first external handoff round-trip through researcher-harness"
    priority: "P1"
  - title: "Document the smoke path as the first operational end-to-end supervised loop"
    priority: "P1"
depends_on:
  - "20260507-external-handoff-and-loop-runner-codex-01-execplan"
---

## Outcomes & Retrospective

The control plane should have a repeatable operator smoke path that exercises the full supervised loop against the real external researcher runtime and validates one returned handoff request.

## Context and Orientation

The platform can now render platform draft ExecPlan candidates and external researcher handoff requests. This slice turns that architecture into a concrete operational proof by adding a live smoke test that runs the bounded loop and then runs one returned handoff request back through `researcher-harness`.

## Plan of Work

Add a smoke test entrypoint that synthesizes a bounded request, runs the full platform loop against the live sibling `researcher-harness` repo, validates the produced draft and handoff artifacts, and then runs one generated handoff request through the external researcher runtime.

## Validation and Acceptance

This slice is accepted when the smoke test returns zero, proves the end-to-end loop writes reviewable platform artifacts, and proves at least one external handoff request can be executed successfully through `researcher-harness`.

## Artifacts and Notes

This slice intentionally keeps the loop supervised and local. It does not auto-apply any generated follow-up to either repo.
