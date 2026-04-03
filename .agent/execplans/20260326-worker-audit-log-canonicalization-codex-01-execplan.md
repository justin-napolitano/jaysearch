---
id: "20260326-worker-audit-log-canonicalization-codex-01-execplan"
title: "Classify worker session audit logs as canonical append-only governance evidence"
owner: "agent/codex-01"
created: "2026-03-26T00:00:00Z"
status: draft
base_branch: initiative/local-offline-orchestration-bootstrap
changes:
  - .agent/execplans/20260326-worker-audit-log-canonicalization-codex-01-execplan.md
  - artifacts/governance/worker-session-events.jsonl
  - artifacts/planner/research/remaining-work-graph.json
  - docs/codex-orchestrator-contract.md
  - docs/merge-readiness-contract.md
  - docs/queued-execplans.md
  - spec/governance.yaml
  - spec/workflow.yaml
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
initiative_branch: "initiative/local-offline-orchestration-bootstrap"
initiative_node_id: "initiative-local-offline-orchestration-bootstrap"
graph_registration:
  node_id: "rwg-045"
  queue_position: 45
  goal_area: "governance"
  implementation_branch: "impl-execplan/20260326-worker-audit-log-canonicalization"
  conflict_domains:
    - "documentation"
    - "governance"
    - "workflow"
  expected_artifacts:
    - ".agent/execplans/20260326-worker-audit-log-canonicalization-codex-01-execplan.md"
    - "artifacts/governance/worker-session-events.jsonl"
    - "artifacts/planner/research/remaining-work-graph.json"
    - "docs/codex-orchestrator-contract.md"
    - "docs/merge-readiness-contract.md"
    - "docs/queued-execplans.md"
    - "spec/governance.yaml"
    - "spec/workflow.yaml"
  integration_mode: "via_initiative"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260326-worker-audit-log-canonicalization-codex-01-20260326"
draft_created: "2026-03-26T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan validation"
      command: "bin/execplan-validate .agent/execplans/20260326-worker-audit-log-canonicalization-codex-01-execplan.md"
      expected_exit: 0
    - name: "remaining work graph check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "policy compliance check"
      command: "bin/policy-compliance-check --execplan-path .agent/execplans/20260326-worker-audit-log-canonicalization-codex-01-execplan.md"
      expected_exit: 0
tasks:
  - title: "Make the worker session event log canonical append-only merge evidence"
    priority: "P1"
  - title: "Keep the live worker lease directory operational and non-default for merges"
    priority: "P1"
  - title: "Preserve audit history without promoting ephemeral runtime directories into canonical state"
    priority: "P1"
depends_on:
  - "20260326-initiative-branch-plan-authority-correction-codex-01-execplan"
---

# Purpose / Big Picture

Clarify the governance distinction between durable worker audit history and live worker runtime state. The worker session event log should be treated as canonical append-only evidence that merges with governed work when it changes, while the live worker lease directory should remain operational runtime state unless a slice explicitly promotes it.

## Progress

- [ ] define canonical append-only status for the worker session event log
- [ ] define non-default merge status for the live worker session directory
- [ ] retain current worker audit history in canonical repo state

## Surprises & Discoveries

- the workflow already distinguishes `worker_session_audit_log` from `worker_session_lease_directory`, but it did not say clearly which one should merge by default
- the event log is compact and valuable as durable audit history
- the lease directory is operational state and would create noise if treated as a default merge artifact

## Decision Log

- `artifacts/governance/worker-session-events.jsonl` is canonical append-only evidence
- canonical append-only audit artifacts should merge when they change under governed work
- `artifacts/governance/worker-sessions/` remains operational runtime state and is not a default merge artifact
- a later slice may promote lease artifacts only when an active ExecPlan explicitly requires them as evidence

## Outcomes & Retrospective

- expected outcome: preserve worker audit history without polluting canonical governance state with live lease residue

## Context and Orientation

- PR merge-back is now the normal governed integration path for implementation slices
- merge-readiness already distinguishes intended artifacts from disposable runtime output
- this slice makes the worker audit/history rule explicit in the same machine-readable workflow and governance surfaces

## Plan of Work

1. update workflow and governance specs to classify the audit log and lease directory differently
2. update merge-readiness and orchestrator contract docs to reflect that distinction
3. retain the current worker session event log in canonical state
4. register the slice in the graph and queue projection

## Concrete Steps

1. update `spec/workflow.yaml`
2. update `spec/governance.yaml`
3. update `docs/merge-readiness-contract.md`
4. update `docs/codex-orchestrator-contract.md`
5. add the current append-only worker event log as canonical evidence
6. register and validate the slice

## Validation and Acceptance

- `bin/execplan-validate .agent/execplans/20260326-worker-audit-log-canonicalization-codex-01-execplan.md`
- `bin/remaining-work-graph-check`
- the workflow must state explicitly that the worker session event log is canonical append-only evidence
- the workflow must state explicitly that the lease directory is operational runtime state and not a default merge artifact

## Idempotence and Recovery

- the event log is append-only evidence, so later slices may extend it without rewriting prior entries
- if the repo later defines additional canonical governance logs, they should be added through the same explicit contract path rather than by habit

## Artifacts and Notes

- this slice governs artifact classification and retention, not worker runtime behavior itself
- the existing event log entries are retained as canonical evidence under the new rule

## Interfaces and Dependencies

- depends on initiative-branch governance clarification for merge behavior
- interacts with merge-readiness artifact hygiene and orchestrator mutation boundaries
