---
id: "20260311-github-projects-bootstrap-runtime-codex-01-execplan"
title: "Bootstrap a GitHub Projects board from canonical provider schema"
owner: "agent/codex-01"
created: "2026-03-11T00:00:00Z"
status: draft
base_branch: main
changes:
  - .agent/execplans/20260311-github-projects-bootstrap-runtime-codex-01-execplan.md
  - src/platform_tools/integrations/github_projects_runtime.py
  - src/platform_tools/integrations/github_projects_bootstrap.py
  - bin/github-projects-bootstrap
  - spec/providers/github-projects.schema.yaml
  - tests/test_github_projects_bootstrap.py
  - bin/github-projects-bootstrap-smoke-test
approve_policy: codeowners
reviewers:
  - "github:justin-napolitano"
draft_by: "agent/codex-01"
draft_branch: "draft-execplan/20260311-github-projects-bootstrap-runtime-codex-01-execplan-codex-01-20260311"
draft_created: "2026-03-11T00:00:00Z"
finalized_by: ""
finalized_at: ""
finalized_in_pr: ""
validation:
  tests:
    - name: "execplan-validate"
      command: "bin/execplan-validate .agent/execplans/20260311-github-projects-bootstrap-runtime-codex-01-execplan.md"
      expected_exit: 0
    - name: "github-projects-bootstrap-smoke-test"
      command: "bin/github-projects-bootstrap-smoke-test"
      expected_exit: 0
tasks:
  - title: "Implement deterministic GitHub Projects board bootstrap planning"
    priority: "P1"
  - title: "Create board fields and option ids from canonical provider schema"
    priority: "P1"
  - title: "Emit a local field-map artifact for later sync runs"
    priority: "P1"
  - title: "Add focused tests and smoke coverage"
    priority: "P1"
depends_on:
  - "20260311-github-projects-provider-sync-runtime-codex-01-execplan"
  - "20260311-provider-sync-scaffold-codex-01-execplan"
---

# Purpose / Big Picture

Bootstrap a real GitHub Projects board directly from the canonical provider schema so the existing sync runtime can seed items without manual board setup.

This slice should create the board, create the required custom fields and option ids, and emit the local field-map artifact that `bin/github-projects-sync` already expects.

## Progress

- [x] Implement deterministic bootstrap planning
- [x] Add outbound bootstrap runtime and command wrapper
- [x] Emit reusable local field-map artifact
- [x] Add focused tests and smoke coverage

## Surprises & Discoveries

- GitHub Projects bootstrap needs a stable way to define required fields without live schema guessing, so the provider schema must become the canonical board blueprint
- the clean handoff is bootstrap first, sync second: create board + field-map, then let `github-projects-sync` handle item-level projection
- a dry-run field-map preview is useful because it proves the projected board contract before any live GitHub mutation happens
- GitHub option ids are only authoritative after board creation, so execute mode must list project fields after mutation rather than fabricate placeholder ids

## Decision Log

- 2026-03-11 / agent-codex-01 / The provider schema should serve as the canonical blueprint for GitHub Projects board bootstrap.
- 2026-03-11 / agent-codex-01 / Bootstrap should emit the same local field-map artifact consumed by `bin/github-projects-sync`.
- 2026-03-11 / agent-codex-01 / Bootstrap remains a board-setup authority only; workflow authority still stays local in canonical graph state.

## Outcomes & Retrospective

On completion, this slice should let the repo create a real GitHub Projects board from local contracts and immediately hand off to the existing sync runtime for item seeding.

Implemented:

- deterministic `bin/github-projects-bootstrap` dry-run planning from canonical schema
- execute mode that creates the board, creates fields, re-reads the project field surface, and emits a sync-compatible field-map artifact
- focused tests and a smoke path covering the bootstrap contract

## Context and Orientation

The current GitHub Projects sync runtime can:

- build deterministic dry-run operations
- execute mapped updates and draft-item creation
- project PR/review/finalization fields from local evidence

But it still assumes a real project id, field ids, and option ids are already known locally.

This slice fills that gap by making board setup reproducible from the provider schema.

## Plan of Work

1. Implement GitHub Projects bootstrap planning from `spec/providers/github-projects.schema.yaml`.
2. Add an outbound bootstrap runtime and command wrapper.
3. Emit the local field-map artifact used by `bin/github-projects-sync`.
4. Add focused tests and a smoke path.

## Concrete Steps

1. Add `src/platform_tools/integrations/github_projects_bootstrap.py`.
2. Add `bin/github-projects-bootstrap`.
3. Extend `spec/providers/github-projects.schema.yaml` as needed to support bootstrap-time board metadata.
4. Define runtime inputs for:
   - owner/org context
   - board title
   - output field-map path
   - dry-run mode
5. Ensure bootstrap output includes:
   - project id
   - field ids
   - single-select option ids
   - stable mapping keyed by canonical provider field names
6. Add focused tests and `bin/github-projects-bootstrap-smoke-test`.
7. Run:
   - `bin/execplan-validate .agent/execplans/20260311-github-projects-bootstrap-runtime-codex-01-execplan.md`
   - `bin/github-projects-bootstrap-smoke-test`

## Validation and Acceptance

Acceptance criteria:

- GitHub Projects bootstrap is deterministic and machine-readable
- bootstrap can be dry-run or executed without guessing field structure at runtime
- the emitted field-map artifact is compatible with `bin/github-projects-sync`
- focused tests and smoke coverage pass

## Idempotence and Recovery

This slice should be safe to rerun if the bootstrap runtime can detect already-created board fields, emit stable mappings, and keep dry-run as a no-side-effect proof path.

## Artifacts and Notes

Expected artifacts:

- `src/platform_tools/integrations/github_projects_bootstrap.py`
- `bin/github-projects-bootstrap`
- focused tests
- `bin/github-projects-bootstrap-smoke-test`

## Interfaces and Dependencies

Primary dependencies:

- `spec/providers/github-projects.schema.yaml`
- `src/platform_tools/integrations/github_projects_runtime.py`
- `bin/github-projects-sync`
