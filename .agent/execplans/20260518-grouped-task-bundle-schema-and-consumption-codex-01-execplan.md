# Grouped Task Bundle Schema And Consumption Exec Plan

## Purpose

Freeze the grouped-task-bundle contract and the minimum implementation path required for `platform-template-bootstrap` to consume it.

## Problem

The platform already has:

- canonical task graph state
- ExecPlan projection
- bounded worker-slice orchestration

What it lacks is a small projection layer that can package canonical DAG node sets into governed grouped execution slices.

## Scope

- define grouped-task-bundle schema
- define grouped-task-bundle consumption rules
- identify the minimum runtime touchpoints
- avoid broader orchestrator redesign

## Deliverables

- schema:
  - `spec/grouped-task-bundle.schema.yaml`
- contract doc:
  - `docs/grouped-task-bundle-contract.md`
- touchpoint plan for runtime implementation

## Runtime Touchpoints

Primary files:

- `src/platform_tools/next_worker_slice.py`
- `src/platform_tools/prepare_next_worker_slice.py`
- `src/platform_tools/resolve_worker_contract.py`
- `src/platform_tools/worker_contracts.py`

Likely new module:

- `src/platform_tools/grouped_task_bundles.py`

Likely tests:

- grouped bundle schema validation
- illegal node reference failure
- bundle expansion behavior
- fallback to non-bundle behavior

## Minimal Implementation Order

1. add grouped bundle schema
2. add grouped bundle loader and validator
3. teach `prepare_next_worker_slice.py` to expand bundle -> node set -> task packet
4. teach `next_worker_slice.py` to prefer an active grouped bundle when one is declared
5. propagate `bundle_id` and `dag_id` lineage through worker contracts
6. add tests

## Constraints

- task graph remains canonical
- grouped bundles are projection-only
- no second canonical graph
- no broad orchestrator rewrite
- no grouped-bundle authoring surface is required in this slice

## Exit Criteria

- grouped-bundle contract is frozen
- runtime touchpoints are explicit
- the next implementation slice can start without reopening the architecture
