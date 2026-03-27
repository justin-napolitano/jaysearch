---
id: "20260327-orchestrate-governed-slice-control-plane-codex-01-execplan"
title: "Make orchestrate-governed-slice compose the control-plane APIs"
owner: "agent/codex-01"
created: "2026-03-27T05:35:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-orchestrate-governed-slice-control-plane-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/queued-execplans.md
  - pyproject.toml
  - src/platform_tools/orchestrate_governed_slice.py
  - tests/test_orchestrate_governed_slice.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-051"
  queue_position: 51
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-orchestrate-governed-slice-control-plane-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-orchestrate-governed-slice-control-plane-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "src/platform_tools/orchestrate_governed_slice.py"
    - "tests/test_orchestrate_governed_slice.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-orchestrate-governed-slice-control-plane-codex-01-20260327"
draft_created: "2026-03-27T05:35:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "orchestrate governed slice tests"
      command: "uv run pytest -q tests/test_orchestrate_governed_slice.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-control-plane-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-orchestrate-governed-slice-control-plane-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Make orchestrate-governed-slice consume the composite control-plane commands instead of older status projections"
    priority: "P1"
  - title: "Preserve managed-repo behavior while routing through the control-plane layer"
    priority: "P1"
  - title: "Wire the command into the script entrypoint catalog so the terminal command surface matches the documented contract"
    priority: "P1"
depends_on:
  - "20260327-control-plane-composite-runtime-codex-01-execplan"
  - "20260327-control-plane-api-check-codex-01-execplan"
  - "20260327-managed-repo-control-plane-codex-01-execplan"
---

# Purpose / Big Picture

Make `orchestrate-governed-slice` the real terminal control-loop entrypoint for this initiative by composing the newer control-plane APIs instead of older orchestration/status surfaces. The command should stay deterministic and thin, but it should now route through the same bounded machine-readable status and next-action contracts that the local orchestrator uses elsewhere.

## Progress

- [ ] register the slice in graph and queue state
- [ ] refactor `orchestrate-governed-slice` to consume the composite control-plane commands
- [ ] preserve managed-repo targeting semantics through explicit `repo_root` handling
- [ ] validate the updated control-loop behavior with focused tests

## Surprises & Discoveries

- `orchestrate-governed-slice` is documented as the local control-loop entrypoint already, but it still composes older surfaces directly instead of the new control-plane layer
- the script is present under `bin/`, but the packaged script entrypoint catalog does not currently expose it in `pyproject.toml`

## Decision Log

- `orchestrate-governed-slice` should become a thin orchestrator over `get-control-plane-status`, `get-next-orchestration-action`, and the managed-repo/readiness primitives they already compose
- this slice should not invent a second control-loop contract; it should reuse the one already built

## Outcomes & Retrospective

- expected outcome: the documented local control-loop entrypoint finally aligns with the actual control-plane contracts and can drive both self-hosted and managed repos deterministically

## Context and Orientation

- the initiative now has deterministic APIs for graph state, worker status, local runtime checks, merge-back readiness, branch preparation, and composite control-plane status/next-step selection
- the remaining gap is the top-level orchestration entrypoint, which still reflects an older orchestration/status model

## Plan of Work

1. refactor `src/platform_tools/orchestrate_governed_slice.py` to use the composite control-plane functions
2. preserve explicit managed-repo support without bypassing the control-plane contract
3. align tests with the new orchestration flow
4. add the script entrypoint to `pyproject.toml` so the documented command surface is packaged deterministically

## Concrete Steps

1. update `src/platform_tools/orchestrate_governed_slice.py`
2. update `tests/test_orchestrate_governed_slice.py`
3. update `pyproject.toml` and `docs/commands.md`

## Validation and Acceptance

- `uv run pytest -q tests/test_orchestrate_governed_slice.py`
- `bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-control-plane-codex-01-execplan.md`
- `bin/remaining-work-graph-check`

## Idempotence and Recovery

- the refactor should stay read-only with respect to repo state and fail closed when the active control-plane status or next action is blocked or ambiguous
- managed-repo targeting should continue to work through explicit root selection rather than hidden context

## Artifacts and Notes

- this slice is about orchestration composition, not about widening the underlying control-plane schemas again

## Interfaces and Dependencies

- depends on `control_plane.py`, `managed_repo_status.py`, and the existing merge-back and local-runtime control-plane surfaces already present in the initiative
