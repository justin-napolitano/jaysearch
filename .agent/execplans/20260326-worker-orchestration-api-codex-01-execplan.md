---
id: "20260326-worker-orchestration-api-codex-01-execplan"
title: "Add an orchestrator-agnostic worker contract execution API"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/worker-orchestration-api
changes:
  - .agent/execplans/20260326-worker-orchestration-api-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/queued-execplans.md
  - docs/commands.md
  - docs/public-orchestration-api.md
  - pyproject.toml
  - bin/get-graph-state
  - bin/get-worker-status
  - bin/public-orchestration-api-check
  - bin/resolve-worker-contract
  - bin/run-worker-contract
  - bin/start-next-worker
  - spec/public-orchestration-api.schema.yaml
  - spec/agent-capability-policy.yaml
  - spec/protected-surfaces.schema.yaml
  - src/platform_tools/get_graph_state.py
  - src/platform_tools/get_worker_status.py
  - src/platform_tools/public_orchestration_api.py
  - src/platform_tools/public_orchestration_api_check.py
  - src/platform_tools/resolve_worker_contract.py
  - src/platform_tools/run_worker_contract.py
  - src/platform_tools/start_next_worker.py
  - tests/test_public_orchestration_api_check.py
  - tests/test_public_orchestration_api.py
  - tests/test_run_worker_contract.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/worker-orchestration-api"
initiative_node_id: "initiative-worker-orchestration-api"
graph_registration:
  node_id: "rwg-040"
  queue_position: 40
  goal_area: "orchestrator-runtime"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260326-worker-orchestration-api-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/commands.md"
    - "docs/public-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "pyproject.toml"
    - "spec/public-orchestration-api.schema.yaml"
    - "src/platform_tools/get_graph_state.py"
    - "src/platform_tools/get_worker_status.py"
    - "src/platform_tools/public_orchestration_api.py"
    - "src/platform_tools/public_orchestration_api_check.py"
    - "src/platform_tools/resolve_worker_contract.py"
    - "src/platform_tools/run_worker_contract.py"
    - "src/platform_tools/start_next_worker.py"
    - "tests/test_public_orchestration_api_check.py"
    - "tests/test_public_orchestration_api.py"
    - "tests/test_run_worker_contract.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-worker-orchestration-api-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "worker orchestration api tests"
      command: "uv run pytest -q tests/test_public_orchestration_api.py tests/test_run_worker_contract.py tests/test_worker_session_coordinator.py tests/test_next_worker_slice.py tests/test_worker_session_status.py"
      expected_exit: 0
tasks:
  - title: "Add one orchestrator-agnostic command that resolves and runs a bounded worker contract"
    priority: "P1"
  - title: "Add a small public orchestration facade for graph state, contract resolution, worker execution, and worker status"
    priority: "P1"
  - title: "Add a composite next-worker entrypoint for thin orchestrators"
    priority: "P1"
  - title: "Keep executor and push policy explicit so the API can serve thin local or cloud orchestrators later"
    priority: "P1"
  - title: "Avoid duplicating worker runtime logic by composing existing governed worker surfaces"
    priority: "P1"
depends_on:
  - "20260325-graph-runtime-contract-hardening-codex-01-execplan"
---

# Purpose / Big Picture

Add one small repo-owned execution API for worker contracts so a thin orchestrator can drive bounded work without loading large prompt or skill surfaces. The API should stay orchestrator-agnostic: Codex may call it now, but a smaller planner model or another orchestrator should be able to call the same contract later.

## Progress

- [x] add the public facade commands for graph state, contract resolution, worker execution, and worker status
- [x] add the orchestrator-agnostic `run-worker-contract` command surface
- [x] add the composite `start-next-worker` facade command
- [x] add the public orchestration API contract doc
- [x] version the facade envelope and record the schema contract
- [x] add a live contract validator and wire it into governed pre-push checks
- [x] map executor and push policy into explicit backend fields
- [x] compose the existing worker resolver and coordinator instead of reimplementing worker execution
- [x] register the new command under governed policy surfaces

## Surprises & Discoveries

- the existing runtime already had most of the mechanics; the main gap was a compact entrypoint that can resolve one worker contract directly
- the right abstraction is contract execution, not Codex session control
- explicit `executor` and `push_mode` fields keep the command usable by local and future cloud orchestrators without changing the API shape
- graph and worker status also benefit from compact orchestration-facing projections instead of exposing raw internal reports directly
- facade outputs need explicit versioning so thin orchestrators can upgrade against one governed contract instead of brittle command-by-command assumptions
- schema-only versioning is not enough; the facade needs a live validator to catch drift between documented contracts and emitted command outputs

## Decision Log

- keep the new surface orchestrator-agnostic by naming it around worker contracts, not Codex
- support only local executor backends in this slice and fail closed for unsupported future backends
- reuse `next-worker-slice` when the caller wants the next runnable contract, and allow direct contract lookup when the caller already knows the target

## Outcomes & Retrospective

- expected outcome: one small machine-oriented command that a thin orchestrator can invoke to run bounded worker work with explicit executor and push policy

## Context and Orientation

- the repo already has the worker runtime, lease model, contract registry, and graph reconciliation surfaces
- the remaining gap is one compact execution API that another orchestrator can call without inheriting Codex-specific assumptions

## Plan of Work

1. add the new command as a thin adapter over existing worker resolution and coordination APIs
2. keep executor and push policy explicit in the command contract
3. add compact facade commands for graph state, worker contract resolution, and worker status
4. add a composite next-worker command for thin orchestrators
5. register the commands under governed policy and graph state
6. version the facade envelope in a governed schema
7. validate live facade outputs against the versioned schema catalog before push and merge

## Concrete Steps

1. add `src/platform_tools/run_worker_contract.py`
2. add `src/platform_tools/resolve_worker_contract.py`, `src/platform_tools/get_graph_state.py`, and `src/platform_tools/get_worker_status.py`
3. add `src/platform_tools/start_next_worker.py`
4. add focused tests for public API projections and worker execution facade behavior
5. update policy and command reference surfaces

## Validation and Acceptance

- `uv run pytest -q tests/test_public_orchestration_api.py tests/test_run_worker_contract.py tests/test_worker_session_coordinator.py tests/test_next_worker_slice.py tests/test_worker_session_status.py`
- `bin/remaining-work-graph-check`
- `bin/execplan-validate .agent/execplans/20260326-worker-orchestration-api-codex-01-execplan.md`

## Idempotence and Recovery

- repeated runs of the command should either resolve the same ready contract or fail closed if the registry becomes ambiguous
- unsupported executor and push-mode combinations must fail without mutating worker state

## Artifacts and Notes

- the public facade returns compact machine-readable output intended for a calling orchestrator rather than a human narrative session
- `docs/public-orchestration-api.md` is the public contract note for the facade surface
- `spec/public-orchestration-api.schema.yaml` is the canonical versioned envelope contract for facade responses
- `bin/public-orchestration-api-check` is the live validator that exercises facade outputs against the governed contract catalog

## Interfaces and Dependencies

- depends on `next-worker-slice` for initiative-level selection when the caller does not specify a contract
- depends on `worker-session-coordinator` for the actual governed execution path
- depends on the worker contract registry as the canonical selection surface
- exposes a facade layer suitable for Codex today and thinner orchestration models later
