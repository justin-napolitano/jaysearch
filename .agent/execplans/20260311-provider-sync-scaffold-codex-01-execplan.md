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
  - spec/providers/github-projects.schema.yaml
  - spec/providers/microsoft-lists.schema.yaml
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
  - title: "Define provider-neutral adapter and projection contract"
    priority: "P1"
  - title: "Define GitHub Projects-first mapping contract"
    priority: "P1"
  - title: "Scaffold provider integration package"
    priority: "P1"
  - title: "Preserve local canonical authority in all sync flows"
    priority: "P1"
  - title: "Keep provider state human- and agent-operable"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-implementation-orchestrator-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Scaffold provider-sync adapters for downstream systems without granting external systems authority over canonical local state.

This slice is review-gated and should begin only after the implementation orchestrator runtime is in place.

GitHub Projects is the first provider target. Microsoft Lists should be represented as a placeholder mapping contract so the adapter model stays provider-neutral from the beginning.

## Progress

- [ ] Define provider-neutral adapter contract
- [ ] Define GitHub Projects-first projection model
- [ ] Scaffold provider integration package
- [ ] Protect canonical local authority
- [ ] Preserve human/agent portability across provider projections
- [ ] Add focused tests and smoke coverage

## Surprises & Discoveries

- provider contracts may reveal missing execution-state fields needed for downstream projections
- preserving local authority may require stronger conflict-report artifacts than the current draft contract assumes
- one remote board per ExecPlan would fragment the governed graph; a graph-domain board with slice items is the better first projection model
- the board must remain usable by humans if Codex, Claude, or any single agent disappears, so synced fields must expose enough structured state to resume safely from canonical artifacts

## Decision Log

- 2026-03-11 / agent-codex-01 / Provider sync must remain downstream projection only and must not grant external systems authority over canonical local state.
- 2026-03-11 / agent-codex-01 / GitHub Projects is the first provider target and should project the remaining-work graph as a single governed execution/review board rather than one board per ExecPlan.
- 2026-03-11 / agent-codex-01 / The sync framework should support both human and agent players, so provider items must be comprehensible and actionable without access to any one agent's hidden state.
- 2026-03-11 / agent-codex-01 / Provider-neutral adapter contracts and provider-specific schema mappings should both be explicit first-class artifacts.

## Outcomes & Retrospective

On completion, this slice should leave a provider-neutral adapter scaffold plus a GitHub Projects-first mapping contract that can project canonical remaining-work state outward without weakening the platform’s source-of-truth rules.

## Context and Orientation

This slice is review-gated and should begin only after the implementation orchestrator runtime is in place.

The provider model for this slice is:

- local remaining-work graph and ExecPlan state remain canonical
- provider systems receive projections only
- GitHub Projects is the first external board
- project items should represent governed slice nodes rather than turning each ExecPlan into its own remote board
- remote boards must remain understandable to humans and portable across future agents

## Plan of Work

1. Define the provider-neutral adapter contract and projection semantics.
2. Define GitHub Projects mapping and identity rules for remaining-work nodes.
3. Scaffold the integration package with GitHub Projects first and Microsoft Lists as a placeholder mapping contract.
4. Add focused tests and smoke coverage.

## Concrete Steps

1. Add `spec/provider-adapter.schema.yaml`.
2. Add provider-specific mapping schemas for GitHub Projects first and Microsoft Lists placeholder coverage.
3. Add the integration package under `src/platform_tools/integrations/`.
4. Encode projection rules for:
   - remaining-work node -> provider item identity
   - canonical status/gating/branch/execplan fields -> provider fields
   - local-only authority and conflict reporting
5. Add focused tests and `bin/provider-sync-smoke-test`.
4. Run:
   - `bin/execplan-validate .agent/execplans/20260311-provider-sync-scaffold-codex-01-execplan.md`
   - `bin/provider-sync-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- adapter scaffolding preserves local canonical authority
- provider-neutral contract and provider-specific mapping contracts are explicit
- GitHub Projects mapping is defined for one graph-domain board with item-level slice projection
- projected items carry enough structured context for human or agent continuation
- focused tests cover the contract
- the smoke script passes

## Idempotence and Recovery

This slice should be safe to rerun if the adapter contract remains deterministic and the smoke path does not create disposable external state.

## Artifacts and Notes

Expected artifacts:

- `spec/provider-adapter.schema.yaml`
- `spec/providers/github-projects.schema.yaml`
- `spec/providers/microsoft-lists.schema.yaml`
- `src/platform_tools/integrations/`
- focused tests
- `bin/provider-sync-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `artifacts/planner/research/remaining-work-graph.json`
- `bin/remaining-work-graph-check`
- `docs/adr/ADR-0001-graph-canonical-execplan-projection.md`
- `bin/implementation-orchestrator`
