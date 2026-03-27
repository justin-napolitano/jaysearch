---
id: "20260327-orchestrate-governed-slice-api-check-codex-01-execplan"
title: "Add a schema and checker for orchestrate-governed-slice"
owner: "agent/codex-01"
created: "2026-03-27T05:40:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-orchestrate-governed-slice-api-check-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/orchestrate-governed-slice-api.md
  - docs/queued-execplans.md
  - pyproject.toml
  - spec/orchestrate-governed-slice-api.schema.yaml
  - src/platform_tools/orchestrate_governed_slice_api_check.py
  - tests/test_orchestrate_governed_slice_api_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-052"
  queue_position: 52
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-orchestrate-governed-slice-api-check-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-orchestrate-governed-slice-api-check-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/orchestrate-governed-slice-api.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "spec/orchestrate-governed-slice-api.schema.yaml"
    - "src/platform_tools/orchestrate_governed_slice_api_check.py"
    - "tests/test_orchestrate_governed_slice_api_check.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-orchestrate-governed-slice-api-check-codex-01-20260327"
draft_created: "2026-03-27T05:40:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "orchestrate governed slice api check tests"
      command: "uv run pytest -q tests/test_orchestrate_governed_slice_api_check.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-api-check-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-orchestrate-governed-slice-api-check-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Define a versioned response schema for orchestrate-governed-slice"
    priority: "P1"
  - title: "Add a checker command so the top-level control-loop entrypoint is contract-validated"
    priority: "P1"
  - title: "Document the orchestrate-governed-slice output contract in the terminal command catalog"
    priority: "P1"
depends_on:
  - "20260327-orchestrate-governed-slice-control-plane-codex-01-execplan"
---

# Purpose / Big Picture

`orchestrate-governed-slice` is now the documented terminal control-loop entrypoint over the new control-plane APIs, but it still lacks its own versioned schema and compatibility checker. This slice adds that contract layer so the top-level entrypoint is machine-validated like the underlying APIs it composes.

## Progress

- [ ] register the slice in graph and queue state
- [ ] add a versioned schema for orchestrate-governed-slice responses
- [ ] add an API checker command and focused tests
- [ ] wire the checker into the packaged command catalog and docs

## Surprises & Discoveries

- the top-level terminal control-loop entrypoint was the remaining high-level API surface without its own compatibility check

## Decision Log

- the entrypoint should remain a thin wrapper, but its response envelope still needs its own contract because it is now a stable operator-facing command

## Outcomes & Retrospective

- expected outcome: the terminal orchestration entrypoint can be validated deterministically and will fail fast if later changes break its bounded output shape

## Context and Orientation

- the initiative now has versioned schemas and checkers for merge-back and control-plane APIs
- this slice extends the same contract discipline to the top-level orchestration entrypoint

## Plan of Work

1. add `spec/orchestrate-governed-slice-api.schema.yaml`
2. add `src/platform_tools/orchestrate_governed_slice_api_check.py`
3. add focused tests and command/doc wiring

## Concrete Steps

1. update `pyproject.toml` and `docs/commands.md`
2. add the schema and support doc
3. add the checker and tests

## Validation and Acceptance

- `uv run pytest -q tests/test_orchestrate_governed_slice_api_check.py`
- `bin/execplan-validate .agent/execplans/20260327-orchestrate-governed-slice-api-check-codex-01-execplan.md`
- `bin/remaining-work-graph-check`

## Idempotence and Recovery

- the checker should be read-only and should block cleanly on missing schema, invalid envelope fields, or missing required top-level orchestration projections

## Artifacts and Notes

- this slice does not widen orchestration behavior; it only hardens the contract around the existing entrypoint

## Interfaces and Dependencies

- depends on `orchestrate_governed_slice.py` and the control-plane APIs it already composes
