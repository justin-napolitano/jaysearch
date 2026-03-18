---
id: "20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan"
title: "Enforce rule-registry drift checks and harden provider-sync runtime contracts"
owner: "agent/codex-01"
created: "2026-03-18T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan.md
  - artifacts/planner/research/remaining-work-graph.json
  - docs/commands.md
  - docs/execplans.md
  - docs/queued-execplans.md
  - docs/rules-architecture.md
  - spec/governance.yaml
  - spec/providers/github-projects.schema.yaml
  - spec/rule-registry.yaml
  - src/platform_tools/governance_check.py
  - src/platform_tools/integrations/github_projects_runtime.py
  - src/platform_tools/integrations/github_projects_sync.py
  - src/platform_tools/reconcile_remaining_work_merge.py
  - src/platform_tools/rule_graph_check.py
  - src/platform_tools/rule_registry_check.py
  - tests/test_github_projects_sync.py
  - tests/test_reconcile_remaining_work_merge.py
  - tests/test_rule_graph_check.py
  - tests/test_rule_registry_check.py
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-20260318"
draft_created: "2026-03-18T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan.md"
      expected_exit: 0
    - name: "rule-graph-check"
      command: "bin/rule-graph-check"
      expected_exit: 0
    - name: "remaining-work-graph-check"
      command: "bin/remaining-work-graph-check"
      expected_exit: 0
    - name: "github-projects-sync-tests"
      command: "uv run pytest -q tests/test_github_projects_sync.py tests/test_reconcile_remaining_work_merge.py tests/test_rule_graph_check.py tests/test_rule_registry_check.py"
      expected_exit: 0
tasks:
  - title: "Add rule-registry drift enforcement with a dedicated registry checker"
    priority: "P1"
  - title: "Fail when enforced rules are missing from the registry or point at missing enforcement surfaces"
    priority: "P1"
  - title: "Standardize provider-sync token preflight and error reporting around GITHUB_TOKEN"
    priority: "P1"
  - title: "Validate field-map completeness against canonical graph and provider item identities"
    priority: "P1"
  - title: "Harden merge reconciliation so implementation merge evidence is selected deterministically"
    priority: "P1"
depends_on:
  - "20260318-rule-authority-consolidation-codex-01-execplan"
  - "20260312-human-operations-review-runtime-codex-01-execplan"
  - "20260311-github-projects-provider-sync-runtime-codex-01-execplan"
---

# Purpose / Big Picture

Make the new rule-registry authority durable by adding explicit drift enforcement, then tighten the adjacent provider-sync and reconciliation paths that now depend on canonical graph state being trustworthy.

This slice exists because the repository now has a canonical rule registry, a graph-backed review board, and governed merge reconciliation, but there are still gaps in durability:

- nothing fails if a new enforced rule appears outside `spec/rule-registry.yaml`
- provider-sync token handling is operationally brittle even though the runtime itself works
- the local field-map can drift away from the graph and board state without one focused completeness check
- merge reconciliation can still choose the wrong merge evidence if multiple related PRs exist for one ExecPlan lifecycle

## Progress

- [ ] Add dedicated rule-registry drift enforcement
- [ ] Tie rule-registry completeness to existing graph validation
- [ ] Standardize GitHub provider token handling and preflight errors
- [ ] Add field-map completeness and board-identity hygiene checks
- [ ] Harden post-merge reconciliation evidence selection
- [ ] Validate the slice

## Surprises & Discoveries

- The prior consolidation slice created the rule registry, but `bin/rule-graph-check` still remains the only guardrail on inventory completeness.
- Live GitHub Project sync works when a correctly scoped `GITHUB_TOKEN` is present, but operational paths have recently depended on ad hoc token bridging and shell knowledge rather than one explicit preflight contract.
- The current field-map artifact is now materially important local state because it stores stable item ids for all projected nodes.
- The merge reconciliation tool can incorrectly choose draft-plan PR evidence over implementation PR evidence unless the selection rule is explicit.

## Decision Log

- 2026-03-18 / agent-codex-01 / Rule-registry completeness should have its own first-class checker rather than remaining an implied property of rule-graph projection only.
- 2026-03-18 / agent-codex-01 / GitHub provider-sync runtime should standardize on `GITHUB_TOKEN` as the live execution contract and emit scope-specific blockers before mutation attempts.
- 2026-03-18 / agent-codex-01 / Field-map completeness is governed local state and should be validated against the canonical graph rather than treated as a passive bootstrap artifact.
- 2026-03-18 / agent-codex-01 / Merge reconciliation should prefer implementation-finalization evidence when both draft and implementation merges exist for a slice lifecycle.

## Outcomes & Retrospective

On completion, the repository should have:

- a dedicated `rule-registry-check` that fails on rule drift
- rule-to-check and rule-to-artifact references validated mechanically
- one explicit live token contract for GitHub provider sync
- clearer provider-sync blockers for missing token, missing scopes, and incomplete field-map state
- deterministic merge reconciliation that selects the correct finalization evidence for implementation slices

Expected implemented outcome:

- no enforced rule can be added silently outside `spec/rule-registry.yaml`
- the provider-sync runtime can be run procedurally without token-name guesswork
- field-map artifacts and graph state stay aligned enough to trust update-vs-create decisions
- completion reconciliation no longer needs manual evidence correction when the intended implementation merge is unambiguous

## Context and Orientation

The repository now has the core machine-readable authority surfaces in place:

- `spec/rule-registry.yaml` as the rule inventory
- `artifacts/planner/research/remaining-work-graph.json` as the canonical execution graph
- `artifacts/provider-sync/github-projects-field-map.json` as the local provider identity map

This slice is the follow-through that prevents those surfaces from drifting apart operationally.

## Plan of Work

1. Inventory the rule registry against active validators and rule-bearing specs.
2. Add a dedicated runtime check for registry completeness and enforcement mapping validity.
3. Decide how `rule_graph_check` and the new registry check divide responsibility.
4. Standardize provider-sync token and preflight error semantics around `GITHUB_TOKEN`.
5. Add field-map completeness checks that protect provider item reuse.
6. Harden merge reconciliation evidence selection for completed implementation slices.

## Concrete Steps

1. Add `src/platform_tools/rule_registry_check.py` and a matching `bin/rule-registry-check` command.
2. Validate at least:
   - every `class: enforced` rule has non-empty `enforced_by`
   - every `enforced_by` command resolves to a known command surface
   - required source artifacts exist
   - rule ids are unique and canonical
3. Update rule-graph validation so the graph and registry checks complement each other rather than overlap ambiguously.
4. Update GitHub provider runtime/sync code so:
   - `GITHUB_TOKEN` is the required execution token
   - missing token yields a precise blocker
   - insufficient project scopes yield a clearer blocker
5. Add field-map hygiene checks that fail when required graph nodes lack stable provider item ids after live sync has established a reusable board.
6. Update merge reconciliation so implementation merge evidence is chosen deterministically when both draft and implementation merges are present.
7. Update docs for the new checker and runtime preflight contract.

## Validation and Acceptance

Acceptance criteria:

- `bin/rule-registry-check` fails when enforced rules are omitted or mapped to missing command/artifact surfaces
- `bin/rule-graph-check` still passes for a consistent registry-backed graph
- GitHub provider-sync emits precise blockers for missing `GITHUB_TOKEN` and missing project scopes
- field-map completeness can be validated mechanically once a board exists
- merge reconciliation chooses implementation merge evidence for governed implementation slices without manual correction when the evidence is unambiguous

## Idempotence and Recovery

- rerunning the registry checker should be deterministic for the same repo state
- provider-sync preflight should fail before remote mutation when required token/scopes are absent
- merge reconciliation should remain safe to rerun and should not duplicate completion actions once canonical completion is already recorded

## Artifacts and Notes

Expected artifacts:

- `src/platform_tools/rule_registry_check.py`
- updated `src/platform_tools/integrations/github_projects_sync.py`
- updated `src/platform_tools/integrations/github_projects_runtime.py`
- updated `src/platform_tools/reconcile_remaining_work_merge.py`
- updated docs and tests for the new contracts

Planned implementation branch:

- `impl-execplan/20260318-rule-registry-drift-and-provider-sync-hardening-codex-01-execplan-codex-01-20260318`

## Interfaces and Dependencies

Primary interfaces:

- `spec/rule-registry.yaml`
- `spec/governance.yaml`
- `spec/providers/github-projects.schema.yaml`
- `artifacts/provider-sync/github-projects-field-map.json`
- `artifacts/planner/research/remaining-work-graph.json`
- `src/platform_tools/rule_graph_check.py`
- `src/platform_tools/rule_registry_check.py`
- `src/platform_tools/integrations/github_projects_sync.py`
- `src/platform_tools/reconcile_remaining_work_merge.py`

Primary dependencies:

- the merged rule-authority consolidation slice
- the existing GitHub Projects bootstrap and provider-sync runtime
- the existing human-operations and completion-reconciliation flow
