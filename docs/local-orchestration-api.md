# Local Orchestration API

## Objective

Define the phase-1 local orchestration edge as deterministic repo-owned contract surfaces rather than prose-only guidance.

## Canonical Artifacts

- profile contract: `spec/local-orchestration.yaml`
- request/response/problem contract catalog: `spec/local-orchestration-api.schema.yaml`

These files are canonical for local orchestration behavior. This document is explanatory support only.

## Why This Exists

The local model should orchestrate against compact APIs and machine-readable artifacts instead of rediscovering workflow and governance rules from markdown each session.

If a later implementation worker or local planner needs this doc to discover a governance-critical routing rule, authority boundary, or execution precondition, the contract surface is incomplete and must be promoted into the spec or schema files.

## Command Inventory

Phase 1 defines two local orchestration commands:

- `local-runtime-check`
  - validates local runtime reachability and policy-safe configuration
- `local-task-router`
  - emits one bounded routing decision for a task

## Routing Targets

The local task router may choose only:

- `local_planner`
- `planning_worker`
- `local_execution_worker`
- `remote_execution_worker`
- `human_escalation`

The router must emit deterministic fields for route target, reason codes, policy basis, next action, validations, and blockers.

Those fields are not freeform. The canonical schema now constrains:

- `reason_codes` to a finite enum
- `policy_basis` to explicit contract-surface references
- `next_action` to specific governed commands or `human_review_required`
- `blockers` to a finite enum
- `problem.type` to a finite catalog of local-orchestration problem URIs
- `next_validations` to a finite catalog of governed validation command ids
- `evidence_refs` to typed refs using `<kind>:<value>` with allowed kinds `spec`, `doc`, `artifact`, and `command`

Where possible, router follow-up should point at existing public orchestration commands such as `bin/get-graph-state`, `bin/resolve-worker-contract`, `bin/run-worker-contract`, `bin/start-next-worker`, or `bin/get-worker-status` instead of inventing new ad hoc action text.

## Standards Posture

- request and response payloads use versioned JSON Schema contracts
- failure payloads are RFC 9457-aligned problem objects where practical
- local orchestration remains subordinate to repo-native authority in workflow, ruleset, orchestrator, and capability-policy specs
- managed repos remain canonical for their own state; local orchestration reaches them only through explicit `repo_root` targeting

## Non-Goals

- this document does not create new governance rules
- this document does not replace `spec/workflow.yaml` or `spec/codex-orchestrator.yaml`
- this document does not authorize workers to widen command semantics during implementation
