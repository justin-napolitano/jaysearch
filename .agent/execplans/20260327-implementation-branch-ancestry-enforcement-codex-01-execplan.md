---
id: "20260327-implementation-branch-ancestry-enforcement-codex-01-execplan"
title: "Enforce implementation branch ancestry and merge-back completion before new slices start"
owner: "agent/codex-01"
created: "2026-03-27T04:56:24Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260327-implementation-branch-ancestry-enforcement-codex-01-execplan.md
  - artifacts/governance/board-action-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/mergeback-orchestration-api.md
  - docs/queued-execplans.md
  - pyproject.toml
  - spec/mergeback-orchestration-api.schema.yaml
  - src/platform_tools/get_merge_readiness.py
  - src/platform_tools/mergeback_orchestration.py
  - src/platform_tools/prepare_next_impl_branch.py
  - src/platform_tools/policy_compliance_check.py
  - tests/test_mergeback_orchestration_api.py
  - tests/test_prepare_next_impl_branch.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-047"
  queue_position: 47
  goal_area: "orchestrator-runtime"
  implementation_branch: "impl-execplan/20260327-implementation-ancestry-enforcement-codex-01"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260327-implementation-branch-ancestry-enforcement-codex-01-execplan.md"
    - "artifacts/governance/board-action-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/mergeback-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "spec/mergeback-orchestration-api.schema.yaml"
    - "src/platform_tools/mergeback_orchestration.py"
    - "src/platform_tools/prepare_next_impl_branch.py"
    - "src/platform_tools/policy_compliance_check.py"
    - "tests/test_mergeback_orchestration_api.py"
    - "tests/test_prepare_next_impl_branch.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260327-implementation-branch-ancestry-enforcement-codex-01-20260327"
draft_created: "2026-03-27T04:56:24Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "mergeback orchestration api tests"
      command: "uv run pytest -q tests/test_mergeback_orchestration_api.py tests/test_prepare_next_impl_branch.py"
      expected_exit: 0
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260327-implementation-branch-ancestry-enforcement-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260327-implementation-branch-ancestry-enforcement-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Block merge-back when an implementation branch no longer descends from the current initiative head"
    priority: "P1"
  - title: "Add a deterministic prepare-next-impl-branch command that refuses to cut a new slice while older implementation work remains unmerged"
    priority: "P1"
  - title: "Expose the new ancestry and unresolved-prior-slice blockers through bounded API vocabularies"
    priority: "P1"
depends_on:
  - "20260327-mergeback-orchestration-api-runtime-codex-01-execplan"
  - "20260326-initiative-branch-plan-authority-correction-codex-01-execplan"
---

# Purpose / Big Picture

Make it impossible for the orchestrator to silently recreate the stale-implementation-branch failure mode. Implementation slices must be cut from the current initiative head, and merge-back must fail closed once the initiative has advanced beyond that slice.

## Progress

- [ ] extend the merge-back orchestration surface with ancestry-aware blockers
- [ ] implement `prepare-next-impl-branch`
- [ ] add focused tests for stale ancestry and unresolved prior implementation slices
- [ ] register the slice in graph and queue state

## Surprises & Discoveries

- the current merge-back surface already resolves lawful initiative targets, but it does not yet prove the implementation branch still contains the current initiative head
- the missing guardrail is not more prose; it is one ancestry check at merge time and one ancestry/unmerged-slice gate before the next implementation branch is cut

## Decision Log

- the new branch-preparation surface should be deterministic and read-only; it should return the lawful next branch and blockers, not create the branch itself
- merge-back should report stale ancestry through bounded blocker and problem vocabularies
- unresolved prior implementation slices should block the next implementation branch rather than rely on operator memory

## Outcomes & Retrospective

- expected outcome: the orchestrator can no longer start the next implementation slice or merge an old slice without machine-readable ancestry validation

## Context and Orientation

- the local runtime and merge-back APIs now exist, but the repo still allowed one implementation slice to drift behind the initiative branch until it needed a manual restack
- this slice closes that governance gap directly in the API and policy layer

## Plan of Work

1. extend the merge-back schema and runtime with ancestry-aware blockers and actions
2. add a deterministic `prepare-next-impl-branch` command for initiative-based slicing
3. enforce the same rule in policy compliance where branch ancestry can be checked deterministically
4. add focused tests and validate the slice

## Concrete Steps

1. update `spec/mergeback-orchestration-api.schema.yaml`
2. update `src/platform_tools/mergeback_orchestration.py`
3. add `src/platform_tools/prepare_next_impl_branch.py`
4. update `pyproject.toml` and `docs/commands.md`
5. add tests for stale ancestry and prior-unmerged-slice blocking

## Validation and Acceptance

- `uv run pytest -q tests/test_mergeback_orchestration_api.py tests/test_prepare_next_impl_branch.py`
- `bin/execplan-validate .agent/execplans/20260327-implementation-branch-ancestry-enforcement-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the orchestrator must be able to determine, from command output alone, whether an impl branch is stale against its initiative and whether a new impl branch may lawfully be cut

## Idempotence and Recovery

- repeated branch-preparation checks should not mutate canonical state
- stale implementation slices should block with deterministic blockers instead of being silently restacked by operator memory

## Artifacts and Notes

- this slice extends the merge-back control-plane family rather than introducing a second governance API

## Interfaces and Dependencies

- depends on `mergeback_orchestration.py`, `merge_readiness.py`, and branch-policy logic
- must stay subordinate to `spec/workflow.yaml`, `spec/governance.yaml`, and the remaining-work graph
