---
id: "20260327-control-plane-composite-runtime-codex-01-execplan"
title: "Implement composite control-plane status and next-action commands for terminal orchestration"
owner: "agent/codex-01"
created: "2026-03-27T05:20:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-control-plane-composite-runtime-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/control-plane-api.md
  - docs/queued-execplans.md
  - pyproject.toml
  - spec/control-plane-api.schema.yaml
  - src/platform_tools/control_plane.py
  - src/platform_tools/get_control_plane_status.py
  - src/platform_tools/get_next_orchestration_action.py
  - tests/test_control_plane_api.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-048"
  queue_position: 48
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-control-plane-composite-runtime-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-control-plane-composite-runtime-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/control-plane-api.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "spec/control-plane-api.schema.yaml"
    - "src/platform_tools/control_plane.py"
    - "src/platform_tools/get_control_plane_status.py"
    - "src/platform_tools/get_next_orchestration_action.py"
    - "tests/test_control_plane_api.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-control-plane-composite-runtime-codex-01-20260327"
draft_created: "2026-03-27T05:20:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "control plane api tests"
      command: "uv run pytest -q tests/test_control_plane_api.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-control-plane-composite-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-control-plane-composite-runtime-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Implement get-control-plane-status as a compact operator-facing summary over graph, runtime, worker, and mergeback surfaces"
    priority: "P1"
  - title: "Implement get-next-orchestration-action as a deterministic next-step projection for initiative and implementation branches"
    priority: "P1"
  - title: "Keep the composite control-plane layer thin and subordinate to existing repo-owned command surfaces"
    priority: "P1"
depends_on:
  - "20260327-implementation-branch-ancestry-enforcement-codex-01-execplan"
  - "20260327-mergeback-orchestration-api-runtime-codex-01-execplan"
  - "20260326-local-offline-orchestration-bootstrap-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first composite terminal control-plane layer so a thin local orchestrator can inspect current repo state and decide the next bounded action without re-reading multiple command surfaces manually. This is a projection layer only; canonical authority remains in the underlying commands and specs.

## Progress

- [ ] implement `get-control-plane-status`
- [ ] implement `get-next-orchestration-action`
- [ ] add a versioned control-plane schema and focused tests
- [ ] register the slice in graph and queue state

## Surprises & Discoveries

- the necessary authority surfaces are already present; the missing layer is composition, not more core governance machinery
- keeping the output compact matters because the terminal is the operator interface and a local model should not need the full raw payload of every underlying command on each step

## Decision Log

- this layer should summarize existing command outputs rather than duplicate raw payloads
- initiative branches and implementation branches need different next-action logic, but both should come from one versioned control-plane surface
- the composite commands should fail closed and surface blockers from the underlying commands instead of guessing

## Outcomes & Retrospective

- expected outcome: one status command and one next-action command that let a terminal-based orchestrator navigate the repo without prose interpretation

## Context and Orientation

- graph state, worker execution, local runtime, merge-back, and implementation ancestry are now encoded as deterministic commands
- what is still missing is one thin layer that says “where are we now?” and “what do we do next?”

## Plan of Work

1. define a small control-plane schema for status and next action
2. implement shared composition helpers
3. add the two commands and focused tests
4. validate and register the slice

## Concrete Steps

1. add `spec/control-plane-api.schema.yaml`
2. add `docs/control-plane-api.md`
3. add `src/platform_tools/control_plane.py`
4. add `src/platform_tools/get_control_plane_status.py`
5. add `src/platform_tools/get_next_orchestration_action.py`
6. update `pyproject.toml` and `docs/commands.md`
7. add `tests/test_control_plane_api.py`

## Validation and Acceptance

- `uv run pytest -q tests/test_control_plane_api.py`
- `bin/execplan-validate .agent/execplans/20260327-control-plane-composite-runtime-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the composite commands must determine current state and next bounded action from repo-owned APIs without requiring prose interpretation

## Idempotence and Recovery

- repeated runs should be read-only projections
- if one underlying command blocks, the composite layer should expose that blocker rather than override it

## Artifacts and Notes

- this slice implements the terminal control-plane projection, not a new authority layer or UI

## Interfaces and Dependencies

- depends on graph, worker, local runtime, merge-back, and branch-preparation commands already present in the initiative
