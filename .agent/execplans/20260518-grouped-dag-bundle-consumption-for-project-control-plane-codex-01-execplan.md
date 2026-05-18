# Grouped DAG Bundle Consumption For Project Control Plane Exec Plan

## Purpose

Add the minimum platform capability needed for `platform-template-bootstrap` to consume task-level DAGs plus grouped DAG bundle projections for the `project-control-plane` build.

## Problem

The platform already has canonical graph state and ExecPlan projection, but `project-control-plane` needs one additional packaging layer:

- grouped execution bundles that reference canonical DAG node ids

Without that layer, the platform can see the fine-grained graph but cannot cleanly orchestrate the grouped foundation packets already defined by the project.

## Scope

- define the grouped DAG bundle as a projection surface
- link grouped bundles to canonical DAG ids and node ids
- define how grouped bundles expand into task packets
- preserve lineage from grouped bundle to task packet outputs

## Inputs

- canonical task-level DAG
- grouped foundation exec-plan set from `project-control-plane`
- existing ExecPlan projection rules

## Deliverables

- grouped DAG bundle contract
- lineage expectations for grouped bundles
- implementation slice definition for task-packet expansion

## Constraints

- the task graph remains canonical
- grouped bundles are projection-only
- lineage must remain explicit
- no broad orchestrator redesign is in scope

## Exit Criteria

- the minimum grouped-bundle concept is documented
- the platform has a clear bounded next step
- `project-control-plane` can rely on the platform to package grouped execution slices without more architectural drift
