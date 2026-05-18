# Project Control Plane DAG Consumption

## Purpose

This document defines the minimum platform capability required for `platform-template-bootstrap` to orchestrate the first `project-control-plane` build.

## Current State Assessment

The platform already has two strong foundations:

1. a canonical task-graph model
2. an ExecPlan projection model

Existing evidence:

- `spec/task-graph.schema.yaml`
- `docs/planner-execplan-projection.md`
- `docs/remaining-work-graph.md`
- `docs/codex-orchestrator-execution-loop.md`

That means the platform already knows how to:

- treat graph state as canonical
- project graph state into governed ExecPlans
- traverse bounded ready work
- preserve projection-versus-authority boundaries

## Gap For This Project

The missing piece is not a new graph engine.

The missing piece is an explicit way to package a subset of graph nodes into a higher-order grouped execution slice without replacing the canonical graph.

For `project-control-plane`, that grouped layer is:

- grouped foundation exec plans
- grouped implementation packets
- grouped DAG bundles that reference task-node ids

## Required Capability

`platform-template-bootstrap` must support two linked views:

### 1. Task-Level DAG

This remains canonical for dependency traversal.

Examples:

- `fnd-001`
- `fnd-002`
- `fnd-003`

### 2. Grouped DAG Bundle

This is a projection that packages multiple task-level nodes into one governed execution slice.

Examples:

- `foundation bootstrap`
- `bronze scan model`
- `silver contract model`

The grouped bundle must be projection-only. It cannot replace the canonical task graph.

## Platform Rule

The platform should treat grouped DAG bundles the same way it treats ExecPlans:

- as governed projections
- sourced from canonical graph-backed state
- lineage-preserving
- bounded

## Minimal Implementation Direction

The first implementation slice should add a grouped execution-bundle contract that:

- has a stable bundle id
- references one source DAG id
- references one source ExecPlan id where applicable
- carries an ordered list of node ids
- carries scope and status metadata
- can expand into task packets

## Non-Goals

This slice should not:

- replace the task graph
- introduce a second canonical graph
- redesign the entire orchestrator
- generalize every future bundle concept up front

## Acceptance

The platform is sufficient for `project-control-plane` when it can:

1. ingest the task-level DAG
2. ingest a grouped DAG bundle projection
3. validate that grouped bundles reference legal node ids
4. expand a grouped bundle into bounded task packets
5. preserve lineage from bundle to task packet to execution outputs
