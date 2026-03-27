---
id: "20260326-local-offline-orchestration-bootstrap-codex-01-execplan"
title: "Bootstrap a local offline orchestration runtime and thin task router"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260326-local-offline-orchestration-bootstrap-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/local-offline-orchestration-bootstrap.md
  - docs/queued-execplans.md
  - prompts/20260326-local-offline-orchestration-bootstrap-codex-01.md
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-041"
  queue_position: 41
  goal_area: "orchestrator-runtime"
  conflict_domains:
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260326-local-offline-orchestration-bootstrap-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/local-offline-orchestration-bootstrap.md"
    - "docs/queued-execplans.md"
    - "prompts/20260326-local-offline-orchestration-bootstrap-codex-01.md"
    - "spec/local-orchestration.yaml"
    - "src/platform_tools/local_runtime/adapter.py"
    - "src/platform_tools/local_runtime/config.py"
    - "src/platform_tools/local_runtime/ollama_adapter.py"
    - "src/platform_tools/local_runtime/router.py"
    - "src/platform_tools/local_runtime/runtime_check.py"
    - "src/platform_tools/local_runtime/types.py"
    - "bin/local-runtime-check"
    - "bin/local-task-router"
    - "tests/test_local_runtime_adapter.py"
    - "tests/test_local_runtime_check.py"
    - "tests/test_local_runtime_router.py"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-local-offline-orchestration-bootstrap-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260326-local-offline-orchestration-bootstrap-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Capture a governed local-first orchestration posture that can run without internet access"
    priority: "P1"
  - title: "Define a minimal local runtime adapter surface with ollama as the first backend"
    priority: "P1"
  - title: "Add one local runtime reachability command and one local task-router command with compact JSON outputs"
    priority: "P1"
  - title: "Make the terminal the operator UI and the local model a cheap planner/router rather than a new chat authority"
    priority: "P1"
  - title: "Separate planning workers from execution workers and route between them explicitly"
    priority: "P1"
  - title: "Keep the local planner token-economical, offline-first, and subordinate to repo-native authority surfaces"
    priority: "P1"
  - title: "Fail closed when the local runtime is missing, misconfigured, or requires unsupported internet behavior"
    priority: "P1"
depends_on:
  - "20260326-worker-orchestration-api-codex-01-execplan"
---

# Purpose / Big Picture

Bootstrap a local-first orchestration loop that can run cheaply and offline on this workstation while preserving the current contract-first graph, worker, and governance model. The local model should be a thin planner/router over repo-native APIs rather than a new authority layer or an internet-backed agent framework.

## Progress

- [x] capture the local offline orchestration posture in a repo doc
- [x] capture the initial bootstrap prompt and machine constraints
- [x] register the initiative and the first bootstrap slice in the work graph
- [ ] implement the phase-1 local runtime adapter, config, runtime check, and task router

## Surprises & Discoveries

- this workstation is a CPU-first local orchestration host, not a GPU inference box, so the first local model needs to stay small and bounded
- the current public orchestration facade already provides the right authority surface for a thin local router to call later
- the biggest risk is not model quality alone; it is letting the local planner drift into a second uncontrolled platform with hidden memory or verbose prompt habits
- DeerFlow is a useful capability reference because it has explicit planner, research, and coding roles, but this repo should implement similar role separation over thin repo-owned APIs rather than a web-first, prompt-heavy control plane

## Decision Log

- keep the local planner deliberately small, structured, and policy-driven
- treat `ollama` as the first backend because it is the fastest bootstrap path, not because it is the final architecture
- do not build autonomous execution or multi-backend complexity in this first slice
- keep the prompt artifact as supporting context and the ExecPlan as the canonical authority
- treat prose docs and prompts as explanatory support for humans rather than required operational context for the orchestrator
- if the local orchestrator needs prose to understand a governance-critical rule or execution precondition, that rule surface is incomplete and must be promoted into a deterministic spec, schema, or stable command output before the slice is considered complete
- keep the terminal as the operator UI and treat the local model as a decision engine within that UI
- split planning workers and execution workers as separate governed roles from the start

## Outcomes & Retrospective

- expected outcome: a governed phase-1 bootstrap plan for a local offline orchestration loop that can classify work cheaply and hand off through existing worker contract surfaces

## Context and Orientation

- the current repo already has graph-backed planning, governed `bin/` commands, worker contracts, and a versioned public orchestration facade
- the new local orchestration work should call those surfaces, not replace them
- the orchestrator should be able to operate from deterministic repo-owned APIs and machine-readable artifacts without needing to infer workflow rules from prose narratives
- `docs/local-offline-orchestration-bootstrap.md` contains the operating model, host constraints, and recommended phase-1 cut
- `prompts/20260326-local-offline-orchestration-bootstrap-codex-01.md` captures the intended narrow implementation prompt for the first slice
- DeerFlow provides a role-and-capability reference for planner, researcher, coder, and human-in-the-loop behaviors, but this repo should implement those capabilities over compact API surfaces and terminal workflows

## Plan of Work

1. formalize a local orchestration runtime contract and config surface
2. add a minimal `ollama` adapter behind a repo-owned local runtime interface
3. add `bin/local-runtime-check` for reachability and fail-closed validation
4. add `bin/local-task-router` for compact routing decisions across local planner, planning worker, execution worker, remote worker, and human escalation
5. add focused tests for adapter contract, routing output shape, and missing-runtime failure behavior

## Concrete Steps

1. add `spec/local-orchestration.yaml`
2. add `src/platform_tools/local_runtime/types.py`, `adapter.py`, `config.py`, and `ollama_adapter.py`
3. add `src/platform_tools/local_runtime/router.py` and `runtime_check.py`
4. add `bin/local-runtime-check` and `bin/local-task-router`
5. define the planning-worker vs execution-worker routing shape in the config and router outputs
6. add focused tests for adapter, router, and runtime-check behavior

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260326-local-offline-orchestration-bootstrap-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the later implementation slice must add focused tests for adapter, router, and runtime-check behavior
- the phase-1 contract is not acceptable if the local orchestrator must read prose docs to discover governance-critical routing rules, authority boundaries, or execution preconditions that could have been exposed through deterministic specs or stable command outputs

## Idempotence and Recovery

- the planning artifacts are safe to re-run and should only mutate graph/queue state deterministically
- the eventual runtime-check and router commands must fail closed when local runtime prerequisites are missing

## Artifacts and Notes

- `docs/local-offline-orchestration-bootstrap.md` is the repo-local design note for the local-first posture
- `prompts/20260326-local-offline-orchestration-bootstrap-codex-01.md` is supporting prompt material, not canonical authority
- the later implementation should continue using the public orchestration facade and worker contracts as the core handoff mechanism
- planning workers should propose graph and contract changes through governed command paths instead of direct freeform edits

## Interfaces and Dependencies

- depends on the public orchestration facade added by `20260326-worker-orchestration-api-codex-01-execplan`
- should remain compatible with the token-economy and API-first rules captured in the graph/runtime hardening slice
- should keep local runtime selection as an executor/backend concern, not a redesign of the orchestration kernel
