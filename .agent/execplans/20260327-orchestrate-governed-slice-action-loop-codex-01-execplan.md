---
id: "20260327-orchestrate-governed-slice-action-loop-codex-01-execplan"
title: "Teach orchestrate-governed-slice to execute one bounded next step"
owner: "agent/codex-01"
created: "2026-03-27T06:10:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-orchestrate-governed-slice-action-loop-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/orchestrate-governed-slice-api.md
  - docs/queued-execplans.md
  - spec/orchestrate-governed-slice-api.schema.yaml
  - src/platform_tools/orchestrate_governed_slice.py
  - tests/test_orchestrate_governed_slice.py
  - tests/test_orchestrate_governed_slice_api_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-053"
  queue_position: 53
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-orchestrate-governed-slice-action-loop-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-orchestrate-governed-slice-action-loop-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/orchestrate-governed-slice-api.md"
    - "docs/queued-execplans.md"
    - "spec/orchestrate-governed-slice-api.schema.yaml"
    - "src/platform_tools/orchestrate_governed_slice.py"
    - "tests/test_orchestrate_governed_slice.py"
    - "tests/test_orchestrate_governed_slice_api_check.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-orchestrate-governed-slice-action-loop-codex-01-20260327"
draft_created: "2026-03-27T06:10:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "orchestrate governed slice tests"
      command: "uv run pytest -q tests/test_orchestrate_governed_slice.py tests/test_orchestrate_governed_slice_api_check.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-action-loop-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-orchestrate-governed-slice-action-loop-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Add an explicit execute mode to orchestrate-governed-slice"
    priority: "P1"
  - title: "Route task-bearing calls through local-task-router and start-next-worker when the route resolves to bounded execution"
    priority: "P1"
  - title: "Execute recommended merge-back or branch-preparation API calls when no explicit task is provided"
    priority: "P1"
depends_on:
  - "20260327-orchestrate-governed-slice-control-plane-codex-01-execplan"
  - "20260327-orchestrate-governed-slice-api-check-codex-01-execplan"
---

# Purpose / Big Picture

The initiative already has a deterministic control plane, but the top-level terminal entrypoint still stops at recommendation. This slice keeps `orchestrate-governed-slice` thin while teaching it to execute one bounded next step through the existing APIs when the operator opts in with explicit execute mode.

## Progress

- [ ] register the slice in graph and queue state
- [ ] add execute mode to `orchestrate-governed-slice`
- [ ] route explicit tasks through `local-task-router` and worker dispatch when safe
- [ ] update tests and response contract for the execution projection

## Decision Log

- execute mode remains opt-in; project-only behavior stays the default
- the entrypoint may call existing bounded APIs, but it must not invent direct side effects outside those APIs

## Plan of Work

1. register the slice
2. add execution projection to the orchestrate-governed-slice response
3. map execute mode to bounded existing commands
4. validate through focused tests

## Surprises & Discoveries

- the top-level entrypoint already had the right control-plane posture after the previous slice, so the remaining gap was execution wiring rather than more status projection
- the cleanest way to keep this thin is to execute one bounded next step only, not to add a long-running loop inside the command

## Outcomes & Retrospective

- expected outcome: the terminal entrypoint can now either project the next step or execute exactly one governed step through the existing API surfaces

## Context and Orientation

- this initiative already has local runtime checks, task routing, merge-back APIs, branch-preparation APIs, worker execution facades, and control-plane status/next-action projections
- the last practical gap is turning those projections into one bounded executable turn without reintroducing prompt-only orchestration

## Concrete Steps

1. update `src/platform_tools/orchestrate_governed_slice.py`
2. update `spec/orchestrate-governed-slice-api.schema.yaml`
3. update `docs/orchestrate-governed-slice-api.md`
4. extend `tests/test_orchestrate_governed_slice.py`
5. extend `tests/test_orchestrate_governed-slice_api_check.py`

## Validation and Acceptance

- `uv run pytest -q tests/test_orchestrate_governed_slice.py tests/test_orchestrate_governed_slice_api_check.py`
- `bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-action-loop-codex-01-execplan.md`
- `bin/remaining-work-graph-check`

## Idempotence and Recovery

- project-only mode remains side-effect free
- execute mode runs at most one bounded command path and returns its result directly
- if the control plane is blocked or the recommended action is not safely executable, the command must fail closed rather than improvise

## Artifacts and Notes

- this slice intentionally reuses existing commands such as `local-task-router`, `start-next-worker`, `prepare-next-impl-branch`, and merge-back projections
- it does not add a new orchestration backend or secondary authority surface

## Interfaces and Dependencies

- depends on `control_plane.py`, `local_runtime/router.py`, `start_next_worker.py`, and `mergeback_orchestration.py`
