---
id: "20260327-managed-repo-control-plane-codex-01-execplan"
title: "Make the composite control-plane commands explicitly managed-repo aware"
owner: "agent/codex-01"
created: "2026-03-27T05:46:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-managed-repo-control-plane-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/control-plane-api.md
  - docs/queued-execplans.md
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
  node_id: "rwg-050"
  queue_position: 50
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-managed-repo-control-plane-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-managed-repo-control-plane-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/control-plane-api.md"
    - "docs/queued-execplans.md"
    - "spec/control-plane-api.schema.yaml"
    - "src/platform_tools/control_plane.py"
    - "src/platform_tools/get_control_plane_status.py"
    - "src/platform_tools/get_next_orchestration_action.py"
    - "tests/test_control_plane_api.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-managed-repo-control-plane-codex-01-20260327"
draft_created: "2026-03-27T05:46:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "control plane api tests"
      command: "uv run pytest -q tests/test_control_plane_api.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-managed-repo-control-plane-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-managed-repo-control-plane-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Add repo_root targeting to the composite control-plane commands"
    priority: "P1"
  - title: "Use managed-repo status when the control plane is pointed at an external repo"
    priority: "P1"
  - title: "Keep the managed-repo control-plane layer thin and subordinate to the existing managed-repo and local-runtime contracts"
    priority: "P1"
depends_on:
  - "20260327-control-plane-composite-runtime-codex-01-execplan"
  - "20260319-managed-repo-orchestration-codex-01-execplan"
---

# Purpose / Big Picture

Extend the composite control-plane commands so they can reason about an explicitly targeted managed repo instead of only the current local repo. The control plane should stay terminal-first and deterministic, but it needs one level of managed-repo awareness to orchestrate other repositories cleanly.

## Progress

- [ ] add `repo_root` targeting to the composite control-plane commands
- [ ] integrate `managed-repo-status` into control-plane status and next-action logic
- [ ] validate the managed-repo-aware projections with focused tests
- [ ] register the slice in graph and queue state

## Surprises & Discoveries

- the lower layers already have explicit target-repo semantics; the composite layer was the remaining assumption-heavy surface

## Decision Log

- managed repos should remain canonical for their own state, and the composite layer should inspect them by explicit root targeting only

## Outcomes & Retrospective

- expected outcome: the terminal control-plane commands can summarize and route work for a managed repo without centralizing that repo’s state into this repository

## Context and Orientation

- local runtime, merge-back, and the composite control plane are already in place for the current repo
- the next practical step is to make those composite commands operate over explicit managed-repo roots too

## Plan of Work

1. add `repo_root` targeting to the control-plane functions and CLI wrappers
2. integrate `managed-repo-status` into control-plane status and next-action logic
3. adjust the schema/doc contract where needed
4. update tests and validate

## Concrete Steps

1. update `src/platform_tools/control_plane.py`
2. update `src/platform_tools/get_control_plane_status.py`
3. update `src/platform_tools/get_next_orchestration_action.py`
4. update `spec/control-plane-api.schema.yaml` and `docs/control-plane-api.md`
5. extend `tests/test_control_plane_api.py`

## Validation and Acceptance

- `uv run pytest -q tests/test_control_plane_api.py`
- `bin/execplan-validate .agent/execplans/20260327-managed-repo-control-plane-codex-01-execplan.md`
- `bin/remaining-work-graph-check`

## Idempotence and Recovery

- managed-repo control-plane inspection should be read-only and fail closed when the target repo is missing or ambiguous

## Artifacts and Notes

- this slice extends the composite control-plane projection only; it does not move canonical planning state out of the target repo

## Interfaces and Dependencies

- depends on `managed_repo_status.py`, `control_plane.py`, and the existing local runtime and merge-back command surfaces
