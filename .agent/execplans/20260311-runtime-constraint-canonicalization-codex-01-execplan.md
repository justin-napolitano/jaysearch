---
id: "20260311-runtime-constraint-canonicalization-codex-01-execplan"
title: "Canonicalize remaining runtime constraints out of prose"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-runtime-constraint-canonicalization-codex-01-execplan.md
  - docs/queued-execplans.md
  - docs/remaining-work-graph.md
  - docs/codex-orchestrator-contract.md
  - docs/parallel-execution-policy.md
  - spec/remaining-work-graph.schema.yaml
  - artifacts/planner/research/remaining-work-graph.json
  - bin/remaining-work-graph-check
  - src/platform_tools/remaining_work_graph_check.py
  - src/platform_tools/orchestrator_status.py
  - src/platform_tools/implementation_orchestrator.py
  - tests/test_remaining_work_graph_check.py
  - tests/test_orchestrator_status.py
  - tests/test_implementation_orchestrator.py
  - bin/runtime-constraint-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-runtime-constraint-canonicalization-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-runtime-constraint-canonicalization-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "runtime-constraint-smoke-test"
      command: "bin/runtime-constraint-smoke-test"
      expected_exit: 0
tasks:
  - title: "Define machine-checkable remaining-work graph validation contract"
    priority: "P1"
  - title: "Make orchestrator status consume canonical runtime readiness instead of prose projections"
    priority: "P1"
  - title: "Make implementation orchestrator rely on validated runtime constraint state"
    priority: "P1"
  - title: "Reduce queue docs to explanatory mirrors of canonical artifacts"
    priority: "P2"
depends_on:
  - "20260311-remaining-work-graph-codex-01-execplan"
  - "20260311-composite-orchestrator-status-codex-01-execplan"
  - "20260311-implementation-orchestrator-runtime-codex-01-execplan"
---

# Purpose / Big Picture

The game is now largely machine-playable, but some runtime-relevant constraints still survive as prose guidance or human-readable projections instead of validated canonical state.

This slice should move the remaining runtime-critical queue and readiness rules into machine-checkable artifacts and validators so orchestration does not rely on explanatory docs to decide what is legal or next.

## Progress

- [ ] Define the remaining-work graph validator contract
- [ ] Canonicalize runtime-ready and active-slice derivation
- [ ] Remove prose-only runtime constraints from operational paths
- [ ] Add focused tests and smoke coverage

## Surprises & Discoveries

- the current remaining-work graph still lags merged implementation state, which proves the need for a canonical validator and refresh discipline
- `docs/queued-execplans.md` is still useful for humans, but the runtime must not depend on it for legality or next-step selection

## Decision Log

- 2026-03-11 / agent-codex-01 / Runtime-critical queue and readiness constraints should be enforced from canonical graph artifacts and validators, not from prose mirrors.
- 2026-03-11 / agent-codex-01 / Human-readable queue documents may remain, but only as explanatory projections whose mismatch against canonical state is treated as drift.

## Outcomes & Retrospective

On completion, the orchestrator and implementation runtime should be able to prove their next legal move and stop conditions from machine-checkable state without depending on prose queue descriptions or contract summaries.

## Context and Orientation

The current runtime already consumes `remaining-work-graph.json`, but:

- that graph has no dedicated validator
- merged slice completion can lag the graph artifact
- queue docs still carry some state humans may read as operationally relevant

This slice should close that gap before external provider sync introduces another layer of state and contracts.

## Plan of Work

1. Add a dedicated validator for the remaining-work graph and runtime constraint invariants.
2. Tighten the schema and artifact so active slice status, dependency completion, and branch targeting are canonical.
3. Update orchestrator runtime surfaces to consume only validated canonical state.
4. Reduce queue/contract docs to explanatory material that clearly defers to the canonical runtime artifacts.

## Concrete Steps

1. Add `src/platform_tools/remaining_work_graph_check.py` and `bin/remaining-work-graph-check`.
2. Extend `spec/remaining-work-graph.schema.yaml` and `artifacts/planner/research/remaining-work-graph.json` so runtime-critical fields are explicit.
3. Update `src/platform_tools/orchestrator_status.py` and `src/platform_tools/implementation_orchestrator.py` to consume validated runtime constraint state.
4. Update `docs/queued-execplans.md`, `docs/remaining-work-graph.md`, `docs/codex-orchestrator-contract.md`, and `docs/parallel-execution-policy.md` so they no longer act as hidden runtime authorities.
5. Add focused tests and `bin/runtime-constraint-smoke-test`.
6. Run:
   - `bin/execplan-validate .agent/execplans/20260311-runtime-constraint-canonicalization-codex-01-execplan.md`
   - `bin/remaining-work-graph-check`
   - `bin/runtime-constraint-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- runtime-critical remaining-work and queue constraints have a dedicated machine-readable validator
- orchestrator runtime paths do not rely on prose documents for legality or next-step selection
- human-readable queue docs are explicitly secondary to the canonical artifact
- focused tests and the smoke path pass

## Idempotence and Recovery

This slice should be safe to rerun if the remaining-work graph validator is deterministic and the smoke path uses isolated or read-only artifact state.

## Artifacts and Notes

Expected artifacts:

- `bin/remaining-work-graph-check`
- `src/platform_tools/remaining_work_graph_check.py`
- tightened remaining-work schema and canonical graph artifact
- focused tests
- `bin/runtime-constraint-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `artifacts/planner/research/remaining-work-graph.json`
- `docs/queued-execplans.md`
- `bin/orchestrator-status`
- `bin/implementation-orchestrator`
