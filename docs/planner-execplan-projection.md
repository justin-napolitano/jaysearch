# Planner to ExecPlan Projection

## Purpose

This document defines how canonical planner state becomes a governed ExecPlan draft. The projection exists to create a human-reviewable execution contract, not to replace planner or graph state as the source of truth.

## Preconditions

`bin/planner contract draft-execplan` should only succeed when:

- the graph has a bounded objective
- major constraints are captured
- required decisions are recorded
- scope boundaries are explicit
- candidate files, interfaces, or artifact targets are known
- validation expectations are defined
- unresolved questions are below a documented threshold or are explicitly deferred

If the planner cannot satisfy these conditions, the command should refuse projection and emit the blocking reasons.

## Mapping

The projection should map canonical planner state into ExecPlan sections as follows:

- purpose and goal context -> `Purpose / Big Picture`
- current readiness and tracked work items -> `Progress`
- unresolved or newly discovered facts -> `Surprises & Discoveries`
- accepted architectural decisions -> `Decision Log`
- expected deliverables and later review notes -> `Outcomes & Retrospective`
- local repo and platform constraints -> `Context and Orientation`
- high-level implementation sequence -> `Plan of Work`
- concrete operator steps and validation commands -> `Concrete Steps`
- pass/fail conditions -> `Validation and Acceptance`
- rerun and partial-failure strategy -> `Idempotence and Recovery`
- output artifact paths and notes -> `Artifacts and Notes`
- touched systems, files, contracts, and providers -> `Interfaces and Dependencies`

## Projection Rules

- The rendered ExecPlan must include explicit path changes.
- The rendered ExecPlan must point back to session and graph provenance.
- The rendered ExecPlan must not contain hidden reasoning that is absent from local artifacts.
- The rendered ExecPlan must be draftable by the agent, but finalization remains human-governed.
- The rendered ExecPlan must remain a projection.
- Direct reverse-sync from edited markdown contracts back into canonical planner state is forbidden.
- Any contract changes that must affect canonical state require an explicit `contract import-execplan` reconciliation step.

## Import and Reconciliation

If an operator edits a draft ExecPlan and wants those edits reflected in canonical planner state, the platform must require an explicit import path.

The import path must:

- compare edited contract content against the original projection
- identify accepted, rejected, and unresolved changes
- preserve original session and graph provenance
- record any canonical graph updates as explicit new evidence
- refuse silent intent mutation

## Reconciliation Report

`contract import-execplan` must emit a deterministic reconciliation report as a local artifact and command result.

The report must include:

- `report_id`
- `session_id`
- `graph_id`
- `execplan_id`
- `source_execplan_path`
- `original_projection_hash`
- `edited_execplan_hash`
- `created_at`
- `status`
- `accepted_changes`
- `rejected_changes`
- `unresolved_changes`
- `canonical_updates`
- `operator_notes`

Each change entry must identify:

- affected section or frontmatter field
- change classification
- whether the change alters intent, scope, validation, or metadata only
- resulting canonical action taken or refusal reason

The report schema must be machine-readable so review, validation, and future tooling can reason about imports without parsing prose.

## Open Design Decisions

The implementation phase must still define:

- exact readiness score or thresholding mechanism
- exact provenance fields embedded in rendered contracts
- whether the projection includes graph-node identifiers directly in markdown
