# Grouped Task Bundle Contract

## Purpose

This document defines the minimum grouped-bundle projection contract required for `project-control-plane` style orchestration.

## Role

Grouped task bundles are projection-only packaging layers over the canonical task graph.

They exist so a project can say:

- these node ids belong to one governed execution packet
- this packet should be orchestrated as a bounded slice

They do not replace:

- the canonical task graph
- the remaining-work graph
- the ExecPlan projection model

## Minimal Shape

Required fields:

- `bundle_id`
- `project_id`
- `dag_id`
- `title`
- `status`
- `node_ids`
- `selection_mode`
- `lineage`

Optional but expected fields:

- `exec_plan_id`
- `initiative_branch`
- `scope`
- `description`
- `priority`
- `constraints`
- `validation_refs`

## Example

```json
{
  "bundle_id": "foundation-bootstrap",
  "project_id": "project-control-plane",
  "dag_id": "registry-control-plane-foundation",
  "exec_plan_id": "20260518-registry-control-plane-foundation-bootstrap-codex-01-execplan",
  "initiative_branch": "initiative/project-control-plane",
  "title": "Foundation Bootstrap",
  "status": "ready",
  "scope": "foundation",
  "node_ids": [
    "fnd-001",
    "fnd-002",
    "fnd-003",
    "fnd-010"
  ],
  "selection_mode": "ordered",
  "lineage": {
    "source_repo": "project-control-plane",
    "source_artifact": "docs/operations/registry-control-plane-foundation-exec-plan-set.md",
    "recorded_at_utc": "2026-05-18T00:00:00Z"
  }
}
```

## Rules

1. The bundle must reference exactly one source DAG.
2. Every `node_id` must exist in the canonical DAG.
3. The bundle must not add new dependency semantics.
4. The bundle may reference one ExecPlan projection when useful.
5. The bundle must preserve lineage into task-packet expansion.

## Consumption Model

The platform should:

1. load the canonical DAG
2. load the grouped bundle projection
3. validate that all referenced node ids exist
4. expand the bundle into bounded task packets
5. preserve lineage from bundle to task packet to execution outputs

## Initial Use

The first intended consumer is `project-control-plane`, where grouped foundation exec plans package task-level DAG nodes into governed build slices.
