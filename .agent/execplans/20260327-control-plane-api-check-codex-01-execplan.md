---
id: "20260327-control-plane-api-check-codex-01-execplan"
title: "Validate control-plane composite commands against their versioned schema"
owner: "agent/codex-01"
created: "2026-03-27T05:34:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-control-plane-api-check-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/queued-execplans.md
  - pyproject.toml
  - src/platform_tools/control_plane_api_check.py
  - tests/test_control_plane_api_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-049"
  queue_position: 49
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-control-plane-api-check-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-control-plane-api-check-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "src/platform_tools/control_plane_api_check.py"
    - "tests/test_control_plane_api_check.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-control-plane-api-check-codex-01-20260327"
draft_created: "2026-03-27T05:34:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "control plane api check tests"
      command: "uv run pytest -q tests/test_control_plane_api_check.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-control-plane-api-check-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-control-plane-api-check-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Add a schema validator for get-control-plane-status and get-next-orchestration-action"
    priority: "P1"
  - title: "Keep the checker thin and contract-driven like the public orchestration API checker"
    priority: "P1"
depends_on:
  - "20260327-control-plane-composite-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Add a deterministic checker for the composite control-plane API so regressions in the terminal operator surface are caught the same way regressions in the public orchestration facade are caught.

## Progress

- [ ] implement `control-plane-api-check`
- [ ] add focused schema-check tests
- [ ] register the slice in graph and queue state

## Plan of Work

1. reuse the schema-check pattern from `public_orchestration_api_check.py`
2. validate `get-control-plane-status` and `get-next-orchestration-action`
3. add focused tests
4. validate and register the slice

## Surprises & Discoveries

- the control-plane schema is compact enough that a thin checker can validate it without pulling in a second schema runtime

## Decision Log

- keep the checker schema-driven and limited to the composite control-plane commands

## Outcomes & Retrospective

- expected outcome: a regression check that keeps the terminal control-plane contract stable

## Context and Orientation

- the composite control-plane commands are now part of the initiative; this slice adds the matching contract checker

## Concrete Steps

1. add `src/platform_tools/control_plane_api_check.py`
2. add `tests/test_control_plane_api_check.py`
3. update command registration

## Validation and Acceptance

- `uv run pytest -q tests/test_control_plane_api_check.py`
- `bin/execplan-validate .agent/execplans/20260327-control-plane-api-check-codex-01-execplan.md`
- `bin/remaining-work-graph-check`

## Idempotence and Recovery

- the checker is read-only and should fail closed on schema drift

## Artifacts and Notes

- this is a checker slice only; it does not widen the control-plane runtime surface

## Interfaces and Dependencies

- depends on `spec/control-plane-api.schema.yaml` and the two composite commands already merged into the initiative
