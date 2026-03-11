---
id: "20260311-provider-sync-scaffold-codex-01-execplan"
title: "Scaffold provider-sync adapters without external authority"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-provider-sync-scaffold-codex-01-execplan.md
  - src/platform_tools/integrations/
  - spec/provider-adapter.schema.yaml
  - tests/test_provider_adapter_contract.py
  - bin/provider-sync-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-provider-sync-scaffold-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-provider-sync-scaffold-codex-01-execplan.md"
      expected_exit: 0
    - name: "provider-sync-smoke-test"
      command: "bin/provider-sync-smoke-test"
      expected_exit: 0
tasks:
  - title: "Define provider adapter contract in code"
    priority: "P1"
  - title: "Scaffold provider integration package"
    priority: "P1"
  - title: "Preserve local canonical authority in all sync flows"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-implementation-orchestrator-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Scaffold provider-sync adapters for downstream systems without granting external systems authority over canonical local state.

This slice is review-gated and should begin only after the implementation orchestrator runtime is in place.

## Progress

- [ ] Define adapter contract
- [ ] Scaffold provider integration package
- [ ] Protect canonical local authority
- [ ] Add focused tests and smoke coverage

## Surprises & Discoveries

- provider contracts may reveal missing execution-state fields needed for downstream projections
- preserving local authority may require stronger conflict-report artifacts than the current draft contract assumes

## Decision Log

- 2026-03-11 / agent-codex-01 / Provider sync must remain downstream projection only and must not grant external systems authority over canonical local state.

## Outcomes & Retrospective

On completion, this slice should leave a code-level adapter scaffold that is ready for later GitHub Projects work without weakening the platform’s source-of-truth rules.

## Context and Orientation

This slice is review-gated and should begin only after the implementation orchestrator runtime is in place.

## Plan of Work

1. Define the provider adapter contract in code and schema.
2. Scaffold the integration package.
3. Add focused tests and smoke coverage.

## Concrete Steps

1. Add `spec/provider-adapter.schema.yaml`.
2. Add the integration package under `src/platform_tools/integrations/`.
3. Add focused tests and `bin/provider-sync-smoke-test`.
4. Run:
   - `bin/execplan-validate .agent/execplans/20260311-provider-sync-scaffold-codex-01-execplan.md`
   - `bin/provider-sync-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- adapter scaffolding preserves local canonical authority
- focused tests cover the contract
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if the adapter contract remains deterministic and the smoke path does not create disposable external state.

## Artifacts and Notes

Expected artifacts:

- `spec/provider-adapter.schema.yaml`
- `src/platform_tools/integrations/`
- focused tests
- `bin/provider-sync-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `docs/planner-control-plane-design-codex-01` 
- `bin/implementation-orchestrator`
