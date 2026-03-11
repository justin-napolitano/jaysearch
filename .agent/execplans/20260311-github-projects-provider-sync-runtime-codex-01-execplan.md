---
id: "20260311-github-projects-provider-sync-runtime-codex-01-execplan"
title: "Implement outbound GitHub Projects sync from canonical graph state"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-github-projects-provider-sync-runtime-codex-01-execplan.md
  - src/platform_tools/integrations/provider_adapter.py
  - src/platform_tools/integrations/github_projects_runtime.py
  - bin/github-projects-sync
  - spec/providers/github-projects.schema.yaml
  - tests/test_github_projects_sync.py
  - bin/github-projects-sync-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-github-projects-provider-sync-runtime-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-github-projects-provider-sync-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "github-projects-sync-smoke-test"
      command: "bin/github-projects-sync-smoke-test"
      expected_exit: 0
tasks:
  - title: "Implement deterministic GitHub Projects payload generation"
    priority: "P1"
  - title: "Add provider runtime for outbound sync execution"
    priority: "P1"
  - title: "Project PR and review-finalization fields without making GitHub authoritative"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-provider-sync-scaffold-codex-01-execplan"
  - "20260311-runtime-constraint-canonicalization-codex-01-execplan"
---

# Purpose / Big Picture

Implement the first real outbound provider runtime by syncing canonical remaining-work graph state into GitHub Projects.

This slice should turn the existing projection scaffold into a deterministic runtime that can produce and execute GitHub Projects updates for the governed board model without transferring workflow authority to GitHub.

## Progress

- [x] Implement deterministic GitHub Projects payload generation
- [x] Add outbound sync runtime and command wrapper
- [x] Project PR/review/finalization fields safely
- [x] Add focused tests and smoke coverage

## Surprises & Discoveries

- GitHub Projects field ids and option ids may require a locally supplied mapping artifact instead of discovery-time API dependence
- PR and merge-finalization state should be projected from canonical branch/merge evidence rather than inferred from mutable board edits
- locally supplied item ids and field ids are the cleanest first runtime boundary; the command can update mapped items and create draft items without relying on live schema discovery
- dry-run mode is enough to prove deterministic outbound intent in tests and smoke coverage while keeping network side effects out of the validation path

## Decision Log

- 2026-03-11 / agent-codex-01 / GitHub Projects sync remains outbound projection only; remote edits must not become canonical local state in this slice.
- 2026-03-11 / agent-codex-01 / The synced board model should represent remaining-work slice nodes, not one board per ExecPlan.
- 2026-03-11 / agent-codex-01 / Review and finalization fields should be projected as evidence-bearing board fields sourced from PR links, validation state, and signed-merge status.
- 2026-03-11 / agent-codex-01 / Runtime execution should require a local field-map artifact for project id, field ids, option ids, and optional pre-existing item ids rather than doing live GitHub schema discovery.
- 2026-03-11 / agent-codex-01 / The initial live runtime should support dry-run by default and optional execute mode behind `GITHUB_TOKEN`, preserving deterministic local validation.

## Outcomes & Retrospective

This slice now provides the first live external projection runtime for the game: canonical local state in, deterministic GitHub Projects updates out, no authority drift back in.

## Context and Orientation

The provider-sync scaffold now defines:

- provider-neutral projection rules
- a GitHub Projects mapping schema
- a placeholder Microsoft Lists mapping schema

What it does not yet do is perform actual outbound sync execution against GitHub Projects.

This slice should add that first live runtime while preserving:

- local graph canonicality
- human/agent portability
- signed-merge finalization authority on `main`

## Plan of Work

1. Implement GitHub Projects payload and field mapping generation from canonical remaining-work state.
2. Add an outbound sync runtime and command wrapper.
3. Project PR/review/finalization evidence into board fields without granting GitHub authority.
4. Add focused tests and a smoke path.

## Concrete Steps

1. Add `src/platform_tools/integrations/github_projects_runtime.py`.
2. Add `bin/github-projects-sync`.
3. Extend `src/platform_tools/integrations/provider_adapter.py` and `spec/providers/github-projects.schema.yaml` as needed for runtime execution inputs.
4. Define runtime inputs for:
   - project id
   - field id mapping / option id mapping
   - dry-run mode
   - canonical execplan / branch context
5. Ensure projected fields cover:
   - node identity and title
   - canonical status and gating class
   - implementation branch
   - PR URL
   - validation/smoke status
   - human review state
   - merge/finalization state
6. Add focused tests and `bin/github-projects-sync-smoke-test`.
7. Run:
   - `bin/execplan-validate .agent/execplans/20260311-github-projects-provider-sync-runtime-codex-01-execplan.md`
   - `bin/github-projects-sync-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- GitHub Projects sync is deterministic and machine-readable
- outbound sync can be executed or dry-run without changing local authority rules
- projected review/finalization fields are sourced from canonical local evidence
- focused tests and smoke coverage pass

## Idempotence and Recovery

This slice should be safe to rerun if GitHub Projects item identity is stable, updates are idempotent, and dry-run mode can prove the planned mutations without external side effects.

## Artifacts and Notes

Expected artifacts:

- `src/platform_tools/integrations/github_projects_runtime.py`
- `bin/github-projects-sync`
- focused tests
- `bin/github-projects-sync-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `artifacts/planner/research/remaining-work-graph.json`
- `bin/remaining-work-graph-check`
- `src/platform_tools/integrations/provider_adapter.py`
- `spec/providers/github-projects.schema.yaml`
