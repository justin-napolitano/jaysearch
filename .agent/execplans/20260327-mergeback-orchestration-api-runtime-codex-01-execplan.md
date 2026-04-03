---
id: "20260327-mergeback-orchestration-api-runtime-codex-01-execplan"
title: "Implement merge-back orchestration commands for readiness and PR target resolution"
owner: "agent/codex-01"
created: "2026-03-27T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-mergeback-orchestration-api-runtime-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/queued-execplans.md
  - pyproject.toml
  - src/platform_tools/get_merge_readiness.py
  - src/platform_tools/get_pr_integration_contract.py
  - src/platform_tools/mergeback_orchestration.py
  - tests/test_mergeback_orchestration_api.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-046"
  queue_position: 46
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-mergeback-orchestration-api-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-mergeback-orchestration-api-runtime-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "src/platform_tools/get_merge_readiness.py"
    - "src/platform_tools/get_pr_integration_contract.py"
    - "src/platform_tools/mergeback_orchestration.py"
    - "tests/test_mergeback_orchestration_api.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-mergeback-orchestration-api-runtime-codex-01-20260327"
draft_created: "2026-03-27T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "mergeback orchestration api tests"
      command: "uv run pytest -q tests/test_mergeback_orchestration_api.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-mergeback-orchestration-api-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-mergeback-orchestration-api-runtime-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Implement get-merge-readiness as a compact merge-back projection over existing readiness and workflow authority surfaces"
    priority: "P1"
  - title: "Implement get-pr-integration-contract as a deterministic initiative-target resolution command for implementation slices"
    priority: "P1"
  - title: "Keep merge-back orchestration commands thin and subordinate to existing merge-readiness and branch-policy logic"
    priority: "P1"
depends_on:
  - "20260326-mergeback-orchestration-api-contract-codex-01-execplan"
  - "20260326-worker-orchestration-api-codex-01-execplan"
  - "20260326-initiative-branch-plan-authority-correction-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first live merge-back orchestration commands so a thin local orchestrator can determine whether an implementation slice is ready to merge back into its parent initiative branch and where that PR should target. This turns the contract-only merge-back planning work into repo-owned command surfaces.

## Progress

- [ ] implement `get-merge-readiness`
- [ ] implement `get-pr-integration-contract`
- [ ] add focused tests for initiative-target resolution and readiness projection
- [ ] register the live runtime slice in graph and queue state

## Surprises & Discoveries

- existing branch-policy and merge-readiness modules already contain most of the authority logic needed for the new commands
- the right implementation is a thin adapter over those existing surfaces, not a second merge engine

## Decision Log

- the live commands should stay compact and deterministic
- target resolution should fail closed when the implementation branch cannot be mapped to one initiative target
- merge-back commands should reuse the recent contract vocabularies instead of inventing ad hoc strings

## Outcomes & Retrospective

- expected outcome: two merge-back orchestration commands that make PR target selection and merge readiness machine-readable for terminal-based orchestration

## Context and Orientation

- the public orchestration facade already covers graph state and worker execution
- the missing control-plane step is deterministic PR merge-back guidance for implementation branches

## Plan of Work

1. add shared merge-back resolution helpers
2. implement the two command modules and CLI entrypoints
3. update command reference surfaces
4. add focused tests
5. validate the slice

## Concrete Steps

1. add `src/platform_tools/mergeback_orchestration.py`
2. add `src/platform_tools/get_merge_readiness.py`
3. add `src/platform_tools/get_pr_integration_contract.py`
4. update `pyproject.toml` command entrypoints and `docs/commands.md`
5. add `tests/test_mergeback_orchestration_api.py`

## Validation and Acceptance

- `uv run pytest -q tests/test_mergeback_orchestration_api.py`
- `bin/execplan-validate .agent/execplans/20260327-mergeback-orchestration-api-runtime-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the commands must resolve initiative targets and readiness without relying on prose interpretation

## Idempotence and Recovery

- repeated command runs should project current state without mutating canonical state
- ambiguous graph or branch mapping should block rather than guess

## Artifacts and Notes

- this slice implements the contract from `20260326-mergeback-orchestration-api-contract-codex-01-execplan`

## Interfaces and Dependencies

- depends on `merge_readiness.py` for underlying readiness checks
- depends on branch-policy and remaining-work graph metadata for target resolution
