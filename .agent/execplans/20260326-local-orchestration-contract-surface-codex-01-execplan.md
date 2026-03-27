---
id: "20260326-local-orchestration-contract-surface-codex-01-execplan"
title: "Define the local orchestration contract surface before implementation workers execute"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260326-local-orchestration-contract-surface-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/local-orchestration-api.md
  - docs/queued-execplans.md
  - spec/local-orchestration.yaml
  - spec/local-orchestration-api.schema.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-042"
  queue_position: 42
  goal_area: "orchestrator-runtime"
  conflict_domains:
    - "documentation"
    - "governance"
    - "orchestrator-runtime"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260326-local-orchestration-contract-surface-codex-01-execplan.md"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/local-orchestration-api.md"
    - "docs/queued-execplans.md"
    - "spec/local-orchestration.yaml"
    - "spec/local-orchestration-api.schema.yaml"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-local-orchestration-contract-surface-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260326-local-orchestration-contract-surface-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
tasks:
  - title: "Define one machine-readable local orchestration profile that stays subordinate to existing workflow, ruleset, orchestrator, and capability-policy authority"
    priority: "P1"
  - title: "Define one versioned API/schema catalog for local-runtime-check and local-task-router request, response, and failure payloads"
    priority: "P1"
  - title: "Define routing targets, fail-closed conditions, and managed-repo targeting semantics before implementation workers begin coding"
    priority: "P1"
  - title: "Make prose explanatory only and require governance-critical execution behavior to be derivable from deterministic specs and stable command outputs"
    priority: "P1"
depends_on:
  - "20260325-graph-runtime-contract-hardening-codex-01-execplan"
  - "20260326-worker-orchestration-api-codex-01-execplan"
  - "20260326-local-offline-orchestration-bootstrap-codex-01-execplan"
---

# Purpose / Big Picture

Define the contract surface for phase-1 local orchestration before implementation workers execute. This slice should turn the local-orchestration design intent into deterministic repo-owned spec artifacts so later workers can build `local-runtime-check` and `local-task-router` without inventing request shapes, response semantics, escalation behavior, or managed-repo targeting rules in code.

## Progress

- [x] state explicitly that prose and prompts are explanatory support rather than required operational context
- [ ] define the local orchestration profile as a machine-readable spec
- [ ] define the local orchestration request/response/problem contract catalog as a versioned schema
- [ ] define managed-repo targeting and fail-closed routing rules for the phase-1 local orchestrator

## Surprises & Discoveries

- the public orchestration facade already provides a strong lower layer for graph state, worker resolution, and bounded execution, so the main remaining risk is contract drift at the local-router edge rather than missing execution primitives
- if endpoint and problem shapes are left to implementation workers, the local orchestration layer will likely duplicate policy that already belongs in workflow, orchestrator, or capability specs
- the repo already favors versioned schema catalogs for orchestration-facing commands, so the local contract should follow the same pattern rather than hiding structure in markdown examples

## Decision Log

- this ExecPlan is planning authority for phase-1 local orchestration endpoint and payload shapes; later implementation workers must reference these artifacts rather than redefine them
- `spec/local-orchestration.yaml` is a subordinate runtime-profile contract and may not redefine governance semantics that already belong to `spec/workflow.yaml`, `spec/ruleset.yaml`, `spec/codex-orchestrator.yaml`, or `spec/agent-capability-policy.yaml`
- `spec/local-orchestration-api.schema.yaml` is the canonical machine-readable contract for `local-runtime-check` and `local-task-router` requests, responses, and problem payloads
- prose docs may explain rationale and usage, but if the local orchestrator needs prose to discover a governance-critical rule, routing precondition, or authority boundary, the contract surface is incomplete
- problem payloads should align to RFC 9457 shape where practical, and API contracts should remain compact, bounded, and deterministic

## Outcomes & Retrospective

- expected outcome: one planning package that defines the local orchestration contract surface cleanly enough that implementation workers can build to spec without widening authority or endpoint semantics ad hoc

## Context and Orientation

- the current repo already has canonical workflow, ruleset, orchestrator, and capability-policy contracts
- the public orchestration facade already exposes compact command surfaces that a local planner/router can call
- the missing layer is the local orchestration edge contract: configuration profile, routing schema, runtime-check schema, and failure semantics
- this slice is contract definition only; it does not implement the runtime adapter or command handlers

## Plan of Work

1. define the subordinate local orchestration profile in `spec/local-orchestration.yaml`
2. define versioned local command request and response contracts in `spec/local-orchestration-api.schema.yaml`
3. define managed-repo targeting semantics and fail-closed rules that keep repo-local canonical state authoritative
4. define routing targets and bounded decision outputs for phase 1
5. document the authority boundary so later workers implement against the contract rather than reinterpret prose

## Concrete Steps

1. add `spec/local-orchestration.yaml`
2. add `spec/local-orchestration-api.schema.yaml`
3. add `docs/local-orchestration-api.md`
4. register this planning slice in the remaining-work graph and queue projection
5. validate the ExecPlan and graph consistency

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260326-local-orchestration-contract-surface-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the canonical local orchestration contract artifacts exist and define:
  1. endpoint inventory
  2. request fields
  3. response fields
  4. problem payload shape
  5. routing target enum
  6. fail-closed conditions
  7. managed-repo targeting semantics
- the planning package is not acceptable if a later implementation worker would still need to infer governance-critical behavior from prose-only guidance

## Idempotence and Recovery

- rerunning graph registration is safe only if node identity, queue position, and expected artifacts remain aligned
- if later planning discovers that local-runtime-check and local-task-router need separate major versions, that should happen through versioned schema evolution rather than silent widening of one schema

## Artifacts and Notes

- `spec/local-orchestration.yaml` is the subordinate local runtime profile
- `spec/local-orchestration-api.schema.yaml` is the versioned command contract catalog
- `docs/local-orchestration-api.md` is explanatory support for humans and must not become the only operational source of truth

## Interfaces and Dependencies

- this slice depends on the public orchestration facade for lower-level graph and worker execution surfaces
- this slice should remain compatible with the standards posture and token-economy rules defined in the graph/runtime hardening slice
- this slice should preserve managed-repo orchestration by explicit repo-root targeting instead of centralizing other repos into platform-template-bootstrap state
